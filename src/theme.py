"""
theme.py
--------
Sistema visual único de StreamView Analytics (consistencia gráfica = requisito no funcional).

Decisiones de diseño (justificadas en el informe, sección "Justificación de representaciones"):
* Paleta categórica validada para daltonismo (protanopía/deuteranopía/tritanopía):
  Película = azul, Serie = naranjo. El color SIGUE a la entidad en todos los gráficos.
* Gris de contexto + un color de foco ("highlight") para dirigir la atención (atributo preatentivo).
* Secuencial de un solo tono (azul claro -> oscuro) para magnitudes (mapas, heatmaps).
* Divergente azul <-> rojo con punto medio gris para brechas (sobre/sub-oferta).
* Tipografía de sistema sin serif, grilla tenue, un único eje Y por gráfico (sin ejes duales).
"""
import plotly.graph_objects as go
import plotly.io as pio

# --- Superficies y tinta -----------------------------------------------------
SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

# --- Categórica (orden fijo, nunca ciclado) ---------------------------------
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
COLOR_TIPO = {"Película": "#2a78d6", "Serie": "#eb6834"}
# Tintes claros de cada tipo para el contexto en gráficos con foco
TINTE_TIPO = {"Película": "#b7d3f6", "Serie": "#f7c9b5"}

FOCO = "#6250d6"          # foco cuando el gráfico mezcla ambos tipos
CONTEXTO = "#d6d5ce"      # gris de contexto (de-énfasis)
CONTEXTO_OSCURO = "#6e6d68"  # gris oscuro: el segmento "problema" (sobre-ofertado), con texto blanco

# --- Secuencial (azul) y divergente -------------------------------------------
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
DIVERGING = ["#c43a3a", "#e34948", "#f0a3a2", "#f0efec", "#9ec5f4", "#2a78d6", "#184f95"]
NEG, NEU, POS = "#e34948", "#f0efec", "#2a78d6"

# --- Estado (reservado: nunca se usa como serie) -----------------------------
GOOD, WARNING, CRITICAL = "#0ca30c", "#fab219", "#d03b3b"

FONT = "Segoe UI, system-ui, -apple-system, sans-serif"
FUENTE = "Fuente: catálogo StreamView Analytics (TMDB), estrenos 2010–2025."


def _template() -> go.layout.Template:
    t = go.layout.Template()
    t.layout = go.Layout(
        font=dict(family=FONT, size=13, color=INK_2),
        title=dict(font=dict(family=FONT, size=18, color=INK), x=0, xanchor="left", xref="container",
                   y=1, yanchor="top", yref="container", pad=dict(t=16, l=16)),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        colorway=SERIES,
        margin=dict(l=20, r=30, t=110, b=60),
        xaxis=dict(gridcolor=GRID, linecolor=AXIS, zeroline=False, ticks="", showline=True, automargin=True,
                   title=dict(font=dict(size=12, color=MUTED)), tickfont=dict(color=MUTED)),
        yaxis=dict(gridcolor=GRID, linecolor=AXIS, zeroline=False, ticks="", showline=False, automargin=True,
                   title=dict(font=dict(size=12, color=MUTED)), tickfont=dict(color=MUTED)),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0,
                    font=dict(size=12, color=INK_2), title=dict(text="")),
        hoverlabel=dict(bgcolor="white", bordercolor=AXIS, font=dict(family=FONT, size=12, color=INK)),
        bargap=0.25,
        separators=",.",
    )
    t.data.bar = [go.Bar(marker=dict(cornerradius=4, line=dict(width=0)))]
    t.data.scatter = [go.Scatter(line=dict(width=2), marker=dict(size=8, line=dict(width=1, color=SURFACE)))]
    return t


pio.templates["streamview"] = _template()
pio.templates.default = "streamview"


def titulo(hallazgo: str, alcance: str) -> dict:
    """Título-hallazgo (action title) + subtítulo con período y alcance (regla de negocio 7)."""
    return dict(
        text=f"<b>{hallazgo}</b><br><span style='font-size:13px;color:{INK_2}'>{alcance}</span>",
    )


def nota_fuente(fig: go.Figure, texto: str = FUENTE, y: float = -0.14) -> go.Figure:
    fig.add_annotation(text=texto, xref="paper", yref="paper", x=0, y=y, showarrow=False,
                       xanchor="left", yanchor="top", font=dict(size=11, color=MUTED))
    return fig
