# Security Policy / Politique de sécurité

## Supported Versions / Versions supportées

| Version | Supported / Supportée |
| :--- | :---: |
| `0.2.x` (`main`) | ✅ |
| `< 0.2.0` | ❌ |

## Security Architecture

* **Zero shared credentials:** Every user authenticates with their own IDhall JWT (`Authorization: Bearer <jwt>` in HTTP mode; `IDHALL_API_TOKEN` in local `stdio` mode). HTTP mode strictly refuses environment-variable token fallback by default.
* **SSRF defense-in-depth:**
  * HTTPS is strictly enforced; embedded URL credentials, paths, queries, and fragments are rejected.
  * Allowed hosts default to `*.idhall.com` (configurable via `IDHALL_ALLOWED_HOSTS` / `IDHALL_BASE_URL`).
  * Private, loopback, link-local, and cloud-metadata IP ranges (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`, `fc00::/7`, `fe80::/10`, `localhost`) are blocked by default (opt-in via `IDHALL_ALLOW_PRIVATE_NETWORKS=true` for internal on-premise deployments only).
  * HTTP redirects are disabled (`follow_redirects=False`) to prevent `Authorization` header leakage.
* **Path traversal & injection guards:** Relative API paths and `endpoint_id` values are strictly validated; HTTP headers (`Accept-Language`, `IDhall-Timezone`) are sanitized against CR/LF injection; JWT tokens are masked in object representations (`repr=False`).
* **Optional read-only enforcement:** Set `IDHALL_READ_ONLY=true` to block all mutating HTTP methods (`POST`, `PUT`, `PATCH`, `DELETE`) at the server boundary.
* **Container hardening:** Multi-stage non-root image (`mcpuser`), read-only root filesystem, `cap_drop: [ALL]`, `no-new-privileges:true`, automated Trivy CVE scanning, and GitHub build-provenance attestation.

## Reporting a Vulnerability / Signaler une vulnérabilité

* **English:** Please **do not** open a public GitHub issue for security vulnerabilities. Report them privately via **GitHub Security Advisories** (*Security > Advisories > Report a vulnerability*) on this repository. We aim to acknowledge reports within 72 hours.
* **Français :** Merci de **ne pas** ouvrir d'issue publique pour une faille de sécurité. Signalez-la en privé via **GitHub Security Advisories** (*Security > Advisories > Report a vulnerability*) sur ce dépôt. Nous nous engageons à accuser réception sous 72 h.
