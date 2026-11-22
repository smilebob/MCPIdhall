# Synthèse complète — API REST IDhall (Humanperf Software)

- **Instance :** `https://example.idhall.com`
- **Version IDhall :** `5.0.0.6` (`version_number`: `5000006`)
- **Version API :** `v1`
- **Total endpoints documentés :** **208**
- **Répartition par méthode HTTP :** `DELETE` : 31, `GET` : 102, `PATCH` : 26, `POST` : 41, `PUT` : 8
- **Modèles / Classes typées :** **124** (+ `ProblemDetails`)
- **Export généré le :** `2026-11-22T15:25:01.153933+00:00`

---

## 1. Conventions techniques transverses

### Authentification & En-têtes
- `Authorization: Bearer <JWT>` *(obligatoire)* — Jeton JWT signé (`RS256`), lié à un utilisateur IDhall dont il hérite strictement les permissions.
- `Accept: application/json`
- `Accept-Language` *(optionnel, ex. `fr`, `en`)* — Langue des libellés et messages d'erreur.
- `IDhall-Timezone` *(optionnel)* — Fuseau horaire (liste via `GET /api/v1/locale-settings/timezones`).

### Pagination, Projection (`props`) et Filtres (`filter`)
- **Pagination :** `offset` (défaut `0`), `page_size` (`1` à `100`, défaut `20`), `count` (`true`/`false` pour inclure le total dans la réponse). Chaque collection dispose aussi d'un endpoint dédié `GET .../count`.
- **Projection des champs (`props`) :** Par défaut, les endpoints `GET` ne retournent que les champs minimaux (`id`, `title`, etc.). Passez `props` (tableau `props[]=...` ou liste séparée par des espaces) pour sélectionner les propriétés voulues.
- **Filtres (`filter`) :** Objet structuré (ex. `IdeaFilter`, `UserFilter`, etc.). Sur la plupart des endpoints `GET`, les paramètres de requête peuvent aussi être envoyés dans le **corps de la requête** (`application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`).
- **Erreurs :** Format standard RFC 7807 `application/problem+json` (`title`, `severity`, `issuer`, `issue_type`, `issue_code`, `status`).
- **Rate Limiting :** Limitation de débit active côté serveur (`HTTP 429 Too Many Requests`). Prévoir un backoff exponentiel côté client / serveur MCP.

---

## 2. Vue d'ensemble par domaine

| Domaine | Endpoints | Méthodes |
| :--- | :---: | :--- |
| Aides à la déclaration d'initiatives | 3 | `GET` |
| Axes | 9 | `DELETE`, `GET`, `PATCH`, `POST` |
| Catégories | 6 | `DELETE`, `GET`, `PATCH`, `POST` |
| Demandes d'inscription | 3 | `GET` |
| Initiatives | 13 | `DELETE`, `GET`, `PATCH`, `POST` |
| Initiatives — Analyse d'opportunité | 8 | `DELETE`, `GET`, `PATCH`, `POST`, `PUT` |
| Initiatives — Contributions | 4 | `DELETE`, `GET`, `POST` |
| Initiatives — Mise en œuvre | 4 | `GET`, `PATCH`, `POST` |
| Initiatives — Mémo | 3 | `DELETE`, `GET`, `PUT` |
| Initiatives — Plan d'action | 23 | `DELETE`, `GET`, `PATCH`, `POST`, `PUT` |
| Initiatives — Tags | 4 | `DELETE`, `GET`, `POST`, `PUT` |
| Initiatives — Traitement (Workflow) | 12 | `DELETE`, `GET`, `POST` |
| Initiatives — Vérifications d'efficacité | 4 | `DELETE`, `GET`, `POST` |
| Modèles de plan d'action | 3 | `GET` |
| Motifs de non-recevabilité | 3 | `GET` |
| Paramètres régionaux | 1 | `GET` |
| Parties prenantes | 11 | `DELETE`, `GET`, `PATCH`, `POST` |
| Pays | 1 | `GET` |
| Perspectives | 3 | `GET` |
| Plans de phases | 3 | `GET` |
| Processus | 6 | `DELETE`, `GET`, `PATCH`, `POST` |
| Produits | 6 | `DELETE`, `GET`, `PATCH`, `POST` |
| Profils d'accès | 3 | `GET` |
| Risques | 9 | `DELETE`, `GET`, `PATCH`, `POST` |
| Référentiel de l'API | 2 | `GET` |
| Services | 6 | `DELETE`, `GET`, `PATCH`, `POST` |
| Sites | 6 | `DELETE`, `GET`, `PATCH`, `POST` |
| Sélections d'initiatives | 3 | `GET` |
| Types d'évènement | 6 | `DELETE`, `GET`, `PATCH`, `POST` |
| Types de partie prenante | 6 | `DELETE`, `GET`, `PATCH`, `POST` |
| Types de risque | 6 | `DELETE`, `GET`, `PATCH`, `POST` |
| Typologies | 6 | `DELETE`, `GET`, `PATCH`, `POST` |
| Unités de mesure | 3 | `GET` |
| Utilisateurs | 6 | `DELETE`, `GET`, `PATCH`, `POST` |
| À propos de l'API | 1 | `GET` |
| Échelles de mesure | 3 | `GET` |
| Évènements générateurs | 9 | `DELETE`, `GET`, `PATCH`, `POST` |

---

## 3. Catalogue complet des 208 endpoints

### Aides à la déclaration d'initiatives (3)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/idea-submission-guidances` | Lister les aides à la déclaration | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `GET` | `/api/v1/idea-submission-guidances/count` | Compter les aides à la déclaration | Query: `filter` | `200` |
| `GET` | `/api/v1/idea-submission-guidances/{id}` | Obtenir une aide à la déclaration d'initiatives | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |

