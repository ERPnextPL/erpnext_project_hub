<template>
	<a
		href="/app"
		class="fixed bottom-4 left-4 z-30 flex items-center gap-1.5 px-3 py-2
		       bg-white border border-gray-300 rounded-full shadow-lg
		       text-sm text-gray-600 hover:text-gray-900 hover:shadow-xl
		       transition-all"
		:title="translate('Back to Desk')"
	>
		<ArrowLeft class="w-4 h-4" />
		<span class="hidden sm:inline">{{ translate("Desk") }}</span>
	</a>
</template>

<script setup>
import { ArrowLeft } from "lucide-vue-next";

// Inline translate to avoid cross-app import path issues (this component is shared between apps)
const translate = (text) =>
	typeof window !== "undefined" && typeof window.__ === "function" ? window.__(text) : text;
</script>
