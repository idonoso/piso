---
name: analyze-piso
description: Analiza anuncios de pisos desde portales inmobiliarios, extrae datos estructurados, evalúa las fotos con visión y guarda en data/pisos.json. Usar cuando el usuario diga "analiza este piso", "analiza la URL de idealista", "guarda este piso", "evalúa este apartamento", "puntúa este inmueble", "añade este piso a pisos.json", "analiza el anuncio", "procesa esta vivienda", "analiza el piso de fotocasa", "analiza el piso de habitaclia", o cuando proporcione directamente una URL de idealista.com, fotocasa.es, habitaclia.com o pisos.com. También usar si el usuario quiere descartar un piso ya guardado o actualizar su comentario personal.
---

# Skill: analyze-piso

Extrae datos estructurados de un anuncio inmobiliario, analiza las fotos con visión, verifica criterios mínimos, calcula puntuaciones y guarda en `pisos.json`.

## Rutas base

- Proyecto: `/Users/ignacio/Sites/casa/`
- Datos: `/Users/ignacio/Sites/casa/pisos.json`
- Criterios de puntuación: `.claude/skills/analyze-piso/references/scoring-criteria.md`

## Portales soportados

- `idealista.com`
- `fotocasa.es`
- `habitaclia.com`
- `pisos.com`

Si el dominio no es ninguno de estos, intentar igualmente y advertir al usuario.

---

## Paso 1: Recibir URL y generar ID único

Si el usuario ya proporcionó una URL en su mensaje, usarla directamente.

Si no la proporcionó, preguntar: "¿Cuál es la URL del anuncio que quieres analizar?"

Detectar el portal a partir del dominio de la URL y guardarlo en el campo `portal`.

**Generar el `id` único del piso:**

Extraer la secuencia de dígitos más larga del path de la URL (el ID nativo del portal) y combinarla con el nombre del portal:

| Portal | Ejemplo URL | ID generado |
|---|---|---|
| idealista | `.../inmueble/111504013/` | `idealista_111504013` |
| fotocasa | `.../anunci/12345678` | `fotocasa_12345678` |
| habitaclia | `.../piso/87654321` | `habitaclia_87654321` |
| pisos.com | `.../vivienda/54321` | `pisos_54321` |

Regla: buscar en el path de la URL la secuencia de dígitos más larga (mínimo 5 dígitos). Construir el ID como `{portal}_{digitos}`.

**Si no se encuentran dígitos** en la URL, generar un ID secuencial: leer pisos.json (si existe), contar cuántos tienen ID con prefijo `piso_`, y usar `piso_{NNN}` con 3 dígitos cero-rellenos (piso_001, piso_002...).

El `id` debe ser único. Si al cargar pisos.json (Paso 7) se detecta que ya existe otro piso con el mismo `id` pero distinta `url`, añadir sufijo `_b`, `_c`, etc.

---

## Paso 2: Obtener el contenido del anuncio

Hacer fetch de la URL con `WebFetch`.

**Si WebFetch devuelve error (403, 429, bloqueo anti-bot, contenido vacío):**
Pedir al usuario: "No he podido acceder al anuncio directamente (el portal puede bloquear el acceso automático). Por favor, abre el anuncio en tu navegador, selecciona todo el texto (Cmd+A, Cmd+C) y pégalo aquí."

Continuar con el texto pegado exactamente igual que con el HTML obtenido por fetch.

---

## Paso 3: Extraer datos del anuncio

Del HTML o texto obtenido, extraer todos los campos posibles. Si un campo no aparece, asignar `null` (no cadena vacía).

**Campos a extraer:**

