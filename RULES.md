# Rules learned (one line each, cause → rule)

1. frappe-ui's package "exports" hides deep paths → locate internals (colors.json) relative to an exported entry via `require.resolve("frappe-ui/tailwind")`.
2. A Tailwind theme colour used where Tailwind injects its own alpha (ringColor.DEFAULT) must be a `({ opacityValue }) => …` function, not an `<alpha-value>` string.
3. Codemods that delete class tokens must exclude `;` from the token pattern and be verified by exact text equivalence (old minus tokens == new, modulo whitespace).
4. Codemods delete a token together with its own leading whitespace only; never re-flow the surrounding whitespace.
5. Frontend unit tests run without a DOM environment → stub browser globals in the test file (Vue also needs `document.createElement`) instead of adding devDependencies.
6. Colours hard-coded in `<style>` blocks or inline styles read `var(--hub-…, <light literal>)`, with the variable defined only under `html.dark`, so light output stays identical.
7. Everything under `frontend/src` is scanned by Tailwind → keep class-like words (e.g. `sepia`, `text-gray-200`) out of comments and test strings.
8. The live page loads Frappe's website CSS (Bootstrap 4.6, `!important` utilities `.bg-white`, `.text-white`, `.border`, `.border-white`) before ours → every visual check must load Bootstrap 4.6.2 first, and dark overrides of those names need `html.dark .x { … !important }`.
