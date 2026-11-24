# Install via RudderStack

Sources: rudderstack.com/docs/destinations/streaming-destinations/appcues/ [RS] · docs.appcues.com/integration-documents/rudderstack-integration [AC]

With the RudderStack web destination in **device mode**, RudderStack loads the Appcues SDK. You don't need the Appcues snippet or separate Appcues identify calls [AC].

## Before starting, check

- The RudderStack JS SDK (`@rudderstack/analytics-js` or the snippet) is on every page where Appcues content should show.
- `rudderanalytics.identify(userId, traits)` uses the **plan's user ID** and runs before every other call, on every page load [RS].
- **Mobile**: RudderStack's Appcues destination is **cloud mode only** for Android/iOS/React Native/Flutter sources [RS]. That forwards data but doesn't load the Appcues mobile SDK, so RudderStack can't install Appcues in a mobile app. Say so, and ask whether to switch to a direct mobile install (Track A, mobile.md).

- Separate staging and production **sources**? The destination goes on each. If the app's identify doesn't send the plan's user ID yet, enable it on **staging only** until the developer note ships: wrong IDs create Appcues users whose history can't be merged.
- Changing the RudderStack `userId` (e.g. from email to the plan's ID) affects every RudderStack destination. Raise it, don't decide it. The same goes for excluding internal users by skipping identify; prefer RudderStack's client-side event filtering or a transformation for the Appcues destination where possible.
- If the app already loads Appcues directly (snippet or `@appcues/web-sdk`), device mode would load it twice. The developer removes the direct install first.

## Web: step by step (once per environment source)

1. RudderStack dashboard → the web **source** → Add Destination → **Appcues** → name it → Continue.
2. Connection settings:
   - **Account ID** = Appcues Account ID (Studio → Settings → Account).
   - **Use device mode to send events** = **ON** (required for in-app content on web).
   - **Appcues JavaScript Native SDK URL**: the default is `https://fast.appcues.com/<account_id>.js`. **EU accounts**: change it to `https://fast.eu.appcues.com/<account_id>.js`.
   - Client-side event filtering: leave it off, or allowlist the plan's events.
3. Save. Enable only on sources whose data is already correct (see above).

## Call mapping [RS]

| RudderStack call | Device mode (web) | Notes |
|---|---|---|
| `identify` | ✅ | Must come first. Nested traits get flattened, but send flat values per the plan anyway |
| `track` | ✅ | Plan event names, exact |
| `page` | ✅ | Calls `Appcues.page()`. Call it on SPA route changes (or rely on the SDK's URL detection) |
| `group` | ⚠️ | **Docs conflict**: RudderStack's table marks group unsupported, while Appcues' doc lists it as supported. If the plan uses accounts, verify Group Identified in the Appcues Debugger. If it's missing, add a developer note item: call `window.Appcues?.group(accountId, props)` right after identify |
| `screen` | cloud only | Sent as a "Viewed a Screen" event |
| `reset` | n/a | Developer note: also call `window.Appcues?.reset()` on logout, to be safe |

**Prerequisites (B1):** the app's RudderStack calls need the same things as Segment's (see segment.md "Prerequisites"): identify on every page load, the plan's types and names, no `userId` trait, no `""`, and reset on logout. Check them (read-only) and put anything missing in the developer note.

## CSP

Allow `https://fast.appcues.com` (or the custom/EU SDK URL) in `script-src` [RS], plus the full Appcues list in web-direct.md §8.

## Verify

RudderStack → **Live Events** shows the payloads, then run the Appcues Debugger (verification.md).

## Outbound

The Appcues → RudderStack integration (Appcues Integrations page → RudderStack → Connect) sends Appcues events to RudderStack. It's separate and optional [AC].
