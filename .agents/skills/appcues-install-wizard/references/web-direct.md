# Direct Web install (snippet or npm)

Sources: docs.appcues.com. [INSTALL] /install-appcues-web/install-the-appcues-sdk · [JSAPI] /dev-api-data/javascript-api-developer · [IDENTIFY] /install-appcues-web/identify-users-and-groups · [TRACK] /install-appcues-web/track-events-in-your-web-app · [TYPES] /users-groups-events/supported-data-types · [SPA] /install-appcues-web/single-page-application-spa-guide-developer · [IDV] /users-groups-events/identity-verification · [CSP] /install-appcues-web/faq-content-security-policies · [HOSTING] /installation-overview/appcues-us-and-eu-hosting-environments · [NOREWORK] /installation-overview/install-appcues-without-rework

If anything here looks stale, or the user's setup isn't covered, fetch the source page before improvising.

## 1. Choose snippet vs npm

| Use | When |
|---|---|
| **Script snippet** | Default. Server-rendered apps, multi-page apps, or when the plan says "snippet". Always gets the latest SDK. |
| **npm `@appcues/web-sdk`** | Bundled SPAs where the team wants version control and TypeScript types. They bump versions themselves [INSTALL]. |

Follow the plan's choice. If the plan says nothing, use the snippet for server-rendered/MPA apps and ask for bundled SPAs.

