/**
 * Keeps filter state in the page URL so it survives a refresh and can be shared.
 *
 * One-way sync on purpose: the URL is read once when the page sets up, and
 * written on every change. Nothing watches `route.query` afterwards, which is
 * what keeps this free of the write -> read -> write loops that a two-way sync
 * needs guarding against. The trade-off is that Back/Forward changes the address
 * without restoring filters.
 *
 * The default value of a field decides how it is encoded, so the schema is just
 * the defaults object: array -> comma separated, boolean -> 1/0, everything else
 * -> raw string. A field holding its default value is dropped from the URL, so
 * only what the user actually changed shows up in the address bar.
 */

function encodeValue(value) {
	if (Array.isArray(value)) {
		return value.join(",");
	}
	if (typeof value === "boolean") {
		return value ? "1" : "0";
	}
	if (value === null || value === undefined) {
		return "";
	}
	return String(value);
}

function decodeValue(raw, fallback) {
	if (Array.isArray(fallback)) {
		return String(raw ?? "")
			.split(",")
			.map((entry) => entry.trim())
			.filter(Boolean);
	}
	if (typeof fallback === "boolean") {
		return raw === "1";
	}
	if (typeof fallback === "string") {
		return raw ?? "";
	}
	return raw || null;
}

/**
 * Build a filter object from the current query string.
 *
 * A key missing from the query falls back to its default. A key present but
 * empty (`?status=`) is an explicit empty selection - that distinction is why
 * this checks for presence instead of truthiness, and it is what stops a
 * deliberately cleared filter from springing back to its defaults on refresh.
 *
 * `sanitizers` is keyed by field name and runs on the decoded value. Query
 * strings are user-editable and outlive deploys, so anything read from them has
 * to be checked against the values the app currently accepts.
 */
export function readFilters(route, defaults, sanitizers = {}) {
	// Copy array defaults instead of handing out the shared instance: callers
	// mutate the result in place (push/splice on a status list), which would
	// otherwise rewrite `defaults` itself - and a field whose value is literally
	// the default object can never be detected as changed, so it would silently
	// stop being written to the URL.
	const result = {};
	for (const key of Object.keys(defaults)) {
		result[key] = Array.isArray(defaults[key]) ? [...defaults[key]] : defaults[key];
	}

	for (const key of Object.keys(defaults)) {
		if (!(key in (route.query || {}))) continue;

		const queryValue = route.query[key];
		const raw = Array.isArray(queryValue) ? queryValue[0] : queryValue;
		const decoded = decodeValue(raw, defaults[key]);
		const sanitize = sanitizers[key];

		result[key] = sanitize ? sanitize(decoded) : decoded;
	}

	return result;
}

/**
 * Write the filters back into the query string, leaving unrelated query
 * parameters (such as the selected task deep link) untouched.
 *
 * Uses `replace` rather than `push`: filtering is not navigation, and pushing
 * would bury the previous page under one history entry per checkbox click.
 */
export function writeFilters(router, route, filters, defaults) {
	const query = { ...(route.query || {}) };
	let changed = false;

	for (const key of Object.keys(defaults)) {
		const value = filters[key];
		const isDefault = JSON.stringify(value ?? null) === JSON.stringify(defaults[key] ?? null);

		if (isDefault) {
			if (key in query) {
				delete query[key];
				changed = true;
			}
			continue;
		}

		const encoded = encodeValue(value);
		if (query[key] !== encoded) {
			query[key] = encoded;
			changed = true;
		}
	}

	if (!changed) return;

	router.replace({ path: route.path, query, hash: route.hash });
}
