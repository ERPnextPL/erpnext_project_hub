<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter, RouterLink } from "vue-router";
import { getNavItems, getTabByRouteName } from "../tabRegistry";

const route = useRoute();
const router = useRouter();

// Get navigation items from Tab Registry
// This allows plugins to add additional tabs dynamically
const isManager = (window.frappe?.user_roles || window.frappe?.boot?.user?.roles || []).some(
	(r) => ["Projects Manager", "Project Manager", "System Manager", "Administrator"].includes(r)
);

const navItems = getNavItems().filter((item) => !item.managerOnly || isManager);

const translate = (text) => {
	return typeof window !== "undefined" && typeof window.__ === "function"
		? window.__(text)
		: text;
};

const scrollerRef = ref(null);
const itemRefs = ref({});
const touchStartX = ref(null);
const touchStartScrollLeft = ref(0);

// Normalize Vue component refs to raw DOM elements
const normalizeEl = (el) => {
	if (!el) return null;
	return el.$el || el;
};

const handleResize = () => scrollActiveIntoView("auto");

// 🎯 KROK 1: Obsługa wheel scrolla (scroll myszką)
// Kiedy użytkownik scrolluje myszką - zamiast scrollować w pionie,
// scrollujemy w poziomie przez menu
function handleWheel(event) {
	const scroller = normalizeEl(scrollerRef.value);
	if (!scroller) return;

	// Jeśli jest scroll, zapobiegamy domyślnemu zachowaniu
	if (scroller.scrollWidth > scroller.clientWidth) {
		event.preventDefault();
		// event.deltaY to ilość scrollu (dodatnia = dół, ujemna = góra)
		// Zamieniamy to na horizontal scroll
		scroller.scrollLeft += event.deltaY;
	}
}

// 🎯 KROK 2: Obsługa touch/swipe (dla telefonów)
// Kiedy użytkownik dotknie ekranu - zapisujemy pozycję początkową
function handleTouchStart(event) {
	touchStartX.value = event.touches[0]?.clientX ?? null;
	const scroller = normalizeEl(scrollerRef.value);
	if (scroller) {
		touchStartScrollLeft.value = scroller.scrollLeft;
	}
}

// Kiedy użytkownik przesuwa palec - obliczamy różnicę i scrollujemy
function handleTouchMove(event) {
	if (touchStartX.value === null) return; // Nie zaczęliśmy od dotknięcia

	const scroller = normalizeEl(scrollerRef.value);
	if (!scroller) return;

	// Obliczamy o ile się przesunął palec
	const deltaX = event.touches[0].clientX - touchStartX.value;

	// Jeśli przesunął się w lewo (deltaX ujemny), scrollujemy w prawo (dodajemy)
	// Jeśli przesunął się w prawo (deltaX dodatni), scrollujemy w lewo (odejmujemy)
	scroller.scrollLeft = touchStartScrollLeft.value - deltaX;
}

function handleTouchEnd() {
	touchStartX.value = null;
}

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

	// 🎯 KROK 3: Podłączamy nasze handlery do elementu
	const scroller = normalizeEl(scrollerRef.value);
	if (scroller) {
		// Wheel scroll - scroll myszką
		scroller.addEventListener("wheel", handleWheel, { passive: false });
		// Touch start - palec dotyka ekranu
		scroller.addEventListener("touchstart", handleTouchStart, { passive: true });
		// Touch move - palec się przesuwa
		scroller.addEventListener("touchmove", handleTouchMove, { passive: true });
		scroller.addEventListener("touchend", handleTouchEnd, { passive: true });
		scroller.addEventListener("touchcancel", handleTouchEnd, { passive: true });
	}
});

watch(activeKey, () => {
	scrollActiveIntoView();
});

onBeforeUnmount(() => {
	window.removeEventListener("resize", handleResize);

	// 🎯 KROK 4: Usuwamy event listenery by nie zajmowały pamięci
	const scroller = normalizeEl(scrollerRef.value);
	if (scroller) {
		scroller.removeEventListener("wheel", handleWheel);
		scroller.removeEventListener("touchstart", handleTouchStart);
		scroller.removeEventListener("touchmove", handleTouchMove);
		scroller.removeEventListener("touchend", handleTouchEnd);
		scroller.removeEventListener("touchcancel", handleTouchEnd);
	}
});
</script>

<template>
	<div class="flex items-center gap-3">
		<!-- 🎯 KROK 5: Gradient fade wrapper - tworzy efekt gradientu na krawędziach -->
		<div class="relative w-full max-w-[200px] sm:max-w-[260px]">
			<!-- Gradient fade na lewej stronie -->
			<div
				class="absolute left-0 top-0 bottom-0 w-4 bg-gradient-to-r from-gray-50 to-transparent pointer-events-none z-10"
			></div>

			<!-- Gradient fade na prawej stronie -->
			<div
				class="absolute right-0 top-0 bottom-0 w-4 bg-gradient-to-l from-gray-50 to-transparent pointer-events-none z-10"
			></div>

			<!-- Główny scroller -->
			<div
				ref="scrollerRef"
				class="overflow-x-auto scrollbar-hide py-1"
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
