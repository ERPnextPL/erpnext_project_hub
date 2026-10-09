/**
 * Runtime loader for tab plugins shipped by other apps (e.g. projekt_hub_pro).
 *
 * A plugin app builds its own IIFE bundle and registers it in its hooks.py
 * (`projekt_hub_plugins`). www/project_hub.py passes the bundles of the apps
 * installed on this site as frappe.boot.projekt_hub_plugins. When a bundle runs
 * it registers its tabs via registerTab(), reading this app's Vue, Pinia,
 * Vue Router, tab registry and shared components from window.projektHub, so
 * plugin stores, routes and components share this app's instances.
 *
 * Plugins are loaded at runtime instead of being compiled into this app because
 * Frappe Press builds each app on its own, in dependency order: this app's build
 * never sees the sources of an app that depends on it.
 */
import * as Vue from "vue";
import * as Pinia from "pinia";
import * as VueRouter from "vue-router";
import * as tabRegistry from "./tabRegistry";
import OutlinerNav from "./components/OutlinerNav.vue";
import BackToDeskButton from "./components/BackToDeskButton.vue";

function loadAsset(element) {
	return new Promise((resolve, reject) => {
		element.onload = resolve;
		element.onerror = () => reject(new Error(`Failed to load ${element.src || element.href}`));
		document.head.appendChild(element);
	});
}

function loadScript(src) {
	const script = document.createElement("script");
	script.src = src;
	return loadAsset(script);
}

function loadStylesheet(href) {
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.href = href;
	return loadAsset(link);
}

/**
 * Load the plugin bundles of this site. Never rejects: a broken plugin is
 * logged and skipped so the core tabs keep working.
 */
export async function loadPlugins() {
	const plugins = window.frappe?.boot?.projekt_hub_plugins || [];
	if (!plugins.length) return;

	window.projektHub = {
		vue: Vue,
		pinia: Pinia,
		vueRouter: VueRouter,
		tabRegistry,
		OutlinerNav,
		BackToDeskButton,
	};

	await Promise.all(
		plugins.map(async (plugin) => {
			try {
				await Promise.all([
					plugin.css && loadStylesheet(plugin.css),
					loadScript(plugin.js),
				]);
			} catch (error) {
				console.error("Projekt HUB plugin failed to load", plugin, error);
			}
		})
	);
}
