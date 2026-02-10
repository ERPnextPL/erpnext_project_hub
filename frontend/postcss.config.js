import tailwindcss from "tailwindcss";
import autoprefixer from "autoprefixer";
import tailwindNesting from "tailwindcss/nesting";
import postcssNested from "postcss-nested";

export default {
	plugins: [
		tailwindNesting(postcssNested),
		tailwindcss,
		autoprefixer,
	],
};
