# Plan JSON schema

`scripts/build_plan.py` reads one JSON object. Every key is optional - missing sections render with blank fill-in rows so the skeleton is always complete. Any value that is `""`, `null`, `"TBD"` or `"?"` renders as a shaded fill-in cell. See `assets/example-plan.json` for a full example.

Owner values (`owner`) shade blank cells: `"customer"` (Petal - business team), `"developer"` (Glacier), `"appcues"` (Thistle). Default is customer.

```jsonc
{
  "meta": {
    "customer": "Acme",                 // cover + footer
    "subtitle": "...",                  // optional cover line
    "date": "YYYY-MM-DD", "version": "1.0", "stage": "Discovery draft",
    "target_go_live": "YYYY-MM-DD",
    "platforms": ["Web", "Mobile", "Agent"],   // drives which sections/checklists render
    "audience": "internal|customer",          // "customer" = friendlier status labels + "For your developer"
    "source": "customer self-serve",          // where the answers came from
    "customer_team": [{"name": "", "role": "", "email": ""}],
    "appcues_team":  [{"name": "", "role": "", "email": ""}]
  },
  "summary": {
    "overview": "2-4 sentence situation summary",
    "headline_callout": {"title": "The one thing to settle this week", "body": "..."},
    "readiness": [{"area": "1. SDK initialized in every environment", "status": "green|yellow|red|grey", "note": "..."}],  // all six pillars
    "key_decisions": [{"decision": "", "answer": "", "why": "", "owner": ""}]
  },
  "account":   [{"item": "", "answer": "", "notes": "", "owner": "customer|developer|appcues"}],
  "objectives":  [{"objective": "", "why": "", "metric": "today → target", "owner": ""}],
  "key_moments": [{"name": "", "objective": "", "events": "", "platform": "", "exists": ""}],
  "launches":    [{"sentence": "", "success_measure": "", "platform": "", "properties": "", "events": "", "screens": ""}],
  "identity":    [{"item": "", "answer": "", "notes": "", "owner": ""}],
  "has_accounts": true,
  "user_properties":    [{"name": "", "use": "", "used_in": "", "layer": "Behavioral|Contextual|Attitudinal", "source": "Installation|Integration (Tool)|API", "type": "String|Number|Boolean|Date"}],
  "account_properties": [ /* same shape */ ],
  "events": [{"name": "", "where": "", "platform": "", "method": "track()|Event Tracking (no code)", "used_in": "", "key_moment": "Yes|"}],
  "measurement": {"dashboards": [{"name": "", "question": "", "events": "", "breakdown": ""}]},
  "crm": {
    "system": "Salesforce|HubSpot|Marketo|...",   // also selects doc links
    "items": [{"item": "", "answer": "", "notes": "", "owner": ""}],
    "field_mapping": [{"object": "", "field": "", "property": "", "level": "User|Account", "use": ""}],
    "audiences": [{"name": "", "conditions": "", "use": ""}],
    "data_out": ["bullet", "..."]
  },
  "integrations": [{"tool": "", "category": "CDP|Warehouse|Analytics|MCP|Marketing|Support", "direction": "In|Out|Both", "purpose": "", "id_match": "", "owner": "", "status": ""}],
  "mobile": {
    "screens": [{"name": "", "description": "", "app": ""}],
    "items":   [{"item": "", "answer": "", "notes": "", "owner": "developer"}]
  },
  "targeting_web":    [{"element": "", "where": "", "attribute": "data-appcues=\"...\""}],
  "targeting_mobile": [{"element": "", "screen": "", "identifier": "", "added": ""}],
  "agents": {"items": [{"item": "", "answer": ""}], "notes": ""},
  "checklist_extra": [{"platform": "", "component": "", "required": "", "pillar": 1}],   // customer-specific steps; pillar = 1-6
  "open_questions": [{"question": "", "why": "", "owner": "", "due": ""}],
  "next_steps":     [{"step": "", "owner": "", "due": ""}],
  "docs": ["optional override list of doc names from DOCS in build_plan.py"]
}
```

Conventions:
- `[Suggested]` at the end of a name or sentence marks something Claude proposed that the customer hasn't confirmed. It renders as plain text. Before building the plan, resolve each one: confirm it (remove the marker), drop it, or turn it into an open question.
- The `userId` / `groupId` rows document the IDs passed as the first argument to `identify()` / `group()`. They are not extra properties, so don't also send `userId` as a property.
- `owner` on `identity` / `account` items is a key (`customer`, `developer`, `appcues`) that controls shading. The decisions table shows it as "Your team" / "Developer" / "Appcues" when no named owner is given.

Section order in the rendered doc (sections number themselves; empty optional parts are skipped):
- Cover band
- 01 Plan at a glance: overview, headline callout, Snapshot (`account` + team), "Installed" scorecard, decisions to make (`key_decisions` merged with `identity`), next steps
- 02 Objectives, Key Moments and first launches
- 03 Data plan: user properties, account properties, events, Dashboards
- 04 CRM and integrations: connection, field mapping, audiences, data out, other tools
- 05 Environments: web elements, mobile (if in scope), agent and chat
- 06 Open questions (if any)
- Developer appendix: ordered checklist tagged by "Installed" pillar (includes `checklist_extra`), plus up to 7 doc links
