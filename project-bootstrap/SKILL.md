---
name: project-bootstrap
description: Inicializa un proyecto nuevo de punta a punta - crea el repositorio en GitHub, investiga y planea el objetivo, deduce las especialidades necesarias y genera toda la configuracion de Claude Code del proyecto (CLAUDE.md, subagentes, skills, hooks, permisos/settings, rules y MCP). Usa esta skill SIEMPRE que el usuario quiera arrancar, iniciar, montar, configurar o hacer el setup de un proyecto nuevo, crear un repo en GitHub, o preparar el andamiaje de Claude Code para un proyecto. Tambien cuando diga "nuevo proyecto", "bootstrap", "scaffolding", "setup de proyecto", "inicializa", "crea el repo", "configura Claude Code para", o pida generar agentes, skills, hooks o permisos para un proyecto completo.
---

# Project Bootstrap

Convierte una idea de proyecto en un repositorio de GitHub **funcional y con Claude Code completamente configurado**: subagentes especializados, skills, hooks, permisos, rules y MCP — todo derivado del objetivo real del proyecto.

## Filosofia (leer primero)

Esta skill es **spec-driven**. La division del trabajo es deliberada:

- **Claude hace lo creativo**: entrevistar, investigar el dominio, planear, y deducir qué especialidades y guardrails necesita ESTE proyecto en particular. Esto llena un archivo `project-spec.json`.
- **Un script hace lo mecanico**: `scripts/scaffold_claude.py` lee ese spec y escribe todos los archivos de configuracion de forma determinista y validable.

Ventaja: el andamiaje es reproducible y sin errores de dedo, y tú solo revisas el spec (una decision de diseño) en vez de docenas de archivos.

Regla de oro heredada de la doc de Claude Code: **empieza determinista y escala solo cuando haga falta**. Codifica las reglas duras en permisos/hooks primero; deja los subagentes y flujos autónomos para cuando el proyecto realmente los exija.

## Flujo en fases

Sigue las fases en orden. No inventes mecanica de Claude Code de memoria: la referencia canónica y corregida está en `references/claude-code-objects.md` — consúltala cuando generes agentes, hooks, permisos o MCP.

### Fase 0 · Intake (definir el objetivo)

Si la conversacion ya contiene el objetivo, el stack y el destino en GitHub, **sáltate las preguntas** y confírmalos en una frase. Si falta info, pregunta de forma compacta (idealmente en un solo turno):

1. **Objetivo** en una o dos frases: ¿qué hace el proyecto y para quién?
2. **Dominio / tipo**: web app, API/servicio, CLI, librería, data/ML, móvil, otro.
3. **Stack** (si ya lo tienen): lenguaje, framework, base de datos. Si no, lo propones en la Fase 1.
4. **GitHub**: owner (usuario u organización), nombre del repo, visibilidad (private/public), licencia.
5. **Restricciones** duras: seguridad, cumplimiento, cosas que Claude NUNCA debe hacer.

No avances hasta tener al menos el objetivo y el destino en GitHub. Todo lo demás lo puedes proponer.

### Fase 1 · Investigar y planear

1. Investiga el dominio con las herramientas disponibles (web search, y subagentes en paralelo si el entorno los tiene). Busca: soluciones/competidores comparables, buenas prácticas, patrones de arquitectura típicos, y consideraciones regulatorias o técnicas del dominio.
2. Si el stack no venía dado, **propón uno** con una justificación de una línea por elección.
3. Redacta un brief breve: objetivo, no-objetivos, usuarios, hitos iniciales y riesgos. Este texto irá a `docs/PROJECT_BRIEF.md` (el script lo escribe desde el spec).

Mantén el plan conciso y accionable. No es un documento académico; es el mapa para configurar el proyecto.

### Fase 2 · Deducir especialidades → roles → subagentes

Del brief, extrae las **capacidades** que el proyecto necesitará (p.ej. "revisar seguridad de dependencias", "escribir tests", "mantener docs", "diseñar el schema"). Mapea cada capacidad a un **rol**, y cada rol a un **subagente**.

