# Plantillas de skills de proyecto

Skills específicas del repo que se generan en `.claude/skills/<nombre>/SKILL.md`. En el `project-spec.json`, cada objeto de `skills` produce una carpeta con su SKILL.md (el campo `body` es el cuerpo Markdown).

Reglas: `name` y `description` obligatorios; description "pushy" (qué + cuándo, sin `<` ni `>`); cuerpo bajo ~500 líneas; usa forma imperativa; explica el porqué, no MUST secos.

## commit-style
```markdown
---
name: commit-style
description: Escribe mensajes de commit del proyecto en Conventional Commits. Use SIEMPRE que se vaya a commitear, generar un mensaje de commit, o preparar un PR.
---
# Estilo de commits

Usa Conventional Commits: `tipo(scope): resumen en imperativo`.

Tipos: feat, fix, docs, style, refactor, test, chore, perf, ci.

**Ejemplos:**
Input: agregué login con JWT
Output: feat(auth): implementar autenticación con JWT

Input: corregí el cálculo de impuestos en el checkout
Output: fix(checkout): corregir cálculo de IVA

Reglas: resumen bajo ~72 caracteres, en minúscula, sin punto final. Cuerpo opcional
explicando el porqué del cambio, no el qué.
```

## pr-review
```markdown
---
name: pr-review
description: Prepara la descripción y checklist de un Pull Request. Use al abrir un PR, redactar su descripción, o pedir una revisión previa antes de subir.
---
# Descripción de Pull Request

Genera la descripción con esta plantilla exacta:

## Qué cambia
(resumen en 1-3 viñetas)

## Por qué
(contexto y motivación)

## Cómo probar
(pasos reproducibles)

## Checklist
- [ ] Tests pasan localmente
- [ ] Sin secretos ni credenciales en el diff
- [ ] Docs actualizadas si cambió comportamiento público

Antes de generar, corre `git diff` contra la rama base para basar la descripción en los
cambios reales, no en suposiciones.
```

## test-writing
```markdown
---
name: test-writing
description: Escribe tests siguiendo las convenciones del proyecto. Use al agregar features o corregir bugs, o cuando el usuario pida tests o cobertura.
---
# Escritura de tests

Sigue el framework y estructura del proyecto (ver CLAUDE.md). Un test por comportamiento;
nombres descriptivos que digan qué se verifica. Cubre el caso feliz y al menos un caso
borde/erróneo. Los tests deben ser deterministas (sin dependencias de red ni de reloj sin
mockear). Corre la suite antes de dar por terminado.
```

## Cómo elegir qué skills generar

- `commit-style` y `pr-review`: casi siempre útiles si hay repo git.
- `test-writing`: si el proyecto tiene (o tendrá) suite de tests.
- Skills de dominio: si hay un procedimiento repetible propio del proyecto (p.ej. "generar reporte fiscal", "crear endpoint CRUD"), crea una skill con los pasos ordenados, un checklist y el formato de salida. Si el procedimiento tiene efectos secundarios (deploy), considera `disable-model-invocation: true` para que solo se dispare manualmente.

## Skills con scripts

Si una skill implica validación compleja o un procedimiento fijo, mete el código en `scripts/` de esa skill y en el SKILL.md instruye a EJECUTARLO (no a leerlo): así no consume contexto y es fiable. Ejemplo de instrucción en el cuerpo: "Ejecuta `scripts/validate.py <archivo>` y usa su salida".
