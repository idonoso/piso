---
name: gestionar-piso
description: Cambia el estado de gestión de un piso en pisos.json. Usar cuando el usuario diga "cambia el estado del piso", "marca el piso como contactado", "marca como visitado", "marca como descartado", "marca como no disponible", "actualiza la gestión del piso", "gestiona el piso", "cambia la gestión del piso", "estado de gestión", "piso contactado", "piso visitado", "piso descartado", "piso no disponible", "cambia estado", o cualquier variación en la que se quiera actualizar el estado de gestión de un piso concreto.
---

# Skill: gestionar-piso

Cambia el campo `gestion` de un piso en `pisos.json`, actualizando también los campos de fecha y descarte que correspondan según el nuevo estado.

## Rutas base

- Datos: `/Users/ignacio/Sites/casa/pisos.json`

## Estados disponibles

| Clave JSON | Badge | Visible por defecto |
|---|---|---|
| `pendiente_contactar` | Nuevo | ✅ |
| `pendiente_visita` | Contactado | ✅ |
| `pendiente_programar_visita` | Pdte. programar visita | ✅ |
| `visita_programada` | Visita 📅 | ✅ |
| `visitado` | Visitado | ✅ |
| `descartado` | Descartado | ❌ |
| `no_disponible` | No disponible | ❌ |

---

## Paso 1: Identificar el piso

Leer `/Users/ignacio/Sites/casa/pisos.json`.

Buscar el piso que menciona el usuario por:
- ID exacto (ej. `idealista_111504013`)
- Dirección, barrio o distrito (comparación insensible a mayúsculas y acentos)
- Descripción parcial del mensaje (ej. "el de Carabanchel", "el piso barato de Usera", "el de 3 habitaciones en Vallecas")

**Si hay más de un candidato**, mostrar lista numerada con datos breves (dirección, precio, estado actual) y pedir al usuario que confirme cuál.

**Si no se encuentra ninguno**, decirlo al usuario y pedirle que lo aclare (ID, dirección, o descripción más concreta).

Una vez localizado, mostrar ficha breve:

```
📍 [dirección o barrio], [distrito] — [precio]€ — [m2]m² — Nota: [puntuacion_general]/10
Estado actual: [badge del estado actual]
```

---

## Paso 2: Determinar el nuevo estado

Si el usuario ya indicó el estado en su mensaje (ej. "marca como contactado", "ponlo como no disponible"), mapear la intención al valor de clave:

| Intención del usuario | Clave destino |
|---|---|
| nuevo, sin contactar, restablecer | `pendiente_contactar` |
| contactado, hemos contactado, ya contactado | `pendiente_visita` |
| pendiente de programar visita, concretando visita, sin fecha aún | `pendiente_programar_visita` |
| visita programada, visita confirmada, tiene visita | `visita_programada` |
| visitado, ya lo he visto, hemos ido | `visitado` |
| descartar, descartado, no me interesa, rechazar | `descartado` |
| no disponible, vendido, ya no está, retirado | `no_disponible` |

Si la intención **no está clara**, mostrar la lista de opciones y esperar respuesta:

```
¿A qué estado quieres cambiar?
  1. Nuevo                      (pendiente_contactar)
  2. Contactado                 (pendiente_visita)
  3. Pdte. programar visita     (pendiente_programar_visita)
  4. Visita programada          (visita_programada)
  5. Visitado                   (visitado)
  6. Descartado                 (descartado)
  7. No disponible              (no_disponible)
```

---

## Paso 3: Recoger datos adicionales

Según el estado destino, pedir datos opcionales o requeridos:

### → `pendiente_visita`
Preguntar: "¿Fecha en que lo contactaste? (ej. hoy, 2026-06-10, o deja en blanco para no registrarla)"
- Si responde con una fecha o "hoy" → guardar en `fecha_contacto` (formato `YYYY-MM-DD`; "hoy" = `currentDate` del contexto del sistema)
- Si deja en blanco o dice "no" → no modificar `fecha_contacto`

### → `pendiente_programar_visita`
Sin datos adicionales. Continuar directamente al Paso 4. (Este estado indica que se ha contactado y se está intentando concretar una fecha de visita, pero todavía no hay fecha confirmada.)

### → `visita_programada`
Preguntar: "¿Fecha y hora de la visita? (ej. 15 de junio a las 17:00, o deja en blanco)"
- Si responde → guardar `fecha_visita` en `YYYY-MM-DD` y `hora_visita` en `HH:MM` (24h)
- Si deja en blanco → no modificar esos campos

### → `visitado`
Si `fecha_visita` es `null` en el piso, preguntar: "¿Cuándo fue la visita?"
- Si responde → guardar en `fecha_visita`
- Si deja en blanco → no modificar

### → `descartado`
Preguntar: "¿Cuál es el motivo del descarte?"
- Guardar la respuesta en `motivo_descarte`. Si el usuario no da motivo, usar `"Sin especificar"`.

### → `no_disponible`
Sin datos adicionales. Continuar directamente al Paso 4.

### → `pendiente_contactar`
Sin datos adicionales. Continuar directamente al Paso 4.

---

## Paso 4: Actualizar pisos.json

Localizar el objeto del piso en el array por su `id`. Actualizar **únicamente** los campos que correspondan:

**Siempre:**
- `gestion` → nueva clave de estado

**Según el estado destino:**
- `pendiente_visita` → `fecha_contacto` si se proporcionó
- `pendiente_programar_visita` → sin campos extra
- `visita_programada` → `fecha_visita` y/o `hora_visita` si se proporcionaron
- `visitado` → `fecha_visita` si no estaba ya registrada y el usuario la proporcionó
- `descartado` → `descartado: true`, `motivo_descarte: "[motivo]"`
- `no_disponible` → sin campos extra
- `pendiente_contactar` → `descartado: false`, `motivo_descarte: null` (limpiar estado de descarte si lo había)

Escribir el archivo con indentación de 2 espacios. **No reordenar el array**, solo modificar el objeto correspondiente en su posición actual.

---

## Paso 5: Confirmar

Mostrar confirmación del cambio realizado:

```
✅ Actualizado: [id del piso]
   📍 [dirección o barrio]
   Estado: [badge anterior] → [badge nuevo]
   [Si se actualizó fecha_contacto: Fecha contacto: YYYY-MM-DD]
   [Si se actualizó fecha_visita: Fecha visita: YYYY-MM-DD HH:MM]
   [Si se actualizó motivo_descarte: Motivo: "..."]
```

---

## Notas importantes

- Usar `currentDate` del contexto del sistema para resolver fechas relativas ("hoy", "ayer").
- No modificar ningún otro campo del piso que no esté listado en el Paso 4.
- Si el piso ya tenía `gestion` igual al estado destino, avisar: "El piso ya estaba en ese estado" y preguntar si quiere continuar igualmente (por si quiere actualizar fechas).
- Cuando se cambia a `pendiente_contactar` desde `descartado`, limpiar `descartado` y `motivo_descarte` para que el piso vuelva a ser visible en el listado por defecto.
