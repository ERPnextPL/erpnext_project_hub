import MarkdownIt from "markdown-it";
import DOMPurify from "dompurify";

// Safe URL protocols whitelist
const SAFE_PROTOCOLS = /^(https?|mailto|tel|ftp):/i;
const SAFE_DATA_URL = /^data:image\/(gif|png|jpeg|webp);/i;

/**
 * Validates URLs to prevent XSS via dangerous protocols like javascript:, vbscript:, data:
 * Only allows safe protocols: http, https, mailto, tel, ftp, and safe image data URLs
 */
function validateLinkUrl(url) {
	if (!url) return false;
	const trimmedUrl = url.trim().toLowerCase();
	// Allow relative URLs (starting with / or # or no protocol)
	if (trimmedUrl.startsWith("/") || trimmedUrl.startsWith("#") || !trimmedUrl.includes(":")) {
		return true;
	}
	// Allow safe protocols
	if (SAFE_PROTOCOLS.test(trimmedUrl)) {
		return true;
	}
	// Allow safe data URLs (images only)
	if (SAFE_DATA_URL.test(trimmedUrl)) {
		return true;
	}
	return false;
}

const markdownParser = new MarkdownIt({
	html: true,
	linkify: true,
	typographer: true,
	breaks: true,
});

// Override default link validator to prevent javascript: and other dangerous URLs
const defaultLinkValidator = markdownParser.validateLink.bind(markdownParser);
markdownParser.validateLink = function (url) {
	return defaultLinkValidator(url) && validateLinkUrl(url);
};

export function renderMarkdown(value) {
	if (!value) {
		return "";
	}
	return DOMPurify.sanitize(markdownParser.render(value), {
		USE_PROFILES: { html: true },
	});
}
