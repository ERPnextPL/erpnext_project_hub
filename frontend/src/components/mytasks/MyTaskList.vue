<script setup>
import { computed } from 'vue'
import { useMyTasksStore } from '../../stores/myTasksStore'
import MyTaskRowDesktop from './MyTaskRowDesktop.vue'
import MyTaskCardMobile from './MyTaskCardMobile.vue'
import { useWindowSize } from '@vueuse/core'

const store = useMyTasksStore()
const { width } = useWindowSize()
const isMobile = computed(() => width.value < 768)
</script>

<template>
	<div>
		<!-- Task list -->
		<div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
			<!-- Table header (desktop only) -->
			<div v-if="!isMobile" class="grid grid-cols-12 gap-4 px-4 py-3 bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-500 uppercase tracking-wider">
				<div class="col-span-4">Zadanie</div>
				<div class="col-span-2">Projekt</div>
				<div class="col-span-2">Status</div>
				<div class="col-span-2">Priorytet</div>
				<div class="col-span-2">Termin</div>
			</div>
			
			<!-- Task rows -->
			<div class="divide-y divide-gray-100">
				<template v-for="task in store.tasks" :key="task.name">
					<!-- Desktop row -->
					<MyTaskRowDesktop 
						v-if="!isMobile" 
						:task="task" 
					/>
					<!-- Mobile card -->
					<MyTaskCardMobile 
						v-else 
						:task="task" 
					/>
				</template>
			</div>
		</div>

		<!-- Load more / pagination info -->
		<div v-if="store.tasks.length > 0" class="mt-4 text-center text-sm text-gray-500">
			Wyświetlono {{ store.tasks.length }} z {{ store.total }} zadań
		</div>
	</div>
</template>
