# Observabilidad

Cómo dejar el proyecto listo para medir uso, costo y calidad. Si `observability.enabled` está en el spec, el scaffold escribe `.claude/telemetry.env.example`; este archivo documenta el resto.

## Activar OpenTelemetry

Claude Code exporta métricas, logs y traces por OTel a TU backend (nunca a Anthropic). Se activa por variables de entorno (no por `settings.json`):

```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp        # otlp | prometheus | console
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc  # grpc | http/protobuf
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```
Intervalos por defecto: métricas 60 s, logs 5 s. Carga estas variables antes de abrir `claude` (p.ej. `source .claude/telemetry.env.example`).

## Qué se mide

**8 métricas**: `session.count`, `active_time.total`, `lines_of_code.count`, `commit.count`, `pull_request.count`, `cost.usage`, `token.usage` (por tipo/modelo), `code_edit_tool.decision` (accept/reject). La **tasa de rechazo alta de ediciones** es señal de que tu CLAUDE.md/rules necesitan trabajo.

**24 log events** en 5 grupos (agrupación pedagógica, no oficial): API (7), tools/permisos (3), hooks (4), extensiones/MCP (4), usuario/sesión (6). Todo correlaciona por `prompt.id`.

**Traces** (beta): `+ CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` y `OTEL_TRACES_EXPORTER`.

## Redacción (privacidad) — ON por defecto

Prompts, input/detalle de tools, contenido de tools y cuerpos crudos de API se **redactan por defecto**. Solo se incluyen si haces opt-in explícito por flag (`OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_TOOL_DETAILS`, `OTEL_LOG_RAW_API_BODIES`, …). El pensamiento extendido siempre se redacta. En backends compartidos, deja la redacción ON.

## Sin OTel: opciones básicas

- `/cost` muestra tokens y costo de la sesión — **no disponible en Pro/Max** (no hay cobro por token).
- Dashboard de Consola: métricas de contribución (líneas aceptadas, commits, PRs) en Teams/Enterprise.

## Palancas de costo (relacionado)

Para controlar el gasto que la observabilidad te ayuda a ver: `CLAUDE_CODE_SUBAGENT_MODEL` a un modelo barato, rutear tareas simples a Haiku, y aprovechar la caché de prompts (un hit cuesta 10% del input). Recuerda que output cuesta 5x input.

## Qué añadir al spec

```json
"observability": {
  "enabled": true,
  "endpoint": "http://localhost:4317",
  "protocol": "grpc"
}
```
Con esto, el scaffold genera `.claude/telemetry.env.example` (plantilla, sin secretos). Ajusta el endpoint a tu colector (Grafana/Tempo, SigNoz, Honeycomb, etc.) y NO commitees endpoints privados ni tokens.
