# Guía de defensa individual · EP6

Cada integrante debe poder responder **cualquiera** de estas preguntas (son cruzadas). Respuesta corta = 20–40 segundos.
Estructura de toda respuesta: **evidencia → recomendación → decisión → impacto esperado** (no medido).

## Guion de 10 minutos (diapositivas)

| Tiempo | Bloque | Diapositivas |
|---|---|---|
| 0:00–1:15 | Problema y audiencia | 1–2 |
| 1:15–2:15 | Datos y límites | 3 |
| 2:15–5:15 | Dashboard y hallazgos | 4–7 (demo en la 7) |
| 5:15–8:15 | Evaluación crítica y mejoras | 8–11 |
| 8:15–10:00 | Decisiones e impacto | 12–13 |
| Preguntas | Respaldo | Anexos A–C |

Demo sugerida (30 s): pestaña **Oportunidades** → filtro *Tipo = Serie* → clic en la burbuja **Telenovela** → mostrar títulos.

---

## Cómo explicar cada gráfico en una frase

Primero **qué muestra**, después **qué significa para la decisión**. Sin jerga: decir "popularidad relativa (50 = título típico)" en vez de "percentil".

| Gráfico | Cómo leerlo | Qué significa |
|---|---|---|
| Brecha de géneros (barras hacia ambos lados) | Cada barra compara cuánto pesa un género entre los títulos más populares vs en el catálogo. Derecha = falta oferta; izquierda = sobra. | Faltan títulos de Acción y aventura y Telenovela; sobra Drama. |
| Matriz de oportunidad (burbujas) | Derecha = más popular; arriba = mejor evaluado; tamaño = cuántos títulos ya tenemos. | Burbuja chica arriba a la derecha = adquirir. Animación es el caso más claro. |
| Mix de géneros (áreas) | De cada 10 estrenos de cada año, cuántos son Drama, Animación/Familiar u otro. | 2 de cada 10 películas son Drama y menos de 1 es Animación/Familiar, todos los años. |
| Mercados (ranking de países) | Barra más larga = contenido más popular (50 = típico). El texto dice cuánto pesa ese país en el catálogo. | Chile, México y Colombia son muy populares pero suman menos del 2,5% del catálogo. |
| Popularidad vs calificación (nube de puntos) | Cada punto es un título. Si fueran de la mano formarían una diagonal; forman una nube. | Hay que mirar las dos métricas juntas: por eso existe la matriz. |
| Treemap | Cada rectángulo es un género; su tamaño, la cantidad de títulos. | Drama ocupa el rectángulo más grande en películas y en series. |
| ROI por género | ROI = ingresos ÷ presupuesto de la película típica. 2x = recupera el doble. | Animación y Familiar rinden más que Drama (1,3x). |
| Presupuesto vs ingresos | Cada punto es una película; sobre la línea de abajo recuperó lo invertido. | 37% no recupera; las de bajo presupuesto son más riesgosas pero tienen joyas. |

## IE26 · Justificación técnica de los gráficos

**¿Simplificaron algún gráfico?**
Sí. Dos eran difíciles de explicar: el mix de géneros tenía 6 bandas por "asignaciones de género" y ahora tiene 3 grupos por
género principal ("de cada 10 películas, 2 son Drama"); y mercados era una dispersión en escala logarítmica, ahora es un
ranking de barras con el % del catálogo escrito al lado. También cambiamos "percentil" por "popularidad relativa" y
agregamos una línea "Cómo leer" bajo cada gráfico del dashboard. Es una mejora de legibilidad para la audiencia (IE29).

**¿Por qué una matriz de burbujas y no un ranking de popularidad?**
Porque popularidad y calificación casi no se relacionan (correlación 0,23 en películas: débil). Un ranking usa una sola métrica y deja
fuera géneros valiosos. La matriz muestra 3 variables (popularidad, calificación, oferta) y sus cuadrantes se traducen en decisiones.

**¿Por qué escala logarítmica?**
La popularidad es muy asimétrica (la media es 2–3 veces la mediana; el máximo, cientos de veces). En escala lineal,
unos pocos títulos virales aplastan al resto. Igual con presupuesto/ingresos (4 órdenes de magnitud) y con países (EE.UU.).

**¿Por qué barras divergentes para la brecha?**
La brecha tiene signo (+ = demanda > oferta). Se lee desde el 0, y el color solo en las oportunidades (atributo preatentivo) dirige la mirada.

**¿Por qué áreas al 100% y no una línea de títulos por año?**
El dataset tiene exactamente 1.000 títulos por año y tipo: una línea de conteo sería plana *por construcción* y engañaría.
Lo informativo es la composición.

**¿Por qué no un gráfico de doble eje en idiomas?**
El doble eje es un anti-patrón: la escala de cada eje es arbitraria y sugiere cruces falsos. Usamos small multiples (dos barras alineadas por fila).

**¿Cómo eligieron los colores?**
Por función: categórico (película azul, serie naranjo, en todos los gráficos), secuencial de un tono (mapa, mapa de calor),
foco violeta sobre gris. La paleta se validó con un script para protanopía, deuteranopía y tritanopía (separación ΔE ≥ 9).
La identidad nunca depende solo del color: siempre hay leyenda o etiqueta directa.

## IE31 · Fortalezas con evidencia

