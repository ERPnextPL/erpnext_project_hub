/**
 * Tab Registry Tests
 *
 * Basic tests for the Tab Registry system
 * Run with: npm test or your test runner
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import tabRegistry, { registerTab, getTabs, getNavItems } from '../tabRegistry';
import { Folder } from 'lucide-vue-next';

describe('Tab Registry', () => {
	beforeEach(() => {
		// Reset registry before each test
		tabRegistry.reset();
	});

	describe('Tab Registration', () => {
		it('should register a tab successfully', () => {
			const tabConfig = {
				key: 'test',
				routeName: 'TestRoute',
				path: '/project-hub/test',
				labelKey: 'Test',
				icon: Folder,
				color: 'text-blue-600',
				bg: 'bg-blue-50',
				component: () => import('../pages/ProjectList.vue'),
			};

			registerTab(tabConfig);

			const tabs = getTabs();
			expect(tabs).toHaveLength(1);
			expect(tabs[0].key).toBe('test');
		});

		it('should assign default order if not provided', () => {
			registerTab({
				key: 'test',
				routeName: 'TestRoute',
				path: '/test',
				labelKey: 'Test',
				icon: Folder,
				color: 'text-blue-600',
				bg: 'bg-blue-50',
				component: () => {},
			});

			const tabs = getTabs();
			expect(tabs[0].order).toBe(50);
		});

		it('should warn when registering duplicate key', () => {
			const consoleSpy = vi.spyOn(console, 'warn');

			const config = {
				key: 'duplicate',
				routeName: 'Test',
				path: '/test',
				labelKey: 'Test',
				icon: Folder,
				color: 'text-blue-600',
				bg: 'bg-blue-50',
				component: () => {},
			};

			registerTab(config);
			registerTab(config);

			expect(consoleSpy).toHaveBeenCalledWith(
				expect.stringContaining('already registered')
			);
			consoleSpy.mockRestore();
		});

		it('should reject duplicate route name', () => {
			const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

			registerTab({
				key: 'first',
				routeName: 'DuplicateRoute',
				path: '/first',
				labelKey: 'First',
				icon: Folder,
				color: '',
				bg: '',
				component: () => {},
			});

			registerTab({
				key: 'second',
				routeName: 'DuplicateRoute',
				path: '/second',
				labelKey: 'Second',
				icon: Folder,
				color: '',
				bg: '',
				component: () => {},
			});

			expect(getTabs()).toHaveLength(1);
			expect(warnSpy).toHaveBeenCalled();
			warnSpy.mockRestore();
		});

		it('should reject duplicate path', () => {
			const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

			registerTab({
				key: 'first',
				routeName: 'FirstRoute',
				path: '/duplicate',
				labelKey: 'First',
				icon: Folder,
				color: '',
				bg: '',
				component: () => {},
			});

			registerTab({
				key: 'second',
				routeName: 'SecondRoute',
				path: '/duplicate',
				labelKey: 'Second',
				icon: Folder,
				color: '',
				bg: '',
				component: () => {},
			});

			expect(getTabs()).toHaveLength(1);
			expect(warnSpy).toHaveBeenCalled();
			warnSpy.mockRestore();
		});
	});

	describe('Tab Ordering', () => {
		it('should sort tabs by order value', () => {
			registerTab({ key: 'third', routeName: 'T3', path: '/t3', labelKey: 'T3', icon: Folder, color: '', bg: '', component: () => {}, order: 30 });
			registerTab({ key: 'first', routeName: 'T1', path: '/t1', labelKey: 'T1', icon: Folder, color: '', bg: '', component: () => {}, order: 10 });
			registerTab({ key: 'second', routeName: 'T2', path: '/t2', labelKey: 'T2', icon: Folder, color: '', bg: '', component: () => {}, order: 20 });

			const tabs = getTabs();
			expect(tabs[0].key).toBe('first');
			expect(tabs[1].key).toBe('second');
			expect(tabs[2].key).toBe('third');
		});
	});

	describe('Navigation Items', () => {
		it('should return navigation items without component', () => {
			registerTab({
				key: 'test',
				routeName: 'TestRoute',
				path: '/test',
				labelKey: 'Test',
				icon: Folder,
				color: 'text-blue-600',
				bg: 'bg-blue-50',
				component: () => {},
			});

			const navItems = getNavItems();
			expect(navItems).toHaveLength(1);
			expect(navItems[0]).not.toHaveProperty('component');
			expect(navItems[0]).toHaveProperty('key');
			expect(navItems[0]).toHaveProperty('to');
		});
	});

	describe('Route Generation', () => {
		it('should generate routes for all tabs', () => {
			registerTab({
				key: 'test1',
				routeName: 'Test1',
				path: '/test1',
				labelKey: 'Test 1',
				icon: Folder,
				color: '',
				bg: '',
				component: () => {},
			});

			registerTab({
				key: 'test2',
				routeName: 'Test2',
				path: '/test2',
				labelKey: 'Test 2',
				icon: Folder,
				color: '',
				bg: '',
				component: () => {},
			});

			const routes = tabRegistry.getRoutes();
			expect(routes).toHaveLength(2);
			expect(routes[0]).toHaveProperty('path');
			expect(routes[0]).toHaveProperty('name');
			expect(routes[0]).toHaveProperty('component');
		});
	});

	describe('Reserved Segments', () => {
		it('should generate reserved segments from tab paths', () => {
			registerTab({
				key: 'my-tasks',
				routeName: 'MyTasks',
				path: '/project-hub/my-tasks',
				labelKey: 'Tasks',
				icon: Folder,
				color: '',
				bg: '',
				component: () => {},
			});

			const segments = tabRegistry.getReservedSegments();
			expect(segments).toHaveProperty('/project-hub/my-tasks');
			expect(segments).toHaveProperty('my-tasks');
			expect(segments['my-tasks']).toBe('MyTasks');
		});

		it('should not include base path as segment', () => {
			registerTab({
				key: 'projects',
				routeName: 'ProjectList',
				path: '/project-hub',
				labelKey: 'Projects',
				icon: Folder,
				color: '',
				bg: '',
				component: () => {},
			});

			const segments = tabRegistry.getReservedSegments();
			expect(segments).not.toHaveProperty('project-hub');
		});
	});

	describe('Tab Lookup', () => {
		it('should find tab by key', () => {
			registerTab({
				key: 'test',
				routeName: 'TestRoute',
				path: '/test',
				labelKey: 'Test',
				icon: Folder,
				color: '',
				bg: '',
				component: () => {},
			});

			const tab = tabRegistry.getTab('test');
			expect(tab).toBeDefined();
			expect(tab.key).toBe('test');
		});

		it('should find tab by route name', () => {
			registerTab({
				key: 'test',
				routeName: 'TestRoute',
				path: '/test',
				labelKey: 'Test',
				icon: Folder,
				color: '',
				bg: '',
				component: () => {},
			});

			const tab = tabRegistry.getTabByRouteName('TestRoute');
			expect(tab).toBeDefined();
			expect(tab.routeName).toBe('TestRoute');
		});

		it('should return undefined for non-existent tab', () => {
			const tab = tabRegistry.getTab('nonexistent');
			expect(tab).toBeUndefined();
		});
	});

	describe('Initialization', () => {
		it('should track initialization state', () => {
			expect(tabRegistry.isInitialized()).toBe(false);

			tabRegistry.markInitialized();
			expect(tabRegistry.isInitialized()).toBe(true);
		});

		it('should reset initialization state on reset', () => {
			tabRegistry.markInitialized();
			expect(tabRegistry.isInitialized()).toBe(true);

			tabRegistry.reset();
			expect(tabRegistry.isInitialized()).toBe(false);
		});
	});

	describe('Unregistration', () => {
		it('should unregister a tab by key', () => {
			registerTab({
				key: 'test',
				routeName: 'TestRoute',
				path: '/test',
				labelKey: 'Test',
				icon: Folder,
				color: '',
				bg: '',
				component: () => {},
			});

			expect(getTabs()).toHaveLength(1);

			tabRegistry.unregisterTab('test');
			expect(getTabs()).toHaveLength(0);
		});
	});
});

describe('Core Tabs Integration', () => {
	beforeEach(() => {
		tabRegistry.reset();
	});

	it('should register all core tabs', async () => {
		const { registerCoreTabs } = await import('../coreTabs');
		registerCoreTabs();

		const tabs = getTabs();
		expect(tabs.length).toBeGreaterThanOrEqual(3);
		expect(tabs.find(t => t.key === 'projects')).toBeDefined();
		expect(tabs.find(t => t.key === 'tasks')).toBeDefined();
		expect(tabs.find(t => t.key === 'my-time')).toBeDefined();
	});
});

describe('PRO Tabs Example', () => {
	beforeEach(() => {
		tabRegistry.reset();
	});

	it('should allow adding PRO tabs after core tabs', () => {
		// Simulate core tabs registration
		registerTab({
			key: 'projects',
			routeName: 'ProjectList',
			path: '/project-hub',
			labelKey: 'Projects',
			icon: Folder,
			color: 'text-blue-600',
			bg: 'bg-blue-50',
			component: () => {},
			order: 10,
		});

		// Simulate PRO tabs registration
		registerTab({
			key: 'team',
			routeName: 'TeamManager',
			path: '/project-hub/team-manager',
			labelKey: 'Team',
			icon: Folder,
			color: 'text-purple-600',
			bg: 'bg-purple-50',
			component: () => {},
			order: 40,
		});

		const tabs = getTabs();
		expect(tabs).toHaveLength(2);
		expect(tabs[0].key).toBe('projects'); // Lower order comes first
		expect(tabs[1].key).toBe('team');
	});
});
