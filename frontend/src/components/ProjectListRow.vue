<script setup>
import { computed } from "vue";
import { Folder, Calendar, User, Users, CheckCircle2 } from "lucide-vue-next";
import { translate } from "../utils/translation";
import { getProgressColorClass } from "../utils/progressColors";
import { customerInitials, formatDate, isOverdue, STATUS_VARIANTS } from "../utils/projectDisplay";

const props = defineProps({
	project: { type: Object, required: true },
	variant: { type: String, required: true }, // 'active' | 'onHold' | 'completed'
});

const emit = defineEmits(["open"]);

const v = computed(() => STATUS_VARIANTS[props.variant]);
</script>

<template>
	<div
		role="button"
		tabindex="0"
		@click="emit('open', project.name)"
		@keydown.enter="emit('open', project.name)"
		@keydown.space.prevent="emit('open', project.name)"
		:class="[
			'grid grid-cols-[minmax(0,2fr)_repeat(4,minmax(0,1fr))] gap-4 px-4 py-3 border-b border-gray-100 dark:border-gray-700 last:border-b-0 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer group transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500',
			v.opacity,
		]"
	>
		<!-- Name -->
		<div class="flex items-center gap-2 min-w-0">
			<img
				v-if="project.customer_image"
				:src="project.customer_image"
				:alt="project.customer_name"
				class="w-6 h-6 rounded object-contain border border-gray-100 dark:border-gray-700 bg-white flex-shrink-0"
			/>
			<div
				v-else-if="project.customer_name"
				:class="['w-6 h-6 rounded flex items-center justify-center text-[10px] font-semibold flex-shrink-0 select-none', v.avatarClass]"
			>
				{{ customerInitials(project.customer_name) }}
			</div>
			<Folder v-else :class="['w-4 h-4 flex-shrink-0', v.iconClass]" />
			<span :class="['font-medium text-gray-900 dark:text-gray-100 truncate text-sm', v.hoverText]">
				{{ project.project_name }}
			</span>
		</div>

		<!-- Progress -->
		<div v-if="variant !== 'completed'" class="flex items-center gap-2 min-w-0">
			<div class="flex-1 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden min-w-[40px]">
				<div
					:class="[
						'h-full rounded-full transition-all',
						variant === 'active' ? getProgressColorClass(project.percent_complete || 0) : 'bg-amber-400',
					]"
					:style="{ width: (project.percent_complete || 0) + '%' }"
				></div>
			</div>
			<span class="text-xs text-gray-600 dark:text-gray-400 flex-shrink-0">{{ project.percent_complete || 0 }}%</span>
		</div>
		<div v-else class="flex items-center gap-1.5">
			<CheckCircle2 class="w-3.5 h-3.5 text-green-600 flex-shrink-0" />
			<span class="text-xs text-green-700 dark:text-green-400">100%</span>
		</div>

		<!-- Deadline -->
		<div
			class="flex items-center gap-1.5 text-sm"
			:class="variant === 'active' && isOverdue(project) ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'"
		>
			<Calendar v-if="project.expected_end_date" class="w-3.5 h-3.5 flex-shrink-0" />
			<span class="truncate">
				{{ project.expected_end_date ? formatDate(project.expected_end_date) : "—" }}
			</span>
		</div>

		<!-- Manager -->
		<div class="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400 min-w-0">
			<User v-if="project.project_manager_name" class="w-3.5 h-3.5 flex-shrink-0" />
			<span class="truncate">{{ project.project_manager_name || "—" }}</span>
		</div>

		<!-- Tasks -->
		<div class="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
			<Users class="w-3.5 h-3.5 flex-shrink-0" />
			<span>{{ project.task_count || 0 }}</span>
			<span v-if="variant === 'active' && project.user_task_count" class="text-blue-600 dark:text-blue-400 text-xs">({{ project.user_task_count }} {{ translate("yours") }})</span>
		</div>
	</div>
</template>
