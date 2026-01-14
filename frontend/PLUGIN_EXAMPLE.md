# Plugin System - Practical Example

This document shows a complete, working example of how to create a PRO version app that adds tabs to Project Hub.

## Complete Example: Creating a PRO App

### Step 1: Create the PRO App Structure

```bash
cd frappe-bench/apps
bench new-app erpnext_projekt_hub_pro
```

### Step 2: Set Up Frontend Structure

```
erpnext_projekt_hub_pro/
├── frontend/
│   ├── package.json
│   └── src/
│       ├── main.js
│       ├── tabs/
│       │   └── proTabs.js
│       └── pages/
│           ├── TeamManager.vue
│           └── TimeManagement.vue
├── hooks.py
└── setup.py
```

### Step 3: Create `proTabs.js`

**File: `erpnext_projekt_hub_pro/frontend/src/tabs/proTabs.js`**

```javascript
// Import the registry from the base app
import tabRegistry, { registerTab } from '../../../../erpnext_projekt_hub/frontend/src/tabRegistry';
import { Users, Clock } from 'lucide-vue-next';

/**
 * Register PRO tabs
 * This function should be called AFTER core tabs are registered
 * but BEFORE the router is initialized
 */
export function registerProTabs() {
	console.log('Registering PRO tabs...');

	// Team Manager Tab
	registerTab({
		key: 'team',
		routeName: 'TeamManager',
		path: '/project-hub/team-manager',
		labelKey: 'Team',
		icon: Users,
		color: 'text-purple-600',
		bg: 'bg-purple-50',
		component: () => import('../pages/TeamManager.vue'),
		order: 40, // After My Time (30), before Time Management (50)
	});

	// Time Management Tab
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

	console.log('PRO tabs registered:', tabRegistry.getTabs().map(t => t.key));
}

/**
 * Conditional registration based on license check
 */
export async function registerProTabsIfLicensed() {
	try {
		// Check license via Frappe API
		const response = await frappe.call({
			method: 'erpnext_projekt_hub_pro.api.check_license',
			args: {}
		});

		if (response.message && response.message.has_license) {
			registerProTabs();
			return true;
		} else {
			console.log('No PRO license found');
			return false;
		}
	} catch (error) {
		console.error('Error checking PRO license:', error);
		return false;
	}
}
```

### Step 4: Create Team Manager Page

**File: `erpnext_projekt_hub_pro/frontend/src/pages/TeamManager.vue`**

```vue
<template>
  <div class="team-manager">
    <div class="page-header">
      <h1>Team Manager</h1>
      <p class="text-gray-600">Manage your team and assignments</p>
    </div>

    <div class="team-content">
      <!-- Your team management UI here -->
      <div class="team-grid">
        <div v-for="member in teamMembers" :key="member.name" class="team-card">
          <div class="member-avatar">
            {{ member.initials }}
          </div>
          <h3>{{ member.full_name }}</h3>
          <p class="role">{{ member.role }}</p>
          <div class="stats">
            <div class="stat">
              <span class="label">Active Tasks</span>
              <span class="value">{{ member.active_tasks }}</span>
            </div>
            <div class="stat">
              <span class="label">Workload</span>
              <span class="value">{{ member.workload }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const teamMembers = ref([]);

onMounted(async () => {
  // Fetch team data
  const response = await frappe.call({
    method: 'erpnext_projekt_hub_pro.api.get_team_members',
    args: {}
  });

  teamMembers.value = response.message || [];
});
</script>

<style scoped>
.team-manager {
  padding: 2rem;
}

.page-header {
  margin-bottom: 2rem;
}

.team-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.team-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.member-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 1rem;
}

.stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 1rem;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat .label {
  font-size: 0.75rem;
  color: #6b7280;
  text-transform: uppercase;
}

.stat .value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #1f2937;
}
</style>
```

### Step 5: Update Base App's Router

**File: `erpnext_projekt_hub/frontend/src/router.js`**

Modify the router to load PRO tabs dynamically:

```javascript
import { createRouter, createWebHistory } from "vue-router";
import tabRegistry, { getRoutes, getReservedSegments } from "./tabRegistry";
import { registerCoreTabs } from "./tabs/coreTabs";

// Register core tabs first
registerCoreTabs();

// Try to load PRO tabs if available
async function loadPlugins() {
  const plugins = [];

  // Try to load PRO tabs
  try {
    const proModule = await import('../../../erpnext_projekt_hub_pro/frontend/src/tabs/proTabs');
    if (proModule.registerProTabs) {
      plugins.push(proModule.registerProTabs());
      console.log('✓ PRO tabs loaded');
    }
  } catch (error) {
    console.log('ℹ PRO version not available');
  }

  // Wait for all plugins to load
  await Promise.all(plugins);

  // Mark registry as ready
  tabRegistry.markInitialized();
}

// Load plugins before creating router
await loadPlugins();

// Get routes from registry
const tabRoutes = getRoutes();
const RESERVED_PROJECT_SEGMENTS = getReservedSegments();

const routes = [
  ...tabRoutes,
  {
    path: "/project-hub/:projectId",
    name: "ProjectOutliner",
    component: () => import("./pages/ProjectOutliner.vue"),
    props: true,
    beforeEnter(to) {
      const segment = to.params.projectId;
      if (typeof segment !== "string") return;
      if (RESERVED_PROJECT_SEGMENTS[segment]) {
        return { name: RESERVED_PROJECT_SEGMENTS[segment] };
      }
    },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
```

