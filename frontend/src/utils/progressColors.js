export function getProgressColorClass(percent) {
	const value = Number(percent);
	if (!Number.isFinite(value)) return "bg-gray-300";

	const normalized = Math.max(0, Math.min(100, value));
	if (normalized >= 80) return "bg-green-500";
	if (normalized >= 50) return "bg-blue-500";
	if (normalized >= 25) return "bg-amber-500";
	return "bg-gray-300";
}
