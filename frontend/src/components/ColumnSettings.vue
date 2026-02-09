<script setup>
import { ref, computed, watch } from 'vue';
import { Settings, Check } from 'lucide-vue-next';
import { translate } from '../utils/translation';

const props = defineProps({
	availableColumns: {
		type: Array,
		required: true,
	},
	visibleColumns: {
		type: Array,
		required: true,
	},
});

const emit = defineEmits(['update:visibleColumns']);

const showDropdown = ref(false);
const dropdownPosition = ref({ x: 0, y: 0 });

function toggleDropdown(event) {
	event.stopPropagation();
	if (showDropdown.value) {
		showDropdown.value = false;
	} else {
		const rect = event.currentTarget.getBoundingClientRect();
		dropdownPosition.value = {
			x: rect.right - 200, // Position dropdown to align right edge
			y: rect.bottom + 4,
		};
		showDropdown.value = true;
	}
}

function toggleColumn(columnId) {
	const column = props.availableColumns.find((item) => item.id === columnId);
	const newVisibleColumns = [...props.visibleColumns];
	const index = newVisibleColumns.indexOf(columnId);

	if (index > -1) {
		if (column?.required) {
			return;
		}
		// Don't allow removing the last column
		if (newVisibleColumns.length > 1) {
			newVisibleColumns.splice(index, 1);
		}
	} else {
		newVisibleColumns.push(columnId);
	}

	emit('update:visibleColumns', newVisibleColumns);
}

function isColumnVisible(columnId) {
	return props.visibleColumns.includes(columnId);
}

function closeDropdown() {
	showDropdown.value = false;
}

// Close dropdown when clicking outside
function handleClickOutside(event) {
	if (showDropdown.value && !event.target.closest('.column-settings-dropdown')) {
		closeDropdown();
	}
}

watch(showDropdown, (isOpen) => {
	if (isOpen) {
		setTimeout(() => {
			document.addEventListener('click', handleClickOutside);
		}, 0);
	} else {
		document.removeEventListener('click', handleClickOutside);
	}
});
</script>

<template>
	<div class="column-settings-dropdown relative">
		<button
			@click="toggleDropdown"
			class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
			:title="translate('Column settings')"
		>
			<Settings class="w-4 h-4" />
		</button>

		<Teleport to="body">
			<Transition name="dropdown-fade">
				<div
					v-if="showDropdown"
					class="fixed z-50 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-600 py-2 min-w-[200px]"
					:style="{
						left: dropdownPosition.x + 'px',
						top: dropdownPosition.y + 'px',
					}"
				>
					<div class="px-3 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
						{{ translate('Visible Columns') }}
					</div>

					<div class="py-1">
						<button
							v-for="column in availableColumns"
							:key="column.id"
							@click="toggleColumn(column.id)"
							:disabled="column.required && isColumnVisible(column.id)"
							:aria-disabled="column.required && isColumnVisible(column.id)"
							class="w-full flex items-center justify-between gap-3 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:bg-transparent dark:disabled:hover:bg-transparent"
						>
							<span>{{ column.label }}</span>
							<Check
								v-if="isColumnVisible(column.id)"
								class="w-4 h-4 text-blue-600 dark:text-blue-400"
							/>
						</button>
					</div>
				</div>
			</Transition>
		</Teleport>
	</div>
</template>

<style scoped>
.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
	transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
	opacity: 0;
	transform: translateY(-4px);
}
</style>
