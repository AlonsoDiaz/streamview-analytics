"""
StreamView Analytics · Dashboard de Contenidos y Adquisición
------------------------------------------------------------
Audiencia principal: Gerencia de Contenidos y Adquisición.
Ejecutar desde la raíz del proyecto:

    streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import importlib  # noqa: E402

import charts as C  # noqa: E402
import data as _data  # noqa: E402
import theme as T  # noqa: E402

# Streamlit no recarga módulos fuera de dashboard/: se recargan en cada ejecución para
# que un cambio en src/ nunca deje corriendo código antiguo (evita errores con versiones viejas).
for _m in (T, _data, C):
    importlib.reload(_m)
filtrar, load = _data.filtrar, _data.load

st.set_page_config(page_title="StreamView · Contenidos y Adquisición", layout="wide",
                   initial_sidebar_state="expanded")

# --------------------------------------------------------------------------- estilos
st.markdown(f"""
<style>
  .block-container {{padding-top: 1.6rem; padding-bottom: 2rem; max-width: 1500px;}}
  h1, h2, h3 {{color: {T.INK}; letter-spacing: -0.01em;}}
  div[data-testid="stMetric"] {{background: {T.SURFACE}; border: 1px solid rgba(11,11,11,0.08);
      border-radius: 10px; padding: 12px 16px;}}
  div[data-testid="stMetricLabel"] p {{color: {T.INK_2}; font-size: 0.85rem;}}
  div[data-testid="stMetricValue"] {{color: {T.INK}; font-size: 1.65rem;}}
  .hallazgo {{background: {T.SURFACE}; border-left: 4px solid {T.FOCO}; border-radius: 6px;
      padding: 10px 14px; margin-bottom: 8px; color: {T.INK};}}
  .hallazgo b {{color: {T.INK};}}
  .proposito {{display:flex; gap:10px; margin: 2px 0 14px;}}
  .proposito div {{flex:1; background:{T.SURFACE}; border:1px solid rgba(11,11,11,0.08); border-radius:8px;
      padding:8px 12px; font-size:0.86rem; color:{T.INK_2};}}
  .proposito b {{display:block; color:{T.INK}; font-size:0.72rem; letter-spacing:.06em; text-transform:uppercase;}}
  .alcance {{color: {T.INK_2}; font-size: 0.9rem; margin-top: -0.6rem;}}
  .stTabs [data-baseweb="tab"] {{font-size: 0.98rem;}}