### Axes (9)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/plans` | Lister les axes | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `POST` | `/api/v1/plans` | Créer un axe | Body: `title*`, `ref_lang`, `confidential`, `priority`, `synopsis`, `description`, `description_resources`, `constraints` (+13) | `201` |
| `GET` | `/api/v1/plans/count` | Compter les axes | Query: `filter` | `200` |
| `DELETE` | `/api/v1/plans/{id}` | Supprimer un axe | — | `204` |
| `GET` | `/api/v1/plans/{id}` | Obtenir un axe | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/plans/{id}` | Modifier un axe | Body: `title`, `confidential`, `priority`, `synopsis`, `description`, `constraints`, `requirements`, `sponsor` (+9) | `204` |
| `POST` | `/api/v1/plans/{id}/resources` | Modifier un axe – Ajouter une ressource | Query: `field` ; Body: `file*`, `title`, `description`, `url*`, `title`, `description`, `idea*`, `title` (+1) | `201` |
| `DELETE` | `/api/v1/plans/{id}/resources/{resource_id}` | Modifier un axe – Supprimer une ressource | — | `204` |
| `PATCH` | `/api/v1/plans/{id}/resources/{resource_id}` | Modifier un axe – Modifier une ressource | Body: `file`, `title`, `description`, `url`, `title`, `description`, `idea`, `title` (+1) | `200` |

### Catégories (6)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/categories` | Lister les catégories | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `POST` | `/api/v1/categories` | Créer une catégorie | Body: `title*`, `ref_lang`, `approver`, `archived`, `followed` | `201` |
| `GET` | `/api/v1/categories/count` | Compter les catégories | Query: `filter` | `200` |
| `DELETE` | `/api/v1/categories/{id}` | Supprimer une catégorie | — | `204` |
| `GET` | `/api/v1/categories/{id}` | Obtenir une catégorie | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/categories/{id}` | Modifier une catégorie | Body: `title`, `approver`, `archived`, `followed` | `204` |

### Demandes d'inscription (3)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/user-registration-requests` | Lister les demandes d'inscription | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `GET` | `/api/v1/user-registration-requests/count` | Compter les demandes d'inscription | Query: `filter` | `200` |
| `GET` | `/api/v1/user-registration-requests/{id}` | Obtenir une demande d'inscription | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |

### Initiatives (13)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/ideas` | Lister les initiatives | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `POST` | `/api/v1/ideas` | Publier une nouvelle initiative | Body: `title*`, `plan*`, `author`, `authors`, `targeted_sites`, `targeted_organizations`, `targeted_processes`, `targeted_products` (+23) | `201` |
| `GET` | `/api/v1/ideas/count` | Compter les initiatives | Query: `filter` | `200` |
| `POST` | `/api/v1/ideas/draft` | Créer une initiative brouillon | Body: `title*`, `plan`, `author`, `authors`, `targeted_sites`, `targeted_organizations`, `targeted_processes`, `targeted_products` (+22) | `201` |
| `GET` | `/api/v1/ideas/post-input-availability` | Obtenir des informations sur les propriétés disponibles pour la création d'une initiative | Query: `plan` | `200` |
| `DELETE` | `/api/v1/ideas/{id}` | Supprimer une initiative | — | `204` |
| `GET` | `/api/v1/ideas/{id}` | Obtenir une initiative | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/ideas/{id}` | Modifier une initiative | Body: `title`, `plan`, `author`, `authors`, `targeted_sites`, `targeted_organizations`, `targeted_processes`, `targeted_products` (+20) | `204` |
| `GET` | `/api/v1/ideas/{id}/patch-input-availability` | Obtenir des informations sur les propriétés disponibles pour la mise à jour d'une initiative | Query: `plan` | `200` |
| `POST` | `/api/v1/ideas/{id}/publish` | Publier une initiative brouillon | Body: `approver`, `comment`, `comment_resources` | `200` |
| `POST` | `/api/v1/ideas/{id}/resources` | Modifier une initiative – Ajouter une ressource | Query: `field` ; Body: `file*`, `title`, `description`, `url*`, `title`, `description`, `idea*`, `title` (+1) | `201` |
| `DELETE` | `/api/v1/ideas/{id}/resources/{resource_id}` | Modifier une initiative – Supprimer une ressource | — | `204` |
| `PATCH` | `/api/v1/ideas/{id}/resources/{resource_id}` | Modifier une initiative – Modifier une ressource | Body: `file`, `title`, `description`, `url`, `title`, `description`, `idea`, `title` (+1) | `200` |

### Initiatives — Analyse d'opportunité (8)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `DELETE` | `/api/v1/ideas/{id}/opportunity-analysis` | Supprimer l'analyse d'opportunité d'une initiative | — | `204` |
| `GET` | `/api/v1/ideas/{id}/opportunity-analysis` | Obtenir l'analyse d'opportunité d'une initiative | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/ideas/{id}/opportunity-analysis` | Corriger l'analyse d'opportunité d'une initiative | Body: `benefits_scale`, `benefits_measures`, `achievability_scale`, `achievability_measures`, `benefits_rating`, `achievability_rating`, `comment` | `200` |
| `PUT` | `/api/v1/ideas/{id}/opportunity-analysis` | Créer ou remplacer l'analyse d'opportunité d'une initiative | Body: `benefits_scale`, `benefits_measures`, `achievability_scale`, `achievability_measures`, `benefits_rating`, `achievability_rating`, `comment`, `comment_resources` | `` |
| `PATCH` | `/api/v1/ideas/{id}/opportunity-analysis/criteria/{criterion_id}` | Modifier la valeur d'un critère de l'analyse d'opportunité | Body: `value*`, `update_rating` | `204` |
| `POST` | `/api/v1/ideas/{id}/opportunity-analysis/resources` | Corriger l'analyse d'opportunité d'une initiative – Ajouter une ressource | Body: `file*`, `title`, `description`, `url*`, `title`, `description`, `idea*`, `title` (+1) | `201` |
| `DELETE` | `/api/v1/ideas/{id}/opportunity-analysis/resources/{resource_id}` | Corriger l'analyse d'opportunité d'une initiative – Supprimer une ressource | — | `204` |
| `PATCH` | `/api/v1/ideas/{id}/opportunity-analysis/resources/{resource_id}` | Corriger l'analyse d'opportunité d'une initiative – Modifier une ressource | Body: `file`, `title`, `description`, `url`, `title`, `description`, `idea`, `title` (+1) | `200` |

### Initiatives — Contributions (4)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/ideas/{id}/contributions` | Obtenir les contributions d'une initiative | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `POST` | `/api/v1/ideas/{id}/contributions` | Apporter une contribution à une initiative | Body: `text*`, `resources`, `sentiment` | `201` |
| `DELETE` | `/api/v1/ideas/{id}/contributions/{contribution_id}` | Supprimer une contribution | — | `204` |
| `GET` | `/api/v1/ideas/{id}/contributions/{contribution_id}` | Obtenir une contribution | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |

### Initiatives — Mise en œuvre (4)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/ideas/{id}/implementation` | Obtenir des informations sur la mise en œuvre d'une initiative | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/ideas/{id}/implementation` | Modifier les informations de mise en œuvre d'une initiative | Body: `implementation_coordinator`, `time_range`, `priority` | `204` |
| `GET` | `/api/v1/ideas/{id}/implementation/progress` | Obtenir l'état d'avancement de la mise en œuvre d'une initiative | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `POST` | `/api/v1/ideas/{id}/implementation/progress` | Mettre à jour l'avancement de la mise en œuvre d'une initiative | Body: `percent`, `confidence`, `comment`, `resources` | `201` |

