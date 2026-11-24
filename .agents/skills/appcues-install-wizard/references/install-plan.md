# Reading the installation plan → install spec

The installation plan comes from the Appcues team's intake process. It usually arrives as a **PDF**, sometimes as a Google Doc / Word export, an HTML page or a **JSON** file (`<Customer>-install-plan.json`). Every format has the same sections. Your job is to turn it into one **install spec**, the single source of truth for the rest of the session.

## Reading each format

- **PDF / DOCX / HTML**: read the whole document. Tables carry the data. **Shaded or empty cells are unanswered.** The colors mean: pink = the customer's team, blue = their developer, purple = Appcues. A cell that's visually shaded but has text in it is answered.
- **JSON**: the keys map directly. `meta.platforms`, `account[]` (item/answer), `identity[]`, `has_accounts`, `user_properties[]`, `group_properties[]` (if present), `events[]` (name/where/platform/method), `targeting_web[]` (element/where/attribute), `targeting_mobile[]` / screens (if present), `crm`, `integrations[]`, `key_moments[]`, `objectives[]`, `launches[]`, `open_questions[]`. An empty string `""` means unanswered.
- **`[Draft]` marker** on a row (or `Draft` in a field): Appcues proposed it, and the customer hasn't confirmed it. Treat it as *proposed*. Ask once, in a batch, which Draft rows to implement as written, which to rename, and which to drop. Only include rows that change the install: properties, code events, no-code events and elements to tag. Draft Key Moments, launches, dashboards and segments are configured in Appcues later, so list them in the handoff instead. Two exceptions:
  - **Integration-sourced Draft rows** (`Source = Integration (…)`) never get code. Put them straight into "noted for CRM owner" and leave them out of the batch.
  - **Draft rows that other parts of the plan call required** (for example the Developer appendix says "Send signupSource and hasPurchased: Required for first launches", or the summary says "must send"): point out the conflict in the batch question and recommend implementing them.

## Where things live in the plan

| Spec field | PDF section | JSON key |
|---|---|---|
| Appcues Account ID | 01 Snapshot | `account[]` "Appcues Account ID" |
| Region (US/EU) | 01 Snapshot; Open questions | `account[]` "Data hosting region" |
| Environments / platforms | 01 Snapshot "Environments in scope" | `meta.platforms`, `account[]` "Environments in scope" |
| Install method (snippet / npm / Segment / GTM / RudderStack / mobile SDK) | 01 "Decisions to make before install" | `account[]` "Install method" |
| Web framework / SPA | Open questions / Developer appendix | `account[]` "Web framework" |
| User ID | Decisions → "User ID" | `identity[]` / `summary.key_decisions[]` |
| Account (group) ID | Decisions → "Account (group) ID" | `identity[]`; `has_accounts` |
| Identity verification | Decisions → "Identity verification" | `identity[]` / `key_decisions[]` |
| User properties | 03 "User properties (identify)" | `user_properties[]` |
| Group properties | 03 "Account properties (group)" | `group_properties[]` |
| Events | 03 "Events" (`How to send` = `track()` or "Event Tracking (no code)") | `events[]` (`method`) |
| Elements to tag | 05 "Web: elements your launches attach to" | `targeting_web[]` |
| Mobile screens | 05 (mobile section, when present) | `targeting_mobile[]` / `launches[].screens` |
| CRM / integrations | 04 | `crm`, `integrations[]` |
| Objectives / Key Moments | 02 | `objectives[]`, `key_moments[]` |
| Developer checklist | Appendix "Developer appendix" | (not in JSON, so use the baseline in SKILL.md "Final checklist") |

**Final checklist** = the plan's Developer appendix rows (they win, wording included) + any baseline rows from SKILL.md "Final checklist" that the appendix lacks. Rows for out-of-scope environments (e.g. Agent rows when there's no agent work) stay, marked "n/a – out of scope".

## Property `Source` column: what you install vs. what you don't

- `Source = Installation` → **you send it** from code (identify/group properties).
- `Source = Integration (Salesforce/HubSpot/…)` → **don't send it from code.** It arrives through the CRM integration. Note it for the handoff and don't instrument it.
- `Type` sets the value type: String, Number, Boolean or Date. Dates must be sent the way the SDK docs specify (see the platform reference).
- The `userId` / `groupId` rows in the property tables are **the identify()/group() IDs themselves**, not properties. Never send a property named `userId`, because Appcues warns against it.
- Installation-sourced properties with slashes or spaces in the plan name (e.g. `persona / role`) need a confirmed final name before coding. Ask.
- **Check that each Installation-sourced property has a writer.** If a property depends on a field nothing sets (e.g. `firstWebSessionAt` reads `user.first_web_session_at`, but no code ever sets it), segments like "is empty" stay true forever. Ask, and if it's unset, flag it as a backend follow-up.

## Event semantics

For each code event, decide *when exactly* it fires. Ask if the plan's "Where it happens" leaves it open, on both tracks (on Track B, it goes in the developer note).

