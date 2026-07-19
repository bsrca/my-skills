#!/usr/bin/env bash
# new_project.sh - Crea el repositorio en GitHub e inicializa git local de forma robusta.
# Requiere la CLI de GitHub (gh) autenticada:  gh auth status
#
# Estrategia: commitea PRIMERO en local y crea el repo DESDE la fuente
# (gh repo create --source=. --push). Esto evita el conflicto non-fast-forward
# que ocurre cuando GitHub inicializa el repo con commits (README/gitignore/license)
# y luego intentas empujar un historial local distinto.
#
# Uso:
#   bash new_project.sh --name NOMBRE --owner OWNER [--visibility private] \
#        [--license mit] [--description "..."] [--gitignore Node] [--no-push]
set -euo pipefail

NAME="" OWNER="" VISIBILITY="private" LICENSE="" DESC="" GITIGNORE="" PUSH=1

while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME="$2"; shift 2 ;;
    --owner) OWNER="$2"; shift 2 ;;
    --visibility) VISIBILITY="$2"; shift 2 ;;
    --license) LICENSE="$2"; shift 2 ;;
    --description) DESC="$2"; shift 2 ;;
    --gitignore) GITIGNORE="$2"; shift 2 ;;
    --no-push) PUSH=0; shift ;;
    *) echo "Flag desconocido: $1" >&2; exit 1 ;;
  esac
done

[ -z "$NAME" ] && { echo "Falta --name" >&2; exit 1; }
[ -z "$OWNER" ] && { echo "Falta --owner" >&2; exit 1; }

# 1. Verificar gh
if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: 'gh' (GitHub CLI) no esta instalado. Instalalo o usa el camino MCP (references/github-setup.md)." >&2
  exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: 'gh' no esta autenticado. Corre:  gh auth login" >&2
  exit 1
fi

# 2. Inicializar git local si hace falta
if [ ! -d .git ]; then
  git init -q
  git branch -M main
fi

# 3. Archivos base locales (garantizan un commit y evitan que el servidor inicialice el repo)
[ -f README.md ] || printf '# %s\n\n%s\n' "$NAME" "$DESC" > README.md

if [ -n "$GITIGNORE" ] && [ ! -f .gitignore ]; then
  # Baja la plantilla real de GitHub; si falla (offline), usa un fallback minimo.
  gh api "gitignore/templates/$GITIGNORE" --jq .source > .gitignore 2>/dev/null \
    || printf 'node_modules/\n__pycache__/\n' > .gitignore
fi
# Asegurar SIEMPRE que los secretos esten ignorados
touch .gitignore
grep -qxF '.env' .gitignore 2>/dev/null || printf '\n# secretos\n.env\n.env.*\n*.pem\n*.key\n' >> .gitignore

if [ -n "$LICENSE" ] && [ ! -f LICENSE ]; then
  gh api "licenses/$LICENSE" --jq .body > LICENSE 2>/dev/null \
    || echo "aviso: no pude bajar la licencia '$LICENSE'; agregala luego." >&2
fi

# 4. Commit local (garantiza al menos un commit antes de crear/empujar)
git add -A
git diff --cached --quiet 2>/dev/null || git commit -q -m "chore: commit inicial"

# 5. Crear el repo desde la fuente, o enlazar si ya existe
if gh repo view "$OWNER/$NAME" >/dev/null 2>&1; then
  echo ">> El repo $OWNER/$NAME ya existe; enlazando remoto y empujando."
  git remote get-url origin >/dev/null 2>&1 || git remote add origin "git@github.com:$OWNER/$NAME.git"
  [ "$PUSH" -eq 1 ] && git push -u origin main
else
  echo ">> Creando repo $OWNER/$NAME ($VISIBILITY) desde la fuente local..."
  CREATE=("$OWNER/$NAME" "--$VISIBILITY" --source=. --remote=origin)
  [ -n "$DESC" ] && CREATE+=(--description "$DESC")
  [ "$PUSH" -eq 1 ] && CREATE+=(--push)
  gh repo create "${CREATE[@]}"
fi

echo "Listo: https://github.com/$OWNER/$NAME"
