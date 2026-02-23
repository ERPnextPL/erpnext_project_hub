import vue from "@vitejs/plugin-vue";
import frappeui from "frappe-ui/vite";
import path from "path";
import fs from "fs";
import { execFileSync } from "child_process";
import { defineConfig } from "vite";

// Resolve projekt_hub_pro frontend path
const proFrontendPath = path.resolve(
	__dirname,
	"../../projekt_hub_pro/projekt_hub_pro/public/frontend/src"
);

/**
 * Determine whether projekt_hub_pro is installed.
 *
 * Primary:  run scripts/detect-pro.py which queries the Frappe database.
 *           Works on both self-hosted and Frappe Cloud / Press — no persistent
 *           file needed, the source of truth is always the database.
 *
 * Fallback: check for frontend/.pro-enabled marker file.
 *           Used in CI environments or when the DB is not reachable during build.
 */
function detectProApp() {
	if (!fs.existsSync(proFrontendPath)) return false;

	try {
		const script = path.resolve(__dirname, "scripts/detect-pro.py");
		// Use bench virtualenv Python so frappe and its dependencies are available.
		// Fall back to python3 if the venv doesn't exist (e.g. fresh CI checkout).
		const benchRoot = path.resolve(__dirname, "../../..");
		const venvPython = path.join(benchRoot, "env", "bin", "python");
		const pythonCmd = fs.existsSync(venvPython) ? venvPython : "python3";
		const result = execFileSync(pythonCmd, [script], {
			encoding: "utf-8",
			timeout: 15000,
		});
		if (result.trim() === "True") return true;
		if (result.trim() === "False") return false;
	} catch (_) {
		// DB unreachable or python not found — fall through to marker file
	}

	// Fallback: marker file created by projekt_hub_pro after_install hook
	return fs.existsSync(path.resolve(__dirname, ".pro-enabled"));
}

const proAppExists = detectProApp();

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
