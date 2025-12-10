/** @type {import('tailwindcss').Config} */
export default {
	presets: [require('frappe-ui/tailwind')],
	content: [
		'./index.html',
		'./src/**/*.{vue,js,ts,jsx,tsx}',
		'../node_modules/frappe-ui/src/**/*.{vue,js,ts}',
	],
	theme: {
		extend: {
			colors: {
				'task-open': '#3b82f6',
				'task-working': '#f59e0b',
				'task-completed': '#10b981',
				'task-overdue': '#ef4444',
				'task-cancelled': '#6b7280',
			},
		},
	},
	plugins: [],
}
