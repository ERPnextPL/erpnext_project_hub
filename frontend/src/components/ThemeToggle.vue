<script setup>
import { onMounted } from "vue";
import { Moon, Sun } from "lucide-vue-next";
import { useDarkMode } from "../composables/useDarkMode";

const { isDark, toggleTheme, initTheme } = useDarkMode();

onMounted(initTheme);

const translate = (text) =>
	typeof window !== "undefined" && typeof window.__ === "function" ? window.__(text) : text;
</script>

<template>
	<!-- Floats above the "Desk" button (BackToDeskButton) on every page. -->
	<button
		type="button"
		data-theme-toggle
		class="fixed bottom-16 left-4 z-30 flex h-9 w-9 items-center justify-center rounded-full border border-gray-300 bg-white text-gray-600 shadow-lg transition-all hover:text-gray-900 hover:shadow-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
		:title="isDark ? translate('Switch to light mode') : translate('Switch to dark mode')"
		:aria-label="isDark ? translate('Switch to light mode') : translate('Switch to dark mode')"
		@click="toggleTheme"
	>
		<Sun v-if="isDark" class="h-4 w-4" aria-hidden="true" />
		<Moon v-else class="h-4 w-4" aria-hidden="true" />
	</button>
</template>