</style>
""", unsafe_allow_html=True)

PLOT_CFG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
            "toImageButtonOptions": {"format": "png", "scale": 2}}


def _wrap(texto: str, n: int) -> str:
    out, linea = [], ""
    for w in texto.split(" "):
        if len(linea) + len(w) + 1 > n and linea:
            out.append(linea)
            linea = w
        else:
            linea = f"{linea} {w}".strip()
    out.append(linea)
    return "<br>".join(out)


def plot(fig, key=None, select=False, ancho=None):
    """Envoltura única: ancho completo, configuración de la barra de herramientas y selección opcional.
    `ancho` = caracteres por línea del título (para gráficos en columnas angostas)."""
    if ancho and fig.layout.title and fig.layout.title.text and "<b>" in fig.layout.title.text:
        t = fig.layout.title.text
        head, rest = t.split("</b>", 1)
        sub = rest.split("'>", 1)[-1].replace("</span>", "") if "<span" in rest else ""
        nl = _wrap(head.replace("<b>", ""), ancho).count("<br>") + _wrap(sub, int(ancho * 1.35)).count("<br>")
        fig.update_layout(title_text=f"<b>{_wrap(head.replace('<b>', ''), ancho)}</b><br>"
                                     f"<span style='font-size:12px;color:{T.INK_2}'>{_wrap(sub, int(ancho * 1.35))}</span>",
                          margin_t=110 + 22 * nl)
        fig.update_layout(height=(fig.layout.height or 450) + 22 * nl)
    if select:
        ev = st.plotly_chart(fig, width="stretch", config=PLOT_CFG, key=key,
                             on_select="rerun", selection_mode="points")
    else:
        ev = None
        st.plotly_chart(fig, width="stretch", config=PLOT_CFG, key=key)
    if key in LEER:
        st.caption(f"**Cómo leer:** {LEER[key]}")
    return ev


# Una frase por gráfico para leerlo sin conocimientos estadísticos
LEER = {
    "res_brecha": "cada barra compara cuánto pesa un género entre los títulos más populares vs en el catálogo. "
                  "Barra de color hacia la derecha = falta oferta de ese género; gris hacia la izquierda = sobra.",
    "res_mapa": "más oscuro = más títulos producidos en ese país. La escala es logarítmica para que EE.UU. no tape al resto.",
    "mapa2": "más oscuro = más títulos (o más popularidad, según el botón). Pase el mouse sobre un país para ver el detalle.",
    "matriz": "cada burbuja es un género. Más a la derecha = más popular; más arriba = mejor evaluado; más grande = más títulos "
              "en el catálogo. Lo ideal: burbujas chicas arriba a la derecha (populares, bien evaluadas y con poca oferta).",
    "popnota": "cada punto es un título. Si popularidad y calificación fueran de la mano, los puntos formarían una diagonal; "
               "como forman una nube, hay que mirar ambas métricas para decidir.",
    "tend": "cada línea es la calificación promedio de los títulos estrenados ese año. El círculo vacío (2025) tiene pocos votos todavía.",
    "distpop": "la caja contiene la mitad central de los títulos y la raya del medio es el título típico. "
               "Los puntos a la derecha son éxitos excepcionales.",
    "distnota": "cada barra muestra qué % de títulos tiene esa nota. La línea punteada es el promedio de cada tipo.",
    "rank": "los 10 títulos con mayor valor en la métrica elegida; el color indica si es película o serie.",
    "tree": "cada rectángulo es un género y su tamaño es la cantidad de títulos. Azul = películas, naranjo = series.",
    "idiomas": "izquierda: cuánto del catálogo está en cada idioma. Derecha: qué tan popular es ese contenido (50 = título típico). "
               "Un idioma con poca barra a la izquierda y mucha a la derecha está sub-ofertado.",
    "mix": "de cada 100 títulos estrenados cada año, cuántos tienen como género principal Drama, Animación/Familiar u otro.",
    "heat": "cada celda es un género en un año; más oscuro = más popular (o mejor evaluado). Filas oscuras de punta a punta = géneros consistentemente fuertes.",
    "meses": "cantidad de títulos incorporados a la plataforma en cada mes; en color, los dos meses con más incorporaciones.",
    "merc": "barra más larga = el contenido de ese país es más popular (50 = título típico). "
            "El texto indica cuánto pesa ese país en el catálogo: barra larga + % chico = oportunidad.",
    "pnota": "cada punto es la calificación promedio del contenido de un país; en color, los que superan el promedio (línea punteada).",
    "budrev": "cada punto es una película. Sobre la línea punteada inferior recuperó lo invertido; sobre la superior ganó 5 veces su costo.",
    "roig": "ROI = ingresos ÷ presupuesto de la película típica de cada género. 2x = recupera el doble de lo invertido; bajo 1x pierde dinero.",
    "tramo": "de cada 100 películas en cada rango de presupuesto, cuántas recuperaron su inversión.",
    "dir": "directores con más títulos en el catálogo; el color indica si dirigieron películas o series.",
    "act": "actores y actrices que más aparecen (5 primeros créditos de cada título).",
    "calidad": "% de registros con cada problema de datos, por fuente. Barras largas = variables que no se pueden usar o se usan con cuidado.",
}


def proposito(audiencia: str, pregunta: str, decision: str):
    """Encabezado de cada página: quién la usa, qué responde y qué decisión habilita."""
    st.markdown(f"<div class='proposito'><div><b>Audiencia</b>{audiencia}</div>"
                f"<div><b>Pregunta que responde</b>{pregunta}</div>"
                f"<div><b>Decisión que habilita</b>{decision}</div></div>", unsafe_allow_html=True)


@st.cache_data(show_spinner="Cargando catálogo…")
def datos():
    return load()


D = datos()

NAN = float("nan")
ASIA = ["Japón", "Corea del Sur"]
LAT_IDIOMAS = ["Español", "Portugués"]


def indicadores(cat: pd.DataFrame, gen: pd.DataFrame, pais: pd.DataFrame) -> dict:
    """Indicador de seguimiento de cada recomendación (misma definición que el informe ejecutivo)."""
    n = len(cat)
    tg = C.tabla_generos(gen, min_n=1)
    dr = tg[(tg["tipo"] == "Película") & (tg["genero"] == "Drama")]
    jk = pais.loc[pais["pais"].isin(ASIA), "nota"]
    fin = cat[cat["fin_valido"] == True]  # noqa: E712
    return {
        "af": gen.loc[gen["genero"].isin(["Animación", "Familiar"]), "uid"].nunique() / n if n else NAN,
        "latam": cat["idioma"].isin(LAT_IDIOMAS).mean() if n else NAN,
        "drama": dr["brecha_pp"].iloc[0] if len(dr) else NAN,
        "asia": jk.mean() if jk.notna().any() else NAN,
        "rent": (fin["roi"] >= 1).mean() if len(fin) else NAN,
    }


@st.cache_data(show_spinner=False)
def linea_base() -> dict:
    """Línea base = catálogo completo, sin filtros (valores del informe)."""
    return indicadores(D["cat"], D["gen"], D["pais"])


def _v(x, f):
    """Formatea un valor o devuelve '—' si no hay datos para los filtros actuales."""
    return "—" if x is None or pd.isna(x) else f(x)


COLS_TIT = {"title": "Título", "tipo": "Tipo", "release_year": "Año", "genero_principal": "Género",
            "pais_principal": "País", "idioma": "Idioma", "pct_popularidad": "Popularidad relativa",
            "nota": "Calificación", "vote_count": "Votos"}
CFG_TIT = {"Popularidad relativa": st.column_config.ProgressColumn(format="%.0f", min_value=0, max_value=100),
           "Calificación": st.column_config.NumberColumn(format="%.2f")}


def titulos_referencia(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Títulos populares (sobre el típico) ordenados por calificación ponderada."""
    d = df[(df["pct_popularidad"] >= 0.5) & df["nota"].notna()].nlargest(n, "nota_ponderada")
    d = d[list(COLS_TIT)].assign(pct_popularidad=lambda x: x["pct_popularidad"] * 100)
    return d.rename(columns=COLS_TIT)


