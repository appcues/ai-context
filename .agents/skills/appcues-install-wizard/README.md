# Appcues Install Wizard

A Claude Code plugin that turns your **Appcues installation plan** into a working, verified Appcues install.

## What it does

1. **Reads your installation plan.** This is the PDF, doc or JSON your Appcues team prepared. No plan? It asks you seven quick questions instead.
2. **Confirms how you're installing.** Every install is one of two kinds:
   - **Direct code install** (Web SDK by default, or a mobile SDK for iOS, Android, React Native or Flutter). It reads your repo and shows you exactly where each piece goes before changing anything: SDK load, `identify`, `group`, each `track` event, logout `reset`, and `data-appcues` attributes. Then it writes the code on a new branch, runs your lint, tests and build, and opens a PR whose description doubles as the install checklist.
   - **Indirect install** (Segment, Google Tag Manager, RudderStack or another CDP). It walks you through the setup in that platform one step at a time, with the exact values to paste. It doesn't change your code or open a PR. If your app is missing something the platform needs (for example the right user ID in your Segment `identify` call), it gives you a short note for your developer.
3. **Walks you through verification** with the Appcues Debugger. If you've connected the Appcues MCP server, it also checks that your properties and events actually arrived, and offers to create your Key Moments.

It asks before every change that's hard to undo: committing, pushing, opening a PR, and creating anything in your Appcues account.

## Install

To try it from a local copy of this folder:

```bash
claude --plugin-dir ./appcues-install-wizard
```

For wider distribution, publish it to a plugin marketplace. Or copy `skills/appcues-install-wizard/` into `~/.claude/skills/` (personal) or `<your-repo>/.claude/skills/` (shared with your team).

## Use

Open Claude Code in your app's repo and say something like:

> Install Appcues using our installation plan at ~/Downloads/Acme - Appcues Installation Plan.pdf

or just:

> Help me install Appcues

## What you'll need

- Your Appcues **Account ID** (Studio → Settings) and, for mobile, the **Application ID**
- Whether your Appcues account is hosted in the **US or EU**
- The field that permanently identifies a logged-in user, and an account/company ID if you have one
- `git`, plus the `gh` CLI if you want the PR opened for you
- Optional: the Appcues MCP server connected in Claude Code, for automated verification

## Docs

- Installation overview: https://docs.appcues.com/installation-overview/appcues-installation-overview
- Install without rework: https://docs.appcues.com/installation-overview/install-appcues-without-rework
- Web SDK: https://docs.appcues.com/install-appcues-web/install-the-appcues-sdk
- Mobile SDK: https://docs.appcues.com/mobile-installation-overview/installing-the-mobile-sdk
