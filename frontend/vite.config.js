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
 * Determine whether projekt_hub_pro should be included in the build.
 *
 * Rule: projekt_hub_pro must be both present on disk AND installed in the DB.
 * Uses detect-pro.py to query tabInstalled Application directly.
 * If the DB is unreachable (offline build), falls back to False so that
 * PRO tabs are never shown when installation cannot be confirmed.
 */
function detectProApp() {
	if (!fs.existsSync(proFrontendPath)) return false;
	try {
		const scriptPath = path.resolve(__dirname, "scripts", "detect-pro.py");
		// Prefer the bench virtualenv Python (has pymysql/psycopg2).
		// Fall back to system python3 if the venv isn't present.
		const benchPython = path.resolve(__dirname, "../../../env/bin/python3");
		const pythonExe = fs.existsSync(benchPython) ? benchPython : "python3";
		const result = execFileSync(pythonExe, [scriptPath], {
			encoding: "utf-8",
			cwd: path.resolve(__dirname, ".."),
		}).trim();
		return result === "True";
	} catch {
		return false;
	}
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
						// Resolve shared packages from base app's node_modules so that
						// PRO app source files (which have no own node_modules) can import
						// the same packages without Rollup failing to find them.
						"lucide-vue-next": path.resolve(__dirname, "node_modules/lucide-vue-next"),
						pinia: path.resolve(__dirname, "node_modules/pinia"),
						"vue-router": path.resolve(__dirname, "node_modules/vue-router"),
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
