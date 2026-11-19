# StreamView Analytics · Visual Analytics para la Gerencia de Contenidos y Adquisición

Proyecto semestral **ADY1104 – Visualización de Datos** (Duoc UC). Evaluaciones **EP5 (Encargo)** y **EP6 (Presentación y defensa)**.

**Pregunta de negocio:** *¿Qué géneros, mercados y tipos de contenido debería adquirir StreamView para tener un catálogo más popular y mejor evaluado?*
**Audiencia principal:** Gerente de Contenidos y Adquisición.

## Entregables

| # | Entregable (pauta EP5/EP6) | Archivo |
|---|---|---|
| 1 | Informe ejecutivo (PDF) | `reports/Informe_Ejecutivo_StreamView.pdf` |
| 2 | Dashboard interactivo (Streamlit + Plotly) | `dashboard/app.py` |
| 3 | Presentación ejecutiva (PowerPoint: 13 diapositivas en el guion de 10 min + 3 de anexo, con notas del orador y tiempos) | `reports/Presentacion_Ejecutiva_StreamView.pptx` |
| – | Guía de defensa individual (preguntas cruzadas por indicador de la rúbrica) | `reports/Guia_Defensa_Individual.md` |
| 4 | Archivos del proyecto documentados | `src/`, `notebooks/` |
| 5 | Datos y archivos complementarios | `data/raw/`, `data/processed/` |
| 6 | Carpeta organizada | esta estructura |

## Estructura

```
StreamView EV3/
├── data/
│   ├── raw/                 # Fuentes oficiales del caso (no se modifican)
│   └── processed/           # Catálogo unificado + tablas de géneros, países, personas + bitácora de calidad
├── notebooks/
│   ├── 01_calidad_y_preparacion.ipynb              # Calidad de datos y justificación de transformaciones
│   └── 02_analisis_exploratorio_y_storytelling.ipynb # EDA visual en 4 actos + recomendaciones
├── dashboard/app.py         # Dashboard interactivo (7 vistas, 5 filtros globales, drill-down)
├── src/
│   ├── prepare_data.py      # Integración, limpieza y variables derivadas
│   ├── data.py              # Carga y filtrado común
│   ├── theme.py             # Sistema visual (paleta validada para daltonismo, tipografía, plantilla Plotly)
│   ├── charts.py            # 24 visualizaciones con títulos-hallazgo dinámicos
│   ├── export_images.py     # Exporta las imágenes estáticas (images/ e images/slides/)
│   ├── build_notebooks.py   # Genera y ejecuta los notebooks
│   ├── build_report.py      # Genera el informe ejecutivo (HTML + PDF)
│   └── build_presentation.js# Genera la presentación .pptx
├── images/                  # Gráficos PNG + capturas del dashboard
├── reports/                 # Informe ejecutivo y presentación
├── docs/                    # Caso semestral e instrucciones EP5/EP6
├── .streamlit/config.toml   # Tema del dashboard
├── requirements.txt
└── README.md
```

## Cómo ejecutar

```bash
pip install -r requirements.txt

python src/prepare_data.py          # 1. datos procesados
streamlit run dashboard/app.py      # 2. dashboard en http://localhost:8501
```

Regenerar todos los productos (opcional):

```bash
python src/export_images.py            # gráficos para el informe
python src/export_images.py --slides   # gráficos para la presentación
python src/build_notebooks.py          # notebooks ejecutados
python src/build_report.py             # informe PDF (usa Chrome o Edge instalado)
npm install                            # una vez (pptxgenjs)
node src/build_presentation.js         # presentación .pptx
```

## Alcance

La solución usa datos de **catálogo** (TMDB): contenidos, popularidad y valoración; finanzas solo para películas con datos válidos. **No analiza retención, engagement ni comportamiento de usuarios**, porque no hay datos de usuarios, suscripciones ni reproducciones. Las recomendaciones distinguen la evidencia medida del impacto esperado, que se sigue con indicadores y líneas base.

## Decisiones clave de datos (detalle en notebook 01)

| Problema | Decisión |
|---|---|
| `rating` es idéntica a `vote_average` (no es clasificación etaria) | Se excluye → KPIs de clasificación etaria no calculables (limitación reportada) |
| `duration` vacía (películas) o constante "1 Seasons" (series) | Se excluye |
| "Sin información" como texto | Convertido a nulo |
| 397 `show_id` repetidos entre películas y series | Clave `uid` = tipo + id |
| Calificaciones con pocos votos | Solo con ≥ 10 votos; ranking con calificación bayesiana |
| Popularidad muy asimétrica y con escala distinta por tipo | Mediana, percentil dentro del tipo, escala log |
| 1.000 títulos por año y tipo (muestra estratificada) | Se analiza composición, no volumen |
| Presupuestos < USD 100 mil (errores) | Finanzas solo con 3.500 películas válidas (reglas 3 y 6) |
| Géneros con taxonomías distintas por tipo | Taxonomía armonizada en español (regla 2) |

## Hallazgos principales

1. **Drama** domina el catálogo (23% de las asignaciones de género) pero está sub-representado entre los títulos más populares (−5,1 pp en películas).
2. **Animación y Familiar** combinan alta popularidad, alta calificación, poca oferta y ROI mediano > 2x.
3. **Popularidad y calificación casi no se relacionan** (ρ = 0,23 / 0,17): hay que evaluar ambas.
4. **Latinoamérica está sub-representada**: el español es 5,1% del catálogo con popularidad en el percentil 58; México, Chile y Colombia tienen alta popularidad con poca oferta; Telenovela es la mayor brecha en series (+3,4 pp).
5. **37% de las películas no recupera su presupuesto**; los blockbusters (> USD 60 M) son los más seguros (85% rentables).
