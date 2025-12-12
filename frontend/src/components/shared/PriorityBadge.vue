<script setup>
import { computed } from 'vue'
import { Flag } from 'lucide-vue-next'

const props = defineProps({
	priority: {
		type: String,
		required: true,
	},
	size: {
		type: String,
		default: 'sm', // 'xs', 'sm', 'md'
	},
	showLabel: {
		type: Boolean,
		default: true,
	},
	showIcon: {
		type: Boolean,
		default: true,
	},
})

// Priority configuration - shared across all components
const priorityConfig = {
	'Urgent': { class: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200', label: 'Pilne' },
	'High': { class: 'text-orange-500', bg: 'bg-orange-50', border: 'border-orange-200', label: 'Wysokie' },
	'Medium': { class: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200', label: 'Średnie' },
	'Low': { class: 'text-gray-500', bg: 'bg-gray-50', border: 'border-gray-200', label: 'Niskie' },
}

const config = computed(() => {
	return priorityConfig[props.priority] || priorityConfig['Medium']
})

const sizeClasses = computed(() => {
	switch (props.size) {
		case 'xs':
			return {
				badge: 'px-1.5 py-0.5 text-xs',
				icon: 'w-3 h-3',
			}
		case 'md':
			return {
				badge: 'px-3 py-1.5 text-sm',
				icon: 'w-4 h-4',
			}
		default: // sm
			return {
				badge: 'px-2 py-1 text-xs',
				icon: 'w-3.5 h-3.5',
			}
	}
})
</script>

<template>
	<span 
		:class="[
			'inline-flex items-center gap-1 rounded font-medium',
			config.class,
			showLabel ? [config.bg, config.border, 'border', sizeClasses.badge] : ''
		]"
	>
		<Flag v-if="showIcon" :class="sizeClasses.icon" />
		<span v-if="showLabel">{{ config.label }}</span>
	</span>
</template>
