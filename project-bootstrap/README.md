# project-bootstrap

Skill de Claude Code que convierte una idea en un **repositorio de GitHub funcional con
Claude Code completamente configurado**. Investiga y planea el objetivo, deduce las
especialidades que el proyecto necesita y genera todo el andamiaje (`CLAUDE.md`,
subagentes, skills, hooks, permisos, rules y MCP) de forma **spec-driven**.

## Cómo funciona

La división del trabajo es deliberada:

- **Claude hace lo creativo** — entrevista, investiga el dominio, planea y deduce qué
  especialidades y guardrails necesita *este* proyecto. Todo eso se vuelca en un
  `project-spec.json`.
- **Un script hace lo mecánico** — `scripts/scaffold_claude.py` lee el spec y escribe
  todos los archivos de configuración de forma determinista y validable.

Así el andamiaje es reproducible y sin errores de dedo: tú solo revisas el spec (una
decisión de diseño) en vez de docenas de archivos.

## Flujo en fases

0. **Intake** — objetivo, dominio, stack, destino en GitHub y restricciones duras.
1. **Investigar y planear** — research del dominio, propuesta de stack y un brief breve.
2. **Deducir especialidades** — capacidades → roles → subagentes (read-only cuando es análisis, modelos baratos por defecto).
3. **Setup en GitHub** — crea el repo e inicializa git (vía `gh` CLI o GitHub MCP).
4. **Generar la configuración** — construye el spec y ejecuta el scaffolder.
5. **Validar y documentar** — valida la config, commitea y resume próximos pasos.

## Qué genera

- `CLAUDE.md` — memoria del proyecto (conciso).
- `.claude/settings.json` — permisos (allow/ask/deny) y bloque `hooks`.
- `.claude/rules/*.md` — reglas por área (se cargan según `paths:`).
- `.claude/agents/*.md` — subagentes especializados.
- `.claude/skills/<nombre>/SKILL.md` — skills del proyecto.
- `.mcp.json` — servidores MCP (con placeholders de env para secretos).
- `.claude/telemetry.env.example` — solo si activas observabilidad (OTel).
- `docs/PROJECT_BRIEF.md` y `docs/CLAUDE_CODE_SETUP.md`.

## Seguridad de secretos (3 capas, fail-closed)

Proteger `.env` requiere tres capas, porque `deny Read(./.env)` **no** frena
`Bash(cat .env)`:

1. `deny Read` de secretos,
2. hook `PreToolUse` con matcher `Read|Edit`,
3. hook `PreToolUse` con matcher `Bash` que inspecciona el comando.

Los hooks de seguridad **fallan cerrado** (bloquean si falta `jq`). Los tokens nunca se
hardcodean: van como variables de entorno en `.mcp.json`.

## Instalación

Esta skill inicializa proyectos **nuevos**, así que debe vivir a nivel de **usuario**
para estar disponible antes de que exista el `.claude/` del proyecto:

- **Claude Code (recomendado):** copia la carpeta a `~/.claude/skills/project-bootstrap/`
- **Claude.ai:** sube el `.skill` empaquetado (Settings → Skills) o usa **Save skill**.

## Uso

Di algo como:

> "arranca un proyecto nuevo para \<idea\>"
> "configura Claude Code para \<repo\>"

## Estructura

```
project-bootstrap/
├── SKILL.md                       # instrucciones principales (flujo en fases)
├── assets/
│   └── project-spec.example.json  # spec de entrada, con cada campo comentado
├── scripts/
│   ├── new_project.sh             # crea el repo en GitHub e inicializa git
│   ├── scaffold_claude.py         # escribe toda la config .claude/ desde el spec
│   └── validate_config.py         # valida la config generada
└── references/                    # se leen según la fase
    ├── claude-code-objects.md     # catálogo canónico de objetos de Claude Code
    ├── agent-templates.md         # plantillas de subagentes por rol
    ├── skill-templates.md         # plantillas de SKILL.md
    ├── hooks-cookbook.md          # recetas de hooks (con semántica de exit codes)
    ├── settings-permissions.md    # plantillas de settings.json y permisos
    ├── github-setup.md            # recetas de gh CLI y GitHub MCP
    └── observability.md           # OpenTelemetry, métricas y redacción
```

## Historial

Ver [`CHANGELOG.md`](./CHANGELOG.md). La **v1.1** incluye las correcciones de la
revisión adversarial: flujo de GitHub robusto (sin *non-fast-forward*), control de
secretos en 3 capas fail-closed, y módulo de observabilidad.
