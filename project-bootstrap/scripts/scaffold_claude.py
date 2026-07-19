#!/usr/bin/env python3
"""
scaffold_claude.py - Genera la configuración de Claude Code de un proyecto a partir
de un project-spec.json (ver assets/project-spec.example.json para el esquema).

Uso:
    python3 scaffold_claude.py --spec project-spec.json --dest .

Escribe (en --dest): CLAUDE.md, .claude/settings.json, .claude/rules/*.md,
.claude/agents/*.md, .claude/skills/<n>/SKILL.md, .claude/hooks/*.sh, .mcp.json,
docs/PROJECT_BRIEF.md y docs/CLAUDE_CODE_SETUP.md. Sin dependencias externas.
"""
import argparse
import json
import os
import stat
from pathlib import Path


def w(path: Path, text: str, executable: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return path


def yaml_list(items):
    return "[" + ", ".join(json.dumps(str(i)) for i in items) + "]"


def bullets(items, prefix="- "):
    return "\n".join(f"{prefix}{i}" for i in items) if items else "_(sin definir)_"


# ---------- generadores por sección ----------

def gen_claude_md(spec):
    p = spec.get("project", {})
    cm = spec.get("claude_md", {})
    stack = p.get("stack", {})
    stack_line = " / ".join(
        v for v in [stack.get("language"), stack.get("framework"), stack.get("database")] if v
    ) or "_(sin definir)_"
    cmds = cm.get("commands", {})
    cmd_lines = "\n".join(
        f"- `{k}`: `{v}`" for k, v in cmds.items() if v
    ) or "_(sin definir)_"
    return f"""# {p.get('name', 'Proyecto')}

Objetivo: {p.get('objective', p.get('description', '_(sin definir)_'))}

## Stack
{stack_line}

## Arquitectura
{cm.get('architecture', '_(describe el mapa de carpetas y responsabilidades)_')}

## Convenciones
{cm.get('conventions', '_(estilo, naming y patrones; el detalle fino va en .claude/rules)_')}

## Comandos
{cmd_lines}

## Importante
{bullets(cm.get('important', []))}

> Recordatorio: este archivo es GUÍA. Las reglas que deben cumplirse SIEMPRE
> viven en permisos (`deny`) o en hooks (`exit 2`), no aquí.
"""


def gen_settings(spec):
    perms = spec.get("permissions", {})
    settings = {}
    if perms:
        settings["permissions"] = {
            k: perms.get(k, []) for k in ("allow", "ask", "deny") if perms.get(k)
        }
    # agrupar hooks por evento
    hooks_by_event = {}
    for h in spec.get("hooks", []):
        event = h["event"]
        entry = {
            "matcher": h.get("matcher", ""),
            "hooks": [{"type": "command", "command": _hook_cmd(h)}],
        }
        hooks_by_event.setdefault(event, []).append(entry)
    if hooks_by_event:
        settings["hooks"] = hooks_by_event
    return json.dumps(settings, indent=2, ensure_ascii=False) + "\n"


def _hook_cmd(h):
    cmd = h["command"]
    # rutas relativas dentro de .claude se prefijan con $CLAUDE_PROJECT_DIR
    if cmd.startswith(".claude/"):
        return "$CLAUDE_PROJECT_DIR/" + cmd
    return cmd


def gen_agent(agent):
    fm = [f"name: {agent['name']}", f"description: {agent['description']}"]
    if agent.get("tools"):
        fm.append(f"tools: {agent['tools']}")
    if agent.get("disallowedTools"):
        fm.append(f"disallowedTools: {agent['disallowedTools']}")
    if agent.get("model"):
        fm.append(f"model: {agent['model']}")
    if agent.get("isolation"):
        fm.append(f"isolation: {agent['isolation']}")
    body = agent.get("prompt", "").strip() or "Describe aquí el rol y las instrucciones del subagente."
    return "---\n" + "\n".join(fm) + "\n---\n\n" + body + "\n"


def gen_skill(skill):
    fm = [f"name: {skill['name']}", f"description: {skill['description']}"]
    if skill.get("allowed-tools"):
        fm.append(f"allowed-tools: {skill['allowed-tools']}")
    body = skill.get("body", "").strip() or "# " + skill["name"] + "\n\nInstrucciones de la skill."
    return "---\n" + "\n".join(fm) + "\n---\n\n" + body + "\n"


def gen_rule(rule):
    content = rule.get("content", "").strip()
    if rule.get("paths"):
        return f"---\npaths: {yaml_list(rule['paths'])}\n---\n\n{content}\n"
    return content + "\n"


def gen_mcp(mcp_list):
    servers = {}
    for s in mcp_list:
        entry = {"command": s.get("command", "npx"), "args": s.get("args", [])}
        if s.get("env"):
            entry["env"] = s["env"]
        servers[s["name"]] = entry
    return json.dumps({"mcpServers": servers}, indent=2, ensure_ascii=False) + "\n"


def gen_brief(spec):
    p = spec.get("project", {})
    stack = p.get("stack", {})
    stack_line = " / ".join(
        v for v in [stack.get("language"), stack.get("framework"), stack.get("database")] if v
    ) or "_(sin definir)_"
    return f"""# Project Brief · {p.get('name', 'Proyecto')}

## Objetivo
{p.get('objective', p.get('description', '_(sin definir)_'))}

## Usuarios
{p.get('users', '_(sin definir)_')}

## No-objetivos
{bullets(p.get('non_goals', []))}

## Stack
{stack_line}

## Hitos
{bullets(p.get('milestones', []))}

## Riesgos
{bullets(p.get('risks', []))}
"""


def gen_setup_doc(spec):
    agents = [a["name"] for a in spec.get("agents", [])]
    skills = [s["name"] for s in spec.get("skills", [])]
    hooks = [f"{h['event']} ({h.get('matcher', '*') or '*'})" for h in spec.get("hooks", [])]
    mcp = [m["name"] for m in spec.get("mcp", [])]
    rules = [r["name"] for r in spec.get("rules", [])]
    obs = spec.get("observability", {}).get("enabled")
    obs_line = (
        "Generado `.claude/telemetry.env.example`. Cárgalo con `source` antes de `claude`. Ver `references/observability.md`."
        if obs else "_(no configurada; ver `references/observability.md` para activarla)_"
    )
    return f"""# Configuración de Claude Code generada

Este proyecto fue inicializado con la skill `project-bootstrap`.

## Subagentes (.claude/agents/)
{bullets(agents) if agents else '_(ninguno)_'}

## Skills (.claude/skills/)
{bullets(skills) if skills else '_(ninguna)_'}

## Hooks (.claude/settings.json)
{bullets(hooks) if hooks else '_(ninguno)_'}

## Rules (.claude/rules/)
{bullets(rules) if rules else '_(ninguna)_'}

## Servidores MCP (.mcp.json)
{bullets(mcp) if mcp else '_(ninguno)_'}

## Observabilidad
{obs_line}

## Próximos pasos
- Exporta los tokens de los servidores MCP como variables de entorno (nunca los commitees).
- Abre el proyecto con `claude` y verifica los servidores con `/mcp`.
- Prueba un subagente pidiendo, por ejemplo, una revisión de código.
- Revisa `.claude/settings.json` y ajusta permisos/hooks si hace falta.
"""


def gen_telemetry_example(spec):
    obs = spec.get("observability", {})
    endpoint = obs.get("endpoint", "http://localhost:4317")
    protocol = obs.get("protocol", "grpc")
    return f"""# Telemetria de Claude Code (OpenTelemetry).
# Carga estas variables en tu entorno ANTES de abrir `claude`:  source .claude/telemetry.env.example
# NO commitees valores sensibles (endpoints privados, tokens). La redaccion esta ON por defecto.

export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL={protocol}
export OTEL_EXPORTER_OTLP_ENDPOINT={endpoint}

# Redaccion (privacidad): prompts, inputs y cuerpos de API se redactan por defecto.
# Descomenta SOLO lo que necesites y con conciencia de lo que expone:
# export OTEL_LOG_USER_PROMPTS=1
# export OTEL_LOG_TOOL_DETAILS=1

# Metricas clave a vigilar: token.usage, cost.usage, code_edit_tool.decision (accept/reject).
# En Pro/Max, /cost no aplica; usa este pipeline OTel o el dashboard de Consola.
"""


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description="Genera la config .claude desde un project-spec.json")
    ap.add_argument("--spec", required=True, help="Ruta al project-spec.json")
    ap.add_argument("--dest", default=".", help="Directorio raíz del proyecto")
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    dest = Path(args.dest).resolve()
    written = []

    # CLAUDE.md
    written.append(w(dest / "CLAUDE.md", gen_claude_md(spec)))

    # settings.json
    written.append(w(dest / ".claude" / "settings.json", gen_settings(spec)))

    # agents
    for a in spec.get("agents", []):
        written.append(w(dest / ".claude" / "agents" / f"{a['name']}.md", gen_agent(a)))

    # skills
    for s in spec.get("skills", []):
        written.append(w(dest / ".claude" / "skills" / s["name"] / "SKILL.md", gen_skill(s)))

    # rules
    for r in spec.get("rules", []):
        written.append(w(dest / ".claude" / "rules" / f"{r['name']}.md", gen_rule(r)))

    # hooks scripts (si el spec trae el cuerpo del script)
    for h in spec.get("hooks", []):
        script_body = h.get("script")
        cmd = h.get("command", "")
        if script_body and cmd.startswith(".claude/"):
            written.append(w(dest / cmd, script_body if script_body.endswith("\n") else script_body + "\n", executable=True))

    # .mcp.json
    if spec.get("mcp"):
        written.append(w(dest / ".mcp.json", gen_mcp(spec["mcp"])))

    # observabilidad (opcional)
    if spec.get("observability", {}).get("enabled"):
        written.append(w(dest / ".claude" / "telemetry.env.example", gen_telemetry_example(spec)))

    # docs
    written.append(w(dest / "docs" / "PROJECT_BRIEF.md", gen_brief(spec)))
    written.append(w(dest / "docs" / "CLAUDE_CODE_SETUP.md", gen_setup_doc(spec)))

    # resumen
    print("Archivos generados:")
    for p in written:
        print("  +", p.relative_to(dest))
    print(f"\nTotal: {len(written)} archivos en {dest}")
    print("Siguiente: valida con  python3 scripts/validate_config.py --dest", args.dest)


if __name__ == "__main__":
    main()