def recomendacion(n: int, titulo: str, porque: str, evidencia: list, ind: tuple, respaldo: str, tabla=None, cfg=None):
    """Tarjeta de una recomendación: evidencia medida (con filtros) + indicador de seguimiento con línea base."""
    with st.container(border=True):
        st.markdown(f"#### {n}. {titulo}")
        st.markdown(porque)
        cols = st.columns(len(evidencia) + 1)
        for c, (lab, val, ayuda) in zip(cols, evidencia):
            c.metric(lab, val, help=ayuda)
        nombre, clave, f = ind
        base, actual = linea_base()[clave], IND[clave]
        cols[-1].metric(f"Indicador: {nombre}", _v(base, f), help="Línea base = catálogo completo hoy. "
                        "Es el valor contra el que se medirá el impacto en cada actualización del catálogo.")
        if FILTRADO:
            cols[-1].caption(f"Con los filtros actuales: **{_v(actual, f)}**")
        st.caption(f"Respaldo: {respaldo}")
        if tabla is not None:
            with st.expander("Ver títulos de referencia en el catálogo"):
                if tabla.empty:
                    st.info("No hay títulos para los filtros seleccionados.")
                else:
                    st.dataframe(tabla, hide_index=True, width="stretch", column_config=cfg or CFG_TIT)

# --------------------------------------------------------------------------- filtros (sidebar)
with st.sidebar:
    st.markdown("### StreamView Analytics")
    st.caption("Dashboard de la **Gerencia de Contenidos y Adquisición**")
    st.divider()
    st.markdown("**Filtros globales**")
    if st.button("Restablecer filtros", width="stretch"):
        for k in ["f_tipo", "f_anios", "f_gen", "f_idi", "f_pais"]:
            st.session_state.pop(k, None)
    tipos = st.multiselect("Tipo de contenido", ["Película", "Serie"], default=["Película", "Serie"], key="f_tipo")
    anios = st.slider("Año de estreno", 2010, 2025, (2010, 2025), key="f_anios")
    generos = st.multiselect("Género", sorted(D["gen"]["genero"].unique()), key="f_gen",
                             placeholder="Todos")
    top_idiomas = D["cat"]["idioma"].value_counts().index.tolist()
    idiomas = st.multiselect("Idioma original", top_idiomas, key="f_idi", placeholder="Todos")
    top_paises = D["pais"]["pais"].value_counts().index.tolist()
    paises = st.multiselect("País de producción", top_paises, key="f_pais", placeholder="Todos")
    st.divider()
    st.caption("Popularidad = índice relativo TMDB (no son reproducciones). Calificación válida = ≥ 10 votos. "
               "Finanzas solo para películas con presupuesto ≥ USD 100 mil.")

F = filtrar(D, tipos or None, anios, generos or None, idiomas or None, paises or None)
cat, gen, pais, pers = F["cat"], F["gen"], F["pais"], F["pers"]

# --------------------------------------------------------------------------- encabezado
st.title("Catálogo audiovisual: dónde invertir y qué adquirir")
filtros_txt = [f"{C.tipos_txt(cat) if len(cat) else '—'}", f"estrenos {anios[0]}–{anios[1]}"]
for nombre, sel in [("géneros", generos), ("idiomas", idiomas), ("países", paises)]:
    if sel:
        filtros_txt.append(f"{nombre}: {', '.join(sel[:3])}{'…' if len(sel) > 3 else ''}")
st.markdown(f"<div class='alcance'>Alcance: <b>{C.fmt(len(cat))}</b> títulos · {' · '.join(filtros_txt)}</div>",
            unsafe_allow_html=True)

if cat.empty:
    st.warning("No hay títulos para la combinación de filtros seleccionada. Amplíe los filtros en la barra lateral.")
    st.stop()

K = C.kpis(cat, gen, pais)
IND = indicadores(cat, gen, pais)
FILTRADO = len(cat) != len(D["cat"])

tabs = st.tabs(["Resumen ejecutivo", "Recomendaciones", "Oportunidades de adquisición", "Composición del catálogo",
                "Mercados", "Finanzas (películas)", "Talento", "Datos y metodología"])

