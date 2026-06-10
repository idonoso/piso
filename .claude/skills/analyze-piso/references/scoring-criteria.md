# Criterios de puntuación de pisos

## Puntuación de fotos (1-10)

### Escala general

| Puntuación | Descripción |
|---|---|
| 9-10 | Fotos profesionales, piso muy luminoso, acabados de alta calidad, vistas, sin defectos visibles |
| 7-8 | Buen estado general, luminoso, fotos de calidad media-alta, nada llamativamente negativo |
| 5-6 | Estado aceptable, fotos mediocres o amateur, algún defecto menor visible |
| 3-4 | Piso oscuro o pequeño percibido, defectos visibles, mobiliario muy deteriorado |
| 1-2 | Daños evidentes (humedad, grietas, moho), fotos de bajísima calidad, estado ruinoso |

### Factores positivos (fotos)

| Factor | Bonus |
|---|---|
| Luz natural abundante | +1.5 |
| Cocina reformada o moderna | +1.0 |
| Terraza o balcón con espacio real | +1.0 |
| Suelos de calidad (parquet, porcelánico) | +0.5 |
| Vistas exteriores visibles | +0.5 |
| Baño renovado | +0.5 |

### Factores negativos (fotos)

| Factor | Penalización |
|---|---|
| Manchas de humedad visibles | -2.0 |
| Fotos muy oscuras o mal encuadradas | -1.0 |
| Fachada o entrada muy deteriorada | -1.0 |
| Mobiliario muy deteriorado | -0.5 |
| Desorden extremo | -0.5 |

---

## Puntuación general (1-10)

La puntuación general combina tres componentes:

- **40% Características objetivas**
- **35% Ubicación / zona**
- **25% Puntuación de fotos**

Si la puntuación de fotos es `null` (no accesibles), repartir ese 25% entre los otros dos componentes proporcionalmente (23% características, 12% ubicación adicional, aprox 51% y 49%).

### Características objetivas (puntuación base: 5)

| Factor | Ajuste |
|---|---|
| Planta alta (4ª o superior) con ascensor | +1.5 |
| Planta baja sin terraza privada | -1.5 |
| Sin ascensor y planta > 2ª | -1.0 |
| m² >= 90 | +1.0 |
| m² entre 70-89 | +0.5 |
| m² entre 50-69 | neutral |
| m² < 50 | -1.5 |
| Terraza o balcón real (no Juliette) | +1.0 |
| Garaje incluido en el precio | +1.0 |
| Estado "A reformar" | -1.5 |
| Estado "Obra nueva" | +0.5 |
| Certificado energético A o B | +0.5 |
| Certificado energético F o G | -0.5 |
| Exterior (no interior) | neutral (es requisito mínimo) |
| Trastero incluido | +0.3 |

### Ubicación (puntuación base variable por zona)

Para **Madrid**:

| Zona | Puntuación base |
|---|---|
| Zonas prime: Salamanca, Jerónimos, Recoletos, Almagro | 8-9 |
| Zonas muy buenas: Chamberí, Retiro, Castellana, Barrio de Lista | 7-8 |
| Zonas buenas: Chamartín, Moncloa, Arganzuela norte, Justicia | 7 |
| Zonas medias: Tetuán, Hortaleza, Carabanchel norte, Latina | 5-6 |
| Zonas periféricas o con menos demanda | 3-4 |

Para **otras ciudades**, aplicar criterio equivalente basado en el conocimiento general del modelo. Si la ubicación es desconocida o ambigua, usar puntuación base 5 y anotarlo en `notas_analisis`.

### Precio relativo al mercado

Comparar el `precio_m2` con la media aproximada de la zona. Aplicar sobre la puntuación final:

| Situación | Ajuste |
|---|---|
| Precio/m² > 20% por encima de la media | -1.0 |
| Precio/m² > 10% por encima de la media | -0.5 |
| Precio/m² alineado con la media (±10%) | neutral |
| Precio/m² > 10% por debajo de la media | +0.5 |
| Precio/m² > 20% por debajo de la media | +1.0 |

Anotar siempre en `notas_analisis` si el precio se considera caro, ajustado o barato respecto a la zona.

---

## Negociación

### Base y ajustes para calcular `descuento_estimado_pct`

**Base Madrid periférico:** 5%

| Factor | Ajuste |
|---|---|
| Estado "a reformar" | +5% |
| Precio/m² > 20% sobre la media de zona | +4% |
| Precio/m² > 10% sobre la media de zona | +2% |
| Precio alineado o por debajo de la media | 0% |
| Anuncio publicado > 60 días | +3% |
| Anuncio publicado > 30 días | +1% |
| Anunciante es particular (no agencia) | +2% |
| Anunciante es agencia profesional | -1% |
| Honorarios de agencia no incluidos en el precio | +2% |
| Fotos con IA (estado real incierto) | +2% |
| Buen estado / reformado recientemente | -2% |
| Zona de alta demanda / prime | -2% |

**Rango válido:** clamp entre 3% y 20%.

### Cálculo de precios objetivo

```
precio_objetivo     = round(precio × (1 - pct/100), al millar más próximo)
precio_objetivo_max = round(precio × (1 - (pct-2)/100), al millar)   ← descuento mínimo
precio_objetivo_min = round(precio × (1 - (pct+3)/100), al millar)   ← descuento agresivo
```

### Interpretación del margen

| Descuento estimado | Interpretación |
|---|---|
| 3-5% | Mercado favorable al vendedor; poco margen |
| 6-9% | Margen razonable; oferta estándar en la zona |
| 10-14% | Bastante margen; piso con debilidades claras |
| 15-20% | Máximo razonable; piso con problemas o muy sobrepriced |

---

## Criterios mínimos (deal-breakers)

Si **cualquiera** de estos no se cumple, advertir al usuario:

| Criterio | Condición |
|---|---|
| Tamaño | m2 >= 50 |
| Ascensor | ascensor = true |
| Planta | Distinto de "Bajo", "Entresuelo", "Sótano", "Semi-sótano" |
| Exterior | exterior = true |

Texto de aviso: "⚠️ Este piso no cumple los criterios mínimos: [lista de criterios incumplidos]. ¿Deseas descartarlo o guardarlo igualmente?"
