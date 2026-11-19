/**
 * PostCSS plugin: let Tailwind's border utilities win over Bootstrap's `.border`.
 *
 * On the live page Frappe's website CSS (Bootstrap 4) loads before the app and
 * declares `.border { border: 1px solid #dee2e6 !important }`. Tailwind's own
 * `border` class has the same name, so every element using it got Bootstrap's
 * gray, solid, 1px border: border colours (border-blue-500, hover:/focus:
 * variants, transparent), border-dashed and border-2 were ignored.
 *
 * For every Tailwind rule that sets a border colour/style/width, this adds a
 * twin rule whose last compound selector also requires `.border`, with all
 * declarations !important. `.border.x` (0,2,0) beats Bootstrap's `.border`
 * (0,1,0), and applies exactly where the conflict exists. Elements with plain
 * `border` get Tailwind's default border colour back.
 */
const BORDER_PROP = /^(border(-(top|right|bottom|left))?-(color|style|width)|--tw-border-opacity)$/;
const COMBINATOR = /(\s*[>+~]\s*|\s+)(?![^[]*\])(?![^(]*\))/g;

function lastCompoundWithBorder(selector) {
	const parts = selector.split(COMBINATOR);
	const last = parts[parts.length - 1];
	if (!/^\.(?:\\.|[^.:\s\\])*border/.test(last) || /^\.border(?=[:.\s]|$)/.test(last)) return null;
	parts[parts.length - 1] = `.border${last}`;
	return parts.join("");
}

const themeBorderGuard = () => ({
	postcssPlugin: "theme-border-guard",
	OnceExit(root, { Rule }) {
		const twins = [];
		root.walkRules((rule) => {
			if (rule.parent.type === "atrule" && /keyframes/.test(rule.parent.name)) return;
			const decls = rule.nodes.filter((node) => node.type === "decl" && BORDER_PROP.test(node.prop));
			if (!decls.length) return;
			const selectors = rule.selectors.map(lastCompoundWithBorder).filter(Boolean);
			if (selectors.length !== rule.selectors.length) return;
			const twin = new Rule({ selectors });
			for (const decl of decls) twin.append(decl.clone({ important: true }));
			twins.push([rule, twin]);
		});
		if (!twins.length) return;
		// Plain `border`: Tailwind's default colour (gray-200 of the palette).
		root.append(
			new Rule({ selector: ".border.border" }).append({
				prop: "border-color",
				value: "rgb(var(--hub-line-gray-200) / var(--tw-border-opacity, 1))",
				important: true,
			})
		);
		for (const [rule, twin] of twins) {
			// Keep media queries / layers of the original rule.
			if (rule.parent.type === "atrule") {
				const wrapper = rule.parent.clone({ nodes: [] });
				wrapper.append(twin);
				root.append(wrapper);
			} else {
				root.append(twin);
			}
		}
	},
});
themeBorderGuard.postcss = true;

export default themeBorderGuard;
