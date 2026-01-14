# Integration Guide for PRO Version

This guide shows how to integrate PRO tabs into the base Project Hub application.

## Quick Start

### Option 1: Simple Import (Recommended for Monorepo)

If your PRO version is in the same build system:

**In `router.js`, add after core tabs registration:**

```javascript
import { registerCoreTabs } from "./tabs/coreTabs";

// Register core tabs
registerCoreTabs();

// Register PRO tabs (if available)
if (process.env.VITE_ENABLE_PRO === 'true') {
  import('./tabs/proTabs').then(({ registerProTabs }) => {
    registerProTabs();
  });
}

tabRegistry.markInitialized();
```

### Option 2: Separate PRO App

If your PRO version is a separate Frappe app:

**Step 1:** Create PRO app structure
```
erpnext_projekt_hub_pro/
├── frontend/
│   └── src/
│       ├── tabs/
│       │   └── proTabs.js
│       └── pages/
│           ├── TeamManager.vue
│           └── TimeManagement.vue
└── hooks.py
```

**Step 2:** Create `proTabs.js` in PRO app
```javascript
// erpnext_projekt_hub_pro/frontend/src/tabs/proTabs.js
import { registerTab } from '../../../erpnext_projekt_hub/frontend/src/tabRegistry';
import { Users, Clock } from 'lucide-vue-next';

export function registerProTabs() {
  registerTab({
    key: 'team',
    routeName: 'TeamManager',
    path: '/project-hub/team-manager',
    labelKey: 'Team',
    icon: Users,
    color: 'text-purple-600',
    bg: 'bg-purple-50',
    component: () => import('../pages/TeamManager.vue'),
    order: 40,
  });

  registerTab({
    key: 'time',
    routeName: 'TimeManagement',
    path: '/project-hub/time-management',
    labelKey: 'Time',
    icon: Clock,
    color: 'text-emerald-600',
    bg: 'bg-emerald-50',
    component: () => import('../pages/TimeManagement.vue'),
    order: 50,
  });
}
```

**Step 3:** Modify base app's `router.js`
```javascript
import { registerCoreTabs } from "./tabs/coreTabs";

// Register core tabs
registerCoreTabs();

// Try to load PRO tabs
async function loadProTabs() {
  try {
    // This path will be resolved by your build tool
    const proModule = await import('erpnext_projekt_hub_pro/tabs/proTabs');
    if (proModule.registerProTabs) {
      proModule.registerProTabs();
      console.log('PRO tabs loaded successfully');
    }
  } catch (error) {
    console.log('PRO version not available, running base version');
  }
}

loadProTabs().then(() => {
  tabRegistry.markInitialized();
});
```

### Option 3: Runtime Loading via Frappe

Load PRO tabs based on Frappe system settings:

**Step 1:** Add setting in Frappe
```python
# In PRO app's hooks.py or setup
frappe.db.set_value('System Settings', None, 'enable_project_hub_pro', 1)
```

**Step 2:** Expose to frontend
```python
# In PRO app's boot.py
def boot_session(bootinfo):
    bootinfo.project_hub_pro_enabled = frappe.db.get_single_value(
        'System Settings', 'enable_project_hub_pro'
    )
```

**Step 3:** Conditional loading in `router.js`
```javascript
import { registerCoreTabs } from "./tabs/coreTabs";

registerCoreTabs();

// Check if PRO is enabled
const isProEnabled = window.frappe?.boot?.project_hub_pro_enabled;

if (isProEnabled) {
  // Load PRO tabs dynamically
  import('./tabs/proTabs').then(({ registerProTabs }) => {
    registerProTabs();
    console.log('PRO features enabled');
  });
}

tabRegistry.markInitialized();
```

### Option 4: License-Based Loading

**Create a license checker:**

```javascript
// src/utils/license.js
export function hasProLicense() {
  // Check Frappe boot info
  if (window.frappe?.boot?.has_pro_license) {
    return true;
  }

  // Or check via API
  return frappe.call({
    method: 'erpnext_projekt_hub_pro.api.check_license',
    async: false
  }).then(r => r.message);
}
```

**Use in router:**

```javascript
import { registerCoreTabs } from "./tabs/coreTabs";
import { hasProLicense } from "./utils/license";

registerCoreTabs();

hasProLicense().then(hasPro => {
  if (hasPro) {
    import('./tabs/proTabs').then(({ registerProTabs }) => {
      registerProTabs();
    });
  }
  tabRegistry.markInitialized();
});
```