# =========================================================================== 1. RESUMEN
with tabs[0]:
    proposito("Gerente de Contenidos (y Directorio)", "¿Cuál es el estado del catálogo y dónde están las brechas?", "Qué segmentos revisar primero")
    c = st.columns(6)
    c[0].metric("Total de contenidos", C.fmt(K["Total de contenidos"]))
    c[1].metric("Películas", C.fmt(K["Películas"]))
    c[2].metric("Series", C.fmt(K["Series"]))
    c[3].metric("Países", C.fmt(K["Países representados"]))
    c[4].metric("Idiomas", C.fmt(K["Idiomas"]))
    c[5].metric("Géneros", C.fmt(K["Géneros"]))
    c = st.columns(4)
    c[0].metric("Popularidad mediana", C.fmt(K["Popularidad mediana"], 1),
                help="Índice TMDB. Se usa la mediana porque la distribución es muy asimétrica.")
    c[1].metric("Calificación promedio", f"{C.fmt(K['Calificación promedio'], 2)} / 10" if pd.notna(K["Calificación promedio"]) else "N/A",
                help="Solo títulos con ≥ 10 votos (valoración confiable).")
    c[2].metric("ROI mediano (películas)", f"{C.fmt(K['ROI mediano'], 2)}x" if pd.notna(K["ROI mediano"]) else "N/A",
                help="Ingresos / presupuesto. Solo películas con datos financieros válidos.")
    c[3].metric("Películas rentables", C.pct(K["% películas rentables"]) if pd.notna(K["% películas rentables"]) else "N/A",
                help="Películas con ROI ≥ 1 (recuperan su presupuesto).")

    st.markdown("#### Lo que el catálogo dice hoy")
    tg = C.tabla_generos(gen)
    if not tg.empty:
        best = tg.sort_values("brecha_pp", ascending=False).iloc[0]
        worst = tg.sort_values("brecha_pp").iloc[0]
        st.markdown(f"<div class='hallazgo'><b>{best.genero}</b> ({best.tipo.lower()}s) aparece en el 20% más popular "
                    f"<b>{C.fmt(best.brecha_pp, 1)} pp</b> más de lo que pesa en el catálogo → <b>candidato a adquirir</b>.</div>",
                    unsafe_allow_html=True)
        st.markdown(f"<div class='hallazgo'><b>{worst.genero}</b> ({worst.tipo.lower()}s) está sobre-ofertado: "
                    f"{C.fmt(abs(worst.brecha_pp), 1)} pp menos presencia entre los títulos más populares que en el catálogo.</div>",
                    unsafe_allow_html=True)
    tp = C.tabla_paises(pais, 50)
    if not tp.empty:
        lat = tp[tp["pais"].isin(C.LATAM)].sort_values("percentil_pop", ascending=False)
        if len(lat):
            r = lat.iloc[0]
            st.markdown(f"<div class='hallazgo'><b>{r.pais}</b> tiene popularidad relativa <b>{C.fmt(r.percentil_pop * 100)}</b> (típico = 50) "
                        f"con solo {C.pct(r.share, 1)} de las producciones → mercado latinoamericano sub-representado.</div>",
                        unsafe_allow_html=True)
    if K["Películas con datos financieros"] > 20:
        st.markdown(f"<div class='hallazgo'>El ROI mediano de las películas es <b>{C.fmt(K['ROI mediano'], 2)}x</b> y "
                    f"<b>{C.pct(1 - K['% películas rentables'])}</b> no recupera su inversión → priorizar géneros de retorno estable.</div>",
                    unsafe_allow_html=True)

    col1, col2 = st.columns([1.15, 1])
    with col1:
        plot(C.fig_brecha_generos(gen), "res_brecha", ancho=58)
    with col2:
        plot(C.fig_mapa(pais), "res_mapa", ancho=58)

