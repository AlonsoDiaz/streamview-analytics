"""
build_report.py
---------------
Genera el Informe Ejecutivo (HTML + PDF) en reports/. Las cifras se calculan desde los datos
procesados, por lo que el informe es reproducible. El PDF se imprime con Chrome/Edge headless.

    python src/build_report.py
"""
import subprocess
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import charts as C  # noqa: E402
from data import ROOT, load  # noqa: E402

REP = ROOT / "reports"
IMG = "../images"

D = load()
cat, gen, pais, pers = D["cat"], D["gen"], D["pais"], D["pers"]
K = C.kpis(cat, gen, pais)
TG = C.tabla_generos(gen)
TP = C.tabla_paises(pais, 50)
f = cat[cat["fin_valido"] == True]  # noqa: E712
fg = gen[gen["fin_valido"] == True]  # noqa: E712
roi_g = fg.groupby("genero").agg(roi=("roi", "median"), rent=("roi", lambda x: (x >= 1).mean()), n=("uid", "size"))
esp = cat[cat["idioma"] == "Español"]


def g(tipo, genero, col):
    return TG[(TG.tipo == tipo) & (TG.genero == genero)][col].iloc[0]


def p(pais_, col):
    return TP[TP.pais == pais_][col].iloc[0]


N = dict(
    total=C.fmt(K["Total de contenidos"]), paises=C.fmt(K["Países representados"]), idiomas=C.fmt(K["Idiomas"]),
    nota=C.fmt(K["Calificación promedio"], 2), roi=C.fmt(K["ROI mediano"], 2), rent=C.pct(K["% películas rentables"]),
    nofin=C.pct(1 - K["% películas rentables"]), nfin=C.fmt(K["Películas con datos financieros"]),
    esp_share=C.pct(len(esp) / len(cat), 1), esp_pct=C.fmt(esp["pct_popularidad"].median() * 100),
    eng_share=C.pct((cat.idioma == "Inglés").mean()),
    ac_m=C.fmt(g("Película", "Acción y aventura", "brecha_pp"), 1),
    cf_m=C.fmt(g("Película", "Ciencia ficción y fantasía", "brecha_pp"), 1),
    dr_m=C.fmt(g("Película", "Drama", "brecha_pp"), 1), dr_s=C.fmt(g("Serie", "Drama", "brecha_pp"), 1),
    tel=C.fmt(g("Serie", "Telenovela", "brecha_pp"), 1), tel_pct=C.fmt(g("Serie", "Telenovela", "percentil_pop") * 100),
    tel_share=C.pct(g("Serie", "Telenovela", "share_catalogo"), 1),
    fam_s=C.fmt(g("Serie", "Familiar", "brecha_pp"), 1),
    ani_pct=C.fmt(g("Película", "Animación", "percentil_pop") * 100), ani_nota=C.fmt(g("Película", "Animación", "nota_media"), 2),
    ani_share=C.pct(g("Película", "Animación", "share_catalogo"), 1),
    roi_ani=C.fmt(roi_g.loc["Animación", "roi"], 1), roi_fam=C.fmt(roi_g.loc["Familiar", "roi"], 1),
    rent_ani=C.pct(roi_g.loc["Animación", "rent"]), rent_fam=C.pct(roi_g.loc["Familiar", "rent"]),
    roi_dr=C.fmt(roi_g.loc["Drama", "roi"], 1), rent_dr=C.pct(roi_g.loc["Drama", "rent"]),
    mx_pct=C.fmt(p("México", "percentil_pop") * 100), mx_sh=C.pct(p("México", "share"), 1),
    cl_pct=C.fmt(p("Chile", "percentil_pop") * 100), co_pct=C.fmt(p("Colombia", "percentil_pop") * 100),
    us_sh=C.pct(TP.iloc[0].share), jp=C.fmt(p("Japón", "nota_media"), 2), kr=C.fmt(p("Corea del Sur", "nota_media"), 2),
    rho_m=C.fmt(cat[(cat.tipo == "Película")][["popularity", "nota"]].corr("spearman").iloc[0, 1], 2),
    rho_s=C.fmt(cat[(cat.tipo == "Serie")][["popularity", "nota"]].corr("spearman").iloc[0, 1], 2),
    nota_m=C.fmt(cat[cat.tipo == "Película"].nota.mean(), 2), nota_s=C.fmt(cat[cat.tipo == "Serie"].nota.mean(), 2),
    pop_ratio=C.fmt(cat[cat.tipo == "Serie"].popularity.median() / cat[cat.tipo == "Película"].popularity.median(), 1),
    block=C.pct((f[f.budget > 60e6].roi >= 1).mean()), bajo=C.pct((f[f.budget < 5e6].roi >= 1).mean()),
    val=C.pct(cat.nota.notna().mean()), val_s=C.pct(cat[cat.tipo == "Serie"].nota.notna().mean()),
)

