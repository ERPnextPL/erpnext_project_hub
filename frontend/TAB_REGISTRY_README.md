# Tab Registry Plugin System

## Overview

The Tab Registry is an **extension point system** that enables external applications (such as a PRO version) to dynamically register additional tabs in the Project Hub **without modifying the core codebase**.

This architecture provides clean separation between base and premium features, making it easy to maintain both versions independently.

## 🎯 Key Benefits

- ✅ **No Core Modifications** - PRO features don't touch base code
- ✅ **Dynamic Loading** - Tabs can be added/removed at runtime
- ✅ **Clean Separation** - Base and PRO versions are independent
- ✅ **Extensible** - Any app can register custom tabs
- ✅ **Maintainable** - Update base without affecting plugins
- ✅ **Order Control** - Tabs can be positioned precisely

## 📁 File Structure

```
frontend/src/
├── tabRegistry.js              # Core registry singleton
├── tabs/
│   ├── README.md              # Detailed API documentation
│   ├── coreTabs.js            # Base version tabs
│   ├── proTabs.example.js     # Example PRO implementation
│   └── __tests__/
│       └── tabRegistry.test.js
├── router.js                  # Router using registry
├── components/
│   └── OutlinerNav.vue       # Navigation using registry
├── INTEGRATION_GUIDE.md      # Integration instructions
├── PLUGIN_EXAMPLE.md         # Complete working example
└── TAB_REGISTRY_README.md    # This file
```

## 🚀 Quick Start

### For Base Version Users

No changes needed! The base version works exactly as before with these tabs:
- Projects
- Tasks
- My Time

### For PRO Version Developers

**1. Create your PRO tabs file:**

```javascript
// erpnext_projekt_hub_pro/frontend/src/tabs/proTabs.js
import { registerTab } from 'erpnext_projekt_hub/tabRegistry';
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
}
```

**2. Register in router.js:**

```javascript
// In base app's router.js
import { registerCoreTabs } from "./tabs/coreTabs";

registerCoreTabs();

// Load PRO tabs if available
try {
  const { registerProTabs } = await import('erpnext_projekt_hub_pro/tabs/proTabs');
  registerProTabs();
} catch (e) {
  console.log('Base version only');
}
```

That's it! Your PRO tabs will automatically appear in the navigation.

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [tabs/README.md](src/tabs/README.md) | Complete API reference and architecture |
| [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) | Multiple integration approaches |
| [PLUGIN_EXAMPLE.md](PLUGIN_EXAMPLE.md) | Full working example with code |

## 🔧 Tab Configuration

Each tab requires:

```javascript
{
  key: 'unique-key',           // Unique identifier
  routeName: 'RouteName',      // Vue Router name
  path: '/project-hub/path',   // URL path
  labelKey: 'Label',           // Translation key
  icon: IconComponent,         // Lucide icon
  color: 'text-blue-600',      // Active color
  bg: 'bg-blue-50',           // Active background
  component: () => import(),   // Lazy-loaded component
  order: 40,                   // Position (optional, default: 50)
}
```

## 🎨 Tab Order System

Tabs are sorted by `order` value (lower = earlier):

```
Order 10: Projects       (core)
Order 20: Tasks          (core)
Order 30: My Time        (core)
Order 40: Team Manager   (PRO)
Order 50: Time Mgmt      (PRO)
Order 60: Your Tab       (custom)
```

## 🧪 Testing

### Visual Test

1. Navigate to `/project-hub`
2. Check navigation bar shows all tabs
3. Click each tab - should navigate correctly
4. Active tab should be highlighted

### Console Test

```javascript
import { getTabs } from './tabRegistry';

// Check registered tabs
console.log(getTabs());

// Expected output with PRO:
// [
//   { key: 'projects', order: 10, ... },
//   { key: 'tasks', order: 20, ... },
//   { key: 'my-time', order: 30, ... },
//   { key: 'team', order: 40, ... },
//   { key: 'time', order: 50, ... }
// ]
```

### Unit Tests

```bash
cd frontend
npm test
```

## 🔌 Integration Methods

### Method 1: Static Import (Simple)

```javascript
import { registerProTabs } from './tabs/proTabs';
registerProTabs();
```

### Method 2: Dynamic Import (Recommended)

```javascript
try {
  const { registerProTabs } = await import('erpnext_projekt_hub_pro/tabs/proTabs');
  registerProTabs();
} catch (e) {
  // PRO not installed
}
```

### Method 3: License-Based

```javascript
if (window.frappe?.boot?.has_pro_license) {
  const { registerProTabs } = await import('./tabs/proTabs');
  registerProTabs();
}
```

### Method 4: Multi-Plugin

