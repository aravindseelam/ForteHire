# Acceptance Criteria: HirePulse

**Version:** 1.0  
**Format:** Behavior-Driven Development (`Given / When / Then`)  

---

## US-01: Daily Action Triage (Prioritized Queue)

* **AC-01.1 (Default Grouping & Ordering)**  
  **Given** I am logged into HirePulse with open tasks across past, current, and future dates,  
  **When** I navigate to the Action Queue,  
  **Then** tasks are grouped in order: **Overdue**, **Due Today**, and **Upcoming**, and sorted chronologically by due date (oldest overdue first).

* **AC-01.2 (Task Card Context)**  
  **Given** an open task is displayed in the Action Queue,  
  **When** I inspect the task card,  
  **Then** it displays the task title, candidate name, job title, current hiring stage badge, due date/time, and quick actions (*Complete*, *Snooze*, *Change Stage*).

* **AC-01.3 (Time-to-Action Instrumentation)**  
  **Given** I load the Action Queue page at timestamp $t_0$,  
  **When** I perform my first task interaction (click *Complete*, *Snooze*, or open a candidate card) at timestamp $t_1$,  
  **Then** the system records a session metric of $(t_1 - t_0)$ in seconds for the **Time to Identify Next Action** calculation.

---

## US-02: Overdue Action Visibility & Filtering

* **AC-02.1 (Overdue Visual Highlighting)**  
  **Given** an open task has a `due_at` timestamp earlier than the current system time,  
  **When** the Action Queue renders,  
  **Then** the task appears under the **Overdue** section with a red overdue indicator showing how many days/hours late it is.

* **AC-02.2 (Multi-Filter Support)**  
  **Given** I am on the Action Queue,  
  **When** I select the **Overdue** status filter and the **Interview** stage filter,  
  **Then** only open overdue tasks for candidates currently in the *Interview* stage are displayed, along with an updated task count.

* **AC-02.3 (Empty State)**  
  **Given** no tasks match my active filter combination,  
  **When** the list refreshes,  
  **Then** a clear empty state message is shown with a one-click **"Reset Filters"** button.

---

## US-03: Workflow Execution Analytics

* **AC-03.1 (Core KPI Cards)**  
  **Given** there are recorded tasks and sessions in the workspace,  
  **When** I open the **Analytics** page,  
  **Then** I see three KPI cards displaying:
  1. **Time to Identify Next Action** (median seconds)
  2. **Overdue Action Rate** ($\frac{\text{Open Overdue Tasks}}{\text{Total Open Tasks}} \times 100\%$)
  3. **% of Tasks Completed Within Due Date** ($\frac{\text{Completed On/Before Original Due Date}}{\text{Total Completed Tasks}} \times 100\%$)

* **AC-03.2 (Real-Time Recalculation)**  
  **Given** my Overdue Action Rate is currently 40% (2 of 5 open tasks overdue),  
  **When** I mark 1 overdue task as Complete and navigate to the Analytics page,  
  **Then** the Overdue Action Rate immediately updates to 25% (1 of 4 open tasks overdue).

* **AC-03.3 (Zero-Data Handling)**  
  **Given** no tasks have been completed yet in the selected date range,  
  **When** I view the Analytics page,  
  **Then** `% of Tasks Completed Within Due Date` displays `—` (or `N/A`) rather than a `NaN` or division-by-zero error.

---

## US-04: Create a Follow-Up Task

* **AC-04.1 (Successful Creation)**  
  **Given** I click **"+ New Task"** on the Action Queue,  
  **When** I enter a title ("Send technical interview feedback"), select a candidate, select a task type, set a valid due date, and click **Save**,  
  **Then** the modal closes, a confirmation toast appears, and the new task immediately appears in the appropriate urgency bucket (**Due Today** or **Upcoming**).

* **AC-04.2 (Form Validation)**  
  **Given** the Create Task modal is open,  
  **When** I click **Save** without entering a task title or without selecting a due date,  
  **Then** submission is blocked and inline validation messages highlight the missing required fields.

* **AC-04.3 (Original Due Date Persistence)**  
  **Given** a task is created with `due_at = 2026-11-22`,  
  **When** the record is saved,  
  **Then** the system stores both `due_at` and an immutable `original_due_at` set to `2026-11-22`.

---

## US-05: Snooze / Reschedule a Task

* **AC-05.1 (Preset Snooze)**  
  **Given** an open task is in the **Overdue** or **Due Today** section,  
  **When** I click **Snooze** and select **"+1 Day"**,  
  **Then** the task's `due_at` shifts forward by 24 hours, `snooze_count` increments by 1, and the task moves into the **Upcoming** section.

* **AC-05.2 (Snooze Abuse Indicator)**  
  **Given** a task has been snoozed 3 or more times (`snooze_count >= 3`),  
  **When** the task card renders in the Action Queue,  
  **Then** a subtle warning badge (e.g., `"Snoozed 3x"`) is displayed on the card.

* **AC-05.3 (Original Due Date Integrity)**  
  **Given** a task originally due yesterday is snoozed to tomorrow,  
  **When** I complete that task tomorrow,  
  **Then** it counts as **completed late** against `original_due_at` in the Analytics metric `% of Tasks Completed Within Due Date`.

---

## US-06: Change Candidate Hiring Stage

* **AC-06.1 (Stage Transition)**  
  **Given** a candidate is currently in the **Screening** stage,  
  **When** I select **Client Submission** from the stage dropdown on their task card,  
  **Then** the candidate's stage updates immediately across all associated tasks in the Action Queue, and a stage-change event is logged with a timestamp.

* **AC-06.2 (Next-Action Prompt)**  
  **Given** I change a candidate's stage to an active stage (*Screening*, *Client Submission*, *Interview*, or *Offer*),  
  **When** the stage update saves,  
  **Then** a non-blocking prompt appears asking **"Schedule next follow-up task?"** with pre-filled candidate/job context and a **"Skip"** option.

* **AC-06.3 (Terminal Stage Handling)**  
  **Given** I change a candidate's stage to a terminal stage (**Placed** or **Rejected**),  
  **When** the stage update saves,  
  **Then** the next-action prompt is suppressed, and the system asks if I want to close any remaining open tasks for that candidate.