---
name: preguntas-visita
description: Genera preguntas personalizadas para preparar la visita a un piso y las guarda en pisos.json como campo preguntas_visita. Usar cuando el usuario diga "genera preguntas para la visita", "preguntas visita", "prepara la visita", "qué preguntar en la visita", "checklist visita", "qué tengo que preguntar", o cuando mencione una visita a un piso concreto y pida preguntas.
---

# Skill: preguntas-visita

Genera dos listas personalizadas para preparar la visita a un piso: **preguntas** (a hacer al vendedor/agente) y **comprobaciones** (cosas a verificar tú mismo in situ). Todo se guarda en el campo `preguntas_visita` de pisos.json.

**Disparadores:** "genera preguntas para la visita", "preguntas visita", "prepara la visita", "qué preguntar en la visita", "checklist visita", "qué tengo que preguntar", o cuando el usuario menciona una visita a un piso concreto y pide preguntas.

---

## Paso 1: Identificar el piso

Si el usuario menciona un piso concreto (por dirección, barrio, ID o descripción parcial), localizar ese piso en `pisos.json`.

Si no especifica cuál, buscar todos los pisos con `gestion: "visita_programada"` y preguntar cuál si hay más de uno, o usar el único que haya.

Leer `/Users/ignacio/Sites/casa/pisos.json`.

---

## Paso 2: Revisar el piso en profundidad

Antes de generar nada, analizar todos los datos disponibles del piso:

- `descripcion`: leer completa para detectar elementos mencionados o ausentes
- `notas_analisis`: prestar especial atención a puntos débiles, incógnitas y elementos no vistos en fotos
- `comentario_personal`: incorporar inquietudes ya anotadas
- `urls_fotos` + `puntuacion_fotos`: si hay fotos disponibles, revisarlas con visión para detectar estado real de suelos, techos, cocina, baño, humedad, materiales, etc.
- Campos estructurados: `estado`, `ano_construccion`, `m2`, `habitaciones`, `terraza`, `garaje`, `trastero`, `calefaccion`, `aire_acondicionado`, `orientacion`, `certificado_energetico`, `gastos_comunidad`, `honorarios_agencia`, `planta`

El objetivo es generar preguntas y comprobaciones **muy específicas** a ese piso concreto, no genéricas.

---

## Paso 3: Generar las PREGUNTAS (para hacer al vendedor/agente)

Generar entre 8 y 14 preguntas concretas. Mezclar las del bloque base con las condicionales según el piso.

### Preguntas base (siempre presentes)
- ¿Hay derramas pendientes o aprobadas en la comunidad?
- ¿Cuánto son los gastos de comunidad mensuales? (si no consta en el anuncio)
- ¿Por qué venden? ¿Cuánto tiempo llevan en venta?
- ¿Ha pasado la ITE el edificio? ¿Estado de fachada y zonas comunes?
- ¿Cuánto es el IBI anual?
- ¿Cuándo fue la última reforma y qué se reformó?
- ¿De qué año es la instalación eléctrica? ¿Tiene cuadro con diferencial y magnetotérmicos?
- ¿De qué año es la instalación de fontanería? ¿Son tuberías de cobre, PVC o plomo?
- ¿La vivienda tiene alguna carga hipotecaria, embargo u otra carga registral?
- ¿La calefacción tiene termostato automático o es manual? ¿Hay termostato por estancias o uno central?

### Preguntas condicionales según características del piso

| Situación | Preguntas a añadir |
|---|---|
| Planta 1ª o baja | ¿Cuánto ruido llega de la calle? ¿Los vecinos de abajo tienen problemas de humedad? |
| 3+ habitaciones en ≤70m² | ¿Cuánto miden exactamente las habitaciones (útil, sin armarios)? |
| Terraza | ¿Es totalmente privada o compartida? ¿Cuánto mide? ¿Tiene licencia si está cerrada? |
| Terraza = null | ¿Hay algún balcón, terraza o espacio exterior? |
| Cocina sin reformar | ¿Hay salida de humos homologada? ¿Tiene toma de gas y espacio para lavavajillas? |
| Aire acondicionado = null | ¿Hay AC o preinstalación? ¿Hay posibilidad de instalar split? |
| Trastero = null | ¿Hay trastero y está incluido en el precio? |
| Garaje = null | ¿Hay plaza de garaje disponible o en alquiler? |
| Honorarios agencia no especificados | ¿Hay honorarios de agencia adicionales al precio? ¿A cuánto ascienden? |
| Año construcción anterior a 1980 | ¿Las ventanas son las originales o han sido cambiadas? ¿Hay algún elemento de amianto conocido? |
| Certificado energético en trámite o nulo | ¿Cuándo estará disponible el certificado energético? |
| Estado "a reformar" | ¿Hay presupuestos de reforma disponibles? ¿Se puede acceder antes del cierre para medir? |
| Sin calefacción / calefacción eléctrica | ¿Se puede instalar calefacción central o aerotermia? ¿Por dónde pasaría? |
| Orientación nula | ¿A qué orientación dan las ventanas principales? ¿Entra sol directo y en qué horas? |
| Precio/m² elevado (>10% sobre zona) | ¿Hay margen de negociación sobre el precio? |
| Anunciante particular | ¿Cuánto tiempo llevan en el piso? |
| m² útiles no especificados | ¿Cuántos m² útiles tiene (sin contar paredes y zonas comunes)? |
| Notas mencionan elemento no visto en fotos | Preguntar específicamente por ese elemento (ej. "¿Cómo está el baño?") |

---

## Paso 4: Generar las COMPROBACIONES (para verificar tú mismo in situ)

