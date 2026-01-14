# Tab Registry - Plugin System Documentation

## Overview

The Tab Registry is an extension point system that allows external applications (like a PRO version) to register additional tabs in the Project Hub without modifying the core codebase.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Tab Registry System                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Core Tabs   │    │  PRO Tabs    │    │ Custom Tabs  │  │
│  │              │    │              │    │              │  │
│  │ • Projects   │    │ • Team Mgr   │    │ • Your Tab   │  │
│  │ • Tasks      │    │ • Time Mgmt  │    │ • ...        │  │
│  │ • My Time    │    │              │    │              │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │           │
│         └───────────────────┴───────────────────┘           │
│                             │                                │
│                    ┌────────▼────────┐                       │
│                    │  Tab Registry   │                       │
│                    │   (Singleton)   │                       │
│                    └────────┬────────┘                       │
│                             │                                │
│         ┌───────────────────┴───────────────────┐           │
│         │                                       │           │
│    ┌────▼─────┐                          ┌─────▼──────┐    │
│    │  Router  │                          │ Navigation │    │
│    │  (Vue)   │                          │ Component  │    │
│    └──────────┘                          └────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Core Files

- **`tabRegistry.js`** - Main registry singleton with API for tab management
- **`tabs/coreTabs.js`** - Registration of core (base version) tabs
- **`tabs/proTabs.example.js`** - Example of how to register PRO tabs
- **`router.js`** - Router configuration using Tab Registry
- **`components/OutlinerNav.vue`** - Navigation component using Tab Registry

## How It Works

### 1. Core Tabs Registration

Core tabs are registered in `tabs/coreTabs.js`:

```javascript
import { registerTab } from '../tabRegistry';
import { Folder } from 'lucide-vue-next';

registerTab({
  key: 'projects',
  routeName: 'ProjectList',
  path: '/project-hub',
  labelKey: 'Projects',
  icon: Folder,
  color: 'text-blue-600',
  bg: 'bg-blue-50',
  component: () => import('../pages/ProjectList.vue'),
  order: 10,
});
```

### 2. Router Integration

The router automatically uses registered tabs in `router.js`:

```javascript
import { registerCoreTabs } from "./tabs/coreTabs";

// Register core tabs
registerCoreTabs();

// Extension point for plugins
// import { registerProTabs } from 'erpnext_projekt_hub_pro/tabs/proTabs';
// registerProTabs();
```

### 3. Navigation Component

The navigation component dynamically displays all registered tabs:

```javascript
import { getNavItems } from "../tabRegistry";

const navItems = getNavItems(); // Gets all registered tabs
```

## Adding Tabs from External App (PRO Version)

### Step 1: Create Your PRO App Plugin File

In your PRO app, create a file like `erpnext_projekt_hub_pro/frontend/src/tabs/proTabs.js`:

```javascript
import { registerTab } from 'erpnext_projekt_hub/tabRegistry';
import { Users, Clock } from 'lucide-vue-next';

export function registerProTabs() {
  // Team Manager tab
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

  // Time Management tab
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

### Step 2: Import and Register in Router

Modify `router.js` to import your PRO tabs:

```javascript
import { registerCoreTabs } from "./tabs/coreTabs";

// Register core tabs
registerCoreTabs();

// Register PRO tabs (if available)
try {
  const { registerProTabs } = await import('erpnext_projekt_hub_pro/tabs/proTabs');
  registerProTabs();
} catch (e) {
  // PRO version not installed
  console.log('Running base version');
}

tabRegistry.markInitialized();
```

### Step 3: Conditional Registration Based on License

You can also register tabs conditionally:

```javascript
export function registerProTabsConditional() {
  const hasPROLicense = window.frappe?.boot?.has_pro_license || false;

  if (hasPROLicense) {
    registerTab({
      key: 'team',
      // ... tab config
    });
  }
}
```

## Tab Configuration Options

```javascript
{
  key: string,              // Unique identifier (required)
  routeName: string,        // Vue Router route name (required)
  path: string,             // URL path (required)
  labelKey: string,         // Translation key for label (required)
  icon: Component,          // Lucide icon component (required)
  color: string,            // Tailwind color class for active state (required)
  bg: string,               // Tailwind background class for active state (required)
  component: Function,      // Lazy-loaded Vue component (required)
  order: number,            // Sort order (optional, default: 50)
}
```

## Tab Registry API

### Registration Methods

- `registerTab(tabConfig)` - Register a new tab
- `unregisterTab(key)` - Unregister a tab by key
- `markInitialized()` - Mark registry as initialized

### Query Methods

- `getTabs()` - Get all tabs sorted by order
- `getNavItems()` - Get navigation items for UI
- `getRoutes()` - Get Vue Router route configurations
- `getReservedSegments()` - Get reserved URL segments
- `getTab(key)` - Get tab by key
- `getTabByRouteName(routeName)` - Get tab by route name
- `isInitialized()` - Check if registry is initialized

## Benefits of This Approach

1. **Separation of Concerns** - Core and PRO features are separated
2. **No Code Modification** - PRO version doesn't modify core files
3. **Dynamic Loading** - Tabs can be added/removed at runtime
4. **Maintainability** - Easy to update core without affecting plugins
5. **Extensibility** - Any app can add custom tabs
6. **Order Control** - Tabs can be positioned using the `order` field

## Example: Adding a Custom Tab

```javascript
import { registerTab } from 'erpnext_projekt_hub/tabRegistry';
import { BarChart } from 'lucide-vue-next';

registerTab({
  key: 'analytics',
  routeName: 'Analytics',
  path: '/project-hub/analytics',
  labelKey: 'Analytics',
  icon: BarChart,
  color: 'text-green-600',
  bg: 'bg-green-50',
  component: () => import('./pages/Analytics.vue'),
  order: 60, // Will appear after all core tabs
});
```

## Migration from Hardcoded Tabs

The old approach had hardcoded tabs:
```javascript
const navItems = [
  { key: 'projects', to: '/project-hub', ... },
  { key: 'tasks', to: '/project-hub/my-tasks', ... },
];
```

New approach uses dynamic registry:
```javascript
const navItems = getNavItems(); // Gets all registered tabs
```

This allows PRO tabs to be added without modifying the core code!
