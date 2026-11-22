# Docker & Portainer Deployment Guide (Beginner-Friendly)

> 🇬🇧 **English** | [🇫🇷 **Version française (GUIDE_DOCKER_PORTAINER.md)**](GUIDE_DOCKER_PORTAINER.md)

This step-by-step guide shows how to deploy **MCPIdhall** on your own server with zero guesswork:
1. **Simple Docker CLI** (1 command)
2. **Portainer** (100% graphical UI, no terminal required)
3. **Nginx Proxy Manager (NPM)** for automatic HTTPS

---

## Before You Start (30-Second Read)

* **No secrets or JWT tokens on the server:** `MCPIdhall` is multi-user by design. Every user passes their own IDhall JWT token from their AI client.
* **Multi-arch ready:** The official image `ghcr.io/smilebob/mcp-idhall:latest` supports both `linux/amd64` (standard PCs/servers/VPS) and `linux/arm64` (Raspberry Pi, Apple Silicon, ARM servers).

---

## Method A — Simple Docker Deployment (CLI)

### Option 1: Pull Ready-to-Use Image from GHCR *(fastest)*

```bash
docker run -d \
  --name mcp-idhall \
  --restart unless-stopped \
  -p 8000:8000 \
  -e IDHALL_ALLOWED_HOSTS="*" \
  -e IDHALL_LANGUAGE="en" \
  -e IDHALL_TIMEZONE="UTC" \
  ghcr.io/smilebob/mcp-idhall:latest
```

### Option 2: Build Locally from the Repository

```bash
git clone https://github.com/smilebob/MCPIdhall.git
cd MCPIdhall
cp .env.docker.example .env.docker
docker compose --env-file .env.docker up -d --build
```

### Verify It Works ✅

```bash
curl http://127.0.0.1:8000/health
# Expected output:
# {"status":"ok","service":"mcp-idhall","version":"0.1.0"}
```

---

## Method B — Step-by-Step Deployment in Portainer (GUI)

### Step 1: Open Stacks
1. Log into **Portainer** and select your Docker environment (usually **`local`**).
2. In the left sidebar, click **`Stacks`**.
3. Click **`+ Add stack`** (top right).

### Step 2: Name the Stack and Paste the YAML
1. Set **Name** to `mcp-idhall`.
2. Keep **Build method** on **`Web editor`**.
3. Paste **one of the two configurations** below:

#### Option 1 — Simple (Exposes Port `8000`)

```yaml
services:
  mcp-idhall:
    image: ghcr.io/smilebob/mcp-idhall:latest
    container_name: mcp-idhall
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      MCP_TRANSPORT: "streamable-http"
      IDHALL_ALLOWED_HOSTS: "*"
      IDHALL_LANGUAGE: "en"
      IDHALL_TIMEZONE: "UTC"
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
```

#### Option 2 — Connected Directly to Nginx Proxy Manager's Docker Network *(recommended)*
*(Replace `npm_network` with your actual NPM Docker network name from Portainer ➔ **Networks**.)*

```yaml
services:
  mcp-idhall:
    image: ghcr.io/smilebob/mcp-idhall:latest
    container_name: mcp-idhall
    restart: unless-stopped
    environment:
      MCP_TRANSPORT: "streamable-http"
      IDHALL_ALLOWED_HOSTS: "*"
      IDHALL_LANGUAGE: "en"
      IDHALL_TIMEZONE: "UTC"
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    networks:
      - npm_network

networks:
  npm_network:
    external: true
```

> **Environment variables explained:**
> * `MCP_TRANSPORT: "streamable-http"` → modern MCP protocol (endpoint `/mcp`).
> * `IDHALL_ALLOWED_HOSTS: "*"` → allows any HTTPS IDhall instance (SaaS & on-premise). Set e.g. `"my-company.idhall.com"` to lock to a single instance.
> * `IDHALL_LANGUAGE` → `en`, `fr`, etc.
> * `IDHALL_TIMEZONE` → e.g. `UTC`, `Europe/Paris`, `America/New_York`.

### Step 3: Deploy & Verify ✅
1. Click **`Deploy the stack`**.
2. Go to **`Containers`** ➔ wait ~15 seconds for **`mcp-idhall`** to show green **`healthy`**.
3. To update later: open **`mcp-idhall`** ➔ **`Recreate`** ➔ toggle **`Re-pull image`** ON ➔ **`Recreate`**.

---

## Next Step — Add HTTPS with Nginx Proxy Manager (NPM)

> ⚠️ Always use **HTTPS** so JWT tokens are encrypted in transit.

1. In **Nginx Proxy Manager**, go to **`Hosts`** ➔ **`Proxy Hosts`** ➔ **`Add Proxy Host`**.
2. **`Details` tab:**
   * **Domain Names:** `mcp-idhall.your-domain.com`
   * **Scheme:** `http`
   * **Forward Hostname / IP:** server IP (Option 1) or `mcp-idhall` (Option 2)
   * **Forward Port:** `8000`
   * Enable **`Block Common Exploits`** and **`Websockets Support`**.
3. **`SSL` tab:** enable Let's Encrypt SSL + **`Force SSL`** + **`HTTP/2 Support`**.
4. **`Advanced` tab** *(important for MCP HTTP streaming)*:
   ```nginx
   proxy_buffering off;
   proxy_cache off;
   proxy_read_timeout 3600s;
   proxy_send_timeout 3600s;
   ```
5. Click **`Save`**, then open `https://mcp-idhall.your-domain.com/health` in your browser — you should see `{"status":"ok","service":"mcp-idhall","version":"0.1.0"}`.

---

## Connect Your AI Client

```json
{
  "mcpServers": {
    "idhall": {
      "url": "https://mcp-idhall.your-domain.com/mcp",
      "headers": {
        "Authorization": "Bearer <your_idhall_jwt_token>"
      }
    }
  }
}
```

---

## Quick Troubleshooting FAQ

| Problem | Likely Cause | Solution |
| :--- | :--- | :--- |
| **`502 Bad Gateway` in NPM** | NPM cannot reach the container | Option 2: ensure `mcp-idhall` and NPM share the same Docker network. Option 1: verify port `8000` is reachable. |
| **Container stuck on `unhealthy`** | Startup error | Click **Logs** on `mcp-idhall` in Portainer to see the exact message. |
| **`unauthorized` pulling GHCR image** | GitHub package is private | Set the package visibility to **Public** in GitHub (*Packages > mcp-idhall > Package settings*). |
| **AI says no JWT token provided** | Missing `Authorization` header | Verify `"headers": { "Authorization": "Bearer <token>" }` in your MCP client config. |
| **`404` on MCP connection** | Wrong endpoint path | Ensure the URL ends with **`/mcp`** (when `MCP_TRANSPORT=streamable-http`). |
