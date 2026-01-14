# Tab Registry - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PLUGIN ECOSYSTEM                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │
│  │   Core Tabs    │  │   PRO Tabs     │  │  Custom Tabs   │        │
│  │  (Built-in)    │  │ (External App) │  │ (Third-party)  │        │
│  ├────────────────┤  ├────────────────┤  ├────────────────┤        │
│  │ • Projects     │  │ • Team Manager │  │ • Analytics    │        │
│  │ • Tasks        │  │ • Time Mgmt    │  │ • Reports      │        │
│  │ • My Time      │  │                │  │ • Custom...    │        │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘        │
│           │                   │                   │                 │
│           │  registerTab()    │  registerTab()    │  registerTab()  │
│           └───────────────────┴───────────────────┘                 │
│                               │                                      │
└───────────────────────────────┼──────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         TAB REGISTRY                                 │
│                         (Singleton)                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Storage:                                                            │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ Map<key, TabConfig>                                       │      │
│  │                                                            │      │
│  │ 'projects'  → { key, routeName, path, icon, order: 10 }  │      │
│  │ 'tasks'     → { key, routeName, path, icon, order: 20 }  │      │
│  │ 'my-time'   → { key, routeName, path, icon, order: 30 }  │      │
│  │ 'team'      → { key, routeName, path, icon, order: 40 }  │      │
│  │ 'time'      → { key, routeName, path, icon, order: 50 }  │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                       │
│  API:                                                                │
│  • registerTab(config)    - Add tab                                 │
│  • unregisterTab(key)     - Remove tab                              │
│  • getTabs()              - Get all tabs (sorted)                   │
│  • getNavItems()          - Get nav data                            │
│  • getRoutes()            - Get router config                       │
│  • getReservedSegments()  - Get URL segments                        │
│  • getTab(key)            - Find by key                             │
│  • getTabByRouteName(name) - Find by route                          │
│                                                                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│      VUE ROUTER           │   │   NAVIGATION COMPONENT    │
│                           │   │                           │
│ Consumes:                 │   │ Consumes:                 │
│ • getRoutes()             │   │ • getNavItems()           │
│ • getReservedSegments()   │   │ • getTabByRouteName()     │
│                           │   │                           │
│ Generates:                │   │ Renders:                  │
│ ┌─────────────────────┐   │   │ ┌─────────────────────┐   │
│ │ /project-hub        │   │   │ │ [📁] [✓] [⏱] ...   │   │
│ │ /project-hub/tasks  │   │   │ │                     │   │
│ │ /project-hub/team   │   │   │ │ Projects Tasks Time │   │
│ │ ...                 │   │   │ └─────────────────────┘   │
│ └─────────────────────┘   │   │                           │
└───────────────────────────┘   └───────────────────────────┘
```

## Data Flow

### 1. Registration Phase (App Initialization)

```
┌──────────────┐
│ App Startup  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────┐
│ router.js                    │
│                              │
│ 1. Import Tab Registry       │
│ 2. registerCoreTabs()        │ ───┐
│ 3. (optional) registerProTabs()│  │
│ 4. tabRegistry.markInit()    │   │
└──────┬───────────────────────┘   │
       │                           │
       │                           ▼
       │               ┌─────────────────────┐
       │               │  Tab Registry       │
       │               │  • Stores configs   │
       │               │  • Sorts by order   │
       │               └─────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Create Vue Router            │
│ • getRoutes()                │
│ • getReservedSegments()      │
└──────────────────────────────┘
```

### 2. Navigation Phase (User Interaction)

```
┌────────────────┐
│ User clicks    │
│ tab button     │
└────────┬───────┘
         │
         ▼
┌────────────────────────────┐
│ OutlinerNav.vue            │
│                            │
│ 1. navItems (from registry)│
│ 2. activeKey (computed)    │
│ 3. Route to path           │
└────────┬───────────────────┘
         │
         ▼
┌────────────────────────────┐
│ Vue Router                 │
│ • Match route              │
│ • Load component           │
│ • Update URL               │
└────────┬───────────────────┘
         │
         ▼
┌────────────────────────────┐
│ Tab Component Renders      │
│ (e.g., TeamManager.vue)    │
└────────────────────────────┘
```

### 3. Plugin Loading (Dynamic)

```
┌──────────────────────┐
│ Check if PRO exists  │
└──────────┬───────────┘
           │
           ▼
    ┌──────────────┐
    │   Exists?    │
    └──┬────────┬──┘
       │        │
    Yes│        │No
       │        │
       ▼        ▼
┌──────────┐  ┌──────────────┐
│ Load PRO │  │ Continue     │
│ tabs     │  │ with core    │
└──────────┘  │ only         │
       │      └──────────────┘
       │
       ▼
┌──────────────────────┐
│ registerProTabs()    │
│ • Adds to registry   │
│ • Re-sorts tabs      │
└──────────────────────┘
```

## Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                        App.vue                               │
│                    (Root Component)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    <RouterView>                              │
│              (Renders active route)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│ ProjectList  │ │ MyTasks  │ │ TeamManager  │
│              │ │          │ │   (PRO)      │
│ Includes:    │ └──────────┘ └──────────────┘
│ ┌──────────┐ │
│ │Outliner  │ │
│ │Nav       │ │
│ └──────────┘ │
└──────────────┘
```

## Registry State Management

```
┌─────────────────────────────────────────────┐
│           Tab Registry State                 │
├─────────────────────────────────────────────┤
│                                              │
│  tabs: Map {                                │
│    'projects' => {                          │
│      key: 'projects',                       │
│      routeName: 'ProjectList',              │
│      path: '/project-hub',                  │
│      labelKey: 'Projects',                  │
│      icon: FolderIcon,                      │
│      color: 'text-blue-600',                │
│      bg: 'bg-blue-50',                      │
│      component: Function,                   │
│      order: 10                              │
│    },                                        │
│    'tasks' => { ... },                      │
│    'my-time' => { ... },                    │
│    'team' => { ... },     // PRO            │
│    'time' => { ... }      // PRO            │
│  }                                           │
│                                              │
│  initialized: true                          │
│                                              │
└─────────────────────────────────────────────┘
```

