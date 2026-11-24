# Install via Google Tag Manager

Sources: docs.appcues.com/install-appcues-web/installing-with-google-tag-manager-developer [GTM] · docs.appcues.com/integration-documents/google-tag-manager-integration (outbound, different thing)

GTM loads the Appcues SDK and runs identify, group and track from tags. Everything below happens in the GTM UI. Walk the user through one step at a time, and wait for "done". The one dependency on the app's code is that **the user ID, properties and events must already be in the `dataLayer`**. You don't write that code; you check for it, and hand the developer a note if it's missing.

## Prerequisites (B1): the app's data layer

GTM can only identify users with data it can read. Ask the user (or read the repo, read-only, if they want you to look) whether the app already pushes the logged-in user to the `dataLayer` on **every page load**, and pushes the plan's events.

- **It does** → note the exact key and event names. Steps 2–4 use them instead of the suggested names below.
- **It doesn't** → give the user this **developer note** and carry on with the GTM setup. The tags start working once the developer ships it. The push should happen wherever the user becomes known, on every page load (web-direct.md §4 has the placement and type rules):

```js
window.dataLayer = window.dataLayer || [];
window.dataLayer.push({
  event: 'appcues_user_ready',          // custom trigger for the identify tag
  appcuesUserId: String(user.id),       // the plan's user ID
  appcuesAccountId: String(account.id), // the plan's account ID (if accounts)
  // plan properties, flat values only:
  createdAt: Math.floor(new Date(user.createdAt).getTime() / 1000),
  planTier: account.planTier,
});
```
Each code-tracked plan event, at its success point (exact plan name):
```js
window.dataLayer.push({ event: 'Ran Search' });
```
And on logout: `window.dataLayer.push({ event: 'appcues_logout' });`. Add the plan's `data-appcues` attributes (element-targeting.md) to the developer note too, if the plan lists elements.

The names `appcues_user_ready`, `appcuesUserId` and `appcues_logout` are suggestions. Follow any existing data-layer naming convention.

## Step 1: SDK tag

GTM → Tags → New → **Custom HTML** (the doc shows HTML script code but doesn't name the tag type; Custom HTML is the standard choice). Paste:
```html
<script type="text/javascript">
  window.AppcuesSettings = { enableURLDetection: true };
</script>
<script src="https://fast.appcues.com/YOUR_ACCOUNT_ID.js"></script>
```
(EU: `https://fast.eu.appcues.com/YOUR_ACCOUNT_ID.js`.) `enableURLDetection` handles SPA route changes [GTM]. Trigger: **All Pages** (Page View). Name it "Appcues – SDK".

## Step 2: Data Layer variables

GTM → Variables → New → **Data Layer Variable**, one per key in the data layer (see Prerequisites; `appcuesUserId`, `appcuesAccountId`, each property). Name them like `DLV – appcuesUserId`.

## Step 3: Identify (+ group) tag

Custom HTML:
```html
<script>
  if (window.Appcues && {{DLV - appcuesUserId}}) {
    Appcues.identify({{DLV - appcuesUserId}}, {
      createdAt: {{DLV - createdAt}},
      planTier: {{DLV - planTier}}
    });
    // if accounts:
    Appcues.group({{DLV - appcuesAccountId}}, { planTier: {{DLV - planTier}} });
  }
</script>
```
Trigger: **Custom Event** `appcues_user_ready`. Use the plan's exact property names. Never hardcode a test ID in production (the doc's `'testUserId'` example gives every user the same ID).

**Load-order safety** (from [GTM]'s async pattern): if the identify tag might fire before the SDK has loaded, use tag sequencing (Identify tag → Advanced Settings → Tag Sequencing → fire "Appcues – SDK" before). Alternatively, use the doc's two-tag async loader, which pushes `AppcuesLoaded` to the data layer when the script loads and fires identify on that event.

## Step 4: Event tags

For each code-tracked plan event, create a Custom HTML tag:
```html
<script>
  window.Appcues && Appcues.track('Ran Search');
</script>
```
Trigger: **Custom Event**, with the event name exactly as pushed (`Ran Search`). Name it "Appcues – Track – Ran Search". If there are many events, one tag can serve all of them: trigger it on a regex Custom Event matching the plan's event names, and call `Appcues.track({{Event}})` using GTM's built-in **Event** variable.

## Step 5: Logout tag

Custom HTML `<script>window.Appcues && Appcues.reset();</script>`, with trigger Custom Event `appcues_logout`.

## Step 6: Preview, then publish

GTM **Preview** → log in to the site → confirm the "Appcues – SDK" tag and the identify tag fired, with variables populated. Then open the console and run `Appcues.debug()` (verification.md). **Submit/Publish** the container only after the checks pass. Remind the user that GTM changes are live once published.

**Environments.** If the site has separate staging and production (separate containers, or GTM Environments), publish to staging first and verify there. **Don't publish to production while the data layer still lacks the plan's user ID** (the developer note isn't shipped yet). The identify tag would either send nothing or the wrong ID, and wrong IDs create Appcues users whose history can't be merged.

## Notes

- **Existing install:** if the app's code already loads Appcues (snippet or `@appcues/web-sdk`), don't add the SDK tag. Raise it, because two loads double-track. The developer removes one.
- **Internal users:** add a trigger exception to the identify, track and logout tags (e.g. a data-layer variable `isInternal` equals `true`), so internal users never get identified.

- CSP: if the site has one, GTM-injected scripts need the Appcues domains too (web-direct.md §8), plus `'unsafe-inline'` / nonce handling that GTM itself already needs.
- Identity verification: set `window.AppcuesSettings.userIdSignature` before identify (fetch it server-side and push it into the data layer, then set it in the SDK tag).
- The **Appcues → GTM integration** on Appcues' Integrations page is *outbound*: it pushes Appcues flow events into the dataLayer. It's separate, and optional.