```javascript
const plugins = [
  () => import('app1/tabs'),
  () => import('app2/tabs'),
  () => import('app3/tabs'),
];

await Promise.allSettled(plugins.map(p => p().then(m => m.registerTabs())));
```

## 📖 API Reference

### Core Functions

```javascript
import {
  registerTab,          // Register a new tab
  unregisterTab,        // Remove a tab
  getTabs,              // Get all tabs
  getNavItems,          // Get navigation items
  getRoutes,            // Get router routes
  getReservedSegments,  // Get reserved URL segments
  getTab,               // Get tab by key
  getTabByRouteName,    // Get tab by route name
} from './tabRegistry';
```

### Registry Methods

```javascript
import tabRegistry from './tabRegistry';

tabRegistry.registerTab(config);
tabRegistry.unregisterTab('key');
tabRegistry.markInitialized();
tabRegistry.isInitialized();
tabRegistry.reset(); // Testing only
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         External Apps/Plugins           │
│  (PRO, Analytics, Reports, Custom)      │
└───────────────┬─────────────────────────┘
                │ registerTab()
                ▼
┌─────────────────────────────────────────┐
│          Tab Registry                   │
│          (Singleton)                    │
│                                         │
│  • Stores all tab configurations       │
│  • Sorts by order                      │
│  • Provides query methods              │
└───────────────┬─────────────────────────┘
                │
        ┌───────┴───────┐
        ▼               ▼
┌──────────────┐  ┌──────────────┐
│   Router     │  │  Navigation  │
│   (Vue)      │  │  Component   │
│              │  │              │
│ getRoutes()  │  │ getNavItems()│
└──────────────┘  └──────────────┘
```

## 🎯 Use Cases

### 1. PRO Version Features

Add premium tabs without forking the base code:
- Team Manager
- Time Management
- Advanced Analytics
- Reporting Dashboard

### 2. Industry-Specific Extensions

Create industry-specific tabs:
- Construction: Site Manager
- Agency: Client Portal
- Manufacturing: Production Dashboard

### 3. Custom Integrations

Integrate third-party services:
- Slack Integration Tab
- GitHub Projects Tab
- Jira Sync Tab

### 4. A/B Testing

Test new features with subsets of users:
```javascript
if (isInExperimentGroup()) {
  registerTab({ key: 'new-feature', ... });
}
```

## 🐛 Troubleshooting

### Tabs Not Showing

1. Check console for errors
2. Verify tab registration: `console.log(tabRegistry.getTabs())`
3. Check registry initialization: `console.log(tabRegistry.isInitialized())`
4. Ensure `order` values are unique

### Route Conflicts

1. Check reserved segments: `console.log(tabRegistry.getReservedSegments())`
2. Ensure paths don't conflict with `/:projectId`
3. Verify route names are unique

### Import Errors

1. Check build tool alias configuration
2. Verify file paths are correct
3. Ensure tabRegistry is properly exported

### Icon Not Rendering

1. Ensure icon is imported from `lucide-vue-next`
2. Check component is a valid Vue component
3. Verify icon is passed as component, not string

## 🔒 Best Practices

1. **Unique Keys** - Use descriptive, unique tab keys
2. **Consistent Ordering** - Use increments of 10 for order values
3. **Error Handling** - Wrap dynamic imports in try-catch
4. **Logging** - Log registration for debugging
5. **Documentation** - Document custom tabs in your app
6. **Testing** - Test with and without plugins
7. **Lazy Loading** - Always use `() => import()` for components

## 📝 Migration from Hardcoded Tabs

### Before (Hardcoded):

```javascript
const navItems = [
  { key: 'projects', to: '/project-hub', ... },
  { key: 'tasks', to: '/project-hub/my-tasks', ... },
];
```

### After (Dynamic):

```javascript
import { getNavItems } from './tabRegistry';
const navItems = getNavItems();
```

Benefits: External apps can now add tabs!

## 🤝 Contributing

When adding tabs to the registry:

1. Use meaningful `key` and `routeName` values
2. Set appropriate `order` value (multiples of 10)
3. Provide translations for `labelKey`
4. Use Lucide icons for consistency
5. Test with and without your plugin
6. Document your tabs

## 📄 License

Same as base ERPNext Projekt Hub application.

## 🔗 Related Documentation

- [Tab Registry API](src/tabs/README.md)
- [Integration Guide](INTEGRATION_GUIDE.md)
- [Plugin Example](PLUGIN_EXAMPLE.md)
- [Test Suite](src/tabs/__tests__/tabRegistry.test.js)

## 💡 Examples

See [PLUGIN_EXAMPLE.md](PLUGIN_EXAMPLE.md) for a complete, production-ready example including:

- PRO app structure
- Frontend components
- Backend API
- License checking
- Build configuration
- Deployment steps

---

**Questions or issues?** Check the documentation or create an issue in the repository.
