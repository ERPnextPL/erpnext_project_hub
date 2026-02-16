<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { WifiOff } from "lucide-vue-next";
import { translate } from "../utils/translation";

const isOffline = ref(!navigator.onLine);

function handleOnline() {
	isOffline.value = false;
}

function handleOffline() {
	isOffline.value = true;
}

onMounted(() => {
	window.addEventListener("online", handleOnline);
	window.addEventListener("offline", handleOffline);
});

onUnmounted(() => {
	window.removeEventListener("online", handleOnline);
	window.removeEventListener("offline", handleOffline);
});
</script>

<template>
	<Transition name="offline-banner">
		<div
			v-if="isOffline"
			class="bg-amber-500 text-white px-3 py-1.5 text-center text-xs sm:text-sm font-medium flex items-center justify-center gap-2"
		>
			<WifiOff class="w-4 h-4 flex-shrink-0" />
			<span>{{ translate("Offline mode") }} &mdash; {{ translate("viewing cached data") }}</span>
		</div>
	</Transition>
</template>

<style scoped>
.offline-banner-enter-active,
.offline-banner-leave-active {
	transition: all 0.3s ease;
}
.offline-banner-enter-from,
.offline-banner-leave-to {
	transform: translateY(-100%);
	opacity: 0;
}
</style>
