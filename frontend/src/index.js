import { createApp } from "vue";
import { createPinia } from "pinia";
import { FrappeUI, setConfig, frappeRequest } from "frappe-ui";
import App from "./App.vue";
import { createAppRouter } from "./router";
import { registerCoreTabs } from "./tabs/coreTabs";
import { loadPlugins } from "./plugins";
import "./index.css";
import { formatTranslation } from "./utils/translation";

// Provide a minimal window.__ stub during server-side initialization so imports
// that reference `window.__` don't crash before the client hydrates.
const rootContext = typeof globalThis !== "undefined" ? globalThis : {};
const stubTranslate = (text, replacements) => formatTranslation(text, replacements);

if (!rootContext.window) {
	rootContext.window = {
		__(text, replacements) {
			return stubTranslate(text, replacements);
		},
	};
} else if (typeof rootContext.window.__ !== "function") {
	rootContext.window.__ = (text, replacements) => stubTranslate(text, replacements);
}

// Configure frappe-ui
setConfig("resourceFetcher", frappeRequest);

// Core tabs go first so plugins can override them (unregisterTab); the router is
// built once plugins have registered their tabs too.
registerCoreTabs();

loadPlugins().then(() => {
	const app = createApp(App);
	const pinia = createPinia();

	app.use(pinia);
	app.use(createAppRouter());
	app.use(FrappeUI);

	app.mount("#app");
});
