<script setup>
import { computed } from "vue";
import { User } from "lucide-vue-next";
import UserAvatar from "./UserAvatar.vue";
import { resolveAssignees } from "../../utils/taskAssignees";
import { translate } from "../../utils/translation";

// Overlapping avatars of the users assigned to a task (`_assign`).
const props = defineProps({
	assign: {
		type: [String, Array],
		default: null,
	},
	users: {
		type: Array,
		default: () => [],
	},
	max: {
		type: Number,
		default: 3,
	},
	size: {
		type: String,
		default: "sm",
	},
	showEmpty: {
		type: Boolean,
		default: false,
	},
});

const assignees = computed(() => resolveAssignees(props.assign, props.users));
const visible = computed(() => assignees.value.slice(0, props.max));
const hiddenCount = computed(() => Math.max(0, assignees.value.length - props.max));
const title = computed(() => assignees.value.map((user) => user.fullName).join(", "));
</script>

<template>
	<div v-if="assignees.length" class="flex items-center -space-x-1" :title="title">
		<UserAvatar
			v-for="user in visible"
			:key="user.name"
			:name="user.name"
			:full-name="user.fullName"
			:image="user.image"
			:size="size"
			ring
		/>
		<span
			v-if="hiddenCount"
			class="inline-flex h-6 min-w-6 items-center justify-center rounded-full bg-gray-200 px-1 text-[10px] font-semibold text-gray-700 ring-2 ring-white"
		>
			+{{ hiddenCount }}
		</span>
	</div>
	<span
		v-else-if="showEmpty"
		class="inline-flex h-6 w-6 items-center justify-center rounded-full border border-dashed border-gray-300 text-gray-400"
		:title="translate('Unassigned')"
	>
		<User class="h-3 w-3" />
	</span>
</template>
