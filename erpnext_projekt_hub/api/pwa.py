"""
PWA Service Worker endpoint.

Serves the service worker JavaScript via Frappe API with correct MIME type.
The SW is served at /api/method/erpnext_projekt_hub.api.pwa.service_worker
and needs Service-Worker-Allowed header (set via after_request hook in hooks.py)
to extend its scope to /project-hub/.
"""

import frappe

SW_JS = """\
const CACHE_VERSION = 'projekt-hub-v1';
const STATIC_CACHE = CACHE_VERSION + '-static';
const API_CACHE = CACHE_VERSION + '-api';

// Critical assets: SW install FAILS if any of these can't be cached.
// This guarantees the app shell works offline.
const CRITICAL_PRECACHE_URLS = [
  '/project-hub',
  '/assets/erpnext_projekt_hub/frontend/assets/main.js',
  '/assets/erpnext_projekt_hub/frontend/assets/index.css',
  '/assets/erpnext_projekt_hub/frontend/assets/frappe-ui.css',
];

// Optional assets: cached if available, failures don't block SW install.
const OPTIONAL_PRECACHE_URLS = [
  '/assets/erpnext_projekt_hub/frontend/manifest.json',
  '/assets/erpnext_projekt_hub/frontend/favicon.svg',
  '/assets/erpnext_projekt_hub/frontend/icons/icon-192.png',
  '/assets/erpnext_projekt_hub/frontend/icons/icon-512.png',
];

// API endpoints safe to cache (read-only, GET-like)
const CACHEABLE_API_PATTERNS = [
  'get_project_tasks',
  'get_task_detail',
  'get_all_projects',
  'get_users',
  'get_projects_settings',
  'get_project_users',
  'get_activity_types',
  'get_task_statuses',
  'get_task_priorities',
  'get_task_timelogs',
  'get_task_subtasks',
  'get_project_milestones',
  'get_my_tasks',
  'get_my_timelogs',
  'get_my_tasks_projects',
];

// Metadata endpoints (rarely change, cache longer)
const METADATA_API_PATTERNS = [
  'get_activity_types',
  'get_task_statuses',
  'get_task_priorities',
  'get_projects_settings',
];

// Max age for cached API responses (in ms)
const API_CACHE_MAX_AGE = 30 * 60 * 1000;       // 30 minutes
const METADATA_CACHE_MAX_AGE = 24 * 60 * 60 * 1000; // 24 hours

// ─── Install: pre-cache app shell ───────────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then(async (cache) => {
      // Critical assets MUST succeed - if any fail, SW install is aborted
      await cache.addAll(CRITICAL_PRECACHE_URLS);
      // Optional assets - cache individually, ignore failures
      await Promise.allSettled(
        OPTIONAL_PRECACHE_URLS.map((url) =>
          cache.add(url).catch((err) => {
            console.warn('[SW] Optional pre-cache skipped:', url, err);
          })
        )
      );
    })
  );
  self.skipWaiting();
});

// ─── Activate: clean old caches ─────────────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key !== STATIC_CACHE && key !== API_CACHE)
          .map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// ─── Fetch: routing logic ───────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // 1) Static assets (/assets/erpnext_projekt_hub/frontend/...)
  //    Strategy: Cache First, fallback to network
  if (url.pathname.startsWith('/assets/erpnext_projekt_hub/frontend/')) {
    event.respondWith(cacheFirst(event.request, STATIC_CACHE));
    return;
  }

  // 2) JS chunk files loaded lazily (also static)
  if (url.pathname.startsWith('/assets/') && url.pathname.endsWith('.js')) {
    event.respondWith(cacheFirst(event.request, STATIC_CACHE));
    return;
  }

  // 3) API calls (POST to /api/method/erpnext_projekt_hub.api.project_hub.*)
  if (url.pathname.startsWith('/api/method/erpnext_projekt_hub.api.project_hub.')) {
    const endpoint = url.pathname.split('.').pop();

    if (isCacheableEndpoint(endpoint)) {
      event.respondWith(networkFirstForAPI(event.request, endpoint));
      return;
    }

    // Write endpoints: network only, no caching
    event.respondWith(fetch(event.request));
    return;
  }

  // 4) HTML pages (/project-hub, /project-hub/*)
  //    Strategy: Network First, fallback to cached shell
  if (url.pathname.startsWith('/project-hub')) {
    event.respondWith(networkFirstForPage(event.request));
    return;
  }

  // 5) Everything else: passthrough
  event.respondWith(fetch(event.request));
});

// ─── Caching strategies ─────────────────────────────────────────────

// Cache First: check cache, fallback to network (and update cache)
async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    // Offline and not in cache
    return new Response('Offline', { status: 503, statusText: 'Offline' });
  }
}

// Network First for API: try network, cache response, fallback to cache
async function networkFirstForAPI(request, endpoint) {
  const cacheKey = await buildAPICacheKey(request, endpoint);

  try {
    const response = await fetch(request.clone());
    if (response.ok) {
      // Store in cache with timestamp
      const cache = await caches.open(API_CACHE);
      const responseToCache = response.clone();
      const headers = new Headers(responseToCache.headers);
      headers.set('X-SW-Cached-At', Date.now().toString());
      const cachedResponse = new Response(await responseToCache.blob(), {
        status: responseToCache.status,
        statusText: responseToCache.statusText,
        headers: headers,
      });
      await cache.put(cacheKey, cachedResponse);
    }
    return response;
  } catch (err) {
    // Offline: serve ANY cached data regardless of age.
    // Stale data is always better than no data when offline.
    const cache = await caches.open(API_CACHE);
    const cached = await cache.match(cacheKey);
    if (cached) {
      return cached;
    }
    // Nothing in cache at all: return offline error as JSON (Frappe format)
    return new Response(
      JSON.stringify({ message: 'Offline - no cached data available', _offline: true }),
      { status: 503, headers: { 'Content-Type': 'application/json' } }
    );
  }
}

// Network First for HTML pages: try network, fallback to cached page
async function networkFirstForPage(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    // Offline: serve cached HTML
    const cached = await caches.match(request) || await caches.match('/project-hub');
    if (cached) return cached;
    return new Response(
      '<html><body><h1>Offline</h1><p>Projekt HUB is not available offline yet. Please reconnect.</p></body></html>',
      { status: 503, headers: { 'Content-Type': 'text/html' } }
    );
  }
}

// ─── Helpers ────────────────────────────────────────────────────────

function isCacheableEndpoint(endpoint) {
  return CACHEABLE_API_PATTERNS.includes(endpoint);
}

function isMetadataEndpoint(endpoint) {
  return METADATA_API_PATTERNS.includes(endpoint);
}

// Build a unique cache key for POST API requests
// Uses URL + sorted body params to create a GET-like cache key
async function buildAPICacheKey(request, endpoint) {
  try {
    const cloned = request.clone();
    const formData = await cloned.formData();
    const params = new URLSearchParams();
    for (const [key, value] of formData.entries()) {
      if (typeof value === 'string') {
        params.set(key, value);
      }
    }
    params.sort();
    return new Request(request.url + '?_sw_cache=' + params.toString(), { method: 'GET' });
  } catch (err) {
    // Fallback: just use the URL
    return new Request(request.url + '?_sw_cache=default', { method: 'GET' });
  }
}
"""


@frappe.whitelist(allow_guest=False)
def service_worker():
	"""Serve the PWA service worker as JavaScript binary response.

	Frappe's binary response type sets Content-Type based on filename extension,
	so filename='sw.js' → Content-Type: application/javascript.
	The Service-Worker-Allowed header is added via after_request hook in hooks.py.
	"""
	frappe.local.response.update(
		{
			"type": "binary",
			"filename": "sw.js",
			"filecontent": SW_JS.encode("utf-8"),
		}
	)


def add_sw_allowed_header(response=None, **kwargs):
	"""after_request hook: add Service-Worker-Allowed header for SW endpoint."""
	if response is None:
		return
	try:
		path = frappe.request.path if frappe.request else ""
		if "pwa.service_worker" in path:
			response.headers["Service-Worker-Allowed"] = "/project-hub"
			response.headers["Content-Type"] = "application/javascript"
	except Exception:
		pass
