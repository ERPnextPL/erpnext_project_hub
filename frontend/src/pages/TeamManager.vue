<script setup>
import { Users, Lock, Sparkles } from 'lucide-vue-next'
import OutlinerNav from '../components/OutlinerNav.vue'
</script>

<template>
	<div class="min-h-screen bg-gray-50">
		<!-- Header -->
		<header class="bg-white border-b border-gray-200 sticky top-0 z-10">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				<div class="flex items-center justify-between h-16">
					<div class="flex items-center gap-3">
						<Users class="w-6 h-6 text-purple-600" />
						<h1 class="text-xl font-semibold text-gray-900">Zarządzanie zespołem</h1>
					</div>
					<div class="flex items-center gap-3 sm:gap-4">
						<OutlinerNav />
						<a
							href="/app"
							class="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1 whitespace-nowrap"
						>
							← Back to Desk
						</a>
					</div>
				</div>
			</div>
		</header>

		<!-- Pro Feature Placeholder -->
		<div class="max-w-2xl mx-auto px-4 py-16">
			<div class="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 text-center">
				<!-- Icon -->
				<div class="w-20 h-20 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
					<Users class="w-10 h-10 text-white" />
				</div>

				<!-- Badge -->
				<div class="inline-flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r from-amber-400 to-orange-500 text-white text-sm font-semibold rounded-full mb-4">
					<Sparkles class="w-4 h-4" />
					PRO
				</div>

				<!-- Title -->
				<h2 class="text-2xl font-bold text-gray-900 mb-3">
					Widok kierownika zespołu
				</h2>

				<!-- Description -->
				<p class="text-gray-600 mb-6 max-w-md mx-auto">
					Zarządzaj zadaniami całego zespołu, przydzielaj pracę, monitoruj postępy i obciążenie pracowników w jednym miejscu.
				</p>

				<!-- Features list -->
				<div class="bg-gray-50 rounded-xl p-6 mb-6 text-left">
					<h3 class="text-sm font-semibold text-gray-700 mb-3">Co zawiera wersja Pro:</h3>
					<ul class="space-y-2 text-sm text-gray-600">
						<li class="flex items-center gap-2">
							<div class="w-1.5 h-1.5 bg-purple-500 rounded-full"></div>
							Widok wszystkich zadań zespołu
						</li>
						<li class="flex items-center gap-2">
							<div class="w-1.5 h-1.5 bg-purple-500 rounded-full"></div>
							Przydzielanie zadań pracownikom
						</li>
						<li class="flex items-center gap-2">
							<div class="w-1.5 h-1.5 bg-purple-500 rounded-full"></div>
							Monitorowanie obciążenia zespołu
						</li>
						<li class="flex items-center gap-2">
							<div class="w-1.5 h-1.5 bg-purple-500 rounded-full"></div>
							Raporty wydajności
						</li>
						<li class="flex items-center gap-2">
							<div class="w-1.5 h-1.5 bg-purple-500 rounded-full"></div>
							Widok Kanban dla zespołu
						</li>
					</ul>
				</div>

				<!-- Lock notice -->
				<div class="flex items-center justify-center gap-2 text-gray-500 text-sm">
					<Lock class="w-4 h-4" />
					<span>Ta funkcja jest dostępna tylko w wersji Pro</span>
				</div>
			</div>
		</div>
	</div>
</template>
