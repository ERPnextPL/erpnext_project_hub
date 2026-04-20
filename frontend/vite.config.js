import vue from "@vitejs/plugin-vue";
import frappeui from "frappe-ui/vite";
import path from "path";
import fs from "fs";
import { defineConfig } from "vite";

// Resolve projekt_hub_pro frontend path (if the PRO app is installed)
const proFrontendPath = path.resolve(
	__dirname,
	"../../projekt_hub_pro/projekt_hub_pro/public/frontend/src"
);
const proAppExists = fs.existsSync(proFrontendPath);

// Virtual module plugin: provides "virtual:pro-tabs" that either
// re-exports from the real PRO app or exports a noop when PRO is absent.
function proTabsPlugin() {
	const virtualId = "virtual:pro-tabs";
	const resolvedId = "\0" + virtualId;

	return {
		name: "projekt-hub-pro-tabs",
		resolveId(id) {
			if (id === virtualId) return resolvedId;
		},
		load(id) {
			if (id === resolvedId) {
				if (proAppExists) {
					return `export { registerProTabs } from "projekt-hub-pro/tabs/proTabs";`;
				}
				return `export function registerProTabs() {}`;
			}
		},
	};
}

export default defineConfig({
	plugins: [
		frappeui({
			frappeProxy: true,
			lucideIcons: true,
			jinjaBootData: true,
			buildConfig: false,
		}),
		vue(),
		proTabsPlugin(),
	],
	server: {
		allowedHosts: true,
		...(proAppExists
			? {
					fs: {
						allow: [proFrontendPath],
					},
				}
			: {}),
	},
	resolve: {
		alias: {
			vue: "vue/dist/vue.esm-bundler.js",
			"@": path.resolve(__dirname, "src"),
			"tailwind.config.js": path.resolve(__dirname, "tailwind.config.js"),
			// Alias for PRO app - points to projekt_hub_pro frontend sources
			...(proAppExists
				? {
						"projekt-hub-pro": proFrontendPath,
						// Allow PRO app to import from base app's tabRegistry
						"@erpnext-projekt-hub": path.resolve(__dirname, "src"),
					}
				: {}),
		},
	},
	build: {
		outDir: `../erpnext_projekt_hub/public/frontend`,
		emptyOutDir: true,
		sourcemap: true,
		rollupOptions: {
			input: {
				main: path.resolve(__dirname, "index.html"),
			},
			output: {
				// Use fixed filenames without hash for easier template integration
				entryFileNames: "assets/[name].js",
				// Chunk files must be hashed to avoid name collisions/caching issues (e.g. flag.js, archive.js)
				chunkFileNames: "assets/chunks/[name]-[hash].js",
				assetFileNames: "assets/[name].[ext]",
				manualChunks: {
					"frappe-ui": ["frappe-ui"],
				},
			},
		},
	},
	optimizeDeps: {
		include: ["tailwind.config.js"],
	},
});