JUST = [
    ("KPIs (tarjetas)", "Cuantitativo agregado", "Lectura inmediata del estado del catálogo", "Un número aislado no necesita ejes; el tamaño tipográfico da jerarquía", "Velocímetros (gauge): más tinta, menos precisión"),
    ("Treemap", "Jerárquico parte-todo (tipo → género)", "¿Qué géneros predominan?", "El área muestra pesos relativos de 30+ categorías en un espacio compacto", "Torta: ilegible con > 5 categorías"),
    ("Barras divergentes (small multiples)", "Diferencia con signo (pp)", "Brecha oferta vs demanda por género", "Se lee desde el 0; color de foco solo en oportunidades (atributo preatentivo)", "Barras agrupadas oferta/demanda: obliga a restar mentalmente"),
    ("Burbujas en cuadrantes", "3 variables cuantitativas", "Matriz de oportunidad popularidad × calificación × oferta", "Los cuadrantes traducen el gráfico en decisiones (adquirir, nicho, revisar)", "Tabla: no muestra relaciones ni agrupamientos"),
    ("Small multiples de barras", "2 métricas de escala distinta", "Oferta vs popularidad por idioma", "Evita el eje dual (anti-patrón) manteniendo la comparación por fila", "Gráfico de doble eje Y"),
    ("Mapa coroplético (log)", "Geográfico + cantidad", "¿Qué países producen más?", "Patrón espacial; escala log para que EE.UU. no anule al resto; secuencial de un tono", "Mapa de burbujas: superposición en Europa"),
    ("Barras ordenadas con anotación", "Ranking + % del catálogo", "¿Qué países tienen contenido popular y poca oferta?", "Se lee sin escala log: largo = popularidad, texto = oferta", "Dispersión log oferta vs popularidad (versión anterior, difícil de explicar)"),
    ("Dispersión (log)", "2 cuantitativas, n grande", "Relación popularidad–calificación; presupuesto–ingresos", "Muestra forma, dispersión y outliers; log por asimetría; transparencia contra sobre-impresión", "Líneas de tendencia solas: ocultan la dispersión"),
    ("Áreas apiladas 100% (3 grupos)", "Composición en el tiempo", "¿Cuántos de cada 10 estrenos son Drama vs Animación/Familiar?", "Volumen constante por la muestra; 3 grupos por género principal (cada título cuenta una vez)", "Líneas de conteo (planas) y versión de 6 bandas (difícil de leer)"),
    ("Líneas", "Serie temporal continua", "Tendencia de la calificación", "La pendiente comunica dirección; 2025 marcado como incompleto", "Barras por año: enfatizan valores, no tendencia"),
    ("Mapa de calor", "Matriz categoría × tiempo", "Popularidad/calificación por género y año", "12 géneros × 16 años sin 'espagueti' de líneas; escala secuencial", "12 líneas superpuestas"),
    ("Box plot (log) e histograma", "Distribuciones", "Diferencias películas vs series", "Mediana, cuartiles y outliers en una forma compacta", "Promedios en barras: ocultan la asimetría"),
    ("Barras horizontales ordenadas", "Ranking categórico", "Top títulos, directores, actores, ROI por género", "La longitud es el canal más preciso; etiquetas largas legibles en Y", "Barras verticales con etiquetas rotadas"),
    ("Dot plot", "Comparación en rango estrecho (6–7,5)", "Calificación por país", "No obliga a empezar en 0, menos tinta que barras", "Barras truncadas (engañosas)"),
]

