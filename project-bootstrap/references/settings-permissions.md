# Settings, permisos y rules

Cómo generar `.claude/settings.json`, permisos y `.claude/rules/`. En el `project-spec.json`, la sección `permissions` (allow/ask/deny) y `hooks` se combinan en `settings.json`; `rules` produce archivos en `.claude/rules/`.

## Permisos (recordatorio)

Precedencia `deny > ask > allow`; un `deny` nunca se anula. Las reglas se fusionan entre niveles (usuario/proyecto/local/managed). Categorías por defecto: read-only sin aprobación; Bash aprueba y persiste por proyecto; Write/Edit aprueban y se reinician por sesión.

### Base recomendada (ajusta al stack)
```json
{
  "permissions": {
    "allow": [
      "Read(**)",
      "Bash(git status:*)", "Bash(git diff:*)", "Bash(git add:*)", "Bash(git commit:*)"
    ],
    "ask": [
      "Bash(git push:*)", "Bash(rm:*)", "Bash(npx:*)"
    ],
    "deny": [
      "Read(./.env)", "Read(./.env.*)", "Read(./**/secrets/**)",
      "Read(./**/*.pem)", "Read(./**/id_rsa*)"
    ]
  }
}
```
> **Importante (hueco real de permisos)**: `deny Read(./.env)` solo bloquea la herramienta Read.
> **NO impide `Bash(cat .env)`**, que lee el secreto por Bash esquivando la regla. Los patrones
> `deny Bash(...)` ayudan como primera capa pero son frágiles (hay mil formas de leer un archivo:
> `cat`, `less`, `head`, `xxd`, `source`, redirecciones…). La defensa REAL es el hook `PreToolUse`
> con matcher `Bash` (receta 2b del cookbook), que inspecciona el comando y falla cerrado.
> Usa las tres capas juntas: `deny Read`, hook Bash, y `ask`/`deny` de Bash para lo más obvio.

Capa Bash de primer nivel (añádela a `ask` o `deny`; NO sustituye al hook 2b):
```json
"ask": ["Bash(cat:*)", "Bash(less:*)", "Bash(source:*)"]
```

Presets por stack (añádelos a `allow`):
- Node/Next.js: `Bash(npm run:*)`, `Bash(npm test:*)`, `Bash(pnpm:*)`.
- Python: `Bash(pytest:*)`, `Bash(ruff:*)`, `Bash(python -m:*)`.
- Rust: `Bash(cargo build:*)`, `Bash(cargo test:*)`, `Bash(cargo clippy:*)`.

Sintaxis: Bash usa comodines donde espacio+`*` es frontera de palabra; Read/Edit usan globs estilo gitignore; WebFetch usa `domain:`. Un nombre de tool "pelón" en `deny` (p.ej. `"WebFetch"`) lo quita del contexto por completo.

## settings.json completo (ejemplo)
```json
{
  "permissions": {
    "allow": ["Read(**)", "Bash(npm test:*)", "Bash(npm run:*)"],
    "ask": ["Bash(git push:*)"],
    "deny": ["Read(./.env)", "Read(./.env.*)"]
  },
  "hooks": {
    "PostToolUse": [
      { "matcher": "Edit|Write", "hooks": [{ "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/format.sh" }] }
    ],
    "PreToolUse": [
      { "matcher": "Read|Edit", "hooks": [{ "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/block-secrets.sh" }] }
    ]
  }
}
```
`.claude/settings.local.json` (git-ignored) es para overrides personales que NO se comparten. El scaffold escribe el `settings.json` compartido; deja el `.local` al usuario.

## Rules (`.claude/rules/`)

- SIN frontmatter: carga global, como una extensión de CLAUDE.md. Úsalo para principios que aplican a todo el repo.
- CON frontmatter `paths:`: carga solo al tocar archivos que coinciden. Ideal para reglas por lenguaje/área sin inflar el contexto siempre.

Ejemplo `.claude/rules/typescript.md`:
```markdown
---
paths: ["**/*.ts", "**/*.tsx"]
---
# TypeScript
- Sin `any` implícito. Tipa las fronteras públicas.
- Prefiere funciones puras y módulos pequeños.
- Maneja errores explícitamente; nada de promesas sin await.
```

Ejemplo `.claude/rules/security.md` (global, sin frontmatter):
```markdown
# Seguridad (siempre)
- Nunca hardcodees secretos; usa variables de entorno.
- Valida y sanea toda entrada de usuario.
- No registres datos sensibles en logs.
```

## CLAUDE.md (memoria del proyecto)

Conciso (bajo ~200-300 líneas). Estructura sugerida:
```markdown
# <Proyecto>
Objetivo: <una frase>.

## Stack
<lenguaje / framework / BD>

## Arquitectura
<mapa de carpetas y responsabilidades; punteros, no volcado>

## Convenciones
<estilo, naming, patrones; el detalle fino va en .claude/rules>

## Comandos
<build, test, lint, dev>

## Importante
<cosas que Claude debe recordar siempre; reglas duras van en permisos/hooks, no aquí>
```
Recuerda: CLAUDE.md es GUÍA blanda. Lo que debe cumplirse SIEMPRE va en permisos (`deny`) o hooks (`exit 2`).