# =========================================================================== 2. RECOMENDACIONES
with tabs[1]:
    proposito("Gerente de Contenidos y Adquisición", "¿Qué hacer con la evidencia y cómo se medirá?",
              "Qué priorizar en las próximas adquisiciones y qué indicador seguir")
    st.warning("**Impacto esperado, no medido.** La evidencia de cada recomendación sí está medida en los datos; el impacto es una "
               "proyección. Para seguirlo, cada recomendación tiene un **indicador con su línea base** (catálogo completo de hoy). "
               "No se proyecta retención ni engagement: no hay datos de usuarios, suscripciones ni reproducciones.")
    if FILTRADO:
        st.caption("La evidencia se recalcula con los filtros de la barra lateral; la línea base siempre corresponde al catálogo completo.")

    TG = C.tabla_generos(gen, min_n=1)
    TPa = C.tabla_paises(pais, 50)
    fg = gen[(gen["fin_valido"] == True) & (gen["tipo"] == "Película")]  # noqa: E712
    fin = cat[cat["fin_valido"] == True]  # noqa: E712

    def g(tipo, genero, col):
        r = TG[(TG["tipo"] == tipo) & (TG["genero"] == genero)]
        return r[col].iloc[0] if len(r) else NAN

    def roi(genero):
        s = fg.loc[fg["genero"] == genero, "roi"]
        return s.median() if len(s) >= 10 else NAN

    def p(pais_, col):
        r = TPa[TPa["pais"] == pais_]
        return r[col].iloc[0] if len(r) else NAN

    pop = lambda x: C.fmt(x * 100)  # noqa: E731
    pp = lambda x: f"{'+' if x > 0 else ''}{C.fmt(x, 1)} pp"  # noqa: E731
    veces = lambda x: f"{C.fmt(x, 1)}x"  # noqa: E731
    porc = lambda x: C.pct(x, 1)  # noqa: E731
    nota = lambda x: C.fmt(x, 2)  # noqa: E731

    # 1 · Animación y Familiar
    af_uids = set(gen.loc[gen["genero"].isin(["Animación", "Familiar"]), "uid"])
    recomendacion(
        1, "Aumentar la adquisición de Animación y Familiar",
        "Combinan **alta popularidad, alta calificación, poca oferta y el mejor retorno** en taquilla: están en el cuadrante "
        "superior derecho de la matriz de oportunidad con burbujas pequeñas.",
        [("Popularidad relativa · Animación (películas)", _v(g("Película", "Animación", "percentil_pop"), pop), "50 = título típico de su tipo."),
         ("Oferta · Animación (películas)", _v(g("Película", "Animación", "share_catalogo"), porc), "% de las asignaciones de género en películas."),
         ("Calificación · Animación (películas)", _v(g("Película", "Animación", "nota_media"), nota), "Promedio de títulos con ≥ 10 votos."),
         ("ROI mediano · Animación / Familiar", f"{_v(roi('Animación'), veces)} / {_v(roi('Familiar'), veces)}", "Ingresos ÷ presupuesto de la película típica.")],
        ("% del catálogo en Animación o Familiar", "af", porc),
        "Oportunidades (matriz) · Finanzas (ROI por género)",
        titulos_referencia(cat[cat["uid"].isin(af_uids)]))

    # 2 · Latinoamérica
    lat = TPa[TPa["pais"].isin(C.LATAM)].nlargest(3, "percentil_pop")
    lat_txt = " · ".join(f"{r.pais} {C.fmt(r.percentil_pop * 100)}" for r in lat.itertuples()) or "—"
    esp = cat[cat["idioma"] == "Español"]
    recomendacion(
        2, "Crecer en contenido latinoamericano (español y portugués)",
        f"El contenido en español es **más popular que el típico pero tiene poca oferta**, y los mercados latinoamericanos más "
        f"populares suman solo **{_v(lat['share'].sum() if len(lat) else NAN, porc)}** de las producciones. Telenovela es la mayor "
        f"brecha en series. Es coherente con la visión de StreamView: ser líder en Latinoamérica.",
        [("Oferta en español", _v(len(esp) / len(cat), porc), "% de los títulos del alcance actual."),
         ("Popularidad relativa · español", _v(esp["pct_popularidad"].median() if len(esp) else NAN, pop), "50 = título típico."),
         ("Brecha · Telenovela (series)", _v(g("Serie", "Telenovela", "brecha_pp"), pp), "% en el 20% más popular − % en el catálogo."),
         ("Popularidad relativa · mercados LatAm", lat_txt, "Países latinoamericanos con ≥ 50 títulos, los 3 más populares.")],
        ("% del catálogo en español/portugués", "latam", porc),
        "Mercados (ranking de países) · Composición (idiomas)",
        titulos_referencia(cat[cat["idioma"].isin(LAT_IDIOMAS) | cat["pais_principal"].isin(C.LATAM)]))

    # 3 · Menos Drama
    recomendacion(
        3, "Reducir la adquisición incremental de Drama y reasignar ese presupuesto",
        "Drama es el género **más ofertado** pero pesa menos entre los títulos más populares que en el catálogo, y su retorno es "
        "bajo. Dejar de crecer en Drama **financia las recomendaciones 1 y 2 sin aumentar el gasto total**.",
        [("Peso de Drama en el catálogo", _v(gen["genero"].eq("Drama").mean() if len(gen) else NAN, porc), "% de las asignaciones de género."),
         ("Brecha · Drama (películas)", _v(g("Película", "Drama", "brecha_pp"), pp), "Negativo = sobre-ofertado."),
         ("Brecha · Drama (series)", _v(g("Serie", "Drama", "brecha_pp"), pp), "Negativo = sobre-ofertado."),
         ("ROI mediano · Drama", _v(roi("Drama"), veces), "Ingresos ÷ presupuesto de la película típica.")],
        ("Brecha de Drama en películas", "drama", pp),
        "Resumen (brecha oferta vs demanda) · Finanzas (ROI por género)")

    # 4 · Asia de calidad
    recomendacion(
        4, "Mantener un pipeline asiático de calidad (Japón y Corea del Sur)",
        "Japón y Corea del Sur tienen la **mejor calificación media entre los 15 mayores productores**: sostienen la calidad del catálogo.",
        [("Calificación · Japón", _v(p("Japón", "nota_media"), nota), "Promedio de títulos con ≥ 10 votos."),
         ("Calificación · Corea del Sur", _v(p("Corea del Sur", "nota_media"), nota), "Promedio de títulos con ≥ 10 votos."),
         ("Calificación · catálogo", _v(cat["nota"].mean(), nota), "Promedio del alcance actual, para comparar.")],
        ("Calificación media Japón + Corea del Sur", "asia", nota),
        "Mercados (países por calificación)",
        titulos_referencia(cat[cat["pais_principal"].isin(ASIA)]))

    # 5 · Portafolio balanceado
    rent = lambda s: (s["roi"] >= 1).mean() if len(s) else NAN  # noqa: E731
    j = C.tabla_joyas(cat, 10).rename(columns={"title": "Título", "release_year": "Año", "genero_principal": "Género",
                                               "pais_principal": "País", "budget": "Presupuesto (USD)", "revenue": "Ingresos (USD)",
                                               "roi": "ROI", "nota": "Calificación"})
    recomendacion(
        5, "Portafolio de películas balanceado: blockbusters + apuestas de bajo presupuesto",
        "Los blockbusters dan **estabilidad** (la mayoría recupera su inversión); las películas de bajo presupuesto son más "
        "riesgosas, pero ahí están las **joyas de altísimo retorno**. Combinar ambos controla el riesgo sin renunciar al retorno.",
        [("Rentables · blockbusters (> USD 60 M)", _v(rent(fin[fin["budget"] > 60e6]), C.pct), "% de películas con ROI ≥ 1."),
         ("Rentables · bajo presupuesto (< USD 5 M)", _v(rent(fin[fin["budget"] < 5e6]), C.pct), "% de películas con ROI ≥ 1."),
         ("No recuperan su inversión", _v(1 - rent(fin) if len(fin) else NAN, C.pct), "% de películas con ROI < 1.")],
        ("% de películas con ROI ≥ 1", "rent", C.pct),
        "Finanzas (presupuesto vs ingresos, rentabilidad por tramo)",
        j, {"Presupuesto (USD)": st.column_config.NumberColumn(format="$%,.0f"),
            "Ingresos (USD)": st.column_config.NumberColumn(format="$%,.0f"),
            "ROI": st.column_config.NumberColumn(format="%.1fx"),
            "Calificación": st.column_config.NumberColumn(format="%.2f")})

    st.markdown("#### Tablero de seguimiento")
    st.caption("Cómo se medirá el impacto de cada recomendación en las próximas actualizaciones del catálogo.")
    B = linea_base()
    filas = [("1. Animación y Familiar", "% del catálogo en Animación o Familiar", "af", porc, "Subir"),
             ("2. Latinoamérica", "% del catálogo en español/portugués", "latam", porc, "Subir"),
             ("3. Menos Drama", "Brecha de Drama en películas (pp)", "drama", pp, "Acercarse a 0"),
             ("4. Asia de calidad", "Calificación media Japón + Corea del Sur", "asia", nota, "Mantener o subir"),
             ("5. Portafolio balanceado", "% de películas con ROI ≥ 1", "rent", C.pct, "Subir")]
    seg = pd.DataFrame([{"Recomendación": r, "Indicador": i, "Línea base (catálogo completo)": _v(B[k], f),
                         **({"Con filtros actuales": _v(IND[k], f)} if FILTRADO else {}), "Dirección esperada": d}
                        for r, i, k, f, d in filas])
    st.dataframe(seg, hide_index=True, width="stretch")

