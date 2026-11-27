---
name: idhall
description: >-
  Guides AI agents in operating the IDhall innovation, continuous improvement,
  and action-plan platform (Humanperf Software) through the MCPIdhall MCP
  server. Use whenever the user asks to inspect, report on, create, update,
  prioritize, or transition IDhall initiatives (ideas), action plans, tasks,
  contributions, memos, tags, users, or reference catalogs (plans, sites,
  organizations, risks, stakeholders), or to query any of the 208 IDhall REST
  API v1 endpoints.
---

# IDhall Operational Skill (via MCPIdhall)

Use this skill whenever interacting with an **IDhall** instance through the `idhall` MCP server (`idhall_*` tools).

## Core Operating Rules

1. **Always respond in the user's language** (French, English, etc.) regardless of the language of this skill.
2. **Identify the caller first when context requires "my" items:** Call `idhall_whoami` (with `props: ["id", "first_name", "last_name", "site", "organization"]`) once per session to obtain the user's numeric `sub` (`id`) before filtering by `person_in_charge`, `approver`, `author`, or `owner`.
3. **Always pass `props` on read calls:** IDhall `GET` endpoints return only minimal fields (`id`, `title`) by default. Explicitly request the properties needed for the task (see [API Cheatsheet](./references/api_cheatsheet.md)).
4. **Respect rate limits (`HTTP 429`):** Prefer server-side `filter` + `page_size: 100` over fetching many individual items in loops.
5. **Never guess undocumented payloads:** For any unfamiliar endpoint or transition, inspect its exact schema with `idhall_search_endpoints` and `idhall_get_endpoint_spec` (zero network calls — uses the local 208-endpoint catalog) before executing `idhall_api_request`.

## Write Safety & Confirmation Guardrails

Because `MCPIdhall` operates in **read/write** mode with the user's live RBAC permissions:

* **Mandatory explicit confirmation BEFORE executing:**
  * Any permanent deletion (`idhall_delete_idea`, `idhall_delete_action_plan_task`, or `DELETE` via `idhall_api_request`).
  * Any irreversible or high-impact workflow transition: `reject`, `close`, or `publish` (when moving a draft into the live workflow).
  * Any **bulk mutation** affecting **more than 1 initiative or task** — always show the exact list of target IDs, titles, and action before executing, unless the user has already explicitly confirmed that exact batch.
* **No unnecessary friction for low-risk explicit requests:**
  * Read operations (`GET`, counts, reports, endpoint discovery).
  * Single-item drafts (`idhall_create_idea_draft`), memos (`idhall_set_idea_memo`), tags (`idhall_manage_idea_tags`), contributions (`idhall_add_idea_contribution`), and single progress updates when explicitly requested by the user.

## Supported Workflows

Read the detailed step-by-step runbook for the active task in [Workflow Runbooks](./references/workflows.md):

1. **Portfolio Cockpit & Action Report** — Fetch active initiatives assigned to the user (`person_in_charge`, `approver`), compute KPIs, and group by priority: awaiting decision, 100% quick wins, upcoming deadlines, overdue items, and future horizon.
2. **Guided Initiative Creation** — List available plans (`plans`), check mandatory/available fields for the chosen plan via `idhall_get_idea_input_availability(plan_id=...)`, default to creating a **draft** (`idhall_create_idea_draft`), and only publish upon confirmation.
3. **Action Plan & Progress Tracking** — Inspect or manage tasks (`idhall_list_action_plan_tasks`, `idhall_create_action_plan_task`, `idhall_update_action_plan_task`, `idhall_update_task_progress`), implementation progress, contributions, memos, and tags.
4. **Workflow Stage Transitions** — Inspect current stage (`idhall_get_idea_stage`), verify required fields (`comment`, `status`, `due_date`, etc.) via `idhall_get_endpoint_spec`, and execute `idhall_transition_idea_stage`.
5. **Universal 208-Endpoint Access** — Follow the strict 3-step sequence: `idhall_search_endpoints` → `idhall_get_endpoint_spec` → `idhall_api_request`.

## References (Read On Demand)

* [Workflow Runbooks](./references/workflows.md) — Detailed procedures and output templates for all 5 workflows.
* [IDhall API v1 Cheatsheet](./references/api_cheatsheet.md) — Key properties, filter keys, stage statuses, transition payloads, and known API behaviors.
