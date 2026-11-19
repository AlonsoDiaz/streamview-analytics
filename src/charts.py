"""
charts.py
---------
Biblioteca de visualizaciones de StreamView Analytics.

Cada función recibe datos (ya filtrados) y devuelve una figura Plotly con:
  * título-hallazgo calculado desde los datos (siempre verdadero, también al filtrar),
  * subtítulo con período y alcance (regla de negocio 7),
  * hover con el detalle (interacción) y etiquetas directas selectivas.

La justificación de cada forma está en el docstring de la función
(y se resume en el informe, tabla "Justificación de representaciones").
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:  # import relativo/absoluto (src como paquete o como carpeta en sys.path)
    from . import theme as T
except ImportError:
    import theme as T

TIPOS = ["Película", "Serie"]
GENRE_COLORS = ["#1baf7a", "#eda100", "#e87ba4", "#6250d6", "#e34948"]  # validado CVD (orden fijo)
OTROS = "#c3c2b7"


# --------------------------------------------------------------------------- utilidades
def fmt(x, dec=0):
    """Número con formato chileno: 12.345,6"""
    if pd.isna(x):
        return "–"
    s = f"{x:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x, dec=0):
    return f"{fmt(100 * x, dec)}%"


def money(x):
    if pd.isna(x):
        return "–"
    for div, suf in [(1e9, " mil M"), (1e6, " M")]:
        if abs(x) >= div:
            return f"USD {fmt(x / div, 1)}{suf}"
    return f"USD {fmt(x)}"


def periodo(df: pd.DataFrame) -> str:
    if df.empty:
        return "sin datos"
    a, b = int(df["release_year"].min()), int(df["release_year"].max())
    return f"{a}" if a == b else f"{a}–{b}"


def tipos_txt(df: pd.DataFrame) -> str:
    t = sorted(df["tipo"].unique())
    return "películas y series" if len(t) == 2 else ("películas" if t == ["Película"] else "series")


def _etiquetar_burbujas(fig, x, y, textos, diam, xr, yr, w=1050, h=380, prioridad=None):
    """Etiquetas con línea guía sin superposición (greedy en píxeles aproximados).
    Primero se ubican las burbujas prioritarias/grandes; cada etiqueta prueba 16 posiciones
    alrededor de su burbuja y elige la primera que no choca con otras etiquetas ni burbujas."""
    x, y, diam = np.asarray(x, float), np.asarray(y, float), np.asarray(diam, float)
    px_ = (x - xr[0]) / (xr[1] - xr[0]) * w
    py_ = (y - yr[0]) / (yr[1] - yr[0]) * h
    circles = list(zip(px_, py_, diam / 2))
    orden = np.argsort(-(np.asarray(prioridad, float) if prioridad is not None else diam))
    placed = []

    def choca(cx, cy, tw, th, own):
        x0, x1, y0, y1 = cx - tw / 2, cx + tw / 2, cy - th / 2, cy + th / 2
        if x0 < 0 or x1 > w or y0 < 0 or y1 > h:
            return True
        for (a0, a1, b0, b1) in placed:
            if x0 < a1 and x1 > a0 and y0 < b1 and y1 > b0:
                return True
        for j, (ccx, ccy, r) in enumerate(circles):
            if j == own:
                continue
            nx, ny = min(max(ccx, x0), x1), min(max(ccy, y0), y1)
            if (nx - ccx) ** 2 + (ny - ccy) ** 2 < (r + 2) ** 2:
                return True
        return False

    angs = np.deg2rad([90, 270, 0, 180, 45, 135, 315, 225])
    for i in orden:
        tw, th = 6.6 * len(str(textos[i])) + 6, 16
        r = circles[i][2]
        best = None
        for extra in (6, 26, 50):
            for a in angs:
                dist = r + extra + (tw / 2 if abs(np.cos(a)) > 0.5 else th / 2)
                cx, cy = px_[i] + dist * np.cos(a), py_[i] + dist * np.sin(a)
                if not choca(cx, cy, tw, th, i):
                    best = (cx, cy)
                    break
            if best:
                break
        if best is None:
            best = (px_[i], py_[i] + r + 12)
        cx, cy = best
        placed.append((cx - tw / 2, cx + tw / 2, cy - th / 2, cy + th / 2))
        lejos = np.hypot(cx - px_[i], cy - py_[i]) > r + tw / 2 + 14
        fig.add_annotation(x=x[i], y=y[i], text=str(textos[i]), ax=cx - px_[i], ay=-(cy - py_[i]),
                           showarrow=True, arrowhead=0, arrowwidth=0.8, standoff=r + 1,
                           arrowcolor=T.MUTED if lejos else T.AXIS,
                           font=dict(size=11, color=T.INK_2), xanchor="center", yanchor="middle")


def vacio(msg="No hay datos para los filtros seleccionados") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
                       font=dict(size=15, color=T.MUTED))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(height=300)
    return fig


# --------------------------------------------------------------------------- KPIs
def kpis(cat: pd.DataFrame, gen: pd.DataFrame, pais: pd.DataFrame) -> dict:
    fin = cat[cat["fin_valido"] == True]  # noqa: E712
    return {
        "Total de contenidos": len(cat),
        "Películas": int((cat["tipo"] == "Película").sum()),
        "Series": int((cat["tipo"] == "Serie").sum()),
        "Países representados": pais["pais"].nunique(),
        "Idiomas": cat["idioma"].nunique(),
        "Géneros": gen["genero"].nunique(),
        "Popularidad mediana": cat["popularity"].median(),
        "Calificación promedio": cat["nota"].mean(),
        "Títulos con valoración válida": cat["nota"].notna().mean() if len(cat) else np.nan,
        "Películas con datos financieros": len(fin),
        "ROI mediano": fin["roi"].median() if len(fin) else np.nan,
        "Ingresos totales": fin["revenue"].sum(),
        "Presupuesto total": fin["budget"].sum(),
        "% películas rentables": (fin["roi"] >= 1).mean() if len(fin) else np.nan,
    }


# --------------------------------------------------------------------------- CATÁLOGO
def fig_treemap_generos(gen: pd.DataFrame) -> go.Figure:
    """Treemap: composición jerárquica parte-todo (tipo -> género). El área codifica cantidad,
    lo que permite ver de un vistazo qué géneros dominan sin leer números."""
    if gen.empty:
        return vacio()
    g = gen.groupby(["tipo", "genero"]).size().reset_index(name="n")
    top = gen.groupby("genero").size().sort_values(ascending=False)
    share = top.iloc[0] / top.sum()
    fig = px.treemap(g, path=[px.Constant("Catálogo"), "tipo", "genero"], values="n", color="tipo",
                     color_discrete_map={**T.COLOR_TIPO, "(?)": T.CONTEXTO})
    fig.update_traces(marker=dict(cornerradius=4, line=dict(width=2, color=T.SURFACE)),
                      texttemplate="%{label}<br>%{value:,.0f}", textfont=dict(color="white"),
                      hovertemplate="<b>%{label}</b><br>%{value:,.0f} títulos<br>%{percentParent:.1%} de %{parent}<extra></extra>",
                      root_color=T.SURFACE, tiling=dict(pad=2))
    fig.update_layout(title=T.titulo(f"{top.index[0]} domina el catálogo: {pct(share)} de las asignaciones de género",
                                     f"Títulos por tipo y género · {periodo(gen)} · un título puede tener varios géneros"),
                      margin=dict(l=10, r=10, t=90, b=10), height=520, separators=",.")
    return fig


def fig_idiomas(cat: pd.DataFrame, foco: str = "Español", n: int = 10) -> go.Figure:
    """Small multiples (2 barras horizontales) en vez de eje dual: oferta (participación) vs
    demanda relativa (percentil mediano de popularidad). Se destaca un idioma foco."""
    if cat.empty:
        return vacio()
    agg = cat.groupby("idioma").agg(n=("uid", "size"), pctl=("pct_popularidad", "median"))
    agg["share"] = agg["n"] / agg["n"].sum()
    agg = agg.sort_values("n", ascending=False).head(n).iloc[::-1]
    col = [T.FOCO if i == foco else T.CONTEXTO for i in agg.index]
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.04,
                        subplot_titles=("Participación en el catálogo", "Popularidad relativa (50 = título típico)"))
    fig.add_bar(y=agg.index, x=agg["share"], orientation="h", marker_color=col, row=1, col=1,
                text=[pct(v, 1) for v in agg["share"]], textposition="outside",
                hovertemplate="<b>%{y}</b><br>%{x:.1%} del catálogo<extra></extra>")
    fig.add_bar(y=agg.index, x=agg["pctl"] * 100, orientation="h", marker_color=col, row=1, col=2,
                text=[fmt(v * 100) for v in agg["pctl"]], textposition="outside",
                hovertemplate="<b>%{y}</b><br>Popularidad relativa: %{x:.0f} / 100<extra></extra>")
    fig.add_vline(x=50, line=dict(color=T.MUTED, dash="dot", width=1), row=1, col=2)
    fig.update_xaxes(showticklabels=False, showgrid=False)
    fig.update_xaxes(range=[0, agg["share"].max() * 1.25], row=1, col=1)
    fig.update_xaxes(range=[0, 100], row=1, col=2)
    fig.update_layout(showlegend=False, height=460, separators=",.")
    if foco in agg.index:
        r = agg.loc[foco]
        h = f"El {foco.lower()} tiene solo {pct(r.share, 1)} del catálogo, pero su contenido es más popular que el típico ({fmt(r.pctl * 100)} vs 50)" if r.pctl > 0.5 else f"El {foco.lower()} tiene {pct(r.share, 1)} del catálogo y popularidad relativa {fmt(r.pctl * 100)} (típico = 50)"
    else:
        h = f"{agg.index[-1]} concentra {pct(agg['share'].iloc[-1])} del catálogo"
    fig.update_layout(title=T.titulo(h, f"Top {n} idiomas por cantidad de títulos · {tipos_txt(cat)} · {periodo(cat)} · "
                                        "popularidad relativa 0–100 (50 = título típico de su tipo)"))
    for a in fig.layout.annotations:
        a.font = dict(size=12, color=T.INK_2)
    return fig


def fig_incorporaciones_mes(cat: pd.DataFrame) -> go.Figure:
    """Barras por mes: estacionalidad de incorporación (variable temporal discreta y cíclica).
    Se destacan los 2 meses de mayor actividad."""
    if cat.empty:
        return vacio()
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    m = cat.groupby("mes_incorporacion").size().reindex(range(1, 13), fill_value=0)
    top2 = m.nlargest(2).index
    fig = go.Figure(go.Bar(x=meses, y=m.values, marker_color=[T.FOCO if i in top2 else T.CONTEXTO for i in m.index],
                           text=[fmt(v) for v in m.values], textposition="outside",
                           hovertemplate="%{x}: %{y:,.0f} títulos<extra></extra>"))
    share = m.loc[top2].sum() / m.sum()
    fig.update_layout(title=T.titulo(f"{meses[top2[0]-1]} y {meses[top2[1]-1]} concentran el {pct(share)} de las incorporaciones",
                                     f"Títulos incorporados por mes (date_added) · {tipos_txt(cat)} · {periodo(cat)}"),
                      yaxis_title="Títulos", height=420, separators=",.")
    fig.update_yaxes(showgrid=False, showticklabels=False)
    return fig


def fig_mix_generos_tiempo(cat: pd.DataFrame, tipo: str) -> go.Figure:
    """Áreas apiladas al 100% con solo 3 grupos (género principal de cada título): Drama, Animación y
    Familiar (la oportunidad) y Otros. Cada título cuenta una sola vez, así la lectura es directa:
    'de cada 10 títulos estrenados ese año, X son Drama'. Se usa la composición (no el volumen)
    porque la muestra tiene 1.000 títulos por año."""
    s = cat[cat["tipo"] == tipo]
    if s.empty:
        return vacio()
    grp = s["genero_principal"].map(lambda g: "Drama" if g == "Drama" else
                                    ("Animación y Familiar" if g in ("Animación", "Familiar") else "Otros géneros"))
    t = pd.crosstab(s["release_year"], grp, normalize="index")
    orden = [("Drama", T.CONTEXTO_OSCURO), ("Animación y Familiar", T.COLOR_TIPO[tipo]), ("Otros géneros", "#ebeae5")]
    fig = go.Figure()
    for g, color in orden:
        if g not in t:
            continue
        fig.add_scatter(x=t.index, y=t[g], name=g, mode="lines", stackgroup="one", line=dict(width=1, color=T.SURFACE),
                        fillcolor=color, hovertemplate=f"<b>{g}</b> · %{{x}}<br>%{{y:.0%}} de los títulos del año<extra></extra>")
    acum = 0.0
    for g, _ in orden:  # etiqueta directa dentro de cada banda (al inicio del período)
        if g not in t:
            continue
        v = t[g].iloc[0]
        fig.add_annotation(x=t.index[0], y=acum + v / 2, text=f"<b>{g}</b> {pct(v)}", showarrow=False, xanchor="left",
                           xshift=8, font=dict(size=12, color=T.INK if g == "Otros géneros" else "white"))
        acum += v
    d = t.get("Drama", pd.Series(0, index=t.index)).mean()
    a = t.get("Animación y Familiar", pd.Series(0, index=t.index)).mean()
    dr = t.get("Drama", pd.Series(0, index=t.index))
    d0, d1 = dr.iloc[:3].mean(), dr[dr.index < 2025].iloc[-3:].mean()  # 2025 incompleto
    a_txt = fmt(a * 10, 1 if a * 10 < 1.95 else 0)
    if abs(d1 - d0) >= 0.08:  # cambio visible (≥ 0,8 de cada 10)
        h = (f"De cada 10 {tipo.lower()}s, las de Drama pasan de {fmt(d0 * 10)} a {fmt(d1 * 10)}; "
             f"Animación o Familiar promedian solo {a_txt}")
    else:
        h = f"De cada 10 {tipo.lower()}s, {fmt(d * 10)} son Drama y solo {a_txt} Animación o Familiar, año tras año"
    fig.update_layout(title=T.titulo(h, f"% de títulos por género principal y año de estreno · {tipo.lower()}s · {periodo(s)}"),
                      yaxis=dict(tickformat=".0%", range=[0, 1], title="", fixedrange=True, dtick=0.25),
                      xaxis=dict(title="Año de estreno", range=[t.index.min(), t.index.max()], dtick=3, fixedrange=True),
                      hovermode="x unified", height=440, separators=",.", showlegend=False)
    return fig


# --------------------------------------------------------------------------- OFERTA vs DEMANDA
def tabla_generos(gen: pd.DataFrame, min_n: int = 30) -> pd.DataFrame:
    g = gen.copy()
    g["top20"] = g["pct_popularidad"] >= 0.8
    agg = g.groupby(["tipo", "genero"]).agg(
        titulos=("uid", "size"), popularidad_mediana=("popularity", "median"),
        percentil_pop=("pct_popularidad", "median"), nota_media=("nota", "mean"),
        n_valorados=("nota", "count"), n_top20=("top20", "sum")).reset_index()
    agg["share_catalogo"] = agg["titulos"] / agg.groupby("tipo")["titulos"].transform("sum")
    agg["share_top20"] = agg["n_top20"] / agg.groupby("tipo")["n_top20"].transform("sum")
    agg["brecha_pp"] = (agg["share_top20"] - agg["share_catalogo"]) * 100
    agg["indice_demanda"] = agg["share_top20"] / agg["share_catalogo"]
    return agg[agg["titulos"] >= min_n]


def fig_brecha_generos(gen: pd.DataFrame) -> go.Figure:
    """Barras divergentes (small multiples por tipo): diferencia entre la participación de un
    género en el 20% más popular y su participación en el catálogo. Positivo = la demanda supera
    a la oferta (oportunidad de adquisición, color foco); negativo = sobre-oferta (gris)."""
    t = tabla_generos(gen)
    tipos = [x for x in TIPOS if x in t["tipo"].unique()]
    if not tipos:
        return vacio()
    fig = make_subplots(rows=1, cols=len(tipos), subplot_titles=[f"{x}s" for x in tipos], horizontal_spacing=0.22)
    best = []
    for i, tp in enumerate(tipos, 1):
        d = t[t["tipo"] == tp].sort_values("brecha_pp")
        fig.add_bar(y=d["genero"], x=d["brecha_pp"], orientation="h", row=1, col=i,
                    marker_color=[T.COLOR_TIPO[tp] if v > 0 else T.CONTEXTO for v in d["brecha_pp"]],
                    text=[f"{'+' if v > 0 else ''}{fmt(v, 1)}" for v in d["brecha_pp"]], textposition="outside",
                    customdata=np.c_[d["share_catalogo"] * 100, d["share_top20"] * 100, d["titulos"]],
                    hovertemplate="<b>%{y}</b><br>Catálogo: %{customdata[0]:.1f}%<br>Top 20% popular: %{customdata[1]:.1f}%"
                                  "<br>Brecha: %{x:+.1f} pp<br>%{customdata[2]:,.0f} títulos<extra></extra>")
        fig.add_vline(x=0, line=dict(color=T.AXIS, width=1), row=1, col=i)
        lim = d["brecha_pp"].abs().max() * 1.45
        fig.update_xaxes(range=[-lim, lim], row=1, col=i)
        b = d.iloc[-1]
        best.append(f"{b.genero} ({tp.lower()}s, +{fmt(b.brecha_pp, 1)} pp)")
    worst = t.sort_values("brecha_pp").iloc[0]
    fig.update_layout(
        title=T.titulo(f"Faltan títulos de {' y '.join(best)}; sobran de {worst.genero}",
                       f"Barra a la derecha = el género pesa más entre los títulos populares que en el catálogo (falta oferta) · "
                       f"puntos porcentuales · {periodo(gen)}"),
        showlegend=False, height=560, separators=",.")
    fig.update_xaxes(showgrid=False, showticklabels=False)
    for a in fig.layout.annotations:
        a.font = dict(size=13, color=T.INK)
    return fig


def fig_matriz_oportunidad(gen: pd.DataFrame, tipo: str) -> go.Figure:
    """Gráfico de burbujas en cuadrantes (matriz de oportunidad): X = percentil mediano de
    popularidad, Y = calificación media, tamaño = cantidad de títulos (oferta). Cuadrante
    superior derecho = alta demanda y alta calidad; burbuja pequeña allí = oportunidad."""
    t = tabla_generos(gen)
    d = t[t["tipo"] == tipo].copy()
    if d.empty:
        return vacio()
    x0, y0 = 50, d["nota_media"].median()
    d["x"] = d["percentil_pop"] * 100
    d["oport"] = (d["x"] >= x0) & (d["nota_media"] >= y0)
    col = T.COLOR_TIPO[tipo]
    xr = [min(d["x"].min(), x0) - 6, max(d["x"].max(), x0) + 6]
    span = d["nota_media"].max() - d["nota_media"].min()
    yr = [d["nota_media"].min() - 0.18 * span, d["nota_media"].max() + 0.18 * span]
    D = 48  # diámetro máximo de burbuja (px)
    fig = go.Figure()
    for flag, color, name in [(False, T.CONTEXTO, "Resto de géneros"), (True, col, "Alta popularidad y alta calificación")]:
        s = d[d["oport"] == flag]
        fig.add_scatter(x=s["x"], y=s["nota_media"], mode="markers", name=name, text=s["genero"],
                        marker=dict(size=s["titulos"], sizemode="area", sizeref=2 * d["titulos"].max() / D ** 2,
                                    sizemin=8, color=color, opacity=0.85, line=dict(width=2, color=T.SURFACE)),
                        customdata=np.c_[s["titulos"], s["share_catalogo"] * 100],
                        hovertemplate="<b>%{text}</b><br>Popularidad relativa: %{x:.0f} / 100<br>Calificación media: %{y:.2f}"
                                      "<br>%{customdata[0]:,.0f} títulos (%{customdata[1]:.1f}% del catálogo)<extra></extra>")
    fig.add_vline(x=x0, line=dict(color=T.MUTED, dash="dot", width=1))
    fig.add_hline(y=y0, line=dict(color=T.MUTED, dash="dot", width=1))
    diam = np.maximum(D * np.sqrt(d["titulos"] / d["titulos"].max()), 8)
    _etiquetar_burbujas(fig, d["x"], d["nota_media"], d["genero"].tolist(), diam, xr, yr,
                        prioridad=diam + 1000 * d["oport"])
    for (xx, yy, txt, xa, ya) in [(xr[1], yr[1], "OPORTUNIDAD<br>populares y bien evaluados", "right", "top"),
                                  (xr[0], yr[1], "NICHO DE CALIDAD<br>bien evaluados, menos populares", "left", "top"),
                                  (xr[1], yr[0], "MASIVOS<br>populares, peor evaluados", "right", "bottom"),
                                  (xr[0], yr[0], "REVISAR<br>baja popularidad y calificación", "left", "bottom")]:
        fig.add_annotation(x=xx, y=yy, text=txt, showarrow=False, xanchor=xa, yanchor=ya,
                           font=dict(size=10, color=T.MUTED), align=xa)
    ops = d[d["oport"]].copy()
    # orden por distancia combinada a ambas medianas (normalizada por el rango de cada eje)
    ops["score"] = (ops["x"] - x0) / (xr[1] - xr[0]) + (ops["nota_media"] - y0) / (yr[1] - yr[0])
    ops = ops.sort_values("score", ascending=False)
    h = (f"{tipo}s: {', '.join(ops['genero'].head(3))} combinan alta popularidad y calificación"
         if len(ops) else f"{tipo}s: ningún género supera ambas medianas")
    fig.update_layout(title=T.titulo(h, f"Por género · {periodo(gen)} · calificación con ≥ 10 votos · tamaño = n° de títulos · líneas = medianas"),
                      xaxis=dict(title="Popularidad relativa (0–100; 50 = título típico)", range=xr),
                      yaxis=dict(title="Calificación media (0–10)", range=yr),
                      height=560, separators=",.", legend=dict(itemsizing="constant"))
    return fig


def fig_heatmap_genero_anio(gen: pd.DataFrame, tipo: str, metrica: str = "pct_popularidad") -> go.Figure:
    """Mapa de calor (secuencial de un tono): género × año. Permite detectar tendencias de
    muchas series a la vez sin el 'espagueti' de 15 líneas superpuestas."""
    g = gen[gen["tipo"] == tipo]
    if g.empty:
        return vacio()
    top = g["genero"].value_counts().head(12).index
    g = g[g["genero"].isin(top)]
    if metrica == "nota":
        g = g[g["release_year"] < 2025]
        z = g.groupby(["genero", "release_year"])["nota"].mean().unstack()
        label, fmt_ = "Calificación media", ".2f"
    else:
        z = g.groupby(["genero", "release_year"])["pct_popularidad"].median().unstack() * 100
        label, fmt_ = "Popularidad relativa (0–100)", ".0f"
    z = z.loc[z.mean(axis=1).sort_values().index]
    fig = go.Figure(go.Heatmap(z=z.values, x=z.columns, y=z.index, colorscale=T.SEQ_BLUE, xgap=2, ygap=2,
                               colorbar=dict(title=dict(text=label, side="right"), thickness=12, outlinewidth=0),
                               hovertemplate=f"<b>%{{y}}</b> · %{{x}}<br>{label}: %{{z:{fmt_}}}<extra></extra>"))
    best = z.mean(axis=1).idxmax()
    fig.update_layout(title=T.titulo(f"{tipo}s: {best} se mantiene arriba en {label.lower()} año tras año",
                                     f"Top 12 géneros · {periodo(g)} · {'2025 excluido (solo ~8% con votos suficientes)' if metrica == 'nota' else '50 = título típico · 2025 bajo: estrenos recientes aún acumulan popularidad'}"),
                      xaxis=dict(title="Año de estreno", dtick=1, showgrid=False, showline=False),
                      yaxis=dict(showgrid=False), height=500, separators=",.")
    return fig


# --------------------------------------------------------------------------- POPULARIDAD Y VALORACIÓN
def fig_dist_popularidad(cat: pd.DataFrame) -> go.Figure:
    """Box plot horizontal en escala log: la popularidad es muy asimétrica (pocos títulos
    'virales'); la escala log y la mediana evitan que los extremos oculten la distribución."""
    if cat.empty:
        return vacio()
    fig = go.Figure()
    meds = {}
    for tp in TIPOS:
        s = cat.loc[cat["tipo"] == tp, "popularity"]
        if s.empty:
            continue
        meds[tp] = s.median()
        fig.add_box(x=s, name=tp, orientation="h", marker=dict(color=T.COLOR_TIPO[tp], size=4, opacity=0.35),
                    line=dict(color=T.COLOR_TIPO[tp], width=2), fillcolor=T.TINTE_TIPO[tp], boxpoints="outliers",
                    hovertemplate=f"<b>{tp}</b><br>Popularidad: %{{x:.1f}}<extra></extra>")
    h = "Distribución de popularidad"
    if len(meds) == 2:
        h = f"Las series tienen una popularidad mediana {fmt(meds['Serie'] / meds['Película'], 1)} veces mayor que las películas"
    fig.update_layout(title=T.titulo(h, f"Índice de popularidad TMDB (escala log) · {periodo(cat)} · índice relativo, no son reproducciones (regla 5)"),
                      xaxis=dict(type="log", title="Popularidad (escala logarítmica)"), showlegend=False,
                      height=380, separators=",.")
    return fig


def fig_dist_nota(cat: pd.DataFrame) -> go.Figure:
    """Histogramas superpuestos con transparencia (misma escala 0–10): forma de la distribución de
    la calificación por tipo, solo con valoraciones confiables (≥ 10 votos)."""
    v = cat[cat["nota"].notna()]
    if v.empty:
        return vacio()
    fig = go.Figure()
    means = {}
    for tp in TIPOS:
        s = v.loc[v["tipo"] == tp, "nota"]
        if s.empty:
            continue
        means[tp] = s.mean()
        fig.add_histogram(x=s, name=f"{tp} (promedio {fmt(s.mean(), 2)})", histnorm="percent", xbins=dict(start=0, end=10, size=0.25),
                          marker=dict(color=T.COLOR_TIPO[tp], line=dict(width=0), cornerradius=2),
                          hovertemplate="Nota %{x}<br>%{y:.1f}% de los títulos<extra></extra>")
        fig.add_vline(x=s.mean(), line=dict(color=T.COLOR_TIPO[tp], dash="dash", width=2))
    h = "Distribución de la calificación"
    if len(means) == 2:
        h = f"Las series están mejor evaluadas: {fmt(means['Serie'], 2)} vs {fmt(means['Película'], 2)} de las películas"
    fig.update_layout(barmode="group", bargap=0.15, bargroupgap=0.05, title=T.titulo(h, f"Calificación promedio de usuarios (0–10) · títulos con ≥ 10 votos · {periodo(cat)}"),
                      xaxis=dict(title="Calificación (0–10)", range=[1, 10]), yaxis_title="% de títulos",
                      height=400, separators=",.")
    return fig


def fig_pop_vs_nota(cat: pd.DataFrame, n_muestra: int = 4000) -> go.Figure:
    """Dispersión (relación entre dos variables cuantitativas) con eje X logarítmico y
    transparencia contra la sobre-impresión. Se informa la correlación de Spearman (robusta a
    la asimetría) en el título."""
    v = cat[cat["nota"].notna()]
    if len(v) < 10:
        return vacio()
    fig = go.Figure()
    rhos = []
    for tp in TIPOS:
        s = v[v["tipo"] == tp]
        if len(s) < 10:
            continue
        rho = s[["popularity", "nota"]].corr("spearman").iloc[0, 1]
        rhos.append(f"ρ {tp.lower()}s = {fmt(rho, 2)}")
        s = s.sample(min(len(s), n_muestra), random_state=1)
        fig.add_scattergl(x=s["popularity"], y=s["nota"], mode="markers", name=tp, text=s["title"],
                          marker=dict(color=T.COLOR_TIPO[tp], size=6, opacity=0.35, line=dict(width=0)),
                          hovertemplate="<b>%{text}</b><br>Popularidad: %{x:.1f}<br>Calificación: %{y:.2f}<extra></extra>")
    fig.update_layout(title=T.titulo("Que un título sea popular no significa que esté bien evaluado",
                                     f"Cada punto es un título · la nube no forma una diagonal: relación débil ({', '.join(rhos)}) · ≥ 10 votos · {periodo(cat)}"),
                      xaxis=dict(type="log", title="Popularidad (escala logarítmica)"),
                      yaxis=dict(title="Calificación (0–10)", range=[0, 10.3]), height=480, separators=",.")
    return fig


def fig_tendencia_nota(cat: pd.DataFrame) -> go.Figure:
    """Línea (cambio en el tiempo, variable continua): calificación media por año y tipo.
    2025 se muestra separado (marcador hueco) porque solo ~8% de sus títulos tiene votos suficientes."""
    v = cat[cat["nota"].notna()]
    if v.empty:
        return vacio()
    t = v.groupby(["release_year", "tipo"])["nota"].mean().unstack()
    fig = go.Figure()
    for tp in [x for x in TIPOS if x in t]:
        s = t[tp].dropna()
        ok, inc = s[s.index < 2025], s[s.index >= 2025]
        fig.add_scatter(x=ok.index, y=ok.values, name=tp, mode="lines+markers",
                        line=dict(color=T.COLOR_TIPO[tp], width=2), marker=dict(size=8),
                        hovertemplate=f"<b>{tp}</b> · %{{x}}<br>Calificación media: %{{y:.2f}}<extra></extra>")
        if len(inc):
            fig.add_scatter(x=inc.index, y=inc.values, name=f"{tp} 2025 (datos incompletos)", mode="markers",
                            marker=dict(size=9, color=T.SURFACE, line=dict(width=2, color=T.COLOR_TIPO[tp])),
                            showlegend=False, hovertemplate=f"<b>{tp}</b> · %{{x}} (incompleto)<br>%{{y:.2f}}<extra></extra>")
        if len(ok):
            fig.add_annotation(x=ok.index[-1], y=ok.values[-1], text=f"<b>{tp}</b>", showarrow=False, xanchor="left",
                               xshift=10, yshift=12, font=dict(color=T.INK_2, size=12))
    h = "Evolución de la calificación media"
    if "Película" in t and t["Película"].dropna().size > 3:
        p = t["Película"].dropna()
        p = p[p.index < 2025]
        h = f"La calificación media de las películas sube de {fmt(p.iloc[0], 2)} a {fmt(p.iloc[-1], 2)} entre {p.index[0]} y {p.index[-1]}"
    fig.update_layout(title=T.titulo(h, f"Calificación media por año de estreno · títulos con ≥ 10 votos · 2025 con marcador hueco: datos incompletos"),
                      xaxis=dict(title="Año de estreno", dtick=1), yaxis=dict(title="Calificación media (0–10)"),
                      hovermode="x unified", height=420, separators=",.", showlegend=False)
    return fig


def fig_top_titulos(cat: pd.DataFrame, por: str = "popularity", n: int = 10) -> go.Figure:
    """Barras horizontales ordenadas (ranking): la longitud es el atributo preatentivo más preciso
    para comparar magnitudes; los títulos largos se leen cómodamente en el eje Y."""
    if por == "nota_ponderada":
        d = cat[cat["nota_ponderada"].notna()].nlargest(n, "nota_ponderada")
        xt, fmt_x, h0 = "Calificación ponderada (bayesiana)", ".2f", "mejor evaluados"
    elif por == "vote_count":
        d = cat.nlargest(n, "vote_count")
        xt, fmt_x, h0 = "Cantidad de votos", ",.0f", "con más votos"
    else:
        d = cat.nlargest(n, "popularity")
        xt, fmt_x, h0 = "Popularidad (índice TMDB)", ",.0f", "más populares"
    if d.empty:
        return vacio()
    d = d.iloc[::-1]
    lab = d["title"].str.slice(0, 38) + " (" + d["release_year"].astype(str) + ")"
    fig = go.Figure(go.Bar(y=lab, x=d[por], orientation="h", marker_color=[T.COLOR_TIPO[t] for t in d["tipo"]], showlegend=False,
                           text=[fmt(v, 2 if por == "nota_ponderada" else 0) for v in d[por]], textposition="outside",
                           customdata=np.c_[d["tipo"], d["genero_principal"].fillna("–"), d["pais_principal"].fillna("–"), d["vote_count"]],
                           hovertemplate="<b>%{y}</b><br>%{customdata[0]} · %{customdata[1]} · %{customdata[2]}"
                                         f"<br>{xt}: %{{x:{fmt_x}}}<br>Votos: %{{customdata[3]:,.0f}}<extra></extra>"))
    # leyenda manual (identidad de color nunca sola)
    for tp in TIPOS:
        if tp in d["tipo"].values:
            fig.add_bar(x=[None], y=[None], marker_color=T.COLOR_TIPO[tp], name=tp, showlegend=True)
    mix = d["tipo"].value_counts()
    h = f"Top {n} {h0}: {mix.idxmax().lower()}s ocupan {mix.max()} de {len(d)} posiciones"
    sub = (f"{xt} · {periodo(cat)}" + (" · ≥ 10 votos, ajustada por cantidad de votos" if por == "nota_ponderada" else ""))
    fig.update_layout(title=T.titulo(h, sub), xaxis=dict(title=xt, showgrid=False, showticklabels=False,
                                                          range=[0, d[por].max() * 1.18]),
                      height=440, separators=",.", margin=dict(l=280))
    return fig


# --------------------------------------------------------------------------- MERCADOS
def tabla_paises(pais: pd.DataFrame, min_n: int = 50) -> pd.DataFrame:
    a = pais.groupby(["pais", "iso3"]).agg(titulos=("uid", "size"), percentil_pop=("pct_popularidad", "median"),
                                           nota_media=("nota", "mean"), peliculas=("tipo", lambda x: (x == "Película").sum())).reset_index()
    a["share"] = a["titulos"] / a["titulos"].sum()
    return a[a["titulos"] >= min_n].sort_values("titulos", ascending=False)


def fig_mapa(pais: pd.DataFrame, metrica: str = "titulos") -> go.Figure:
    """Mapa coroplético (dato geográfico) con escala secuencial de un solo tono. Para volumen se
    usa escala logarítmica: EE.UU. aplastaría al resto con una escala lineal."""
    if pais.empty:
        return vacio()
    a = tabla_paises(pais, min_n=1 if metrica == "titulos" else 30)
    if metrica == "titulos":
        z, cb, tv = np.log10(a["titulos"]), "Títulos (escala log)", [1, 10, 100, 1000, 10000]
        top = a.iloc[0]
        sig = a["pais"].iloc[1:3].tolist()
        h = f"{top.pais} concentra el {pct(top.share)} de las producciones" + (f"; le siguen {' y '.join(sig)}" if sig else "")
        hov = "<b>%{text}</b><br>%{customdata[0]:,.0f} títulos<extra></extra>"
    else:
        z, cb, tv = a["percentil_pop"] * 100, "Popularidad relativa (50 = típico)", None
        top = a.sort_values("percentil_pop").iloc[-1]
        h = f"{top.pais} lidera en popularidad relativa entre países con ≥ 30 títulos"
        hov = "<b>%{text}</b><br>Popularidad relativa: %{z:.0f} / 100<br>%{customdata[0]:,.0f} títulos<extra></extra>"
    fig = go.Figure(go.Choropleth(locations=a["iso3"], z=z, text=a["pais"], customdata=np.c_[a["titulos"]],
                                  colorscale=T.SEQ_BLUE, marker_line_color=T.SURFACE, marker_line_width=0.5,
                                  colorbar=dict(title=dict(text=cb, side="right"), thickness=12, outlinewidth=0,
                                                tickvals=np.log10(tv) if tv else None, ticktext=[fmt(x) for x in tv] if tv else None),
                                  hovertemplate=hov))
    fig.update_geos(showframe=False, showcoastlines=False, showland=True, landcolor="#efeee9", bgcolor=T.SURFACE,
                    projection_type="natural earth", lataxis_range=[-58, 85])
    fig.update_layout(title=T.titulo(h, f"Países de producción (coproducciones cuentan para cada país) · {tipos_txt(pais)} · {periodo(pais)}"),
                      height=500, margin=dict(l=0, r=0, t=90, b=0), separators=",.")
    return fig


LATAM = {"México", "Brasil", "Argentina", "Colombia", "Chile", "Perú", "Venezuela", "Uruguay", "Ecuador",
         "Bolivia", "Paraguay", "Cuba", "Puerto Rico", "Guatemala", "Costa Rica", "República Dominicana", "Panamá"}


def fig_mercados(pais: pd.DataFrame, min_n: int = 50, n: int = 15) -> go.Figure:
    """Barras horizontales ordenadas: popularidad relativa del contenido de cada país (0–100,
    50 = título típico). La etiqueta de cada barra recuerda cuánto pesa ese país en el catálogo,
    para leer 'muy popular, pero poco ofertado' sin escalas logarítmicas. Latinoamérica destacada."""
    a = tabla_paises(pais, min_n)
    if a.empty:
        return vacio()
    a = a.nlargest(n, "percentil_pop").sort_values("percentil_pop")
    a["latam"] = a["pais"].isin(LATAM)
    fig = go.Figure(go.Bar(
        y=a["pais"], x=a["percentil_pop"] * 100, orientation="h",
        marker_color=[T.FOCO if l else T.CONTEXTO for l in a["latam"]],
        text=[f"{fmt(v * 100)}  ·  {pct(s, 1)} del catálogo" for v, s in zip(a["percentil_pop"], a["share"])],
        textposition="outside", textfont=dict(size=12, color=T.INK_2),
        customdata=np.c_[a["titulos"], a["nota_media"]],
        showlegend=False, hovertemplate="<b>%{y}</b><br>Popularidad relativa: %{x:.0f} / 100<br>%{customdata[0]:,.0f} títulos"
                      "<br>Calificación media: %{customdata[1]:.2f}<extra></extra>"))
    fig.add_vline(x=50, line=dict(color=T.MUTED, dash="dot", width=1))
    fig.add_annotation(x=50, y=0, yref="paper", text="título típico (50)", showarrow=False, yanchor="top",
                       font=dict(size=11, color=T.MUTED))
    for nm, col in [("Latinoamérica", T.FOCO), ("Otros países", T.CONTEXTO)]:
        fig.add_bar(x=[None], y=[None], marker_color=col, name=nm, showlegend=True)
    la = a[a["latam"]].sort_values("percentil_pop", ascending=False)
    h = (f"{', '.join(la['pais'].head(3))}: contenido más popular que el típico, pero con poca presencia en el catálogo"
         if len(la) else f"Países cuyo contenido es más popular que el título típico")
    fig.update_layout(title=T.titulo(h, f"Top {n} países por popularidad relativa (0–100; 50 = título típico) · países con ≥ {min_n} títulos · {periodo(pais)}"),
                      xaxis=dict(range=[0, 100 * 1.32], showgrid=False, showticklabels=False, title="", fixedrange=True),
                      yaxis=dict(fixedrange=True), height=540, separators=",.", bargap=0.3)
    return fig


def fig_paises_nota(pais: pd.DataFrame, n: int = 15) -> go.Figure:
    """Gráfico de puntos (dot plot) ordenado: compara calificación media por país con menos tinta
    que una barra y sin forzar el eje a 0 (la escala relevante es 6–7,5)."""
    a = tabla_paises(pais, 100).dropna(subset=["nota_media"]).nlargest(n, "titulos").sort_values("nota_media")
    if a.empty:
        return vacio()
    media = pais["nota"].mean()
    fig = go.Figure()
    fig.add_scatter(x=a["nota_media"], y=a["pais"], mode="markers+text", text=[fmt(v, 2) for v in a["nota_media"]],
                    textposition="middle right", marker=dict(size=12, color=[T.FOCO if v >= media else T.CONTEXTO for v in a["nota_media"]],
                                                             line=dict(width=2, color=T.SURFACE)),
                    customdata=a["titulos"], hovertemplate="<b>%{y}</b><br>Calificación: %{x:.2f}<br>%{customdata:,.0f} títulos<extra></extra>")
    fig.add_vline(x=media, line=dict(color=T.MUTED, dash="dot"), annotation_text=f"Promedio {fmt(media, 2)}",
                  annotation_font=dict(size=11, color=T.MUTED))
    top = a.iloc[-1]
    fig.update_layout(title=T.titulo(f"{top.pais} produce el contenido mejor evaluado entre los {n} mayores productores",
                                     f"Calificación media (≥ 10 votos) · {tipos_txt(pais)} · {periodo(pais)}"),
                      xaxis=dict(title="Calificación media (0–10)"), showlegend=False, height=520, separators=",.")
    return fig


# --------------------------------------------------------------------------- FINANZAS (solo películas)
def fig_presupuesto_ingresos(cat: pd.DataFrame) -> go.Figure:
    """Dispersión log-log con líneas de referencia ROI = 1 (punto de equilibrio) y ROI = 5.
    Escala log porque presupuesto e ingresos abarcan 4 órdenes de magnitud."""
    f = cat[cat["fin_valido"] == True]  # noqa: E712
    if len(f) < 5:
        return vacio("No hay películas con datos financieros válidos para los filtros")
    rho = np.corrcoef(np.log10(f["budget"]), np.log10(f["revenue"]))[0, 1]
    fig = go.Figure()
    for flag, color, name in [(False, T.CONTEXTO, "No recupera la inversión (ROI < 1)"), (True, T.COLOR_TIPO["Película"], "Rentable (ROI ≥ 1)")]:
        s = f[(f["roi"] >= 1) == flag]
        fig.add_scattergl(x=s["budget"], y=s["revenue"], mode="markers", name=name, text=s["title"],
                          marker=dict(size=7, color=color, opacity=0.6, line=dict(width=0)),
                          customdata=np.c_[s["roi"], s["release_year"]],
                          hovertemplate="<b>%{text}</b> (%{customdata[1]})<br>Presupuesto: $%{x:,.0f}<br>Ingresos: $%{y:,.0f}"
                                        "<br>ROI: %{customdata[0]:.1f}x<extra></extra>")
    lo, hi = f["budget"].min() * 0.8, f["budget"].max() * 1.2
    for k, txt in [(1, "ROI 1x (equilibrio)"), (5, "ROI 5x")]:
        fig.add_scatter(x=[lo, hi], y=[lo * k, hi * k], mode="lines", line=dict(color=T.MUTED, dash="dot", width=1),
                        showlegend=False, hoverinfo="skip")
        fig.add_annotation(x=np.log10(lo), y=np.log10(lo * k), text=txt, showarrow=False, xanchor="left", yanchor="bottom",
                           yshift=4, font=dict(size=10, color=T.MUTED), bgcolor="rgba(252,252,251,0.85)")
    hl = f[(f["budget"] < 5e6)].nlargest(3, "revenue")
    hl = pd.concat([hl, f.nlargest(1, "revenue")])
    hl = hl.sort_values("budget")
    for i, r in enumerate(hl.itertuples()):
        fig.add_annotation(x=np.log10(r.budget), y=np.log10(r.revenue), text=f"{r.title} ({fmt(r.roi)}x)", showarrow=True,
                           arrowhead=0, arrowcolor=T.MUTED, ax=(-60 + 10 * i) if i < 3 else -170,
                           ay=(-35 - 28 * (i % 3)) if i < 3 else -10,
                           font=dict(size=11, color=T.INK), bgcolor="rgba(252,252,251,0.85)")
    fig.update_layout(title=T.titulo(f"Más presupuesto tiende a más ingresos (r = {fmt(rho, 2)} en log), pero el {pct((f['roi'] < 1).mean())} no recupera la inversión",
                                     f"{fmt(len(f))} películas con presupuesto ≥ USD 100 mil e ingresos > 0 · {periodo(f)} · series excluidas (regla 3)"),
                      xaxis=dict(type="log", title="Presupuesto (USD, escala log)"),
                      yaxis=dict(type="log", title="Ingresos (USD, escala log)"), height=560, separators=",.")
    return fig


def fig_roi_genero(gen: pd.DataFrame, min_n: int = 25) -> go.Figure:
    """Barras horizontales ordenadas de ROI MEDIANO (la media está distorsionada por éxitos
    extremos de 50x–500x). Se destacan los 3 mejores y se marca el ROI = 1 (equilibrio)."""
    f = gen[(gen["fin_valido"] == True) & (gen["tipo"] == "Película")]  # noqa: E712
    a = f.groupby("genero").agg(roi=("roi", "median"), n=("uid", "size"), rent=("roi", lambda x: (x >= 1).mean()),
                                bud=("budget", "median"))
    a = a[a["n"] >= min_n].sort_values("roi")
    if a.empty:
        return vacio("No hay suficientes películas con datos financieros")
    top3 = a.index[-3:]
    fig = go.Figure(go.Bar(y=a.index, x=a["roi"], orientation="h",
                           marker_color=[T.COLOR_TIPO["Película"] if g in top3 else T.TINTE_TIPO["Película"] for g in a.index],
                           text=[f"{fmt(v, 1)}x" for v in a["roi"]], textposition="outside",
                           customdata=np.c_[a["n"], a["rent"] * 100, a["bud"] / 1e6],
                           hovertemplate="<b>%{y}</b><br>ROI mediano: %{x:.2f}x<br>%{customdata[1]:.0f}% rentables"
                                         "<br>Presupuesto mediano: USD %{customdata[2]:.1f} M<br>%{customdata[0]:,.0f} películas<extra></extra>"))
    fig.add_vline(x=1, line=dict(color=T.MUTED, dash="dot"), annotation_text="Equilibrio (1x)",
                  annotation_position="bottom right", annotation_font=dict(size=10, color=T.MUTED))
    fig.update_layout(title=T.titulo(f"{', '.join(top3[::-1])} entregan el mayor retorno mediano por dólar invertido",
                                     f"ROI = ingresos / presupuesto (mediana) · películas con datos financieros válidos · {periodo(f)} · géneros con ≥ {min_n} películas"),
                      xaxis=dict(title="ROI mediano (veces la inversión)", showgrid=False, range=[0, a["roi"].max() * 1.2]),
                      height=520, separators=",.")
    return fig


def fig_rentabilidad_tramo(cat: pd.DataFrame) -> go.Figure:
    """Barras verticales en orden natural (ordinal) del tramo de presupuesto: % de películas que
    recuperan su inversión. Responde '¿qué nivel de inversión es más seguro?'."""
    f = cat[cat["fin_valido"] == True]  # noqa: E712
    if f.empty:
        return vacio("No hay películas con datos financieros válidos")
    orden = ["Bajo (< 5M)", "Medio (5–20M)", "Alto (20–60M)", "Blockbuster (> 60M)"]
    a = f.groupby("tramo_presupuesto").agg(rent=("roi", lambda x: (x >= 1).mean()), roi=("roi", "median"), n=("uid", "size")).reindex(orden).dropna()
    best = a["rent"].idxmax()
    fig = go.Figure(go.Bar(x=a.index, y=a["rent"], marker_color=[T.COLOR_TIPO["Película"] if i == best else T.TINTE_TIPO["Película"] for i in a.index],
                           text=[pct(v) for v in a["rent"]], textposition="outside",
                           customdata=np.c_[a["roi"], a["n"]],
                           hovertemplate="<b>%{x}</b><br>%{y:.0%} rentables<br>ROI mediano: %{customdata[0]:.2f}x<br>%{customdata[1]:,.0f} películas<extra></extra>"))
    fig.update_layout(title=T.titulo(f"{best.split(' (')[0]}: el {pct(a.loc[best, 'rent'])} de las películas recupera su inversión",
                                     f"% de películas con ROI ≥ 1 por tramo de presupuesto (USD) · {periodo(f)}"),
                      yaxis=dict(tickformat=".0%", range=[0, 1.05], showgrid=False, showticklabels=False),
                      xaxis_title="Tramo de presupuesto", height=420, separators=",.")
    return fig


def tabla_joyas(cat: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Películas exitosas con presupuesto reducido (< USD 5 M, ROI ≥ 5x, ingresos ≥ USD 10 M)."""
    f = cat[(cat["fin_valido"] == True) & (cat["budget"] < 5e6) & (cat["roi"] >= 5) & (cat["revenue"] >= 1e7)]  # noqa: E712
    return f.nlargest(n, "revenue")[["title", "release_year", "genero_principal", "pais_principal", "budget", "revenue", "roi", "nota"]]