Guía de mapeo y plantillas listas: `references/agent-templates.md`.

Criterios (ver detalle en la referencia):
- Prefiere subagentes **read-only** cuando el rol es de análisis (revisor, explorador). Menos superficie de error.
- Asigna **modelos baratos** (haiku/sonnet) a subagentes; reserva opus para razonamiento difícil.
- Empieza con un set pequeño y de alto valor. Roles base casi siempre útiles: `explorer` (read-only), `code-reviewer`, `test-runner`, `docs-writer`. Añade roles de stack (`backend`, `frontend`, `data`, `infra`) solo si el proyecto los usa.
- Recuerda: los subagentes NO se comunican entre sí (topología estrella); solo reportan al agente principal. Si el proyecto exige colaboración real entre agentes, eso es un equipo de agentes (experimental) — documéntalo, no lo asumas por defecto.

### Fase 3 · Setup en GitHub

Crea el repositorio y el andamiaje base. Recetas completas (gh CLI y alternativa por GitHub MCP, más branch protection, labels e issue templates): `references/github-setup.md`.

Ruta rápida con la CLI de GitHub (script parametrizado):

```bash
bash scripts/new_project.sh \
  --name "NOMBRE" --owner "OWNER" --visibility private \
  --license mit --description "DESCRIPCION" --gitignore Node
```

El script commitea PRIMERO en local (creando un `README.md` si el directorio está vacío y un `.gitignore` que **siempre ignora `.env`/llaves**) y luego crea el repo **desde la fuente** con `gh repo create --source=. --push`. Esto evita el conflicto *non-fast-forward* que ocurre si GitHub inicializa el repo con commits y luego intentas empujar un historial distinto. Si el repo ya existe, enlaza el remoto y empuja. Si el usuario prefiere GitHub MCP (o no tiene `gh`), usa la receta MCP de la referencia. Nunca subas secretos: van como variables de entorno.

### Fase 4 · Generar la configuracion de Claude Code

1. **Construye el spec.** Copia `assets/project-spec.example.json` y complétalo con lo decidido en las fases 0-2: metadatos, stack, agentes, skills, hooks, permisos, rules y MCP. El esquema y cada campo están comentados en el propio archivo de ejemplo y en `references/claude-code-objects.md`.
2. **Genera los archivos** ejecutando el andamiaje:

```bash
python3 scripts/scaffold_claude.py --spec project-spec.json --dest .
```

Esto escribe, en la raíz del proyecto:
- `CLAUDE.md` — memoria del proyecto (overview, convenciones, punteros de arquitectura). Conciso (bajo ~200-300 líneas).
- `.claude/settings.json` — permisos (allow/ask/deny) y bloque `hooks`.
- `.claude/rules/*.md` — reglas por área; con frontmatter `paths:` cargan solo al tocar archivos que coinciden.
- `.claude/agents/*.md` — subagentes de la Fase 2.
- `.claude/skills/<nombre>/SKILL.md` — skills específicas del proyecto (plantillas en `references/skill-templates.md`).
- `.mcp.json` — servidores MCP del proyecto (con placeholders de env para secretos).
- `.claude/telemetry.env.example` — **solo si** el spec trae `observability.enabled: true` (plantilla OTel, sin secretos).
- `docs/PROJECT_BRIEF.md` y `docs/CLAUDE_CODE_SETUP.md` — el plan y la explicación de lo generado.

Detalle de cada pieza:
- Permisos y settings: `references/settings-permissions.md`
- Recetas de hooks (formateo al editar, bloqueo de `.env` por tool Y por Bash, tests, log): `references/hooks-cookbook.md`
- Observabilidad (OTel, métricas, redacción): `references/observability.md`

**Seguridad de secretos (hazlo bien)**: proteger `.env` requiere TRES capas, porque `deny Read(./.env)` NO impide `Bash(cat .env)`. Genera: (1) `deny Read` de secretos, (2) hook `PreToolUse` matcher `Read|Edit`, y (3) hook `PreToolUse` matcher `Bash` que inspecciona el comando. Los hooks de seguridad deben FALLAR CERRADO (bloquear si falta `jq`). Ver recetas 2a y 2b del cookbook.

