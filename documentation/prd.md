# Product Requirements Document (PRD): ForteHire

**Product Name:** ForteHire – Recruitment Intelligence & Workflow Optimisation Platform  
**Author:** Product Management Portfolio Project  
**Status:** Draft v1.0 (Phase 1 – Discovery & Specification)  
**Target Release:** MVP (Single-Recruiter & Small Agency Desk)

---

## 1. Problem Statement

Agency and high-volume recruiters manage 15–30 open requisitions and 100+ active candidates simultaneously across multiple hiring stages. While existing ATS/CRM tools (such as Recruit CRM) store candidate records, stages, and basic task lists, recruiters still struggle to answer one critical daily question: **“Who do I need to follow up with right now so no high-priority candidate or client slips through the cracks?”**

Because follow-ups are scattered across candidate profiles, flat task lists, email inboxes, and personal spreadsheets:
* Recruiters waste time at the start of every shift scanning multiple views to decide their next action.
* Tasks quietly become overdue without surfacing urgency relative to pipeline stage.
* Recruiters and desk leads lack real-time visibility into their own execution hygiene (overdue rates and on-time completion).

---

## 2. Product Hypothesis

If we give recruiters a unified **Action Queue** that surfaces prioritized, time-bound next actions alongside pipeline stage context—and pair it with a lightweight **Workflow Analytics** view tracking execution hygiene—recruiters will spend less time deciding what to do next, reduce overdue follow-ups, and complete a higher percentage of tasks on time without adding administrative overhead.

---

## 3. Target Users

| Persona | Profile | Primary Goal | Core Frustration |
| :--- | :--- | :--- | :--- |
| **Primary: Agency Recruiter (360° or Delivery)** | Manages 10–25 active roles; juggles candidate screens, client submissions, and interview prep daily. | Execute high-priority follow-ups fast without dropping candidates between stages. | Clicking through dozens of profiles and flat task lists to figure out what is urgent today. |
| **Secondary: Recruiting Team Lead / Desk Manager** | Oversees 3–8 recruiters; accountable for placement velocity and client SLAs. | Spot execution bottlenecks before candidates ghost or clients churn. | Relying on manual check-ins or lagging placement reports instead of leading workflow metrics. |

---

## 4. Scope (MVP)

### In Scope
1. **Prioritized Next-Action Queue (Home View):** Single workspace displaying tasks grouped by urgency (**Overdue**, **Due Today**, **Upcoming**) with candidate name, role, current hiring stage, and due date/time.
2. **Task Lifecycle Management:**
   * Create a task linked to a candidate and role with a due date and action type (e.g., *Follow-up Call*, *Send Feedback*, *Interview Prep*, *Client Check-in*).
   * Mark a task as **Complete** with timestamp logging.
   * **Snooze / Reschedule** a task to a preset interval (+1 day, +3 days, Next Monday) or custom date, tracking snooze count.
3. **Inline Pipeline Stage Updates:** Update a candidate's hiring stage (*Applied → Screening → Client Submission → Interview → Offer → Placed / Rejected*) directly from the queue or candidate drawer, with an optional prompt to create the next follow-up task.
4. **Workflow Analytics Page:** Live dashboard displaying the exact three MVP success metrics (see Section 6) with date-range filtering (Last 7 days / Last 30 days) and breakdown by hiring stage.

### Out of Scope (Explicit Non-Goals for MVP)
* **No AI or ML features:** No generative email drafting, no AI-powered prioritization, no automated resume parsing, and no LLM summaries. All prioritization is deterministic (rule-based on due date and stage).
* **No Candidate Scoring or Ranking:** ForteHire optimizes *recruiter workflow execution*, not candidate evaluation. There are no match percentages, fit scores, or automated candidate ratings.
* **No Two-Way Email / Calendar / LinkedIn Sync:** Outbound communication happens outside the MVP; ForteHire tracks the workflow action and timestamp.
* **No Multi-Tenant Enterprise Permissions or Billing:** MVP supports single-workspace operation with seeded realistic recruitment data.

---

## 5. Success Metrics

These three North Star execution metrics define MVP success and are surfaced directly on the **ForteHire Analytics** page:

| Metric | Definition | Formula | MVP Target |
| :--- | :--- | :--- | :--- |
| **1. Time to Identify Next Action** | Median elapsed seconds from opening the Action Queue (session start) to initiating/clicking the first task action (complete, snooze, or open candidate). | $\text{Median}(t_{\text{first\_action}} - t_{\text{queue\_load}})$ | **< 15 seconds** |
| **2. Overdue Action Rate** | Percentage of currently open tasks whose due date/time has passed. | $\frac{\text{Open Tasks Past Due Date}}{\text{Total Open Tasks}} \times 100\%$ | **< 15%** |
| **3. % of Tasks Completed Within Due Date** | Percentage of completed tasks finished on or before their original due date/time. | $\frac{\text{Tasks Completed } \le \text{ Due Date}}{\text{Total Completed Tasks}} \times 100\%$ | **$\ge 80\%$** |

*Note: Snoozing a task updates its active due date for scheduling purposes, while preserving the original due date in the data model so on-time completion cannot be gamed silently.*

---

## 6. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
| :--- | :---: | :---: | :--- |
| **Adoption Friction ("Another Tool")** — Recruiters already live in an ATS and resist logging tasks in a separate workspace. | High | High | Keep task creation under 3 clicks, auto-prompt next action on stage change, and design ForteHire as a lightweight workflow layer that could eventually sit atop an ATS API. |
| **Snooze Abuse ("Kicking the Can")** — Recruiters repeatedly snooze overdue tasks to artificially lower their Overdue Action Rate. | Medium | Medium | Track `snooze_count` per task, preserve `original_due_at` for the On-Time Completion metric, and visually badge tasks snoozed $\ge 3$ times. |
| **Metric Anxiety / Surveillance Pushback** — Recruiters perceive execution metrics as micromanagement rather than a personal productivity aid. | Medium | High | Frame the Analytics page as a self-service desk health check for the recruiter first, avoiding individual leaderboard rankings in MVP. |
| **Unvalidated Gap Hypothesis** — Pain points are sourced from secondary research (forums/docs) and not yet validated with live user interviews. | High | High | Explicitly label research as unvalidated; run 5–8 structured discovery interviews with agency recruiters before investing in Phase 2 integrations. |
