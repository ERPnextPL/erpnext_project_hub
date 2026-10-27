<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter, RouterLink } from "vue-router";
import { Check, ChevronDown, ChevronLeft, ChevronRight } from "lucide-vue-next";
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
const hasOverflow = ref(false);
const canScrollLeft = ref(false);
const canScrollRight = ref(false);
const mobileMenuOpen = ref(false);
const mobileMenuRef = ref(null);
const isMobile = ref(false);

// Normalize Vue component refs to raw DOM elements
const normalizeEl = (el) => {
	if (!el) return null;
	return el.$el || el;
};

const handleResize = () => {
	isMobile.value = window.innerWidth < 640;
	if (isMobile.value) {
		mobileMenuOpen.value = false;
		return;
	}
	updateScrollState();
	scrollActiveIntoView("auto");
};

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

const activeItem = computed(() => {
	return navItems.find((item) => item.key === activeKey.value) || navItems[0];
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

	// Keep the current menu position unless the active item is outside the visible area.
	const offset =
		elRect.left < scrollerRect.left
			? elRect.left - scrollerRect.left
			: elRect.right > scrollerRect.right
				? elRect.right - scrollerRect.right
				: 0;
	const target = currentScroll + offset;
	const clamped = Math.min(Math.max(0, target), maxScroll);
	scroller.scrollTo({ left: clamped, behavior });
	if (behavior === "auto") {
		updateScrollState();
	}
}

function handleNavigate(to) {
	if (route.path !== to) {
		router.push(to);
	} else {
		scrollActiveIntoView();
	}
}

function handleMobileNavigate(to) {
	mobileMenuOpen.value = false;
	if (route.path !== to) router.push(to);
}

function toggleMobileMenu() {
	mobileMenuOpen.value = !mobileMenuOpen.value;
}

function closeMobileMenu(event) {
	if (mobileMenuOpen.value && !mobileMenuRef.value?.contains(event.target)) {
		mobileMenuOpen.value = false;
	}
}

function handleKeydown(event) {
	if (event.key === "Escape") mobileMenuOpen.value = false;
}

function updateScrollState() {
	const scroller = normalizeEl(scrollerRef.value);
	if (!scroller) return;

	const maxScroll = Math.max(0, scroller.scrollWidth - scroller.clientWidth);
	const currentScroll = scroller.scrollLeft;
	const threshold = 1;

	hasOverflow.value = maxScroll > threshold;
	canScrollLeft.value = currentScroll > threshold;
	canScrollRight.value = currentScroll < maxScroll - threshold;
}

function scrollNav(direction) {
	const scroller = normalizeEl(scrollerRef.value);
	if (!scroller) return;

	scroller.scrollBy({
		left: direction === "left" ? -scroller.clientWidth * 0.8 : scroller.clientWidth * 0.8,
		behavior: "smooth",
	});
}

onMounted(() => {
	isMobile.value = window.innerWidth < 640;
	nextTick(() => {
		if (!isMobile.value) {
			updateScrollState();
			scrollActiveIntoView("auto");
		}
	});
	window.addEventListener("resize", handleResize);
	document.addEventListener("pointerdown", closeMobileMenu);
	document.addEventListener("keydown", handleKeydown);
});

watch(activeKey, () => {
	if (!isMobile.value) scrollActiveIntoView();
});

onBeforeUnmount(() => {
	window.removeEventListener("resize", handleResize);
	document.removeEventListener("pointerdown", closeMobileMenu);
	document.removeEventListener("keydown", handleKeydown);
});
</script>

<template>
	<div v-if="isMobile" ref="mobileMenuRef" class="relative min-w-0">
		<button
			type="button"
			class="flex h-10 max-w-[min(70vw,240px)] items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 text-sm font-medium text-gray-700 shadow-sm transition hover:bg-gray-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200 dark:hover:bg-gray-800"
			:aria-label="translate('Open navigation')"
			:aria-expanded="mobileMenuOpen"
			@click.stop="toggleMobileMenu"
		>
			<component :is="activeItem?.icon" class="h-4 w-4 flex-shrink-0" :class="activeItem?.color" />
			<span class="truncate">{{ translate(activeItem?.labelKey || "Navigation") }}</span>
			<ChevronDown
				class="ml-auto h-4 w-4 flex-shrink-0 text-gray-400 transition-transform"
				:class="mobileMenuOpen ? 'rotate-180' : ''"
			/>
		</button>

		<div
			v-if="mobileMenuOpen"
			class="absolute right-0 top-full z-50 mt-2 w-56 max-w-[calc(100vw-24px)] overflow-hidden rounded-2xl border border-gray-200 bg-white p-1.5 shadow-xl dark:border-gray-700 dark:bg-gray-900"
		>
			<RouterLink
				v-for="item in navItems"
				:key="item.key"
				:to="item.to"
				:aria-current="activeKey === item.key ? 'page' : undefined"
				class="flex min-h-11 items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500"
				:class="
					activeKey === item.key
						? `${item.bg} ${item.color}`
						: 'text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
				"
				@click.prevent="handleMobileNavigate(item.to)"
			>
				<component :is="item.icon" class="h-4 w-4 flex-shrink-0" />
				<span class="flex-1">{{ translate(item.labelKey) }}</span>
				<Check v-if="activeKey === item.key" class="h-4 w-4" />
			</RouterLink>
		</div>
	</div>

	<nav
		v-else
		class="flex w-fit min-w-0 max-w-full items-center gap-1 rounded-2xl border border-gray-200/80 bg-white/90 p-1 shadow-sm backdrop-blur dark:border-gray-700 dark:bg-gray-900/90"
		:aria-label="translate('Main navigation')"
	>
		<button
			v-if="hasOverflow"
			type="button"
			:title="translate('Scroll left')"
			:aria-label="translate('Scroll left')"
			:disabled="!canScrollLeft"
			class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl text-gray-500 transition hover:bg-gray-100 hover:text-gray-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:pointer-events-none disabled:opacity-30 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100"
			@click="scrollNav('left')"
		>
			<ChevronLeft class="h-4 w-4" />
		</button>
		<div
			ref="scrollerRef"
			class="min-w-0 max-w-full flex-[0_1_auto] overflow-x-auto scrollbar-hide"
			@scroll="updateScrollState"
		>
			<div class="flex min-w-max items-center gap-0.5">
				<RouterLink
					v-for="item in navItems"
					:key="item.key"
					:to="item.to"
					:title="translate(item.labelKey)"
					:aria-label="translate(item.labelKey)"
					:aria-current="activeKey === item.key ? 'page' : undefined"
					class="group flex h-9 flex-shrink-0 items-center gap-2 rounded-xl px-2.5 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
					:class="
						activeKey === item.key
							? `${item.bg} ${item.color} shadow-sm dark:bg-opacity-20`
							: 'text-gray-500 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100'
					"
					:ref="(el) => setItemRef(item.key, el)"
					@click.prevent="handleNavigate(item.to)"
				>
					<component :is="item.icon" class="h-4 w-4 flex-shrink-0" />
					<span>{{ translate(item.labelKey) }}</span>
				</RouterLink>
			</div>
		</div>
		<button
			v-if="hasOverflow"
			type="button"
			:title="translate('Scroll right')"
			:aria-label="translate('Scroll right')"
			:disabled="!canScrollRight"
			class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl text-gray-500 transition hover:bg-gray-100 hover:text-gray-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:pointer-events-none disabled:opacity-30 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100"
			@click="scrollNav('right')"
		>
			<ChevronRight class="h-4 w-4" />
		</button>
	</nav>
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