### Initiatives — Mémo (3)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `DELETE` | `/api/v1/ideas/{id}/memo` | Supprimer le mémo d'une initiative | — | `204` |
| `GET` | `/api/v1/ideas/{id}/memo` | Obtenir le mémo d'une initiative | — | `200` |
| `PUT` | `/api/v1/ideas/{id}/memo` | Définir un mémo pour une initiative | Body: `memo*` | `201` |

### Initiatives — Plan d'action (23)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/ideas/{id}/action-plan/phase-template` | Obtenir le plan de phases d'un plan d'action | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PUT` | `/api/v1/ideas/{id}/action-plan/phase-template` | Spécifier le plan de phases d'un plan d'action | Body: `phases_template*` | `200` |
| `GET` | `/api/v1/ideas/{id}/action-plan/phase-template/{phase_id}/tasks` | Obtenir les tâches d'une phase d'un plan d'action | Query: `props`, `notify_props_errors`, `pop_null_values`, `filter` | `200` |
| `PUT` | `/api/v1/ideas/{id}/action-plan/phase-template/{phase_id}/tasks` | Définir les tâches d'une phase d'un plan d'action | Body: `tasks*` | `200` |
| `GET` | `/api/v1/ideas/{id}/action-plan/progress` | Obtenir l'état d'avancement d'un plan d'action | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `GET` | `/api/v1/ideas/{id}/action-plan/sections` | Obtenir la liste des lots définis pour un plan d'action | — | `200` |
| `POST` | `/api/v1/ideas/{id}/action-plan/sections` | Ajouter un lot de tâches à un plan d'action | Body: `title*`, `tasks` | `200` |
| `PUT` | `/api/v1/ideas/{id}/action-plan/sections` | Définir les lots de tâches d'un plan d'action | Body: `sections*` | `200` |
| `DELETE` | `/api/v1/ideas/{id}/action-plan/sections/{section_id}` | Supprimer un lot d'un plan d'action | Body: `task_handling` | `204` |
| `GET` | `/api/v1/ideas/{id}/action-plan/sections/{section_id}/tasks` | Obtenir les tâches d'un lot d'un plan d'action | Query: `props`, `notify_props_errors`, `pop_null_values`, `filter` | `200` |
| `PUT` | `/api/v1/ideas/{id}/action-plan/sections/{section_id}/tasks` | Définir les tâches d'un lot d'un plan d'action | Body: `tasks*` | `200` |
| `DELETE` | `/api/v1/ideas/{id}/action-plan/tasks` | Supprimer le plan d'action d'une initiative | — | `204` |
| `GET` | `/api/v1/ideas/{id}/action-plan/tasks` | Obtenir les tâches d'un plan d'action | Query: `props`, `notify_props_errors`, `pop_null_values`, `filter` | `200` |
| `POST` | `/api/v1/ideas/{id}/action-plan/tasks` | Ajouter une tâche à un plan d'action | Body: `title*`, `phase`, `section`, `owner`, `time_range`, `description`, `description_resources` | `201` |
| `PUT` | `/api/v1/ideas/{id}/action-plan/tasks` | Définir les tâches d'un plan d'action | Body: `tasks*` | `200` |
| `DELETE` | `/api/v1/ideas/{id}/action-plan/tasks/{task_id}` | Supprimer une tâche issue d'un plan d'action | — | `204` |
| `GET` | `/api/v1/ideas/{id}/action-plan/tasks/{task_id}` | Obtenir une tâche issue d'un plan d'action | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/ideas/{id}/action-plan/tasks/{task_id}` | Corriger une tâche issue d'un plan d'action | Body: `title*`, `phase`, `section`, `owner`, `time_range`, `description` | `204` |
| `GET` | `/api/v1/ideas/{id}/action-plan/tasks/{task_id}/progress` | Obtenir l'état d'avancement d'une tâche issue d'un plan d'action | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `POST` | `/api/v1/ideas/{id}/action-plan/tasks/{task_id}/progress` | Mettre à jour l'avancement d'une tâche issue d'un plan d'action | Body: `percent`, `confidence`, `comment`, `resources` | `201` |
| `POST` | `/api/v1/ideas/{id}/action-plan/tasks/{task_id}/resources` | Corriger une tâche issue d'un plan d'action – Ajouter une ressource | Body: `file*`, `title`, `description`, `url*`, `title`, `description`, `idea*`, `title` (+1) | `201` |
| `DELETE` | `/api/v1/ideas/{id}/action-plan/tasks/{task_id}/resources/{resource_id}` | Corriger une tâche issue d'un plan d'action – Supprimer une ressource | — | `204` |
| `PATCH` | `/api/v1/ideas/{id}/action-plan/tasks/{task_id}/resources/{resource_id}` | Corriger une tâche issue d'un plan d'action – Modifier une ressource | Body: `file`, `title`, `description`, `url`, `title`, `description`, `idea`, `title` (+1) | `200` |

### Initiatives — Tags (4)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `DELETE` | `/api/v1/ideas/{id}/tags` | Supprimer des tags d'une initiative | Query: `tags` | `204` |
| `GET` | `/api/v1/ideas/{id}/tags` | Obtenir les tags d'une initiative | — | `200` |
| `POST` | `/api/v1/ideas/{id}/tags` | Ajouter des tags à une initiative | Body: `tags*` | `204` |
| `PUT` | `/api/v1/ideas/{id}/tags` | Définir les tags d'une initiative | Body: `tags*` | `204` |

### Initiatives — Traitement (Workflow) (12)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/ideas/{id}/stages/approve--end-implementation` | Approuver une initiative dont la mise en œuvre est terminée | Body: `implementation_coordinator*`, `status`, `comment*`, `comment_resources` | `201` |
| `POST` | `/api/v1/ideas/{id}/stages/approve--launch-implementation` | Approuver une initiative avec planification de sa mise en œuvre | Body: `implementation_coordinator*`, `time_range*`, `priority`, `comment`, `comment_resources` | `201` |
| `POST` | `/api/v1/ideas/{id}/stages/approve--request-implementation-schedule` | Approuver une initiative et demander la planification de sa mise en œuvre | Body: `addressee*`, `due_date`, `comment`, `comment_resources` | `201` |
| `POST` | `/api/v1/ideas/{id}/stages/change-approver` | Transférer une initiative à un autre approbateur | Body: `addressee*`, `comment*`, `comment_resources` | `201` |
| `POST` | `/api/v1/ideas/{id}/stages/close` | Clôturer une initiative | Body: `status`, `comment*`, `comment_resources` | `201` |
| `DELETE` | `/api/v1/ideas/{id}/stages/current` | Annuler la dernière étape de traitement d'une initiative | — | `200` |
| `GET` | `/api/v1/ideas/{id}/stages/current` | Obtenir l'étape en cours d'une initiative | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `POST` | `/api/v1/ideas/{id}/stages/end-implementation` | Terminer la mise en œuvre d'une initiative | Body: `status`, `comment*`, `comment_resources` | `201` |
| `POST` | `/api/v1/ideas/{id}/stages/reject` | Rejeter une initiative | Body: `comment*`, `comment_resources`, `rejection_reason` | `201` |
| `POST` | `/api/v1/ideas/{id}/stages/request-details` | Demander un approfondissement au rédacteur d'une initiative | Body: `due_date`, `comment*`, `comment_resources` | `201` |
| `POST` | `/api/v1/ideas/{id}/stages/request-expertise` | Demander l'expertise d'une initiative | Body: `addressee*`, `due_date`, `comment*`, `comment_resources` | `201` |
| `POST` | `/api/v1/ideas/{id}/stages/standby` | Mettre une initiative en attente | Body: `due_date*`, `comment*`, `comment_resources` | `201` |