| Campo | Tipo | Notas |
|---|---|---|
| `precio` | number | Euros sin IVA. "195.000 €" → 195000 |
| `precio_m2` | number | Si no aparece, calcular: `precio / m2` (redondear a 2 decimales) |
| `m2` | number | Metros útiles si se distinguen del construido |
| `m2_construidos` | number\|null | Solo si el anuncio lo especifica |
| `habitaciones` | number | |
| `banos` | number | |
| `planta` | string | Mantener el texto original: "Bajo", "1", "2", "Ático", etc. |
| `ascensor` | boolean\|null | `true`/`false`/`null` si no se menciona |
| `exterior` | boolean\|null | `true` si dice "exterior", `false` si dice "interior", `null` si no se indica |
| `terraza` | boolean\|null | Incluye balcón real (no balcón Juliette) |
| `garaje` | boolean\|null | `true` solo si está incluido en el precio |
| `trastero` | boolean\|null | |
| `orientacion` | string\|null | "Sur", "Este", "Sur-Oeste", etc. |
| `calefaccion` | string\|null | "Gas natural", "Eléctrica", "Aerotermia", "Sin calefacción", etc. |
| `aire_acondicionado` | boolean\|null | |
| `estado` | string\|null | "A reformar", "Buen estado", "Reformado", "Obra nueva", etc. |
| `ano_construccion` | number\|null | |
| `certificado_energetico` | string\|null | "A", "B", "C", "D", "E", "F", "G", "En trámite" |
| `direccion` | string\|null | Dirección visible en el anuncio |
| `barrio` | string\|null | |
| `ciudad` | string\|null | |
| `descripcion` | string | Texto completo de la descripción del anuncio |
| `urls_fotos` | array | Array de URLs absolutas de las imágenes. Si las URLs son relativas, intentar construirlas con el dominio base. |

---

## Paso 4: Analizar fotos con visión

Cargar como imágenes las primeras **8 URLs** del array `urls_fotos` usando WebFetch en modo imagen (pasar la URL directamente como contenido de imagen al contexto visual).

### 4a. Detectar fotos generadas o mejoradas con IA

**Antes de evaluar el contenido**, inspeccionar cada foto en busca de indicadores de generación o mejora con IA:

- Marca de agua o texto visible: "Contenido generado por IA", "Generated by AI", "✦ AI", "Virtual staging", "Home staging virtual", o similares
- Aspectos visuales sospechosos: iluminación perfecta irreal, muebles flotantes o mal integrados, texturas repetidas, proporciones incorrectas, reflejos imposibles, detalles borrosos o incoherentes en bordes y fondos
- Inconsistencia entre fotos: una foto del pasillo muestra un estado diferente al del salón (ej: pasillo parece real y oscuro, salón parece un render perfecto)

**Contabilizar cuántas fotos de las analizadas son sospechosas de IA** y guardar el ratio: `fotos_ia: N de M analizadas`.

**Si hay fotos con IA**, incluir en `notas_analisis` una alerta prominente:
> ⚠️ ALERTA FOTOS IA: N de las M fotos analizadas muestran indicios de generación o mejora con IA. El estado real del piso puede diferir significativamente de las imágenes. Se recomienda visita presencial antes de tomar cualquier decisión.

**Penalización automática sobre `puntuacion_fotos`** según ratio de fotos con IA:
- 1-2 fotos IA de 8: -0.5
- 3-4 fotos IA de 8: -1.0
- 5-6 fotos IA de 8: -1.5
- 7-8 fotos IA de 8: -2.0 (considerar `puntuacion_fotos` como no fiable)

### 4b. Evaluar contenido de las fotos

Para cada foto visible (independientemente de si es IA o real), evaluar:
- Luminosidad y amplitud percibida del espacio
- Estado de conservación y limpieza
- Calidad del mobiliario y acabados
- Elementos positivos (vistas, terraza, cocina moderna, suelos de calidad)
- Elementos negativos (humedad, deterioro, desorden extremo)

Consultar `references/scoring-criteria.md` para aplicar los factores de bonus y penalización exactos.

Producir:
- `puntuacion_fotos`: número de 1 a 10 (puede ser decimal: 7.5, 6.0, etc.), ya con la penalización por IA aplicada
- Sección `FOTOS` para `notas_analisis` con este formato exacto:

```
FOTOS ([puntuacion_fotos]/10)
[N] fotos analizadas — [X] con IA, [Y] reales.
• [Observación 1 sobre contenido o estancias]
• [Observación 2]
• [Observación 3 si aplica]
```

**Si las fotos no son accesibles** (URLs bloqueadas, relativas no resolubles, etc.):
- Asignar `puntuacion_fotos: null`
- Sección fotos: `FOTOS\nNo se pudieron analizar las fotos.`

---

## Paso 5: Verificar criterios mínimos

