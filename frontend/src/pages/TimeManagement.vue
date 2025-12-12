<script setup>
import { RouterLink } from 'vue-router'
import { Clock, Lock, Sparkles, ArrowLeft } from 'lucide-vue-next'
</script>

<template>
	<div class="min-h-screen bg-gray-50">
		<!-- Header -->
		<header class="bg-white border-b border-gray-200 sticky top-0 z-10">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				<div class="flex items-center justify-between h-16">
					<div class="flex items-center gap-3">
						<Clock class="w-6 h-6 text-emerald-600" />
						<h1 class="text-xl font-semibold text-gray-900">Zarządzanie czasem pracy</h1>
					</div>
					<RouterLink 
						to="/outliner" 
						class="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
					>
						<ArrowLeft class="w-4 h-4" />
						Powrót
					</RouterLink>
				</div>
			</div>
		</header>

		<!-- Pro Feature Placeholder -->
		<div class="max-w-2xl mx-auto px-4 py-16">
			<div class="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 text-center">
				<!-- Icon -->
				<div class="w-20 h-20 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
					<Clock class="w-10 h-10 text-white" />
				</div>

				<!-- Badge -->
				<div class="inline-flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r from-amber-400 to-orange-500 text-white text-sm font-semibold rounded-full mb-4">
					<Sparkles class="w-4 h-4" />
					PRO
				</div>

				<!-- Title -->
				<h2 class="text-2xl font-bold text-gray-900 mb-3">
					Zarządzanie czasem pracowników
				</h2>

				<!-- Description -->
				<p class="text-gray-600 mb-6 max-w-md mx-auto">
					Przeglądaj i zarządzaj zarejestrowanym czasem pracy wszystkich członków zespołu. Generuj raporty i analizuj produktywność.
				</p>

				<!-- Features list -->
				<div class="bg-gray-50 rounded-xl p-6 mb-6 text-left">
					<h3 class="text-sm font-semibold text-gray-700 mb-3">Co zawiera wersja Pro:</h3>
					<ul class="space-y-2 text-sm text-gray-600">
						<li class="flex items-center gap-2">
							<div class="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
							Przegląd czasu pracy całego zespołu
						</li>
						<li class="flex items-center gap-2">
							<div class="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
							Zatwierdzanie i odrzucanie wpisów czasu
						</li>
						<li class="flex items-center gap-2">
							<div class="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
							Raporty tygodniowe i miesięczne
						</li>
						<li class="flex items-center gap-2">
							<div class="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
							Analiza czasu według projektów
						</li>
						<li class="flex items-center gap-2">
							<div class="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
							Eksport do Excel/PDF
						</li>
						<li class="flex items-center gap-2">
							<div class="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
							Integracja z systemem płac
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