### Fase 5 · Validar y documentar

1. **Valida** la configuración generada:

```bash
python3 scripts/validate_config.py --dest .
```

Comprueba: JSON bien formado (`settings.json`, `.mcp.json`), frontmatter YAML de agentes/skills, y estructura del bloque `hooks` (evento → matcher → handlers). Corrige lo que marque antes de continuar.
2. Haz un commit con la configuración (`git add -A && git commit -m "chore: configuracion inicial de Claude Code"`), y push.
3. Presenta al usuario un resumen: repo creado, agentes/skills/hooks generados, y **próximos pasos** (p.ej. exportar tokens de MCP, abrir el proyecto con `claude`, y probar un subagente).

## Principios que la configuracion generada debe respetar

Estos vienen de la doc oficial de Claude Code (ver `references/claude-code-objects.md` para el detalle y las correcciones):

- **Reglas duras en permisos/hooks, no en CLAUDE.md.** CLAUDE.md es guía blanda; un `deny` o un hook `PreToolUse` que sale con código 2 es lo único que bloquea de verdad.
- **Precedencia de permisos**: `deny` gana a `ask` gana a `allow`. Un `deny` nunca se anula.
- **Secretos (3 capas, no 1)**: `deny Read(.env)` + hook `Read|Edit` + hook `Bash` (porque el `deny` de Read NO frena `cat .env` por Bash). Hooks de seguridad FALLAN CERRADO. Nunca hardcodear tokens; usar env en `.mcp.json`.
- **Hooks**: estructura `evento → [{matcher, hooks:[{type, command}]}]`. `Edit|Write` con `|` = OR. Código de salida 2 bloquea; código 1 NO.
- **Subagentes**: `tools` omitido = hereda todas; acótalo. Profundidad máxima nivel 1 (no anidan).
- **Skills**: SKILL.md bajo ~500 líneas; el detalle va en `references/` de cada skill.

## Archivos de referencia

Léelos según la fase; no cargues todo de golpe.

- `references/claude-code-objects.md` — **catálogo canónico y corregido** de los objetos de Claude Code (MCP, subagentes, skills, hooks, permisos, settings, modelos, esfuerzo) y el mapeo capacidad→objeto. Es la fuente de verdad.
- `references/agent-templates.md` — plantillas de subagentes por rol, con frontmatter correcto.
- `references/skill-templates.md` — plantillas de SKILL.md para skills de proyecto.
- `references/hooks-cookbook.md` — recetas de hooks probadas, con semántica de exit codes.
- `references/settings-permissions.md` — plantillas de `settings.json`, permisos y rules (incluye el hueco del bypass de Bash).
- `references/github-setup.md` — recetas de `gh` CLI y de GitHub MCP.
- `references/observability.md` — activar OpenTelemetry, métricas/log events, redacción, y palancas de costo.

## Assets y scripts

- `assets/project-spec.example.json` — el spec de entrada, con cada campo comentado. Cópialo y complétalo.
- `scripts/scaffold_claude.py` — escribe toda la config `.claude/` desde el spec.
- `scripts/new_project.sh` — crea el repo en GitHub e inicializa git.
- `scripts/validate_config.py` — valida la config generada.

## Instalacion (nota para el usuario)

Esta skill inicializa proyectos NUEVOS, así que debe vivir a nivel de **usuario** para estar disponible antes de que exista el `.claude` del proyecto:

```
~/.claude/skills/project-bootstrap/
```

(En vez de `.claude/skills/` del proyecto, que es para skills específicas de un repo ya creado.)

## Seguridad

No generes hooks ni permisos que faciliten exfiltración de datos, acceso no autorizado o ejecución de código malicioso. Los hooks corren con las credenciales del usuario: valida y entrecomilla inputs, usa `$CLAUDE_PROJECT_DIR` para rutas, y bloquea `path traversal`. Ante cualquier duda de alcance de un permiso, prefiere `ask` sobre `allow`.
