# Install via Segment (Track B: guided, no code changes)

Sources: docs.appcues.com/install-appcues-web/installing-with-segment [S1] · Segment catalog: twilio.com/docs/segment/connections/destinations/catalog/appcues [S2] · docs.appcues.com/integration-documents/segment-two-way-integration [S3] · docs.appcues.com/mobile-installation-overview/install-appcues-mobile-via-segment-device-mode-plugin [S4]

With Segment, the **Segment script loads Appcues for you**, and Segment's `identify`/`group`/`track`/`page` calls are forwarded to Appcues. You don't add the Appcues snippet. If an Appcues snippet or `@appcues/web-sdk` is *already* in the app, the developer must remove it before the destination goes live, or Appcues loads twice (double tracking, duplicate flows).

## Prerequisites (B1): check these before any setup step

Ask the user, or read the repo (read-only) if they want you to look. Each gap becomes a line in the **developer note**.

**1. Segment coverage and environments**
- Segment (Analytics.js / `@segment/analytics-next`) is on **every page** where Appcues content should appear [S1].
- Which **Segment sources** exist per environment (e.g. "Web – Staging", "Web – Production")? The plan asks for verification on staging *and* production, so the destination is added to each source.
- Is a **Segment Tracking Plan (Protocols)** blocking unplanned events or traits, or does a **consent tool** gate destinations? Either can silently drop Appcues data, so note them.

**2. What the app's Segment calls must contain**

| Segment call | Appcues requirement |
|---|---|
| `analytics.page()` | **Required** on every page load and SPA route change. Without it, Segment won't load Appcues [S1][S2]. On Segment installs, these `page()` calls handle SPA navigation; don't ask for `enableURLDetection` as well |
| `analytics.identify(userId, traits)` | **Required on every page load** (not just login), with `userId` = **the plan's user ID**. Traits become Appcues user properties: plan names, plan types |
| `analytics.group(groupId, traits)` | The plan's CRM account ID and group properties (if accounts) |
| `analytics.track(event, props)` | The plan's events, exact names, at the success point (see "Event semantics" in install-plan.md) |
| `analytics.reset()` | On logout |

Data rules that fail silently (full list in web-direct.md §4; use it only as a source for the developer note):
- Traits must be an object. A string creates one property per character [S1].
- No nested objects/arrays, never `""` (send `null` to clear), real booleans/numbers, and no trait named `userId`.
- Dates: Segment's spec expects **ISO 8601** for `createdAt`-style traits, and Appcues accepts ISO 8601, so recommend ISO strings on Segment installs.

**3. Segment-specific side effects to raise with the user, not decide for them**
- **The user ID isn't the plan's ID** (e.g. the app identifies by email): changing Segment's `userId` affects **every** Segment destination, not just Appcues. The user and their data owner must agree to the change. The alternative is updating the plan's user ID.
- **The ID is wrong today = don't enable in production yet.** If production sends the wrong ID, every user it creates in Appcues is keyed on that ID, and the history can't be merged later. Set the destination up on **staging only** (or leave it disabled) until the developer note ships, then enable production.
- **Excluding internal users**: skipping `identify` for them would also remove them from every other destination. Prefer a Segment **Destination Filter** on the Appcues destination (e.g. drop events where `traits.is_internal = true`), if their Segment plan includes it. Otherwise, ask the developer to send a trait the filter can use, or accept the trade-off.
- **An existing event has a different name** (e.g. the app sends `search_performed` and the plan says `Ran Search`): ask which way to go. Either the plan adopts the existing name (simplest, no code), or the developer adds the plan's name. Renaming an existing event breaks other tools' history.

**4. Things that live in the app's code** (developer note, only if the plan needs them): `data-appcues` attributes on the plan's elements (element-targeting.md), CSP directives (web-direct.md §8), and identity verification (web-direct.md §9: `window.AppcuesSettings.userIdSignature` set before Segment's identify fires).

## Web setup (B2): one step at a time, once per environment source

1. **Segment app → Connections → Sources →** the source for this environment (start with staging).
2. **Add Destination** → search "Appcues" → **Configure Appcues**.
3. Settings:
   - **Appcues Id** = the Appcues **Account ID** (Studio → Settings → Account). This enables the client-side destination, and it's all a web install needs [S1].
   - **API Key** (Legacy API key, Studio → Settings → API Keys): only if they also send **server-side** events through Segment. Optional.
4. **Destination Filter** for internal users, if agreed in B1.
5. **Enable** the destination, but only on sources whose data is already correct (see "don't enable in production yet" above). Analytics.js sources default to **device mode** for Appcues [S2], so Segment loads the Appcues SDK in the browser.
6. Repeat for the production source when it's ready.
7. EU accounts: the Segment destination doesn't document an EU setting. Ask the user to confirm EU support with their Appcues contact before going live, and flag it in the handoff.

## Mobile via Segment ("Appcues Mobile" destination) [S4]

1. Register the app(s) in Studio → Settings → Apps & Installation for the App ID(s).
2. Segment → Destinations → "**Appcues Mobile**" → configure with the **Account ID** and **App ID**. Use **one destination per App ID**.
3. The device-mode plugin has to be added to the app by their developer. Give them this in the developer note:
   - iOS (analytics-swift): SPM `https://github.com/appcues/segment-appcues-ios.git` from `5.0.0`, then `import SegmentAppcues` and `analytics.add(plugin: AppcuesDestination())`
   - Android (analytics-kotlin): `implementation 'com.appcues:segment-appcues:<latest_version>'`, then `analytics.add(plugin = AppcuesDestination(applicationContext))`
   - React Native: `npm install --save @appcues/segment-react-native @appcues/react-native`, `pod install`, then `segmentClient.add({ plugin: new AppcuesPlugin() })`
   - Flutter / Ionic: no Segment plugin, so Segment can't install Appcues here. Say so, and ask whether to switch to a direct mobile install (Track A, mobile.md).
4. The plugin handles SDK loading, identify, group, screens and events. The app **still needs the URL scheme / deep link setup** from mobile.md (required for preview and the debugger). Add that to the developer note too.

## Verify (B3)

Segment Source → **Debugger** shows identify/group/track/page with the right `userId`, traits and event names. Then run the Appcues Debugger (verification.md). Network: XHR to Segment and a WebSocket to Appcues [S3].

## Don't confuse

The **Appcues → Segment** (outbound) integration in Appcues' Integrations page sends Appcues flow events *into* Segment. It's a separate, optional step [S3]. Mention it in the handoff if the plan's Integrations section lists Segment as "Out" or "Both".
