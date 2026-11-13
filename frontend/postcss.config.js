import tailwindcss from "tailwindcss";
import autoprefixer from "autoprefixer";
import tailwindNesting from "tailwindcss/nesting/index.js";
import postcssNested from "postcss-nested";
import themeBorderGuard from "./scripts/theme-border-guard.js";

export default {
	plugins: [
		tailwindNesting(postcssNested),
		tailwindcss,
		themeBorderGuard,
		autoprefixer,
	],
};
