---
name: editar-presupuesto
description: Añade, edita o elimina elementos (materiales, mano de obra o muebles) en la calculadora de presupuesto de obra `presupuesto.html`. Usar cuando el usuario diga "añade [elemento] al presupuesto", "añade el sofá/suelo/armario/etc.", "pon otra calidad/opción de precio", "cambia el precio de", "actualiza la cantidad de", "quita el elemento", "elimina del presupuesto", "asigna esto a la fase X", "edita el presupuesto de la obra", o cualquier variación en la que se quiera modificar el catálogo de elementos del presupuesto de reforma/amueblamiento.
---

# Skill: editar-presupuesto

Añade, edita o elimina elementos del catálogo de `presupuesto.html`, la calculadora de presupuesto de obra y amueblamiento (piso ~90m² en Madrid).

## Ruta base

- Archivo: `/Users/ignacio/Sites/casa/presupuesto.html` (HTML autocontenido: `<style>` + `<script>` con todo el JS vanilla, sin dependencias externas).

## Cómo funciona el archivo (contexto necesario)

- El catálogo vive en el array `const CATALOGO = [...]` dentro del `<script>`, construido con la función helper `item(...)`.
- **No hay `localStorage`**: al recargar la página, el estado (qué está marcado, cantidades, calidad y fase elegidas) se reconstruye siempre desde los valores por defecto del `CATALOGO`. Es decir, **el archivo es la única fuente de verdad persistente**. Los ajustes que el usuario haga en vivo en el navegador (marcar/desmarcar, cambiar cantidad, cambiar calidad o fase) no se guardan solos — si el usuario quiere que un cambio hecho en el navegador quede fijo, hay que pedírselo y aplicarlo aquí, en el archivo.
- Hay un catálogo de referencia con precios orientativos de Madrid 2025 comentado (`/* ... */`) justo debajo de `const CATALOGO = [];`... si ya se ha empezado a rellenar, aparecerá tras los elementos activos. Reutilizar esos precios cuando el usuario no dé uno explícito, en vez de inventar cifras nuevas.

### Función `item()`

```js
item(id, habitacion, categoria, nombre, unidad, cantidadDefault, precios, faseDefault)
```

| Parámetro | Valores válidos |
|---|---|
| `id` | string única, kebab-case. Convención de prefijo por habitación: `gen-` (general), `salon-`, `cocina-`, `bano1-`, `bano2-`, `hg-` (hab. grande), `hm-` (hab. mediana), `hp-` (hab. pequeña). Sufijo opcional `-mat` (material) / `-mo` (mano de obra) cuando el mismo concepto tiene una partida de material y otra de mano de obra separadas (ej. `salon-suelo-mat` y `salon-suelo-mo`). |
| `habitacion` | `general`, `salon`, `cocina`, `bano1`, `bano2`, `hab_grande`, `hab_mediana`, `hab_pequena` |
| `categoria` | `materiales`, `mano_obra`, `muebles` |
| `nombre` | Texto libre. Si el mismo `nombre` se repite en varias habitaciones (ej. "Suelo laminado (material)" en salón + 3 habitaciones), la pestaña **"Todos"** las agrupa automáticamente bajo un único encabezado con subtotal combinado — es el patrón preferido para partidas que se repiten por habitación, en vez de darles nombres distintos. |
| `unidad` | `m²`, `ud`, `m lineal`, `global` (para partidas de importe fijo sin cantidad variable; el input de cantidad se deshabilita y queda fijo en 1) |
| `cantidadDefault` | Número. El usuario puede ajustarlo luego libremente desde el navegador (input editable), así que una estimación razonable basta — no hace falta preguntar la cifra exacta salvo que el usuario la dé. |
| `precios` | Array de 3 números `[económico, estándar, premium]`. Si el usuario solo da un precio o un rango, úsalo como se indique (ver "Precios" abajo). |
| `faseDefault` | `'fase1'`, `'fase2'`, `'fase3'`, o se omite (`undefined`) para que el elemento empiece "Sin asignar". Los nombres de fase son editables por el usuario en la propia página, así que en el código siempre se referencian por id (`fase1`/`fase2`/`fase3`), nunca por el nombre visible. |

### Función `addCalidad()`

Para añadir un nivel de calidad extra (ej. una opción intermedia entre Estándar y Premium):

```js
addCalidad(item(...), index, nombre, precio, setDefault)
```

- `index`: posición 0-based donde insertar (0=antes de Económico, 1=entre Económico y Estándar, 2=entre Estándar y Premium, etc.)
- `setDefault`: `true` si ese nuevo nivel debe quedar preseleccionado por defecto.
- Envuelve directamente la llamada a `item(...)`, ej.: `addCalidad(item('salon-suelo-mat', ...), 2, 'Superior', 15, true)`.

---

## Paso 1: Determinar la acción

