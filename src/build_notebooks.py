"""
build_notebooks.py
------------------
Genera y ejecuta los notebooks del proyecto (quedan con sus salidas incrustadas):

    notebooks/01_calidad_y_preparacion.ipynb
    notebooks/02_analisis_exploratorio_y_storytelling.ipynb

    python src/build_notebooks.py
"""
from pathlib import Path

import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks"

SETUP = """import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT / "src"))
import numpy as np, pandas as pd
import plotly.io as pio
pio.renderers.default = "png"          # imágenes estáticas: el notebook se ve igual en cualquier visor
pio.renderers["png"].width = 1100
pio.renderers["png"].scale = 1.5
pd.set_option("display.max_columns", 30); pd.set_option("display.width", 160)
import theme as T, charts as C
from data import load"""


def md(t):
    return nbf.v4.new_markdown_cell(t.strip())


def code(t):
    return nbf.v4.new_code_cell(t.strip())


# =========================================================================== NOTEBOOK 01
nb1 = [
    md("""
# 01 · Calidad de datos y preparación
**Proyecto:** StreamView Analytics · Visual Analytics para la Gerencia de Contenidos y Adquisición
**Objetivo del notebook:** revisar la calidad de los dos datasets oficiales, documentar cada problema encontrado y
justificar las transformaciones aplicadas en `src/prepare_data.py` (sección 15 del caso: *Calidad de los Datos*).

> Regla del caso: *no modificar la estructura original*. Los archivos de `data/raw/` no se tocan; todas las
> transformaciones generan copias en `data/processed/`.
"""),
    code(SETUP),
    md("## 1. Carga de las fuentes oficiales"),
    code("""movies = pd.read_csv(ROOT / "data/raw/movies_clean.csv")
tv = pd.read_csv(ROOT / "data/raw/tvshows_clean.csv")
pd.DataFrame({"Películas": [movies.shape[0], movies.shape[1]], "Series": [tv.shape[0], tv.shape[1]]},
             index=["Registros", "Variables"])"""),
    code("""print("Variables solo en películas:", sorted(set(movies.columns) - set(tv.columns)))
movies.dtypes.to_frame("tipo_películas").join(tv.dtypes.to_frame("tipo_series"))"""),
    md("""
## 2. Valores nulos "disfrazados"
Los datasets no tienen `NaN` reales: los faltantes vienen codificados como el texto **"Sin información"**.
Contarlos como nulos es el primer paso para no tomar *"Sin información"* como si fuera un país o un director.
"""),
    code("""SI = "Sin información"
falt = pd.DataFrame({
    "Películas": (movies == SI).mean() * 100,
    "Series": (tv == SI).mean() * 100}).round(1)
falt[(falt > 0).any(axis=1)].sort_values("Series", ascending=False)"""),
    md("""
**Lectura:** en series faltan director (69%), descripción (20%) y país (11%). Por eso los análisis de talento en
series y los de país se interpretan con cautela y se indica la limitación en cada visualización (regla de negocio 9).
"""),
    md("## 3. Variables sin valor analítico"),
    code("""print("rating == vote_average en películas:", (movies.rating == movies.vote_average).mean())
print("rating == vote_average en series   :", (tv.rating == tv.vote_average).mean())
print("Valores únicos de duration (películas):", movies.duration.unique())
print("Valores únicos de duration (series)   :", tv.duration.unique())"""),
    md("""
**Hallazgo crítico:** `rating`, que según el diccionario debería ser la *clasificación por edad* (TV-MA, PG-13…),
es en realidad una copia exacta de `vote_average` en el 100% de los registros. Y `duration` no tiene información
(películas) o es constante "1 Seasons" (series).

**Decisión:** ambas variables se excluyen. **Consecuencia:** los *KPIs de Clasificación* del caso (distribución
por clasificación etaria, popularidad y calificación por clasificación) **no pueden calcularse con estos datos**.
Se reporta como limitación y como oportunidad de mejora de la fuente (ver informe, evaluación crítica).
"""),
    md("## 4. Duplicados y clave primaria"),
    code("""print("show_id duplicados en películas:", movies.show_id.duplicated().sum())
print("show_id duplicados en series   :", tv.show_id.duplicated().sum())
print("show_id repetidos ENTRE datasets:", len(set(movies.show_id) & set(tv.show_id)))
print("Filas idénticas:", movies.duplicated().sum(), tv.duplicated().sum())
print("Títulos homónimos (distinto show_id):", movies.title.duplicated().sum(), tv.title.duplicated().sum())"""),
    md("""
No hay duplicados dentro de cada dataset, pero **397 `show_id` se repiten entre películas y series** (TMDB usa
espacios de ID separados). Al integrar ambas fuentes se crea la clave `uid = "M-"/"T-" + show_id`.
Los títulos homónimos son obras distintas (remakes, coincidencias) y se conservan (regla 1: cada registro es un contenido).
"""),
    md("## 5. Estructura temporal: una muestra estratificada"),
    code("""pd.DataFrame({"Películas": movies.release_year.value_counts().sort_index(),
              "Series": tv.release_year.value_counts().sort_index()}).T"""),
    code("""for n, d in [("Películas", movies), ("Series", tv)]:
    same = (pd.to_datetime(d.date_added).dt.year == d.release_year).mean()
    print(f"{n}: año de date_added = release_year en {same:.0%} de los casos")"""),
    md("""
**Hallazgo:** hay **exactamente 1.000 títulos por año y tipo** (2010–2025): el extracto es una muestra estratificada.
Además `date_added` cae siempre en el mismo año de estreno.

**Decisión de diseño:** un gráfico de "cantidad de títulos por año" sería una línea plana *por construcción* y
podría inducir a error. Por eso la evolución del catálogo se analiza como **cambio en la composición** (áreas
apiladas al 100%) y **evolución de la calificación/popularidad**, no como volumen. `date_added` se usa solo para
estacionalidad mensual.
"""),
    md("## 6. Votos y confiabilidad de la calificación"),
    code("""q = pd.DataFrame({n: d.vote_count.describe(percentiles=[.25, .5, .75, .9]) for n, d in [("Películas", movies), ("Series", tv)]}).round(0)
q.loc["% con 0 votos"] = [(movies.vote_count == 0).mean() * 100, (tv.vote_count == 0).mean() * 100]
q.loc["% con < 10 votos"] = [(movies.vote_count < 10).mean() * 100, (tv.vote_count < 10).mean() * 100]
q.round(1)"""),
    md("""
La mediana de votos de las series es **4**. Un `vote_average` de 10 con 1 voto, o de 0 con 0 votos, no es una
valoración real. **Decisiones:**
1. La calificación se usa solo si `vote_count ≥ 10` (columna `nota`).
2. Para rankings de "mejor evaluados" se usa una **calificación ponderada bayesiana** (fórmula tipo IMDb,
   m = 100 votos), que acerca a la media los títulos con pocos votos y evita que un 10/10 con 12 votos encabece la lista.
"""),
    md("## 7. Popularidad: asimetría extrema"),
    code("""pd.DataFrame({n: d.popularity.describe(percentiles=[.5, .9, .99]) for n, d in [("Películas", movies), ("Series", tv)]}).round(1)"""),
    md("""
La media es 2–3 veces la mediana y el máximo es cientos de veces la mediana. **Decisiones:** usar **mediana**,
**percentiles dentro de cada tipo** (así una película y una serie se comparan en su propia escala, regla 2) y
**escala logarítmica** en los gráficos. Recordatorio (regla 5): popularidad es un índice relativo, no reproducciones.
"""),
    md("## 8. Presupuesto e ingresos (solo películas)"),
    code("""b, r = movies.budget, movies.revenue
pd.Series({
    "budget = 0": (b == 0).sum(), "revenue = 0": (r == 0).sum(),
    "0 < budget < 100.000 (sospechoso)": ((b > 0) & (b < 1e5)).sum(),
    "Universo válido (budget ≥ 100k y revenue > 0)": ((b >= 1e5) & (r > 0)).sum()}).to_frame("películas")"""),
    code("""m = movies[(b > 0) & (r > 0)].assign(roi=lambda x: x.revenue / x.budget)
m.nlargest(5, "roi")[["title", "release_year", "budget", "revenue", "roi"]]"""),
    md("""
Existen presupuestos de USD 1–7.000 con ingresos de cientos de millones (ROI de 2.400.000x): son **errores de
registro** (cifras en millones cargadas como unidades). **Decisión (reglas 3 y 6):** indicadores financieros
solo con `budget ≥ USD 100.000` y `revenue > 0` → **3.500 películas**. Se usa el **ROI mediano** (no la media),
robusto a los éxitos extremos.
"""),
    md("## 9. Taxonomías de género distintas"),
    code("""gm = movies.genres[movies.genres != SI].str.split(", ").explode().value_counts()
gt = tv.genres[tv.genres != SI].str.split(", ").explode().value_counts()
print("Solo en películas:", sorted(set(gm.index) - set(gt.index)))
print("Solo en series   :", sorted(set(gt.index) - set(gm.index)))"""),
    md("""
Películas usa "Action", "Adventure", "Science Fiction"; series usa "Action & Adventure", "Sci-Fi & Fantasy".
Para comparar ambos tipos **solo cuando la variable es equivalente (regla 2)** se crea una **taxonomía armonizada
en español** (p. ej. *Acción y aventura*, *Ciencia ficción y fantasía*). Además se traducen idiomas (códigos ISO)
y países, porque la audiencia es la Gerencia de Contenidos hispanohablante.
"""),
    md("## 10. Ejecución de la preparación y resultado"),
    code("""import prepare_data
prepare_data.main()
D = load()
print({k: v.shape for k, v in D.items()})
D["cat"][["uid", "tipo", "title", "release_year", "genero_principal", "pais_principal", "idioma",
          "popularity", "pct_popularidad", "nota", "nota_ponderada", "roi"]].head()"""),
    code("""D["calidad"]"""),
    md("## 11. Resumen visual de calidad"),
    code("""C.fig_calidad(movies, tv).show()"""),
    md("""
### Bitácora de transformaciones
| # | Transformación | Justificación |
|---|---|---|
| 1 | "Sin información" → nulo | Evita categorías falsas en gráficos de país, director, género |
| 2 | Clave `uid` = tipo + `show_id` | 397 IDs repetidos entre datasets |
| 3 | Se excluyen `rating` y `duration` | Duplicada / vacía o constante |
| 4 | `nota` = `vote_average` con ≥ 10 votos; `nota_ponderada` bayesiana | Confiabilidad de la valoración |
| 5 | `pct_popularidad` (percentil dentro del tipo) y log10 | Asimetría; comparabilidad película/serie |
| 6 | Universo financiero: budget ≥ 100k y revenue > 0; ROI, ganancia, tramos | Reglas 3 y 6; errores de registro |
| 7 | Taxonomía de géneros armonizada en español; idiomas y países traducidos | Regla 2; audiencia |
| 8 | Tablas "explotadas" de géneros, países y personas | Campos multivalor ("Drama, Romance") |
"""),
]

