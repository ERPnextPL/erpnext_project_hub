# Rules learned (one line each, cause → rule)

1. frappe-ui's package "exports" hides deep paths → locate internals (colors.json) relative to an exported entry via `require.resolve("frappe-ui/tailwind")`.
2. A Tailwind theme colour used where Tailwind injects its own alpha (ringColor.DEFAULT) must be a `({ opacityValue }) => …` function, not an `<alpha-value>` string.
3. Codemods that delete class tokens must exclude `;` from the token pattern and be verified by exact text equivalence (old minus tokens == new, modulo whitespace).
4. Codemods delete a token together with its own leading whitespace only; never re-flow the surrounding whitespace.
5. Frontend unit tests run without a DOM environment → stub browser globals in the test file (Vue also needs `document.createElement`) instead of adding devDependencies.
6. Colours hard-coded in `<style>` blocks or inline styles read `var(--hub-…, <light literal>)`, with the variable defined only under `html.dark`, so light output stays identical.
7. Everything under `frontend/src` is scanned by Tailwind → keep class-like words (e.g. `sepia`, `text-gray-200`) out of comments and test strings.
8. The live page loads Frappe's website CSS (Bootstrap 4.6, `!important` utilities `.bg-white`, `.text-white`, `.border`, `.border-white`) before ours → every visual check must load Bootstrap 4.6.2 first, and dark overrides of those names need `html.dark .x { … !important }`.
9. Bootstrap's `.border` also forces width and style, so the fix is per utility: every Tailwind border rule gets an `!important` twin scoped to `.border` (scripts/theme-border-guard.js); selectors must match escaped variants like `hover\:`.
10. @tailwindcss/forms hard-codes `#fff` on inputs → dark override via `:where(html.dark) :is(...)` inside `@layer base`, so utilities still win.
11. frappe-ui's palette lacks some Tailwind hues (emerald, slate, indigo) → their classes generate no CSS; alias them to existing hues.
12. Text dimmed with opacity loses contrast → dark text target 5.0 (fills 5.5), and remove dimming in dark mode where it still fails.
13. A long unbroken string (URL) in a flex child spills out even with min-w-0 → user-entered text gets `[overflow-wrap:anywhere]`.
14. A visual check must look at the element's own box, not just the viewport: overflow = scrollWidth > clientWidth with overflow-x visible.
15. Changing a light-mode colour must be checked per element against the baseline (path-keyed, not HTML-keyed: removed classes change the HTML) — "fixed N" is not enough, also count "added".
16. Classes that used to generate no CSS made their text inherit a readable colour; when they start working, their text shades must be held to >= 4.5:1 too.
17. Darkening a button colour must keep the ladder to its hover shade (500 < 600 < 700 < 800).
