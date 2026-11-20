# User Stories: ForteHire

**Version:** 1.0  
**Scope:** MVP Workflow & Analytics  
**Primary Persona:** Agency Recruiter  

---

## Core Stories

### US-01: Daily Action Triage (Prioritized Queue)
> **As an** agency recruiter starting my workday,  
> **I want** to see all my open follow-up tasks automatically grouped into **Overdue**, **Due Today**, and **Upcoming** with candidate and hiring-stage context,  
> **So that** I can identify and start my highest-priority next action in seconds without opening multiple profiles.

**Priority:** P0 (Must Have)  
**Linked Metric:** Time to Identify Next Action

---

### US-02: Overdue Action Visibility & Filtering
> **As an** agency recruiter managing 20+ open roles,  
> **I want** to filter my queue by status (**Overdue**, **Due Today**, **Completed**) and hiring stage (e.g., *Interview*, *Offer*),  
> **So that** I can immediately clear overdue follow-ups on late-stage candidates before they drop off.

**Priority:** P0 (Must Have)  
**Linked Metric:** Overdue Action Rate

---

### US-03: Workflow Execution Analytics
> **As an** agency recruiter (or desk lead),  
> **I want** to view a live Analytics page showing my **Time to Identify Next Action**, **Overdue Action Rate**, and **% of Tasks Completed Within Due Date**,  
> **So that** I can measure my follow-up discipline and spot which hiring stages cause the most delays.

**Priority:** P0 (Must Have)  
**Linked Metrics:** All 3 North Star Metrics

---

## Supporting Workflow Stories

### US-04: Create a Follow-Up Task
> **As an** agency recruiter,  
> **I want** to quickly create a new task linked to a specific candidate and job—specifying an action title, type, and due date,  
> **So that** every promised follow-up is captured in my queue instead of sticky notes or spreadsheets.

**Priority:** P0 (Must Have)  
**Linked Metric:** % of Tasks Completed Within Due Date

---

### US-05: Snooze / Reschedule a Task
> **As an** agency recruiter waiting on a client or candidate response,  
> **I want** to snooze an open task to a preset interval (*Tomorrow*, *+3 Days*, *Next Week*) or a custom date,  
> **So that** my "Due Today" queue stays focused on actionable work while ensuring the follow-up resurfaces automatically.

**Priority:** P1 (Should Have)  
**Linked Metrics:** Overdue Action Rate, % of Tasks Completed Within Due Date

---

### US-06: Change Candidate Hiring Stage
> **As an** agency recruiter progressing a candidate through the pipeline,  
> **I want** to update a candidate's hiring stage directly from the Action Queue and be prompted to schedule the next follow-up task,  
> **So that** pipeline status stays accurate and no candidate sits idle after a stage transition.

**Priority:** P1 (Should Have)  
**Linked Metrics:** Time to Identify Next Action, Overdue Action Rate

---

## Story Map Summary

| ID | Story Title | Primary Screen | MVP Release |
| :--- | :--- | :--- | :---: |
| US-01 | Daily Action Triage | Action Queue (`/`) | Yes |
| US-02 | Overdue Visibility & Filtering | Action Queue (`/`) | Yes |
| US-03 | Workflow Execution Analytics | Analytics (`/analytics`) | Yes |
| US-04 | Create a Follow-Up Task | Action Queue Modal / Drawer | Yes |
| US-05 | Snooze / Reschedule a Task | Task Card / Action Menu | Yes |
| US-06 | Change Candidate Hiring Stage | Task Card / Candidate Drawer | Yes |
