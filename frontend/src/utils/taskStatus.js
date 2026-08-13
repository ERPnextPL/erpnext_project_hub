import { AlertCircle, CheckCircle2, Circle, Clock } from "lucide-vue-next";
import { translate } from "./translation";

/**
 * Single source of truth for Task statuses across the Projekt HUB frontend.
 *
 * The values below are the `status` field options of the ERPNext Task DocType.
 * They travel to and from the backend unchanged - never relabel a status in a
 * component. Only the displayed label is localised, and the English status
 * value doubles as the translation source string (see translations/pl.csv).
 */
export const TASK_STATUSES = [
	"Open",
	"Working",
	"Pending Review",
	"Overdue",
	"Template",
	"Completed",
	"Cancelled",
];

/**
 * Statuses offered as board columns and filter options. "Template" only ever
 * applies to template tasks, which are never part of a project.
 */
export const BOARD_STATUSES = TASK_STATUSES.filter((status) => status !== "Template");

/** Statuses counted as still open - the default filter selection. */
export const ACTIVE_STATUSES = ["Open", "Working", "Pending Review", "Overdue"];

const STATUS_CONFIG = {
	Open: {
		icon: Circle,
		text: "text-blue-600",
		strongText: "text-blue-700",
		softBg: "bg-blue-50",
		badgeBg: "bg-blue-100",
		border: "border-blue-200",
		dot: "bg-blue-500",
		solidBg: "bg-blue-100 border border-blue-200",
		solidText: "text-slate-700",
		rowClass: "status-open",
	},
	Working: {
		icon: Clock,
		text: "text-amber-600",
		strongText: "text-amber-700",
		softBg: "bg-amber-50",
		badgeBg: "bg-amber-100",
		border: "border-amber-200",
		dot: "bg-amber-500",
		solidBg: "bg-amber-600 border border-amber-600",
		solidText: "text-white",
		rowClass: "status-working",
	},
	"Pending Review": {
		icon: AlertCircle,
		text: "text-purple-600",
		strongText: "text-purple-700",
		softBg: "bg-purple-50",
		badgeBg: "bg-purple-100",
		border: "border-purple-200",
		dot: "bg-purple-500",
		solidBg: "bg-purple-600 border border-purple-600",
		solidText: "text-white",
		rowClass: "status-pending-review",
	},
	Overdue: {
		icon: AlertCircle,
		text: "text-red-600",
		strongText: "text-red-700",
		softBg: "bg-red-50",
		badgeBg: "bg-red-100",
		border: "border-red-200",
		dot: "bg-red-500",
		solidBg: "bg-red-600 border border-red-600",
		solidText: "text-white",
		rowClass: "status-overdue",
	},
	Template: {
		icon: Circle,
		text: "text-gray-500",
		strongText: "text-gray-700",
		softBg: "bg-gray-50",
		badgeBg: "bg-gray-100",
		border: "border-gray-200",
		dot: "bg-gray-400",
		solidBg: "bg-gray-500 border border-gray-500",
		solidText: "text-white",
		rowClass: "status-template",
	},
	Completed: {
		icon: CheckCircle2,
		text: "text-green-600",
		strongText: "text-green-700",
		softBg: "bg-green-50",
		badgeBg: "bg-green-100",
		border: "border-green-200",
		dot: "bg-green-500",
		solidBg: "bg-green-600 border border-green-600",
		solidText: "text-white",
		rowClass: "status-completed",
	},
	Cancelled: {
		icon: Circle,
		text: "text-gray-500",
		strongText: "text-gray-700",
		softBg: "bg-gray-50",
		badgeBg: "bg-gray-100",
		border: "border-gray-200",
		dot: "bg-gray-400",
		solidBg: "bg-gray-600 border border-gray-600",
		solidText: "text-white",
		rowClass: "status-cancelled",
	},
};

const FALLBACK_STATUS = "Open";

/** Colours, icon and CSS classes for a status. Unknown statuses fall back to Open. */
export function getStatusConfig(status) {
	return STATUS_CONFIG[status] || STATUS_CONFIG[FALLBACK_STATUS];
}

/** Localised label. The status value itself is the translation source string. */
export function getStatusLabel(status) {
	return status ? translate(status) : "";
}

/** Soft badge: light background, coloured text, matching border. */
export function getStatusBadge(status) {
	const config = getStatusConfig(status);
	return {
		icon: config.icon,
		label: getStatusLabel(status),
		bg: config.badgeBg,
		text: config.strongText,
		border: config.border,
		class: `${config.badgeBg} ${config.strongText} ${config.border}`,
	};
}

/** Solid badge: saturated background, white text. Open stays muted on purpose. */
export function getStatusSolid(status) {
	const config = getStatusConfig(status);
	return {
		icon: config.icon,
		label: getStatusLabel(status),
		bg: config.solidBg,
		class: config.solidText,
	};
}

/** Option shape for dropdowns and filter chips. */
export function getStatusOption(status) {
	const config = getStatusConfig(status);
	return {
		value: status,
		label: getStatusLabel(status),
		icon: config.icon,
		class: config.text,
		bg: config.softBg,
	};
}
