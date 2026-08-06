<script setup>
import { computed } from "vue";
import { Folder, ChevronRight, Calendar, Users, User, Flag, PauseCircle, CheckCircle2 } from "lucide-vue-next";
import { translate } from "../utils/translation";
import { getProgressColorClass } from "../utils/progressColors";
import {
	customerInitials,
	formatDate,
	isOverdue,
	getStatusClass,
	STATUS_VARIANTS,
} from "../utils/projectDisplay";

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
			'bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-5 hover:shadow-md transition-all cursor-pointer group focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1',
			v.hoverBorder,
			v.opacity,
		]"
	>
		<div class="flex items-start justify-between mb-3">
			<div class="flex items-center gap-2.5 min-w-0">
				<img
					v-if="project.customer_image"
					:src="project.customer_image"
					:alt="project.customer_name"
					class="w-8 h-8 rounded-md object-contain border border-gray-100 dark:border-gray-700 bg-white flex-shrink-0"
				/>
				<div
					v-else-if="project.customer_name"
					:class="['w-8 h-8 rounded-md flex items-center justify-center text-xs font-semibold flex-shrink-0 select-none', v.avatarClass]"
				>
					{{ customerInitials(project.customer_name) }}
				</div>
				<Folder v-else :class="['w-5 h-5 flex-shrink-0', v.iconClass]" />
				<h3 :class="['font-medium text-gray-900 dark:text-gray-100 truncate', v.hoverText]">
					{{ project.project_name }}
				</h3>
			</div>
			<ChevronRight :class="['w-5 h-5 text-gray-400 transition-colors flex-shrink-0', v.hoverText]" />
		</div>

		<!-- Progress (active + on hold only) -->
		<div v-if="variant !== 'completed'" class="mb-3">
			<div class="flex items-center justify-between text-xs mb-1">
				<span class="text-gray-500 dark:text-gray-400">{{ translate("Progress") }}</span>
				<span class="font-medium text-gray-700 dark:text-gray-300">{{ project.percent_complete || 0 }}%</span>
			</div>
			<div class="w-full h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
				<div
					:class="[
						'h-full rounded-full transition-all duration-300',
						variant === 'active' ? getProgressColorClass(project.percent_complete || 0) : 'bg-amber-400',
					]"
					:style="{ width: (project.percent_complete || 0) + '%' }"
				></div>
			</div>
		</div>

		<div class="space-y-1.5">
			<div v-if="variant === 'active'" class="flex items-center gap-2 text-sm">
				<span :class="['px-2 py-0.5 rounded-full text-xs font-medium', getStatusClass(project.status)]">
					{{ translate(project.status) }}
				</span>
			</div>
			<div v-else-if="variant === 'onHold'" class="flex items-center gap-2 text-sm">
				<span class="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300 rounded-full text-xs font-medium">
					<PauseCircle class="w-3 h-3" />
					{{ translate("On hold") }}
				</span>
			</div>
			<div v-else class="mb-1.5">
				<span class="inline-flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded-full text-xs font-medium">
					<CheckCircle2 class="w-3 h-3" />
					{{ translate("Completed") }}
				</span>
			</div>

			<div
				v-if="project.expected_end_date"
				class="flex items-center gap-1.5 text-sm"
				:class="variant === 'active' && isOverdue(project) ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'"
			>
				<Calendar class="w-3.5 h-3.5" />
				<span>{{ formatDate(project.expected_end_date) }}</span>
				<span v-if="variant === 'active' && isOverdue(project)" class="text-xs font-medium">({{ translate("overdue") }})</span>
			</div>

			<div v-if="project.project_manager_name" class="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
				<User class="w-3.5 h-3.5" />
				<span class="truncate">{{ project.project_manager_name }}</span>
			</div>

			<div class="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
				<div class="flex items-center gap-1.5">
					<Users class="w-3.5 h-3.5" />
					<span>{{ project.task_count || 0 }} {{ translate("tasks") }}</span>
				</div>
				<div v-if="variant === 'active' && project.user_task_count" class="flex items-center gap-1 text-blue-600 dark:text-blue-400">
					<span>{{ project.user_task_count }} {{ translate("yours") }}</span>
				</div>
			</div>

			<div v-if="variant === 'active' && project.assigned_users_count > 0" class="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
				<Users class="w-3.5 h-3.5 text-purple-500" />
				<span>{{ project.assigned_users_count }} {{ project.assigned_users_count === 1 ? translate("person") : translate("people") }}</span>
			</div>

			<div v-if="variant === 'active' && project.next_milestone" class="flex items-center gap-1.5 text-sm">
				<Flag class="w-3.5 h-3.5 text-amber-500" />
				<span :class="[project.days_to_milestone < 0 ? 'text-red-600 dark:text-red-400 font-medium' : project.days_to_milestone <= 3 ? 'text-amber-600 dark:text-amber-400 font-medium' : 'text-gray-500 dark:text-gray-400']">
					<template v-if="project.days_to_milestone < 0">{{ translate("Milestone overdue") }}</template>
					<template v-else-if="project.days_to_milestone === 0">{{ translate("Milestone due today") }}</template>
					<template v-else-if="project.days_to_milestone === 1">{{ translate("Milestone due tomorrow") }}</template>
					<template v-else>{{ translate("{days} days to milestone", { days: project.days_to_milestone }) }}</template>
				</span>
			</div>
		</div>
	</div>
</template>
