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
18. A modal that sets "saving" before emitting must give the parent a way to undo it on failure (here: a callback as the event's second argument), or a failed request leaves the form stuck.
19. frappe-ui's light gray-600 (#7C7C7C) is 4.2:1 on white → new secondary text uses gray-700, icons gray-600 (3:1).
20. A list whose API defaults to "open only" must not feed a count for a status it never returns: load that status separately (with its total) or hide the count.
21. Test data for "latest N" lists must pick items that stay inside the window after the test's own changes.
22. Iterators (Map.values()) have no .flat()/.map() in browsers → spread into an array first; test boards with parent/child tasks, a flat test set hides code paths like this.
23. Never set a global min-width on buttons: in a flex row it replaces min-width:auto and lets text buttons shrink below their text. Global touch rules set min-height only; icon-only buttons opt in to 24x24 with `hub-tap`.
24. Mobile checks must open every view by its mobile controls: a control pushed off-screen (M4) also hides whole views from the audit (projectListRows).
25. Touch-only CSS goes under `@media (pointer: coarse)` so desktop output stays identical (verified by a desktop before/after compare).
26. Touch screens have no hover: controls revealed with `group-hover:opacity-100` must be visible under `pointer: coarse`, and revealing them can expose new too-small targets — re-measure after.
27. Side panels next to a board (`KanbanAttentionPanel`) are `hidden md:flex`; on a phone they cover the board.
28. A mobile-only change must not add wrapper elements on desktop: put the condition on each element (v-if) so desktop DOM and the path-keyed desktop compare stay identical.
29. Records loaded on demand belong in the shared store (a separate collection if they must not widen other views), and every write updates them — a board-local cache drifts from what was saved.
30. Mocked fetch in unit tests must serialise responses (JSON round trip): shared object references make a missing update look like it worked. Prove a regression test by re-introducing the bug and watching it fail.
31. Frappe checks a workflow's "allow edit" roles only in the browser and lets anyone with Submit permission submit around it → lock edits and allow submit/cancel only through the workflow in server hooks (timesheet_approval.validate / before_submit / before_cancel), and test them against plain `doc.save()` / `doc.submit()`.
32. `apply_workflow` reloads the document from the database before the transition → a value the transition needs (rejection reason) must be stored first, in the same request, after checking the user may take that transition.
33. `before_workflow_action` runs after Frappe froze the page → unfreeze before opening a dialog, and return a never-resolving promise to stop the standard transition when the dialog applies it itself.
34. ERPNext v16 `Timesheet.validate` requires whoever saves it to have "select" on every task and project in its rows → approver roles need read/select on Task and Project, or approving fails with "Not permitted".
35. `frappe.sendmail` throws without an outgoing e-mail account and its message stays on screen → check `EmailAccount.find_outgoing` first, keep the desk notification independent of the e-mail, and restore the message log after a swallowed failure.
36. A workflow transition's `condition` is evaluated as whoever triggers the change, also when Frappe builds the next approvers' Workflow Actions → per-user conditions (author only) go only on transitions into optional states, never on the ones that fill the approvers' inbox.
37. Frappe's `allow_self_approval` compares the user with the document's creator only → for "not your own hours" also compare with the employee's user on the server, and put the full-rights (System Manager) transition rows last: Frappe applies the last row matching the user's roles.
38. The live page's `.hidden` is `display: none !important` (Bootstrap), so `hidden md:block` never shows → hide with the opposite variant (`max-md:hidden`).
