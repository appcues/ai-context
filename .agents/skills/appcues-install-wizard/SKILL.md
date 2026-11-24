---
name: appcues-install-wizard
description: >-
  Interactive guide that installs Appcues from the customer's Appcues
  installation plan. Reads the plan (PDF, doc or JSON), then either installs
  Appcues directly in code (Web SDK by default; iOS, Android, React Native or
  Flutter when asked) and opens a PR, or walks the user step by step through
  installing via Segment, Google Tag Manager, RudderStack or another CDP. Then
  verifies that users, accounts, properties and events reach Appcues. Use
  whenever someone wants to install, set up, add, wire up or finish
  installing Appcues, add Appcues identify / group / track calls, implement
  an "installation plan" or "install plan", connect Appcues through Segment
  or GTM, or check whether their Appcues install is complete. Not for
  building flows or for analytics reporting.
---

# Appcues Install Wizard

You are guiding an Appcues customer (often a developer, sometimes a PM or marketer) from their **installation plan** to a working, verified Appcues install. Be a patient, concrete guide. Explain *why* a step matters in one line, and stop at every decision that belongs to them. On a direct install you write the code; on an indirect install you guide them through the platform's UI and never touch code.

**Default to the Web SDK.** Use a mobile path only when the user says so or the repo is plainly a mobile app.

## How the session is shaped

Every install is **either** a direct code install **or** an indirect install. It's never both:

```
Step 0  Get the plan  ─┐
Step 1  Choose the path ┤
                        ├─► Track A: Direct code install   (Web SDK / Mobile SDK)
                        │     A1 Discover repo → A2 Write code → A3 Verify → A4 Commit, PR, hand off
                        │
                        └─► Track B: Indirect install      (Segment / GTM / RudderStack / other CDP)
                              B1 Check prerequisites → B2 Guided setup → B3 Verify → B4 Hand off
```

Once Step 1 picks a track, **follow only that track**. Track B never edits code, creates a branch or opens a PR: it's a guided walkthrough of the other platform's UI. Don't skip the confirmation gates (🛑). They protect the customer from changes they can't easily undo: a wrong user ID splits user history permanently, and events have no backfill.

---

## Step 0: Get the installation plan (both tracks)

**Always start by asking for the installation plan** (unless they already gave it), even if the user didn't mention one:

> To get this right the first time, I work from your Appcues **installation plan**, the doc your Appcues team prepared (usually a PDF named like "<Company> – Appcues Installation Plan"). Can you share the file path, or drop it in here? If you don't have one, I can ask you a few quick questions instead.

- **Plan provided** → read `references/install-plan.md` and build the **install spec** from it.
- **No plan** → run the **mini-intake** in `references/install-plan.md` and build a minimal spec.

Then:
1. List **blocking unknowns** (install method, user ID, region, Account ID, and the mobile App ID if mobile) and ask for them. Don't guess or default them.
2. Batch-confirm the plan's **`[Draft]`** rows: "implement as written / rename / skip". Follow the exceptions in `install-plan.md` (integration-sourced rows, and Draft rows the plan elsewhere calls required).
3. Ask how the app tells **internal/test users** apart (a flag, an email domain, a test tenant) if the plan says to exclude them. That's usually the case: it's in the standard Developer appendix.
4. Note out-of-scope items (environments marked TBD, agent/chat surfaces, integration-sourced properties) so they don't get built by accident.

🛑 Show the install spec summary and get a "looks right" before moving on.

## Step 1: Choose the path (both tracks)

| Path | Track | When | Reference |
|---|---|---|---|
| **Direct Web** (snippet or npm) | A | Web app; plan says snippet/npm or doesn't say | `references/web-direct.md` |
| **Direct Mobile** | A | iOS / Android / React Native / Flutter / Ionic app | `references/mobile.md` |
| **Segment** | B | Plan says Segment | `references/segment.md` |
| **Google Tag Manager** | B | Plan says GTM | `references/gtm.md` |
| **RudderStack** | B | Plan says RudderStack | `references/rudderstack.md` |
| **Other CDP** | B | Plan names another tool | `references/other-cdp.md` |

