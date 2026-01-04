<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useTaskStore } from "../stores/taskStore";
import { User, X, ChevronDown, Check } from "lucide-vue-next";

const props = defineProps({
	modelValue: {
		type: Array,
		default: () => [],
	},
	placeholder: {
		type: String,
		default: "Assign user...",
	},
	multiple: {
		type: Boolean,
		default: true,
	},
});

const emit = defineEmits(["update:modelValue", "add", "remove"]);

const store = useTaskStore();
const isOpen = ref(false);
const searchQuery = ref("");

onMounted(() => {
	if (store.availableUsers.length === 0) {
		store.fetchUsers();
	}
	document.addEventListener("click", closeDropdown);
});

const filteredUsers = computed(() => {
	const query = searchQuery.value.toLowerCase();
	return store.availableUsers.filter(
		(user) =>
			user.full_name?.toLowerCase().includes(query) ||
			user.name?.toLowerCase().includes(query)
	);
});

const selectedUsers = computed(() => {
	if (!props.modelValue) return [];
	try {
		const assigns =
			typeof props.modelValue === "string" ? JSON.parse(props.modelValue) : props.modelValue;
		return store.availableUsers.filter((u) => assigns.includes(u.name));
	} catch {
		return [];
	}
});

function isSelected(user) {
	if (!props.modelValue) return false;
	try {
		const assigns =
			typeof props.modelValue === "string" ? JSON.parse(props.modelValue) : props.modelValue;
		return assigns.includes(user.name);
	} catch {
		return false;
	}
}

function toggleUser(user) {
	if (isSelected(user)) {
		emit("remove", user.name);
	} else {
		emit("add", user.name);
	}
	if (!props.multiple) {
		isOpen.value = false;
	}
}

function closeDropdown(e) {
	if (!e.target.closest(".user-select-container")) {
		isOpen.value = false;
	}
}
</script>

<template>
	<div class="user-select-container relative">
		<!-- Selected users display -->
		<div
			@click="isOpen = !isOpen"
			class="flex items-center gap-2 min-h-[36px] px-2 py-1 border border-gray-300 rounded-md cursor-pointer hover:border-gray-400 bg-white"
		>
			<div v-if="selectedUsers.length > 0" class="flex flex-wrap gap-1 flex-1">
				<span
					v-for="user in selectedUsers"
					:key="user.name"
					class="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-xs"
				>
					<img
						v-if="user.user_image"
						:src="user.user_image"
						class="w-4 h-4 rounded-full"
					/>
					<User v-else class="w-3 h-3" />
					<span class="truncate max-w-[100px]">{{ user.full_name || user.name }}</span>
					<button @click.stop="emit('remove', user.name)" class="hover:text-blue-600">
						<X class="w-3 h-3" />
					</button>
				</span>
			</div>
			<span v-else class="text-gray-400 text-sm flex-1">{{ placeholder }}</span>
			<ChevronDown class="w-4 h-4 text-gray-400 flex-shrink-0" />
		</div>

		<!-- Dropdown -->
		<div
			v-if="isOpen"
			class="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-auto"
		>
			<!-- Search -->
			<div class="p-2 border-b border-gray-100">
				<input
					v-model="searchQuery"
					type="text"
					placeholder="Search users..."
					class="w-full px-2 py-1 text-sm border border-gray-200 rounded focus:outline-none focus:border-blue-400"
					@click.stop
				/>
			</div>

			<!-- User list -->
			<div class="py-1">
				<button
					v-for="user in filteredUsers"
					:key="user.name"
					@click.stop="toggleUser(user)"
					class="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
				>
					<img
						v-if="user.user_image"
						:src="user.user_image"
						class="w-6 h-6 rounded-full"
					/>
					<div
						v-else
						class="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center"
					>
						<User class="w-4 h-4 text-gray-500" />
					</div>
					<span class="flex-1 truncate">{{ user.full_name || user.name }}</span>
					<Check v-if="isSelected(user)" class="w-4 h-4 text-blue-600" />
				</button>
				<div v-if="filteredUsers.length === 0" class="px-3 py-2 text-sm text-gray-500">
					No users found
				</div>
			</div>
		</div>
	</div>
</template>