Leer los criterios mínimos de `references/scoring-criteria.md`.

Verificar:
1. `m2 >= 50` (o `m2` es null → no verificable)
2. `ascensor == true` (si es null → advertir como dato no confirmado)
3. `planta` no es "Bajo", "Entresuelo", "Sótano", "Semi-sótano" (insensible a mayúsculas y acentos)
4. `exterior == true` (si es null → advertir como dato no confirmado)

Si algún criterio falla, construir lista de incumplimientos y mostrar:

```
⚠️ Este piso no cumple los criterios mínimos:
  - [criterio 1 incumplido]
  - [criterio 2 incumplido]

¿Deseas descartarlo o guardarlo igualmente?
```

Esperar respuesta del usuario:
- "Descartar" → continuar con `descartado: true`, preguntar motivo o usar el/los criterios incumplidos como motivo automático
- "Guardar" o "guardar igualmente" → continuar con `descartado: false`, pero dejar nota en `notas_analisis`
- Si todos los criterios se cumplen → continuar sin interrupción con `descartado: false`

---

## Paso 6: Calcular puntuación general y estimación de negociación

Consultar `references/scoring-criteria.md` para la tabla de pesos y ajustes completa.

**Fórmula:** `puntuacion_general = (caracteristicas * 0.40) + (ubicacion * 0.35) + (puntuacion_fotos * 0.25)`

Si `puntuacion_fotos` es null, usar: `(caracteristicas * 0.54) + (ubicacion * 0.46)`

Redondear a 1 decimal. Clamp entre 1.0 y 10.0.

Construir las secciones de `notas_analisis` con este formato exacto (usar `\n` como separador de líneas dentro del string JSON):

```
CARACTERÍSTICAS ([puntuacion_caracteristicas]/10)
• [Factor aplicado con su ajuste, ej: "Base 5; 3ª planta con ascensor (+0)"]
• [Siguiente factor]

UBICACIÓN ([puntuacion_ubicacion]/10)
• [Zona o barrio y por qué se valora así]
• [Acceso a transporte u otros elementos relevantes]

PRECIO
• [precio_m2] €/m² — [caro/ajustado/barato] para la zona ([referencia si se conoce])
• [Ajuste aplicado y motivo]

PUNTOS FUERTES
• [Punto 1]
• [Punto 2]
• [Punto 3...]

PUNTOS DÉBILES
• [Punto 1]
• [Punto 2]
• [Punto 3...]
```

La sección FOTOS ya fue construida en el Paso 4. El orden final de secciones en `notas_analisis` es:
1. FOTOS
2. CARACTERÍSTICAS
3. UBICACIÓN
4. PRECIO
5. COMPARATIVA (se añade en el Paso 7b, tras cargar pisos.json)
6. NEGOCIACIÓN (se añade en el siguiente paso)
7. PUNTOS FUERTES
8. PUNTOS DÉBILES

### Estimación de margen de negociación

Consultar la sección "Negociación" de `references/scoring-criteria.md` para los factores exactos.

Calcular `descuento_estimado_pct` (porcentaje sobre el precio anunciado que es razonable pedir) sumando:

**Base para Madrid periférico:** 5%

**Ajustes según características del anuncio:**

| Factor | Ajuste |
|---|---|
| Estado "a reformar" | +5% (coste de obra es palanca real) |
| Precio/m² > 20% sobre la media de zona | +4% |
| Precio/m² > 10% sobre la media de zona | +2% |
| Precio/m² alineado o por debajo de la media | 0% |
| Tiempo publicado > 60 días (si visible en el anuncio) | +3% |
| Tiempo publicado > 30 días | +1% |
| Anunciante es particular (no agencia) | +2% |
| Anunciante es agencia profesional | -1% |
| Honorarios de agencia NO incluidos en el precio | +2% (el comprador tiene más costes reales) |
| Fotos con IA (fiabilidad baja del estado real) | +2% (incertidumbre = más margen a pedir) |
| Piso en muy buen estado / obra nueva | -2% |
| Zona prime o alta demanda | -2% |

Clamp del resultado: entre 3% y 20%.

