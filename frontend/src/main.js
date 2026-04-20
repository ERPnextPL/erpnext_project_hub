import { createApp } from "vue";
import { createPinia } from "pinia";
import { FrappeUI, setConfig, frappeRequest } from "frappe-ui";
import App from "./App.vue";
import router from "./router";
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

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);
app.use(FrappeUI);

app.mount("#app");
