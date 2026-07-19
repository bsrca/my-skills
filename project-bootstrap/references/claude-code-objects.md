# Catálogo canónico de objetos de Claude Code

Fuente de verdad para generar configuración. Datos de mediados de 2026, corregidos contra la documentación oficial. Las funciones dependen de versión y varias son beta; verifica en `docs.claude.com` al usar.

## Tabla de contenido
1. Espectro de composición (cuándo usar qué)
2. Mapeo capacidad → objeto (para la Fase 2)
3. MCP (Model Context Protocol)
4. Subagentes
5. Skills
6. Hooks
7. Permisos y settings
8. Modelos y niveles de esfuerzo
9. Orquestación avanzada (contexto, no se genera por defecto)

---

## 1. Espectro de composición

De menor a mayor autonomía (y de mayor a menor determinismo, y de menor a mayor costo):

`prompt → comando/skill → hook → subagente → equipo de agentes`

- **Hook**: control determinista, se ejecuta SIEMPRE en su evento. Bajo costo (corre fuera del contexto).
- **Skill/comando**: conocimiento reutilizable; la skill además puede auto-invocarse por su `description`.
- **Subagente**: contexto propio y aislado; ~4-7x tokens.
- **Equipo de agentes**: colaboran P2P; experimental (Opus 4.6+); ~7-15x tokens.

Regla: empieza a la izquierda. Sube de nivel solo cuando la tarea lo exige.

---

## 2. Mapeo capacidad → objeto (Fase 2)

| Necesidad del proyecto | Objeto a generar |
|---|---|
| Explorar/entender el código sin modificarlo | Subagente read-only `explorer` (modelo haiku) |
| Revisar calidad/seguridad de cambios | Subagente read-only `code-reviewer` / `security-reviewer` |
| Escribir y correr tests | Subagente `test-runner` + hook que corre tests al terminar |
| Mantener documentación | Subagente `docs-writer` + skill de estilo de docs |
| Estándar de commits / PRs | Skill `commit-style` / `pr-review` |
| Formatear siempre tras editar | Hook `PostToolUse` con matcher `Edit|Write` |
| Nunca leer secretos | Permiso `deny` de `.env` + hook `PreToolUse` (exit 2) |
| Acceso a un servicio externo (DB, GitHub, etc.) | Servidor MCP en `.mcp.json` |
| Convención de un área de archivos | Rule en `.claude/rules/` con frontmatter `paths:` |
| Conocimiento/estándares globales del repo | `CLAUDE.md` |

Empieza con lo mínimo de alto valor: `explorer`, `code-reviewer`, `test-runner`, `docs-writer`, hooks de formateo + bloqueo de secretos, y permisos base. Añade el resto según el dominio.

---

## 3. MCP (Model Context Protocol)

Arquitectura cliente-servidor: el host (Claude Code) crea un cliente por servidor. Los servidores aportan **herramientas** y acceso a datos externos.

- **Transportes**: `stdio` (subproceso local), `http` (remoto, estándar actual, soporta OAuth), `sse` (deprecado).
- **Ámbitos**: `local` (privado, este proyecto), `project` (`.mcp.json`, versionable, compartido), `user` (global).
- **Config de proyecto**: archivo `.mcp.json` en la raíz. Secretos por variable de entorno, NUNCA hardcodeados.
- **Límites de salida**: aviso a 10 000 tokens, límite duro 25 000 por tool call; subir con `MAX_MCP_OUTPUT_TOKENS`.
- **Añadir por CLI**: `claude mcp add --scope project NOMBRE -- npx -y @paquete` (los flags van ANTES del nombre; `--` separa el comando que lanza el servidor). En Windows nativo envolver con `cmd /c`.

Ejemplo de `.mcp.json`:
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
Corrección: es "Model" Context Protocol (no "Module").

---

## 4. Subagentes

Asistentes especializados con **contexto separado**, system prompt propio, permisos de tools propios y (opcional) modelo propio. Reportan un resumen al agente principal. Profundidad máxima nivel 1 (no anidan). NO se comunican entre sí.

