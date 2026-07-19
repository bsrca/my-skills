# Recetario de hooks

Hooks probados para `.claude/settings.json`. En el `project-spec.json`, cada objeto de `hooks` describe un hook (evento, matcher, comando, y opcional `script`). El scaffold arma la estructura `evento → [{matcher, hooks:[{type, command}]}]` y, cuando el comando apunta a `.claude/hooks/…` y hay `script`, escribe también el script ejecutable.

Semántica: `exit 2` bloquea (stderr vuelve a Claude); **cualquier otro código NO bloquea** (ojo: `exit 1` NO bloquea). Timeout 60 s. Por stdin llega JSON (`tool_name`, `tool_input`, …). Variables: `$CLAUDE_PROJECT_DIR`.

> **Principio de seguridad**: un control de seguridad debe FALLAR CERRADO. Si el hook no puede inspeccionar la operación (p.ej. falta `jq`), debe bloquear, no permitir.

## 1. Formatear al editar (PostToolUse) — no bloqueante, no se cuelga

```json
{ "event": "PostToolUse", "matcher": "Edit|Write", "command": ".claude/hooks/format.sh" }
```
```bash
#!/usr/bin/env bash
# Formatea el archivo recién editado. Usa --no-install para no colgarse y AVISA si falta la herramienta.
command -v jq >/dev/null 2>&1 || { echo "format: falta jq; omito." >&2; exit 0; }
FILE=$(jq -r '.tool_input.file_path // empty')
[ -z "$FILE" ] && exit 0
case "$FILE" in
  *.ts|*.tsx|*.js|*.jsx|*.json|*.css|*.md)
    npx --no-install prettier --write "$FILE" 2>/dev/null || echo "format: prettier no disponible para $FILE" >&2 ;;
  *.py)
    command -v black >/dev/null 2>&1 && black -q "$FILE" 2>/dev/null || echo "format: black no disponible" >&2 ;;
  *.rs)
    command -v rustfmt >/dev/null 2>&1 && rustfmt "$FILE" 2>/dev/null || true ;;
esac
exit 0
```
Cambios vs la versión ingenua: `npx --no-install` (no intenta instalar ni se cuelga en un hook no-interactivo) y avisa por stderr en vez de fallar en silencio.

## 2a. Bloquear lectura de secretos por TOOL (PreToolUse, fail-closed)

```json
{ "event": "PreToolUse", "matcher": "Read|Edit", "command": ".claude/hooks/block-secrets.sh" }
```
```bash
#!/usr/bin/env bash
# Bloquea (exit 2) lectura/edición de archivos sensibles. FALLA CERRADO si no hay jq.
if ! command -v jq >/dev/null 2>&1; then
  echo "block-secrets: falta 'jq'; bloqueo por seguridad (fail-closed)." >&2
  exit 2
fi
FILE=$(jq -r '.tool_input.file_path // empty')
case "$FILE" in
  *.env|*.env.*|*secrets/*|*id_rsa*|*.pem|*.key|*credentials*)
    echo "Bloqueado: archivo sensible ($FILE)." >&2
    exit 2 ;;
esac
exit 0
```

## 2b. Bloquear lectura de secretos por BASH (PreToolUse) — cierra el bypass

**Por qué existe**: `deny Read(./.env)` y el hook 2a solo cubren las herramientas Read/Edit. `Bash(cat .env)` los ESQUIVA. Este hook inspecciona el comando Bash.

```json
{ "event": "PreToolUse", "matcher": "Bash", "command": ".claude/hooks/block-secrets-bash.sh" }
```
```bash
#!/usr/bin/env bash
# Bloquea (exit 2) comandos Bash que intenten acceder a archivos sensibles. Fail-closed.
if ! command -v jq >/dev/null 2>&1; then
  echo "block-secrets-bash: falta 'jq'; bloqueo por seguridad." >&2
  exit 2
fi
CMD=$(jq -r '.tool_input.command // empty')
if printf '%s' "$CMD" | grep -Eiq '(\.env([^a-zA-Z]|$)|secrets/|id_rsa|\.pem([^a-zA-Z]|$)|\.key([^a-zA-Z]|$)|credentials)'; then
  echo "Bloqueado: el comando parece acceder a un archivo sensible." >&2
  exit 2
fi
exit 0
```
Es una defensa heurística: cubre `cat/less/cp/scp/tar` sobre esos paths. No es infalible ante ofuscación, pero cierra el hueco obvio. Úsalo JUNTO con 2a y con el `deny` de permisos (defensa en profundidad).

## 3. Loguear cada comando Bash (PostToolUse, auditoría)

```json
{ "event": "PostToolUse", "matcher": "Bash", "command": ".claude/hooks/log-bash.sh" }
```
```bash
#!/usr/bin/env bash
command -v jq >/dev/null 2>&1 || exit 0
CMD=$(jq -r '.tool_input.command // empty')
echo "$(date -u +%FT%TZ)  $CMD" >> "$CLAUDE_PROJECT_DIR/.claude/bash-audit.log"
exit 0
```

## 4. Correr tests al terminar el turno (Stop) — modo aviso

Recuerda: en `Stop`, `exit 2` FUERZA a Claude a continuar (riesgo de bucle). Por defecto deja el hook en aviso (exit 0).
```json
{ "event": "Stop", "matcher": "", "command": ".claude/hooks/run-tests.sh" }
```
```bash
#!/usr/bin/env bash
npm test --silent >/dev/null 2>&1 && echo "tests OK" || echo "aviso: tests fallando" >&2
exit 0
```

## Selección recomendada por defecto

Todo proyecto: **1 (formateo)**, **2a + 2b (secretos por tool Y por bash)**. Añade **3 (log bash)** si te importa auditoría, y **4 (tests)** si hay suite. La combinación 2a+2b+`deny` es la que realmente protege secretos.

## Seguridad de hooks

Corren con tus credenciales. Entrecomilla variables (`"$FILE"`), usa `$CLAUDE_PROJECT_DIR`, valida el stdin, falla CERRADO en controles de seguridad, y bloquea `path traversal`. No descargues ni ejecutes código remoto en un hook.