The Account ID is in Studio → Settings → Account (https://studio.appcues.com/settings/account). It isn't a secret. Put it where the project already keeps public config, so staging and production can differ:

| Setup | How to get the ID into the snippet | Failure mode to guard |
|---|---|---|
| Vite `index.html` (project already uses `.env` files) | `src="https://fast.appcues.com/%VITE_APPCUES_ACCOUNT_ID%.js"` | If unset, the literal `%VITE_…%` stays in the URL. Add it to every env file the build uses, plus `.env.example` |
| CRA `public/index.html` | `%REACT_APP_APPCUES_ACCOUNT_ID%` | Same |
| Next.js | `process.env.NEXT_PUBLIC_APPCUES_ACCOUNT_ID` in the layout's `<Script src={…}>` | Inlined at build time, so redeploy after changing it |
| Server templates (Rails/Django/…) | The template's config/env helper | — |
| No config/env pattern in the project | Hardcode it in the snippet. It's public. Don't create new `.env` files just for this. If staging and production use *different* Appcues accounts, raise it: they then need a per-environment mechanism, and the user picks one | — |

**Ask once (A1): do staging and production use the same Appcues account?** Most teams use one. The plan's appendix asks for verification on both, so the answer decides whether the ID needs to vary per environment.

Never commit a `.env` that the repo's `.gitignore` excludes. Put the value in `.env.example` (or the docs) and tell the user to set it in their deploy environment.

## 2. Load the SDK

### Snippet (in `<head>` of every page: `index.html`, root layout, base template) [INSTALL]
```html
<script type="text/javascript">
  window.AppcuesSettings = { enableURLDetection: true };
</script>
<script src="https://fast.appcues.com/YOUR_APPCUES_ID.js"></script>
```
**EU accounts:** use `https://fast.eu.appcues.com/YOUR_APPCUES_ID.js` [NOREWORK][HOSTING]. Never mix regions.

**Async loading (optional)**: add the `AppcuesReady` queue before the script and load with `async onload="AppcuesReady()"` [INSTALL]:
```html
<script>
  (function() {
    if (!window.AppcuesReady) {
      window.AppcuesReady = function(callback) {
        callback && window.AppcuesReady.q.push(callback);
        if (window.Appcues) {
          while (window.AppcuesReady.q.length) {
            var cb = window.AppcuesReady.q.shift();
            if (typeof cb === 'function') cb();
          }
        }
      };
      window.AppcuesReady.q = [];
    }
  })();
</script>
<script src="https://fast.appcues.com/YOUR_APPCUES_ID.js" async onload="AppcuesReady()"></script>
```
Then wrap SDK calls in `AppcuesReady(function() { ... })`. The wrapper module (§3) handles this.

**Next.js App Router:** put the settings and SDK in `app/layout.tsx` using `next/script` (`strategy="beforeInteractive"` for the settings inline script, `afterInteractive` for the SDK), or plain `<script>` tags in `<head>`. **Next.js Pages Router:** `pages/_document.tsx` `<Head>`. **Vite/CRA:** `index.html`. **Rails/Django/Laravel/etc.:** the base layout template.

### npm [INSTALL]
```bash
npm install @appcues/web-sdk --save
```
```ts
import Appcues from '@appcues/web-sdk'

window.AppcuesSettings = { enableURLDetection: true }; // must be set BEFORE setup()
await Appcues.setup('APPCUES_ACCOUNT_ID')
// EU: await Appcues.setup('APPCUES_ACCOUNT_ID', { bundleDomain: 'https://fast.eu.appcues.com' })
// Custom proxy domain: { apiHostName: 'you.customdomain.com' }
```
- Call `setup()` once at app launch (client-side only). Calls made before setup finishes are buffered and replayed in order [INSTALL].
- Use the project's package manager (npm/yarn/pnpm/bun, based on the lockfile). Tell the user you're adding the dependency.

### TypeScript (snippet installs) [INSTALL]
If TS complains that `Appcues` isn't on `Window`, add a declaration. Prefer a typed one in the wrapper over `any` where the codebase is strict:
```ts
declare global {
  interface Window {
    Appcues?: {
      identify(userId: string, props?: Record<string, string | number | boolean | null>): void;
      group(groupId: string, props?: Record<string, string | number | boolean | null>): void;
      track(event: string, props?: Record<string, string | number | boolean>): void;
      page(): void;
      reset(): void;
      anonymous(): void;
    };
    AppcuesSettings?: Record<string, unknown>;
  }
}
```

## 3. The wrapper module (always create one)

Example: `src/lib/appcues.ts`. Adapt it to the codebase's language, style and npm-vs-snippet choice. It does three jobs: it **never throws**; it **gates `group`/`track` on a successful `identify`**, so excluded internal users and pre-login code send nothing; and it strips values Appcues mishandles.

```ts
type Value = string | number | boolean | null;
type Props = Record<string, Value | undefined>;

let identified = false; // group/track only after identify; cleared on reset

function sdk() {
  if (typeof window === 'undefined') return undefined; // SSR / tests
  return window.Appcues;
}

function clean(props?: Props): Record<string, Value> | undefined {
  if (!props) return undefined;
  // Appcues rules: no objects/arrays, no "" (treated as a real value). Drop undefined and "".
  const out: Record<string, Value> = {};
  for (const [k, v] of Object.entries(props)) if (v !== undefined && v !== '') out[k] = v;
  return out;
}

function safe(fn: () => void) {
  try { fn(); } catch (e) { console.warn('[appcues]', e); } // or the codebase's logger / dev-only check
}

export const appcues = {
  identify(userId: string, props?: Props) {
    safe(() => { sdk()?.identify(String(userId), clean(props)); identified = true; });
  },
  group(groupId: string, props?: Props) {
    if (!identified) return;
    safe(() => sdk()?.group(String(groupId), clean(props)));
  },
  track(event: string, props?: Props) {
    if (!identified) return;
    // event properties don't accept null: drop it
    const p = clean(props);
    const eventProps = p && Object.fromEntries(Object.entries(p).filter(([, v]) => v !== null)) as Record<string, string | number | boolean>;
    safe(() => sdk()?.track(event, eventProps));
  },
  reset() {
    identified = false;
    safe(() => sdk()?.reset());
  },
};
```
- The type declaration in §2 makes this compile under `strict` without `any`. Don't use `process.env` in browser code unless the project already does (Vite needs `import.meta.env.DEV`; `process` errors without `@types/node`).
- If internal users are excluded, the identify call site simply doesn't call `appcues.identify` for them, and the gate silences everything else.
- **npm installs**: import from `@appcues/web-sdk` instead of reading `window.Appcues`. Calls before `setup()` resolves are buffered by the SDK.
- **async snippet**: route calls through `window.AppcuesReady(cb)` when it exists.
- Where a reusable `toUnixSeconds(date)` helper is needed, add it here: `Math.floor(new Date(d).getTime() / 1000)`.

## 4. identify() and group() [IDENTIFY][TYPES][JSAPI]

```ts
appcues.identify(user.id, {
  createdAt: toUnixSeconds(user.createdAt),   // whole-number Unix timestamp
  signupSource: user.signupSource,            // string, consistent casing
  hasPurchased: user.hasPurchased === true,   // real boolean
});
appcues.group(account.crmAccountId, {         // right after identify; the CRM-matching ID the plan names
  planTier: account.planTier,
});
```

**Where:** in the place the authenticated user becomes known on **every page load**, not only at login. Examples: an auth provider/effect keyed on the user ID, a root layout client component, the `/me` response handler, the server-rendered layout (inline script with the user's values). Re-call it when plan properties change (for example `hasPurchased` flips after checkout).

**Rules that fail silently** [TYPES][NOREWORK][IDENTIFY]:
- First arg: the plan's user ID, as a **string**. Never change it later, because a changed ID creates a new person and history can't be merged. Prefer an opaque ID over email.
- Second arg must be an **object**. Watch for passing unparsed JSON strings from storage.
- **Don't send a property named `userId` / `user_ID` / similar.** Plans often list `userId` in the property table. That row means "the identify() ID", not a property.
- Types: strings are case-sensitive; numbers are native (`599` not `"599"`); booleans are `true`/`false` (not `"true"`); objects/arrays are **silently dropped**, so flatten them (for example `invoices.length`).
- **Dates**: whole-number Unix timestamp (seconds or ms), ISO 8601 (`"2025-01-01T00:00:00Z"`), or `"Jan 1, 2025 12:00:00 AM"`. No decimals. Formats like `06/20/2025` are stored as strings and date targeting breaks. Pick one format per property. Default to Unix seconds.
- Missing value: **never `""`**, because an empty string matches targeting rules. Omitting a key doesn't clear a stored value, but `null` does. Rule: if a property can go from set back to empty (or segments test "is empty"), send `null` explicitly. If it's never been set, omitting is fine. When unsure, send `null`.
- **Enumerated values must match the plan's segments.** If the plan's audience says `planTier is paid` but the app's values are `free|pro|scale`, either send a derived property the plan can use (ask for its name) or flag it so the segment gets rewritten. Don't silently send values the plan's conditions can't match.
- Re-calling identify (for example after checkout updates `hasPurchased`) is expected. It also records a page view, which is harmless.
- Same type for a property every time, for every user.
- `email` is commonly sent as a display identifier when the plan lists it.

**group():** the ID must match the CRM's account ID named in the plan. Group properties are account-wide; user-specific data goes in identify. Only the most recent group is used for targeting, so call `group()` again when the user switches workspace or account.

**Exclude internal/test users** if the plan says so: skip identify (and therefore all Appcues calls) for staff or test tenants, using whatever flag the app already has. Ask the user what that flag is. Each identified user counts toward MAU.

**Anonymous users** (only if the plan explicitly wants pre-login content): `if (userId) Appcues.identify(userId) else Appcues.anonymous()`. Use one or the other per page load, never both. Warn that anonymous traffic can inflate MAU [JSAPI].

## 5. track() [TRACK][TYPES]

```ts
appcues.track('Purchased First Plan');                     // exact plan name
appcues.track('Enriched List', { listSize: rows.length }); // props only if the plan lists them
```
- Fire it at the **success point** (after the API call resolves, in the handler or beside an existing analytics call), after identify.
- Names are case-sensitive and must match the plan exactly. A different spelling creates a separate event.
- Event properties: strings, numbers, booleans. They're usable for event triggering only, not audience targeting.
- **No backfill:** data starts the day this ships. Click-to-Track (no-code) events are backfilled from raw event recording, which is why "Event Tracking (no code)" rows aren't coded.
- If the same product has a mobile app too, web and mobile events with the same name are pooled. Follow the plan's naming.

## 6. Single-page apps [SPA][INSTALL]

- Default: `window.AppcuesSettings = { enableURLDetection: true }` set **before** the SDK loads or `setup()`. No manual `page()` calls needed.
- Caveat: detection watches the full URL, including query strings and hashes. If the app changes the query constantly (search-as-you-type, filters in the URL) and Flows get interrupted, switch to **manual mode**: `enableURLDetection: false` plus `Appcues.page()` only when the **pathname** changes:
  - React Router: a `AppcuesPageTracker` component inside the router using `useLocation()` with a `useRef` of the previous pathname
  - Next.js App Router: a `"use client"` component with `useEffect(() => window.Appcues?.page(), [usePathname()])` in the root layout
  - Next.js Pages Router: `router.events.on('routeChangeComplete', …)`, comparing pathname without the query
  - Vue Router: `router.afterEach((to, from) => { if (to.path !== from.path) window.Appcues?.page(); })`
  - Angular: `NavigationEnd` + `pairwise`, comparing `urlAfterRedirects` without the query
  - SvelteKit: `afterNavigate` in the root layout, comparing `to.url.pathname`
- Never run manual trackers **and** URL detection together, because it double-signals. `identify()` already includes a page call, so don't call `page()` right after it.
- If Flows only appear after a refresh, `page()` is firing before the URL updates. Move it to after navigation completes.

## 7. Logout [IDENTIFY][NOREWORK]

Call `appcues.reset()` in **every** logout path (menu, session expiry, account switch with re-login). It clears session data and in-progress Flows. Skip it only if the plan uses anonymous users and wants continuity. Don't call `anonymous()` right after `reset()`, because Flows may re-show.

## 8. Content Security Policy [CSP]

Look for a CSP in the repo (headers in `next.config.*`, middleware, `helmet`, nginx/vercel config, a `<meta http-equiv>`). **No CSP in the repo doesn't mean no CSP**: it's often set at a CDN, proxy or load balancer. If none is found, ask the user (and always ask if the plan raises CSP). If it lives outside the repo, give them the directives below for their infra team. Merge these into the **existing** directives. Don't replace them:
```
frame-src    https://*.appcues.com
font-src     https://fonts.gstatic.com
style-src    https://*.appcues.com https://*.appcues.net https://fonts.googleapis.com https://fonts.google.com 'unsafe-inline'
script-src   https://*.appcues.com https://*.appcues.net
img-src      https://*.appcues.com https://*.appcues.net res.cloudinary.com cdn.jsdelivr.net
connect-src  https://*.appcues.com https://*.appcues.net wss://*.appcues.net wss://*.appcues.com
```
- `'unsafe-inline'` in `style-src` is required for Appcues themes. If the existing policy forbids it, raise that with the user rather than silently loosening security.
- The wildcards cover EU hosts (`fast.eu.appcues.com`, `api.eu.appcues.net`).
- Docs recommend wildcards because pinned hosts can change. If the security team insists on pinned hosts, point them to [CSP].

## 9. Identity verification [IDV] (only if the plan requires it)

How it works: the **backend** signs a **JWT (HS256)** with claims `iss` = Appcues Account ID, `sub` = the exact user ID passed to `identify()`, and `exp` = expiry (pick it deliberately; docs samples use 15 min to 1 hour). The key is the **SDK authentication key** from the Appcues Public API. It stays server-side.

1. **Server**: add an endpoint (or include it in the existing `/me` / session payload) that returns the signature for the logged-in user only. Use the codebase's existing JWT library if it has one. Otherwise add a standard one (`jsonwebtoken`, `jose`, `PyJWT`, `ruby-jwt`, etc.):
   ```ts
   import jwt from 'jsonwebtoken';
   const signature = jwt.sign(
     { iss: process.env.APPCUES_ACCOUNT_ID, sub: String(user.id) },
     process.env.APPCUES_SDK_AUTH_KEY!,   // server-only env var, never NEXT_PUBLIC_/VITE_
     { algorithm: 'HS256', expiresIn: '1h' }
   );
   ```
2. **Client**: set it **before any SDK call**, preserving the existing settings:
   ```ts
   window.AppcuesSettings = { ...(window.AppcuesSettings || {}), userIdSignature: signature };
   ```
   Then call identify. Refresh the signature before it expires (re-fetch on session refresh).
3. Add `APPCUES_SDK_AUTH_KEY=` to `.env.example`, and tell the user where to get the key. Never commit a value.
4. Testing: set `window.APPCUES_TEST_IDENTITY_VERIFICATION = true` before the first SDK call (dev only). The console reports valid, missing or invalid signatures. Remove it before production.
5. **Enforcement** is switched on separately, account-wide, via the Public API (`/v2/accounts/ACCOUNT_ID/enforcement_mode/enable`). Tell the user **not** to enable it until every web and mobile app sends signatures. Don't do it for them.

## 10. Environments

The plan's appendix asks for verification on staging and production. Make sure the SDK loads in both. Don't gate it behind a production-only flag unless the user asks. If staging should use a separate Appcues account, read the Account ID from env per environment.
