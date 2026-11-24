# Making elements targetable (`data-appcues` attributes)

Source: docs.appcues.com/installation-overview/preparing-your-frontend-for-appcues-best-practices-for-targeting-elements and /installation-overview/install-appcues-without-rework

Appcues tooltips, hotspots and Click-to-Track events attach to CSS selectors. Auto-generated class names (`.css-1a2b3c4`, `sc-…`, `Component_x__hash`) and runtime IDs (`#react-select-9-option-1`) change on the next build, and **nothing errors when that happens**: content just silently stops appearing. Stable attributes prevent this.

## What to do for each row in the plan's "elements to tag" table

1. Find the component that renders the element (grep the visible label, the route, or the handler name from the plan's "Where it is" column). If several candidates match, show them and ask.
2. Add the exact attribute from the plan **to the element itself** (the `<button>`, `<a>`, input, card or row), not a high-level wrapper, unless the whole container is the target:
   ```tsx
   <button data-appcues="search-run" onClick={runSearch}>Search</button>
   ```
3. If it's a design-system component (`<Button>`), check that it forwards unknown props / `data-*` to the DOM node. If it doesn't, ask before changing the shared component. Alternatives are a wrapper prop, or tagging at the call site through a supported prop.
4. Keep the value **static**: never interpolate IDs or indexes into it. For repeated elements (list rows, cards), use one shared value (`data-appcues="feature-card"`). Appcues can refine with position.
5. Same attribute in every environment and every feature-flag variant of the element.
6. If the element is rendered in several places (header and mobile nav, for example), ask whether each should be tagged and whether they need distinct values.

## Conventions

- Use the plan's values. If the user asks you to suggest extra ones, use the kebab-case `area-action` pattern (`primary-cta`, `nav-settings`, `modal-confirm`).
- `data-appcues` is preferred because the Builder picks it up automatically. `data-testid` works as a fallback only if it's unique and survives the production build (some builds strip it).
- Don't use these attributes for styling or tests. They're a contract with Appcues content.
- Avoid unnecessary re-mounting around targets (unstable React `key`s, conditional wrappers that swap DOM structure).

## Handoff note to include

Suggest that the team record these attributes as a "targeting contract" (for example in their README or a code comment). Before anyone renames or removes one, they should check whether Appcues content depends on it.