# =========================================================================== NOTEBOOK 02
nb2 = [
    md("""
# 02 · Análisis exploratorio visual y storytelling
**Audiencia:** Gerente de Contenidos y Adquisición de StreamView Analytics.
**Pregunta central:** *¿Qué contenido debería adquirir y priorizar StreamView para crecer en popularidad y calidad?*

Cada gráfico tiene un **título-hallazgo** (lo que hay que ver), un subtítulo con **período y alcance** (regla 7)
y una justificación de la forma elegida. Estructura narrativa (sección 23 del caso):
**¿Qué está ocurriendo? → ¿Por qué? → ¿Qué evidencia lo demuestra? → ¿Qué decisiones tomar?**
"""),
    code(SETUP + """
D = load(); cat, gen, pais, pers = D["cat"], D["gen"], D["pais"], D["pers"]"""),
    md("## KPIs del catálogo"),
    code("""K = C.kpis(cat, gen, pais)
pd.Series({k: (C.fmt(v, 2) if isinstance(v, float) and v < 100 else C.fmt(v)) for k, v in K.items()}).to_frame("valor")"""),
    md("""
---
# Acto 1 · ¿Qué está ocurriendo? — Cómo es el catálogo hoy
### Q: ¿Cómo se distribuye el catálogo y qué géneros predominan?
**Forma:** treemap (parte-todo jerárquico: tipo → género). El área permite ver el peso relativo sin leer números.
"""),
    code("C.fig_treemap_generos(gen).show()"),
    md("""
**Lectura:** el catálogo es 50/50 películas–series (por diseño de la muestra). **Drama** domina ambos tipos
(23% de las asignaciones de género), seguido de Comedia. Géneros con fuerte demanda como Animación,
Familiar o Telenovela ocupan áreas pequeñas.
### Q: ¿Qué idiomas concentran más contenido?
**Forma:** small multiples de barras horizontales (oferta vs. popularidad) en vez de un eje dual (anti-patrón).
"""),
    code("C.fig_idiomas(cat).show()"),
    md("""
**Lectura:** el inglés concentra el 44% del catálogo. El **español** tiene solo 5,1% pero su popularidad mediana
es **más popular que el título típico (58 sobre 100; típico = 50)**, más que el inglés (55). Para una plataforma latinoamericana, es una
señal clara de sub-oferta. El tagalo (Filipinas) es otro idioma con demanda alta relativa a su oferta.
### Q: ¿Qué países producen más contenido?
**Forma:** mapa coroplético con escala secuencial de un solo tono y **escala logarítmica** (EE.UU. aplastaría al resto).
"""),
    code("C.fig_mapa(pais).show()"),
    code("C.tabla_paises(pais, 50).head(12)"),
    md("""
### Q: ¿Cómo ha evolucionado el catálogo?
Como hay 1.000 títulos por año (muestra estratificada), se analiza la **composición**:
**Forma:** áreas apiladas al 100% con solo 3 grupos por género principal (cada título cuenta una vez), con etiquetas directas.
"""),
    code("C.fig_mix_generos_tiempo(cat, 'Película').show()\nC.fig_mix_generos_tiempo(cat, 'Serie').show()"),
    code("C.fig_incorporaciones_mes(cat).show()"),
    md("""
**Lectura:** de cada 10 películas, 2 tienen Drama como género principal y menos de 1 es Animación o Familiar, año tras año; en series, Drama sube de ~3 a ~4 de cada 10 en los últimos años. Las
incorporaciones se concentran en **septiembre-octubre y enero**, útil para planificar el calendario de lanzamientos.

---
# Acto 2 · ¿Por qué ocurre? — Popularidad y valoración
### Q: ¿Existen diferencias entre películas y series?
**Forma:** box plot en escala log (distribución asimétrica) e histograma agrupado (misma escala 0–10).
"""),
    code("C.fig_dist_popularidad(cat).show()\nC.fig_dist_nota(cat).show()"),
    md("""
**Lectura:** las series tienen popularidad mediana 3,3x mayor y mejor calificación (7,29 vs 6,35).
⚠️ Cautela (regla 2): TMDB calcula la popularidad por separado para cada tipo; por eso las comparaciones de género
usan el **percentil dentro de cada tipo**.
### Q: ¿Existe relación entre popularidad y calificación?
**Forma:** dispersión (dos variables cuantitativas), eje X log, transparencia contra sobre-impresión; correlación de Spearman.
"""),
    code("C.fig_pop_vs_nota(cat).show()"),
    md("""
**Lectura:** la nube no forma una diagonal: la relación es débil (correlación 0,23 en películas; 0,17 en series). **Ser popular no implica ser bien evaluado**:
una decisión de adquisición basada solo en popularidad (o solo en nota) deja oportunidades fuera. Por eso la
herramienta central es una **matriz de dos ejes**.
### Q: ¿Qué contenidos presentan mayor popularidad y mejor evaluación?
**Forma:** barras horizontales ordenadas (la longitud es el atributo preatentivo más preciso; títulos legibles).
"""),
    code("C.fig_top_titulos(cat, 'popularity').show()\nC.fig_top_titulos(cat, 'nota_ponderada').show()"),
    md("""
**Lectura:** los más populares son talk shows y telenovelas brasileñas recientes (*Volta por Cima*, *Crazy About You*)
y estrenos 2024–2025 de Hollywood. Los mejor evaluados (calificación bayesiana) son **todas series**, mayoritariamente
de **animación** (*Arcane*, *Attack on Titan*, *Demon Slayer*).
### Q: ¿La calidad está mejorando?
**Forma:** líneas (cambio continuo en el tiempo), 2025 con marcador hueco por datos incompletos.
"""),
    code("C.fig_tendencia_nota(cat).show()"),
    md("""
---
# Acto 3 · ¿Qué evidencia lo demuestra? — Brechas de oferta y demanda
### Q: ¿Qué géneros concentran mayor popularidad respecto de lo que ofrecemos?
**Métrica propia — brecha oferta/demanda:** % del género dentro del 20% más popular − % del género en el catálogo.
**Forma:** barras divergentes desde 0 (small multiples por tipo). Color de foco = oportunidad; gris = sobre-oferta.
"""),
    code("C.fig_brecha_generos(gen).show()"),
    code("C.tabla_generos(gen).sort_values('brecha_pp', ascending=False)[['tipo','genero','titulos','share_catalogo','share_top20','brecha_pp','nota_media']].round(3).head(10)"),
    md("""
**Lectura:** en películas, **Acción y aventura (+6,0 pp)** y **Ciencia ficción y fantasía (+3,6 pp)** están
sobre-representadas entre los títulos más populares; en series, **Telenovela (+3,4 pp)** y **Familiar (+1,8 pp)**.
**Drama** está sobre-ofertado en ambos tipos (−5,1 pp en películas).
### Matriz de oportunidad: popularidad × calificación × oferta
**Forma:** gráfico de burbujas en cuadrantes (X = popularidad relativa 0–100 con 50 = título típico, Y = calificación, tamaño = cantidad de títulos).
Burbuja **pequeña** en el cuadrante superior derecho = género popular, bien evaluado y con poca oferta.
"""),
    code("C.fig_matriz_oportunidad(gen, 'Película').show()\nC.fig_matriz_oportunidad(gen, 'Serie').show()"),
    md("""
**Lectura:** en películas, **Animación** es el caso más claro: popularidad relativa ~65 (típico = 50), la mejor calificación
de los géneros masivos (6,95) y solo 4% de la oferta. **Familiar** la sigue. En series, **Familiar** y
**Acción y aventura** combinan ambos atributos; **Telenovela** es la más popular (popularidad relativa ~85) aunque con nota
algo menor ("masivo").
"""),
    code("C.fig_heatmap_genero_anio(gen, 'Película').show()\nC.fig_heatmap_genero_anio(gen, 'Serie').show()"),
    md("""
### Q: ¿Qué mercados muestran mayor potencial? ¿Qué países tienen mejores valoraciones?
**Forma:** ranking de barras por popularidad relativa con el % del catálogo anotado (se lee sin escala log), Latinoamérica destacada; dot plot de calificación por país.
"""),
    code("C.fig_mercados(pais).show()\nC.fig_paises_nota(pais).show()"),
    md("""
**Lectura:** **Chile, México y Colombia** tienen popularidad relativa de 60–67 (típico = 50) con muy poca oferta (México 1,5%,
Colombia y Chile < 0,5%). **Japón, Corea del Sur y México** producen el contenido mejor evaluado entre los 15 mayores
productores. Italia y Francia: mucha oferta, baja popularidad relativa.

### Q: Rentabilidad (solo películas)
**Forma:** dispersión log-log con líneas de referencia ROI 1x/5x; barras ordenadas de ROI mediano; barras por tramo.
"""),
    code("C.fig_presupuesto_ingresos(cat).show()\nC.fig_roi_genero(gen).show()\nC.fig_rentabilidad_tramo(cat).show()"),
    code("C.tabla_joyas(cat, 10)"),
    md("""
**Lectura:** existe relación presupuesto–ingresos (r = 0,64 en log), pero **37% de las películas no recupera la
inversión**. **Animación y Familiar** combinan ROI mediano > 2x con 73–77% de títulos rentables. Los blockbusters
(> USD 60 M) son los más seguros (85% rentables). Terror/Misterio de bajo presupuesto generan los mayores
múltiplos (*Get Out* 57x), pero con alta varianza.

### Q: ¿Qué directores y actores aparecen con mayor frecuencia?
"""),
    code("C.fig_top_personas(pers, 'Director').show()\nC.fig_top_personas(pers, 'Actor/Actriz').show()"),
    md("""
**Lectura:** los directores más frecuentes son de telenovelas filipinas (GMA) y cine estadounidense de nicho
(Tyler Perry). Entre actores dominan **actores de voz de anime** japonés (Kana Hanazawa, Yuki Kaji), lo que
confirma el peso del anime en el catálogo de series.

---
# Acto 4 · ¿Qué decisiones deberían tomarse?
| # | Recomendación para la Gerencia de Contenidos | Evidencia |
|---|---|---|
| 1 | **Aumentar la adquisición de Animación y Familiar** (películas y series) | Cuadrante de oportunidad; ROI mediano 2,2–2,3x; 73–77% rentables; top 10 mejor evaluados dominado por animación |
| 2 | **Crecer en contenido latinoamericano en español/portugués**, con foco en **telenovelas y reality** de México, Brasil y Colombia | Español: 5,1% del catálogo, popularidad relativa 58; Telenovela +3,4 pp de brecha; Chile/México/Colombia 60–67 |
| 3 | **Reducir la adquisición incremental de Drama** y reasignar presupuesto | Drama: −5,1 pp (películas) y −1,8 pp (series); ROI mediano 1,3x |
| 4 | **Mantener un pipeline asiático de calidad** (Japón, Corea) | Mejor calificación media por país (7,22 y 7,10) |
| 5 | **Portafolio de películas balanceado:** blockbusters para estabilidad + apuestas de bajo presupuesto en terror/misterio | 85% rentables > USD 60 M; joyas de bajo presupuesto con ROI 20–95x |
| 6 | **Exigir a la fuente datos de clasificación etaria y duración** | Hoy no es posible calcular los KPIs de clasificación |
"""),
]


def build(cells, name):
    nb = nbf.v4.new_notebook()
    nb.cells = cells
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    ExecutePreprocessor(timeout=900, kernel_name="python3").preprocess(nb, {"metadata": {"path": str(NB)}})
    nbf.write(nb, NB / name)
    print("ok", name)


if __name__ == "__main__":
    NB.mkdir(exist_ok=True)
    build(nb1, "01_calidad_y_preparacion.ipynb")
    build(nb2, "02_analisis_exploratorio_y_storytelling.ipynb")