## Build Configuration

### Vite Configuration for Separate PRO App

If using Vite, configure module resolution:

```javascript
// vite.config.js
export default {
  resolve: {
    alias: {
      'erpnext_projekt_hub_pro': path.resolve(
        __dirname,
        '../erpnext_projekt_hub_pro/frontend/src'
      )
    }
  }
}
```

### Webpack Configuration

```javascript
// webpack.config.js
module.exports = {
  resolve: {
    alias: {
      'erpnext_projekt_hub_pro': path.resolve(
        __dirname,
        '../erpnext_projekt_hub_pro/frontend/src'
      )
    }
  }
}
```

## Testing

### Test PRO Tabs Registration

```javascript
import { getTabs, getNavItems } from './tabRegistry';

// Check if PRO tabs are loaded
const tabs = getTabs();
console.log('Registered tabs:', tabs.map(t => t.key));
// Expected output (with PRO): ['projects', 'tasks', 'my-time', 'team', 'time']

const navItems = getNavItems();
console.log('Navigation items:', navItems.length);
// Expected: 5 items with PRO, 3 without
```

### Test Dynamic Loading

```javascript
// In browser console
import('./tabs/proTabs').then(({ registerProTabs }) => {
  registerProTabs();
  console.log('PRO tabs registered:', tabRegistry.getTabs());
});
```

## File Structure Examples

### Monorepo Structure
```
apps/
├── erpnext_projekt_hub/          # Base app
│   └── frontend/
│       └── src/
│           ├── tabRegistry.js
│           ├── router.js
│           └── tabs/
│               ├── coreTabs.js
│               └── proTabs.js    # PRO tabs in same repo
└── build/
```

### Separate Apps Structure
```
apps/
├── erpnext_projekt_hub/          # Base app
│   └── frontend/
│       └── src/
│           ├── tabRegistry.js    # Exported for use by PRO
│           ├── router.js
│           └── tabs/
│               └── coreTabs.js
│
└── erpnext_projekt_hub_pro/      # PRO app
    └── frontend/
        └── src/
            ├── tabs/
            │   └── proTabs.js    # Imports from base
            └── pages/
                ├── TeamManager.vue
                └── TimeManagement.vue
```

## Troubleshooting

### PRO tabs not showing up

1. Check browser console for errors
2. Verify PRO tabs are registered:
   ```javascript
   console.log(tabRegistry.getTabs());
   ```
3. Check if PRO module is loaded:
   ```javascript
   console.log(tabRegistry.isInitialized());
   ```

### Import errors

1. Check build tool configuration (aliases)
2. Verify file paths are correct
3. Ensure tabRegistry is exported properly

### Route conflicts

1. Ensure PRO tabs have unique `key` values
2. Check that paths don't conflict with ProjectOutliner
3. Verify `order` values are different from core tabs

## Best Practices

1. **Always set unique `order` values** - Prevents tab position conflicts
2. **Use try-catch for dynamic imports** - Graceful fallback if PRO not available
3. **Log registration** - Helps debugging in production
4. **Mark registry as initialized** - After all tabs are registered
5. **Test both versions** - Ensure base version works without PRO

## Advanced: Multiple Plugin Apps

If you have multiple apps adding tabs:

```javascript
// router.js
import { registerCoreTabs } from "./tabs/coreTabs";

registerCoreTabs();

// Load all available plugins
const plugins = [
  () => import('erpnext_projekt_hub_pro/tabs/proTabs'),
  () => import('erpnext_projekt_hub_analytics/tabs/analyticsTabs'),
  () => import('erpnext_projekt_hub_reports/tabs/reportTabs'),
];

Promise.allSettled(plugins.map(p => p()))
  .then(results => {
    results.forEach((result, index) => {
      if (result.status === 'fulfilled' && result.value.registerTabs) {
        result.value.registerTabs();
        console.log(`Plugin ${index} loaded`);
      }
    });
  })
  .finally(() => {
    tabRegistry.markInitialized();
  });
```

## Support

For issues or questions about the Tab Registry system:
1. Check the [Tab Registry README](./src/tabs/README.md)
2. Review example in `src/tabs/proTabs.example.js`
3. Check browser console for registration logs