Calcular:
- `descuento_estimado_pct`: porcentaje redondeado al entero
- `precio_objetivo`: `Math.round(precio * (1 - descuento_estimado_pct / 100) / 1000) * 1000` (redondeado al millar)
- `precio_objetivo_min`: precio con el descuento máximo razonable (+3% sobre el estimado)
- `precio_objetivo_max`: precio con el descuento mínimo razonable (-2% sobre el estimado)

Añadir a `notas_analisis` la sección de negociación con este formato:

```
NEGOCIACIÓN ([descuento_estimado_pct]%)
Precio objetivo: ~[precio_objetivo] € (rango [precio_objetivo_min] – [precio_objetivo_max] €)
• [Factor aplicado 1]
• [Factor aplicado 2]
• [...]
```

---

## Paso 7: Cargar pisos.json existente

Leer `/Users/ignacio/Sites/casa/pisos.json`.

Si el archivo no existe, usar array vacío `[]`.

---

## Paso 7b: Buscar pisos similares para comparación de precio

Con los datos del piso actual y el array cargado, buscar pisos comparables para contextualizar el precio.

**Criterios de similitud** (aplicar todos; relajar si hay menos de 2 resultados):

1. **Zona**: mismo `barrio` (comparación case-insensitive). Si hay < 2 coincidencias, ampliar a mismo distrito o ciudad.
2. **Tamaño**: `m2` dentro de ±30% del piso actual (ej: 70m² → incluir 49–91m²).
3. **Habitaciones**: igual o ±1 respecto al piso actual.
4. **Estado**: preferir mismo `estado` (a reformar / buen estado / reformado / obra nueva), pero incluir todos si quedan < 2 pisos.

**Excluir siempre:** pisos con `descartado: true` o `gestion: 'no_disponible'`. También excluir el propio piso si ya existía en el JSON.

**Calcular con los pisos similares encontrados:**
- `precio_m2_media`: media de sus `precio_m2`
- `precio_m2_min` y `precio_m2_max`: rango
- Diferencia del piso actual: `((precio_m2_actual - media) / media * 100)` redondeado a 1 decimal

**Añadir sección COMPARATIVA a `notas_analisis`** entre PRECIO y NEGOCIACIÓN:

```
COMPARATIVA ([N] pisos similares en [zona])
• Media zona: [media] €/m² (rango [min]–[max] €/m²)
• Este piso: [precio_m2] €/m² — [X% más caro que la media / X% más barato / en línea con la media (±5%)]
• [id o dirección corta piso 1]: [m2]m², [hab]hab, [estado], [precio]€ ([precio_m2]€/m²)
• [id o dirección corta piso 2]: [m2]m², [hab]hab, [estado], [precio]€ ([precio_m2]€/m²)
• [hasta 4 pisos similares ordenados por precio_m2 asc]
```

Si hay 0 o 1 piso similar:
```
COMPARATIVA (sin datos suficientes)
• Solo [N] piso similar en la base de datos — comparación no representativa.
```

**Usar la media de pisos similares como referencia de zona** en el ajuste de negociación del Paso 6 (en lugar de estimaciones genéricas): si el precio/m² del piso actual está >10% sobre la media → aplica el factor "+2%"; si >20% → "+4%".

---

## Paso 8: Detectar duplicados

Buscar en el array cargado si ya existe un objeto con el mismo valor de `url` (comparación exacta).

Si existe:
```
Ya existe un análisis para este piso (analizado el [fecha_analisis]).
¿Deseas sobreescribirlo con el nuevo análisis, o cancelar?
```

- "Sobreescribir" → reemplazar el objeto existente por el nuevo
- "Cancelar" → terminar sin modificar el archivo

---

## Paso 9: Completar datos faltantes (opcional)

Si alguno de estos campos es `null` y no apareció en el anuncio, preguntar al usuario:
- `precio` — sin precio no hay análisis útil
- `m2` — sin m² no se puede calcular precio/m²
- `habitaciones` — campo informativo importante

Formular como: "No he encontrado [campo] en el anuncio. ¿Puedes indicarlo? (o escribe 'desconocido' para dejarlo vacío)"

No preguntar por campos opcionales como `trastero`, `certificado_energetico`, `ano_construccion`.

---

## Paso 10: Construir el objeto final y guardar

Construir el objeto JSON con todos los campos en este orden:

