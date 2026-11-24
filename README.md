# ai-context

Appcues-provided context files to assist with using AI tools.

This repo collects reference documentation — guides, tool descriptions, and usage notes — meant to be fed to AI coding assistants (e.g. as context for Claude, MCP clients, or similar tools) so they can work effectively with Appcues-specific systems and workflows.

## Contents

- [beta-tools-guide-updated.md](beta-tools-guide-updated.md) — guide to the Appcues MCP beta tools for building Flows, Embeds, Banners, and Pins, and configuring targeting

## Skills

The [.agents/skills/](.agents/skills/) folder holds customer-facing Claude skills for planning and completing an Appcues install. Each skill is a folder with a `SKILL.md` plus supporting references.

- [appcues-intake-plan-external](.agents/skills/appcues-intake-plan-external/SKILL.md) — walks a customer through a short set of plain-language questions and produces a branded installation plan (Word + PDF, or a Google Doc) to share with their developer and Appcues team. Includes reference files (plan schema, install facts, questions), a `build_plan.py` script, and an example plan. Its `SKILL.md` frontmatter names it `appcues-install-plan-external`.
- [appcues-install-wizard](.agents/skills/appcues-install-wizard/SKILL.md) — takes the installation plan and installs Appcues, either directly in code (Web SDK by default, or iOS, Android, React Native, Flutter) with a PR, or by walking through Segment, Google Tag Manager, RudderStack or another CDP. It then verifies that users, accounts, properties and events reach Appcues. Includes references for each install path, element targeting, and verification. See its [README](.agents/skills/appcues-install-wizard/README.md) for usage.

The two chain together: build the plan with `appcues-install-plan-external`, then hand it to `appcues-install-wizard`.
