# IDhall REST API v1 Cheatsheet

Quick reference of verified behaviors, property names, and payloads for IDhall REST API v1.

---

## Known API Behaviors & Pitfalls

* **Minimal default projection:** `GET` endpoints only return `{id, title}` (or `{id, first_name, last_name}` for users) unless `props` is supplied.
* **Structured `filter` on `GET`:** Handled automatically by `MCPIdhall` (sends all query params in the JSON body when `filter` is present, because IDhall reads either the query string OR the JSON body, never both).
* **`order_by` restriction:** Not all properties are valid `order_by` keys (e.g., `order_by=creation_time` on `/users` returns HTTP 400). When a collection is small (`<= 100`), fetch with `page_size: 100` and sort client-side if `order_by` rejects a field.
* **Rate limiting (`HTTP 429`):** Apache enforces rate limits. `MCPIdhall` retries automatically with exponential backoff, but always prefer batched list calls (`page_size: 100`) over N+1 per-item calls.
* **Error format:** RFC 7807 `application/problem+json` (`title`, `detail`/`issuer`, `issue_code`, `status`).

---

## Key Object Properties (`props`)

### `Idea` (Initiatives)
* **Identity & Scope:** `id`, `reference`, `title`, `plan`, `category`, `classes`, `targeted_sites`, `targeted_organizations`, `targeted_processes`, `targeted_products`
* **Content:** `context`, `description`, `benefits`, `memo`, `tags`
* **People:** `author`, `authors`, `editor`, `approver`, `person_in_charge`, `sponsor`, `additional_members`, `implementation_coordinator`
* **Workflow & Status:** `current_stage`, `approval_stage`, `implementation_ending_stage`, `archived`, `confidential`, `public_draft`
* **Implementation:** `implementation_priority`, `implementation_start`, `implementation_end`, `implementation_actual_end`, `implementation_progress_value`, `implementation_progress_confidence`, `implementation_progress_comment`, `implementation_running_phase`, `implementation_tasks`
* **Timestamps:** `creation_time`, `publication_time`, `update_time`

### `IdeaFilter` (`filter` keys)
`id`, `title`, `keywords`, `plan`, `author`, `editor`, `approver`, `person_in_charge`, `sponsor`, `additional_member`, `current_stage`, `targeted_site`, `targeted_organization`, `targeted_process`, `targeted_product`, `category`, `class`, `risk`, `stakeholder`, `event`, `archived`, `confidential`, `followed`, `tag`, `creation_time`, `publication_time`, `update_time`

### `User`
`id`, `reference`, `first_name`, `last_name`, `email`, `phone`, `job_title`, `expertise_area`, `lang`, `manager`, `site`, `organization`, `login`, `profiles`, `ext_id`, `archived`, `creation_time`, `update_time`

---

## Common Stage Statuses & Transitions

### Frequent `current_stage.status` Values
* `SUBMITTED` — Awaiting initial approval/decision
* `APPROVER_CHANGED` — Transferred to a new approver
* `STANDBY` — On hold until `due_date`
* `APPROVED` — Approved / in implementation
* `IMPLEMENTED_WITH_SUCCESS` / `IMPLEMENTED_WITHOUT_SUCCESS` — Implementation finished, awaiting closure
* `CLOSED_WITH_SUCCESS` / `CLOSED_WITHOUT_SUCCESS` — Closed
* `REJECTED` — Rejected

### Key Transition Payloads (`idhall_transition_idea_stage`)

| Action | Required fields | Optional fields |
| :--- | :--- | :--- |
| `standby` | `due_date` (`YYYY-MM-DD`), `comment` | `comment_resources` |
| `end-implementation` | `comment` | `status`: `IMPLEMENTED_WITH_SUCCESS` \| `IMPLEMENTED_WITHOUT_SUCCESS` |
| `close` | `comment` | `status`: `CLOSED_WITH_SUCCESS` \| `CLOSED_WITHOUT_SUCCESS` |
| `reject` | Check via `idhall_get_endpoint_spec("POST__ideas__(id)__stages__reject")` | `reason`, `comment` |
| `cancel` | *(none — sends `DELETE /api/v1/ideas/{id}/stages/current`)* | — |

---

## 23 Reference Catalogs (`idhall_list_reference_items`)

`plans`, `perspectives`, `categories`, `classes`, `sites`, `organizations`, `processes`, `products`, `risks`, `risk-types`, `stakeholders`, `stakeholder-types`, `events`, `event-types`, `eval-scales`, `eval-units`, `user-profiles`, `action-plan-templates`, `phases-templates`, `idea-selections`, `idea-rejection-reasons`, `idea-submission-guidances`, `countries`.
