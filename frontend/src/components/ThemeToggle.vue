<script setup>
import { onMounted } from 'vue';
import { useDarkMode } from '../composables/useDarkMode';
import { Sun, Moon } from 'lucide-vue-next';

const { isDark, toggleTheme, initTheme, listenToSystemTheme } = useDarkMode();

onMounted(() => {
	initTheme();
	const cleanup = listenToSystemTheme();

	// Cleanup on unmount
	return cleanup;
});

const realWindow = typeof globalThis !== 'undefined' ? globalThis.window : undefined;
const translate = (text) => {
	return typeof realWindow !== 'undefined' && typeof realWindow.__ === 'function'
		? realWindow.__(text)
		: text;
};
</script>

<template>
	<button
		@click="toggleTheme"
		:class="[
			'relative inline-flex items-center justify-center',
			'w-9 h-9 rounded-lg',
			'bg-gray-100 dark:bg-gray-800',
			'hover:bg-gray-200 dark:hover:bg-gray-700',
			'transition-all duration-200',
			'group'
		]"
		:title="isDark ? translate('Switch to light mode') : translate('Switch to dark mode')"
		:aria-label="isDark ? translate('Switch to light mode') : translate('Switch to dark mode')"
	>
		<!-- Sun icon (light mode) -->
		<Transition name="icon-fade">
			<Sun
				v-if="!isDark"
				class="w-5 h-5 text-amber-500 group-hover:text-amber-600 transition-colors"
			/>
		</Transition>

		<!-- Moon icon (dark mode) -->
		<Transition name="icon-fade">
			<Moon
				v-if="isDark"
				class="w-5 h-5 text-blue-400 group-hover:text-blue-300 transition-colors"
			/>
		</Transition>
	</button>
</template>

<style scoped>
.icon-fade-enter-active,
.icon-fade-leave-active {
	transition: all 0.2s ease;
	position: absolute;
}

.icon-fade-enter-from {
	opacity: 0;
	transform: rotate(-90deg) scale(0.5);
}

.icon-fade-leave-to {
	opacity: 0;
	transform: rotate(90deg) scale(0.5);
}
</style>
