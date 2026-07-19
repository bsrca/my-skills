# Setup de GitHub

Dos caminos: la CLI de GitHub (`gh`, más simple) o el servidor MCP de GitHub. Elige según lo que tenga el usuario.

## Camino A · CLI de GitHub (recomendado)

Prerrequisito: `gh auth status` debe mostrar sesión iniciada. Si no, `gh auth login`.

El script `scripts/new_project.sh` automatiza esto:
```bash
bash scripts/new_project.sh \
  --name "mi-proyecto" \
  --owner "mi-usuario-u-org" \
  --visibility private \
  --license mit \
  --description "Descripción corta" \
  --gitignore Node
```
Hace: valida `gh`, crea el repo (`gh repo create`), inicializa git local, primer commit y push.

Equivalente manual:
```bash
gh repo create OWNER/NOMBRE --private --description "DESC" --gitignore Node --license mit
git init && git branch -M main
git remote add origin git@github.com:OWNER/NOMBRE.git
git add -A && git commit -m "chore: commit inicial"
git push -u origin main
```

### Extras opcionales (tras crear el repo)

Branch protection en `main`:
```bash
gh api -X PUT repos/OWNER/NOMBRE/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  -f "required_status_checks=null" \
  -F "enforce_admins=true" \
  -f "required_pull_request_reviews[required_approving_review_count]=1" \
  -f "restrictions=null"
```

Labels útiles:
```bash
for L in "bug:d73a4a" "feature:0e8a16" "docs:0075ca" "chore:cfd3d7"; do
  gh label create "${L%%:*}" --color "${L##*:}" 2>/dev/null || true
done
```

Issue template (`.github/ISSUE_TEMPLATE/bug.md`) y PR template (`.github/pull_request_template.md`) los puede generar el scaffold si el spec lo pide (`github.templates: true`).

## Camino B · GitHub MCP

Si el usuario usa el servidor MCP de GitHub en vez de `gh`:

1. Añádelo (ámbito de proyecto):
```bash
claude mcp add --scope project github -- npx -y @modelcontextprotocol/server-github
```
2. O decláralo en `.mcp.json` (el scaffold lo hace si el spec incluye el server `github`):
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}" }
    }
  }
}
```
3. Exporta el token antes de abrir Claude Code: `export GITHUB_TOKEN=...` (o ponlo en tu gestor de secretos). NUNCA lo commitees.
4. Dentro de la sesión, `/mcp` verifica el estado y dispara OAuth si aplica. Luego Claude puede crear el repo, abrir issues/PRs, etc. vía las tools `mcp__github__*`.

## Recomendación

- Para el arranque puro (crear el repo y hacer push), `gh` es lo más directo y sin fricción.
- Para trabajar el proyecto de forma continua (PRs, issues, reviews) desde Claude Code, el MCP de GitHub da tools nativas más estructuradas. Puedes usar ambos.
- Corrección de transcripción frecuente: el token de Slack para su MCP es el "bot token" (`xoxb-`), no "vote token"; y se usa `curl` (no "curve") para llamadas directas a APIs.
