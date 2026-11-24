# Using the Appcues MCP server (optional)

Check whether tools named like `mcp__*Appcues*__get_installation_status` are available. If they aren't, skip everything here and use the manual steps in `verification.md`. Never tell the user the MCP is required.

All **read** tools are safe to call without asking. **Every write needs explicit user confirmation** of the exact payload. Show what you'll create, then wait for a yes.

## Read: confirm you're pointed at the right account

- `get_appcues_account` → returns the account ID, name and domains. Compare the ID to the install spec's Appcues Account ID. If they differ, stop and ask: the MCP may be connected to a different (for example sandbox) account than the one being installed.
- `list_apps` (mobile) → find the registered mobile app and its Application ID for the platform you're installing. If none exists, tell the user to add the app in Studio → Settings → Mobile Apps first.

## Read: verify the install (A3 / B3)

Data only appears after the user has run the app with the install live (new code deployed, or the CDP/GTM setup published) and taken the actions.

1. `get_installation_status` → reports whether web or mobile SDK traffic is reaching the account.
2. `list_user_properties` with `attribute_names: [<spec user props>]` and `return_metadata: true` → check that each property exists and its type looks right (a Date showing as a string means it's being sent in the wrong format). `first_seen_within_days: 1` surfaces new arrivals.
3. `list_group_properties` the same way, for group props.
4. `list_events` with `source: "application"` and `search_term` per event → confirm that each code-tracked event name appears **exactly** (watch for casing/spacing drift such as `ran_search` vs `Ran Search`).

Report this as a table: spec item · expected · seen in Appcues (✅ / ❌ not yet seen / ⚠️ type or name mismatch).

## Write (optional, after the install is verified)

Offer these as a final step. The user can decline all of them.

### No-code events ("Event Tracking (no code)" rows)
`create_click_to_track_event` needs a real **selector** and a real page URL. Use the `[data-appcues="…"]` attribute you added in code (for example `[data-appcues="upgrade-cta"]`) as the selector. Never invent selectors for elements you didn't tag. The event is created **disabled**: tell the user to review and enable it in the Event Builder. The name is permanent, so use the plan's exact event name.

### Key Moments
`create_key_moment` only accepts **events that already exist** in the account. So run it after the event has been sent at least once (confirm with `list_events`). Call `get_key_moment_schema` first if you need conditions (for example the plan's "Opened Web Platform with signupSource = extension" → event `Opened Web Platform` with an attribute or user-property condition). The slug is lowercase with underscores, for example `first_purchase`. Use the plan's Key Moment name.

### Objectives
`create_objective` attaches to an existing **campaign or tactic**. It isn't standalone. If the user has no campaign yet, don't create one just for this. Say that Objectives get set up with their Appcues team when they build their first campaign, and list the plan's objectives so they're ready.
