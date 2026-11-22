# Guide de déploiement Docker & Portainer (spécial débutants)

Ce guide explique **étape par étape**, sans jargon inutile, comment déployer le serveur **MCPIdhall** sur votre propre serveur :
1. **Avec Docker simple** (3 commandes)
2. **Avec Portainer** (100 % graphique, sans terminal)
3. **Avec Nginx Proxy Manager (NPM)** pour obtenir une adresse `https://` sécurisée

---

## Avant de commencer (à lire en 30 secondes)

* **Aucun mot de passe ni jeton JWT à mettre sur le serveur :** ce serveur MCP est multi-utilisateurs. Chaque personne qui s'y connecte enverra son propre jeton JWT IDhall depuis son client IA.
* **Prérequis :**
  * Un serveur Linux (ou NAS, Raspberry Pi, VPS, VM) avec **Docker** installé (et **Portainer** si vous utilisez la Méthode B).
  * Si vous utilisez l'image prête à l'emploi sur GitHub (`ghcr.io`), remplacez `<votre-user>` par votre nom d'utilisateur ou d'organisation GitHub dans les exemples ci-dessous.

---

## Méthode A — Déploiement Docker simple (terminal)

### Cas 1 : Vous avez l'image publiée sur GitHub (GHCR) *(le plus rapide)*

Lancez simplement cette commande sur votre serveur :

```bash
docker run -d \
  --name mcp-idhall \
  --restart unless-stopped \
  -p 8000:8000 \
  -e IDHALL_ALLOWED_HOSTS="*" \
  -e IDHALL_LANGUAGE="fr" \
  -e IDHALL_TIMEZONE="Europe/Paris" \
  ghcr.io/smilebob/mcp-idhall:latest
```

### Cas 2 : Vous déployez depuis le dossier du projet (build local)

Copiez le dossier `MCPIdhall` sur votre serveur, puis lancez :

```bash
cd MCPIdhall
cp .env.docker.example .env.docker
docker compose --env-file .env.docker up -d --build
```

### Vérifier que ça tourne ✅

Tapez cette commande sur le serveur :

```bash
curl http://127.0.0.1:8000/health
```

Si tout est bon, vous devez voir :
```json
{"status":"ok","service":"mcp-idhall","version":"0.1.0"}
```

---

## Méthode B — Déploiement pas à pas dans Portainer (sans ligne de commande)

Portainer vous permet de tout faire à la souris depuis votre navigateur.

### Étape 1 : Ouvrir la page Stacks
1. Connectez-vous à votre interface **Portainer**.
2. Cliquez sur votre environnement Docker (souvent nommé **`local`**).
3. Dans le menu de gauche, cliquez sur **`Stacks`**.
4. Cliquez sur le bouton bleu **`+ Add stack`** en haut à droite.

---

### Étape 2 : Nommer la stack et coller la configuration

1. Dans le champ **Name**, tapez : `mcp-idhall`
2. Laissez **Build method** sur **`Web editor`**.
3. Collez **l'un des deux blocs** ci-dessous dans l'éditeur :