- **"First …" events** (e.g. `Purchased First Plan`): fire only the first time. Prefer a server-provided flag (e.g. the checkout response says `firstPurchase: true`). Otherwise capture the prior client state *before* the action (`hasPurchased` was false), and note that client state can be stale across tabs.
- **Session/visit events** (e.g. `Opened Web Platform` / "first authenticated web session"): agree whether that's once ever (better as a date property like `firstWebSessionAt` set server-side), once per browser session, or every load. Default meaning of "once per browser session" on web: a `sessionStorage` flag (per tab, cleared when the tab closes), checked in a small helper in the Appcues wrapper and cleared on `reset()`. Say this definition out loud when you confirm.
- **Async jobs** (e.g. "Enrichment job completed"): if the API call only queues the job, fire where completion is observed (polling result, websocket message, job-status UI). If completion is only known server-side, say so; it can't be tracked client-side from this repo.
- **Parentheticals in Key Moments** (e.g. "Opened Web Platform (with signupSource = extension)"): read these as a **user-property condition** applied when the Key Moment is built in Appcues, not an event property, unless the plan's Events table lists the property on the event.
- **Events tied to out-of-scope surfaces** (e.g. `Ran Chat Task` while the agent/chat surface is "Appcues scopes this"): a plan-listed web `track()` event is in scope, even if the surface itself isn't. If its code can't be found in the repo, ask; don't drop it silently.

## The install spec (build this, then show it to the user)

```
Customer:            <name>
Platforms:           Web | iOS | Android | React Native | Flutter | …
Install method:      snippet | npm | Segment | GTM | RudderStack | <other CDP> | mobile SDK
Appcues Account ID:  <value | BLOCKING – unanswered>
Mobile App ID(s):    <value | n/a | BLOCKING>
Region:              US | EU | BLOCKING
User ID:             <description of the field, e.g. "internal user GUID"> | BLOCKING
Account/group ID:    <description> | none (has_accounts=false) | unanswered
Identity verification: yes | no | undecided
Exclude internal/test users: rule (e.g. user.is_internal, @company.com emails, test tenant) | not required
Track:               A (direct code → PR) | B (indirect, guided setup, no PR)
User properties:     name (type) – Draft? – source
Group properties:    name (type) – Draft? – source
Events (code):       "Exact Name" – where – Draft?
Events (no-code):    "Exact Name" – element/where  (→ Event Builder, not code)
Elements to tag:     data-appcues="value" – element – where
Integrations noted:  CRM … / Braze … (ID that must match)
Out of scope / later: e.g. Chrome extension pending decision; agent/chat surface (Appcues scopes this, so nothing to build)
Open questions:      the plan's open questions that affect code
```

## Blocking vs. non-blocking unknowns

**Blocking.** Don't write code until the user answers, or explicitly says to use a clearly marked placeholder:
- **Install method.** It decides the whole path.
- **User ID.** It can't change later, and a wrong choice splits user history.
- **Region (US/EU).** The bundle domain differs and is fixed at account creation.
- **Appcues Account ID.** The user finds it in Appcues Studio → Settings → Account (or the Installation page). If they don't have it yet, you *may* proceed with a single constant `APPCUES_ACCOUNT_ID` placeholder in one place, plus a loud TODO, but only with their OK.
- **Mobile Application ID** (mobile only). It's in Studio → Settings → Mobile Apps.

**Non-blocking.** Proceed, but list them in the handoff:
- Account/group ID undecided → skip `group()`, leave a TODO and flag it.
- Identity verification undecided → don't build it, and note it as a security follow-up.
- Draft properties/events the user hasn't confirmed → implement only the ones they confirm.
- Integration-sourced properties → no code. Note them for the CRM owner.
- Scope questions like "Chrome extension in v1?" → install only the environments that are confirmed.

Never invent a user ID field, an account ID, event names or property names. If the plan's event name is `Ran Search`, the code sends exactly `"Ran Search"`, with the same casing and spacing.

## No plan? Run the mini-intake

Ask these in **one** message (numbered so the user can answer quickly). Then build the spec from the answers:

1. Which app are we installing into: a web app (default) or a mobile app (iOS, Android, React Native, Flutter)?
2. How should Appcues load: directly in code (script snippet or npm), or through Segment, Google Tag Manager, RudderStack or another CDP?
3. Your Appcues Account ID (Studio → Settings), and for mobile, the Application ID.
4. Is your Appcues account hosted in the US or the EU?
5. What uniquely and permanently identifies a logged-in user (for example a database ID or GUID)? Avoid email if it can change.
6. Do users belong to accounts, companies or workspaces? If so, what's that ID? It should match your CRM's account ID.
7. Does your security team require identity verification (signed user IDs)?

A no-plan install is **minimal**: SDK + `identify()` (ID plus a few safe properties the user names, such as `createdAt`) + `group()` (if accounts) + `reset()` on logout + SPA URL detection. No custom events unless the user names them. At the end, recommend asking their Appcues contact for an installation plan, so that events, properties and Key Moments are chosen deliberately.