# --------------------------------------------------------------------------- TALENTO
def fig_top_personas(pers: pd.DataFrame, rol: str = "Director", n: int = 10) -> go.Figure:
    """Barras horizontales apiladas por tipo (identidad por color + leyenda): quién aparece más
    en el catálogo y en qué tipo de contenido."""
    p = pers[pers["rol"] == rol]
    if p.empty:
        return vacio()
    top = p["persona"].value_counts().head(n).index
    t = p[p["persona"].isin(top)].groupby(["persona", "tipo"]).size().unstack(fill_value=0).reindex(top[::-1])
    fig = go.Figure()
    for tp in [x for x in TIPOS if x in t]:
        fig.add_bar(y=t.index, x=t[tp], name=tp, orientation="h", marker_color=T.COLOR_TIPO[tp],
                    hovertemplate=f"<b>%{{y}}</b><br>{tp}s: %{{x}}<extra></extra>")
    tot = t.sum(axis=1)
    for y, v in tot.items():
        fig.add_annotation(x=v, y=y, text=str(v), showarrow=False, xanchor="left", xshift=6, font=dict(size=11, color=T.INK_2))
    nombre = "directores" if rol == "Director" else "actores/actrices (5 primeros créditos)"
    fig.update_layout(barmode="stack", title=T.titulo(f"{top[0]} es quien más títulos acumula entre los {nombre}",
                                                      f"Top {n} por cantidad de títulos en el catálogo filtrado · color = tipo de contenido"),
                      xaxis=dict(title="Títulos", showgrid=False), height=440, separators=",.")
    return fig