- **Añadir** un elemento nuevo → Paso 2.
- **Editar** un elemento existente (precio, cantidad, calidad, fase, nombre) → localizar su `item(...)` en `CATALOGO` por `id` (buscar por habitación + nombre si el usuario no da el id) y modificar directamente los parámetros que correspondan.
- **Eliminar** un elemento → borrar su línea `item(...)` (y su `addCalidad(...)` si lo envuelve) de `CATALOGO`. No hace falta limpiar nada más: el `state` se reconstruye desde `CATALOGO` en cada carga.
- **Añadir un nivel de calidad** a un elemento existente → envolver su `item(...)` con `addCalidad(...)` (ver arriba).

## Paso 2: Determinar habitación(es)

Mapea la descripción del usuario a los ids válidos. Si el usuario dice "todas las habitaciones excepto baños y cocina" o similar, interpreta "habitaciones" como salón + las 3 habitaciones (dormitorios), **no** como "general" (que son partidas transversales sin superficie propia, como instalaciones o tabiquería) — salvo que el propio elemento sea claramente una partida general.

Si el elemento aplica a varias habitaciones (ej. suelo, pintura, armarios), crear **una fila `item(...)` por habitación**, todas con el mismo `nombre` para que se agrupen en "Todos" (ver tabla de `nombre` arriba). Si el usuario da una cantidad total (ej. "unos 70m²") sin desglosar por habitación, repártela proporcionalmente al tamaño relativo de cada habitación usando como referencia (del catálogo comentado): salón ~24-28m², hab. grande ~15-18m², hab. mediana ~11-14m², hab. pequeña ~8-10m², baño1 ~5m², baño2 ~4m², cocina ~9m². Explica siempre el reparto propuesto al usuario y recuérdale que puede ajustar la cantidad de cada fila directamente en el navegador si no encaja con la realidad.

## Paso 3: Determinar categoría

- `materiales`: suelo, baldosa, pintura (material), sanitarios, encimeras, ventanas, puertas, grifería...
- `mano_obra`: instalación, alicatado, fontanería, electricidad, tirar tabiques, pintura (mano de obra)...
- `muebles`: sofás, camas, armarios, mesas, electrodomésticos, iluminación, decoración...

## Paso 4: Precios

- Si el usuario da **un precio único**, úsalo como Estándar y propón Económico/Premium razonables (ej. ±20-40%) explicando el criterio, o pregunta si prefiere fijarlos él.
- Si el usuario da **un rango** (ej. "entre 10 y 14€"), usa el mínimo como Económico y el máximo como Premium; Estándar = punto intermedio razonable (no necesariamente la media exacta).
- Si el usuario pide **una opción intermedia** (ej. "que haya un 15€ entre estándar y premium"), usa `addCalidad()` en vez de tocar el array `precios` de 3 elementos.
- Si el usuario no da ningún precio, busca primero en el catálogo de referencia comentado en el propio archivo; si no está, pide un precio o rango orientativo antes de inventar cifras.

## Paso 5: Fase

Si el usuario menciona una fase ("fase 1", "esto va en la fase 2"...), añade `faseDefault: 'faseN'` como último argumento de `item(...)`. Si no la menciona, omite el argumento (queda "Sin asignar" y el usuario la clasificará luego él mismo).

## Paso 6: Aplicar el cambio

Editar `CATALOGO` en `/Users/ignacio/Sites/casa/presupuesto.html` con el tool `Edit`, manteniendo el estilo existente (alineación de columnas con espacios, comentario `//` agrupando por habitación/concepto si se añade un bloque nuevo).

## Paso 7: Verificar

**Siempre**, tras cualquier edición:

1. Comprobar que el JS sigue siendo sintácticamente válido:
   ```bash
   node -e "
   const fs = require('fs');
   const html = fs.readFileSync('/Users/ignacio/Sites/casa/presupuesto.html', 'utf8');
   const match = html.match(/<script>([\s\S]*)<\/script>/);
   new Function(match[1]);
   console.log('Syntax OK');
   "
   ```
2. Para cambios que tocan solo líneas de `CATALOGO` (añadir/editar/eliminar un `item(...)`), el chequeo de sintaxis y una relectura del bloque editado son suficientes.
3. Para cambios que tocan las funciones helper (`item()`, `addCalidad()`, `renderItemRow()`, `recalcTotales()`, etc.) o la estructura del HTML/CSS, además del chequeo de sintaxis, escribir una prueba rápida con `jsdom` que cargue el archivo (`runScripts: 'dangerously'`) y simule la interacción relevante (dispatch de eventos `change`/`input`/`click`) para confirmar que no rompe nada existente. Si `jsdom` no está instalado, instalarlo en el directorio scratchpad de la sesión con `npm install jsdom --no-save --silent` antes de escribir el test.

## Paso 8: Confirmar al usuario

Resumir en una tabla o lista breve: elemento(s) añadido/editado/eliminado, habitación(es), cantidad, precios por calidad, fase asignada (si aplica), y el nuevo subtotal/total relevante recalculado a mano (cantidad × precio de la calidad por defecto) para que el usuario pueda verificar sin tener que abrir el navegador.
