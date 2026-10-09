// Stable colour per project, so a project keeps its colour across the work plan.
const PROJECT_COLORS = [
	{ chip: "bg-blue-50 text-blue-800 border-blue-200 hover:bg-blue-100", dot: "bg-blue-500" },
	{ chip: "bg-green-50 text-green-800 border-green-200 hover:bg-green-100", dot: "bg-green-500" },
	{ chip: "bg-amber-50 text-amber-800 border-amber-200 hover:bg-amber-100", dot: "bg-amber-500" },
	{ chip: "bg-violet-50 text-violet-800 border-violet-200 hover:bg-violet-100", dot: "bg-violet-500" },
	{ chip: "bg-pink-50 text-pink-800 border-pink-200 hover:bg-pink-100", dot: "bg-pink-500" },
	{ chip: "bg-cyan-50 text-cyan-800 border-cyan-200 hover:bg-cyan-100", dot: "bg-cyan-500" },
	{ chip: "bg-yellow-50 text-yellow-800 border-yellow-200 hover:bg-yellow-100", dot: "bg-yellow-600" },
	{ chip: "bg-purple-50 text-purple-800 border-purple-200 hover:bg-purple-100", dot: "bg-purple-500" },
	{ chip: "bg-orange-50 text-orange-800 border-orange-200 hover:bg-orange-100", dot: "bg-orange-500" },
	{ chip: "bg-teal-50 text-teal-800 border-teal-200 hover:bg-teal-100", dot: "bg-teal-500" },
];

export function getProjectColor(project) {
	let hash = 0;
	for (const char of String(project || "")) {
		hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
	}
	return PROJECT_COLORS[hash % PROJECT_COLORS.length];
}
