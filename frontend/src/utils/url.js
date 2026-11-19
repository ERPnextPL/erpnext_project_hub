/**
 * Turn a user-typed link into a safe, openable http(s) URL.
 * Adds https:// when no scheme is given; returns "" for empty or non-http(s) values.
 */
export function toOpenableUrl(value) {
	const raw = (value || "").trim();
	if (!raw) return "";
	const withProtocol = /^[a-z][a-z0-9+.-]*:/i.test(raw) ? raw : `https://${raw}`;
	return /^https?:\/\//i.test(withProtocol) ? withProtocol : "";
}
