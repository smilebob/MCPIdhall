# IDhall Workflow Runbooks

Detailed procedures for the 5 core workflows supported by the `idhall` skill.

---

## Workflow 1: Portfolio Cockpit & Action Report

Use when the user asks for *"my initiatives"*, *"what I need to work on"*, *"portfolio review"*, or *"overdue items"*.

1. **Resolve caller ID:** Call `idhall_whoami` to get `user.id` (`UID`).
2. **Fetch active initiatives in charge:** Call `idhall_list_ideas` with:
   * `filter`: `{"archived": false, "person_in_charge": UID}`
   * `page_size`: `100`, `count`: `true`
   * `props`: `["id", "reference", "title", "plan", "current_stage", "person_in_charge", "approver", "implementation_coordinator", "implementation_end", "implementation_progress_value", "implementation_progress_confidence", "update_time"]`
   * If `total_count > 100`, paginate with `offset: 100, 200, ...`.
3. **Optionally check `approver`** (`filter: {"archived": false, "approver": UID}`) if the user asks for approval queues.
4. **Exclude terminal statuses** (`CLOSED_WITH_SUCCESS`, `CLOSED_WITHOUT_SUCCESS`, `REJECTED`) unless the user asks for historical/closed items.
5. **Classify into 5 actionable buckets** (comparing `implementation_end` against today's date):
   * **Priority 1 — Awaiting Decision / Approval:** `current_stage.status` in `SUBMITTED`, `APPROVER_CHANGED`, `DETAILS_PROVIDED`, `EXPERTISE_PROVIDED`.
   * **Priority 2 — Quick Wins (Ready to Finish / Close):** `IMPLEMENTED_WITH_SUCCESS` (ready for `close`) OR `APPROVED` with `implementation_progress_value == 100` (ready for `end-implementation`).
   * **Priority 3 — Imminent Deadlines:** `APPROVED`, `< 100%`, `implementation_end` within the next 60 days.
   * **Priority 4 — Overdue Items:** `implementation_end < today`, `< 100%` (highlight near-complete `>= 80%` items separately from stalled `0%` items).
   * **Priority 5 — Future Horizon:** `implementation_end` beyond 60 days.
6. **Present the report:** Start with a compact KPI summary table, then concise Markdown tables per bucket (`ID`, `Status`, `Due Date`, `Progress`, `Title`), and finish with 2–3 concrete next-step offers.

---

## Workflow 2: Guided Initiative Creation

Use when the user wants to create a new initiative.

1. **List available plans:** Call `idhall_list_reference_items(resource="plans", props=["id", "title"])`.
2. **Select the plan (`plan_id`):** If the user didn't specify one, ask them to pick from the returned plans (recommending the plan matching their site/organization when obvious).
3. **Check plan-specific field requirements:** Call `idhall_get_idea_input_availability(plan_id=<id>)`.
   * Note every property where `required: true` (for example, `targeted_organizations` may be required on certain plans) and ignore properties where `available: false`.
4. **Resolve referenced IDs:** If the user names a site, organization, category, or user, resolve their numeric ID via `idhall_list_reference_items` or `idhall_list_users` — never invent IDs.
5. **Default to Draft (`idhall_create_idea_draft`):**
   * Only `title` (max 150 chars) is strictly required for a draft, plus `plan` and any provided fields.
   * Present the created `#id` and title, then offer to enrich it (`idhall_update_idea`) or publish it (`idhall_publish_idea_draft`, after confirmation).
6. **Direct Publication (`idhall_create_idea`):** Only if the user explicitly asks to publish immediately AND all `required: true` fields from step 3 are populated. Confirm before publishing.

---

## Workflow 3: Action Plan & Progress Tracking

Use when managing implementation tasks, progress updates, or collaboration items on an initiative `#id`.

1. **Inspect current state:**
   * Implementation overview: `idhall_get_idea_implementation(idea_id=<id>, props=["coordinator", "start_date", "end_date", "priority", "progress_value", "progress_confidence", "progress_comment"])`
   * Task list: `idhall_list_action_plan_tasks(idea_id=<id>, props=["id", "title", "owner", "progress_value", "progress_confidence", "start_date", "end_date", "phase", "section"])`
2. **Task creation / updates:**
   * Create: `idhall_create_action_plan_task(idea_id, title, owner?, description?, phase?, section?, time_range?)`
   * Update fields: `idhall_update_action_plan_task(idea_id, task_id, fields={...})`
   * Update progress: `idhall_update_task_progress(idea_id, task_id, percent?, confidence?, comment?)`
   * Delete: **confirm first**, then `idhall_delete_action_plan_task(idea_id, task_id)`.
3. **Collaboration:**
   * Contributions: `idhall_list_idea_contributions` / `idhall_add_idea_contribution(idea_id, text, sentiment?)`
   * Memo: `idhall_get_idea_memo` / `idhall_set_idea_memo(idea_id, memo)`
   * Tags: `idhall_get_idea_tags` / `idhall_manage_idea_tags(idea_id, operation="add"|"replace"|"remove", tags=[...])`

---

## Workflow 4: Workflow Stage Transitions

Use when advancing, putting on standby, approving, rejecting, finishing, closing, or cancelling a stage.

1. **Inspect current stage:** `idhall_get_idea_stage(idea_id=<id>)`.
2. **Check exact payload schema** if unsure: `idhall_get_endpoint_spec("POST__ideas__(id)__stages__<action>")`.
3. **Apply safety guardrails:**
   * Always confirm before `reject`, `close`, `cancel`, or batch transitions (`> 1` initiative).
4. **Execute transition:** `idhall_transition_idea_stage(idea_id=<id>, action="<action>", payload={...})`.
5. **Verify & report:** Show the returned new `status` and `addressee` (next person in charge in the workflow).

---

## Workflow 5: Universal Access to All 208 Endpoints

Use for specialized domains not covered by dedicated tools (e.g., `audits`, `stakeholders/{id}/contacts`, `opportunity-analysis/criteria`, `resources`, `risks`, `events`, `action-plan/sections`, `user-registration-requests`).

1. **Search locally (0 API calls):** `idhall_search_endpoints(query="<keywords>", method="GET"|"POST"|...)`.
2. **Inspect schema locally (0 API calls):** `idhall_get_endpoint_spec(endpoint_id="<id_from_step_1>")`.
   * Check `path_params`, `request_query_params`, `request_payload_formats` (required fields & enum values), and `classes`.
3. **Confirm if mutating/destructive** according to the safety guardrails.
4. **Execute:** `idhall_api_request(method=..., path="/api/v1/...", query_params=..., json_body=...)`.