# --------------------------------------------------------------------------- CALIDAD DE DATOS
def fig_calidad(raw_movies: pd.DataFrame, raw_tv: pd.DataFrame) -> go.Figure:
    """Barras agrupadas horizontales: % de registros sin información por variable y dataset.
    Hace visible por qué algunas variables se excluyen o se usan con advertencias."""
    SI = "Sin información"
    rows = []
    for tp, d in [("Película", raw_movies), ("Serie", raw_tv)]:
        for c in ["director", "cast", "country", "genres", "description"]:
            rows.append([tp, c, (d[c] == SI).mean()])
        # duration: películas = 'Sin información'; series = valor constante '1 Seasons' -> sin valor analítico
        rows.append([tp, "duration (vacía o constante)", 1.0 if d["duration"].nunique() == 1 else (d["duration"] == SI).mean()])
        rows.append([tp, "vote_average (< 10 votos)", (d["vote_count"] < 10).mean()])
        if "budget" in d:
            rows.append([tp, "budget/revenue (sin dato válido)", 1 - ((d["budget"] >= 1e5) & (d["revenue"] > 0)).mean()])
        else:
            rows.append([tp, "budget/revenue (sin dato válido)", 1.0])
        rows.append([tp, "rating (duplica vote_average)", (d["rating"] == d["vote_average"]).mean()])
    q = pd.DataFrame(rows, columns=["tipo", "variable", "pct"])
    orden = q.groupby("variable")["pct"].max().sort_values().index
    fig = go.Figure()
    for tp in TIPOS:
        s = q[q["tipo"] == tp].set_index("variable").reindex(orden)
        fig.add_bar(y=s.index, x=s["pct"], name=tp, orientation="h", marker_color=T.COLOR_TIPO[tp],
                    text=[pct(v) for v in s["pct"]], textposition="outside",
                    hovertemplate=f"<b>%{{y}}</b><br>{tp}s: %{{x:.1%}}<extra></extra>")
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.1,
                      title=T.titulo("Duración y clasificación etaria no son utilizables; las series tienen pocos votos",
                                     "% de registros con el problema, por variable y dataset · datos originales (data/raw)"),
                      xaxis=dict(tickformat=".0%", range=[0, 1.15], showgrid=False, showticklabels=False),
                      height=520, separators=",.")
    return fig