### Initiatives — Vérifications d'efficacité (4)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/ideas/{id}/audits` | Obtenir les vérifications d'efficacité d'une initiative | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `POST` | `/api/v1/ideas/{id}/audits` | Apporter une vérification d'efficacité à une initiative | Body: `text*`, `resources`, `sentiment` | `201` |
| `DELETE` | `/api/v1/ideas/{id}/audits/{audit_id}` | Supprimer une vérification d'efficacité | — | `204` |
| `GET` | `/api/v1/ideas/{id}/audits/{audit_id}` | Obtenir une vérification d'efficacité | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |

### Modèles de plan d'action (3)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/action-plan-templates` | Lister les modèles de plan d'action | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `GET` | `/api/v1/action-plan-templates/count` | Compter les modèles de plan d'action | Query: `filter` | `200` |
| `GET` | `/api/v1/action-plan-templates/{id}` | Obtenir un modèle de plan d'action | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |

### Motifs de non-recevabilité (3)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/idea-rejection-reasons` | Lister les motifs de non-recevabilité | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `GET` | `/api/v1/idea-rejection-reasons/count` | Compter les motifs de non-recevabilité | Query: `filter` | `200` |
| `GET` | `/api/v1/idea-rejection-reasons/{id}` | Obtenir un motif de non-recevabilité | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |

### Paramètres régionaux (1)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/locale-settings/timezones` | Lister les fuseaux horaires | Query: `group` | `200` |

### Parties prenantes (11)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/stakeholders` | Lister les parties prenantes | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `POST` | `/api/v1/stakeholders` | Créer une partie prenante | Body: `title*`, `ref_lang`, `approver`, `type`, `description`, `contacts`, `archived`, `followed` | `201` |
| `GET` | `/api/v1/stakeholders/count` | Compter les parties prenantes | Query: `filter` | `200` |
| `DELETE` | `/api/v1/stakeholders/{id}` | Supprimer une partie prenante | — | `204` |
| `GET` | `/api/v1/stakeholders/{id}` | Obtenir une partie prenante | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/stakeholders/{id}` | Modifier une partie prenante | Body: `title`, `approver`, `type`, `description`, `contacts`, `archived`, `followed` | `204` |
| `GET` | `/api/v1/stakeholders/{id}/contacts` | Obtenir les contacts d'une partie prenante | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `POST` | `/api/v1/stakeholders/{id}/contacts` | Ajouter un contact à une partie prenante | Body: `last_name*`, `first_name`, `job_title`, `email`, `phone`, `address` | `201` |
| `DELETE` | `/api/v1/stakeholders/{id}/contacts/{contact_id}` | Supprimer un contact d'une partie prenante | — | `204` |
| `GET` | `/api/v1/stakeholders/{id}/contacts/{contact_id}` | Obtenir un contact d'une partie prenante | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/stakeholders/{id}/contacts/{contact_id}` | Modifier un contact d'une partie prenante | Body: `last_name`, `first_name`, `job_title`, `email`, `phone`, `address` | `200` |

### Pays (1)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/countries` | Lister les pays | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |

### Perspectives (3)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/perspectives` | Lister les perspectives | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `GET` | `/api/v1/perspectives/count` | Compter les perspectives | Query: `filter` | `200` |
| `GET` | `/api/v1/perspectives/{id}` | Obtenir une perspective | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |

### Plans de phases (3)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/phases-templates` | Lister les plans de phases | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `GET` | `/api/v1/phases-templates/count` | Compter les plans de phases | Query: `filter` | `200` |
| `GET` | `/api/v1/phases-templates/{id}` | Obtenir un plan de phases | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |

### Processus (6)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/processes` | Lister les processus | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `POST` | `/api/v1/processes` | Créer un processus | Body: `title*`, `ref_lang`, `top`, `approver`, `ext_id`, `archived` | `201` |
| `GET` | `/api/v1/processes/count` | Compter les processus | Query: `filter` | `200` |
| `DELETE` | `/api/v1/processes/{id}` | Supprimer un processus | — | `204` |
| `GET` | `/api/v1/processes/{id}` | Obtenir un processus | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/processes/{id}` | Modifier un processus | Body: `title`, `top`, `approver`, `ext_id`, `archived` | `204` |

### Produits (6)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/products` | Lister les produits | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `POST` | `/api/v1/products` | Créer un produit | Body: `title*`, `ref_lang`, `top`, `approver`, `archived` | `201` |
| `GET` | `/api/v1/products/count` | Compter les produits | Query: `filter` | `200` |
| `DELETE` | `/api/v1/products/{id}` | Supprimer un produit | — | `204` |
| `GET` | `/api/v1/products/{id}` | Obtenir un produit | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/products/{id}` | Modifier un produit | Body: `title`, `top`, `approver`, `archived` | `204` |

### Profils d'accès (3)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/user-profiles` | Lister les profils d'accès | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `GET` | `/api/v1/user-profiles/count` | Compter les profils d'accès | Query: `filter` | `200` |
| `GET` | `/api/v1/user-profiles/{id}` | Obtenir un profil d'accès | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |

### Risques (9)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/risks` | Lister les risques | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `POST` | `/api/v1/risks` | Créer un risque | Body: `title*`, `ref_lang`, `type`, `status`, `confidential`, `sponsor`, `controller*`, `concerned_sites` (+13) | `201` |
| `GET` | `/api/v1/risks/count` | Compter les risques | Query: `filter` | `200` |
| `DELETE` | `/api/v1/risks/{id}` | Supprimer un risque | — | `204` |
| `GET` | `/api/v1/risks/{id}` | Obtenir un risque | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/risks/{id}` | Modifier un risque | Body: `title`, `type`, `status`, `confidential`, `sponsor`, `controller`, `concerned_sites`, `concerned_organizations` (+9) | `204` |
| `POST` | `/api/v1/risks/{id}/resources` | Modifier un risque – Ajouter une ressource | Query: `field` ; Body: `file*`, `title`, `description`, `url*`, `title`, `description`, `idea*`, `title` (+1) | `201` |
| `DELETE` | `/api/v1/risks/{id}/resources/{resource_id}` | Modifier un risque – Supprimer une ressource | — | `204` |
| `PATCH` | `/api/v1/risks/{id}/resources/{resource_id}` | Modifier un risque – Modifier une ressource | Body: `file`, `title`, `description`, `url`, `title`, `description`, `idea`, `title` (+1) | `200` |

### Référentiel de l'API (2)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/reference/endpoints` | Obtenir la liste des services disponibles pour cette API | Query: `domain`, `method`, `url` | `200` |
| `GET` | `/api/v1/reference/endpoints/{endpoint_id}` | Obtenir des informations sur un service de l'API | — | `200` |

### Services (6)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/organizations` | Lister les services | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `POST` | `/api/v1/organizations` | Créer un service | Body: `title*`, `ref_lang`, `top`, `approver`, `ext_id`, `archived` | `201` |
| `GET` | `/api/v1/organizations/count` | Compter les services | Query: `filter` | `200` |
| `DELETE` | `/api/v1/organizations/{id}` | Supprimer un service | — | `204` |
| `GET` | `/api/v1/organizations/{id}` | Obtenir un service | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/organizations/{id}` | Modifier un service | Body: `title`, `top`, `approver`, `ext_id`, `archived` | `204` |

### Sites (6)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/sites` | Lister les sites | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `POST` | `/api/v1/sites` | Créer un site | Body: `title*`, `ref_lang`, `approver`, `address`, `zipcode`, `city`, `country`, `tz` (+3) | `201` |
| `GET` | `/api/v1/sites/count` | Compter les sites | Query: `filter` | `200` |
| `DELETE` | `/api/v1/sites/{id}` | Supprimer un site | — | `204` |
| `GET` | `/api/v1/sites/{id}` | Obtenir un site | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/sites/{id}` | Modifier un site | Body: `title`, `approver`, `address`, `zipcode`, `city`, `country`, `tz`, `spoken_lang` (+2) | `204` |

### Sélections d'initiatives (3)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/idea-selections` | Lister les sélections d'initiatives | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `GET` | `/api/v1/idea-selections/count` | Compter les sélections d'initiatives | Query: `filter` | `200` |
| `GET` | `/api/v1/idea-selections/{id}` | Obtenir une sélection d'initiatives | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |

### Types d'évènement (6)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/event-types` | Lister les types d'évènement | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `POST` | `/api/v1/event-types` | Créer un type d'évènement | Body: `title*`, `ref_lang`, `top`, `archived` | `201` |
| `GET` | `/api/v1/event-types/count` | Compter les types d'évènement | Query: `filter` | `200` |
| `DELETE` | `/api/v1/event-types/{id}` | Supprimer un type d'évènement | — | `204` |
| `GET` | `/api/v1/event-types/{id}` | Obtenir un type d'évènement | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/event-types/{id}` | Modifier un type d'évènement | Body: `title`, `top`, `archived` | `204` |

### Types de partie prenante (6)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/stakeholder-types` | Lister les types de partie prenante | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `POST` | `/api/v1/stakeholder-types` | Créer un type de partie prenante | Body: `title*`, `ref_lang`, `top`, `archived` | `201` |
| `GET` | `/api/v1/stakeholder-types/count` | Compter les types de partie prenante | Query: `filter` | `200` |
| `DELETE` | `/api/v1/stakeholder-types/{id}` | Supprimer un type de partie prenante | — | `204` |
| `GET` | `/api/v1/stakeholder-types/{id}` | Obtenir un type de partie prenante | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/stakeholder-types/{id}` | Modifier un type de partie prenante | Body: `title`, `top`, `archived` | `204` |

### Types de risque (6)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/risk-types` | Lister les types de risque | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `POST` | `/api/v1/risk-types` | Créer un type de risque | Body: `title*`, `ref_lang`, `top`, `archived` | `201` |
| `GET` | `/api/v1/risk-types/count` | Compter les types de risque | Query: `filter` | `200` |
| `DELETE` | `/api/v1/risk-types/{id}` | Supprimer un type de risque | — | `204` |
| `GET` | `/api/v1/risk-types/{id}` | Obtenir un type de risque | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/risk-types/{id}` | Modifier un type de risque | Body: `title`, `top`, `archived` | `204` |

### Typologies (6)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/classes` | Lister les typologies | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `POST` | `/api/v1/classes` | Créer une typologie | Body: `title*`, `ref_lang`, `top`, `approver`, `archived`, `followed` | `201` |
| `GET` | `/api/v1/classes/count` | Compter les typologies | Query: `filter` | `200` |
| `DELETE` | `/api/v1/classes/{id}` | Supprimer une typologie | — | `204` |
| `GET` | `/api/v1/classes/{id}` | Obtenir une typologie | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/classes/{id}` | Modifier une typologie | Body: `title`, `top`, `approver`, `archived`, `followed` | `204` |

### Unités de mesure (3)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/eval-units` | Lister les unités de mesure | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `GET` | `/api/v1/eval-units/count` | Compter les unités de mesure | Query: `filter` | `200` |
| `GET` | `/api/v1/eval-units/{id}` | Obtenir une unité de mesure | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |

### Utilisateurs (6)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/users` | Lister les utilisateurs | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `POST` | `/api/v1/users` | Créer un utilisateur | Body: `last_name*`, `first_name`, `job_title`, `expertise_area`, `email`, `phone`, `lang`, `manager` (+9) | `201` |
| `GET` | `/api/v1/users/count` | Compter les utilisateurs | Query: `filter` | `200` |
| `DELETE` | `/api/v1/users/{id}` | Supprimer un utilisateur | — | `204` |
| `GET` | `/api/v1/users/{id}` | Obtenir un utilisateur | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/users/{id}` | Modifier un utilisateur | Body: `last_name`, `first_name`, `job_title`, `expertise_area`, `email`, `phone`, `lang`, `manager` (+9) | `204` |

### À propos de l'API (1)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/about` | Obtenir des informations au sujet de cette API | — | `200` |