```json
{
  "id": "idealista_111504013",
  "url": "...",
  "portal": "...",
  "fecha_analisis": "YYYY-MM-DD",
  "fecha_contacto": null,
  "fecha_visita": null,
  "descartado": false,
  "motivo_descarte": null,
  "comentario_personal": null,
  "precio": 0,
  "precio_m2": 0.0,
  "m2": 0,
  "m2_construidos": null,
  "habitaciones": 0,
  "banos": 0,
  "planta": "...",
  "ascensor": null,
  "exterior": null,
  "terraza": null,
  "garaje": null,
  "trastero": null,
  "orientacion": null,
  "calefaccion": null,
  "aire_acondicionado": null,
  "estado": null,
  "ano_construccion": null,
  "certificado_energetico": null,
  "direccion": null,
  "barrio": null,
  "ciudad": null,
  "descripcion": "...",
  "urls_fotos": [],
  "puntuacion_fotos": null,
  "puntuacion_general": null,
  "descuento_estimado_pct": null,
  "precio_objetivo": null,
  "precio_objetivo_min": null,
  "precio_objetivo_max": null,
  "notas_analisis": "..."
}
```

La `fecha_analisis` es la fecha actual en formato `YYYY-MM-DD` (consultar el contexto del sistema para la fecha de hoy).

Añadir o reemplazar el piso en el array. Ordenar el array por `fecha_analisis` descendente. Escribir el archivo con indentación de 2 espacios.

---

## Paso 11: Preguntar por comentario personal

Tras mostrar el resumen del piso, preguntar:

"¿Quieres añadir algún comentario o valoración personal sobre este piso?"

- Si el usuario responde con contenido útil → guardar en `comentario_personal` y reescribir el archivo
- Si dice "no", "nada", "no gracias", o algo sin contenido → dejar `comentario_personal: null`

---

## Paso 12: Resumen final

Mostrar al usuario una ficha completa:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏠 [id]  |  📍 [dirección o barrio], [ciudad]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💶 Precio: [precio] € ([precio_m2] €/m²)
📐 [m2] m² útiles | [habitaciones] hab | [banos] baños
🏢 Planta [planta] | Ascensor: [Sí/No] | [Exterior/Interior]
🌿 [Terraza: Sí/No] | Garaje: [Sí/No/—]

⭐ Puntuación fotos:    [puntuacion_fotos]/10
⭐ Puntuación general:  [puntuacion_general]/10

✅ Puntos fuertes:
  - ...

❌ Puntos débiles:
  - ...

📝 Análisis:
[notas_analisis — mostrar con los saltos de línea tal cual, no en una sola línea]

✅ Guardado en pisos.json (piso #[N] en la lista)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Si el piso fue descartado, mostrar también: `🚫 Descartado: [motivo_descarte]`

---

## Operaciones adicionales

### Descartar un piso ya guardado

Si el usuario dice "descarta el piso de [referencia]" o "marca como descartado [referencia]":
1. Localizar el piso en pisos.json por URL, barrio, dirección o descripción parcial
2. Si hay ambigüedad, listar los candidatos y pedir confirmación
3. Preguntar el motivo del descarte
4. Actualizar `descartado: true` y `motivo_descarte: "motivo"` en el archivo

### Actualizar comentario personal

Si el usuario dice "añade un comentario al piso de [referencia]" o "actualiza el comentario de [referencia]":
1. Localizar el piso
2. Pedir o confirmar el nuevo comentario
3. Actualizar `comentario_personal` en el archivo

---

## Notas importantes

- **Idealista bloquea agresivamente el scraping.** Si WebFetch falla, la vía del texto pegado es igual de válida y siempre funciona.
- **Fotos y visión:** pasar las URLs de foto directamente como imágenes al contexto. Si WebFetch no puede cargar imágenes binarias, `puntuacion_fotos` queda `null`.
- **Fechas:** usar la fecha del contexto del sistema (`currentDate`), no intentar generar fechas dinámicamente.
- **No duplicar campos** en el JSON final — `descartado`, `motivo_descarte` y `comentario_personal` aparecen solo una vez al inicio del objeto.
- **Precio/m²:** si el anuncio lo muestra explícitamente, usar ese valor; si no, calcularlo como `Math.round((precio / m2) * 100) / 100`.
