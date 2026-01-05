const getGlobalWindow = () => (typeof globalThis !== "undefined" ? globalThis.window : undefined);

const formatWithReplacements = (text, replacements) => {
	if (!text || replacements == null) {
		return text;
	}

	const args = Array.isArray(replacements)
		? replacements
		: typeof replacements === "object"
		? replacements
		: [replacements];

	let unkeyedIndex = 0;

	return text.replace(/\{(\w*)\}/g, (match, key) => {
		const resolvedKey = key === "" ? unkeyedIndex++ : key;
		return Object.prototype.hasOwnProperty.call(args, resolvedKey) ? args[resolvedKey] : match;
	});
};

export const formatTranslation = formatWithReplacements;
export const getRealWindow = () => getGlobalWindow();

export const translate = (text, replacements) => {
	const win = getGlobalWindow();
	if (win && typeof win.__ === "function") {
		return win.__(text, replacements);
	}
	return formatWithReplacements(text, replacements);
};