#### Option 1 — Simple (port `8000` ouvert sur le serveur)
*(Idéal si vous débutez ou si NPM pointe vers l'IP de votre serveur sur le port `8000`.)*

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
      IDHALL_LANGUAGE: "fr"
      IDHALL_TIMEZONE: "Europe/Paris"
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
```

#### Option 2 — Connecté directement au réseau Docker de Nginx Proxy Manager *(plus propre)*
*(Aucun port exposé à l'extérieur : seul NPM peut parler au conteneur. Remplacez `npm_network` par le vrai nom de votre réseau Docker NPM, visible dans Portainer ➔ menu **Networks**.)*

```yaml
services:
  mcp-idhall:
    image: ghcr.io/smilebob/mcp-idhall:latest
    container_name: mcp-idhall
    restart: unless-stopped
    environment:
      MCP_TRANSPORT: "streamable-http"
      IDHALL_ALLOWED_HOSTS: "*"
      IDHALL_LANGUAGE: "fr"
      IDHALL_TIMEZONE: "Europe/Paris"
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

> **Que veulent dire ces 4 variables ?**
> * `MCP_TRANSPORT: "streamable-http"` → protocole MCP moderne (compatible Antigravity, Claude, Cursor…).
> * `IDHALL_ALLOWED_HOSTS: "*"` → autorise toutes les instances IDhall en HTTPS. *(Pour limiter à une seule instance, remplacez `"*"` par `"mon-entreprise.idhall.com"`.)*
> * `IDHALL_LANGUAGE: "fr"` → langue des réponses/erreurs IDhall.
> * `IDHALL_TIMEZONE: "Europe/Paris"` → fuseau horaire.

*(Astuce : si vous n'avez pas encore poussé l'image sur GHCR mais que vous utilisez un dépôt Git, vous pouvez aussi choisir **Build method : Repository** dans Portainer, coller l'URL de votre dépôt GitHub et indiquer `docker-compose.yml` — Portainer construira l'image tout seul !)*

---

### Étape 3 : Lancer le déploiement
1. Descendez tout en bas de la page.
2. Cliquez sur le bouton bleu **`Deploy the stack`**.
3. Patientez quelques secondes pendant le téléchargement de l'image.

---

### Étape 4 : Vérifier que le conteneur est en bonne santé ✅
1. Dans le menu de gauche de Portainer, cliquez sur **`Containers`**.
2. Trouvez **`mcp-idhall`**.
3. Après ~10 à 30 secondes, son statut doit passer au vert : **`healthy`**.
4. *(Optionnel)* Cliquez sur la petite icône **Logs** (feuille de papier) à côté du nom : vous devez voir le serveur Uvicorn démarré sur `http://0.0.0.0:8000`.

---

### Étape 5 : Comment mettre à jour plus tard dans Portainer ?
Quand une nouvelle version de l'image est disponible :
1. Allez dans **Containers** ➔ cliquez sur **`mcp-idhall`**.
2. Cliquez sur **`Recreate`**.
3. Activez l'interrupteur **`Re-pull image`**, puis cliquez sur **`Recreate`**.
C'est tout !

---

## Étape suivante — Mettre en HTTPS avec Nginx Proxy Manager (NPM)

> ⚠️ **Indispensable :** ne passez jamais de jetons JWT en `http://` sur Internet. Utilisez toujours `https://` via NPM.

1. Ouvrez **Nginx Proxy Manager** ➔ **`Hosts`** ➔ **`Proxy Hosts`** ➔ **`Add Proxy Host`**.
2. **Onglet `Details` :**
   * **Domain Names :** `mcp-idhall.votre-domaine.fr` *(créez d'abord cet enregistrement DNS vers l'IP de votre serveur)*
   * **Scheme :** `http`
   * **Forward Hostname / IP :**
     * Si Option 1 (port `8000`) : l'IP locale de votre serveur (ex. `192.168.1.50`)
     * Si Option 2 (réseau Docker NPM) : tapez simplement `mcp-idhall`
   * **Forward Port :** `8000`
   * Cochez **`Block Common Exploits`** et **`Websockets Support`**.
3. **Onglet `SSL` :**
   * **SSL Certificate :** `Request a new SSL Certificate` *(ou votre certificat wildcard)*
   * Cochez **`Force SSL`** et **`HTTP/2 Support`**.
4. **Onglet `Advanced` :**
   Collez ces 4 lignes *(évite que Nginx ne coupe ou ne mette en tampon les réponses MCP en streaming)* :
   ```nginx
   proxy_buffering off;
   proxy_cache off;
   proxy_read_timeout 3600s;
   proxy_send_timeout 3600s;
   ```
5. Cliquez sur **`Save`**.

### Test final dans votre navigateur 🌐
Ouvrez `https://mcp-idhall.votre-domaine.fr/health` dans votre navigateur.
Vous devez voir s'afficher :
```json
{"status":"ok","service":"mcp-idhall","version":"0.1.0"}
```

---

## Connecter votre client IA au serveur distant

Chaque utilisateur ajoute ceci dans la configuration MCP de son client IA avec **son propre jeton JWT IDhall** :

```json
{
  "mcpServers": {
    "idhall": {
      "url": "https://mcp-idhall.votre-domaine.fr/mcp",
      "headers": {
        "Authorization": "Bearer <votre_jeton_jwt_idhall>"
      }
    }
  }
}
```

> Notez bien le **`/mcp`** à la fin de l'URL !

---

## Mini-FAQ « Au secours, ça ne marche pas ! »

| Problème | Cause la plus fréquente | Solution |
| :--- | :--- | :--- |
| **Erreur `502 Bad Gateway` dans NPM** | NPM n'arrive pas à joindre le conteneur | Si Option 2 : vérifiez que `mcp-idhall` et NPM sont sur le **même réseau Docker** dans Portainer. Si Option 1 : vérifiez que le port `8000` n'est pas bloqué par le pare-feu (`ufw`). |
| **Conteneur bloqué sur `unhealthy` dans Portainer** | Le conteneur n'a pas démarré correctement | Cliquez sur **Logs** du conteneur `mcp-idhall` dans Portainer pour lire le message d'erreur exact. |
| **`Error: image not found` ou `unauthorized` sur GHCR** | L'image GitHub est privée | Rendez le package **Public** dans GitHub (*Packages > mcp-idhall > Package settings*) ou ajoutez un *Registry* GHCR dans Portainer (*Registries > Add registry*). |
| **L'IA dit `Aucun jeton JWT IDhall fourni`** | L'en-tête `Authorization` n'est pas envoyé | Vérifiez que `"headers": { "Authorization": "Bearer ..." }` est bien présent dans la config du client MCP et qu'il y a bien un espace après `Bearer`. |
| **L'URL `/mcp` répond `404` ou échoue** | Mauvais chemin ou mauvais transport | Vérifiez que l'URL se termine bien par **`/mcp`** (et que `MCP_TRANSPORT` vaut `streamable-http`). |
