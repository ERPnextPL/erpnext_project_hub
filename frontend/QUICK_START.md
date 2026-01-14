# Quick Start Guide - Tab Registry Plugin System

Get up and running with the Tab Registry system in 5 minutes!

## 🎯 What is Tab Registry?

A plugin system that lets you add custom tabs to Project Hub without modifying core code. Perfect for:
- Creating a PRO version with extra features
- Adding custom integrations
- Building industry-specific extensions

## 🚀 For Base Version Users

**Good news:** Nothing changes for you! The system works exactly as before:

```
✓ Projects tab - works
✓ Tasks tab - works
✓ My Time tab - works
```

Just rebuild your frontend and you're done:

```bash
cd frontend
npm install
npm run build
```

## 💎 For PRO Version Developers

### Step 1: Create Your PRO Tab File

Create `erpnext_projekt_hub_pro/frontend/src/tabs/proTabs.js`:

```javascript
import { registerTab } from '../../../../erpnext_projekt_hub/frontend/src/tabRegistry';
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

### Step 2: Create Your Tab Components

Create the Vue components referenced above:

**`TeamManager.vue`:**
```vue
<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold">Team Manager</h1>
    <p>Manage your team here!</p>
  </div>
</template>
```

**`TimeManagement.vue`:**
```vue
<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold">Time Management</h1>
    <p>Track time here!</p>
  </div>
</template>
```

### Step 3: Load PRO Tabs in Base App

Modify `erpnext_projekt_hub/frontend/src/router.js`:

Find this section:
```javascript
// Extension point: PRO version or other plugins can register additional tabs here
// Example:
// import { registerProTabs } from 'erpnext_projekt_hub_pro/tabs/proTabs';
// registerProTabs();
```

Uncomment and modify to:
```javascript
// Load PRO tabs if available
try {
  const { registerProTabs } = await import('../../../erpnext_projekt_hub_pro/frontend/src/tabs/proTabs');
  registerProTabs();
  console.log('✓ PRO tabs loaded');
} catch (error) {
  console.log('ℹ Base version only');
}
```

### Step 4: Configure Build Tool (Vite)

Add alias in `vite.config.js`:

```javascript
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      'erpnext_projekt_hub_pro': path.resolve(
        __dirname,
        '../../erpnext_projekt_hub_pro/frontend/src'
      ),
    },
  },
});
```

### Step 5: Build and Test

```bash
# Build PRO app
cd apps/erpnext_projekt_hub_pro/frontend
npm install
npm run build

# Build base app
cd ../../erpnext_projekt_hub/frontend
npm run build

# Or use bench
cd ../../../..
bench build
```

### Step 6: Verify

Open `/project-hub` in browser. You should see 5 tabs:

```
[📁] [✓] [⏱] [👥] [🕐]
Projects Tasks My Time Team Time
```

Check browser console:
```
✓ PRO tabs loaded
```

Done! 🎉

## 🔧 Configuration Options

### Tab Configuration

```javascript
{
  key: 'unique-id',           // Required: Unique key
  routeName: 'RouteName',     // Required: Vue Router name
  path: '/project-hub/path',  // Required: URL path
  labelKey: 'Label',          // Required: Display label
  icon: IconComponent,        // Required: Lucide icon
  color: 'text-color-600',    // Required: Active text color
  bg: 'bg-color-50',         // Required: Active background
  component: () => import(), // Required: Component
  order: 40,                 // Optional: Position (default: 50)
}
```

### Order Values

Control tab position with `order`:

```
10 - Projects (core)
20 - Tasks (core)
30 - My Time (core)
40 - Your first PRO tab
50 - Your second PRO tab
60 - Your third PRO tab
...
```

Lower numbers appear first.

## 🧪 Testing

### Quick Test

Open browser console on `/project-hub`:

```javascript
// Check registered tabs
import { getTabs } from './tabRegistry';
console.log(getTabs().map(t => t.key));

// Expected with PRO:
// ['projects', 'tasks', 'my-time', 'team', 'time']
```

### Visual Test

1. Navigate to `/project-hub`
2. See 5 tabs in navigation
3. Click each tab - should navigate correctly
4. Active tab should highlight

## 🐛 Troubleshooting

### PRO tabs not showing

**Check console for errors:**
```javascript
// In browser console
console.log(tabRegistry.getTabs());
```

**Verify PRO tabs registered:**
Should see `'team'` and `'time'` in the list.

**Check module loading:**
Look for "✓ PRO tabs loaded" in console. If you see "ℹ Base version only", check:
- File paths in import statement
- Vite alias configuration
- PRO app is in correct location

### Import errors

**Check alias configuration in `vite.config.js`:**
```javascript
resolve: {
  alias: {
    'erpnext_projekt_hub_pro': path.resolve(...)
  }
}
```

**Verify relative paths:**
```javascript
// Adjust based on your directory structure
'../../../../erpnext_projekt_hub/frontend/src/tabRegistry'
```

### Icons not rendering

**Ensure Lucide icons are installed:**
```bash
npm install lucide-vue-next
```

**Import correctly:**
```javascript
import { Users, Clock } from 'lucide-vue-next';
```

## 📚 Learn More

- **[TAB_REGISTRY_README.md](TAB_REGISTRY_README.md)** - System overview
- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - Integration methods
- **[PLUGIN_EXAMPLE.md](PLUGIN_EXAMPLE.md)** - Complete example
- **[tabs/README.md](src/tabs/README.md)** - API reference
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Architecture diagrams

## 🎓 Next Steps

### Add License Checking

```javascript
export async function registerProTabsIfLicensed() {
  const hasLicense = await frappe.call({
    method: 'check_license',
  });

  if (hasLicense.message) {
    registerProTabs();
  }
}
```

### Add Backend API

Create API endpoints for your PRO tabs:

```python
# erpnext_projekt_hub_pro/api.py
@frappe.whitelist()
def get_team_members():
    return frappe.get_all('User', ...)
```

### Add Permissions

Control who sees PRO tabs:

```javascript
if (frappe.user.has_role('Team Manager')) {
  registerTab({ key: 'team', ... });
}
```

## 💡 Tips

1. **Use order increments of 10** - Leaves room for future tabs
2. **Test without PRO** - Ensure base version still works
3. **Log registration** - Helps debugging in production
4. **Lazy load components** - Better performance
5. **Handle errors gracefully** - Don't break if PRO not available

## ✅ Checklist

Before deploying:

- [ ] PRO tabs render correctly
- [ ] Navigation works
- [ ] Icons display properly
- [ ] Active state highlights correctly
- [ ] Base version works without PRO
- [ ] No console errors
- [ ] Build succeeds
- [ ] Routes work correctly
- [ ] Components load

## 🎉 Success!

You now have a working plugin system! Your PRO tabs are cleanly separated from core code and can be deployed independently.

**Questions?** Check the documentation or open an issue.

---

**Total setup time:** ~5 minutes ⚡
