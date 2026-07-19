#!/usr/bin/env python3
"""
validate_config.py - Valida la configuración de Claude Code generada.

Uso:
    python3 validate_config.py --dest .

Comprueba: JSON bien formado (.claude/settings.json, .mcp.json), frontmatter de
agentes y skills (name/description presentes, sin < >), estructura del bloque hooks
(evento -> [{matcher, hooks:[{type, command}]}]), y reglas básicas de permisos.
Sin dependencias externas.
"""
import argparse
import json
import re
from pathlib import Path

ok = []
warn = []
err = []


def check_json(path: Path):
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        ok.append(f"JSON válido: {path.name}")
        return data
    except json.JSONDecodeError as e:
        err.append(f"JSON inválido en {path}: {e}")
        return None


def parse_frontmatter(path: Path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        err.append(f"Sin frontmatter: {path}")
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm


def check_agent_or_skill(path: Path, kind: str):
    fm = parse_frontmatter(path)
    for field in ("name", "description"):
        if not fm.get(field):
            err.append(f"{kind} sin '{field}': {path}")
    desc = fm.get("description", "")
    if "<" in desc or ">" in desc:
        err.append(f"{kind} con '<' o '>' en description (no permitido): {path}")
    if len(desc) > 1024:
        warn.append(f"{kind} con description > 1024 chars: {path}")
    if fm.get("name"):
        if not re.match(r"^[a-z0-9-]+$", fm["name"]):
            err.append(f"{kind} con name no-kebab-case: {path} ({fm['name']})")
    # Sobre-permiso: un subagente sin 'tools' hereda TODAS las herramientas.
    if kind == "Agente" and not fm.get("tools"):
        warn.append(f"Agente sin 'tools' (hereda TODAS las herramientas; acótalo): {path}")


def check_hooks(settings):
    hooks = settings.get("hooks", {})
    if not isinstance(hooks, dict):
        err.append("El bloque 'hooks' debe ser un objeto (evento -> lista).")
        return
    valid_events = {
        "SessionStart", "Setup", "SessionEnd", "UserPromptSubmit", "UserPromptExpansion",
        "PreToolUse", "PermissionRequest", "PermissionDenied", "PostToolUse",
        "PostToolUseFailure", "PostToolBatch", "SubagentStart", "SubagentStop",
        "TaskCreated", "TaskCompleted", "Stop", "StopFailure", "TeammateIdle",
        "Notification", "MessageDisplay", "PreCompact", "PostCompact",
        "WorktreeCreate", "WorktreeRemove", "Elicitation", "ElicitationResult",
        "FileChanged", "ConfigChange", "CwdChanged", "InstructionsLoaded",
    }
    for event, entries in hooks.items():
        if event not in valid_events:
            warn.append(f"Evento de hook no reconocido: '{event}' (¿typo? revisa el catálogo).")
        if not isinstance(entries, list):
            err.append(f"hooks['{event}'] debe ser una lista.")
            continue
        for entry in entries:
            if "hooks" not in entry or not isinstance(entry["hooks"], list):
                err.append(f"Entrada de hook en '{event}' sin lista 'hooks'.")
                continue
            for handler in entry["hooks"]:
                if handler.get("type") != "command" or not handler.get("command"):
                    warn.append(f"Handler en '{event}' sin type=command o sin command.")
    if hooks:
        ok.append(f"Estructura de hooks OK ({len(hooks)} evento[s]).")


def check_permissions(settings):
    perms = settings.get("permissions", {})
    if not perms:
        warn.append("Sin bloque 'permissions' en settings.json.")
        return
    deny = perms.get("deny", [])
    if not any(".env" in d for d in deny):
        warn.append("Recomendado: agrega un 'deny' para lectura de .env en permissions.")
    ok.append("Bloque 'permissions' presente.")


def check_secret_bash_bypass(settings):
    """Un deny Read(.env) NO bloquea 'cat .env' via Bash. Avisa si falta la
    defensa por Bash (hook con matcher Bash o regla Bash sobre secretos)."""
    perms = settings.get("permissions", {})
    deny = perms.get("deny", [])
    protects_read_secret = any((".env" in d or "secret" in d.lower()) and d.startswith("Read") for d in deny)
    if not protects_read_secret:
        return
    hooks = settings.get("hooks", {})
    bash_hook = any(
        "Bash" in (entry.get("matcher", "") or "")
        for entries in hooks.values() if isinstance(entries, list)
        for entry in entries
    )
    bash_rule = any("Bash" in r and (".env" in r or "secret" in r.lower())
                    for k in ("deny", "ask") for r in perms.get(k, []))
    if not (bash_hook or bash_rule):
        warn.append(
            "Bypass de secretos: 'deny Read(.env)' no impide 'cat .env' via Bash. "
            "Agrega un hook con matcher 'Bash' (ver hooks-cookbook) o reglas Bash sobre secretos."
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=".")
    args = ap.parse_args()
    dest = Path(args.dest).resolve()

    settings = check_json(dest / ".claude" / "settings.json")
    check_json(dest / ".mcp.json")
    if settings:
        check_hooks(settings)
        check_permissions(settings)
        check_secret_bash_bypass(settings)

    agents_dir = dest / ".claude" / "agents"
    if agents_dir.exists():
        for p in sorted(agents_dir.glob("*.md")):
            check_agent_or_skill(p, "Agente")

    skills_dir = dest / ".claude" / "skills"
    if skills_dir.exists():
        for p in sorted(skills_dir.glob("*/SKILL.md")):
            check_agent_or_skill(p, "Skill")

    # reporte
    for m in ok:
        print("  OK  ", m)
    for m in warn:
        print("  WARN", m)
    for m in err:
        print("  ERR ", m)
    print(f"\n{len(ok)} ok · {len(warn)} avisos · {len(err)} errores")
    raise SystemExit(1 if err else 0)


if __name__ == "__main__":
    main()
