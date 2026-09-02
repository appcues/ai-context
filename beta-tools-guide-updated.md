# Appcues MCP Beta Tools — Building Flows & Setting Targeting

These tools extend the Appcues MCP server with the ability to **create and edit web experiences** (Flows 2.0, Embeds, Banners, and Pins), **theme them**, and **configure audience targeting and triggers** directly from your AI coding assistant.

> **Note:** These tools create and modify **draft** experiences. Nothing goes live until you publish from Appcues Studio.

## Quick Start

A typical flow-building conversation looks like this:

1. **Create an experience** — give it a name and type. If the account has a default theme, it's assigned automatically.
2. **Add steps** — each step is a screen in the flow.
3. **Check for a theme** — if the experience has a theme, load its variants before writing any content.
4. **Design each step** — set the layout, text, images, and buttons using the DSL.
5. **Configure step behavior** — position, animations, backdrop, delay, or navigation as needed.
6. **Set targeting** — decide who sees it and where.

---

## Flow Building Tools

### `create_experience`

Creates a new web experience and returns its ID.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `name` | Yes | Name for the experience |
| `type` | No | `"flow"` (overlay dialog, default), `"embed"` (inline within the page), `"banner"` (top-of-page banner), or `"persistent"` (pin) |
| `build_url` | No / **Required for `banner` and `persistent`** | The page in the customer's product where the experience will be built and previewed. Must include protocol. |
| `theme_id` | No | Published experience theme ID to assign. Omit to use the account's default theme if one exists. Pass `null` explicitly to create with no theme. |
| `tactic_id` | No | If this content is part of a tactic, pass its ID to link automatically. |

NPS and Launchpad experiences cannot be created via tools — use the builder wizard.

**Example prompt:** *"Create a new flow called 'Welcome Tour'"*

