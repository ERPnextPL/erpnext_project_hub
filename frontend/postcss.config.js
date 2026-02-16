import tailwindcss from "tailwindcss";
import autoprefixer from "autoprefixer";
import tailwindNesting from "tailwindcss/nesting/index.js";
import postcssNested from "postcss-nested";

export default {
	plugins: [
		tailwindNesting(postcssNested),
		tailwindcss,
		autoprefixer,
	],
};
