# Changelog · project-bootstrap

## v1.1 — correcciones de la revisión adversarial

**Seguridad**
- Control de secretos ahora en 3 capas: `deny Read(.env)` + hook `Read|Edit` + **nuevo hook `PreToolUse` matcher `Bash`** que inspecciona el comando (cierra el bypass `cat .env`, que las dos primeras capas NO frenaban).
- Los hooks de seguridad ahora **FALLAN CERRADO**: si falta `jq`, bloquean en vez de permitir (antes salían con `exit 0` = permitir).
- `settings-permissions.md` documenta explícitamente el hueco del bypass de Bash y por qué el hook es la defensa real.

**GitHub (bug de arranque)**
- `new_project.sh` reescrito: commitea primero en local (crea `README.md` si el dir está vacío y un `.gitignore` que **siempre** ignora `.env`/llaves) y crea el repo **desde la fuente** con `gh repo create --source=. --push`. Elimina el fallo *non-fast-forward* (que ocurría al usar `--gitignore`/`--license`) y el fallo de push en directorios vacíos. Maneja el caso de repo ya existente.

**Robustez de hooks**
- `format.sh` usa `npx --no-install` (no se cuelga ni intenta instalar en un hook no-interactivo) y **avisa** en vez de fallar en silencio.

**Validación**
- `validate_config.py` ahora marca (WARN) los agentes sin `tools` (heredan TODAS las herramientas) y detecta el **bypass de secretos por Bash** (deny de Read sin hook/regla de Bash).

**Cobertura**
- Nuevo módulo de **observabilidad**: `references/observability.md` + generación opcional de `.claude/telemetry.env.example` cuando el spec trae `observability.enabled: true` (OTel, 8 métricas, 24 log events, redacción ON). El catálogo (`claude-code-objects.md`) suma la sección 10.

**Nota de alcance**
- Esta skill sigue siendo una herramienta de *setup*, no un compendio. El resumen completo de los cursos/investigación vive en el atlas de 9 diagramas y el reporte de investigación.

## v1.0 — versión inicial
- Skill spec-driven: Claude planea (project-spec.json) y un script escribe la config `.claude/`.
- Genera CLAUDE.md, settings.json (permisos + hooks), rules, agentes, skills, .mcp.json y docs.
- Referencias: catálogo de objetos, plantillas de agentes/skills, recetario de hooks, settings/permisos, setup de GitHub.
