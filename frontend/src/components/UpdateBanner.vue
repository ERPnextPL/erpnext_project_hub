<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { RefreshCw, X } from "lucide-vue-next";
import { translate } from "../utils/translation";

const updateAvailable = ref(false);
let waitingSW = null;

function handleSWMessage(event) {
	if (event.data?.type === "SW_UPDATED") {
		updateAvailable.value = true;
	}
}

function handleSWUpdate(registration) {
	if (registration.waiting) {
		waitingSW = registration.waiting;
		updateAvailable.value = true;
	}
}

function applyUpdate() {
	if (waitingSW) {
		waitingSW.postMessage({ type: "SKIP_WAITING" });
	} else if (navigator.serviceWorker?.controller) {
		navigator.serviceWorker.controller.postMessage({ type: "SKIP_WAITING" });
	}
	// Reload after the new SW takes control
	navigator.serviceWorker.addEventListener("controllerchange", () => {
		window.location.reload();
	});
	// Safety fallback – reload after 1.5 s if controllerchange doesn't fire
	setTimeout(() => window.location.reload(), 1500);
}

function dismiss() {
	updateAvailable.value = false;
}

onMounted(() => {
	if (!("serviceWorker" in navigator)) return;

	navigator.serviceWorker.addEventListener("message", handleSWMessage);

	// Check if there's already a waiting SW when the component mounts
	navigator.serviceWorker.getRegistration().then((reg) => {
		if (reg?.waiting) {
			waitingSW = reg.waiting;
			updateAvailable.value = true;
		}

		// Watch for a new SW entering the waiting state
		if (reg) {
			reg.addEventListener("updatefound", () => {
				const newSW = reg.installing;
				if (!newSW) return;
				newSW.addEventListener("statechange", () => {
					if (newSW.state === "installed" && navigator.serviceWorker.controller) {
						waitingSW = newSW;
						updateAvailable.value = true;
					}
				});
			});
		}
	});
});

onUnmounted(() => {
	navigator.serviceWorker?.removeEventListener("message", handleSWMessage);
});
</script>

<template>
	<Transition name="update-banner">
		<div
			v-if="updateAvailable"
			class="bg-purple-600 text-white px-4 py-2 flex items-center justify-between gap-3 text-sm"
		>
			<div class="flex items-center gap-2">
				<RefreshCw class="w-4 h-4 shrink-0" />
				<span class="font-medium">{{ translate("New version available") }}</span>
				<span class="hidden sm:inline text-purple-200">
					&mdash; {{ translate("click to update") }}
				</span>
			</div>

			<div class="flex items-center gap-2 shrink-0">
				<button
					class="px-3 py-1 bg-white text-purple-700 rounded-md font-semibold text-xs hover:bg-purple-50 transition-colors"
					@click="applyUpdate"
				>
					{{ translate("Update now") }}
				</button>
				<button
					class="text-purple-200 hover:text-white transition-colors"
					:title="translate('Dismiss')"
					@click="dismiss"
				>
					<X class="w-4 h-4" />
				</button>
			</div>
		</div>
	</Transition>
</template>

<style scoped>
.update-banner-enter-active,
.update-banner-leave-active {
	transition: all 0.3s ease;
}
.update-banner-enter-from,
.update-banner-leave-to {
	transform: translateY(-100%);
	opacity: 0;
}
</style>
