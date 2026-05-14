export function stripHtmlToText(value) {
	if (!value) return "";

	const html = String(value).trim();
	if (!html) return "";

	if (typeof document !== "undefined") {
		const wrapper = document.createElement("div");
		wrapper.innerHTML = html;
		return (wrapper.innerText || wrapper.textContent || "").trim();
	}

	const withoutBlocks = html
		.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, " ")
		.replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, " ");

	return withoutBlocks.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}
