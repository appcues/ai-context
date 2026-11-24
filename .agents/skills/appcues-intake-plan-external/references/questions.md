# Question bank (customer-facing)

Ask these in plain language, a few at a time. Every question has a short **why** you can share if the customer hesitates, and **examples** to pick from so nobody faces a blank page. The **Plan field** column tells you where the answer goes in the plan JSON (see `plan-schema.md`).

Never ask for real user data, emails, passwords, API keys or secrets. Example values ("e.g. a user ID looks like `usr_8f2k...`") are fine.

## Contents
- Part 1 - About you and your product
- Part 2 - Goals and the moments that prove them
- Part 3 - What you'll launch first
- Part 4 - Who you want to reach (properties)
- Part 5 - Your CRM and other tools
- Part 6 - AI assistant or chat
- Part 7 - For your developer (handoff)
- Examples by type of product
- Turning answers into the plan

---

## Part 1 - About you and your product

| Ask | Why | Plan field |
|---|---|---|
| What's your company name, and what's your role? | So the plan is addressed to the right people. | `meta.customer`, `meta.customer_team` |
| Who else is involved? (product, engineering, whoever owns your CRM) Names optional - roles are enough. | Each section has an owner; naming them early keeps things moving. | `meta.customer_team` |
| Where will Appcues run: your web app, your mobile app(s), or both? | Web and mobile are installed differently. | `meta.platforms`, `account` |
| Roughly how many people use your product each month? | Helps size the rollout. A range is fine. | `account` |
| Do you have a target go-live date? | So the plan's next steps line up with it. | `meta.target_go_live` |

## Part 2 - Goals and the moments that prove them

Start here - it's the part that makes the rest make sense.

| Ask | Why | Plan field |
|---|---|---|
| What 1–3 results do you want Appcues to help with? | Everything else in the plan exists to move these. | `objectives[].objective` |
| For each: what's the number today, and what would success look like? "Don't know yet" is fine. | So you can tell whether it worked. | `objectives[].metric` |
| For each: what does a user **do** in your product that shows it's working? | These are your Key Moments. Each one needs an event, and events only count from the day they're sent - so we plan them now. | `key_moments[]`, `events[]` |
| Do you already track any of those actions (for example in Amplitude, Mixpanel, Heap or Segment)? | Reusing existing tracking saves your developer time. | `key_moments[].exists`, `integrations[]` |

Common goals to offer: more trial-to-paid conversions · faster time to first value for new users · adoption of a specific feature · fewer "how do I…" support tickets · more expansion / upgrades · better retention and renewals · more reviews or referrals from happy users.

## Part 3 - What you'll launch first

| Ask | Why | Plan field |
|---|---|---|
| What are the first 2–3 things you'd like to show users? Describe each as **who** sees it and **when**. | The data you need falls out of the sentence. | `launches[].sentence` |
| Which goal or Key Moment should each one move? | Ties every launch to a result you can measure. | `launches[].success_measure` |

Help them shape vague answers. "An onboarding tour" → "Show new admins a short tour in their first week, until they've invited a teammate." Use Appcues names: Flow, Checklist, Pin, Banner, Survey, Launchpad, Embed.

## Part 4 - Who you want to reach (properties)

Usually you can derive most of these from Parts 2–3 and just confirm them.

| Ask | Why | Plan field |
|---|---|---|
| What do you know about each **person** that you'd target or report by? (role, plan, signup date, language…) | These become user properties. | `user_properties[]` |
| Do people belong to a company, team or workspace in your product? What do you know about it? (plan, size, industry, renewal date…) | These become account properties, shared by everyone in the account. | `account_properties[]`, `has_accounts` |
| Which of these already live in your CRM rather than your product? | Those can sync from the CRM instead of needing code. | `source` on each property |

Every property and event should have a named use (a launch, an audience, a Dashboard or a Key Moment). If the customer can't name one, ask whether to leave it out for now.

## Part 5 - Your CRM and other tools