EVAL_F = [
    ("Foco en una audiencia y una pregunta", "Todo el dashboard responde '¿qué adquirir?' para la Gerencia de Contenidos; los títulos son hallazgos, no descripciones."),
    ("Títulos dinámicos y siempre verdaderos", "Cada título se calcula desde los datos filtrados: al cambiar un filtro, el mensaje se actualiza (no hay textos fijos que queden obsoletos)."),
    ("Sistema visual consistente y accesible", f"Paleta validada para daltonismo (ΔE ≥ 9 en protanopía/deuteranopía), película = azul y serie = naranjo en los 24 gráficos, gris de contexto + un color de foco, sin ejes duales ni 3D."),
    ("Métricas robustas", "Mediana, percentiles dentro de cada tipo, calificación con ≥ 10 votos y ponderación bayesiana; ROI mediano en vez de promedio."),
    ("Interacción con propósito", "Filtros globales, selección de burbuja con detalle del género, rankings intercambiables, exportación PNG y descarga CSV del alcance filtrado."),
    ("Reproducibilidad", "Pipeline en scripts (`src/`), notebooks ejecutados, imágenes e informe regenerables con un comando."),
]
EVAL_L = [
    ("Muestra estratificada (1.000 títulos/año/tipo)", "No permite medir crecimiento real del catálogo ni comparar volúmenes entre años.", "Se analiza composición y no volumen; se advierte en subtítulos. Solicitar extracto completo."),
    ("`rating` duplica `vote_average`; `duration` vacía", "No se pueden calcular los KPIs de clasificación etaria ni de duración que pide el caso.", "Se documenta como brecha de datos; recomendación #6 a Data & Analytics."),
    ("Popularidad TMDB ≠ consumo en StreamView", "Sesgo de fuente: mide interés global, no reproducciones de nuestros usuarios (regla 5).", "Se usa como proxy relativo (percentiles) y no se afirma impacto en retención o engagement; integrar datos propios en una fase 2."),
    ("Sesgo de recencia", "Los estrenos 2024–2025 tienen popularidad inflada y pocos votos (2025: ~8% con votos suficientes).", "2025 marcado como incompleto; percentiles dentro del tipo; umbral de votos."),
    ("Sesgo de supervivencia financiera", f"Solo {N['nfin']} películas (22%) tienen presupuesto e ingresos válidos; suelen ser las más exitosas o conocidas.", "KPIs financieros etiquetados con su universo; ROI mediano; no extrapolar a todo el catálogo."),
    ("Faltantes en series", "69% sin director y 11% sin país: los análisis de talento y mercado sub-representan series.", "Indicado en las visualizaciones; análisis por tipo separados."),
    ("Taxonomía de géneros armonizada", "Agrupar 'Action' y 'Adventure' pierde detalle fino.", "Decisión documentada; se puede desagregar en el dashboard en una versión futura."),
]
EVAL_M = [
    ("1 · Alta", "Integrar datos propios de reproducciones y suscripciones (cuando la empresa los entregue)",
     "Reemplaza el proxy externo (popularidad TMDB) por consumo real y es el requisito para medir el impacto de las adquisiciones; hoy no están disponibles",
     "Alto", "Requiere acceso a fuentes corporativas de usuarios"),
    ("2 · Alta", "Corregir la fuente: clasificación etaria y duración reales",
     "Habilita los KPIs de clasificación que pide el caso; hoy <code>rating</code> es una copia de <code>vote_average</code>",
     "Bajo", "Viable: es un ajuste de extracción del equipo Data &amp; Analytics"),
    ("3 · Media", "Agregar el costo de licencia por título para calcular costo por punto de popularidad",
     "El ROI de taquilla no es el retorno de StreamView; el costo de licencia sí lo es",
     "Medio", "Requiere datos del área de Adquisición"),
    ("4 · Media", "Vista 'lista de compra': títulos candidatos de géneros y mercados prioritarios que aún no están en el catálogo",
     "Pasa del diagnóstico a una acción concreta con los mismos filtros del dashboard",
     "Medio", "Viable con los datos actuales + un listado externo de candidatos"),
    ("5 · Baja", "Modo oscuro validado y texturas para impresión y daltonismo severo",
     "La paleta ya está validada; esto extiende la accesibilidad a otros contextos de uso",
     "Bajo", "Viable de inmediato"),
]
RECS = [
    ("Aumentar la adquisición de <b>Animación y Familiar</b> (películas y series)",
     f"Animación (películas): popularidad relativa {N['ani_pct']}/100 (típico = 50), calificación {N['ani_nota']} y solo {N['ani_share']} de la oferta. ROI mediano {N['roi_ani']}x ({N['rent_ani']} rentables) y Familiar {N['roi_fam']}x ({N['rent_fam']}). El top 10 mejor evaluado está dominado por animación.",
     "Más títulos en el cuadrante de oportunidad; mayor calificación media del catálogo."),
    ("Crecer en <b>contenido latinoamericano</b> en español/portugués, con foco en <b>telenovelas y reality</b>",
     f"Español: {N['esp_share']} del catálogo pero con popularidad relativa {N['esp_pct']}/100 (sobre el típico y sobre el inglés). Telenovela: +{N['tel']} pp de brecha, popularidad relativa {N['tel_pct']}. México (popularidad relativa {N['mx_pct']}, {N['mx_sh']} de las producciones), Chile ({N['cl_pct']}) y Colombia ({N['co_pct']}).",
     "Coherente con la visión de StreamView (líder en Latinoamérica): catálogo más relevante para el mercado propio."),
    ("<b>Reducir la adquisición incremental de Drama</b> y reasignar ese presupuesto",
     f"Drama es el género más ofertado pero está sub-representado entre los más populares ({N['dr_m']} pp en películas, {N['dr_s']} pp en series). ROI mediano {N['roi_dr']}x, solo {N['rent_dr']} rentables.",
     "Libera presupuesto para las recomendaciones 1 y 2 sin aumentar el gasto total."),
    ("Mantener un <b>pipeline asiático de calidad</b> (Japón y Corea del Sur)",
     f"Mejor calificación media entre los 15 mayores productores: Japón {N['jp']}, Corea del Sur {N['kr']}. Actores de voz de anime dominan el ranking de frecuencia.",
     "Sostiene la calificación media del catálogo con los productores mejor evaluados."),
    ("<b>Portafolio de películas balanceado</b>: blockbusters para estabilidad + apuestas de bajo presupuesto en terror/misterio",
     f"El {N['block']} de las películas > USD 60 M recupera su inversión vs {N['bajo']} de las < USD 5 M; pero las 'joyas' de bajo presupuesto logran ROI de 20x–95x (Get Out, Insidious, Lights Out).",
     "Controla el riesgo (37% de películas no recupera la inversión) sin renunciar a alto retorno."),
    ("Exigir a la fuente <b>clasificación etaria y duración</b> y sumar datos propios de consumo",
     "Hoy no es posible calcular los KPIs de clasificación del caso; la popularidad es un proxy externo.",
     "Habilita los KPIs de clasificación del caso y, cuando existan datos de usuarios, medir consumo real en vez de un proxy."),
]


# Indicador de seguimiento por recomendación (cómo se medirá el impacto: aún NO está medido)
SEGUIMIENTO = [
    "% de Animación y Familiar en el catálogo; calificación media de los títulos incorporados",
    "% del catálogo en español/portugués; brecha de Telenovela (pp) y popularidad relativa de títulos LatAm incorporados",
    "% de Drama en las nuevas adquisiciones; brecha de Drama (pp)",
    "Calificación media de títulos de Japón y Corea del Sur incorporados",
    "% de películas adquiridas con ROI ≥ 1 y ROI mediano del portafolio",
    "% de registros con clasificación etaria y duración válidas",
]
RECS = [r + (SEGUIMIENTO[i],) for i, r in enumerate(RECS)]


def tabla(filas, cab):
    th = "".join(f"<th>{c}</th>" for c in cab)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in fila) + "</tr>" for fila in filas)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>"


def fig(nombre, cap):
    return f"<figure><img src='{IMG}/{nombre}.png'><figcaption>{cap}</figcaption></figure>"