Generar entre 8 y 14 comprobaciones concretas. Son cosas que hay que hacer, observar o medir durante la visita, no preguntar.

### Comprobaciones base (siempre)
- Medir las habitaciones con metro o app (anotar largo × ancho de cada una)
- Buscar humedades: revisar esquinas de techos, bajo ventanas, detrás de muebles y en baños
- Abrir grifos: comprobar presión del agua y tiempo hasta que sale caliente
- Escuchar: pedir silencio 1 minuto y anotar ruidos (tráfico, vecinos, ascensor, cañerías)
- Revisar el cuadro eléctrico: ver si tiene diferencial, cuántos circuitos y si hay fusibles anticuados
- Comprobar el cierre de ventanas y si aíslan bien (pasar la mano por el marco buscando corrientes)
- Revisar el estado del portal, escaleras comunes y fachada exterior
- Comprobar si hay tendedero o espacio habilitado para tender ropa
- Fotografiar todos los elementos con dudas o defectos detectados

### Comprobaciones condicionales según características del piso

| Situación | Comprobaciones a añadir |
|---|---|
| Año construcción anterior a 1970 | Buscar tuberías de plomo o cableado sin funda (en zonas vistas: bajo fregadero, caja de registro) |
| Año construcción anterior a 1980 | Inspeccionar suelos vinílicos o falsos techos que puedan contener amianto |
| Notas o fotos mencionan humedad | Ir directamente a esa zona, tocar la pared (si está fría y húmeda, hay problema activo) |
| Estado "a reformar" | Fotografiar toda la cocina y baño al detalle / comprobar si hay grietas estructurales en paredes de carga |
| Terraza cerrada | Verificar si el cerramiento tiene aspecto de licencia o es una obra ilegal |
| Terraza / balcón | Comprobar si hay marcas de goteras en el techo justo debajo de la terraza |
| Cocina sin reformar | Encender el fuego / comprobar el extractor / medir si cabe lavavajillas |
| Planta baja o 1ª | Revisar la parte baja de las paredes en busca de humedad por capilaridad |
| Sin calefacción | Identificar por dónde pasarían los tubos de la calefacción central o el split |
| Piso de esquina | Revisar la pared exterior buscando condensación o manchas de humedad |
| Baño no visible en fotos | Fotografiar el baño completo: suelos, azulejos, ventilación, silicona, presión de la ducha |
| Habitaciones pequeñas o sin medidas | Medir si entra una cama de 150 con mesitas a cada lado |
| Fotos muestran gotelé en paredes | Comprobar si hay grietas ocultas bajo el gotelé (pasar la mano por la pared) |
| Armarios empotrados mencionados | Abrir todos los armarios: comprobar profundidad real y estado interior |
| Piso con plano disponible | Llevar el plano impreso y cotejar medidas reales vs. plano |
| Edificio antiguo sin ascensor declarado | Verificar el número real de escalones hasta el piso |

### Comprobaciones basadas en notas de análisis y fotos
Revisar `notas_analisis`, `comentario_personal` y las fotos del piso. Para cada punto débil concreto o elemento no visto, añadir una comprobación específica (ej. "Las fotos muestran posibles marcas de humedad en el techo del salón → revisar ese techo in situ y tocar la zona").

---

## Paso 5: Ordenar por importancia

**Preguntas**: ordenar de mayor a menor impacto en la decisión de compra:
1. Deal-breakers (cargas, derramas, estado real oculto)
2. Impacto económico (IBI, comunidad, honorarios, reforma)
3. Detalles prácticos (orientación, certificado, electrodomésticos)

**Comprobaciones**: ordenar de mayor a menor urgencia:
1. Estructurales y ocultas (humedades, electricidad, fontanería)
2. Dimensiones y funcionalidad (medidas, tendedero, armarios)
3. Estado cosmético (ventanas, azulejos, puertas)

---

## Paso 6: Recoger fecha y hora de la visita

Si el usuario ha proporcionado fecha y/o hora de la visita en su mensaje (ej. "el viernes a las 5", "el jueves 12 de junio por la mañana"), extraerlas y convertirlas a formato absoluto:

- `fecha_visita`: `YYYY-MM-DD`
- `hora_visita`: `HH:MM` en formato 24h (ej. `"17:00"`)

Si no se menciona fecha, no modificar `fecha_visita` ni añadir `hora_visita`.

Si el usuario menciona un número de contacto o referencia, guardarlo en `comentario_personal` junto con la información ya existente, sin borrar nada.

---

## Paso 7: Guardar en pisos.json

Actualizar el objeto del piso en `/Users/ignacio/Sites/casa/pisos.json` con todos los cambios de una sola escritura:

- `preguntas_visita`: objeto con dos arrays: `{ "preguntas": [...], "comprobaciones": [...] }`. Si ya existe, preguntar si sobreescribir o añadir al final.
- `fecha_visita`: fecha en `YYYY-MM-DD` si se proporcionó
- `hora_visita`: hora en `HH:MM` si se proporcionó
- `gestion`: cambiar a `"visita_programada"` si había fecha de visita y el campo era `"pendiente_contactar"`
- `comentario_personal`: actualizar si había info adicional

---

## Paso 8: Confirmar y mostrar

Mostrar el resultado en dos bloques claramente diferenciados:

**PREGUNTAS PARA EL VENDEDOR / AGENTE**
Lista numerada de preguntas.

**COMPROBACIONES IN SITU**
Lista numerada de cosas a verificar tú mismo.

Informar que también están disponibles en la ficha de detalle del piso (`detalle.html?id=PISO_ID`) como checklist interactivo donde puede ir marcando durante la visita.