| Ask | Why | Plan field |
|---|---|---|
| Which CRM do you use (Salesforce, HubSpot, other)? Who manages it? | Your CRM already holds the audience labels your marketing team uses. | `crm.system`, `crm.items` |
| Which CRM fields would you like to target by? (lifecycle stage, persona, segment, renewal date, account owner…) | They become reusable audiences without extra code. | `crm.field_mapping`, `crm.audiences` |
| Does your CRM store the same user ID and account ID your product uses? | The sync matches records on these. If they're missing, adding a field is usually a quick task for your CRM admin. | `crm.items` |
| Would you like Appcues activity (survey answers, completed Flows) to show up in your CRM? | Lets your customer-facing team see engagement. | `crm.data_out` |
| Any other tools in the picture: analytics, customer data platform (Segment, RudderStack), data warehouse (Snowflake, BigQuery), email (Braze, Customer.io)? | Each one can send data in or receive it, if the IDs match. | `integrations[]` |

If they ask whether an integration is included in their Appcues plan, say their Appcues team will confirm, and add it as an open question owned by Appcues.

## Part 6 - AI assistant or chat

| Ask | Why | Plan field |
|---|---|---|
| Does your product have an AI assistant, chatbot or chat feature? | So your Appcues team can plan around it. Nothing to build for this install. | `agents.items` |
| If yes: built in-house or a vendor (e.g. Intercom Fin, Zendesk)? What can it do today? | Context for your Appcues team. | `agents.items` |

Keep this neutral. Don't describe or promise Appcues features for AI assistants.

## Part 7 - For your developer (handoff)

Ask the customer whether they want to answer these now or hand them to their developer. Default: hand off. Unanswered items render as blue cells in the plan, and the developer appendix lists the steps.

| Question for the developer | Why | Plan field |
|---|---|---|
| What's the frontend framework (React, Angular, Vue, other)? Is it a single-page app? | Single-page apps need one extra setting. | `account` (owner `developer`) |
| How will you add Appcues: script tag, NPM package, Segment, or Google Tag Manager? | Changing this later means redoing some work. | `key_decisions` |
| What permanent, unique ID identifies each user? (not email, if you can avoid it) | The single hardest thing to change later. | `key_decisions`, `identity` |
| What ID identifies each account / company? Does your CRM use the same one? | Needed for account data and the CRM sync. | `key_decisions` |
| Do you enforce a Content Security Policy? | If so, Appcues domains need to be allowlisted. | `account` |
| Mobile only: which frameworks (iOS, Android, React Native, Flutter, Ionic)? Release schedule? | Mobile changes ship with app releases. | `mobile.items` |

## Examples by type of product

Offer these when the customer is stuck.

**B2B SaaS (web)**
- Goals: trial → paid, feature adoption, fewer support tickets.
- Key Moments / events: `Created Project`, `Invited Teammate`, `Connected Integration`, `Upgraded Plan`.
- Properties: `role`, `planTier`, `createdAt`, `trialEndsAt`; account `companySize`, `industry`, `renewalDate`.

**Mobile app**
- Goals: activation in the first session, retention at day 7 / day 30, feature discovery.
- Key Moments / events (prefix mobile events): `mobile-Completed Onboarding`, `mobile-Enabled Notifications`, `mobile-Completed First Order`.
- Properties: `appVersion`, `locale`, `signupSource`, `createdAt`.

**Marketplace / two-sided**
- Goals: first transaction for each side, repeat usage.
- Key Moments / events: `Published Listing`, `Completed First Sale`, `Completed First Purchase`.
- Properties: `userType` (buyer / seller), `listingsCount`, `createdAt`.

## Turning answers into the plan

- Name events the way a person would search for them (`Created Project`, not `proj_create`). Use different names for web and mobile versions of the same action.
- Anything you suggest that the customer hasn't confirmed gets `[Suggested]` at the end of its name or sentence. Show suggestions in the review step and drop or confirm them before rendering.
- Unknowns become blank cells plus an open question with an owner (the customer, their developer, or "Appcues team").
- Score readiness against the six parts of "Installed" with honest, friendly notes (15 words max each).
