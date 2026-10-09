export function customerInitials(name) {
	if (!name) return "?";
	return name
		.split(/\s+/)
		.slice(0, 2)
		.map((w) => w[0].toUpperCase())
		.join("");
}

export function formatDate(dateStr) {
	if (!dateStr) return null;
	const d = new Date(dateStr);
	return d.toLocaleDateString("pl-PL", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export function isOverdue(project) {
	if (!project.expected_end_date || project.status === "Completed" || project.status === "On hold")
		return false;
	const due = new Date(project.expected_end_date);
	due.setHours(23, 59, 59, 999);
	return due < new Date();
}

export function getStatusClass(status) {
	const classes = {
		Open: "bg-blue-100 text-blue-800",
		"On hold": "bg-amber-100 text-amber-800",
		Completed: "bg-green-100 text-green-800",
		Cancelled: "bg-gray-100 text-gray-600",
	};
	return classes[status] || "bg-gray-100 text-gray-600";
}

// Per-status-section accent styling shared by ProjectCard / ProjectListRow / ProjectListHeader.
export const STATUS_VARIANTS = {
	active: {
		iconClass: "text-blue-600",
		avatarClass: "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300",
		hoverBorder: "hover:border-blue-300 dark:hover:border-blue-600",
		hoverText: "group-hover:text-blue-600 dark:group-hover:text-blue-400",
		opacity: "",
		sortable: true,
	},
	onHold: {
		iconClass: "text-amber-600",
		avatarClass: "bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300",
		hoverBorder: "hover:border-amber-300 dark:hover:border-amber-600",
		hoverText: "group-hover:text-amber-600",
		opacity: "opacity-90 hover:opacity-100",
		sortable: false,
	},
	completed: {
		iconClass: "text-green-600",
		avatarClass: "bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300",
		hoverBorder: "hover:border-green-300 dark:hover:border-green-600",
		hoverText: "group-hover:text-green-600",
		opacity: "opacity-75 hover:opacity-100",
		sortable: false,
	},
};