# =========================================================================== 3. OPORTUNIDADES
with tabs[2]:
    proposito("Gerente de Contenidos y Adquisición", "¿Qué géneros son populares y bien evaluados, con poca oferta?", "Qué géneros y títulos adquirir o renovar")
    st.markdown("Use la **matriz de oportunidad** para ubicar géneros populares *y* bien evaluados. "
                "**Haga clic en una burbuja** para ver los títulos que la componen.")
    tipo_m = st.radio("Tipo", [t for t in ["Película", "Serie"] if t in cat["tipo"].unique()], horizontal=True, key="tipo_matriz")
    ev = plot(C.fig_matriz_oportunidad(gen, tipo_m), "matriz", select=True)
    sel_gen = None
    if ev and ev.selection and ev.selection.get("points"):
        sel_gen = ev.selection["points"][0].get("text")
    if sel_gen:
        st.markdown(f"##### Detalle: {sel_gen} · {tipo_m.lower()}s")
        det = gen[(gen["genero"] == sel_gen) & (gen["tipo"] == tipo_m)]
        c1, c2, c3 = st.columns(3)
        c1.metric("Títulos", C.fmt(len(det)))
        c2.metric("Popularidad mediana", C.fmt(det["popularity"].median(), 1))
        c3.metric("Calificación media", C.fmt(det["nota"].mean(), 2))
        top = det.sort_values("popularity", ascending=False).head(15)[
            ["title", "release_year", "popularity", "nota", "vote_count", "idioma", "pais_principal"]]
        st.dataframe(top.rename(columns={"title": "Título", "release_year": "Año", "popularity": "Popularidad",
                                         "nota": "Calificación", "vote_count": "Votos", "idioma": "Idioma",
                                         "pais_principal": "País"}),
                     hide_index=True, width="stretch",
                     column_config={"Popularidad": st.column_config.NumberColumn(format="%.1f"),
                                    "Calificación": st.column_config.NumberColumn(format="%.2f")})
    else:
        st.info("Seleccione una burbuja para ver el detalle del género.")

    c1, c2 = st.columns(2)
    with c1:
        plot(C.fig_pop_vs_nota(cat), "popnota", ancho=58)
    with c2:
        plot(C.fig_tendencia_nota(cat), "tend", ancho=58)
    c1, c2 = st.columns(2)
    with c1:
        plot(C.fig_dist_popularidad(cat), "distpop", ancho=58)
    with c2:
        plot(C.fig_dist_nota(cat), "distnota", ancho=58)

    st.markdown("#### Rankings")
    metr = st.segmented_control("Ordenar por", ["Popularidad", "Mejor evaluados", "Más votados"], default="Popularidad",
                                key="rank_metric")
    por = {"Popularidad": "popularity", "Mejor evaluados": "nota_ponderada", "Más votados": "vote_count"}[metr or "Popularidad"]
    plot(C.fig_top_titulos(cat, por, 10), "rank")

