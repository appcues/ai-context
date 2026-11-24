#!/usr/bin/env python3
"""
Render an Appcues installation plan (JSON) into a branded .docx, and optionally a PDF.

Usage:
    python build_plan.py plan.json --out "Acme - Appcues Installation Plan.docx" [--pdf]

The .docx is designed to survive conversion to a Google Doc (upload it to Drive with
conversion on). Fonts are Poppins (headings) and Mulish (body) - both Google Fonts that
appcues.com uses and that Google Docs renders natively.

Any value that is empty, null, or "TBD" renders as a shaded fill-in cell, colored by who
owns it: Petal (customer business team) or Glacier (customer developer). See
references/plan-schema.md for the JSON shape. Sections with no data are still rendered
with blank rows when they are part of the core template, so the plan always has the same
skeleton the implementation team expects.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import date

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Inches

# ---------------------------------------------------------------- brand tokens
# Pulled from appcues.com's 2025 design tokens (--_appcues-2025---*)
AUBERGINE = "291A3D"   # primary / headers
THISTLE = "E9D9FF"     # light blurple
LAVENDER = "CBA7FF"    # blurple 300
ORCHID = "A688C4"      # blurple 600
PETAL = "F6EBF8"       # customer fill-in
GLACIER = "ECFBFF"     # developer fill-in
TIDAL = "6FEEEC"       # teal accent
AMP = "F0FE52"         # signature yellow accent
BUTTER = "FFFCEF"      # soft yellow callout
MORTAR = "EDE9E8"      # warm neutral
BODY = "20222E"
MUTED = "4F5875"
WHITE = "FFFFFF"

STATUS = {
    "green": ("2DB37F", "Ready"),
    "yellow": ("E0B400", "Needs a decision"),
    "red": ("D9534F", "Blocked / missing"),
    "grey": ("96A3BF", "Not in scope"),
}

# Customer-facing plans (meta.audience == "customer") use softer labels: the customer is
# assessing their own readiness, not being scored by a seller.
CUSTOMER_STATUS = {"green": "Ready", "yellow": "Needs an answer", "red": "Not started", "grey": "Not in scope"}
CUSTOMER_PILLARS = {
    "1": "1. Appcues set up everywhere it runs",
    "2": "2. Users and accounts identified",
    "3": "3. Goals written down",
    "4": "4. CRM and tools connected",
    "5": "5. Data in use, not just collected",
    "6": "6. Key Moments tracked",
}

HEAD_FONT = "Poppins"
BODY_FONT = "Mulish"

DOCS = {
    "Installation overview": "https://docs.appcues.com/installation-overview/appcues-installation-overview",
    "Install Appcues without rework": "https://docs.appcues.com/installation-overview/install-appcues-without-rework",
    "Installation plan guide": "https://docs.appcues.com/installation-overview/installation-plan",
    "Install the web SDK": "https://docs.appcues.com/install-appcues-web/install-the-appcues-sdk",
    "Identify users and groups (web)": "https://docs.appcues.com/install-appcues-web/identify-users-and-groups",
    "Track events (web)": "https://docs.appcues.com/install-appcues-web/track-events-in-your-web-app",
    "Match user IDs across integrations": "https://docs.appcues.com/install-appcues-web/match-user-ids-across-integrations",
    "Choosing events and properties": "https://docs.appcues.com/installation-overview/faq-choosing-which-events-and-properties-to-send-to-appcues",
    "Preparing your frontend for targeting": "https://docs.appcues.com/installation-overview/preparing-your-frontend-for-appcues-best-practices-for-targeting-elements",
    "US and EU hosting": "https://docs.appcues.com/installation-overview/appcues-us-and-eu-hosting-environments",
    "Install the mobile SDK": "https://docs.appcues.com/mobile-installation-overview/installing-the-mobile-sdk",
    "Register your mobile app": "https://docs.appcues.com/mobile-installation-overview/registering-your-mobile-app-in-studio",
    "Testing and debugging": "https://docs.appcues.com/dev-troubleshooting/installation-testing-debugging",
    "Integrations overview": "https://docs.appcues.com/integration-documents/appcues-integrations-overview",
    "Salesforce integration": "https://docs.appcues.com/en_US/integration-documents/salesforce-two-way-integration",
    "HubSpot integration": "https://docs.appcues.com/en_US/integration-documents/hubspot-integration",
    "Marketo integration": "https://docs.appcues.com/en_US/integration-documents/marketo-integration",
    "Segment integration": "https://docs.appcues.com/en_US/integration-documents/segment-two-way-integration",
    "Hightouch integration": "https://docs.appcues.com/en_US/integration-documents/hightouch-integration",
    "Census integration": "https://docs.appcues.com/en_US/integration-documents/census-integration",
}

# Developer checklist. Each step is tagged with the "Installed" pillar it satisfies, so this one
# table doubles as the definition-of-done (no separate checklist that repeats the scorecard).
CHECKLIST = {
    "Web": [
        ("Add the SDK to every page (snippet, NPM, Segment or GTM). EU accounts: fast.eu.appcues.com / bundleDomain", "Required", 1),
        ("Set window.AppcuesSettings.enableURLDetection before setup (single-page apps)", "SPAs", 1),
        ("Allowlist Appcues domains in your Content Security Policy", "If CSP", 1),
        ("identify() on every page load, before group() and track(); exclude internal / test users", "Required", 2),
        ("group() right after identify(), with the CRM's account ID", "If accounts", 2),
        ("track() every event in the Data plan", "Required", 6),
        ("reset() on logout (skip if you use anonymous users)", "Usually", 2),
        ("Add stable data-appcues attributes to the elements under Environments", "Required", 1),
        ("Identity verification endpoint + shared secret", "If security requires", 2),
        ("Verify: Debugger shows Installed, Connected and Tracking Pages green while navigating", "Required", 1),
    ],
    "Mobile": [
        ("Register each app in Studio; record App IDs (dev / prod)", "Required", 1),
        ("Add the SDK and initialize with Account ID + App ID (EU host for EU accounts)", "Required", 1),
        ("identify() at login, then group(); screen() for every planned screen", "Required", 2),
        ("track() every mobile event (platform-prefixed names)", "Required", 6),
        ("Configure the Appcues URL scheme / deep links (preview, debugging, screen capture)", "Required", 1),
        ("Element labels for Anchored Tooltips; FrameViews where Embeds will live", "If used", 1),
        ("Verify: Mobile Debugger shows user, group, screens and events", "Required", 1),
    ],
    "Agent": [
        ("Share how the agent / chat works and how traces or transcripts can be exported", "If agent surface", 1),
        ("Confirm the agent knows the same user ID sent to identify()", "If agent surface", 2),
    ],
    "All": [
        ("Every planned property and event appears with the right type (Events page / Debugger)", "Required", 5),
        ("Each planned integration connected; a test user's data visible on both sides", "Required", 4),
        ("Objectives and Key Moments created in Appcues; first segments and Dashboards live", "Required", 3),
        ("Verified on staging and production", "Required", 1),
    ],
}

# Appcues' internal "Definition of Installed" (Customer Experience, Oct 2026):
# Installed = SDK initialized for each environment AND users and accounts identified AND objectives
# defined (with AI Agent context) AND integration workstream established AND the data being sent is
# used for targeting and analytics AND Key Moments can measure progress against objectives.
INSTALLED_PILLARS = [
    ("1. SDK initialized in every environment",
     "Page tracking and refined selectors on web; screens, deep links, element labels and FrameViews on mobile; "
     "traces / chats for agents."),
    ("2. Users and accounts identified",
     "Stable user ID and account ID, matching the IDs in your CRM and other tools."),
    ("3. Objectives mapped and defined",
     "Your business objectives are written down in Appcues, giving Appcues the context it needs."),
    ("4. Integration workstream established",
     "CRM, CDP, data warehouse / lake and MCP connections planned, owned and connected."),
    ("5. Data in use, not just collected",
     "Every event and property you send is used in a live segment, experience or Dashboard."),
    ("6. Key Moments measure what matters",
     "The events behind each Key Moment exist, so campaigns and tactics can be judged against your objectives."),
]

# ---------------------------------------------------------------- low-level helpers
def blank(v):
    return v is None or (isinstance(v, str) and v.strip() in ("", "TBD", "tbd", "?"))


def shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    for old in tcPr.findall(qn("w:shd")):
        tcPr.remove(old)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def cell_margins(table, top=70, bottom=70, left=100, right=100):
    tblPr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for side, val in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)


def table_borders(table, color=MORTAR, size=4):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)


def no_borders(table):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "nil")
        borders.append(el)
    tblPr.append(borders)


def set_col_widths(table, widths):
    """Fixed layout + explicit grid so Word, LibreOffice and Google Docs all honor widths."""
    table.autofit = False
    tbl = table._tbl
    tblPr = tbl.tblPr
    for old in tblPr.findall(qn("w:tblLayout")):
        tblPr.remove(old)
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblPr.append(lay)
    for old in tblPr.findall(qn("w:tblW")):
        tblPr.remove(old)
    tw = OxmlElement("w:tblW")
    tw.set(qn("w:w"), str(int(sum(widths) * 1440)))
    tw.set(qn("w:type"), "dxa")
    tblPr.append(tw)
    grid = tbl.tblGrid
    for gc in list(grid):
        grid.remove(gc)
    for w in widths:
        gc = OxmlElement("w:gridCol")
        gc.set(qn("w:w"), str(int(w * 1440)))
        grid.append(gc)
    for row in table.rows:
        for i, w in enumerate(widths):
            if i < len(row.cells):
                row.cells[i].width = Inches(w)


def repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def run_fmt(run, size=10, bold=False, color=BODY, font=BODY_FONT, italic=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = font
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    run.font.color.rgb = RGBColor.from_string(color)
    return run


def write_cell(cell, text, size=9, bold=False, color=BODY, font=BODY_FONT, italic=False, align=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    if align:
        p.alignment = align
    lines = str(text).split("\n") if text is not None else [""]
    for i, line in enumerate(lines):
        if i:
            p = cell.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
        run_fmt(p.add_run(line), size=size, bold=bold, color=color, font=font, italic=italic)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP


def fmt_val(v):
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, list):
        return ", ".join(str(x) for x in v if not blank(x))
    return "" if v is None else str(v)


OWNER_FILL = {"customer": PETAL, "developer": GLACIER, "appcues": THISTLE}


# ---------------------------------------------------------------- doc building blocks
class Plan:
    def __init__(self, data):
        self.d = data
        self.doc = Document()
        self._setup()

    def _setup(self):
        sec = self.doc.sections[0]
        sec.page_width, sec.page_height = Inches(8.5), Inches(11)
        sec.left_margin = sec.right_margin = Inches(0.7)
        sec.top_margin = Inches(0.6)
        sec.bottom_margin = Inches(0.6)
        st = self.doc.styles["Normal"]
        st.font.name = BODY_FONT
        st.font.size = Pt(10)
        st.font.color.rgb = RGBColor.from_string(BODY)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
        st.paragraph_format.space_after = Pt(4)
        st.paragraph_format.line_spacing = 1.15
        for lvl, size, color in ((1, 20, AUBERGINE), (2, 13, AUBERGINE), (3, 11, ORCHID)):
            h = self.doc.styles[f"Heading {lvl}"]
            h.font.name = HEAD_FONT
            h.font.size = Pt(size)
            h.font.bold = lvl != 3
            h.font.color.rgb = RGBColor.from_string(color)
            rpr = h.element.get_or_add_rPr()
            rpr.rFonts.set(qn("w:ascii"), HEAD_FONT)
            rpr.rFonts.set(qn("w:hAnsi"), HEAD_FONT)
            rpr.rFonts.set(qn("w:eastAsia"), HEAD_FONT)
            h.paragraph_format.space_before = Pt(14 if lvl == 1 else 10)
            h.paragraph_format.space_after = Pt(4)
            h.paragraph_format.keep_with_next = True
        # footer
        fp = sec.footer.paragraphs[0]
        meta = self.d.get("meta", {})
        run_fmt(fp.add_run(f"{meta.get('customer', 'Customer')}  ·  Appcues installation plan  ·  "
                           f"v{meta.get('version', '1.0')}  ·  {meta.get('date', date.today().isoformat())}"),
                size=8, color=MUTED)

    # -- text
    def h1(self, text, kicker=None):
        if kicker:
            p = self.doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.keep_with_next = True
            run_fmt(p.add_run(kicker.upper()), size=8, bold=True, color=ORCHID, font=HEAD_FONT)
        h = self.doc.add_heading(text, level=1)
        # amp-yellow underline accent
        pPr = h._p.get_or_add_pPr()
        bdr = OxmlElement("w:pBdr")
        b = OxmlElement("w:bottom")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "18")
        b.set(qn("w:space"), "4")
        b.set(qn("w:color"), AMP)
        bdr.append(b)
        pPr.append(bdr)
        return h

    def h2(self, text):
        return self.doc.add_heading(text, level=2)

    def h3(self, text):
        return self.doc.add_heading(text, level=3)

    def para(self, text, size=10, color=BODY, italic=False, bold=False):
        p = self.doc.add_paragraph()
        run_fmt(p.add_run(text), size=size, color=color, italic=italic, bold=bold)
        return p

    def bullets(self, items, size=10):
        for it in items:
            p = self.doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(2)
            run_fmt(p.add_run(str(it)), size=size)

    def page_break(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def callout(self, title, body, fill=BUTTER, bar=AMP):
        t = self.doc.add_table(rows=1, cols=2)
        no_borders(t)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        shade(t.rows[0].cells[0], bar)
        shade(t.rows[0].cells[1], fill)
        write_cell(t.rows[0].cells[0], "")
        c = t.rows[0].cells[1]
        c.text = ""
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        if title:
            run_fmt(p.add_run(title), size=10, bold=True, color=AUBERGINE, font=HEAD_FONT)
            p = c.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
        lines = body if isinstance(body, list) else [body]
        for i, line in enumerate(lines):
            if i:
                p = c.add_paragraph()
                p.paragraph_format.space_after = Pt(0)
            run_fmt(p.add_run(line), size=9.5)
        set_col_widths(t, [0.08, 7.0])
        cell_margins(t, 100, 100, 140, 140)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    # -- tables
    def table(self, headers, rows, widths, owners=None, min_blank_rows=0, size=8.5):
        """rows: list of lists. owners: list per column of 'customer'|'developer'|None
        used to shade blank cells so it is obvious who fills them in."""
        rows = list(rows)
        if not rows:  # one row to fill in; never pad tables that already have content
            rows = [[""] * len(headers)]
        t = self.doc.add_table(rows=1, cols=len(headers))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        table_borders(t)
        cell_margins(t)
        hdr = t.rows[0]
        repeat_header(hdr)
        for i, h in enumerate(headers):
            shade(hdr.cells[i], AUBERGINE)
            write_cell(hdr.cells[i], h, size=8.5, bold=True, color=WHITE, font=HEAD_FONT)
        for r in rows:
            cells = t.add_row().cells
            for i, v in enumerate(r):
                txt = fmt_val(v)
                own = owners[i] if owners and i < len(owners) else None
                if blank(txt) and own:
                    shade(cells[i], OWNER_FILL[own])
                    write_cell(cells[i], "", size=size)
                else:
                    write_cell(cells[i], txt, size=size,
                               bold=(i == 0), color=AUBERGINE if i == 0 else BODY)
        set_col_widths(t, widths)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)
        return t

    def kv_table(self, items, widths=(2.0, 2.6, 2.5), headers=("Item", "Answer", "Notes")):
        """items: dicts with item, answer, notes, owner"""
        rows, owners_per_row = [], []
        t = self.doc.add_table(rows=1, cols=3)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        table_borders(t)
        cell_margins(t)
        repeat_header(t.rows[0])
        for i, h in enumerate(headers):
            shade(t.rows[0].cells[i], AUBERGINE)
            write_cell(t.rows[0].cells[i], h, size=8.5, bold=True, color=WHITE, font=HEAD_FONT)
        for it in items:
            c = t.add_row().cells
            write_cell(c[0], it.get("item", ""), size=8.5, bold=True, color=AUBERGINE)
            ans = fmt_val(it.get("answer"))
            if blank(ans):
                shade(c[1], OWNER_FILL.get(it.get("owner", "customer"), PETAL))
                write_cell(c[1], "", size=8.5)
            else:
                write_cell(c[1], ans, size=8.5)
            write_cell(c[2], fmt_val(it.get("notes")), size=8, color=MUTED)
        set_col_widths(t, widths)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def legend(self):
        t = self.doc.add_table(rows=1, cols=6)
        no_borders(t)
        cells = t.rows[0].cells
        for i, (fill, label) in enumerate(((PETAL, "Your team fills this in"),
                                           (GLACIER, "Your developer fills this in"),
                                           (THISTLE, "Appcues fills this in"))):
            shade(cells[i * 2], fill)
            write_cell(cells[i * 2], "")
            write_cell(cells[i * 2 + 1], label, size=8.5, color=MUTED)
        set_col_widths(t, [0.3, 1.9, 0.3, 2.0, 0.3, 1.9])
        self.doc.add_paragraph().paragraph_format.space_after = Pt(0)

    # ---------------------------------------------------------------- sections
    def cover_band(self):
        m = self.d.get("meta", {})
        band = self.doc.add_table(rows=1, cols=1)
        no_borders(band)
        c = band.rows[0].cells[0]
        shade(c, AUBERGINE)
        c.text = ""
        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(18)
        run_fmt(p.add_run("APPCUES  ·  INSTALLATION PLAN"), size=9, bold=True, color=AMP, font=HEAD_FONT)
        p = c.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        run_fmt(p.add_run(m.get("customer", "Customer")), size=30, bold=True, color=WHITE, font=HEAD_FONT)
        p = c.add_paragraph()
        run_fmt(p.add_run(m.get("subtitle", "Getting your data foundation right the first time")),
                size=13, color=THISTLE, font=HEAD_FONT)
        p = c.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(18)
        bits = [f"Prepared {m.get('date', date.today().isoformat())}"]
        if m.get("target_go_live"):
            bits.append(f"Target go-live {m['target_go_live']}")
        if m.get("stage"):
            bits.append(m["stage"])
        run_fmt(p.add_run("   ·   ".join(bits)), size=9.5, color=WHITE)
        cell_margins(band, 200, 200, 360, 360)
        set_col_widths(band, [7.1])
        self.doc.add_paragraph()

    def cover(self):
        self.cover_band()
        self.para("Shaded cells still need an answer - pink for your team, blue for your developer, purple for "
                  "Appcues. Keep this document after go-live: new properties, events and integrations go here first.",
                  size=9, color=MUTED)

    # Small helpers so sections only render what has content -----------------------
    def _decisions(self):
        """Hard-to-undo decisions plus identity items, de-duplicated (they used to appear twice)."""
        import re
        s = self.d.get("summary", {})
        kd = [dict(k) for k in s.get("key_decisions", [])]
        norm = lambda t: re.sub(r"\(.*?\)", "", str(t).lower()).replace("  ", " ").strip()
        names = [norm(k.get("decision", "")) for k in kd]
        for it in self.d.get("identity", []):
            label = it.get("item", "")
            if any(n and n in norm(label) for n in names):
                # fold the identity answer/notes into the matching decision if it has none
                for k in kd:
                    if norm(k.get("decision", "")) in norm(label):
                        if blank(k.get("answer")) and not blank(it.get("answer")):
                            k["answer"] = it.get("answer")
                continue
            owner_label = {"developer": "Developer", "appcues": "Appcues"}.get(it.get("owner", ""), "")
            kd.append({"decision": label, "answer": it.get("answer"), "why": it.get("notes", ""),
                       "owner": it.get("owner_name") or owner_label})
        return kd

    def team(self):
        m = self.d.get("meta", {})
        people = [[p.get("name", ""), p.get("role", ""), m.get("customer", "")] for p in m.get("customer_team", [])]
        people += [[p.get("name", ""), p.get("role", ""), "Appcues"] for p in m.get("appcues_team", [])]
        if people:
            self.h2("Who's involved")
            self.table(["Name", "Role", "Company"], people, [2.0, 3.6, 1.5], owners=["customer", "customer", None])

    def snapshot(self):
        m = self.d.get("meta", {})
        rows = []
        for it in self.d.get("account", []):
            ans, note = fmt_val(it.get("answer")), fmt_val(it.get("notes"))
            if blank(ans) and it.get("owner") == "developer":
                continue  # developer-only blanks live in the appendix checklist, not the summary
            rows.append({"item": it.get("item", ""), "answer": ans if blank(note) or blank(ans) else f"{ans} ({note})",
                         "owner": it.get("owner", "customer")})
        def people(lst):
            def one(p):
                name, role = p.get("name"), p.get("role", "")
                if not name:
                    return f"{role} (name TBD)"
                return name if not role or role.lower() == "appcues" else f"{name} - {role}"
            return "; ".join(one(p) for p in lst)
        if m.get("customer_team"):
            rows.append({"item": f"{m.get('customer', 'Customer')} team", "answer": people(m["customer_team"])})
        if m.get("appcues_team"):
            rows.append({"item": "Appcues team", "answer": people(m["appcues_team"])})
        if rows:
            self.h2("Snapshot")
            self.table(["What", "Details"], [[r["item"], r["answer"]] for r in rows], [2.1, 5.0],
                       owners=[None, "customer"])

    # 01 -------------------------------------------------------------------------------
    def summary(self):
        s = self.d.get("summary", {})
        self.h1("Plan at a glance", self._secnum())
        if s.get("overview"):
            self.para(s["overview"])
        if s.get("headline_callout"):
            self.callout(s["headline_callout"].get("title", ""), s["headline_callout"].get("body", ""))
        self.snapshot()
        rd = s.get("readiness") or [{"area": a, "status": "yellow", "note": n} for a, n in INSTALLED_PILLARS]
        self.h2("Where we stand on \"Installed\"")
        self.para("Installed means Appcues can reach the right people and measure the outcomes you care about.",
                  size=9, color=MUTED)
        self.scorecard(rd)
        kd = self._decisions()
        if kd:
            self.h2("Decisions to make before install")
            self.table(["Decision", "Answer", "Why it matters", "Owner"],
                       [[k.get("decision"), k.get("answer"), k.get("why"), k.get("owner")] for k in kd],
                       [1.7, 1.7, 2.8, 0.9], owners=[None, "customer", None, "customer"])
        ns = self.d.get("next_steps", [])
        if ns:
            self.h2("Next steps")
            self.table(["Step", "Owner", "Due"], [[n.get("step"), n.get("owner"), n.get("due")] for n in ns],
                       [4.6, 1.5, 1.0], owners=[None, "customer", "customer"])

    # 02 -------------------------------------------------------------------------------
    def objectives(self):
        self.h1("Objectives, Key Moments and first launches", self._secnum())
        self.para("Objectives are what the business wants to move. Key Moments are the user actions that prove it's "
                  "moving - each one needs an event.", size=9, color=MUTED)
        ob = self.d.get("objectives", [])
        self.h2("Objectives")
        self.table(["Objective", "Why it matters", "Today → target", "Owner"],
                   [[o.get("objective"), o.get("why"), o.get("metric"), o.get("owner")] for o in ob],
                   [2.0, 2.5, 1.5, 1.1], owners=["customer"] * 4)
        km = self.d.get("key_moments", [])
        self.h2("Key Moments")
        self.table(["Key Moment", "Objective", "Event(s)", "Tracked today?"],
                   [[k.get("name"), k.get("objective"), k.get("events"), k.get("exists")] for k in km],
                   [1.9, 1.8, 2.2, 1.2], owners=["customer", "customer", "customer", "developer"])
        L = self.d.get("launches", [])
        self.h2("First launches")
        mobile = "Mobile" in self.platforms()
        hdr = ["#", "Who sees what, and when", "Moves", "Needs (properties / events)"]
        widths = [0.25, 3.15, 1.4, 2.3]
        rows = []
        for i, l in enumerate(L, 1):
            needs = "; ".join(x for x in (fmt_val(l.get("properties")), fmt_val(l.get("events")),
                                          ("screens: " + fmt_val(l.get("screens"))) if mobile and l.get("screens") else "")
                              if x)
            rows.append([str(i), l.get("sentence"), l.get("success_measure"), needs])
        self.table(hdr, rows, widths, owners=[None, "customer", "customer", "customer"])

    # 03 -------------------------------------------------------------------------------
    def data_foundation(self):
        self.h1("Data plan", self._secnum())
        self.para("Every row names where it will be used - a segment, an experience, a Dashboard or a Key Moment. "
                  "Events sent with track() count from the day they ship; there is no backfill. "
                  "Layer: Behavioral = what users do · Contextual = who / where / when · Attitudinal = why (surveys, NPS, chat).",
                  size=9, color=MUTED)
        hdr = ["Property", "What it's for", "Used in", "Layer", "Source", "Type"]
        w = [1.3, 1.85, 1.45, 0.85, 1.0, 0.65]
        own = [None, "customer", "customer", "customer", "customer", "developer"]
        up = self.d.get("user_properties", [])
        self.h2("User properties (identify)")
        self.table(hdr, [[p.get("name"), p.get("use"), p.get("used_in"), p.get("layer", "Contextual"), p.get("source"),
                          p.get("type")] for p in up], w, owners=own, size=8)
        ap = self.d.get("account_properties", [])
        if ap or self.d.get("has_accounts", True):
            self.h2("Account properties (group)")
            self.table(hdr, [[p.get("name"), p.get("use"), p.get("used_in"), p.get("layer", "Contextual"),
                              p.get("source"), p.get("type")] for p in ap], w, owners=own, size=8)
        ev = self.d.get("events", [])
        self.h2("Events")
        self.table(["Event", "Where it happens", "Platform", "How to send", "Used in", "Key Moment?"],
                   [[e.get("name"), e.get("where"), e.get("platform"), e.get("method"),
                     e.get("used_in") or e.get("powers"), e.get("key_moment")] for e in ev],
                   [1.5, 1.6, 0.75, 1.0, 1.45, 0.8],
                   owners=[None, "customer", "customer", "developer", "customer", "customer"], size=8)
        dash = self.d.get("measurement", {}).get("dashboards", []) or self.d.get("dashboards", [])
        self.h2("Dashboards for go-live")
        self.table(["Dashboard", "Question it answers", "Events", "Broken down by"],
                   [[x.get("name"), x.get("question"), x.get("events"), x.get("breakdown")] for x in dash],
                   [1.5, 2.6, 1.6, 1.4], owners=["customer"] * 4)

    # 04 -------------------------------------------------------------------------------
    def crm(self):
        c = self.d.get("crm", {})
        self.h1("CRM and integrations", self._secnum())
        self.para("Syncing the CRM fields marketing already uses turns them into reusable segments - no engineering "
                  "ticket per campaign. It only works if the CRM record holds the same user and account IDs sent to Appcues.",
                  size=9, color=MUTED)
        items = c.get("items") or [{"item": x, "answer": "", "owner": "customer"} for x in
                                   ("CRM system", "CRM admin", "Field holding the Appcues user ID",
                                    "Field holding the Appcues account ID")]
        self.h2("CRM connection" + (f" - {c['system']}" if c.get("system") else ""))
        self.kv_table(items)
        fm = c.get("field_mapping", [])
        self.h2("Fields to sync into Appcues")
        self.table(["CRM object", "CRM field", "Appcues property", "Level", "Used for"],
                   [[f.get("object"), f.get("field"), f.get("property"), f.get("level"), f.get("use")] for f in fm],
                   [1.1, 1.6, 1.4, 0.75, 2.25], owners=["customer"] * 5)
        au = c.get("audiences", [])
        if au:
            self.h2("Reusable audiences")
            self.table(["Segment", "Conditions", "Used for"],
                       [[a.get("name"), a.get("conditions"), a.get("use")] for a in au], [1.9, 3.0, 2.2])
        do = c.get("data_out", [])
        if do:
            self.h3("Sending Appcues data back to the CRM")
            self.bullets(do, size=9)
        ints = self.d.get("integrations", [])
        if ints:
            self.h2("Other tools")
            self.table(["Tool", "Type", "Direction", "What it's for", "ID that must match", "Owner"],
                       [[i.get("tool"), i.get("category"), i.get("direction"), i.get("purpose"), i.get("id_match"),
                         i.get("owner")] for i in ints],
                       [1.1, 0.85, 0.75, 1.85, 1.65, 0.9], owners=[None, None, "customer", None, None, "customer"], size=8)

    # 05 -------------------------------------------------------------------------------
    def environments(self):
        plats = self.platforms()
        tw = self.d.get("targeting_web", [])
        mo = self.d.get("mobile", {})
        tm = self.d.get("targeting_mobile", [])
        a = self.d.get("agents", {})
        self.h1("Environments", self._secnum())
        if "Web" in plats:
            self.h2("Web: elements your launches attach to")
            self.para("Give each a stable data-appcues attribute. Auto-generated class names change on the next build and "
                      "content silently stops appearing.", size=9, color=MUTED)
            self.table(["Element", "Where it is", "Attribute to add"],
                       [[t.get("element"), t.get("where"), t.get("attribute")] for t in tw],
                       [2.2, 2.4, 2.5], owners=["customer", "customer", "developer"])
        if "Mobile" in plats:
            self.h2("Mobile")
            sc = mo.get("screens", [])
            self.table(["Screen name", "What the user is looking at", "App"],
                       [[x.get("name"), x.get("description"), x.get("app")] for x in sc], [2.0, 3.6, 1.5],
                       owners=["customer", "customer", "customer"])
            items = mo.get("items") or [{"item": x, "answer": "", "owner": "developer"} for x in
                                        ("App IDs (dev / prod)", "URL scheme / deep link",
                                         "Screens hosting Embeds (FrameViews)", "Next release date")]
            self.kv_table(items)
            if tm:
                self.table(["Anchored element", "Screen", "Identifier"],
                           [[t.get("element"), t.get("screen"), t.get("identifier")] for t in tm], [2.2, 2.4, 2.5])
        self.h2("AI assistant and chat" if self.customer_mode() else "Agent and chat")
        if self.customer_mode():
            self.para("If your product has an AI assistant or chat, note it here so your Appcues team can plan "
                      "around it. Nothing to build for this install.", size=9, color=MUTED)
        else:
            self.para("Agents are the third environment Appcues runs in. Chat transcripts are the best source of "
                      "attitudinal data. Appcues will scope this with you - nothing to build yet.", size=9, color=MUTED)
        items = a.get("items") or [{"item": x, "answer": "", "owner": "customer"} for x in
                                   ("Do you have an agent or chat surface in your product?", "In-house or vendor?",
                                    "Can traces / transcripts be exported?")]
        self.kv_table(items)

    # 06 -------------------------------------------------------------------------------
    def open_questions(self):
        oq = self.d.get("open_questions", [])
        if not oq:
            return
        self.h1("Open questions", self._secnum())
        self.table(["Question", "Why it matters", "Owner", "Due"],
                   [[q.get("question"), q.get("why"), q.get("owner"), q.get("due")] for q in oq],
                   [3.0, 2.2, 1.1, 0.8], owners=[None, None, "customer", "customer"])

    # Appendix ---------------------------------------------------------------------------
    def checklist(self):
        self.page_break()
        self.h1("For your developer" if self.customer_mode() else "Developer appendix", "APPENDIX")
        self.para("Steps in order. The Pillar column shows which part of \"Installed\" each step completes - "
                  "when every row is done, you're Installed.", size=9, color=MUTED)
        rows = []
        for plat in self.platforms():
            rows += [[plat, step, req, str(pil), ""] for step, req, pil in CHECKLIST.get(plat, [])]
        for x in self.d.get("checklist_extra", []):
            rows.append([x.get("platform", ""), x.get("component", ""), x.get("required", ""), str(x.get("pillar", "")), ""])
        rows += [["All", step, req, str(pil), ""] for step, req, pil in CHECKLIST["All"]]
        self.table(["Env.", "Step", "Required?", "Pillar", "Done?"], rows, [0.6, 4.2, 1.1, 0.55, 0.65],
                   owners=[None, None, None, None, "developer"], size=8)
        self.h3("Docs")
        self.references(self.d.get("docs") or self.default_docs())

    def scorecard(self, rd):
        t = self.doc.add_table(rows=1, cols=3)
        table_borders(t)
        cell_margins(t)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, h in enumerate(("Area", "Status", "What's needed")):
            shade(t.rows[0].cells[i], AUBERGINE)
            write_cell(t.rows[0].cells[i], h, size=8.5, bold=True, color=WHITE, font=HEAD_FONT)
        for r in rd:
            c = t.add_row().cells
            write_cell(c[0], self._area(r.get("area", "")), size=9, bold=True, color=AUBERGINE)
            col, label = self._status(r.get("status", "yellow"))
            write_cell(c[1], "●  " + r.get("label", label), size=8.5, bold=True, color=col)
            write_cell(c[2], r.get("note", ""), size=8.5)
        set_col_widths(t, [1.9, 1.5, 3.7])
        self.doc.add_paragraph()

    def references(self, refs):
        for name in refs:
            url = DOCS.get(name, name)
            p = self.doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(1)
            run_fmt(p.add_run(f"{name}: "), size=9, bold=True, color=AUBERGINE)
            run_fmt(p.add_run(url), size=9, color=ORCHID)

    def customer_mode(self):
        return self.d.get("meta", {}).get("audience") == "customer"

    def _area(self, area):
        """Plain-language pillar names for customer-facing plans."""
        a = str(area or "")
        if self.customer_mode() and a[:1] in CUSTOMER_PILLARS:
            return CUSTOMER_PILLARS[a[:1]]
        return a

    def _status(self, key):
        col, label = STATUS.get(key, STATUS["yellow"])
        if self.customer_mode():
            label = CUSTOMER_STATUS.get(key, label)
        return col, label

    def default_docs(self):
        base = ["Install Appcues without rework", "Match user IDs across integrations"]
        if "Web" in self.platforms():
            base += ["Install the web SDK", "Preparing your frontend for targeting"]
        if "Mobile" in self.platforms():
            base += ["Register your mobile app", "Install the mobile SDK"]
        crm = (self.d.get("crm", {}).get("system") or "").lower()
        for k in ("Salesforce", "HubSpot", "Marketo"):
            if k.lower() in crm:
                base.append(f"{k} integration")
        for i in self.d.get("integrations", []):
            for k in ("Segment", "Hightouch", "Census"):
                if k.lower() in str(i.get("tool", "")).lower():
                    base.append(f"{k} integration")
        return list(dict.fromkeys(base))[:7]

    def platforms(self):
        p = self.d.get("meta", {}).get("platforms") or ["Web"]
        out = []
        for x in p:
            x = x.strip().lower()
            if x.startswith("web"):
                out.append("Web")
            elif x.startswith("mob") or x in ("ios", "android", "react native", "flutter", "ionic"):
                out.append("Mobile")
            elif x.startswith("agent") or x.startswith("chat"):
                out.append("Agent")
        return list(dict.fromkeys(out)) or ["Web"]

    def build(self, out):
        self.render_sections()
        self.doc.save(out)
        slim_docx(out)
        return out

    def _secnum(self):
        self._sec = getattr(self, "_sec", 0) + 1
        return f"{self._sec:02d}"

    def render_sections(self):
        self._sec = 0
        self.cover()
        self.summary()
        self.objectives()
        self.data_foundation()
        self.crm()
        self.environments()
        self.open_questions()
        self.checklist()


# ---------------------------------------------------------------- HTML (for Google Docs import)
def esc(s):
    import html
    return html.escape(str(s), quote=False)


# Class-only selectors: this is the form Google Docs itself exports, and it survives import.
CSS = f"""
.c{{border:0.75pt solid #{MORTAR};padding:4pt 5pt;vertical-align:top;font-family:'{BODY_FONT}';font-size:8.5pt;color:#{BODY}}}
.h{{background-color:#{AUBERGINE};color:#{WHITE};font-family:'{HEAD_FONT}';font-weight:bold}}
.k{{font-weight:bold;color:#{AUBERGINE}}}
.n{{font-size:8pt;color:#{MUTED}}}
.fp{{background-color:#{PETAL}}} .fg{{background-color:#{GLACIER}}} .ft{{background-color:#{THISTLE}}}
.x{{border:none}}
.t{{border-collapse:collapse;margin:0 0 8pt 0}}
.p{{font-family:'{BODY_FONT}';font-size:10pt;color:#{BODY};margin:0 0 5pt 0}}
.s{{font-family:'{BODY_FONT}';font-size:9.5pt;color:#{MUTED};margin:0 0 5pt 0}}
.i{{font-style:italic;font-size:8.5pt}}
.li{{font-family:'{BODY_FONT}';font-size:9.5pt;color:#{BODY}}}
.kk{{font-family:'{HEAD_FONT}';font-size:8pt;font-weight:bold;color:#{ORCHID};margin:14pt 0 0 0}}
.h1{{font-family:'{HEAD_FONT}';font-size:20pt;font-weight:bold;color:#{AUBERGINE};margin:2pt 0 6pt 0;border-bottom:2.25pt solid #{AMP};padding-bottom:3pt}}
.h2{{font-family:'{HEAD_FONT}';font-size:13pt;font-weight:bold;color:#{AUBERGINE};margin:10pt 0 4pt 0}}
.h3{{font-family:'{HEAD_FONT}';font-size:11pt;color:#{ORCHID};margin:8pt 0 3pt 0}}
.ct{{font-family:'{HEAD_FONT}';font-size:10pt;font-weight:bold;color:#{AUBERGINE};margin:0 0 3pt 0}}
.cb{{font-family:'{BODY_FONT}';font-size:9.5pt;color:#{BODY};margin:0 0 2pt 0}}
"""
FILL_CLASS = {PETAL: "fp", GLACIER: "fg", THISTLE: "ft"}


class HtmlPlan(Plan):
    """Same sections and content as the .docx, emitted as compact class-styled HTML.
    Upload with Drive create_file (textContent, contentMimeType text/html) and Drive
    converts it into a native Google Doc that keeps the brand colors, fonts and shading.
    Plain text is far safer to pass through a tool call than base64."""

    def __init__(self, data):
        self.d = data
        self.out = []

    def _w(self, s):
        self.out.append(s)

    def h1(self, text, kicker=None):
        if kicker:
            self._w(f'<p class="kk">{esc(kicker)}</p>')
        self._w(f'<h1 class="h1">{esc(text)}</h1>')

    def h2(self, text):
        self._w(f'<h2 class="h2">{esc(text)}</h2>')

    def h3(self, text):
        self._w(f'<h3 class="h3">{esc(text)}</h3>')

    def para(self, text, size=10, color=BODY, italic=False, bold=False):
        cls = "s" if color == MUTED else "p"
        if italic:
            cls += " i"
        t = f"<b>{esc(text)}</b>" if bold else esc(text)
        self._w(f'<p class="{cls}">{t}</p>')

    def bullets(self, items, size=10):
        self._w("<ul>" + "".join(f'<li class="li">{esc(i)}</li>' for i in items) + "</ul>")

    def page_break(self):
        self._w('<hr style="page-break-before:always;display:none">')

    def _td(self, text, width=None, cls=""):
        w = f' style="width:{width}in"' if width else ""
        body = "<br>".join(esc(x) for x in str(text).split("\n")) if text not in (None, "") else ""
        return f'<td class="c {cls}"{w}>{body}</td>'

    def _table(self, header, body_rows, widths):
        hdr = "".join(self._td(h, widths[i], "h") for i, h in enumerate(header))
        self._w(f'<table class="t" style="width:{sum(widths):.2f}in"><tr>{hdr}</tr>'
                + "".join(f"<tr>{r}</tr>" for r in body_rows) + "</table>")

    def callout(self, title, body, fill=BUTTER, bar=AMP):
        lines = body if isinstance(body, list) else [body]
        inner = f'<p class="ct">{esc(title)}</p>' if title else ""
        inner += "".join(f'<p class="cb">{esc(l)}</p>' for l in lines)
        self._w(f'<table class="t" style="width:7.1in"><tr>'
                f'<td class="x" style="width:0.08in;background-color:#{bar}"></td>'
                f'<td class="x" style="background-color:#{fill};padding:6pt 9pt">{inner}</td></tr></table>')

    def table(self, headers, rows, widths, owners=None, min_blank_rows=0, size=8.5):
        rows = list(rows)
        if not rows:  # one row to fill in; never pad tables that already have content
            rows = [[""] * len(headers)]
        out = []
        for r in rows:
            cells = []
            for i, v in enumerate(r):
                txt = fmt_val(v)
                own = owners[i] if owners and i < len(owners) else None
                w = widths[i] if i < len(widths) else None
                if blank(txt) and own:
                    cells.append(self._td("", w, FILL_CLASS[OWNER_FILL[own]]))
                else:
                    cells.append(self._td(txt, w, "k" if i == 0 else ""))
            out.append("".join(cells))
        self._table(headers, out, widths)

    def kv_table(self, items, widths=(2.0, 2.6, 2.5), headers=("Item", "Answer", "Notes")):
        out = []
        for it in items:
            ans = fmt_val(it.get("answer"))
            fill = FILL_CLASS[OWNER_FILL.get(it.get("owner", "customer"), PETAL)]
            a = self._td("", widths[1], fill) if blank(ans) else self._td(ans, widths[1])
            out.append(self._td(it.get("item", ""), widths[0], "k") + a + self._td(fmt_val(it.get("notes")), widths[2], "n"))
        self._table(headers, out, widths)

    def legend(self):
        cells = ""
        for fill, label in ((PETAL, "Your team fills this in"), (GLACIER, "Your developer fills this in"),
                            (THISTLE, "Appcues fills this in")):
            cells += (f'<td class="c x {FILL_CLASS[fill]}" style="width:0.3in"></td>'
                      f'<td class="c x n" style="width:1.9in">{esc(label)}</td>')
        self._w(f'<table class="t"><tr>{cells}</tr></table>')

    def cover_band(self):
        m = self.d.get("meta", {})
        bits = [f"Prepared {m.get('date', date.today().isoformat())}"]
        if m.get("target_go_live"):
            bits.append(f"Target go-live {m['target_go_live']}")
        if m.get("stage"):
            bits.append(m["stage"])
        sub = m.get("subtitle", "Getting your data foundation right the first time")
        self._w(
            f'<table class="t" style="width:7.1in"><tr><td class="x" style="background-color:#{AUBERGINE};padding:20pt 26pt">'
            f'<p style="margin:0;font-family:\'{HEAD_FONT}\';font-size:9pt;font-weight:bold;color:#{AMP}">APPCUES · INSTALLATION PLAN</p>'
            f'<p style="margin:10pt 0 0 0;font-family:\'{HEAD_FONT}\';font-size:30pt;font-weight:bold;color:#{WHITE}">{esc(m.get("customer", "Customer"))}</p>'
            f'<p style="margin:2pt 0 0 0;font-family:\'{HEAD_FONT}\';font-size:13pt;color:#{THISTLE}">{esc(sub)}</p>'
            f'<p style="margin:14pt 0 0 0;font-family:\'{BODY_FONT}\';font-size:9.5pt;color:#{WHITE}">{esc("   ·   ".join(bits))}</p>'
            f'</td></tr></table>')

    def scorecard(self, rd):
        out = []
        for r in rd:
            col, label = self._status(r.get("status", "yellow"))
            out.append(self._td(self._area(r.get("area", "")), 1.9, "k") +
                       f'<td class="c" style="width:1.5in;color:#{col};font-weight:bold">● {esc(r.get("label", label))}</td>' +
                       self._td(r.get("note", ""), 3.7))
        self._table(("Area", "Status", "What's needed"), out, [1.9, 1.5, 3.7])

    def references(self, refs):
        self._w("<ul>" + "".join(
            f'<li class="li"><b style="color:#{AUBERGINE}">{esc(n)}:</b> <a href="{esc(DOCS.get(n, n))}">{esc(DOCS.get(n, n))}</a></li>'
            for n in refs) + "</ul>")

    def build(self, out):
        self.render_sections()
        m = self.d.get("meta", {})
        title = f"{m.get('customer', 'Customer')} - Appcues Installation Plan"
        import re
        css = " ".join(CSS.split())
        body = "\n".join(self.out)
        # Column widths come from the header row; repeating them on every body cell only adds bytes.
        body = re.sub(r'(<td class="c (?!h")[^"]*") style="width:[\d.]+in"', r"\1", body)
        body = body.replace('class="c "', 'class="c"')
        html_doc = (f'<html><head><meta charset="utf-8"><title>{esc(title)}</title><style>{css}</style></head><body>'
                    + body + "</body></html>")
        with open(out, "w", encoding="utf8") as f:
            f.write(html_doc)
        return out


def slim_docx(path):
    """Drop parts of python-docx's default template that Google Docs ignores
    (stylesWithEffects, thumbnail, customXml, latent styles). Roughly halves the
    file, which matters because it is uploaded to Drive as base64."""
    import re
    import zipfile
    drop = {"word/stylesWithEffects.xml", "docProps/thumbnail.jpeg"}
    tmp = path + ".tmp"
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            name = item.filename
            if name in drop or name.startswith("customXml/"):
                continue
            data = zin.read(name)
            if name == "[Content_Types].xml":
                s = data.decode("utf8")
                s = re.sub(r'<Override PartName="/(word/stylesWithEffects\.xml|docProps/thumbnail\.jpeg|customXml/[^"]+)"[^>]*/>', "", s)
                s = re.sub(r'<Default Extension="jpeg"[^>]*/>', "", s)
                data = s.encode("utf8")
            elif name in ("_rels/.rels", "word/_rels/document.xml.rels"):
                s = data.decode("utf8")
                s = re.sub(r'<Relationship [^>]*Target="[^"]*(stylesWithEffects\.xml|thumbnail\.jpeg|customXml/[^"]+)"[^>]*/>', "", s)
                data = s.encode("utf8")
            elif name == "word/styles.xml":
                s = data.decode("utf8")
                s = re.sub(r"<w:latentStyles.*?</w:latentStyles>", "", s, flags=re.S)
                data = s.encode("utf8")
            zout.writestr(item, data)
    os.replace(tmp, path)


def to_pdf(docx_path):
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        print("LibreOffice not found; skipping PDF", file=sys.stderr)
        return None
    outdir = os.path.dirname(os.path.abspath(docx_path))
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", outdir, docx_path],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    pdf = os.path.splitext(docx_path)[0] + ".pdf"
    return pdf if os.path.exists(pdf) else None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("plan_json")
    ap.add_argument("--out", required=True, help="output .docx path")
    ap.add_argument("--pdf", action="store_true", help="also render a local PDF via LibreOffice")
    ap.add_argument("--html", action="store_true",
                    help="also write a .html next to the .docx for Google Docs import (Drive create_file, text/html)")
    a = ap.parse_args()
    with open(a.plan_json) as f:
        data = json.load(f)
    out = Plan(data).build(a.out)
    print("DOCX:", out)
    if a.html:
        print("HTML:", HtmlPlan(data).build(os.path.splitext(a.out)[0] + ".html"))
    if a.pdf:
        print("PDF:", to_pdf(out))
