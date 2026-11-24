# Verifying the install

Sources: docs.appcues.com/dev-troubleshooting/installation-testing-debugging · /install-appcues-web/install-the-appcues-sdk · /install-appcues-web/track-events-in-your-web-app

Verification needs the app **running with the new code** and a real login. Ask the user to start it (`npm run dev`, staging deploy, simulator). You can offer to run the dev server yourself if the project makes that easy.

## Web: the Appcues Debugger

Walk the user through it one check at a time, and ask them to report what they see:

1. Log in to the app. Open the browser console and run `Appcues.debug()`. (Or right-click the Appcues Chrome extension icon → "Debug flows on this page".) Don't have the Appcues Builder open at the same time.
2. **Installed** and **Connected to Appcues** are green.
3. Navigate to 3–4 pages. **Tracking Pages** returns to green after each one. (A brief red flash during load is fine.)
4. **User Identified** shows the plan's user ID (not an email or internal DB key unless that's the plan's choice). Expand Details: every plan user property is present with sensible values. Dates should look like numbers or ISO strings, booleans should be true/false.
5. **Group Identified** shows the account ID and group properties (if the plan uses accounts).
6. Perform each code-tracked event from the plan. Then confirm in Studio → **Events Explorer** (https://studio.appcues.com/insights/explorer), Event Source = "Application Events", that each appears with a recent timestamp and the **exact** name. There's a short delay.
7. Log out → log back in as a different test user. The Debugger shows the new user (this confirms `reset()`).
8. Run `Appcues.debug(false)` to close the panel.

Integration-sourced properties (from Salesforce, HubSpot, etc.) do **not** show in the Debugger. Check them later in Studio → Settings → Properties once the integration is connected.

### Troubleshooting

| Symptom | Likely cause |
|---|---|
| `Appcues` is undefined / Debugger won't open | Script not on this page, wrong Account ID, wrong region domain, ad blocker, or CSP ("Refused to load the script" in console) |
| Tracking Pages stays red | `enableURLDetection` not set before the SDK loaded, or manual `page()` missing |
| Red right after adding identify | identify ran before the SDK loaded. Use the wrapper / `AppcuesReady` / await `setup()` |
| Properties named `0`, `1`, `2…` | A string was passed instead of an object (unparsed JSON) |
| Group missing | `group()` called before `identify()` |
| Event missing | `track()` before identify, name mismatch (case/spacing), or the code path didn't run |
| Date property shows as text | Wrong date format (use whole-number Unix timestamp or ISO 8601) |

Network check: DevTools → Network, filter "appcues". You should see requests to `fast.appcues.com` (or `fast.eu.appcues.com`) and `api.appcues.net`, plus a WebSocket.

## Mobile

See the "Verify" section of `mobile.md` (the debugger is launched via the app's URL scheme or deep link).

## Indirect installs (Segment / GTM / RudderStack)

Same Debugger checks. Also confirm in the CDP's own debugger (Segment Source Debugger, GTM Preview mode, RudderStack Live Events) that the identify/group/track payloads carry the plan's user ID, properties and exact event names, and that the Appcues destination shows deliveries.

## With the Appcues MCP

If Appcues MCP tools are available, also run the read checks in `appcues-mcp.md` and present the ✅/❌/⚠️ table.

## Done means

Every row in the install spec is ✅, or is explicitly listed in the handoff as pending with an owner and a reason.