- **Ubicación**: proyecto `.claude/agents/<name>.md`; usuario `~/.claude/agents/<name>.md`.
- **Frontmatter**: `name`, `description` (así decide Claude cuándo delegar; frases como "Use PROACTIVELY" empujan la delegación), `tools` (allowlist; **omitir = hereda TODAS** — acótalo), `disallowedTools` (denylist), `model` (haiku/sonnet/opus/inherit), `isolation: worktree` (worktree temporal aislado).
- **Modelo de todos los subagentes**: env `CLAUDE_CODE_SUBAGENT_MODEL`.
- **Integrados**: `Explore` (read-only, haiku), `Plan` (read-only en plan mode), `general-purpose` (todas las tools). Puedes sobrescribir uno con el mismo nombre.

Ejemplo (`.claude/agents/code-reviewer.md`):
```markdown
---
name: code-reviewer
description: Revisa calidad, seguridad y estilo de los cambios. Use PROACTIVELY tras editar código.
tools: Read, Grep, Glob
model: sonnet
---
Eres un revisor de código senior. Revisa los diffs buscando bugs, problemas de
seguridad, y desviaciones del estándar del proyecto. Reporta hallazgos priorizados.
```
Corrección: la tool de búsqueda es `Grep` (no "grab").

---

## 5. Skills

Paquetes de instrucciones en Markdown (un directorio con un `SKILL.md`).

- **Frontmatter**: `name` y `description` (obligatorios). En Claude Code además `allowed-tools`, `user-invocable`, `disable-model-invocation`, `model`, `context: fork`, `hooks`. Para empaquetar como `.skill` portable, mantén el frontmatter a `name`/`description`/`allowed-tools` (otros campos solo se usan en Claude Code).
- **Prioridad** (mayor a menor): empresa/managed → personal (`~/.claude/skills`) → proyecto (`.claude/skills`) → plugin.
- **Divulgación progresiva** (3 niveles): name+description siempre; cuerpo del SKILL.md al activarse (bajo ~500 líneas); archivos de `references/` bajo demanda. `scripts/` se ejecutan sin cargar al contexto (solo su salida cuenta).
- **Skills = comandos**: invócala con `/nombre` o deja que Claude la use por coincidencia de la `description`.

`description` "pushy": incluye QUÉ hace Y CUÁNDO usarla, con verbos y sinónimos, para que Claude no la sub-active. Sin `<` ni `>` en la description.

---

## 6. Hooks

Comandos que se ejecutan de forma **determinista** en eventos del ciclo de vida. Definidos en `settings.json` (o en frontmatter de skills/agentes, o plugins).

Eventos clave (hay ~30 en total; el "25" de algunos cursos está desactualizado):
- Sesión: `SessionStart`, `Setup`, `SessionEnd`.
- Prompt: `UserPromptSubmit`, `UserPromptExpansion`.
- Herramientas: `PreToolUse`, `PermissionRequest`, `PermissionDenied`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`.
- Subagentes/tareas: `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`.
- Turno: `Stop`, `StopFailure`. Equipos: `TeammateIdle`.
- Otros: `Notification`, `MessageDisplay`, `PreCompact`, `PostCompact`, `WorktreeCreate`, `WorktreeRemove`, `Elicitation`, `ElicitationResult`, `FileChanged`, `ConfigChange`.

Semántica de salida:
- `exit 0` = éxito (stdout puede inyectar contexto en algunos eventos).
- `exit 2` = **error bloqueante** (stderr vuelve a Claude; `PreToolUse` bloquea el tool; `Stop` fuerza continuar). `PostToolUse` no puede deshacer, solo mostrar stderr.
- **Cualquier otro código NO bloquea** (ojo: `exit 1` NO bloquea).

Estructura en `settings.json` (3 niveles: evento → matcher → handlers):
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/format.sh" }]
      }
    ]
  }
}
```
- Matcher: `Edit|Write` (`|` = OR), `Bash`, regex `mcp__.*`, o `*` = todo.
- Múltiples hooks del mismo evento corren en paralelo y se deduplican. Timeout por defecto 60 s.
- Precedencia en `PreToolUse` si discrepan: `deny > defer > ask > allow`.
- Variables: `$CLAUDE_PROJECT_DIR`, `$CLAUDE_TOOL_INPUT`.