# =========================================================================== 4. CATÁLOGO
with tabs[3]:
    proposito("Gerente de Contenidos", "¿Cómo está compuesto el catálogo y cómo cambia su mix?", "Qué géneros/idiomas reforzar o dejar de crecer")
    c1, c2 = st.columns([1.3, 1])
    with c1:
        plot(C.fig_treemap_generos(gen), "tree", ancho=58)
    with c2:
        foco = st.selectbox("Idioma a destacar", cat["idioma"].value_counts().head(10).index.tolist(),
                            index=(cat["idioma"].value_counts().head(10).index.tolist().index("Español")
                                   if "Español" in cat["idioma"].value_counts().head(10).index else 0))
        plot(C.fig_idiomas(cat, foco=foco), "idiomas", ancho=58)
    tipo_a = st.radio("Evolución del mix de géneros para", [t for t in ["Película", "Serie"] if t in cat["tipo"].unique()],
                      horizontal=True, key="tipo_area")
    c1, c2 = st.columns(2)
    with c1:
        plot(C.fig_mix_generos_tiempo(cat, tipo_a), "mix", ancho=58)
    with c2:
        met = st.segmented_control("Métrica del mapa de calor", ["Popularidad", "Calificación"], default="Popularidad", key="hm")
        plot(C.fig_heatmap_genero_anio(gen, tipo_a, "nota" if met == "Calificación" else "pct_popularidad"), "heat", ancho=58)
    plot(C.fig_incorporaciones_mes(cat), "meses")

# =========================================================================== 5. MERCADOS
with tabs[4]:
    proposito("Gerente de Contenidos (y Marketing)", "¿Qué países e idiomas tienen demanda alta y poca oferta?", "En qué mercados buscar licencias")
    met = st.segmented_control("Mapa coloreado por", ["Cantidad de títulos", "Popularidad relativa"],
                               default="Cantidad de títulos", key="mapa_m")
    plot(C.fig_mapa(pais, "titulos" if met != "Popularidad relativa" else "pop"), "mapa2")
    c1, c2 = st.columns([1.2, 1])
    with c1:
        plot(C.fig_mercados(pais), "merc", ancho=58)
    with c2:
        plot(C.fig_paises_nota(pais), "pnota", ancho=58)
    with st.expander("Tabla de mercados (países con ≥ 50 títulos)"):
        tp = C.tabla_paises(pais, 50).drop(columns=["iso3"])
        st.dataframe(tp.rename(columns={"pais": "País", "titulos": "Títulos", "percentil_pop": "Popularidad relativa (0-1)",
                                        "nota_media": "Calificación media", "peliculas": "Películas", "share": "% catálogo"}),
                     hide_index=True, width="stretch",
                     column_config={"Popularidad relativa (0-1)": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1),
                                    "% catálogo": st.column_config.NumberColumn(format="%.3f"),
                                    "Calificación media": st.column_config.NumberColumn(format="%.2f")})

