### Projekt HUB

New Project design in ERPnext

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app erpnext_projekt_hub
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/erpnext_projekt_hub
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


---

## Project filter in Capacity Planning

### Overview

The **Capacity Planning** tab (`/project-hub/capacity-planning`) provides a weekly Mon–Fri grid that shows every active employee's planned tasks and remaining free capacity. A **Project** filter in the top bar narrows the list to employees who are relevant to the selected project for the current week.

### Accessing the view

Navigate to `/project-hub/capacity-planning`. The tab is visible to users with any of these roles:
- **Projects Manager**
- **Project Manager**
- **Team Lead**
- **Consultant**
- **System Manager / Administrator**

### Filters

| Filter | Behaviour |
|--------|-----------|
| **Week navigator** (◀ / ▶) | Shifts the view one week backward or forward. Click the week label to jump back to the current week. |
| **Project** dropdown | Filters employees to those who (a) already have tasks in the project this week **or** (b) still have free capacity and can be assigned. When a project is selected, each day-cell shows only tasks belonging to that project. |
| **Employee** dropdown | Further narrows the list to a single employee (AND logic with the project filter). |

### Inclusion logic for the project filter

```
include employee if:
    employee.has_tasks_in(project, week) == True
    OR employee.weekly_free_hours > 0
```

Employees who have tasks in **a different project** and are **fully booked** (0 free hours) are hidden from the filtered view.

### Per-day cell

Each cell shows:
- **Task chips** – clickable, open the task in a new Frappe desk tab.
  When no project is selected all tasks are shown; when a project is selected only that project's tasks appear.
- **Free hours badge** – green/amber/red depending on remaining capacity ratio.
- **Overload warning** – shown when `planned_hours > 8h` (daily default capacity).

The **week total** column warns when `weekly_planned > 40h`.

### Quick-add task (+)

Hover over any day cell to reveal the **+** button. Clicking it opens the *Add task* modal pre-filled with:
- The employee from the row
- The project from the active filter (editable)
- The clicked day as both start and end date

The task is created as `Open`, assigned to the employee via Frappe's `assign_to` mechanism, and the employee is auto-added to the project team if not already present.

### Architecture

| File | Purpose |
|------|---------|
| `erpnext_projekt_hub/api/capacity_planning.py` | Three whitelisted endpoints: `get_capacity_planning_data`, `get_capacity_projects`, `create_capacity_task` |
| `frontend/src/stores/capacityPlanningStore.js` | Pinia store: week navigation, filter state, modal state, API calls |
| `frontend/src/pages/CapacityPlanning.vue` | Weekly grid, filters bar, overload badges, add-task modal |
| `frontend/src/tabs/coreTabs.js` | Tab registration (`key: 'capacity'`, route `CapacityPlanning`, path `/project-hub/capacity-planning`) |

### Default capacity

The default capacity is **8 hours/day (40 h/week)**. It is defined as `DEFAULT_DAILY_HOURS = 8.0` in `capacity_planning.py`. To change it, update that constant (or extend with a per-employee configuration if your ERPNext instance tracks `working_hours` on the Employee doctype).

### Running unit tests

```bash
cd ~/frappe-bench/apps/erpnext_projekt_hub
.venv/bin/pip install pytest   # one-time
.venv/bin/python -m pytest erpnext_projekt_hub/tests/test_capacity_planning.py -v
# 38 passed
```

To run inside the Frappe test runner (requires a site):
```bash
cd ~/frappe-bench
bench run-tests --app erpnext_projekt_hub \
    --module erpnext_projekt_hub.tests.test_capacity_planning
```

### Smoke test (UI)

1. Log in as a user with **Projects Manager** role.
2. Navigate to `/project-hub/capacity-planning`.
3. Verify the weekly grid loads with employee rows and Mon–Fri columns.
4. Select a project from the **Project** dropdown — list updates without page reload.
5. Employees without tasks in the project but with free hours remain visible; fully-booked unrelated employees disappear.
6. Hover a day cell → **+** button appears. Click it → modal opens pre-filled.
7. Fill in *Subject*, confirm project & dates → click **Create task**.
8. Modal closes, grid refreshes, new task chip appears in the correct cell.
9. Assign the same employee 10h on the same day → cell turns red with overload warning.
10. Navigate prev/next week — data reloads automatically.

---

### License

mit
