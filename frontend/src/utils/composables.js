import { onMounted, onUnmounted, ref } from "vue";

export function useWindowSize() {
	const width = ref(typeof window !== "undefined" ? window.innerWidth : 0);
	const height = ref(typeof window !== "undefined" ? window.innerHeight : 0);

	function update() {
		width.value = window.innerWidth;
		height.value = window.innerHeight;
	}

	onMounted(() => {
		if (typeof window === "undefined") return;
		window.addEventListener("resize", update);
		update();
	});

	onUnmounted(() => {
		if (typeof window === "undefined") return;
		window.removeEventListener("resize", update);
	});

	return { width, height };
}

export function useDebounceFn(fn, delay = 300) {
	let timer = null;
	return (...args) => {
		if (timer) clearTimeout(timer);
		timer = setTimeout(() => fn(...args), delay);
	};
}