**Response:** Returns the experience ID and, if a theme was assigned (explicitly or by default), its `theme_id`. If a theme is present, call `get_experience_theme_variants` before building step content — see [Theming Tools](#theming-tools).

---

### `update_experience`

Updates top-level experience properties — `name` and/or `theme_id`. Does **not** modify step content.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `experience_id` | Yes | ID of the experience |
| `name` | No | New name |
| `theme_id` | No | Published experience theme ID to (re)assign |

At least one of `name` or `theme_id` must be provided. Reassigning a theme means variants may have changed — call `get_experience_theme_variants` again before your next `update_step_content`.

---

### `add_step`

Adds a new step to an existing experience (flow or embed only). Each step starts with a default template. Returns the new step ID.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `experience_id` | Yes | ID of the experience to add a step to |
| `type` | Yes | `"modal"` or `"tooltip"` for flows, `"embed"` for embeds. Must match the experience type. |

Tooltip steps are a step type within flow experiences, not a separate experience type: `create_experience` with `type: "flow"`, then `add_step` with `type: "tooltip"`. The agent cannot set the tooltip's target DOM selector — a human must enter the builder to attach it to a page element.

**Example prompt:** *"Add two more steps to this flow"*

---

### `move_step_order`

Moves a step before or after another step in the experience sequence (changes ordering only — not visual placement; for that see `update_step_position`).

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

Partial-merges CSS style properties onto an existing block without resending the full DSL. Use this instead of `update_step_content` when you're only changing visual styling on blocks that already exist.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `experience_id` | Yes | ID of the experience |
| `step_id` | Yes | ID of the step |
| `block_id` | Yes | The block's `nodeId`, from the step content structure returned by `get_experience_details` |
| *(any CSS property)* | No | Additional top-level parameters are treated as camelCase CSS properties to merge (e.g. `backgroundColor`, `fontSize`) — only the properties you pass change |

**Example:** call with `{"experience_id": "...", "step_id": "...", "block_id": "...", "backgroundColor": "#F0F4FF", "borderRadius": "8px"}`.

---

### `get_dsl_schema`

Returns the full JSON schema for the DSL format. Useful if your AI assistant needs to understand exactly which properties are valid. No parameters required.

---

### `get_example_block_content`

Returns a complete DSL example for a specific block type, including all available properties and usage notes.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `block_type` | Yes | One of: `button`, `image`, `iframe`, `rich_text`, `cell`, `layout_builder` |

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
| `variant` | string | – | Theme variant for the container. Set when the experience has a theme. |

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

### Actions

Actions go on `button` and `image` blocks. Combine multiple actions in one array.

| Shorthand | Description |
|---|---|
| `"next"` | Go to next step |
| `"prev"` | Go to previous step (not valid on the first step — see [Constraints](#constraints)) |
| `"close"` | Close the experience |

| Object action | Format |
|---|---|
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

`text`, `button`, `image`, and `iframe` blocks accept `margin` for per-block spacing (CSS shorthand). Prefer layout `gap` for uniform spacing between cells; use `margin` for one-off exceptions.

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

Tooltips are a step type within flow experiences, not a separate experience type: `create_experience` with `type: "flow"`, then `add_step` with `type: "tooltip"`. A human must attach the tooltip's target DOM selector in the builder.

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

- **First step:** `update_step_navigation` (`redirect`/`waitForUrl`) must not be used on a flow's first step — it displays immediately with no "before shown" phase. A `prev` action must not be used on the first step — there's no previous step to go to.
- **Spacing:** Prefer `gap` for uniform spacing between cells, `margin` for per-block spacing, `padding` for layout/container inner padding.
- **Never leave `expectedSize` partially set.** Setting it on some top-level cells (e.g. an image) but not others in the same layout causes the undecorated cells to default to a flex weight of 1, get squeezed to near-zero allocated height, and render their content overlapping their neighbors instead of shrinking to fit. Set `expectedSize` on every cell in the layout and size the container `height` to their sum — see [Cell Options](#cell-options-parentcell). Always render a screenshot with `get_experience_screenshot` after building step content and check for overlap before calling it done.

### Image Sourcing

Do not set `src` on image blocks to arbitrary external URLs. Only use URLs returned by `generate_image` or `upload_image` (see [Image Tools](#image-tools)). If no image is needed yet, omit `src` to use a default placeholder — external URLs are silently replaced with a placeholder.

---

## Step Configuration Tools

These control step-level behavior rather than visual content. All require `experience_id` and `step_id`; flow/embed only unless noted.

### `update_step_close_button`

Toggle the native close button on a step.

| Parameter | Required | Description |
|---|---|---|
| `show` | Yes | `true` to show, `false` to hide the native close button |

Use this for ordinary close/X requests instead of adding a custom close button via `update_step_content` — reserve that for when the user explicitly wants a custom dismiss control inside the layout.

### `update_step_position`

Sets the position of a flow modal on the page.

| Parameter | Required | Description |
|---|---|---|
| `position` | Yes | One of: `top-left`, `top-center`, `top-right`, `center-left`, `center`, `center-right`, `bottom-left`, `bottom-center`, `bottom-right` |

Use this for ordinary modal placement requests instead of theme/custom CSS. Use `update_step_content` container `width`/`height` to resize a modal.

### `update_step_animations`

Sets entrance and/or exit animation on a flow step. Omit a parameter to leave it unchanged; set an effect to `"none"` to remove it.

| Parameter | Required | Description |
|---|---|---|
| `entrance` | No | `none`, `fade_in`, `scale_in`, `spring_scale`, `slide_in_top`, `slide_in_bottom`, `slide_in_left`, `slide_in_right`, `drawer_in_top`, `drawer_in_bottom`, `drawer_in_left`, `drawer_in_right`. Default `fade_in`. |
| `exit` | No | `none`, `fade_out`, `scale_out`, `slide_out_top`, `slide_out_bottom`, `slide_out_left`, `slide_out_right`, `drawer_out_top`, `drawer_out_bottom`, `drawer_out_left`, `drawer_out_right`. Default `none`. |

### `update_step_backdrop`

Updates the overlay behind a step. Auto-detects flow vs. tooltip step type.

| Parameter | Applies to | Description |
|---|---|---|
| `enabled` | Flow only | Show the backdrop overlay. Default `true` once this tool is called. |
| `color` | Flow only | CSS hex with optional alpha, e.g. `"#000000"`, `"#00000080"`. Default `"#00000080"`. |
| `blur` | Flow only | One of `none`, `2px`, `4px`, `8px`, `12px`, `16px`. Default `"none"`. |
| `backdrop_style` | Tooltip only | One of `none`, `soft`, `hard`. Default `"soft"`. |

### `update_step_navigation`

Configures page navigation that runs *before* a step is shown. Flow experiences only. Not valid on the first step (see [Constraints](#constraints)).

| Parameter | Required | Description |
|---|---|---|
| `mode` | Yes | `redirect`, `waitForUrl`, or `none` to remove |
| `url` | Required for `redirect` | URL to navigate to before the step renders |
| `url_pattern` | Required for `waitForUrl` | URL pattern to match before showing the step |

### `update_step_delay`

Adds a time delay before a step is shown.

| Parameter | Required | Description |
|---|---|---|
| `duration` | Yes | Milliseconds. `0` removes the delay. Common values: 500, 1000, 2000, 5000. |

### `update_step_advance_on_error`

Configures "advance if selector can't be found" on a **tooltip step only**.

| Parameter | Required | Description |
|---|---|---|
| `action` | Yes | `next` to skip forward, `goTo` to jump to `target_step_id`, `off` to remove |
| `target_step_id` | Required for `goTo` | Another step in this experience |
| `wait_time` | No | Milliseconds to wait before advancing. Default 500, max 30000. |

### Reordering vs. positioning

`move_step_order` changes the step **sequence** (which comes first/second/third). `update_step_position` changes the **visual placement** of a modal on the page (e.g. bottom-right corner).

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

If no variant is specified, `"default"` is used; an unknown variant falls back to `"default"`.

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

---

## Image Tools

### `generate_image`

Generates an AI image for use in experience content and returns its hosted URL.

| Parameter | Required | Description |
|---|---|---|
| `prompt` | Yes | Description of the image to generate |
| `layout` | No | `"square"` (default), `"portrait"`, or `"landscape"` |

### `upload_image`

Uploads a user-attached chat image to get a hosted URL for use in experiences.

| Parameter | Required | Description |
|---|---|---|
| `assistant_file_id` | Yes | The id from a `{{assistant_file:<id>}}` tag preceding the image in the conversation |

For newly generated images use `generate_image` instead.

> Only images hosted on the Appcues CDN or Cloudinary — i.e. URLs returned by these two tools — are supported in the DSL. Arbitrary external URLs are silently replaced with a placeholder.

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

## Tips

- **Everything is a draft.** These tools only modify the draft version of an experience. Publish from Appcues Studio when ready.
- **`content` is a JSON object, not a string.** Pass `update_step_content`'s `content` as a native JSON object with `container`/`layout` keys, not a JSON-encoded string.
- **CSS property names changed.** The DSL now uses real CSS property names (`backgroundColor`, `borderRadius`, `padding`, `fontSize`, `fontWeight`, `objectFit`) instead of older Appcues-specific aliases — see the rename table in [DSL Format](#dsl-format).
- **Themes are opt-in but automatic.** `create_experience` auto-assigns the account's default theme if one exists and none is specified. If an experience has a theme, call `get_experience_theme_variants` before writing DSL and set `variant` on themable blocks — don't guess variant names.
- **Images:** Only images hosted on the Appcues CDN or Cloudinary are supported. Get URLs from `generate_image` or `upload_image` — omit `src` for a default placeholder otherwise.
- **Use the right tool for the job:** `update_step_close_button` for close/X toggles, `update_step_position` for modal placement, `update_block_style` for styling-only tweaks to existing blocks, `replace_step_text` for copy-only tweaks — reserve `update_step_content` for structural changes.
- **`get_experience_details` first.** Fetch it to find a block's `block_id`/`nodeId` before calling `replace_step_text` or `update_block_style`.
- **Read before you write targeting.** Call `get_experience_rule` before `update_experience_rule` so you know what to preserve.
- **Use the schema tools when stuck.** If a step update fails validation, call `get_dsl_schema` or `get_example_block_content` to see the correct format.
- **Set `expectedSize` on every cell, not just one.** Partial `expectedSize` usage (e.g. only on an image) starves undecorated sibling cells down to a sliver of allocated height, and their content overlaps rather than shrinks. Size every top-level cell explicitly and set the container `height` to the sum — then verify with a screenshot.
- **Link buttons to real destinations from context.** If you have an external URL for what's being built (a brand site, docs, a specific page you fetched), and a button's intent obviously maps to a real page on it, add a `redirect` action pointing there instead of leaving a bare `next`/`close` — see [Actions](#actions).
- **The `list_experiences` and `get_experience` tools** (from the base MCP toolset) are available for finding and inspecting existing experiences.