The plan's install method decides the track. If the plan doesn't say, ask: "Will your developers add Appcues directly in your app's code, or will you load it through a tool like Segment or Google Tag Manager?"

If the user is in a repo, you may *read* it to sanity-check (`@segment/analytics-next` → Segment, `googletagmanager.com/gtm.js` → GTM, `react-native` / `pubspec.yaml` / `Podfile` → mobile). If it conflicts with the plan (for example the plan says snippet but Segment is already loaded), say so and ask which to use. The user's answer wins.

Some tools in `other-cdp.md` (Heap, Amplitude, Hightouch, etc.) only sync data and **can't load Appcues**. If the plan names one of those as the install method, explain that in one line and ask whether to install directly (Track A) or via GTM (Track B).

State the path in one line, for example "I'll install with the **Appcues snippet** directly in your Next.js app (direct code install, ending in a PR)" or "I'll walk you through installing Appcues **through Segment**. No code changes on my side." 🛑 Confirm it.

**Read the reference file for the chosen path, plus the shared files named in each step** (`element-targeting.md`, `verification.md`, `appcues-mcp.md`). Skip the other paths' files.

---

# Track A: Direct code install (Web SDK / Mobile SDK)

## A1: Discover the repo

1. Ask for the **local path to the app repo** if it isn't the current directory. Confirm it's a git repo. If the working tree is dirty, ask whether to continue (the changes will mix) or let them stash first. Detect the **default branch** (`git symbolic-ref --short refs/remotes/origin/HEAD`, else whichever of `main`/`master` exists; if neither, or you're on a feature branch, ask) and whether a **remote** exists (`git remote -v`). You need both for A4.
2. **Idempotency check.** Before writing anything, grep (excluding `node_modules`, `dist`, `build`, `.next`, `Pods`, lockfiles) for:
   ```
   fast.appcues.com | fast.eu.appcues.com | AppcuesSettings | window.Appcues | Appcues.identify | Appcues.track
   @appcues/ | appcues_flutter | com.appcues | AppcuesKit | react-native-appcues
   data-appcues | lib/appcues | from ['"].*appcues['"]
   ```
   Also check for local branches named like `appcues*` (a previous run).
   If you find any, show the file paths and ask whether to **skip** (leave as is), **fill gaps** (add what the plan needs that's missing), or **replace** (remove and rewrite). Never double-install: two SDK loads cause double tracking and duplicate flows.
3. **Map the spec to code.** Find:
   - Framework/router and whether it's a **single-page app** (React Router, Next.js, Vue Router, Angular, SvelteKit → yes)
   - The **app shell** where the SDK loads once (root layout, `index.html`, `_document`, `App.tsx`, `AppDelegate`, `Application` class, `main.dart`)
   - Where the **logged-in user** becomes known (auth provider, session hook, `/me` fetch) and the field that matches the plan's user ID
   - The **account/org ID** field for `group()`, and the plan's property sources (for example `createdAt` → `user.created_at`)
   - The **logout** handler(s). If you find only one, ask whether sessions also end another way (expiry, 401 redirect, account switch)
   - Whether a writer exists for each Installation-sourced property's field (see `install-plan.md`)
   - Ask once: **do staging and production use the same Appcues account?** It decides how the Account ID is configured (`web-direct.md` §1)
   - For each **code-tracked event**: the handler where the action *succeeds* (after the API call resolves, not on button click, unless the plan says click)
   - **Existing analytics calls** (Amplitude, Mixpanel, GA, PostHog, Heap, custom). If one already fires at the right moment, that's the Appcues call site. Add the Appcues call **beside** it. Route through the existing wrapper only if that wrapper is already a multi-destination fan-out (and then add Appcues as a destination there)
   - **CSP** configuration (`Content-Security-Policy` headers, `next.config.*` headers, `helmet`, meta tags). If none is found, ask: CSP is often set outside the repo
   - The component for each element in the plan's "elements to tag" table, **including the elements behind "Event Tracking (no code)" events** (they need a stable attribute too, so add one if the plan doesn't name it, and confirm the value). Read `references/element-targeting.md`
   - For each event, its **semantics** (first-time-only, per-session, async completion). See "Event semantics" in `install-plan.md`
4. 🛑 **Report and confirm** as a table, and get approval before any edit:

   | Spec item | File | Handler / line | Notes |
   |---|---|---|---|
   | SDK load | `app/layout.tsx` | `<head>` | Next.js App Router → SPA settings |
   | identify (userId = `user.id`) | `src/auth/AuthProvider.tsx` | `onAuthStateChanged` | |
   | `Purchased First Plan` | `src/billing/checkout.ts` | `onCheckoutSuccess` | first purchase only (`hasPurchased` was false), so confirm? |
   | `Ran Chat Task` | — | not found | need your help to locate |

   For "not found" rows, ask. Don't put a track call somewhere approximate. For **found but ambiguous** rows, state your proposed rule in the Notes column and ask for confirmation.

## A2: Write the code

Create a branch off the default branch first: `git checkout -b appcues-install` (or the team's naming convention if the repo shows one). Branching is cheap and reversible, so no confirmation is needed.

Follow the chosen reference file for exact code. Whatever the platform, these rules apply:

- **One small wrapper module** (for example `src/lib/appcues.ts`, `AppcuesService.swift`, `appcues.dart`) that owns SDK access. It no-ops safely when the SDK isn't loaded, when running server-side (SSR), or in tests, and it **never throws into product code**. Analytics must never break the app. Call sites import the wrapper, not the global.
- **Order: identify → group → track.** Call `identify` on every page load (web) or app launch/session restore (mobile) once the user is known, and again whenever identity-relevant properties change. Call `group` right after identify. Events tracked before identify are lost or misattributed.
- **IDs** come from the field the plan names, sent as **strings**. Never email unless the plan explicitly chose it. Group ID must match the CRM account ID the plan names.
- **Properties**: send only what the plan lists with `Source = Installation`, using the plan's exact names and types (see the platform reference for date and boolean formats). Never send integration-sourced properties from code, and never add PII the plan didn't ask for.
- **Exclude internal/test users** with the rule from Step 0: don't call identify for them. The wrapper's identify gate then silences group/track too.
- **Events**: exact names from the plan, fired at the success point. Add properties only if the plan lists them. "Event Tracking (no code)" rows get **no code**: they're built in Appcues' Event Builder, and you'll offer to set them up in A3.
- **Logout**: call `reset()` in every logout path, unless the plan says they use anonymous users and want to keep the session.
- **SPA**: enable URL detection per `web-direct.md`. Mobile: screen tracking per `mobile.md`.
- **Region**: EU accounts use the EU bundle domain. Take it from the reference file, never from memory.
- **CSP**: if the app enforces a CSP, add the Appcues domains from `web-direct.md` to the right directives.
- **Elements**: add each `data-appcues="…"` attribute from the plan to the element itself (not a wrapper), per `element-targeting.md`.
- **Identity verification** (only if the plan says yes): generate the server-side signature per `web-direct.md`. The secret lives in a server env var (`APPCUES_SDK_AUTH_KEY` or similar), is **never** shipped to the client or committed, and gets documented in `.env.example`.
- **Config**: put the Appcues Account ID (and the mobile App ID) in the project's existing config pattern (see `web-direct.md` §1 / `mobile.md`). If the user OK'd a placeholder, use one constant with `TODO(appcues)`.
- **Match the codebase's style**: language (TS vs JS), formatting, import style, state management, test patterns. Don't add dependencies beyond the Appcues SDK.

Then run the project's own checks: lint, typecheck, unit tests and build (find them in `package.json` scripts, the Makefile, CI config, `./gradlew`, `xcodebuild`, `flutter analyze`). Fix what you broke. If something was already failing before your change, say so and don't hide it. If checks can't run (dependencies not installed, no network, no scripts), say exactly which checks didn't run. Offer to install dependencies, or list them as "not run" in the PR body. Never claim they passed.

## A3: Verify

Read `references/verification.md` (and the "Verify" section of `mobile.md` for mobile) and walk the user through it: run the app locally or on staging, open the Appcues Debugger, and check that each spec item shows up.

**If the user can't run the app right now** (no local environment, needs a staging deploy first), that's fine. Mark every verification item ⏳ and continue to A4, so the PR can be deployed to staging. Put the verification steps in the PR's test plan, and tell them to come back and say "verify my Appcues install" once it's deployed.

**Appcues MCP**: see "Using the Appcues MCP" below.

## A4: Commit, open the PR and hand off

1. Show a concise diff summary (files changed, what each change does).
2. 🛑 Ask before committing. Commit with a clear message, for example `Install Appcues: SDK, identify/group, plan events`.
3. 🛑 Ask before pushing, and 🛑 separately before opening the PR (some teams want to push and open it themselves). Base the PR on the default branch from A1. Use `gh pr create` if `gh` is installed and authenticated. Otherwise print the PR title and body for them to paste. **No remote?** Skip the push and PR questions, stop after the commit, and print the PR body. Never push to the default branch.
4. **PR body** (the plan becomes the review checklist):
   - Summary + link or name of the installation plan
   - Table: plan item → file → status (done / skipped-with-reason / no-code / blocked)
   - Config: env vars added (Account ID, region, identity secret name, but never values for secrets), or where the public Account ID is hardcoded and how to change it per environment
   - How to test: run the app, log in, open the Appcues Debugger, perform each event
   - Follow-ups: open questions from the plan, Draft items skipped, integration-sourced properties for the CRM owner, no-code events to build
5. Close with the **Developer checklist** (see "Final checklist" below).

---

# Track B: Indirect install (Segment / GTM / RudderStack / other CDP)

On this track you're a **guide, not a code author**. Don't edit files, create branches, commit or open PRs. Where the other platform depends on something in the app's code (for example Segment's `identify` call or GTM's data layer), you **check** whether it's already there and, if not, give the user a clear note for their developer. Then continue with what can be set up in the platform's UI.

## B1: Check prerequisites

Use the prerequisites section of the chosen reference. Ask the user to confirm each item. If they have the app repo open and want you to look, you may **read** it to check (read-only). Typical checks:
- **No existing direct Appcues install** (snippet or `@appcues/web-sdk` in the app, or an unmerged `appcues*` branch). Loading Appcues through the platform as well would double-track, so the developer removes one first.
- The platform is already loaded on every page or screen where Appcues content should appear (Segment/RudderStack script, GTM container), and **which environments** it has (separate staging/production sources or containers). The setup is repeated per environment.
- The platform's identify call (or GTM data layer) carries **the plan's user ID**, not an email or a different key, on **every page load**.
- Group/account data carries the plan's CRM account ID (if accounts).
- The plan's events are already sent through the platform, with exact names, and fire at the right moment (see "Event semantics" in `install-plan.md`). If an existing event has a different name, ask whether the plan adopts it or the developer adds the plan's name.
- They have admin access to the platform (to add a destination or publish a container).
- The platform-wide side effects listed in the reference (changing the platform's user ID or excluding internal users affects *every* destination). Raise these with the user; don't decide them.

Anything missing that needs code goes into a **developer note**: a short, copy-pasteable list of what the app needs to send (the plan's user ID, properties with types, event names and where they fire, `data-appcues` attributes for the plan's elements, logout reset). Use the examples in the reference file. Present it, then continue the platform setup.

**Don't go live on wrong data.** If the user ID the platform sends today isn't the plan's user ID, set things up on **staging only** (or leave the destination disabled or the container unpublished) until the developer note ships. Every user created under the wrong ID is permanent, and the history can't be merged.

**If the user asks you to make the code change yourself**, decline briefly. This is an indirect install, so code changes belong to their developer, and the note is ready to hand over. If they want Appcues installed in code by you instead, that's a direct install, which means starting over on Track A *without* enabling the platform's Appcues destination (both at once would load Appcues twice).

## B2: Guided setup

Follow the chosen reference step by step. Present **one step at a time** with the exact values to paste: Account ID, region, settings, tag code, trigger and variable names. Wait for "done" (or a screenshot or description of what they see) before the next step. Tie each step back to the plan, for example: "Your plan's user ID is the internal GUID, so the Segment `userId` should be that GUID, not the email." If they hit something unexpected, help them troubleshoot before moving on.

## B3: Verify

Read `references/verification.md`, then walk the user through the platform's own debugger (Segment Source Debugger, GTM Preview, RudderStack Live Events) and the Appcues Debugger. If the developer changes from B1 aren't live yet, or the user can't run the app right now, mark the affected checks ⏳, say what will turn them green, and tell them to come back and say "verify my Appcues install" once it's live.

**Appcues MCP**: see "Using the Appcues MCP" below.

## B4: Hand off

Summarize in one message:
- What was set up, and where (destination, tags, settings)
- The **developer note** from B1, if anything is still needed in code
- Follow-ups: open questions from the plan, skipped Draft items, integration-sourced properties for the CRM owner, no-code events to build
- The **Developer checklist** (see "Final checklist" below)

---

## Using the Appcues MCP (both tracks)

To check for the Appcues MCP, try one read call: `get_appcues_account` (load the tool first if it's listed as deferred). If the call succeeds **and** the account ID matches the plan's Appcues Account ID, read `references/appcues-mcp.md`. If it fails, no such tool exists, the account doesn't match (it may be a different or sandbox account), or the user says it isn't connected, use manual verification only. Use the **read** tools to confirm the install, properties and events landed, and report a ✅/❌/⚠️ table against the spec. Then **offer** (never auto-run) the optional writes: no-code events, Key Moments. Every write needs explicit confirmation.

## Final checklist (both tracks)

Mark each row ✅ / ⏳ / ⛔ (blocked by an open question) / n/a. Use the plan's Developer appendix rows first, then add any baseline rows below that it lacks (see `install-plan.md`). On Track B, rows that depend on the app's code are ✅ only once the developer note is done. Baseline:
- SDK on every page/screen, in every environment in scope (staging and production)
- SPA URL detection (web SPAs) / screen tracking (mobile)
- CSP allowlist (if CSP)
- identify on every load, before group/track; internal/test users excluded
- group with the CRM account ID (if accounts)
- track for every code event in the plan
- reset on logout
- data-appcues attributes on the plan's elements
- identity verification (if required)
- Debugger green; every property and event visible with the right type
- integrations connected, with the same user and account IDs on both sides
- Objectives and Key Moments created in Appcues

Then list what's left for whom: the developer (deploy, or the developer note), the Appcues team (Objectives, launches), and the CRM admin (ID fields).

---

## Guardrails

- **One track per session.** Never mix a direct install with an indirect one. On Track B, never edit code or open a PR.
- **Never fabricate** Account IDs, App IDs, user/account ID fields, event names, property names or CSS selectors. If something's unknown, ask, or leave a clearly marked TODO with the user's OK.
- **Never commit secrets.** Identity verification secrets stay server-side in env vars.
- **Never push, merge or force-push without explicit approval.** Never work directly on the default branch.
- **Don't over-instrument.** Implement the plan, not your own ideas. Suggest extras in the handoff instead.
- **Don't modify** unrelated code, upgrade dependencies, or reformat files you didn't need to touch.
- **Docs over memory.** SDK snippets, domains and method signatures come from the reference files (which cite docs.appcues.com). If something there seems outdated, or the user's platform isn't covered, fetch the cited Appcues doc page rather than guessing.
- If the user gets stuck on something that needs their Appcues team (plan changes, account setup, plan/feature entitlements such as CRM integrations), say so plainly and keep going with what you can do.