### Échelles de mesure (3)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/eval-scales` | Lister les échelles de mesure | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `GET` | `/api/v1/eval-scales/count` | Compter les échelles de mesure | Query: `filter` | `200` |
| `GET` | `/api/v1/eval-scales/{id}` | Obtenir une échelle | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |

### Évènements générateurs (9)

| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/events` | Lister les évènements | Query: `filter`, `offset`, `page_size`, `count`, `props`, `notify_props_errors` | `200` |
| `POST` | `/api/v1/events` | Créer un évènement | Body: `title*`, `ref_lang`, `approver`, `type`, `date`, `description`, `description_resources`, `archived` (+1) | `201` |
| `GET` | `/api/v1/events/count` | Compter les évènements | Query: `filter` | `200` |
| `DELETE` | `/api/v1/events/{id}` | Supprimer un évènement | — | `204` |
| `GET` | `/api/v1/events/{id}` | Obtenir un évènement | Query: `props`, `notify_props_errors`, `pop_null_values` | `200` |
| `PATCH` | `/api/v1/events/{id}` | Modifier un évènement | Body: `title`, `approver`, `type`, `date`, `description`, `archived`, `followed` | `204` |
| `POST` | `/api/v1/events/{id}/resources` | Modifier un évènement – Ajouter une ressource | Body: `file*`, `title`, `description`, `url*`, `title`, `description`, `idea*`, `title` (+1) | `201` |
| `DELETE` | `/api/v1/events/{id}/resources/{resource_id}` | Modifier un évènement – Supprimer une ressource | — | `204` |
| `PATCH` | `/api/v1/events/{id}/resources/{resource_id}` | Modifier un évènement – Modifier une ressource | Body: `file`, `title`, `description`, `url`, `title`, `description`, `idea`, `title` (+1) | `200` |

---

## 4. Modèles de données principaux (`components.schemas`)

La spécification OpenAPI complète (`docs/openapi.json`) définit **125 schémas**.

| Modèle | Nb propriétés | Aperçu des propriétés |
| :--- | :---: | :--- |
| `APIEndpoint` | 4 | `title`, `method`, `url`, `link` |
| `APIRef.Class` | 3 | `name`, `description`, `properties` |
| `APIRef.EnumValue` | 2 | `value`, `label` |
| `APIRef.HTTPHeader` | 7 | `name`, `description`, `type`, `alt_types`, `required`, `default_value`, `see` |
| `APIRef.InputParam` | 8 | `name`, `description`, `type`, `reset_value`, `alt_types`, `required`, `default_value`, `see` |
| `APIRef.ObjectProperty` | 8 | `name`, `description`, `type`, `reset_value`, `alt_types`, `required`, `default_value`, `see` |
| `APIRef.PathParam` | 4 | `name`, `description`, `type`, `see` |
| `APIRef.PayloadFormat` | 4 | `title`, `description`, `params`, `supported_content_types` |
| `APIRef.RelatedService` | 2 | `description`, `link` |
| `APIRef.Response` | 5 | `occurs_when`, `http_code`, `content_type`, `content_description`, `content_properties` |
| `APIRef.ResponseProperty` | 5 | `name`, `description`, `type`, `alt_types`, `see` |
| `APIRef.Type` | 11 | `name`, `description`, `details`, `properties`, `array_keys`, `array_value_types`, `min_value`, `max_value`, `format`, `max_length`, … (+1) |
| `APIRef.TypeInfo` | 4 | `description`, `type`, `reset_value`, `see` |
| `About.API` | 5 | `version`, `version_number`, `latest_version`, `latest_version_number`, `endpoints_reference` |
| `About.Application` | 3 | `name`, `version`, `version_number` |
| `ActionPlanTemplate` | 10 | `id`, `reference`, `title`, `ref_lang`, `phases_template`, `tasks`, `archived`, `creation_time`, `update_time`, `updated_by` |
| `ActionPlanTemplate.DateRelToProjectStart` | 2 | `base`, `offset` |
| `ActionPlanTemplate.DateRelToTask` | 3 | `base`, `task`, `offset` |
| `ActionPlanTemplate.Task` | 13 | `id`, `reference`, `title`, `ref_lang`, `description`, `phase`, `owner`, `start_date`, `start_relation`, `duration`, … (+3) |
| `ActionPlanTemplate.TaskFilter` | 7 | `id`, `title`, `owner`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time` |
| `ActionPlanTemplateFilter` | 12 | `id`, `title`, `keywords`, `phases_template`, `task`, `valid`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time`, … (+2) |
| `Audit` | 9 | `id`, `reference`, `author`, `text`, `resources`, `sentiment`, `creation_time`, `update_time`, `updated_by` |
| `AuditFilter` | 5 | `id`, `keywords`, `author`, `creation_time`, `update_time` |
| `AuditRequestFilter` | 8 | `id`, `issuer`, `addressee`, `keywords`, `response`, `expired`, `creation_time`, `update_time` |
| `Base64Upload` | 3 | `base64_encoded`, `filename`, `content_type` |
| `ClassificationCategory` | 10 | `id`, `reference`, `title`, `ref_lang`, `approver`, `archived`, `followed`, `creation_time`, `update_time`, `updated_by` |
| `ClassificationCategoryFilter` | 10 | `id`, `title`, `approver`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time`, `archived`, `followed`, `deletable` |
| `ClassificationClass` | 11 | `id`, `reference`, `title`, `ref_lang`, `top`, `approver`, `archived`, `followed`, `creation_time`, `update_time`, … (+1) |
| `ClassificationClassFilter` | 11 | `id`, `title`, `top`, `approver`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time`, `archived`, `followed`, … (+1) |
| `ClassificationEvent` | 14 | `id`, `reference`, `title`, `ref_lang`, `approver`, `type`, `date`, `description`, `description_resources`, `archived`, … (+4) |
| `ClassificationEventFilter` | 13 | `id`, `title`, `keywords`, `date`, `type`, `approver`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time`, … (+3) |
| `ClassificationEventType` | 9 | `id`, `reference`, `title`, `ref_lang`, `top`, `archived`, `creation_time`, `update_time`, `updated_by` |
| `ClassificationEventTypeFilter` | 9 | `id`, `title`, `top`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time`, `archived`, `deletable` |
| `Contribution` | 9 | `id`, `reference`, `author`, `text`, `resources`, `sentiment`, `creation_time`, `update_time`, `updated_by` |
| `ContributionFilter` | 5 | `id`, `keywords`, `author`, `creation_time`, `update_time` |
| `ContributionRequestFilter` | 8 | `id`, `issuer`, `addressee`, `keywords`, `response`, `expired`, `creation_time`, `update_time` |
| `Country` | 4 | `id`, `reference`, `title`, `code` |
| `CountryFilter` | 3 | `id`, `title`, `code` |
| `CriticalityAnalysis` | 13 | `author`, `impact_scale`, `impact_measures`, `probability_scale`, `probability_measures`, `impact_rating`, `probability_rating`, `criticality_rating`, `comment`, `comment_resources`, … (+3) |
| `CriticalityAnalysisFilter` | 9 | `impact_rating`, `probability_rating`, `criticality_rating`, `criticality_zone`, `impact_scale`, `probability_scale`, `author`, `creation_time`, `update_time` |
| `CriticalityMeasure` | 5 | `criterion`, `value`, `creation_time`, `update_time`, `updated_by` |
| `DateRange` | 2 | `start`, `end` |
| `DateRangeFilter` | 2 | `from`, `to` |
| `EvaluationUnit` | 14 | `id`, `reference`, `title`, `ref_lang`, `symbol`, `min`, `max`, `direction`, `decimals`, `choices`, … (+4) |
| `EvaluationUnitFilter` | 8 | `id`, `title`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time`, `archived`, `deletable` |
| `ExpertiseFilter` | 7 | `id`, `keywords`, `author`, `confidential`, `published`, `creation_time`, `update_time` |
| `ExtIDLookup` | 1 | `ext_id` |
| `HierarchyFilter` | 3 | `filter`, `depth`, `include_top` |
| `IDedObject` | 1 | `id` |
| `Idea` | 66 | `id`, `reference`, `title`, `plan`, `editor`, `author`, `authors`, `origin_site`, `origin_organization`, `origin_process`, … (+56) |
| `Idea.SubmissionOptions` | 3 | `approver`, `comment`, `comment_resources` |
| `IdeaFilter` | 54 | `id`, `title`, `keywords`, `plan`, `author`, `editor`, `approver`, `person_in_charge`, `sponsor`, `additional_member`, … (+44) |
| `IdeaImplementation` | 14 | `implementation_coordinator`, `start`, `end`, `actual_end`, `priority`, `progress`, `manual_progress`, `phases_template`, `sections`, `running_phase`, … (+4) |
| `IdeaImplementation.ImplementationSection` | 3 | `id`, `title`, `tasks` |
| `IdeaImplementationFilter` | 16 | `coordinator`, `priority`, `status`, `start_date`, `end_date`, `actual_end_date`, `last_progress_time`, `rescheduled`, `completed_on_time`, `duration`, … (+6) |
| `IdeaInputProperty` | 4 | `label`, `available`, `required`, `helper` |
| `IdeaSelection` | 11 | `id`, `reference`, `title`, `ref_lang`, `description`, `type`, `status`, `archived`, `creation_time`, `update_time`, … (+1) |
| `IdeaSelectionFilter` | 12 | `id`, `title`, `keywords`, `type`, `status`, `content_approved`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time`, … (+2) |
| `IdeaStage` | 13 | `id`, `reference`, `status`, `issuer`, `addressee`, `due_date`, `comment`, `comment_resources`, `rejection_reason`, `archived`, … (+3) |
| `IdeaStageFilter` | 9 | `id`, `status`, `issuer`, `addressee`, `due_date`, `rejection_reason`, `creation_time`, `update_time`, `archived` |
| `IdeaSubmissionHelper` | 22 | `id`, `reference`, `title`, `ref_lang`, `title_helper`, `context_helper`, `description_helper`, `benefits_helper`, `plan_helper`, `targeted_site_helper`, … (+12) |
| `IdeaSubmissionHelperFilter` | 10 | `id`, `title`, `keywords`, `valid`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time`, `archived`, `deletable` |
| `IdeaVoteFilter` | 2 | `value`, `date` |
| `ImplementationPhase` | 4 | `id`, `reference`, `title`, `ref_lang` |
| `ImplementationPhaseTemplate` | 10 | `id`, `reference`, `title`, `ref_lang`, `description`, `phases`, `archived`, `creation_time`, `update_time`, `updated_by` |
| `ImplementationPhaseTemplateFilter` | 10 | `id`, `title`, `keywords`, `valid`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time`, `archived`, `deletable` |
| `ImplementationProgressStatus` | 6 | `percent`, `confidence`, `comment`, `resources`, `time`, `issuer` |
| `ImplementationSection` | 2 | `id`, `title` |
| `ImplementationTask` | 15 | `id`, `reference`, `title`, `phase`, `section`, `owner`, `start`, `end`, `actual_end`, `description`, … (+5) |
| `ImplementationTaskFilter` | 16 | `id`, `title`, `keywords`, `owner`, `phase`, `start_date`, `end_date`, `actual_end_date`, `last_progress_time`, `rescheduled`, … (+6) |
| `Input.IdeaImplementation.ImplementationSection` | 2 | `title`, `tasks` |
| `Input.ImplementationTask` | 7 | `title`, `owner`, `time_range`, `description`, `description_resources`, `phase`, `section` |
| `Input.OpportunityMeasure` | 2 | `criterion`, `value` |
| `Input.Resource.FileUpload` | 3 | `file`, `title`, `description` |
| `Input.Resource.IdeaLink` | 3 | `idea`, `title`, `description` |
| `Input.Resource.RemoteLink` | 3 | `url`, `title`, `description` |
| `Input.StakeholderContact` | 7 | `last_name`, `first_name`, `job_title`, `email`, `phone`, `address`, `id` |
| `OpportunityAnalysis` | 14 | `id`, `reference`, `author`, `benefits_scale`, `benefits_measures`, `achievability_scale`, `achievability_measures`, `benefits_rating`, `achievability_rating`, `comment`, … (+4) |
| `OpportunityAnalysisFilter` | 10 | `id`, `benefits_rating`, `achievability_rating`, `opportunity_zone`, `complete`, `benefits_scale`, `achievability_scale`, `author`, `creation_time`, `update_time` |
| `OpportunityMeasure` | 5 | `criterion`, `value`, `creation_time`, `update_time`, `updated_by` |
| `Organization` | 11 | `id`, `reference`, `title`, `ref_lang`, `top`, `approver`, `ext_id`, `archived`, `creation_time`, `update_time`, … (+1) |
| `OrganizationFilter` | 11 | `id`, `title`, `top`, `approver`, `with_translation_in`, `without_translation_in`, `ext_id`, `creation_time`, `update_time`, `archived`, … (+1) |
| `Perspective` | 11 | `id`, `reference`, `title`, `ref_lang`, `description`, `description_resources`, `sponsor`, `archived`, `creation_time`, `update_time`, … (+1) |
| `PerspectiveFilter` | 10 | `id`, `title`, `keywords`, `sponsor`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time`, `archived`, `deletable` |
| `Plan` | 27 | `id`, `reference`, `title`, `ref_lang`, `confidential`, `priority`, `synopsis`, `description`, `description_resources`, `constraints`, … (+17) |
| `PlanFilter` | 24 | `id`, `title`, `keywords`, `confidential`, `priority`, `sponsor`, `default_approver`, `default_impl_coordinator`, `in_progress`, `awaiting_launch`, … (+14) |
| `PlanScope.Organization` | 3 | `item`, `top_included`, `sub_included` |
| `PlanScope.Process` | 3 | `item`, `top_included`, `sub_included` |
| `PreAnalysisRequestFilter` | 8 | `id`, `issuer`, `addressee`, `keywords`, `response`, `expired`, `creation_time`, `update_time` |
| `ProblemDetails` | 7 | `title`, `severity`, `issuer`, `issue_type`, `issue_code`, `status`, `detail` |
| `Process` | 11 | `id`, `reference`, `title`, `ref_lang`, `top`, `approver`, `ext_id`, `archived`, `creation_time`, `update_time`, … (+1) |
| `ProcessFilter` | 11 | `id`, `title`, `top`, `approver`, `with_translation_in`, `without_translation_in`, `ext_id`, `creation_time`, `update_time`, `archived`, … (+1) |
| `Product` | 10 | `id`, `reference`, `title`, `ref_lang`, `top`, `approver`, `archived`, `creation_time`, `update_time`, `updated_by` |
| `ProductFilter` | 10 | `id`, `title`, `top`, `approver`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time`, `archived`, `deletable` |
| `PropertySet` | 3 | `fields`, `options`, `templates` |
| `RejectionReason` | 8 | `id`, `reference`, `title`, `ref_lang`, `archived`, `creation_time`, `update_time`, `updated_by` |
| `RejectionReasonFilter` | 8 | `id`, `title`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time`, `archived`, `deletable` |
| `Resource` | 6 | `id`, `title`, `description`, `link`, `creation_time`, `update_time` |
| `Risk` | 27 | `id`, `reference`, `title`, `ref_lang`, `type`, `status`, `confidential`, `sponsor`, `controller`, `concerned_sites`, … (+17) |
| `RiskFilter` | 20 | `id`, `title`, `keywords`, `status`, `type`, `sponsor`, `controller`, `confidential`, `scope_site`, `scope_organization`, … (+10) |
| `RiskType` | 8 | `id`, `reference`, `title`, `ref_lang`, `archived`, `creation_time`, `update_time`, `updated_by` |
| `RiskTypeFilter` | 8 | `id`, `title`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time`, `archived`, `deletable` |
| `Scale` | 12 | `id`, `reference`, `title`, `ref_lang`, `description`, `type`, `criteria`, `criteria_sort`, `archived`, `creation_time`, … (+2) |
| `ScaleCriterion` | 15 | `id`, `title`, `ref_lang`, `description`, `unit`, `min_value`, `max_value`, `worst_value`, `best_value`, `direction`, … (+5) |
| `ScaleFilter` | 13 | `id`, `title`, `keywords`, `type`, `unit`, `valid`, `default`, `with_translation_in`, `without_translation_in`, `creation_time`, … (+3) |
| `Site` | 16 | `id`, `reference`, `title`, `ref_lang`, `approver`, `address`, `zipcode`, `city`, `country`, `tz`, … (+6) |
| `SiteFilter` | 13 | `id`, `title`, `keywords`, `country`, `spoken_lang`, `approver`, `with_translation_in`, `without_translation_in`, `ext_id`, `creation_time`, … (+3) |
| `SpreadDownFilter` | 2 | `filter`, `include_children` |
| `SpreadUpDownFilter` | 3 | `filter`, `include_parents`, `include_children` |
| `Stakeholder` | 13 | `id`, `reference`, `title`, `ref_lang`, `approver`, `type`, `description`, `contacts`, `archived`, `followed`, … (+3) |
| `StakeholderContact` | 10 | `id`, `last_name`, `first_name`, `job_title`, `email`, `phone`, `address`, `creation_time`, `update_time`, `updated_by` |
| `StakeholderContactFilter` | 8 | `id`, `name`, `job_title`, `email`, `phone`, `address`, `creation_time`, `update_time` |
| `StakeholderFilter` | 13 | `id`, `title`, `keywords`, `type`, `contact`, `approver`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time`, … (+3) |
| `StakeholderType` | 9 | `id`, `reference`, `title`, `ref_lang`, `top`, `archived`, `creation_time`, `update_time`, `updated_by` |
| `StakeholderTypeFilter` | 9 | `id`, `title`, `top`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time`, `archived`, `deletable` |
| `TimeRangeFilter` | 2 | `from`, `to` |
| `Timezone` | 2 | `id`, `name` |
| `TranslationSearch` | 2 | `lang`, `as` |
| `User` | 19 | `id`, `reference`, `last_name`, `first_name`, `job_title`, `expertise_area`, `email`, `phone`, `lang`, `manager`, … (+9) |
| `UserFilter` | 16 | `id`, `name`, `job_title`, `email`, `lang`, `manager`, `site`, `organization`, `process`, `login`, … (+6) |
| `UserProfile` | 9 | `id`, `reference`, `title`, `ref_lang`, `is_default`, `archived`, `creation_time`, `update_time`, `updated_by` |
| `UserProfileFilter` | 9 | `id`, `title`, `default`, `with_translation_in`, `without_translation_in`, `creation_time`, `update_time`, `archived`, `deletable` |
| `UserSelfRegistrationRequest` | 20 | `id`, `reference`, `last_name`, `first_name`, `job_title`, `expertise_area`, `email`, `phone`, `lang`, `tz`, … (+10) |
| `UserSelfRegistrationRequestFilter` | 9 | `id`, `name`, `lang`, `issuer_ip_address`, `request_status`, `request_expired`, `request_expiration_time`, `creation_time`, `update_time` |
| `ValueRange` | 4 | `min`, `min_included`, `max`, `max_included` |
