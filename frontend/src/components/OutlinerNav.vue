<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter, RouterLink } from "vue-router";
import { getNavItems, getTabByRouteName } from "../tabRegistry";

const route = useRoute();
const router = useRouter();

// Get navigation items from Tab Registry
// This allows plugins to add additional tabs dynamically
const navItems = getNavItems();

const translate = (text) => {
	return typeof window !== "undefined" && typeof window.__ === "function"
		? window.__(text)
		: text;
};

const scrollerRef = ref(null);
const itemRefs = ref({});

// Normalize Vue component refs to raw DOM elements
const normalizeEl = (el) => {
	if (!el) return null;
	return el.$el || el;
};

const handleResize = () => scrollActiveIntoView("auto");

const activeKey = computed(() => {
	const { name } = route;

	// Handle ProjectOutliner specially - it should highlight "projects"
	if (name === "ProjectOutliner") return "projects";

	// Find the tab that matches the current route name
	const tab = getTabByRouteName(name);
	if (tab) return tab.key;

	// Default to "projects" if no match found
	return "projects";
});

function setItemRef(key, el) {
	const domEl = normalizeEl(el);
	if (domEl) {
		itemRefs.value[key] = domEl;
	}
}

async function scrollActiveIntoView(behavior = "smooth") {
	await nextTick();
	const scroller = normalizeEl(scrollerRef.value);
	const activeEl = normalizeEl(itemRefs.value[activeKey.value]);
	if (!scroller || !activeEl) return;

	if (
		typeof scroller.getBoundingClientRect !== "function" ||
		typeof activeEl.getBoundingClientRect !== "function"
	) {
		return;
	}

	const scrollerRect = scroller.getBoundingClientRect();
	const elRect = activeEl.getBoundingClientRect();
	const currentScroll = scroller.scrollLeft;
	const maxScroll = scroller.scrollWidth - scroller.clientWidth;

	// Move the active icon to the center of the visible area
	const offset = elRect.left - scrollerRect.left - (scrollerRect.width / 2 - elRect.width / 2);
	const target = currentScroll + offset;
	const clamped = Math.min(Math.max(0, target), maxScroll);
	scroller.scrollTo({ left: clamped, behavior });
}

function handleNavigate(to) {
	if (route.path !== to) {
		router.push(to);
	} else {
		scrollActiveIntoView();
	}
}

onMounted(() => {
	scrollActiveIntoView("auto");
	window.addEventListener("resize", handleResize);
});

watch(activeKey, () => {
	scrollActiveIntoView();
});

onBeforeUnmount(() => {
	window.removeEventListener("resize", handleResize);
});
</script>

<template>
	<div class="flex items-center gap-3">
		<div
			ref="scrollerRef"
			class="relative w-full max-w-[200px] sm:max-w-[260px] overflow-x-auto scrollbar-hide py-1"
		>
			<div class="flex items-center gap-2 px-1">
				<RouterLink
					v-for="item in navItems"
					:key="item.key"
					:to="item.to"
					:title="translate(item.labelKey)"
					class="group relative flex-shrink-0"
					:ref="(el) => setItemRef(item.key, el)"
					@click.prevent="handleNavigate(item.to)"
				>
					<div
						:class="[
							'flex items-center justify-center w-11 h-11 rounded-2xl transition-all duration-300 ease-out shadow-sm',
							activeKey === item.key
								? `${item.bg} ${item.color} scale-100`
								: 'bg-white text-gray-500 hover:bg-gray-50 hover:scale-95',
						]"
					>
						<component :is="item.icon" class="w-5 h-5" />
					</div>
					<span
						class="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[11px] text-gray-500 hidden sm:block"
					>
						{{ translate(item.labelKey) }}
					</span>
				</RouterLink>
			</div>
		</div>
	</div>
</template>

<style scoped>
.scrollbar-hide {
	scrollbar-width: none;
	-ms-overflow-style: none;
}
.scrollbar-hide::-webkit-scrollbar {
	display: none;
}
</style>