HTML = f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>Informe Ejecutivo · StreamView Analytics</title>
<style>
 @page {{ size: A4; margin: 16mm 15mm 16mm 15mm; }}
 body {{ font-family: "Segoe UI", system-ui, sans-serif; color: #0b0b0b; font-size: 10.3pt; line-height: 1.5; }}
 h1 {{ font-size: 25pt; margin: 0 0 4pt; letter-spacing: -0.02em; }}
 h2 {{ font-size: 15pt; margin: 20pt 0 6pt; padding-bottom: 3pt; border-bottom: 2px solid #6250d6; break-after: avoid; }}
 h3 {{ font-size: 11.5pt; margin: 12pt 0 4pt; color: #0b0b0b; break-after: avoid; }}
 p {{ margin: 4pt 0 6pt; text-align: justify; }}
 .muted {{ color: #52514e; }}
 .cover {{ height: 255mm; display: flex; flex-direction: column; justify-content: center; break-after: page; }}
 .cover .tag {{ color: #6250d6; font-weight: 600; letter-spacing: .08em; font-size: 10pt; }}
 .cover .sub {{ font-size: 14pt; color: #52514e; margin-bottom: 30pt; }}
 .big {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8pt; margin: 10pt 0; }}
 .kpi {{ border: 1px solid #e1e0d9; border-radius: 8px; padding: 8pt 10pt; background: #fcfcfb; }}
 .kpi .v {{ font-size: 18pt; font-weight: 600; }} .kpi .l {{ font-size: 8.5pt; color: #52514e; }}
 .box {{ background: #f3f2fb; border-left: 4px solid #6250d6; padding: 8pt 12pt; border-radius: 4px; margin: 8pt 0; }}
 figure {{ margin: 8pt 0 10pt; break-inside: avoid; }} figure img {{ width: 100%; border: 1px solid #ecebe6; border-radius: 4px; }}
 figcaption {{ font-size: 8.5pt; color: #52514e; margin-top: 2pt; }}
 table {{ border-collapse: collapse; width: 100%; font-size: 8.6pt; margin: 6pt 0 10pt; break-inside: auto; }}
 th {{ background: #efeee9; text-align: left; padding: 4pt 5pt; border-bottom: 1px solid #c3c2b7; }}
 td {{ padding: 4pt 5pt; border-bottom: 1px solid #e1e0d9; vertical-align: top; }}
 tr {{ break-inside: avoid; }}
 .two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10pt; }}
 .pb {{ break-before: page; }}
 .model {{ display: flex; align-items: center; gap: 6pt; margin: 8pt 0; break-inside: avoid; }}
 .model .col {{ display: flex; flex-direction: column; gap: 5pt; flex: 1; }}
 .model .ent {{ border: 1px solid #c3c2b7; border-radius: 6px; padding: 5pt 7pt; font-size: 8.4pt; background: #fcfcfb; }}
 .model .ent.src {{ background: #f1f0ec; }} .model .ent.main {{ background: #f3f2fb; border-color: #6250d6; }}
 .model .arrow {{ text-align: center; font-size: 8pt; color: #52514e; width: 62pt; }}
 code {{ font-size: 8.8pt; background: #f1f0ec; padding: 0 3pt; border-radius: 3px; }}
 ol li, ul li {{ margin-bottom: 3pt; }}
</style></head><body>

<div class="cover">
 <div class="tag">ADY1104 · VISUALIZACIÓN DE DATOS · INFORME EJECUTIVO</div>
 <h1>Catálogo audiovisual: dónde invertir y qué adquirir</h1>
 <div class="sub">Solución de Visual Analytics para la Gerencia de Contenidos y Adquisición de StreamView Analytics</div>
 <div class="big">
  <div class="kpi"><div class="v">{N['total']}</div><div class="l">títulos analizados (2010–2025)</div></div>
  <div class="kpi"><div class="v">24</div><div class="l">visualizaciones justificadas</div></div>
  <div class="kpi"><div class="v">7</div><div class="l">vistas en el dashboard interactivo</div></div>
  <div class="kpi"><div class="v">6</div><div class="l">recomendaciones basadas en evidencia</div></div>
 </div>
</div>

<h2>Resumen ejecutivo</h2>
<div class="box"><b>Mensaje principal:</b> el catálogo de StreamView está sobre-invertido en Drama y en contenido en inglés,
mientras que la popularidad y la calidad apuntan a <b>Animación y Familiar</b>, a <b>contenido latinoamericano</b>
(telenovelas, México, Chile, Colombia) y a <b>producciones asiáticas</b>. Reasignar la adquisición hacia esos segmentos
alinea el catálogo con la visión de la empresa —ser la plataforma líder en Latinoamérica— y con lo que la audiencia
valora.</div>
<div class="big">
 <div class="kpi"><div class="v">{N['esp_share']}</div><div class="l">del catálogo está en español, con popularidad relativa {N['esp_pct']} (típico = 50)</div></div>
 <div class="kpi"><div class="v">+{N['ac_m']} pp</div><div class="l">brecha demanda–oferta de Acción y aventura (películas)</div></div>
 <div class="kpi"><div class="v">{N['dr_m']} pp</div><div class="l">brecha de Drama (películas): sobre-ofertado</div></div>
 <div class="kpi"><div class="v">{N['nofin']}</div><div class="l">de las películas no recupera su presupuesto</div></div>
</div>

<h2>1. Descripción del problema de negocio</h2>
<p>StreamView Analytics es una plataforma de streaming por suscripción con presencia en Latinoamérica, fundada en 2018,
que incorpora semanalmente nuevas producciones de distintos países e idiomas. El crecimiento del catálogo generó un
problema de gestión de la información: cada área usa reportes construidos con criterios diferentes, existen múltiples
versiones de un mismo indicador y <b>las decisiones de adquisición se toman con información parcial</b>
(problemas 1, 3 y 6 del caso). La Gerencia de Contenidos y Adquisición no puede identificar con rapidez qué géneros,
países y contenidos tienen mayor potencial, y los dashboards existentes presentan exceso de información y poca interacción (problema 7).</p>
<p><b>Pregunta de negocio que guía el proyecto:</b> <i>¿Qué tipo de contenido, de qué géneros y de qué mercados debería
adquirir y priorizar StreamView para tener un catálogo más popular y mejor evaluado?</i></p>

<h2>2. Objetivos del proyecto</h2>
<p><b>Objetivo general.</b> Diseñar e implementar una solución de Visual Analytics que comunique la composición, popularidad,
valoración y rentabilidad del catálogo para apoyar las decisiones de adquisición de la Gerencia de Contenidos.</p>
<ol>
 <li>Caracterizar el catálogo por tipo, género, país e idioma (KPIs del catálogo).</li>
 <li>Detectar brechas entre la oferta del catálogo y la demanda (popularidad) por género y mercado.</li>
 <li>Comparar popularidad y calificación para identificar contenido valioso que no es evidente con una sola métrica.</li>
 <li>Analizar la relación presupuesto–ingresos de las películas para orientar el riesgo de inversión.</li>
 <li>Entregar un dashboard interactivo y una narrativa visual con recomendaciones sustentadas en evidencia.</li>
</ol>

<h2>3. Audiencia objetivo y propósito comunicacional</h2>
<p><b>Audiencia principal: Gerente de Contenidos y Adquisición.</b> Responsable de evaluar oportunidades de incorporación de
títulos, negociar licencias con estudios y definir la composición futura del catálogo. Perfil: experto en el negocio
audiovisual, no en estadística; necesita respuestas rápidas, comparables y accionables.</p>
{tabla([
 ["Necesidad de la audiencia", "Cómo la responde la solución"],
 ["¿Qué géneros adquirir?", "Brecha oferta/demanda + matriz de oportunidad con detalle por género (clic)"],
 ["¿Qué mercados tienen potencial?", "Mapa, ranking de popularidad por país con Latinoamérica destacada, calificación por país"],
 ["¿Qué riesgo financiero asumo?", "ROI mediano por género y por tramo de presupuesto, éxitos de bajo presupuesto"],
 ["¿Qué títulos destacar?", "Rankings de popularidad, calificación ponderada y votos"],
][1:], ["Necesidad de la audiencia", "Cómo la responde la solución"])}
<p><b>Propósito comunicacional:</b> <i>persuadir con evidencia</i> para reorientar la política de adquisición. Por eso cada
gráfico tiene un <b>título-hallazgo</b> (la conclusión, no el tema), un subtítulo con período y alcance (regla 7), un color
de foco sobre gris de contexto para guiar la mirada, y lenguaje de negocio en español. Audiencias secundarias:
Directorio (vista Resumen ejecutivo) y Marketing (rankings y mercados).</p>

<h2>4. Fuentes de datos, integración y calidad</h2>
<p>Se usaron exclusivamente las dos fuentes oficiales del caso: <b>Netflix Movies Detailed up to 2025</b> (16.000 películas,
18 variables) y <b>Netflix TV Shows Detailed up to 2025</b> (16.000 series, 16 variables), con metadatos de TMDB.
Ambas se integraron en un catálogo unificado de {N['total']} títulos más tres tablas derivadas (géneros, países y personas,
porque son campos multivalor). Variables relevantes: <code>type</code>, <code>genres</code>, <code>country</code>,
<code>language</code>, <code>release_year</code>, <code>date_added</code>, <code>popularity</code>, <code>vote_average</code>,
<code>vote_count</code>, <code>budget</code>, <code>revenue</code>, <code>director</code>, <code>cast</code>.</p>
<h3>4.1 Modelo de datos y relaciones</h3>
<div class="model">
 <div class="col"><div class="ent src"><b>movies_clean.csv</b><br>16.000 películas · 18 variables<br><small>incluye budget, revenue</small></div>
  <div class="ent src"><b>tvshows_clean.csv</b><br>16.000 series · 16 variables<br><small>sin budget ni revenue</small></div></div>
 <div class="arrow">unión<br>→<br><small>uid = tipo + show_id</small></div>
 <div class="col"><div class="ent main"><b>catalogo</b> (32.000)<br>PK <code>uid</code><br><small>tipo, año, idioma, popularidad, percentil, nota, nota ponderada, ROI…</small></div></div>
 <div class="arrow">1 : N<br>→<br><small>explosión de campos multivalor</small></div>
 <div class="col"><div class="ent"><b>catalogo_generos</b><br>uid → género armonizado</div>
  <div class="ent"><b>catalogo_paises</b><br>uid → país, ISO-3</div>
  <div class="ent"><b>catalogo_personas</b><br>uid → director / actor</div></div>
</div>
<p>Las dos fuentes comparten 16 variables y se apilan en una sola tabla (<code>catalogo</code>); como los <code>show_id</code>
de TMDB se repiten entre películas y series, la clave es <code>uid</code>. Los campos con varios valores por título
("Drama, Romance"; "Reino Unido, Estados Unidos") se separan en tablas relacionadas 1:N por <code>uid</code>; así un título
cuenta en cada uno de sus géneros o países, y todos los filtros del dashboard se propagan entre tablas por esa clave.</p>
{tabla([
 ["<code>type</code> → tipo", "Ambos", "Separar y comparar películas vs series (regla 2)"],
 ["<code>genres</code> → género armonizado", "Ambos", "Oferta vs demanda por género, matriz de oportunidad"],
 ["<code>country</code>, <code>language</code>", "Ambos", "Mercados, mapa, idiomas"],
 ["<code>popularity</code> → percentil dentro del tipo", "Ambos", "Demanda relativa (índice TMDB, no reproducciones)"],
 ["<code>vote_average</code> + <code>vote_count</code> → nota, nota ponderada", "Ambos", "Calidad percibida (≥ 10 votos)"],
 ["<code>release_year</code>, <code>date_added</code>", "Ambos", "Composición en el tiempo, estacionalidad"],
 ["<code>budget</code>, <code>revenue</code> → ROI, tramo", "Solo películas", "Riesgo y retorno de inversión (reglas 3, 6 y 9)"],
 ["<code>director</code>, <code>cast</code>", "Ambos (69% sin director en series)", "Talento más frecuente"],
], ["Variable (→ derivada)", "Disponible en", "Uso en el análisis"])}
<div class="box"><b>Alcance y límites.</b> Las decisiones se fundamentan en datos de <b>catálogo</b>: contenidos, popularidad
y valoración; los indicadores financieros solo para películas con datos válidos. Las pautas mencionan fuentes corporativas
de usuarios, suscripciones y reproducciones, pero <b>no están disponibles</b> en este proyecto; por eso la solución
<b>no analiza retención, engagement ni comportamiento de usuarios</b>, y no promete impacto sobre esas métricas.</div>
<p><b>Popularidad relativa (0–100).</b> Para comparar películas y series —cuya popularidad TMDB se calcula en escalas distintas— cada título recibe su posición dentro de su tipo: 50 es el título típico y 80 significa que es más popular que el 80% de los títulos de su tipo. Para un género o país se informa la del título típico del grupo.</p>
<h3>4.2 Calidad de los datos</h3>
{fig("00_calidad_datos", "Figura 1. Problemas de calidad por variable y dataset (datos originales).")}
{tabla([
 ["`rating` = `vote_average` en el 100% (no es clasificación etaria)", "Excluida → los KPIs de clasificación etaria no son calculables (limitación reportada)"],
 ["`duration` vacía (películas) o constante '1 Seasons' (series)", "Excluida"],
 ["'Sin información' como texto (69% director en series)", "Convertido a nulo; limitación indicada en los gráficos"],
 ["397 `show_id` repetidos entre películas y series", "Clave única `uid` = tipo + id"],
 [f"Calificaciones con pocos votos (mediana de 4 votos en series)", f"`nota` solo con ≥ 10 votos ({N['val']} de los títulos; {N['val_s']} de las series) + calificación bayesiana para rankings"],
 ["Popularidad muy asimétrica; escalas distintas por tipo", "Mediana, percentil dentro de cada tipo, escala log"],
 ["Exactamente 1.000 títulos por año y tipo (muestra estratificada)", "Se analiza composición, no volumen"],
 ["Presupuestos de USD 1–7.000 con ingresos millonarios (errores)", f"Universo financiero: budget ≥ USD 100 mil y revenue > 0 → {N['nfin']} películas"],
 ["Géneros con taxonomías distintas entre tipos", "Taxonomía armonizada en español para comparar (regla 2)"],
], ["Problema detectado", "Decisión"])}

<h2 class="pb">5. Análisis exploratorio mediante visualizaciones</h2>
<h3>5.1 Composición del catálogo</h3>
{fig("01_treemap_generos", "Figura 2. Drama y Comedia dominan ambos tipos; Animación, Familiar y Telenovela ocupan áreas pequeñas.")}
<div class="two">{fig("02_idiomas", f"Figura 3. El inglés concentra {N['eng_share']}; el español, con {N['esp_share']}, tiene popularidad sobre la mediana.")}
{fig("03_mapa_produccion", f"Figura 4. EE.UU. concentra {N['us_sh']} de las producciones (escala log).")}</div>
<div class="two">{fig("13_mix_generos_peliculas", "Figura 5. De cada 10 películas, 2 son Drama y menos de 1 es Animación o Familiar.")}
{fig("14_mix_generos_series", "Figura 6. En series, Drama sube de ~3 a ~4 de cada 10 títulos en los últimos años.")}</div>
<h3>5.2 Popularidad y valoración</h3>
<div class="two">{fig("09_dist_popularidad", f"Figura 7. Series: popularidad mediana {N['pop_ratio']}x la de películas.")}
{fig("10_dist_nota", f"Figura 8. Series mejor evaluadas: {N['nota_s']} vs {N['nota_m']}.")}</div>
<div class="two">{fig("11_pop_vs_nota", f"Figura 9. La nube no forma una diagonal: ser popular no implica estar bien evaluado (correlación {N['rho_m']}).")}
{fig("12_tendencia_nota", "Figura 10. La calificación media de películas sube desde 2010.")}</div>
<div class="two">{fig("19_top_populares", "Figura 11. Más populares: talk shows, telenovelas brasileñas y estrenos recientes.")}
{fig("20_top_evaluados", "Figura 12. Mejor evaluados (bayesiano): todas series, mayoría animación.")}</div>
<h3>5.3 Oferta vs demanda: géneros y mercados</h3>
{fig("04_brecha_oferta_demanda", "Figura 13. Brecha = % del género en el 20% más popular − % en el catálogo.")}
<div class="two">{fig("05_matriz_peliculas", "Figura 14. Matriz de oportunidad · películas.")}
{fig("06_matriz_series", "Figura 15. Matriz de oportunidad · series.")}</div>
<div class="two">{fig("07_mercados", "Figura 16. Chile, México y Colombia: popularidad alta con poca oferta.")}
{fig("08_paises_nota", "Figura 17. Japón, Corea y México: contenido mejor evaluado.")}</div>
<h3>5.4 Rentabilidad (solo películas)</h3>
{fig("16_presupuesto_ingresos", f"Figura 18. {N['nofin']} de las películas no recupera la inversión; joyas de bajo presupuesto anotadas.")}
<div class="two">{fig("17_roi_genero", "Figura 19. ROI mediano por género.")}
{fig("18_rentabilidad_tramo", "Figura 20. % de películas rentables por tramo de presupuesto.")}</div>
<h3>5.5 Producción y talento</h3>
<div class="two">{fig("21_top_directores", "Figura 21. Directores con más títulos.")}
{fig("22_top_actores", "Figura 22. Actores más frecuentes: dominan actores de voz de anime.")}</div>

<h2 class="pb">6. Justificación de las representaciones gráficas</h2>
<p>La forma de cada gráfico se eligió según <b>el tipo de dato</b>, <b>la pregunta</b> y <b>la audiencia</b>; el color se asignó
al final y según su función (identidad, magnitud, polaridad o foco). Principios aplicados: jerarquía visual
(título-hallazgo → gráfico → detalle en hover), atributos preatentivos (un color de foco sobre gris), proximidad y
alineación (Gestalt), alta relación datos-tinta (grilla tenue, sin bordes ni 3D), un solo eje Y por gráfico y
etiquetas directas selectivas.</p>
{tabla(JUST, ["Visualización", "Tipo de dato", "Pregunta que responde", "Por qué esta forma", "Alternativa descartada"])}
<h3>Color y accesibilidad</h3>
<ul>
 <li><b>Categórico:</b> película = azul <code>#2a78d6</code>, serie = naranjo <code>#eb6834</code>, en todos los gráficos (el color sigue a la entidad).
 Paleta validada computacionalmente para protanopía, deuteranopía y tritanopía (separación ΔE ≥ 9).</li>
 <li><b>Foco:</b> violeta <code>#6250d6</code> sobre gris <code>#d6d5ce</code> para dirigir la atención a la oportunidad.</li>
 <li><b>Secuencial:</b> un solo tono (azul claro → oscuro) en mapa y mapa de calor; nunca arcoíris.</li>
 <li><b>Legibilidad:</b> tipografía sans-serif del sistema, tamaño mínimo 10–11 px, números en formato chileno (12.345,6),
 leyenda siempre presente con ≥ 2 series y etiquetas directas; la identidad nunca depende solo del color.</li>
</ul>

<h2>7. Narrativa visual (Data Storytelling)</h2>
<p>La narrativa sigue los 4 pasos de la evaluación (qué ocurre → qué lo sustenta → qué limita → qué decidir), que también
cubren las 4 preguntas del caso (¿qué ocurre?, ¿por qué?, ¿qué evidencia?, ¿qué decisiones?):</p>
{tabla([
 ["1. Qué ocurre (hallazgo principal)", f"Lo más ofertado no es lo más demandado: el catálogo se concentra en Drama (23% de las asignaciones de género) y en inglés ({N['eng_share']}), mientras la popularidad apunta a Animación, Familiar, Telenovela y Latinoamérica.", "Treemap, brecha oferta/demanda"],
 ["2. Qué lo sustenta (datos y visualizaciones)", f"Drama {N['dr_m']} pp de brecha; Acción y aventura +{N['ac_m']} pp; Telenovela +{N['tel']} pp; Animación con popularidad relativa {N['ani_pct']}/100 y nota {N['ani_nota']} y ROI {N['roi_ani']}x; español con popularidad relativa {N['esp_pct']}/100 y {N['esp_share']} de oferta. Popularidad y calidad casi no se relacionan (correlación {N['rho_m']}), por eso se miran juntas.", "Matriz de oportunidad, dispersión, mercados, ROI"],
 ["3. Qué limita (sesgos, riesgos y alcance)", "Popularidad TMDB ≠ consumo propio; muestra de 1.000 títulos/año; finanzas solo para 22% de las películas; sin clasificación etaria; sin datos de usuarios (no se analiza retención).", "Gráfico de calidad de datos, sección 9"],
 ["4. Qué decidir (recomendación e impacto)", "Reasignar la adquisición hacia Animación/Familiar, Latinoamérica y Asia de calidad, con menos Drama y un portafolio de películas balanceado; seguir el impacto esperado con indicadores.", "Recomendaciones (sección 10)"],
], ["Paso", "Mensaje", "Visualizaciones"])}
<p>Recursos aplicados: títulos-hallazgo (el lector entiende la conclusión aunque solo lea los títulos), anotaciones
sobre los casos ejemplares (Get Out, Avengers: Endgame), cuadrantes con nombre de decisión, y un mismo hilo
—<i>oferta vs demanda</i>— que conecta géneros, idiomas y mercados. Para la exposición oral se usa el mismo orden en la
presentación ejecutiva (10 minutos) y el dashboard como respaldo para preguntas.</p>

<h2 class="pb">8. Diseño e implementación del dashboard interactivo</h2>
<p><b>Tecnología:</b> Python + Streamlit + Plotly (código en <code>dashboard/app.py</code>, gráficos en <code>src/charts.py</code>).
Se ejecuta con <code>streamlit run dashboard/app.py</code>.</p>
{tabla([
 ["🏠 Resumen ejecutivo", "10 KPIs, 4 hallazgos dinámicos, brecha de géneros, mapa", "Directorio / Gerente: estado en 30 segundos"],
 ["🎯 Oportunidades de adquisición", "Matriz con clic → detalle del género; dispersión; tendencias; rankings intercambiables", "Vista central del Gerente de Contenidos"],
 ["📚 Composición del catálogo", "Treemap, idiomas con foco seleccionable, áreas 100%, mapa de calor, estacionalidad", "Caracterización del catálogo"],
 ["🌎 Mercados", "Mapa (volumen o popularidad), oferta vs demanda por país, calificación, tabla", "Priorización de países"],
 ["💰 Finanzas (películas)", "KPIs financieros, presupuesto vs ingresos, ROI por género y tramo, joyas", "Riesgo de inversión"],
 ["🎬 Talento", "Directores y actores más frecuentes por tipo", "Negociación con estudios / talento"],
 ["🧾 Datos y metodología", "Calidad de datos, decisiones, descarga CSV", "Transparencia y confianza"],
], ["Vista (navegación por pestañas)", "Contenido", "Audiencia y propósito"])}
<p>Cada página del dashboard abre con un encabezado de tres bloques —<b>Audiencia</b>, <b>Pregunta que responde</b> y
<b>Decisión que habilita</b>— para que el usuario sepa para qué sirve antes de mirar los gráficos.</p>
<p><b>Interacción:</b> 5 filtros globales en la barra lateral (tipo, año, género, idioma, país) que se propagan a todas
las vistas y tablas; botón de restablecer; selección de burbuja con <i>drill-down</i>; controles segmentados para cambiar
la métrica; tooltips con detalle en todos los gráficos; exportación PNG; descarga del alcance filtrado. Los títulos
se recalculan con cada filtro y la línea "Alcance" indica siempre qué se está mirando.</p>
{fig("dashboard_tab0", "Figura 23. Vista Resumen ejecutivo: KPIs, hallazgos dinámicos, brecha y mapa.")}
{fig("dashboard_tab1_vista", "Figura 24. Vista Oportunidades: matriz interactiva (clic en una burbuja para ver los títulos del género).")}
<div class="two">{fig("dashboard_tab4_vista", "Figura 25. Vista Finanzas (películas).")}
{fig("dashboard_tab3_vista", "Figura 26. Vista Mercados.")}</div>

<h2 class="pb">9. Evaluación crítica de la solución</h2>
<h3>9.1 Fortalezas</h3>
{tabla(EVAL_F, ["Fortaleza", "Evidencia"])}
<h3>9.2 Limitaciones, sesgos y riesgos (con mitigación)</h3>
{tabla(EVAL_L, ["Limitación / sesgo", "Riesgo", "Mitigación aplicada o propuesta"])}
<h3>9.3 Oportunidades de mejora priorizadas</h3>
<p>Priorizadas por impacto en la decisión de adquisición y viabilidad (esfuerzo y dependencia de datos):</p>
{tabla(EVAL_M, ["Prioridad", "Mejora", "Fundamento técnico", "Esfuerzo", "Viabilidad / requisito"])}
<h3>9.4 Decisiones de diseño revisadas durante el desarrollo</h3>
<ul>
 <li><b>Simplificación para la audiencia:</b> dos gráficos eran difíciles de explicar. El mix de géneros pasó de 6 bandas por "asignaciones de género" a 3 grupos por género principal ("de cada 10 películas, 2 son Drama"), y mercados pasó de una dispersión logarítmica a un ranking de barras con el % del catálogo anotado. Además, "percentil" se reemplazó por <i>popularidad relativa (0–100; 50 = título típico)</i> y cada gráfico del dashboard tiene una línea "Cómo leer".</li>
 <li>Se descartó un gráfico de "títulos por año" (línea plana por la muestra estratificada) y se reemplazó por áreas al 100%.</li>
 <li>El histograma superpuesto mezclaba colores (azul + naranjo = marrón); se cambió a barras agrupadas.</li>
 <li>Las etiquetas de la matriz de oportunidad se superponían; se implementó un algoritmo de ubicación con líneas guía.</li>
 <li>Los títulos fijos podían quedar falsos al filtrar; se cambiaron por títulos calculados desde los datos.</li>
</ul>

<h2>10. Conclusiones y recomendaciones</h2>
<p><b>Conclusiones.</b> (1) El catálogo está concentrado en lo que más abunda, no en lo que más se demanda.
(2) Popularidad y calidad son dimensiones casi independientes, por lo que deben evaluarse juntas. (3) Animación y
Familiar son los únicos géneros que combinan alta popularidad, alta calificación y retorno financiero sobre la mediana.
(4) Latinoamérica —el mercado objetivo de StreamView— está sub-representada pese a su alta popularidad relativa.
(5) La calidad de los datos limita algunos KPIs del caso y debe corregirse en la fuente.</p>
{tabla(RECS, ["Recomendación", "Evidencia del análisis (medida)", "Impacto esperado (no medido aún)", "Indicador de seguimiento"])}
<div class="box"><b>Impacto esperado vs resultados medidos.</b> La columna "Evidencia" contiene resultados <b>ya medidos</b>
en los datos del catálogo. La columna "Impacto esperado" es una <b>proyección</b>: todavía no ha ocurrido ni se ha medido.
Para verificarla, el dashboard permite seguir los indicadores de la última columna en cada actualización del catálogo
(línea base = valores de este informe). No se afirma impacto en retención, engagement ni ingresos por suscripción, porque
no hay datos de usuarios disponibles.</div>
<div class="box"><b>Impacto esperado de la solución:</b> la Gerencia de Contenidos pasa de reportes aislados a una
herramienta única donde, en minutos, puede (a) ubicar un género o país candidato en la matriz de oportunidad, (b) verificar
su calidad y riesgo financiero, y (c) bajar a la lista de títulos concretos. Esto responde a los problemas 1, 3, 4, 6 y 7
del caso y permite medir el efecto de las recomendaciones en el tiempo con los mismos KPIs.</div>

<h2>Anexo · Reproducibilidad</h2>
{tabla([
 ["<code>python src/prepare_data.py</code>", "Integra y limpia los datos → <code>data/processed/</code>"],
 ["<code>python src/export_images.py</code>", "Regenera las 24 visualizaciones → <code>images/</code>"],
 ["<code>python src/build_notebooks.py</code>", "Ejecuta los notebooks de calidad y EDA → <code>notebooks/</code>"],
 ["<code>python src/build_report.py</code>", "Genera este informe → <code>reports/</code>"],
 ["<code>streamlit run dashboard/app.py</code>", "Abre el dashboard interactivo"],
], ["Comando", "Resultado"])}
</body></html>"""


def chrome() -> str | None:
    for c in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              "/usr/bin/google-chrome", "/usr/bin/chromium"]:
        if Path(c).exists():
            return c
    return None


def main():
    REP.mkdir(exist_ok=True)
    html = REP / "Informe_Ejecutivo_StreamView.html"
    import re
    html.write_text(re.sub(r"`([^`<>]+)`", r"<code>\g<1></code>", HTML), encoding="utf-8")
    pdf = REP / "Informe_Ejecutivo_StreamView.pdf"
    exe = chrome()
    if exe:
        subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", html.resolve().as_uri()], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("PDF:", pdf)
    else:
        print("Chrome/Edge no encontrado: abra el HTML y use Imprimir → PDF:", html)


if __name__ == "__main__":
    main()
