// This file is the SPA's Vite entry, served with a cache-busting query string
// (project-hub.html: main.js?v=<asset hash>, see www/project_hub.py). A lazy
// route chunk that needs code from here would import a URL without that query
// string ("../main.js"), which the browser treats as a different module from
// "main.js?v=…" — loading and running the whole app a second time (two Vue
// apps mounting on #app, loadPlugins() firing twice, Pinia state split across
// the two instances). So this entry must never hold code a chunk can import:
// it only kicks off the real bootstrap as a dynamic import, which Vite then
// emits as its own hashed chunk that every importer references identically.
//
// The bootstrap file is named index.js, not bootstrap.js: Vite names a
// dynamic import's extracted CSS after its chunk, and project-hub.html /
// www/project_hub.py hardcode the built CSS as "index.css".
import("./index.js");
