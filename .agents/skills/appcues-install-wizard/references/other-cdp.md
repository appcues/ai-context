# Other CDPs and data tools

Source index: https://docs.appcues.com/en_US/integration-documents

Most "integrations" **send data into or out of** Appcues. They don't **install** Appcues. Only Segment and RudderStack (web device mode) actually load the Appcues SDK. For everything else, the SDK still has to be installed directly (web-direct.md / mobile.md) or via GTM. Sort out which case the user is in before doing anything.

| Tool | What it does with Appcues | Installs the SDK? | Doc |
|---|---|---|---|
| Segment | Loads the SDK + forwards calls (web device mode; mobile plugin) | ✅ | segment.md |
| RudderStack | Loads the SDK in web device mode; mobile is cloud-only | ✅ web only | rudderstack.md |
| Google Tag Manager | Tag manager loads the SDK | ✅ | gtm.md |
| Heap | Sends Heap **segment membership** into Appcues as `[Heap] <segment>` booleans. Events don't sync | ❌ | /integration-documents/heap-two-way-integration |
| Amplitude, Mixpanel | Two-way data sync | ❌ | /integration-documents/amplitude-two-way-integration, /mixpanel-two-way-integration |
| Hightouch, Census | Import warehouse data into Appcues (properties) | ❌ | /integration-documents/hightouch-integration, /census-integration |
| Fivetran | Data pipeline | ❌ | /integration-documents/fivetran-integration |
| Freshpaint | Outbound: Appcues flow data → analytics tools | ❌ | appcues.com/integrations/apps/freshpaint |
| Zapier | Both directions | ❌ | /integration-documents/using-appcues-and-zapier |
| mParticle, Tealium | No Appcues install doc found | ❓ | Ask the user to confirm with their Appcues contact. Meanwhile, install directly or via GTM |

## What to do

1. If the user's tool can't install the SDK: explain that in one line, and ask whether to install directly (Track A) or via GTM (Track B). Go back to SKILL.md Step 1 with their answer.
2. For every data-sync integration in the plan: the **ID that must match** column is the critical part. Most tools match on the identify() user ID (e.g. Heap needs a property holding the Appcues user ID; Mixpanel's distinct ID; Hightouch/Census sync key). Note each in the handoff with an owner. Don't configure third-party tools yourself.
3. If a tool isn't listed here, fetch the integration index above and look for it before saying it's unsupported.
