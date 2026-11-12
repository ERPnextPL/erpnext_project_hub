import { onBeforeUnmount, ref } from "vue";

/**
 * Scrolls a board card (any element carrying data-task="<name>") into view and
 * flashes it - used when a task is picked in the "Needs attention" panel.
 */
export function useBoardTaskFocus(duration = 2500) {
	const highlightedTaskName = ref(null);
	let timer = null;
	let flashed = null;
	const FLASH = ["ring-2", "ring-amber-400", "ring-offset-1"];

	function clear() {
		clearTimeout(timer);
		flashed?.classList.remove(...FLASH);
		flashed = null;
		highlightedTaskName.value = null;
	}

	function focusBoardTask(taskName) {
		clear();
		highlightedTaskName.value = taskName;
		const card = document.querySelector(`[data-task="${CSS.escape(taskName)}"]`);
		if (card) {
			card.scrollIntoView({ behavior: "smooth", block: "center", inline: "center" });
			card.classList.add(...FLASH);
			flashed = card;
		}
		timer = setTimeout(clear, duration);
	}

	onBeforeUnmount(clear);

	return { highlightedTaskName, focusBoardTask };
}