# =========================================================================== 6. FINANZAS
with tabs[5]:
    proposito("Gerente de Contenidos (y Gerencia General)", "¿Qué géneros y niveles de presupuesto recuperan la inversión?", "Cuánto riesgo financiero asumir por adquisición")
    if "Película" not in cat["tipo"].unique():
        st.info("Los indicadores financieros solo existen para películas (regla de negocio 3). Incluya 'Película' en el filtro de tipo.")
    else:
        st.caption("Solo películas con presupuesto ≥ USD 100 mil e ingresos > 0. Las series no tienen presupuesto ni ingresos (reglas 3, 6 y 9).")
        c = st.columns(5)
        c[0].metric("Películas con datos", C.fmt(K["Películas con datos financieros"]))
        c[1].metric("Presupuesto total (US$ mil M)", C.fmt(K["Presupuesto total"] / 1e9, 1), help="Miles de millones de dólares")
        c[2].metric("Ingresos totales (US$ mil M)", C.fmt(K["Ingresos totales"] / 1e9, 1), help="Miles de millones de dólares")
        c[3].metric("ROI mediano", f"{C.fmt(K['ROI mediano'], 2)}x")
        c[4].metric("% rentables", C.pct(K["% películas rentables"]))
        plot(C.fig_presupuesto_ingresos(cat), "budrev")
        c1, c2 = st.columns([1.2, 1])
        with c1:
            plot(C.fig_roi_genero(gen), "roig", ancho=58)
        with c2:
            plot(C.fig_rentabilidad_tramo(cat), "tramo", ancho=50)
        st.markdown("#### Éxitos con presupuesto reducido (< USD 5 M, ROI ≥ 5x, ingresos ≥ USD 10 M)")
        j = C.tabla_joyas(cat, 15)
        st.dataframe(j.rename(columns={"title": "Título", "release_year": "Año", "genero_principal": "Género",
                                       "pais_principal": "País", "budget": "Presupuesto (USD)", "revenue": "Ingresos (USD)",
                                       "roi": "ROI", "nota": "Calificación"}),
                     hide_index=True, width="stretch",
                     column_config={"Presupuesto (USD)": st.column_config.NumberColumn(format="$%,.0f"),
                                    "Ingresos (USD)": st.column_config.NumberColumn(format="$%,.0f"),
                                    "ROI": st.column_config.NumberColumn(format="%.1fx"),
                                    "Calificación": st.column_config.NumberColumn(format="%.2f")})

# =========================================================================== 7. TALENTO
with tabs[6]:
    proposito("Gerente de Contenidos", "¿Qué directores y talentos aparecen más en el catálogo?", "Con qué estudios/talentos negociar paquetes")
    c1, c2 = st.columns(2)
    with c1:
        plot(C.fig_top_personas(pers, "Director"), "dir", ancho=58)
    with c2:
        plot(C.fig_top_personas(pers, "Actor/Actriz"), "act", ancho=58)
    st.caption("Actores/actrices: se consideran los 5 primeros créditos de cada título. Series: 69% sin director informado.")

# =========================================================================== 8. DATOS
with tabs[7]:
    proposito("Equipo Data & Analytics y auditoría", "¿Qué tan confiables son los datos y qué se decidió?", "Qué conclusiones son sólidas y cuáles tienen límites")
    raw_m = pd.read_csv(ROOT / "data" / "raw" / "movies_clean.csv")
    raw_t = pd.read_csv(ROOT / "data" / "raw" / "tvshows_clean.csv")
    plot(C.fig_calidad(raw_m, raw_t), "calidad")
    st.markdown("""
**Decisiones de preparación (documentadas en `notebooks/01_calidad_y_preparacion.ipynb`)**

| Problema detectado | Decisión |
|---|---|
| `rating` es idéntica a `vote_average` (no es clasificación etaria) | Se excluye; los KPIs de clasificación etaria **no pueden calcularse** con estos datos |
| `duration` vacía (películas) o constante "1 Seasons" (series) | Se excluye del análisis |
| Títulos con < 10 votos tienen `vote_average` poco confiable (0 = sin votos) | Calificación solo con ≥ 10 votos; ranking con calificación ponderada bayesiana |
| `popularity` muy asimétrica (media 2–3x la mediana) | Mediana, percentiles dentro de cada tipo y escala logarítmica |
| Exactamente 1.000 títulos por año y tipo (muestra estratificada) | Se analiza la **composición** en el tiempo, no el volumen |
| `show_id` se repite entre películas y series (397 casos) | Clave única `uid` = tipo + id |
| Presupuestos < USD 100 mil (errores de registro) y valores 0 | Excluidos de indicadores financieros (regla 6) |
| Géneros con taxonomías distintas en películas y series | Taxonomía armonizada en español (regla 2) |
""")
    st.info("**Alcance:** la solución usa datos de catálogo (TMDB). La popularidad es un índice relativo de interés, "
            "no reproducciones. Retención, engagement o comportamiento de usuarios **no se pueden analizar** sin datos "
            "propios de usuarios, suscripciones o reproducciones, que no están disponibles.")
    st.markdown("**Descargar datos del alcance actual**")
    st.download_button("Descargar catálogo filtrado (CSV)", cat.to_csv(index=False).encode("utf-8-sig"),
                       file_name="streamview_catalogo_filtrado.csv", mime="text/csv")