- **Enfoque:** las 7 páginas responden "¿qué priorizar?"; cada una declara audiencia, pregunta y decisión.
- **Títulos dinámicos:** se calculan desde los datos; si filtro "Serie" o "México", el hallazgo cambia y sigue siendo verdadero.
- **Accesibilidad:** paleta validada para daltonismo, contraste, formato numérico chileno, tooltips en todos los gráficos.
- **Métricas robustas:** mediana, popularidad relativa por tipo, calificación con ≥ 10 votos, nota bayesiana, ROI mediano.
- **Reproducible:** todo se regenera con scripts (`src/`) y notebooks ejecutados.

## IE32 · Limitaciones, sesgos y riesgos

**¿Qué limita más el uso de la solución?**
Que la popularidad es un índice de TMDB (interés global), no reproducciones de usuarios de StreamView. Mitigación: se usa
como proxy relativo (popularidad relativa 0–100) y **no afirmamos impacto en retención ni engagement**.

**¿Pueden decir que estas recomendaciones mejoran la retención?**
No. No hay datos de usuarios, suscripciones ni reproducciones. Solo podemos decir que alinean el catálogo con lo que es
más popular y mejor evaluado. Medir retención es la mejora n.º 1 (requiere esas fuentes).

**¿Qué sesgos tienen los datos?**
- Recencia: estrenos 2024–25 con popularidad inflada; 2025 con ~8% de títulos con votos suficientes → marcado incompleto.
- Supervivencia: solo 22% de las películas tienen finanzas válidas, y suelen ser las conocidas → no extrapolar el ROI.
- Faltantes: 69% de las series sin director, 11% sin país.

**¿Por qué no hay KPIs de clasificación etaria si el caso los pide?**
Porque `rating` es una copia exacta de `vote_average` en el 100% de los registros. No es clasificación por edad. Lo
reportamos como limitación y como mejora (corregir la fuente).

**¿Por qué excluyeron títulos con menos de 10 votos?**
La mediana de votos en series es 4: un 10/10 con un voto no es una valoración. Con ≥ 10 votos queda 64% del catálogo.

**¿Por qué ROI mediano y no promedio?**
Hay películas con ROI de 50x a 500x que distorsionan el promedio. La mediana representa a la película típica.

## IE33 · Mejoras fundamentadas y priorizadas

| Prioridad | Mejora | Por qué | Esfuerzo |
|---|---|---|---|
| 1 | Datos de reproducciones y suscripciones | Reemplaza el proxy y permite medir impacto | Alto; requiere fuentes de usuarios |
| 2 | Clasificación etaria y duración reales | Habilita KPIs del caso | Bajo ("hacer primero") |
| 3 | Costo de licencia por título | El retorno real no es la taquilla | Medio |
| 4 | Vista "lista de compra" | Del diagnóstico a la acción | Medio |
| 5 | Modo oscuro y texturas | Accesibilidad extendida | Bajo |

## IE35 · Recomendaciones con evidencia

1. **Más Animación y Familiar.** Animación: popularidad relativa 65 (típico = 50), nota 6,95, 4,3% de la oferta; ROI mediano 2,3x (Familiar 2,2x).
2. **Más contenido latinoamericano.** Español 5,1% del catálogo con popularidad relativa 58 (inglés 55); Telenovela +3,4 pp; México 66, Chile 67, Colombia 60.
3. **Menos Drama incremental.** −5,1 pp de brecha en películas, ROI 1,3x; libera presupuesto sin aumentar el gasto.
4. **Asia de calidad.** Japón 7,22 y Corea del Sur 7,10: mejor calificación entre los 15 mayores productores.
5. **Portafolio balanceado.** Blockbusters 85% rentables; bajo presupuesto 58%, pero con joyas de 20–95x.

## IE36 · Impacto esperado (≠ medido)

**¿Cómo saben que funcionará?**
No lo sabemos todavía: es **impacto esperado**. La evidencia (brechas, popularidad relativa, ROI) sí está medida. Para cada
recomendación definimos un indicador con línea base, que el dashboard permite seguir:

| Recomendación | Indicador | Línea base |
|---|---|---|
| Animación y Familiar | % del catálogo en esos géneros | 18,6% |
| Latinoamérica | % del catálogo en español/portugués | 6,7% |
| Menos Drama | Brecha de Drama en películas | −5,1 pp |
| Asia de calidad | Nota media Japón + Corea | 7,18 |
| Portafolio | % de películas con ROI ≥ 1 | 63% |

**¿Qué decisión concreta permite tomar el dashboard?**
En minutos: ubicar un género o mercado en la matriz, verificar su calidad y riesgo financiero, y bajar a la lista de
títulos concretos para negociar licencias.

## Preguntas sobre los datos

- **¿Cómo integraron las fuentes?** Se apilan (16 variables comunes); clave `uid` = tipo + `show_id` porque 397 IDs se repiten entre películas y series. Géneros, países y personas en tablas 1:N por `uid`.
- **¿Qué es la popularidad relativa?** Un puntaje de 0 a 100 que dice qué tan popular es un título comparado con los de su tipo: 50 es el título típico; 80 = más popular que el 80% de los títulos de su tipo. Se usa porque TMDB calcula la popularidad de películas y series en escalas distintas (técnicamente es un percentil).
- **¿Qué es la brecha?** % del género entre el 20% más popular − % del género en el catálogo, en puntos porcentuales.
- **¿Qué es la calificación bayesiana?** Promedio ponderado entre la nota del título y la media del tipo según sus votos (m = 100); evita que un título con pocos votos encabece el ranking.
