# Appcues MCP Beta Tools — Building Flows & Setting Targeting

These tools extend the Appcues MCP server with the ability to **create and edit web experiences** (Flows 2.0, Embeds, Banners, and Pins), **theme them**, and **configure audience targeting and triggers** directly from your AI coding assistant.

> **Note:** These tools create and modify **draft** experiences. Nothing goes live until it is published, either from Appcues Studio or with `publish_experience` (see [Publishing and related tools](#publishing-and-related-tools)). Only call `publish_experience` when the user has explicitly asked to publish.

## Quick Start

A typical flow-building conversation looks like this:

1. **Create an experience** — give it a name and type. If the account has a default theme, it's assigned automatically.
2. **Add steps** — each step is a screen in the flow.
3. **Check for a theme** — if the experience has a theme, load its variants before writing any content.
4. **Design each step** — set the layout, text, images, and buttons using the DSL.
5. **Configure step behavior** — position, animations, backdrop, delay, navigation, or (for tooltips) the target element and advance-on-click, all with `update_step`.
6. **Set targeting** — decide who sees it and where.

---

## Flow Building Tools

### `create_experience`

Creates a new web experience and returns its ID.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `name` | Yes | Name for the experience |
| `type` | No | `"flow"` (overlay dialog, default), `"embed"` (inline within the page), `"banner"` (top-of-page banner), or `"persistent"` (pin) |
| `build_url` | Yes | The page in the customer's product where the experience will be built and previewed (e.g. `https://app.example.com/dashboard`). Must include protocol. Get it from the user, or infer it from the most recently created web experience. |
| `theme_id` | No | Published experience theme ID to assign. Omit to use the account's default theme if one exists. Pass `null` explicitly to create with no theme. |
| `tactic_id` | No | If this content is part of a tactic, pass its ID to link automatically. |
| `tag_ids` | No | IDs of tags to associate with the experience. Use `list_tags` to find IDs (see [Publishing and related tools](#publishing-and-related-tools)). |
| `recap` | No | 1–2000 characters. A retelling of what the user asked for and decided about *this* experience, in second person and past tense, opening with "You asked for…". Shown as conversation history in the experience's own chat. |

NPS and Launchpad experiences cannot be created via tools — use the builder wizard.

**Example prompt:** *"Create a new flow called 'Welcome Tour'"*

**Response:** Returns the experience ID and, if a theme was assigned (explicitly or by default), its `theme_id`. If a theme is present, call `get_experience_theme_variants` before building step content — see [Theming Tools](#theming-tools).

---

### `update_experience`

Updates top-level experience properties — `name`, `theme_id`, and/or `tag_ids`. Does **not** modify step content, and does not set the display name end users see.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `experience_id` | Yes | ID of the experience |
| `name` | No | New internal name, shown to the team in the Studio experience list |
| `theme_id` | No | Published experience theme ID to (re)assign |
| `tag_ids` | No | New tag IDs. **Replaces** the existing tags; pass an empty array to clear them |

At least one of `name`, `theme_id` or `tag_ids` must be provided. Reassigning a theme means variants may have changed — call `get_experience_theme_variants` again before your next `update_step_content`.

---

### `clone_experience`

Clones an experience into a new **unpublished draft**. Works for any experience type, and the clone is always the same kind and type as the source, in the same folder. The source must be a draft or published item; archived items cannot be cloned.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `id` | Yes | ID of the experience to clone (use `list_experiences` to find it) |
| `name` | No | Name for the clone. Defaults to the source's name |

**Example prompt:** *"Duplicate the Welcome Tour flow so I can try a different version"*

---

### `add_step`

Adds a new step to an existing experience (flow or embed only). Each step starts with a default template. Returns the new step ID.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `experience_id` | Yes | ID of the experience to add a step to |
| `type` | Yes | `"modal"` or `"tooltip"` for flows, `"embed"` for embeds. Must match the experience type. |

`"flow"` is not a step type — passing it is rejected. Use `"modal"` or `"tooltip"` on a flow, `"embed"` on an embed. Modal and tooltip steps are valid only on flow experiences, and embed steps only on embed experiences.

Tooltip steps are a step type within flow experiences, not a separate experience type: `create_experience` with `type: "flow"`, then `add_step` with `type: "tooltip"`. A tooltip's target element is normally attached by a human in the builder. Only set it yourself with `update_step`'s `target_selector` when the user explicitly gives you a selector — never guess one.

**Example prompt:** *"Add two more steps to this flow"*

---

### `move_step_order`

Moves a step before or after another step in the experience sequence (changes ordering only — not visual placement; for that see the `position` key of [`update_step`](#update_step)).

| Parameter | Required | Description |
|-----------|----------|-------------|
| `experience_id` | Yes | ID of the experience |
| `step_id` | Yes | The step to move |
| `target_step_id` | Yes | The step to place it before or after |
| `placement` | Yes | `"before"` or `"after"` |

---

### `delete_step`

Removes a step from an experience. Destructive — cannot be undone via tools.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `experience_id` | Yes | ID of the experience |
| `step_id` | Yes | ID of the step to delete |

---

### `update_step_content`

Updates the visual content and actions for a step using the DSL format. This is the main tool for designing what each step looks like.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `experience_id` | Yes | ID of the experience |
| `step_id` | Yes | ID of the step to update |
| `content` | Yes | **A JSON object** (not a JSON-encoded string) with `"container"` and `"layout"` keys — see [DSL Format](#dsl-format) below |

> **Breaking change from earlier versions:** `content` must be passed as a native JSON object, not a double-encoded string. Passing a string is still accepted if it parses as valid JSON, but object input is preferred and avoids encoding errors with Unicode/emoji content.

The DSL parser generates UUIDs, builds the block hierarchy, expands action shorthands, and applies defaults. If validation fails, fix the DSL and retry automatically rather than asking the user — error messages point at the offending schema path.

When a step contains [survey questions](#survey-questions), rewriting it has extra rules: every existing question must be in the new content with its `fieldId` set to the block's `surveyFieldId` (from `get_experience_details`), and a question is only removed by listing its id in the top-level `removeSurveyFields` array.

---

### `replace_step_text`

Finds and replaces text within a specific content block of a step — a lighter-weight alternative to re-sending the whole DSL for a copy tweak.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `experience_id` | Yes | ID of the experience |
| `step_id` | Yes | ID of the step |
| `block_id` | Yes | ID of the content block to edit, from the step content structure (see `get_experience_details`) |
| `find` | Yes | Exact text to find |
| `replace` | Yes | Replacement text |

---

### `update_block_style`

Partial-merges CSS style properties onto an existing block — or onto one part of a survey question — without resending the full DSL. Use this instead of `update_step_content` when you're only changing visual styling on blocks that already exist.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `experience_id` | Yes | ID of the experience |
| `step_id` | Yes | ID of the step |
| `block_id` | Yes | The block's `nodeId`, from the step content structure returned by `get_experience_details`. With `part`, the survey question's `nodeId` |
| `style` | Yes | Object of camelCase CSS properties to merge, e.g. `{"borderRadius": "12px"}`. Only the keys you pass change, and a key set to `null` is removed. Pseudo-states go under `state` (see below) |
| `part` | No | Survey questions only: which part of the question to style (see [Styling survey questions](#styling-survey-questions)) |

> **Changed from earlier versions:** CSS properties are no longer accepted as top-level parameters. Put them inside `style`. Unknown top-level arguments are rejected.

**Example:** `{"experience_id": "...", "step_id": "...", "block_id": "...", "style": {"backgroundColor": "#F0F4FF", "borderRadius": "8px"}}`.

**Pseudo-states.** Here, unlike `style` in the step DSL, states are **not** `":hover"` keys. Nest them under `state` using the selector suffix without the colon: `{"style": {"state": {"hover": {"backgroundColor": "#EEF2FF"}}}}`. The one exception is the placeholder, which keeps its colon: `{"state": {":placeholder": {"color": "#9CA3AF"}}}`.

**Padding.** A `padding` shorthand of 1–4 values is expanded to `paddingTop`, `paddingInlineEnd`, `paddingBottom` and `paddingInlineStart`. Setting `padding` to `null` clears all four.

#### Styling survey questions

Pass the question's `nodeId` as `block_id` and name the part in `part`:

```json
{ "block_id": "<question nodeId>", "part": "field", "style": { "borderColor": "#7C3AED", "borderRadius": "16px" } }
```

| `part` | Questions | Allowed `state` selectors |
|---|---|---|
| `container` | all | none |
| `title` | all | `hover`, `focus` |
| `error` | all | `hover`, `focus` |
| `field` | text | `hover`, `focus`, `active`, `:placeholder` |
| `description`, `counter` | text | `hover`, `focus` |
| `option` | single select, multi select, rating | `hover`, `active`, `focus`, `focus-within`, `active label` |
| `option_control` | single select, multi select, rating | `hover`, `active`, `focus`, `checked`, `checked + label` |
| `option_title` | single select, multi select, rating | `hover`, `active`, `focus` |

- `option`, `option_control` and `option_title` style **every** option of the question in one call. One call styles one question, so to restyle "the inputs" on a step, call once per question.
- On a rating, `option` is each numbered box, `option_title` is the number, and `option_control` is an invisible input covering the box.
- `checked + label` on `option_control` styles the option's title while it is selected. `active label` on `option` styles it while pressed.
- A part refuses keys that would break the question's layout. The error names the key, so drop it and tell the user why. Refused: layout keys on `container` and `option` (`display`, `flexDirection`, `gap`, `justifyContent`, …), `border` on `container` and `field` (use `borderColor`, `borderWidth`, `borderStyle`), `display`, `position`, size keys on text parts, `visibility` on `error`, and all `state` on `container`. On a rating's `option_control`, position, size, opacity and margin keys are also refused.
- Setting a key to `null` removes it (a themed part shows its theme value again), except a container's `margin` and `flexGrow` and a rating `option`'s `width` and `height`, which cannot be removed.
- In a themed experience, keys you set override the theme for that part. Only change parts when the user asks.

---

### `get_dsl_schema`

Returns the full JSON schema for the DSL format. Useful if your AI assistant needs to understand exactly which properties are valid. No parameters required.

---

### `get_example_block_content`

Returns a complete DSL example for a specific block type, including all available properties and usage notes.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `block_type` | Yes | One of: `button`, `image`, `iframe`, `icon`, `survey`, `rich_text`, `cell`, `layout_builder` |

**Example prompt:** *"Show me how to create a two-column layout"* (uses `layout_builder`)

---

## DSL Format

Every step is described with two top-level keys:

- **`container`** — dimensions and styling of the step frame
- **`layout`** — content blocks arranged in a flex layout

```json
{
  "container": {
    "width": "720px",
    "height": "360px",
    "backgroundColor": "#FFFFFF",
    "borderRadius": "8px"
  },
  "layout": {
    "direction": "column",
    "gap": "12px",
    "cells": [
      { "type": "image", "alt": "Welcome illustration" },
      {
        "type": "text",
        "content": [
          { "tag": "h2", "text": "Welcome to Acme!", "align": "center", "fontSize": "24px", "fontWeight": "bold" },
          { "tag": "p", "text": "Let us show you around.", "align": "center", "fontSize": "16px", "color": "#666" }
        ]
      },
      { "type": "button", "label": "Get Started", "actions": ["next"], "backgroundColor": "#5155CA" }
    ]
  }
}
```

> **Property names now match real CSS**, not Appcues-specific aliases. If you built against the DSL before, note the renames below.

| Old property | New property |
|---|---|
| `background` | `backgroundColor` |
| `cornerRadius` | `borderRadius` |
| `paddingX` / `paddingY` | `padding` (CSS shorthand) |
| `size` / `weight` (text/button) | `fontSize` / `fontWeight` |
| `fit` (image) | `objectFit` |
| Cell `borderColor` / `borderWidth` / `borderStyle` | Cell `border` (shorthand, inside `parentCell`) |

### Container Options

| Property | Type | Default | Description |
|---|---|---|---|
| `width` | string | `"720px"` | Container width |
| `height` | string | `"360px"` | Container height |
| `backgroundColor` | string | `"#FFFFFF"` | Background color |
| `borderRadius` | string | `"8px"` | Border radius |
| `boxShadow` | string | `"0px 6px 16px 0px rgba(0, 0, 0, 0.2)"` | Box shadow |
| `border` | string | `"none"` | Border shorthand (e.g. `"1px solid #ccc"`) |
| `padding` | string | `"0px"` | Inner padding |
| `minWidth` / `maxWidth` | string | – | Embed containers only. Embeds are always `100%` wide, so use these to constrain them. |
| `variant` | string | – | Theme variant for the container. Set when the experience has a theme. |
| `closeX` | boolean \| object | see below | The close X in the container's corner. `false` hides it, `true` shows the default, an object shows it styled. See [Close X](#close-x). |

### Close X

The close X dismisses the experience **without** marking it complete. Set it on the container:

```json
{
  "container": {
    "closeX": {
      "size": 16,
      "color": "#1F2937",
      "hoverColor": "#5155CA",
      "backgroundColor": "#F3F4F6",
      "borderRadius": "50%",
      "margin": "8px",
      "position": "top-left"
    }
  },
  "layout": { "cells": [{ "type": "text", "content": [{ "text": "Hi" }] }] }
}
```

| Property | Type | Default | Description |
|---|---|---|---|
| `size` | integer | `14` | Edge length of the X in pixels, 8–48 |
| `color` | string | `"#000000"` | Color of the X |
| `hoverColor` | string | – | Color of the X while hovered |
| `backgroundColor` | string | `"transparent"` | Background behind the X. The button has 8px padding, so this shows as a badge |
| `borderRadius` | string | `"6px"` | Corner radius of the background (e.g. `"50%"` for a circle) |
| `margin` | string | `"12px"` | Distance from the container's edges (CSS shorthand, 1–4 values) |
| `position` | string | `"top-right"` | `"top-right"` or `"top-left"` |
| `variant` | string | – | Theme variant name. Set when the experience has a theme |

An object **replaces** the current close X, so include every style the user wants to keep. When `closeX` is omitted, the step keeps the close X it already has (or its lack of one). A step with no content yet gets the default for its type: shown on tooltips, hidden on modals and embeds. To simply show or hide the X, use `update_step` with `close_button`; use `container.closeX` to change how it looks or where it sits. Don't add a custom button for an ordinary close request.

### Layout Structure

| Property | Type | Default | Description |
|---|---|---|---|
| `direction` | `"column"` \| `"row"` | `"column"` | Flex direction |
| `cells` | array | required | Array of blocks |
| `gap` | string | – | Gap between cells (e.g. `"8px"`). Prefer this over per-block margin for uniform spacing. |

### Block Types

**Image**

```json
{ "type": "image", "src": "https://images.appcues.com/...", "alt": "Description", "objectFit": "cover", "actions": [...] }
```

| Property | Default | Notes |
|---|---|---|
| `src` | placeholder | Appcues CDN or Cloudinary URLs only — see [Image Sourcing](#image-sourcing) |
| `alt` | `"Image"` | |
| `objectFit` | `"cover"` | `"cover"` or `"contain"` |
| `actions` | – | Optional, for clickable images |
| `variant` | – | Theme variant name |

**IFrame**

```json
{ "type": "iframe", "url": "https://www.youtube.com/watch?v=..." }
```

| Property | Notes |
|---|---|
| `url` | Direct src or share URL (known share URLs, e.g. YouTube watch links, are auto-normalized). One of `url`/`html` required. |
| `html` | Pasted `<iframe>` snippet. One of `url`/`html` required. |
| `style` | Custom CSS; `width` is always 100%, `height` defaults to auto |

**Icon**

A small decorative icon: a single emoji, or a custom SVG. Use it beside a heading or as a badge. Icons are hidden from screen readers, so use an image block when the picture carries meaning.

```json
{ "type": "icon", "emoji": "🚀", "name": "rocket", "size": 32, "backgroundColor": "#EEF2FF", "borderRadius": "50%", "padding": "8px" }
```

| Property | Default | Notes |
|---|---|---|
| `emoji` | – | A single emoji. Exactly one of `emoji` or `url` is required |
| `url` | – | Custom SVG URL on `images.appcues.com` or `res.cloudinary.com` (e.g. from `upload_image`). Exactly one of `emoji` or `url` is required |
| `name` | the emoji, or `"Custom icon"` | Icon name; for emoji use its short id (e.g. `"rocket"`, `"star"`) |
| `size` | `24` | Square edge length in pixels, 8–128 |
| `backgroundColor` | – | Background behind the icon |
| `borderRadius` | – | Corner radius of the background (e.g. `"50%"`) |
| `padding` | – | Space between icon and background edge; grows the box, never the icon |

Icons take **no `margin`**, `actions`, or `variant` — use `padding` or the layout's `gap` for spacing. If validation reports that no schema matched an icon cell, check that exactly one of `emoji`/`url` is set and that no `margin` was given. To place an icon beside text, put both in a nested `"row"` layout.

**Text**

A text block holds one or more `TextNode`s (headings, paragraphs). Prefer a single text block with multiple nodes over separate text blocks when a heading and body are grouped together.

```json
{
  "type": "text",
  "content": [
    { "tag": "h2", "text": "Welcome!", "align": "center", "fontSize": "28px", "fontWeight": "bold", "color": "#1a1a1a" },
    { "tag": "p", "text": "Get started with our quick tour.", "align": "center", "fontSize": "16px", "color": "#666666" }
  ]
}
```

TextBlock: `content` (array of TextNode, required), `margin`.

TextNode: `text` (required), `tag` (`"p"` | `"h1"`–`"h5"`, default `"p"`), `align` (default `"center"`), `fontSize`, `fontWeight`, `color`, `fontFamily`, `lineHeight`, `fontStyle`, `textDecoration`, `variant`.

**Button**

```json
{ "type": "button", "label": "Click Me", "actions": ["next"], "backgroundColor": "#5155CA", "color": "#FFFFFF", "borderRadius": "0px" }
```

| Property | Default |
|---|---|
| `label` | required |
| `actions` | – |
| `backgroundColor` | `"#5155CA"` |
| `color` | `"#FFFFFF"` |
| `borderRadius` | `"0px"` |
| `fontSize` | `"14px"` |
| `fontWeight` | `"normal"` |
| `padding` | `"12px 16px"` |
| `border` | – |
| `submit` | `false` — makes this the button that submits the step's survey answers. See [Survey Questions](#survey-questions) |
| `variant` | – |

**Nested Layout**

For complex layouts (e.g. side-by-side content), nest a layout inside `cells`:

```json
{
  "type": "layout",
  "direction": "row",
  "cells": [
    { "type": "text", "content": [{ "text": "Left column" }] },
    { "type": "text", "content": [{ "text": "Right column" }] }
  ]
}
```

Nested layouts accept `style` for advanced CSS.

### Survey Questions

Four blocks collect answers from visitors: `survey_text`, `survey_single_select`, `survey_multi_select` and `survey_rating`. They can go on **modal and embed steps only**, not tooltips. (NPS surveys are still created in the builder wizard — don't build one from a rating.)

A step's questions are answered together. When the visitor clicks the step's **submit button** (a `button` with `"submit": true`), every question on the step is checked. If any answer is invalid, that question's `errorMessage` is shown and nothing else happens. Otherwise all answers are recorded and then the button's other `actions` run (usually `"next"`). Answers from every step of an experience are reported together as one survey on its analytics page.

- A step with survey questions **must** have at least one submit button; a step without survey questions must not have one.
- Other buttons (Back, Skip) and the close X never submit answers.
- On the last step use `"close"` instead of `"next"`, or `{ "type": "close", "markComplete": true }` if finishing the survey should complete the flow.

```json
{ "type": "button", "label": "Submit", "submit": true, "actions": ["next"] }
```

**Common question properties**

| Property | Type | Default | Description |
|---|---|---|---|
| `reportingName` | string | required | The question's name in survey reports and exports. 1–100 characters, descriptive, unique within the experience (never reuse a name, even across steps) |
| `title` | string | required | The question as the visitor reads it (1–500 characters) |
| `errorMessage` | string | `"Invalid field"` | Shown under the question when validation fails. Write a specific one whenever the question has validation |
| `fieldId` | string | – | Only for questions that already exist — see [Editing survey questions](#editing-survey-questions) |
| `variant` | string | – | Theme variant name. Set when the experience has a theme |

Survey questions take no `actions`, `style` or `margin`. Space them with the layout's `gap` and `parentCell`, and restyle them with [`update_block_style`](#update_block_style) after building.

**`survey_text`** — free text

| Property | Type | Default | Description |
|---|---|---|---|
| `description` | string | – | Helper text under the field |
| `placeholder` | string | `"Type your answer"` | Placeholder inside the field |
| `format` | `"short"` \| `"long"` | `"short"` | One-line input or multi-line text area |
| `inputType` | `"text"` \| `"email"` | `"text"` | `"email"` validates the address. Short format only |
| `required` | boolean | `false` | An answer is required |
| `minLength` | integer | – | Fewest characters. Needs `required: true` |
| `maxLength` | integer | – | Most characters |

**`survey_single_select`** (radio buttons) and **`survey_multi_select`** (checkboxes)

| Property | Type | Default | Description |
|---|---|---|---|
| `options` | array of strings | required | 1–20 unique choices, shown in order. The text is also the recorded answer |
| `required` | boolean | `false` | Single select only: one option must be chosen |
| `minOptions` | integer | – | Multi select only: fewest choices. `1` makes the question required |
| `maxOptions` | integer | – | Multi select only: most choices. Needs `minOptions` |

**`survey_rating`** — numbered boxes

| Property | Type | Default | Description |
|---|---|---|---|
| `min` | integer | `0` | Lowest score, 0–10 |
| `max` | integer | `10` | Highest score, 0–20. Must be greater than `min` and at most `min + 10` |
| `required` | boolean | `false` | A score must be chosen |

A rating has no end labels, so put the meaning of the ends in `title` (e.g. "How easy was setup? (1 = hard, 5 = easy)").

```json
{
  "type": "survey_multi_select",
  "reportingName": "Goals",
  "title": "What do you want to do first?",
  "options": ["Invite my team", "Connect my data", "Build a report"],
  "minOptions": 1,
  "maxOptions": 2,
  "errorMessage": "Choose one or two options"
}
```

#### Editing survey questions

Existing questions appear in `get_experience_details` as blocks whose `blockType` is `SurveyText`, `SurveySingleSelect`, `SurveyMultiSelect` or `SurveyRating`, each with a `surveyFieldId` (the question's id) and `surveyFieldName` (its reporting name).

- **Rewriting a step that has questions (`update_step_content`):** every existing question must be in the new content with `fieldId` set to its `surveyFieldId`. This keeps its answers connected in reports. You can change a question's title, options and validation; changing `reportingName` renames it in reports. You can't change its type — remove it and add a new one.
- **Removing a question:** leave it out of the new content **and** list its id in `removeSurveyFields`. Only do this when the user asked to remove it. A rewrite that silently drops a question is rejected and the error names it. If you remove a step's last question, also remove `submit` from its button.
- **Wording-only changes:** prefer `replace_step_text`. Renaming an option changes the answer recorded from then on, so tell the user earlier answers keep the old wording in reports.
- **Tooltips with questions** can't be rewritten with `update_step_content`; use `replace_step_text` for wording or edit in the builder.
- **Moving a question to another step** isn't possible with its `fieldId`: remove it from the source step, then add it to the target as a new question. Its earlier answers stay under the old question in reports.

Agent-built text questions get the survey character counter automatically.

### Actions

Actions go on `button` and `image` blocks. Combine multiple actions in one array.

| Shorthand | Description |
|---|---|
| `"next"` | Go to next step |
| `"prev"` | Go to previous step (not valid on the first step — see [Constraints](#constraints)) |
| `"close"` | Close the experience |

| Object action | Format |
|---|---|
| Close and complete | `{"type": "close", "markComplete": true}` — closes the experience and marks it complete. Only when the user asked for it. Can't be combined with `next`, `prev` or `goTo` on the same block |
| Redirect | `{"type": "redirect", "url": "https://...", "newTab": true}` |
| Go to step | `{"type": "goTo", "stepId": "step-uuid"}` |
| Track event | `{"type": "track", "event": "Event Name", "properties": {...}}` |
| Set user properties | `{"type": "setProperties", "properties": {"key": "value"}}` |
| Trigger another flow | `{"type": "triggerFlow", "flowId": "flow-uuid", "url": "https://optional-url.com"}` |
| Toggle | `{"type": "toggle", "selector": "#element", "actions": ["close"]}` |

**Link CTA buttons to real destinations when you can.** If the conversation gives you context about what's being built — a brand's website, product docs, a specific page — and there's an obvious real URL a button should point to (a booking/signup page, a pricing page, a specific feature's docs), add a `redirect` action for it rather than leaving the button as a bare `next`/`close`. Check the source (e.g. fetch the site) for the specific page that matches the button's intent — a "Reserve Your Spot" button on a coworking site's booking flow should point at the actual booking portal, not the homepage. Pair `redirect` with `"close"` in the actions array so the flow dismisses itself as it sends the user onward. Only do this when the match is genuinely obvious from context already provided — don't invent or guess a URL that wasn't grounded in something you fetched or were given.

### Cell Options (`parentCell`)

Every block or nested layout in `cells` is wrapped by a Cell. Use `parentCell` to control that cell's sizing, alignment, and visual styling.

| Property | Type | Description |
|---|---|---|
| `expectedSize` | number | **Required on every top-level cell in a layout — not just the ones you care about.** Estimated pixel height (column) or width (row) the block needs. The parser normalizes sibling values into proportional flex weights automatically — use equal values to keep cells equally sized. |
| `verticalAlign` | string | Vertical position within the cell (→ CSS `alignItems`) |
| `horizontalAlign` | string | Horizontal position within the cell (→ CSS `justifyContent`) |
| `backgroundColor` | string | Cell background color |
| `backgroundImage` | string | Cell background gradient (e.g. `"linear-gradient(135deg, #667eea, #764ba2)"`) |
| `borderRadius` | string | Cell corner radius |
| `border` | string | Cell border shorthand |

> ⚠️ **Overlap gotcha, confirmed by testing:** if you set `expectedSize` on *some* sibling cells but leave it off others, the omitted cells silently default to a flex weight of **1** — not "size to content." In a column with an image at `expectedSize: 160` and two undecorated siblings (default weight 1 each, total 162), the image claims ~355 of a 360px container and the other two cells get squeezed to a few pixels of allocated space combined. Flex children aren't clipped to that space by default, so their text/buttons render at natural size and **visually overlap** the image and each other instead of shrinking. This is easy to trigger by adding `parentCell.expectedSize` only to the block you're "sizing" (e.g. an image) and forgetting the text/button sections below it.
>
> Fix: give **every** top-level cell in the layout an explicit `expectedSize`, and set the container's `height` to roughly the **sum** of those values so the proportions map to real pixels instead of being stretched or starved. Rule of thumb for a flow step: estimate each section's natural height (image banner ~150–200px, a heading+paragraph block ~110–140px, a button row with padding ~70–90px), sum them for the container `height`, and assign each section that same estimate as its `expectedSize`.

**Sizing example** — a 390px-tall column with an image (180px), title+body (130px), and button (80px), where every cell has `expectedSize` and the container `height` is the sum:

```json
{
  "container": { "height": "390px" },
  "layout": {
    "direction": "column",
    "cells": [
      { "type": "image", "src": "...", "parentCell": { "expectedSize": 180 } },
      { "type": "text", "content": [{ "tag": "h2", "text": "Welcome", "fontSize": "24px", "fontWeight": "bold" }, { "text": "Long description..." }], "parentCell": { "expectedSize": 130 } },
      { "type": "button", "label": "Continue", "actions": ["next"], "parentCell": { "expectedSize": 80 } }
    ]
  }
}
```

### Block Margin

`text`, `button`, `image`, and `iframe` blocks accept `margin` for per-block spacing (CSS shorthand). Icon and survey blocks do **not** accept `margin` — use `gap` and `parentCell` (and an icon's `padding`). Prefer layout `gap` for uniform spacing between cells; use `margin` for one-off exceptions.

```json
{ "type": "text", "content": [{ "text": "Spaced text" }], "margin": "16px 24px" }
```

### Custom Styles

Blocks (except text, which uses TextNode properties instead), containers, and cells accept a `style` property for advanced CSS, merged with defaults. Pseudo-classes (`:hover`, `:active`, `:focus`) and pseudo-elements (`::before`, `::after`) are nested objects inside `style`, supported on button, layout, and container.

```json
{
  "type": "button",
  "label": "Fancy Button",
  "actions": ["next"],
  "backgroundColor": "#5155CA",
  "style": {
    "boxShadow": "0 4px 12px rgba(81, 85, 202, 0.4)",
    ":hover": { "backgroundColor": "#4A4AE0", "transform": "scale(1.05)" },
    ":active": { "transform": "scale(0.98)" }
  }
}
```

### Experience Types

- **flow** (default): Overlay dialog (Flows 2.0), fixed pixel dimensions (e.g. 720×360px).
- **embed**: Inline experience within the page — banners, cards, inline announcements. `width` is always `100%`.
- **banner**: Persistent top-of-page banner with dismiss button. Created with default content — step content cannot be customized via tools.
- **persistent**: Pin experience. Created as a shell — step content cannot be customized via tools.
- NPS and Launchpad experiences cannot be created via tools — use the builder wizard.

### Tooltips

Tooltips are a step type within flow experiences, not a separate experience type: `create_experience` with `type: "flow"`, then `add_step` with `type: "tooltip"`. A human normally attaches the tooltip's target DOM selector in the builder; you can set it with `update_step`'s `target_selector` only when the user explicitly provides a selector.

Tooltip container defaults differ from flow modals:

| Property | Default | Notes |
|---|---|---|
| `width` | `"320px"` | Smaller than flow modals |
| `height` | `"220px"` | Smaller than flow modals |
| `borderRadius` | `"0px"` | |
| `boxShadow` | `"none"` | Uses a CSS `drop-shadow` filter instead |
| `border` | `"none"` | |

An arrow primitive and close (X) button are auto-injected by the parser.

### Embeds

Embed containers use different defaults from flows:

| Property | Default | Notes |
|---|---|---|
| `width` | `"100%"` | Fills parent container; use `minWidth`/`maxWidth` to constrain |
| `height` | `"176px"` | Shorter than flows since it sits inline |
| `borderRadius` | `"0px"` | Blends into the page |
| `direction` | `"row"` | Horizontal layout for banner-like designs |
| `boxShadow` | *none* | Embeds don't float above the page |

Prefer shorter heights (100–250px) since embeds share space with page content. `"row"` layouts suit banner-style embeds; `"column"` suits card-style. Avoid `boxShadow`/`borderRadius` unless the embed should look like a distinct card.

### Constraints

- **First step:** `update_step` `navigation` (`redirect`/`waitForUrl`) must not be used on a flow's first step — it displays immediately with no "before shown" phase. A `prev` action must not be used on the first step — there's no previous step to go to.
- **Spacing:** Prefer `gap` for uniform spacing between cells, `margin` for per-block spacing, `padding` for layout/container inner padding.
- **Never leave `expectedSize` partially set.** Setting it on some top-level cells (e.g. an image) but not others in the same layout causes the undecorated cells to default to a flex weight of 1, get squeezed to near-zero allocated height, and render their content overlapping their neighbors instead of shrinking to fit. Set `expectedSize` on every cell in the layout and size the container `height` to their sum — see [Cell Options](#cell-options-parentcell). Always render a screenshot with `get_experience_screenshot` after building step content and check for overlap before calling it done.

### Image Sourcing

Do not set `src` on image blocks to arbitrary external URLs. Only use URLs returned by `upload_image` (or `generate_image`, in-app only) — see [Image Tools](#image-tools). If no image is needed yet, omit `src` to use a default placeholder — external URLs are silently replaced with a placeholder.

---

## Step Configuration Tools

Step-level behavior (as opposed to visual content) is set with a single tool, `update_step`. Flow and embed experiences only, unless noted.

### `update_step`

Updates one or more step settings in a single call. **Pass only the keys you want to change** — anything omitted is left alone. The tool replaces the older per-setting tools (`update_step_close_button`, `update_step_position`, `update_step_animations`, `update_step_backdrop`, `update_step_navigation`, `update_step_delay`, `update_step_advance_on_error`); those names no longer exist.

| Parameter | Required | Description |
|---|---|---|
| `experience_id` | Yes | ID of the experience |
| `step_id` | Yes | ID of the step |
| `close_button` | No | Boolean. `true` shows, `false` hides the native close button |
| `position` | No | Flow modal position: `top-left`, `top-center`, `top-right`, `center-left`, `center`, `center-right`, `bottom-left`, `bottom-center`, `bottom-right`. Modal steps only |
| `animations` | No | Object with optional `entrance` and `exit` (see below) |
| `backdrop` | No | Object: `enabled`, `color`, `blur`, `backdrop_style` (see below) |
| `navigation` | No | Object: `mode` (required), `url`, `url_pattern`. Page navigation that runs *before* the step is shown. Flow experiences only |
| `delay` | No | Integer milliseconds to wait before showing the step. `0` removes the delay. Common values: 500, 1000, 2000, 5000 |
| `advance_on_error` | No | Object: `action` (required), `target_step_id`, `wait_time`. Tooltip steps only |
| `advance_on_click` | No | Boolean. Tooltip steps only |
| `target_selector` | No | Object: `selector` (required), `order`, `text`. Tooltip steps only |

At least one key besides the IDs must be provided. The tool is idempotent, and unknown top-level parameters are rejected.

**Order and failures.** When several keys are sent, they are applied in a fixed order: `close_button`, `position`, `animations`, `backdrop`, `navigation`, `delay`, `advance_on_error`, `target_selector`, `advance_on_click`. The first error stops the rest, but keys applied before it have already been written, so re-read the step if a multi-key call fails.

**Do not call `update_step` in parallel with `update_step_content`, `replace_step_text` or `update_block_style` on the same step.** They write the same step, and a parallel call can drop the other's changes (`close_button` and `position` rewrite the step's `content`; on embeds `update_step_content` also rewrites its `traits`). Call content tools first, then `update_step`.

#### `animations`

Omit a key to leave it unchanged; set an effect to `"none"` to remove it. At least one of `entrance` or `exit` is required when `animations` is sent.

| Key | Values |
|---|---|
| `entrance` | `none`, `fade_in`, `scale_in`, `spring_scale`, `slide_in_top`, `slide_in_bottom`, `slide_in_left`, `slide_in_right`, `drawer_in_top`, `drawer_in_bottom`, `drawer_in_left`, `drawer_in_right`. Default `fade_in` |
| `exit` | `none`, `fade_out`, `scale_out`, `slide_out_top`, `slide_out_bottom`, `slide_out_left`, `slide_out_right`, `drawer_out_top`, `drawer_out_bottom`, `drawer_out_left`, `drawer_out_right`. Default `none` |

#### `backdrop`

The overlay behind a step. Auto-detects flow vs. tooltip step type.

| Key | Applies to | Description |
|---|---|---|
| `enabled` | Flow only | Show the backdrop overlay. Defaults to `true` once `backdrop` is sent |
| `color` | Flow only | CSS hex with optional alpha, e.g. `"#000000"`, `"#00000080"`. Default `"#00000080"` |
| `blur` | Flow only | One of `none`, `2px`, `4px`, `8px`, `12px`, `16px`. Default `"none"` |
| `backdrop_style` | Tooltip only | One of `none`, `soft`, `hard`. Default `"soft"` |

Backdrop settings are rejected on non-flow experiences.

#### `navigation`

| Key | Required | Description |
|---|---|---|
| `mode` | Yes | `redirect`, `waitForUrl`, or `none` to remove |
| `url` | For `redirect` | `http(s)` URL to navigate to before the step renders |
| `url_pattern` | For `waitForUrl` | URL pattern to match before showing the step |

Not valid on the first step (see [Constraints](#constraints)).

#### `advance_on_error`

"Advance if the selector can't be found" — **tooltip steps in flows only**.

| Key | Required | Description |
|---|---|---|
| `action` | Yes | `next` to skip forward, `goTo` to jump to `target_step_id`, `off` to remove |
| `target_step_id` | For `goTo` | A *different* step in this experience |
| `wait_time` | No | Milliseconds to wait before advancing. Default 500, max 30000 |

#### `advance_on_click`

The builder's "Advance on click of element" setting — **tooltip steps in flows only**. `true` advances to the next step when the user clicks the tooltip's target element; `false` turns it off. Other actions already on the step are kept.

#### `target_selector`

The page element a tooltip anchors to — **tooltip steps in flows only**. **Only set this when the user explicitly provides a selector — never guess one.** It replaces any existing selector and refinements, so omit `order`/`text` to clear them. If `advance_on_click` is already on, it follows the new selector.

| Key | Required | Description |
|---|---|---|
| `selector` | Yes | Non-empty CSS selector, e.g. `"#save-button"` or `".nav a"` |
| `order` | No | Integer ≥ 1. When the selector matches several elements, anchor to the Nth match (1 = first) |
| `text` | No | Only match elements whose full text equals this (case-insensitive) |

#### Common requests

- **Show or hide the close X:** `close_button`. To change how the X looks or where it sits, use `container.closeX` in `update_step_content` — see [Close X](#close-x).
- **Place a modal:** `position`. Don't use theme or custom CSS for ordinary placement. Resize with the container `width`/`height` in `update_step_content`.
- **Tooltip skips if its element is missing:** `advance_on_error`.

### Reordering vs. positioning

`move_step_order` changes the step **sequence** (which comes first/second/third). `update_step` `position` changes the **visual placement** of a modal on the page (e.g. bottom-right corner).

---

## Theming Tools

An experience theme is a set of published visual defaults (colors, fonts, spacing, per-component variants) that step content can bind to instead of hardcoding styles.

### `list_experience_themes`

Lists published experience themes, with optional name search and pagination.

| Parameter | Required | Description |
|---|---|---|
| `search_term` | No | Filter themes by name |
| `offset` | No | Default 0 |
| `limit` | No | Default 100, max 500 |

Always call this when a user asks about themes — never answer from general knowledge.

### `get_experience_theme`

Gets theme metadata and flattened presets/tokens/components maps, for detailed editing decisions.

| Parameter | Required | Description |
|---|---|---|
| `theme_id` | Yes | Published experience theme ID |

### `get_experience_theme_variants`

Gets component variant names and key visual style hints (a compact inventory, not the full theme) for a theme's web components.

| Parameter | Required | Description |
|---|---|---|
| `theme_id` | Yes | Published experience theme ID |

**Call this before building DSL for any themed experience** — do not guess variant names:

1. Note the `theme` ID on the experience (from `create_experience`, `update_experience`, or `get_experience_details`) — a default theme may be auto-assigned on creation.
2. Call `get_experience_theme_variants` with that ID.
3. Review the returned style hints to understand what each variant looks like.
4. Set `"variant": "variant_name"` on each themable block in your DSL, choosing the closest match to the user's intent.
5. Call it again after `update_experience` reassigns a theme, or before any `update_step_content` on a themed experience where you haven't already retrieved variants in this conversation.

If no variant is specified, `"default"` is used; an unknown variant falls back to `"default"`. Survey questions and the close X also accept a `variant`.

**Themable components:** `button`, `p`, `h1`–`h5`, `img`, `cell`, `modal`, `embed`, `tooltip`.

**Respect theme styles** — treat the theme's colors, fonts, borders, and radii as intentional. Don't override them unless the user asks for a different look or the design clearly requires it; only properties explicitly set in the DSL override the theme.

### `create_experience_theme`

Creates a new theme from the base theme model.

| Parameter | Required | Description |
|---|---|---|
| `name` | Yes | Theme name |
| `is_default` | No | If `true`, sets this theme as the account default |

### `update_experience_theme`

Updates a theme's name and/or styles.

| Parameter | Required | Description |
|---|---|---|
| `theme_id` | Yes | Theme to update |
| `name` | No | New name |
| `presets` | No | Studio theme-editor controls: `fontSize`/`spacing` (`S`/`M`/`L`), `fontFamily` (system font) |
| `tokens` | No | Dotted-path token writes (e.g. `colors.primary`, `parts.container.corner-radius`) → new `$value`. Don't write `font.size`, `dimensions.unit`, or `font.family.base` — use `presets` for those. |
| `components` | No | Dotted-path component variant writes (e.g. `web.tooltip.default`) → style maps merged into that variant |

At least one of `name`/`presets`/`tokens`/`components` is required.

### `set_default_experience_theme`

Sets a theme as the account default.

| Parameter | Required | Description |
|---|---|---|
| `theme_id` | Yes | Theme to set as default |

### `list_legacy_themes`

Lists legacy 1.0 CSS themes that can be migrated into experience themes. Returns each theme's `id`, `name` and `isDefault` only.

| Parameter | Required | Description |
|---|---|---|
| `search_term` | No | Filter legacy themes by name |

### `migrate_legacy_theme`

Creates a **published** experience theme by migrating a legacy 1.0 theme.

| Parameter | Required | Description |
|---|---|---|
| `legacy_theme_id` | Yes | Legacy 1.0 theme ID (from `list_legacy_themes`) |
| `is_default` | No | If `true`, sets the new theme as the account default |

---

## Image Tools

### `generate_image`

> **Not available through the MCP server.** This tool exists only in Appcues' in-app assistant. Over MCP, host images with `upload_image` instead.

Generates an AI image for use in experience content and returns its hosted URL.

| Parameter | Required | Description |
|---|---|---|
| `prompt` | Yes | Description of the image to generate |
| `layout` | No | `"square"` (default), `"portrait"`, or `"landscape"` |

### `upload_image`

Hosts an image or SVG on Cloudinary and returns a URL for use in experiences, including custom [icons](#block-types). Pass **exactly one** source:

| Parameter | Required | Description |
|---|---|---|
| `assistant_file_id` | One of the two | The id from a `{{assistant_file:<id>}}` tag preceding a user-attached image in the in-app chat |
| `image_url` | One of the two | A public `https` URL of the image to host. Use this anywhere there is no in-app chat attachment (e.g. over MCP) |

Hostable formats are JPG, PNG, GIF and SVG, up to 5 MB. If the upload fails, the tool returns the reason — relay it to the user.

> Only images hosted on the Appcues CDN or Cloudinary — i.e. URLs returned by `upload_image` (or `generate_image` in-app) — are supported in the DSL. Arbitrary external URLs are silently replaced with a placeholder.

---

## Targeting & Rules Tools

### `get_experience_rule`

Reads the current targeting configuration for an experience: audience conditions, page/domain targeting, trigger event, and frequency.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `experience_id` | Yes | ID of the experience |

**Example prompt:** *"What are the current targeting rules for this flow?"*

---

### `update_experience_rule`

Updates who sees the experience and when it triggers. **Important:** include all values you want to keep — omitted parameters are reset to defaults.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `experience_id` | Yes | ID of the experience |
| `audience` | No | Audience conditions (who sees it). Omit for all users. |
| `url` | No | URL conditions tree (which pages). Omit for any page. |
| `domains` | No | Array of domain strings. Omit for any domain. |
| `trigger_event` | No | Custom event name. Omit for default page view trigger. |
| `trigger_event_conditions` | No | Attribute conditions on the trigger event. |
| `frequency` | No | `"once"` or `"every_time"` |
| `throttle_exempt` | No | `true` to bypass global throttling |

#### URL Targeting Examples

Show on a specific page:
```json
{"and": [{"url": {"operator": "==", "value": "/pricing"}}]}
```

Show on pages starting with `/docs`:
```json
{"and": [{"url": {"operator": "^", "value": "/docs"}}]}
```

Show on pages containing `dashboard`:
```json
{"and": [{"url": {"operator": "*", "value": "dashboard"}}]}
```

#### Audience Targeting Examples

Target users where `plan` equals `"pro"`:
```json
{"and": [{"properties": {"property": "plan", "operator": "==", "value": "pro"}}]}
```

Target a specific segment:
```json
{"and": [{"segments": {"segment": "segment-uuid"}}]}
```

**Example prompt:** *"Only show this flow to users on the /onboarding page who have the role 'admin'"*

---

### `get_audience_schema`

Returns the full JSON schema for audience conditions. No parameters. Use this when you need to understand valid operators and clause types for audience targeting.

---

### `get_trigger_schema`

Returns the JSON schema for a specific trigger condition type.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `type` | Yes | One of: `page`, `screen`, `version`, `trigger_event` |

---

## Publishing and related tools

### `publish_experience` / `unpublish_experience`

Make an experience live, or take it down. Both take a single `id` and work for every experience type. They require the account **publisher** role.

- `publish_experience` immediately affects production content that end users see. The experience must be in draft state with unpublished changes. **Only call it when the user has explicitly asked to publish**, and confirm first if there is any doubt.
- `unpublish_experience` immediately hides a live experience. It stays as a draft and can be republished.

### Other tools used alongside the builder

| Tool(s) | Use |
|---|---|
| `get_experience_details` | Full JSON of an experience, including step content, `nodeId`s and survey field ids. Optional `state`: `draft` (default), `published`, `archived` |
| `get_publish_history` | Takes `id`. Full publish history: first publish, every publish or push of changes, unpublishes, and the windows it was live |
| `get_experience_screenshot` | Takes `id` and optional `step_id` (omit for the first screenshotable step). Returns a PNG for flows, banners and pins. Use it to check a built step |
| `list_tags`, `get_tag`, `create_tag`, `update_tag`, `delete_tag` | Manage tags. Use `list_tags` to find IDs to pass as `tag_ids` on `create_experience` / `update_experience` |
| `list_click_to_track_events`, `get_click_to_track_event`, `create_click_to_track_event`, `update_click_to_track_event` | Manage click-to-track events |
| `list_key_moments`, `get_key_moment`, `create_key_moment`, `update_key_moment`, `set_key_moment_status`, `get_key_moment_references`, `get_key_moment_schema` | Manage key moments |

---

## Tips

- **Everything is a draft until published.** The build tools only modify the draft version of an experience. Publish from Appcues Studio, or with `publish_experience` when the user explicitly asks.
- **`content` is a JSON object, not a string.** Pass `update_step_content`'s `content` as a native JSON object with `container`/`layout` keys, not a JSON-encoded string.
- **CSS property names changed.** The DSL now uses real CSS property names (`backgroundColor`, `borderRadius`, `padding`, `fontSize`, `fontWeight`, `objectFit`) instead of older Appcues-specific aliases — see the rename table in [DSL Format](#dsl-format).
- **Themes are opt-in but automatic.** `create_experience` auto-assigns the account's default theme if one exists and none is specified. If an experience has a theme, call `get_experience_theme_variants` before writing DSL and set `variant` on themable blocks — don't guess variant names.
- **Images:** Only images hosted on the Appcues CDN or Cloudinary are supported. Get URLs from `upload_image` (a chat attachment or a public `image_url`) — omit `src` for a default placeholder otherwise.
- **Use the right tool for the job:** `update_step` for close/X toggles, modal placement, animations, backdrop, navigation, delay and tooltip behavior; `container.closeX` (via `update_step_content`) to style the close X; `update_block_style` (with a `style` object) for styling-only tweaks to existing blocks and survey question parts; `replace_step_text` for copy-only tweaks — reserve `update_step_content` for structural changes.
- **Don't run write tools in parallel on one step.** `update_step`, `update_step_content`, `replace_step_text` and `update_block_style` all write the same step. Run them one after another.
- **Surveys need a submit button.** A step with survey questions must have a `button` with `"submit": true`, and every existing question must be passed back with its `fieldId` when you rewrite the step — see [Survey Questions](#survey-questions).
- **Never guess a tooltip's target.** Only set `target_selector` when the user gives you the selector.
- **`get_experience_details` first.** Fetch it to find a block's `block_id`/`nodeId` before calling `replace_step_text` or `update_block_style`.
- **Read before you write targeting.** Call `get_experience_rule` before `update_experience_rule` so you know what to preserve.
- **Use the schema tools when stuck.** If a step update fails validation, call `get_dsl_schema` or `get_example_block_content` to see the correct format.
- **Set `expectedSize` on every cell, not just one.** Partial `expectedSize` usage (e.g. only on an image) starves undecorated sibling cells down to a sliver of allocated height, and their content overlaps rather than shrinks. Size every top-level cell explicitly and set the container `height` to the sum — then verify with a screenshot.
- **Link buttons to real destinations from context.** If you have an external URL for what's being built (a brand site, docs, a specific page you fetched), and a button's intent obviously maps to a real page on it, add a `redirect` action pointing there instead of leaving a bare `next`/`close` — see [Actions](#actions).
- **The `list_experiences` and `get_experience` tools** (from the base MCP toolset) are available for finding and inspecting existing experiences.
