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

const lookupMessage = (text) => {
	const win = getGlobalWindow();
	const messages = win && win.messages;
	return messages && Object.prototype.hasOwnProperty.call(messages, text) ? messages[text] : text;
};

export const formatTranslation = (text, replacements) =>
	formatWithReplacements(lookupMessage(text), replacements);
export const getRealWindow = () => getGlobalWindow();

export const translate = (text, replacements) => {
	const win = getGlobalWindow();
	if (win && typeof win.__ === "function") {
		return win.__(text, replacements);
	}
	return formatTranslation(text, replacements);
};
