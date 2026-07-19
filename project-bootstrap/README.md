# project-bootstrap

Skill de Claude Code que inicializa un proyecto de punta a punta: crea el repo en
GitHub, investiga y planea el objetivo, deduce las especialidades necesarias y genera
toda la configuración de Claude Code (CLAUDE.md, subagentes, skills, hooks, permisos,
rules y MCP) de forma spec-driven.

## Instalación
- **Claude Code (recomendado, nivel usuario):** copia la carpeta a `~/.claude/skills/project-bootstrap/`
- **Claude.ai:** sube el `.skill` empaquetado (Settings → Skills) o usa el botón Save skill

## Uso
Di algo como: "arranca un proyecto nuevo para <idea>" o "configura Claude Code para <repo>".

Ver `project-bootstrap/CHANGELOG.md` para el historial (v1.1 incluye las correcciones
de la revisión adversarial: flujo de GitHub robusto, control de secretos en 3 capas
fail-closed, y módulo de observabilidad).
