// vite.config.js
import vue from "file:///home/frapcio/frappe-bench/apps/erpnext_projekt_hub/frontend/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import frappeui from "file:///home/frapcio/frappe-bench/apps/erpnext_projekt_hub/frontend/node_modules/frappe-ui/vite/index.js";
import path from "path";
import { defineConfig } from "file:///home/frapcio/frappe-bench/apps/erpnext_projekt_hub/frontend/node_modules/vite/dist/node/index.js";
var __vite_injected_original_dirname = "/home/frapcio/frappe-bench/apps/erpnext_projekt_hub/frontend";
var vite_config_default = defineConfig({
  plugins: [
    frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
      buildConfig: false
    }),
    vue()
  ],
  server: {
    allowedHosts: true
  },
  resolve: {
    alias: {
      vue: "vue/dist/vue.esm-bundler.js",
      "@": path.resolve(__vite_injected_original_dirname, "src"),
      "tailwind.config.js": path.resolve(__vite_injected_original_dirname, "tailwind.config.js")
    }
  },
  build: {
    outDir: `../erpnext_projekt_hub/public/frontend`,
    emptyOutDir: true,
    sourcemap: true,
    rollupOptions: {
      input: {
        main: path.resolve(__vite_injected_original_dirname, "index.html")
      },
      output: {
        // Use fixed filenames without hash for easier template integration
        entryFileNames: "assets/[name].js",
        // Chunk files must be hashed to avoid name collisions/caching issues (e.g. flag.js, archive.js)
        chunkFileNames: "assets/chunks/[name]-[hash].js",
        assetFileNames: "assets/[name].[ext]",
        manualChunks: {
          "frappe-ui": ["frappe-ui"]
        }
      }
    }
  },
  optimizeDeps: {
    include: ["tailwind.config.js"]
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvaG9tZS9mcmFwY2lvL2ZyYXBwZS1iZW5jaC9hcHBzL2VycG5leHRfcHJvamVrdF9odWIvZnJvbnRlbmRcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIi9ob21lL2ZyYXBjaW8vZnJhcHBlLWJlbmNoL2FwcHMvZXJwbmV4dF9wcm9qZWt0X2h1Yi9mcm9udGVuZC92aXRlLmNvbmZpZy5qc1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vaG9tZS9mcmFwY2lvL2ZyYXBwZS1iZW5jaC9hcHBzL2VycG5leHRfcHJvamVrdF9odWIvZnJvbnRlbmQvdml0ZS5jb25maWcuanNcIjtpbXBvcnQgdnVlIGZyb20gXCJAdml0ZWpzL3BsdWdpbi12dWVcIjtcbmltcG9ydCBmcmFwcGV1aSBmcm9tIFwiZnJhcHBlLXVpL3ZpdGVcIjtcbmltcG9ydCBwYXRoIGZyb20gXCJwYXRoXCI7XG5pbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tIFwidml0ZVwiO1xuXG5leHBvcnQgZGVmYXVsdCBkZWZpbmVDb25maWcoe1xuXHRwbHVnaW5zOiBbXG5cdFx0ZnJhcHBldWkoe1xuXHRcdFx0ZnJhcHBlUHJveHk6IHRydWUsXG5cdFx0XHRsdWNpZGVJY29uczogdHJ1ZSxcblx0XHRcdGppbmphQm9vdERhdGE6IHRydWUsXG5cdFx0XHRidWlsZENvbmZpZzogZmFsc2UsXG5cdFx0fSksXG5cdFx0dnVlKCksXG5cdF0sXG5cdHNlcnZlcjoge1xuXHRcdGFsbG93ZWRIb3N0czogdHJ1ZSxcblx0fSxcblx0cmVzb2x2ZToge1xuXHRcdGFsaWFzOiB7XG5cdFx0XHR2dWU6IFwidnVlL2Rpc3QvdnVlLmVzbS1idW5kbGVyLmpzXCIsXG5cdFx0XHRcIkBcIjogcGF0aC5yZXNvbHZlKF9fZGlybmFtZSwgXCJzcmNcIiksXG5cdFx0XHRcInRhaWx3aW5kLmNvbmZpZy5qc1wiOiBwYXRoLnJlc29sdmUoX19kaXJuYW1lLCBcInRhaWx3aW5kLmNvbmZpZy5qc1wiKSxcblx0XHR9LFxuXHR9LFxuXHRidWlsZDoge1xuXHRcdG91dERpcjogYC4uL2VycG5leHRfcHJvamVrdF9odWIvcHVibGljL2Zyb250ZW5kYCxcblx0XHRlbXB0eU91dERpcjogdHJ1ZSxcblx0XHRzb3VyY2VtYXA6IHRydWUsXG5cdFx0cm9sbHVwT3B0aW9uczoge1xuXHRcdFx0aW5wdXQ6IHtcblx0XHRcdFx0bWFpbjogcGF0aC5yZXNvbHZlKF9fZGlybmFtZSwgXCJpbmRleC5odG1sXCIpLFxuXHRcdFx0fSxcblx0XHRcdG91dHB1dDoge1xuXHRcdFx0XHQvLyBVc2UgZml4ZWQgZmlsZW5hbWVzIHdpdGhvdXQgaGFzaCBmb3IgZWFzaWVyIHRlbXBsYXRlIGludGVncmF0aW9uXG5cdFx0XHRcdGVudHJ5RmlsZU5hbWVzOiBcImFzc2V0cy9bbmFtZV0uanNcIixcblx0XHRcdFx0Ly8gQ2h1bmsgZmlsZXMgbXVzdCBiZSBoYXNoZWQgdG8gYXZvaWQgbmFtZSBjb2xsaXNpb25zL2NhY2hpbmcgaXNzdWVzIChlLmcuIGZsYWcuanMsIGFyY2hpdmUuanMpXG5cdFx0XHRcdGNodW5rRmlsZU5hbWVzOiBcImFzc2V0cy9jaHVua3MvW25hbWVdLVtoYXNoXS5qc1wiLFxuXHRcdFx0XHRhc3NldEZpbGVOYW1lczogXCJhc3NldHMvW25hbWVdLltleHRdXCIsXG5cdFx0XHRcdG1hbnVhbENodW5rczoge1xuXHRcdFx0XHRcdFwiZnJhcHBlLXVpXCI6IFtcImZyYXBwZS11aVwiXSxcblx0XHRcdFx0fSxcblx0XHRcdH0sXG5cdFx0fSxcblx0fSxcblx0b3B0aW1pemVEZXBzOiB7XG5cdFx0aW5jbHVkZTogW1widGFpbHdpbmQuY29uZmlnLmpzXCJdLFxuXHR9LFxufSk7XG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQXNXLE9BQU8sU0FBUztBQUN0WCxPQUFPLGNBQWM7QUFDckIsT0FBTyxVQUFVO0FBQ2pCLFNBQVMsb0JBQW9CO0FBSDdCLElBQU0sbUNBQW1DO0FBS3pDLElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQzNCLFNBQVM7QUFBQSxJQUNSLFNBQVM7QUFBQSxNQUNSLGFBQWE7QUFBQSxNQUNiLGFBQWE7QUFBQSxNQUNiLGVBQWU7QUFBQSxNQUNmLGFBQWE7QUFBQSxJQUNkLENBQUM7QUFBQSxJQUNELElBQUk7QUFBQSxFQUNMO0FBQUEsRUFDQSxRQUFRO0FBQUEsSUFDUCxjQUFjO0FBQUEsRUFDZjtBQUFBLEVBQ0EsU0FBUztBQUFBLElBQ1IsT0FBTztBQUFBLE1BQ04sS0FBSztBQUFBLE1BQ0wsS0FBSyxLQUFLLFFBQVEsa0NBQVcsS0FBSztBQUFBLE1BQ2xDLHNCQUFzQixLQUFLLFFBQVEsa0NBQVcsb0JBQW9CO0FBQUEsSUFDbkU7QUFBQSxFQUNEO0FBQUEsRUFDQSxPQUFPO0FBQUEsSUFDTixRQUFRO0FBQUEsSUFDUixhQUFhO0FBQUEsSUFDYixXQUFXO0FBQUEsSUFDWCxlQUFlO0FBQUEsTUFDZCxPQUFPO0FBQUEsUUFDTixNQUFNLEtBQUssUUFBUSxrQ0FBVyxZQUFZO0FBQUEsTUFDM0M7QUFBQSxNQUNBLFFBQVE7QUFBQTtBQUFBLFFBRVAsZ0JBQWdCO0FBQUE7QUFBQSxRQUVoQixnQkFBZ0I7QUFBQSxRQUNoQixnQkFBZ0I7QUFBQSxRQUNoQixjQUFjO0FBQUEsVUFDYixhQUFhLENBQUMsV0FBVztBQUFBLFFBQzFCO0FBQUEsTUFDRDtBQUFBLElBQ0Q7QUFBQSxFQUNEO0FBQUEsRUFDQSxjQUFjO0FBQUEsSUFDYixTQUFTLENBQUMsb0JBQW9CO0FBQUEsRUFDL0I7QUFDRCxDQUFDOyIsCiAgIm5hbWVzIjogW10KfQo=