## File Dependencies

```
tabRegistry.js
    │
    ├─── Used by ───┬─── router.js
    │               │      │
    │               │      └─── imports coreTabs.js
    │               │      │
    │               │      └─── imports proTabs.js (optional)
    │               │
    │               └─── OutlinerNav.vue
    │                      │
    │                      └─── Uses getNavItems()
    │                      └─── Uses getTabByRouteName()
    │
    └─── Imported by ──── coreTabs.js
                      └─── proTabs.js (PRO app)
                      └─── customTabs.js (third-party)
```

## Tab Configuration Schema

```typescript
interface TabConfig {
  // Required fields
  key: string;              // Unique identifier
  routeName: string;        // Vue Router route name
  path: string;             // URL path
  labelKey: string;         // Translation key
  icon: Component;          // Icon component
  color: string;            // Active text color (Tailwind)
  bg: string;               // Active background (Tailwind)
  component: () => Promise; // Lazy-loaded component

  // Optional fields
  order?: number;           // Sort order (default: 50)
}

interface NavigationItem {
  key: string;
  to: string;
  labelKey: string;
  icon: Component;
  color: string;
  bg: string;
}

interface RouteConfig {
  path: string;
  name: string;
  component: () => Promise;
}
```

## Extension Points

```
┌────────────────────────────────────────────────┐
│          Base App (Core)                       │
│                                                 │
│  router.js ──────────┐                         │
│      │               │ Extension Point 1:      │
│      │               │ Dynamic Import          │
│      │               │                         │
│      │  // import({ registerProTabs })         │
│      │  // registerProTabs()                   │
│      │               │                         │
│      └───────────────┘                         │
│                                                 │
└────────────────────────────────────────────────┘
                    │
                    │ Calls API
                    │
                    ▼
┌────────────────────────────────────────────────┐
│         Tab Registry (API)                     │
│                                                 │
│  registerTab()  ◄─────────────────┐            │
│                                    │            │
└────────────────────────────────────┼───────────┘
                                     │
                                     │
┌────────────────────────────────────┼───────────┐
│         PRO App (Plugin)           │           │
│                                    │           │
│  proTabs.js ───────────────────────┘           │
│      │                                          │
│      │ registerTab({                           │
│      │   key: 'team',                          │
│      │   ...                                   │
│      │ })                                      │
│                                                 │
└────────────────────────────────────────────────┘
```

## Lifecycle

```
1. App Initialization
   └─> Import tabRegistry
   └─> Import coreTabs
   └─> registerCoreTabs() calls registerTab() for each core tab
   └─> [Optional] Import proTabs
   └─> [Optional] registerProTabs() calls registerTab() for each PRO tab
   └─> markInitialized()

2. Router Creation
   └─> getRoutes() - get all registered routes
   └─> getReservedSegments() - get reserved URL segments
   └─> Create Vue Router with routes

3. Component Mounting
   └─> OutlinerNav mounts
   └─> getNavItems() - get navigation data
   └─> Render tab buttons

4. User Navigation
   └─> User clicks tab
   └─> Router navigates to path
   └─> Route component loads
   └─> activeKey computed updates
   └─> Active tab highlights

5. Runtime Plugin Loading (Optional)
   └─> Check license/feature flag
   └─> Dynamically import plugin
   └─> registerTabs()
   └─> Router automatically picks up new routes
   └─> Navigation automatically shows new tabs
```

## Security Considerations

```
┌────────────────────────────────────┐
│      License Check Layer           │
│                                     │
│  Before registerProTabs():         │
│  • Check Frappe license             │
│  • Verify user permissions         │
│  • Validate app installation       │
│                                     │
└─────────────┬──────────────────────┘
              │
              ▼ Only if authorized
┌────────────────────────────────────┐
│      Tab Registration              │
│                                     │
│  registerTab() adds PRO tabs       │
│                                     │
└────────────────────────────────────┘
```

## Performance Optimization

```
┌──────────────────────────────────────┐
│   Lazy Loading Strategy              │
│                                       │
│   Tab Component:                     │
│   component: () => import('./Tab')   │
│                                       │
│   ✓ Only loads when route accessed   │
│   ✓ Code splitting per tab          │
│   ✓ Smaller initial bundle           │
│                                       │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│   Registry Optimization              │
│                                       │
│   • Map for O(1) lookups             │
│   • Sorted once on getTabs()         │
│   • Cached navigation items          │
│   • No re-computation on render      │
│                                       │
└──────────────────────────────────────┘
```

## Error Handling

```
┌────────────────────────────────┐
│   Dynamic Import Failure       │
│                                 │
│   try {                        │
│     import('pro/tabs')         │
│   } catch (error) {            │
│     // Graceful fallback       │
│     console.log('Base only')   │
│   }                            │
│                                 │
│   ✓ App continues to work      │
│   ✓ Base tabs still available  │
│                                 │
└────────────────────────────────┘

┌────────────────────────────────┐
│   Invalid Tab Configuration    │
│                                 │
│   if (!config.key) {           │
│     console.error(...)         │
│     return; // Skip tab        │
│   }                            │
│                                 │
│   ✓ Prevents registry corruption│
│   ✓ Logs helpful error         │
│                                 │
└────────────────────────────────┘
```

---

This architecture provides a **robust, extensible, and maintainable** solution for plugin-based tab management in Project Hub.