### Step 6: Configure Build Tool

**For Vite (Recommended):**

**File: `erpnext_projekt_hub/frontend/vite.config.js`**

```javascript
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      'erpnext_projekt_hub_pro': path.resolve(
        __dirname,
        '../../erpnext_projekt_hub_pro/frontend/src'
      ),
    },
  },
  build: {
    rollupOptions: {
      // Handle missing PRO app gracefully
      external: (id) => {
        if (id.includes('erpnext_projekt_hub_pro')) {
          try {
            require.resolve(id);
            return false;
          } catch {
            return true;
          }
        }
        return false;
      },
    },
  },
});
```

### Step 7: Create Backend License Check

**File: `erpnext_projekt_hub_pro/erpnext_projekt_hub_pro/api.py`**

```python
import frappe

@frappe.whitelist()
def check_license():
    """Check if user has PRO license"""
    # Implement your license checking logic
    # This is a simple example

    has_license = frappe.db.get_single_value(
        'System Settings',
        'projekt_hub_pro_enabled'
    )

    return {
        'has_license': bool(has_license)
    }

@frappe.whitelist()
def get_team_members():
    """Get team members for Team Manager tab"""
    members = frappe.get_all(
        'User',
        filters={'enabled': 1},
        fields=['name', 'full_name', 'email', 'user_image']
    )

    # Add stats for each member
    for member in members:
        member['active_tasks'] = frappe.db.count(
            'Task',
            filters={
                'assigned_to': member['name'],
                'status': ['!=', 'Completed']
            }
        )
        member['initials'] = ''.join([
            n[0].upper()
            for n in member['full_name'].split()[:2]
        ])
        member['role'] = frappe.db.get_value(
            'Has Role',
            {'parent': member['name']},
            'role'
        )
        # Simple workload calculation
        member['workload'] = min(member['active_tasks'] * 20, 100)

    return members
```

### Step 8: Add Hooks

**File: `erpnext_projekt_hub_pro/hooks.py`**

```python
app_name = "erpnext_projekt_hub_pro"
app_title = "ERPNext Projekt Hub PRO"
app_publisher = "Your Company"
app_description = "PRO features for Projekt Hub"
app_version = "1.0.0"

# Required apps
required_apps = ["frappe", "erpnext", "erpnext_projekt_hub"]

# Include frontend assets after base app
app_include_js = [
    "/assets/erpnext_projekt_hub_pro/frontend/dist/main.js"
]

# Boot session hook to pass PRO status to frontend
extend_bootinfo = "erpnext_projekt_hub_pro.boot.boot_session"
```

**File: `erpnext_projekt_hub_pro/boot.py`**

```python
import frappe

def boot_session(bootinfo):
    """Add PRO status to bootinfo"""
    bootinfo.project_hub_pro_enabled = frappe.db.get_single_value(
        'System Settings',
        'projekt_hub_pro_enabled'
    ) or False

    bootinfo.has_pro_license = check_pro_license()

def check_pro_license():
    """Check if current user has PRO license"""
    # Implement your license checking logic
    return True  # Simplified for example
```

## Testing the Integration

### 1. Development Testing

```bash
# In base app
cd apps/erpnext_projekt_hub/frontend
npm run dev

# In PRO app (separate terminal)
cd apps/erpnext_projekt_hub_pro/frontend
npm run build

# Open browser console and check:
console.log(tabRegistry.getTabs());
// Should show: projects, tasks, my-time, team, time
```

### 2. Browser Console Testing

```javascript
// Check if PRO tabs are loaded
import { getTabs } from './tabRegistry';
console.log(getTabs().map(t => ({ key: t.key, order: t.order })));

// Should output:
// [
//   { key: 'projects', order: 10 },
//   { key: 'tasks', order: 20 },
//   { key: 'my-time', order: 30 },
//   { key: 'team', order: 40 },        // PRO
//   { key: 'time', order: 50 }         // PRO
// ]
```

### 3. Visual Verification

Navigate to `/project-hub` and verify:
- ✓ 5 tabs visible in navigation
- ✓ All icons render correctly
- ✓ Clicking each tab works
- ✓ Active state highlights correctly

## Deployment

### Production Build

```bash
# Build base app
cd apps/erpnext_projekt_hub/frontend
npm run build

# Build PRO app
cd apps/erpnext_projekt_hub_pro/frontend
npm run build

# Bench build
cd ../../../..
bench build
```

### Installation

```bash
# Install base app
bench get-app erpnext_projekt_hub

# Install PRO app
bench get-app erpnext_projekt_hub_pro

# Install on site
bench --site [site-name] install-app erpnext_projekt_hub
bench --site [site-name] install-app erpnext_projekt_hub_pro

# Enable PRO features
bench --site [site-name] set-config projekt_hub_pro_enabled 1
```

## Summary

This example demonstrates:

1. ✅ Clean separation of base and PRO features
2. ✅ No modification of base app code
3. ✅ Dynamic plugin loading
4. ✅ License checking
5. ✅ Graceful fallback if PRO not available
6. ✅ Full integration with routing and navigation

The Tab Registry system makes it easy to extend Project Hub with additional features while maintaining a clean, modular architecture.
