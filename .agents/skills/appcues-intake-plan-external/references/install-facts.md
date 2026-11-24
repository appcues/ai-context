# Install facts (from docs.appcues.com)

Use this to explain *why* in the plan's notes and to answer the customer's questions. If something here conflicts with docs.appcues.com, the docs win - check the linked page.

## What gets installed
- **Web:** SDK (snippet, NPM, Segment, or Google Tag Manager) → `identify()` → `group()` → `track()`. "Your installation is incomplete without event tracking." https://docs.appcues.com/installation-overview/appcues-installation-overview
- **Mobile:** register app in Studio (App IDs; separate dev/prod optional) → SDK + init with Account ID and App ID → `identify()` / `group()` → `screen()` → `track()` → URL scheme / deep linking (required for preview, debugging, screen capture) → Anchored Tooltip element recognition and FrameViews for Embeds. ~1 developer hour of code; the release train sets the timeline. https://docs.appcues.com/mobile-installation-overview/installing-the-mobile-sdk
- **AI assistant / chat:** record whether one exists and what it does; nothing to install.

## Mobile requirements
- iOS 13+ renders Flows (analytics from iOS 11). SPM, CocoaPods, XCFramework.
- Android API 21+, targetSDK 34+; SDK 5.0.0+ for edge-to-edge.
- React Native 0.73+ (Expo SDK 50+); compileSdk 35+, minSdk 21+.
- Flutter: `appcues_flutter` on pub.dev; compileSdk 35+, minSdk 21+.
- Ionic: Capacitor plugin; no FrameView setup needed.

## Hard-to-reverse decisions
- **User ID** - permanent and unique; opaque (UUID) recommended. A changed ID creates a new profile; histories never merge. Casing must be identical across tools.
- **Group ID** - should equal the CRM's account ID.
- **Anonymous users / reset()** - call `reset()` on logout unless using anonymous users.
- **Backfill** - `track()` starts when shipped; Event Tracking (web, no code) backfills click and text-input events to when raw event recording began; hover events and mobile events don't backfill.
- **Data path** - switching between direct / Segment / GTM later means redoing identify and track. Amplitude and Mixpanel must load before Appcues. Segment + Mixpanel integrations both on duplicates data.
- **Identity verification** - backend endpoint + shared secret; decide yes/no up front.
- **Screen names and FrameViews** (mobile) - screen names are a contract; FrameViews require a release.
- **Event naming** - different names per platform; matching names pool together.

## Things that break silently
- Types: `599` vs `"599"`; string sort puts "10" before "2".
- Dates: one format per property; seconds or ms, no decimals.
- Empty string is a real value - send `null` or omit.
- Don't send `userId` / `user_ID` as a property.
- Call order: `identify()` before `group()` and `track()`.
- Only strings, numbers, booleans - flatten arrays (`invoices.length`).
- Case sensitivity in values and event names.
- Internal/test users count toward MAU.
- Event Tracking (no-code click) events aren't forwarded to other tools by default - your Appcues team can confirm options. Flow button events are.
- Synced property names that don't exactly match create new properties.
- Auto-detected selectors on React/Ember break on the next build; Event Tracking selectors matching >10 elements can't be saved.
- CSP blocks SDK init (console error).
- EU accounts: `fast.eu.appcues.com`; NPM needs `bundleDomain`.
- `enableURLDetection` goes on `window.AppcuesSettings` before setup.
https://docs.appcues.com/installation-overview/install-appcues-without-rework

## ID matching by integration
https://docs.appcues.com/install-appcues-web/match-user-ids-across-integrations

| Integration | Requirement |
|---|---|
| Salesforce (two-way) | Appcues user ID must be a **Text** field value on Contact or Lead; account ID a Text field on the account-level object (any object, incl. custom). Numeric IDs → `TEXT()` formula field. |
| HubSpot | In: Appcues user ID stored on the HubSpot contact (and group ID on company). Out: HubSpot Contact ID or email must be an Appcues user property. |
| Marketo | In: Appcues user ID on the lead. Out: Marketo Lead ID or email as an Appcues property. |
| Segment | Same user ID flows through the CDP to all tools. |
| Amplitude | Appcues user ID exists as an Amplitude user property. |
| Mixpanel | Appcues user ID = Mixpanel distinct ID. |
| Heap | Appcues user ID on the Heap user profile. |
| Hightouch | Model user ID = `identify()` ID. |
| Census | Sync key = `identify()` ID. |

## CRM details
**Salesforce** - https://docs.appcues.com/en_US/integration-documents/salesforce-two-way-integration
- Bi-directional. One user-level object (Lead or Contact) and one account-level object.
- SF → Appcues every ~5 min, only changed mapped fields; formula and roll-up fields included. Missing users/accounts are created.
- Appcues → SF: NPS fields; activity for Flow completions, checklist completions, goals, NPS, survey Form Submitted. Forwarding Event Tracking events: your Appcues team can confirm options.
- Needs Enterprise / Unlimited / Developer / Performance edition with API access; permissions incl. API Enabled, Customize Application, Create/Edit/Read on Contact/Lead and Event. Optional integration-user license. Sandbox: swap `login` for `test`.
- Availability on your Appcues plan: your Appcues team will confirm.

**HubSpot** - https://docs.appcues.com/en_US/integration-documents/hubspot-integration
- Two-way: contact and company properties in; events to the contact timeline (V2 adds more types). Doesn't update contact properties except NPS.
- Initial sync 30 min after activation, then rolling 30-min cycle; 10,000-record cap per window. For time-sensitive targeting, send properties at install.
- Needs any paid HubSpot CRM plan; use the V2 card (disconnect legacy first). Availability on your Appcues plan: your Appcues team will confirm.

**Others** - Marketo, Intercom, Customer.io, Klaviyo, Vero (marketing automation); Hightouch, Census, Fivetran (warehouse); Amplitude, Mixpanel, Heap (two-way analytics); Appcues MCP server. https://docs.appcues.com/integrations

## Definition of done (docs) - folded into the plan's developer checklist
Web: Debugger green (Installed, Connected, Tracking Pages - stays green during navigation); properties with correct types; events on the Events page; CSP deployed; stable attributes on targeting elements; Event Tracking events saved.
Mobile: Mobile Debugger shows user, group, screens, events; deep linking works; element recognition; FrameViews; release scheduled.
Both: test users excluded; integrations connected with data visible both sides; selector/screen checks in code review; verified on staging and production.