---

## 7. Permisos y settings

`settings.json` (precedencia de mayor a menor): managed/empresa → args de CLI → proyecto local (`.claude/settings.local.json`) → proyecto compartido (`.claude/settings.json`) → usuario (`~/.claude/settings.json`). La mayoría de claves se sobrescriben por precedencia, PERO las reglas de permisos se **fusionan** entre niveles.

Permisos (objeto `permissions`):
```json
{
  "permissions": {
    "allow": ["Read(src/**)", "Bash(npm test:*)", "Bash(npm run:*)"],
    "ask":   ["Bash(git push:*)"],
    "deny":  ["Read(./.env)", "Read(./.env.*)", "Read(./**/secrets/**)"]
  }
}
```
- Precedencia: `deny > ask > allow`. Un `deny` nunca se anula.
- Sintaxis `Tool(especificador)`: Bash usa comodines (espacio+`*` es frontera de palabra), Read/Edit usan globs estilo gitignore.
- Categorías por defecto: read-only (Read/Glob/Grep/LS) sin aprobación; Bash aprueba y persiste por proyecto; Write/Edit aprueban y se reinician por sesión.

Rules: archivos en `.claude/rules/`. SIN frontmatter = carga global (como CLAUDE.md). CON frontmatter `paths:` = carga solo al tocar archivos que coinciden:
```markdown
---
paths: ["**/*.ts", "**/*.tsx"]
---
Reglas de TypeScript para este proyecto: ...
```
`CLAUDE.md` importa archivos con `@ruta` (recursivo hasta 5 niveles). Mantenlo bajo ~200-300 líneas.

---

## 8. Modelos y niveles de esfuerzo

Modelos (mediados 2026, USD/millón input-output): **Haiku 4.5** $1/$5 (rápido/barato, ideal subagentes), **Sonnet 5** $2/$10→$3/$15 (balanceado, default coding, 1M contexto), **Opus 4.8** $5/$25 (flagship coding agéntico), **Fable 5** $10/$50 (más capaz GA), **Mythos 5** $10/$50 (limitado). Output cuesta 5x input. Un hit de caché de prompts cuesta 10% del input.

Niveles de esfuerzo (API): `low → medium → high (default) → xhigh → max`. `ultracode` es solo de Claude Code (no es nivel de API) = xhigh + orquestación de dynamic workflows. Keyword `ultrathink` = razonamiento profundo por un turno. Corrección: no existe "min" (es "low").

Para subagentes del proyecto: default a haiku/sonnet; reserva opus para roles de razonamiento difícil.

---

## 9. Orquestación avanzada (contexto — no generar por defecto)

No los generes a menos que el proyecto lo pida explícitamente:
- **Routines**: workflows recurrentes/programados (disparadores: schedule/`/schedule`, API, evento GitHub). Local (se detiene al cerrar) vs nube (persiste).
- **Goals** (`/goal`): meta MEDIBLE en bucle worker-evaluator. Orientado a PROFUNDIDAD (un worker, muchos turnos). Guardrail: máx. turnos.
- **Dynamic Workflows**: archivo JavaScript, hasta 1000 agentes, orientado a ANCHURA. Research preview, se activa en `/config`.
- **Plugins/marketplaces**: para empaquetar y distribuir skills/hooks/agentes/MCP entre repos u organización.

## 10. Observabilidad (opcional pero recomendada)

OpenTelemetry exporta a TU backend (nunca a Anthropic): 8 métricas, 24 log events, redacción ON por defecto. Se activa por env (`CLAUDE_CODE_ENABLE_TELEMETRY=1` + `OTEL_EXPORTER_OTLP_ENDPOINT`), no por `settings.json`. `/cost` no aplica en Pro/Max. Detalle y plantilla generada: ver `references/observability.md` y la sección `observability` del spec. Vigila `token.usage`, `cost.usage` y `code_edit_tool.decision` (rechazo alto = tu contexto necesita trabajo).
