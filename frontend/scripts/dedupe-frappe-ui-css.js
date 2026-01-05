import fs from "fs";
import path from "path";
import postcss from "postcss";
import cssnano from "cssnano";
import { fileURLToPath } from "url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const cssPath = path.resolve(
	scriptDir,
	"../..",
	"erpnext_projekt_hub",
	"public/frontend/assets/frappe-ui.css"
);

if (!fs.existsSync(cssPath)) {
	console.warn(
		`[dedupe-frappe-ui-css] ${cssPath} not found. Run the build first to generate the asset.`
	);
	process.exit(0);
}

const cssContent = fs.readFileSync(cssPath, "utf8");
const root = postcss.parse(cssContent);

root.walkRules((rule) => {
	const decls = [];
	rule.walkDecls((decl) => {
		decls.push(decl);
	});
	const seenProps = new Set();
	for (let i = decls.length - 1; i >= 0; i -= 1) {
		const decl = decls[i];
		if (seenProps.has(decl.prop)) {
			decl.remove();
		} else {
			seenProps.add(decl.prop);
		}
	}

	if (rule.selector?.includes(".vgl-item__resizer:before")) {
		const widthProps = new Set(["border-bottom-width", "border-right-width"]);
		rule.walkDecls((decl) => {
			if (widthProps.has(decl.prop)) {
				decl.remove();
			}
		});
		const widthValue = "var(--vgl-resizer-border-width)";
		rule.append({ prop: "border-bottom-width", value: widthValue });
		rule.append({ prop: "border-right-width", value: widthValue });
	}
});

const signatureSet = new Set();
const filteredRoot = postcss.root();

for (const node of root.nodes) {
	const signature = node.toString();
	if (signatureSet.has(signature)) {
		continue;
	}
	signatureSet.add(signature);
	filteredRoot.append(node);
}

const minifyCss = async () => {
	const result = await postcss([cssnano({ preset: "default" })]).process(
		filteredRoot.toString(),
		{
			from: cssPath,
			to: cssPath,
		}
	);
	fs.writeFileSync(cssPath, result.css);
	console.log("[dedupe-frappe-ui-css] Cleaned CSS written to", cssPath);
};

minifyCss().catch((error) => {
	console.error("[dedupe-frappe-ui-css] Failed to clean CSS:", error);
	process.exit(1);
});
