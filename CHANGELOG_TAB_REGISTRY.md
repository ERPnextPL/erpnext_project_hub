# Changelog - Tab Registry System

## [Version 2.0.0] - 2026-01-09

### 🎉 Major Feature: Plugin System (Tab Registry)

#### Added

**Core System:**
- ✅ **Tab Registry** - Central registry for managing tabs (`tabRegistry.js`)
- ✅ **Core Tabs Module** - Extracted core tabs to `tabs/coreTabs.js`
- ✅ **Extension Point** - Plugin system allowing external apps to register tabs
- ✅ **Dynamic Loading** - Support for runtime tab registration

**API:**
- `registerTab(config)` - Register a new tab
- `unregisterTab(key)` - Remove a tab
- `getTabs()` - Get all tabs sorted by order
- `getNavItems()` - Get navigation items
- `getRoutes()` - Get Vue Router routes
- `getReservedSegments()` - Get reserved URL segments
- `getTab(key)` - Find tab by key
- `getTabByRouteName(name)` - Find tab by route name

**Documentation:**
- 📚 `tabs/README.md` - Complete API documentation
- 📚 `INTEGRATION_GUIDE.md` - Multiple integration approaches
- 📚 `PLUGIN_EXAMPLE.md` - Full working example
- 📚 `TAB_REGISTRY_README.md` - System overview
- 📚 `ARCHITECTURE.md` - Architecture diagrams
- 🧪 `tabs/__tests__/tabRegistry.test.js` - Unit tests

**Examples:**
- 📝 `tabs/proTabs.example.js` - Example PRO tabs implementation
- 📝 Example integration code in all documentation

#### Changed

**Breaking Changes:**
- 🔧 `router.js` - Now uses Tab Registry instead of hardcoded routes
- 🔧 `OutlinerNav.vue` - Now uses Tab Registry instead of hardcoded nav items
- 🔧 Navigation is now dynamic and extensible

**Migration Required:**
- Old hardcoded tabs removed
- All tabs must now be registered through Tab Registry
- Core tabs automatically registered via `registerCoreTabs()`

#### Removed

- ❌ Hardcoded tab routes in `router.js`
- ❌ Hardcoded navigation items in `OutlinerNav.vue`
- ❌ Direct imports of `Users` and `Clock` icons (moved to PRO example)
- ❌ Team Manager tab route (moved to PRO example)
- ❌ Time Management tab route (moved to PRO example)

#### Migration Guide

**Before (Hardcoded):**
```javascript
// router.js
const routes = [
  { path: '/project-hub', name: 'ProjectList', component: ... },
  { path: '/project-hub/my-tasks', name: 'MyTasks', component: ... },
];

// OutlinerNav.vue
const navItems = [
  { key: 'projects', to: '/project-hub', ... },
  { key: 'tasks', to: '/project-hub/my-tasks', ... },
];
```

**After (Dynamic):**
```javascript
// router.js
import { registerCoreTabs } from './tabs/coreTabs';
import { getRoutes } from './tabRegistry';

registerCoreTabs();
const routes = [...getRoutes(), /* other routes */];

// OutlinerNav.vue
import { getNavItems } from '../tabRegistry';
const navItems = getNavItems();
```

### Benefits

1. **Separation of Concerns** - Core and PRO features are cleanly separated
2. **No Code Modification** - PRO version doesn't need to modify core files
3. **Extensibility** - Any app can register custom tabs
4. **Maintainability** - Update core without affecting plugins
5. **Dynamic Loading** - Tabs can be added/removed at runtime
6. **Order Control** - Precise control over tab positioning

### Use Cases

**1. PRO Version:**
```javascript
import { registerTab } from 'erpnext_projekt_hub/tabRegistry';

registerTab({
  key: 'team',
  routeName: 'TeamManager',
  path: '/project-hub/team-manager',
  labelKey: 'Team',
  icon: Users,
  component: () => import('./pages/TeamManager.vue'),
  order: 40,
});
```

**2. Custom Extensions:**
```javascript
registerTab({
  key: 'analytics',
  routeName: 'Analytics',
  path: '/project-hub/analytics',
  labelKey: 'Analytics',
  icon: BarChart,
  component: () => import('./pages/Analytics.vue'),
  order: 60,
});
```

**3. Conditional Features:**
```javascript
if (hasFeatureFlag('advanced_reporting')) {
  registerTab({ /* ... */ });
}
```

### Technical Details

**Architecture:**
- Singleton pattern for registry
- Map-based storage for O(1) lookups
- Automatic sorting by order value
- Lazy-loaded components for performance
- Type-safe configuration (can add TypeScript)

**Performance:**
- Code splitting per tab
- Lazy loading of components
- No runtime overhead
- Efficient lookups

**Compatibility:**
- Fully backward compatible (core tabs work as before)
- Graceful fallback if plugins not available
- No breaking changes for end users

### Testing

**Unit Tests:**
- Tab registration
- Tab ordering
- Navigation items generation
- Route generation
- Reserved segments
- Lookup methods
- Initialization state

**Integration Tests:**
- Core tabs load correctly
- PRO tabs can be added
- Navigation renders correctly
- Routes work as expected

### Future Enhancements

Possible future additions:
- Tab permissions/roles
- Tab groups/categories
- Tab icons with badges
- Tab-specific permissions
- Lifecycle hooks (beforeRegister, afterRegister)
- Tab metadata (description, version)
- Hot module replacement for development

### Files Changed

**Modified:**
- `frontend/src/router.js` - Use Tab Registry
- `frontend/src/components/OutlinerNav.vue` - Use Tab Registry

**Added:**
- `frontend/src/tabRegistry.js` - Core registry
- `frontend/src/tabs/coreTabs.js` - Core tabs
- `frontend/src/tabs/proTabs.example.js` - PRO example
- `frontend/src/tabs/index.js` - Central exports
- `frontend/src/tabs/README.md` - API docs
- `frontend/src/tabs/__tests__/tabRegistry.test.js` - Tests
- `frontend/INTEGRATION_GUIDE.md` - Integration guide
- `frontend/PLUGIN_EXAMPLE.md` - Complete example
- `frontend/TAB_REGISTRY_README.md` - Overview
- `frontend/ARCHITECTURE.md` - Architecture docs
- `CHANGELOG_TAB_REGISTRY.md` - This file

### Upgrade Instructions

**For Base Version Users:**
No action required. The system works exactly as before.

**For PRO Version Developers:**

1. Create `proTabs.js` in your PRO app
2. Import and register tabs:
   ```javascript
   import { registerTab } from 'erpnext_projekt_hub/tabRegistry';
   export function registerProTabs() {
     registerTab({ /* config */ });
   }
   ```
3. Modify base app's `router.js` to load PRO tabs:
   ```javascript
   try {
     const { registerProTabs } = await import('pro/tabs/proTabs');
     registerProTabs();
   } catch (e) {}
   ```

See `INTEGRATION_GUIDE.md` for detailed instructions.

---

## Summary

This release introduces a **powerful plugin system** that enables clean separation between base and premium features, making the codebase more maintainable and extensible.

**Key Achievement:** PRO features can now be added as separate apps without modifying core code!

For questions or support, see the documentation files or open an issue.
