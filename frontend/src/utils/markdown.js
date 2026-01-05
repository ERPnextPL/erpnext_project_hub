import MarkdownIt from "markdown-it";

const markdownParser = new MarkdownIt({
	html: false, // Prevent raw HTML/JS injection
	linkify: true,
	typographer: true,
	breaks: true,
});

export function renderMarkdown(value) {
	if (!value) {
		return "";
	}
	return markdownParser.render(value);
}
