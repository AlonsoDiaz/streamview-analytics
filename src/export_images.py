"""
export_images.py
----------------
Genera todas las visualizaciones estáticas (PNG alta resolución) usadas en el informe
ejecutivo y la presentación. Requiere kaleido (y Chrome/Edge instalado).

    python src/export_images.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import charts as C  # noqa: E402
from data import ROOT, load  # noqa: E402

IMG = ROOT / "images"


def figuras(d: dict) -> dict:
    cat, gen, pais, pers = d["cat"], d["gen"], d["pais"], d["pers"]
    raw_m = pd.read_csv(ROOT / "data" / "raw" / "movies_clean.csv")
    raw_t = pd.read_csv(ROOT / "data" / "raw" / "tvshows_clean.csv")
    return {
        "00_calidad_datos": C.fig_calidad(raw_m, raw_t),
        "01_treemap_generos": C.fig_treemap_generos(gen),
        "02_idiomas": C.fig_idiomas(cat),
        "03_mapa_produccion": C.fig_mapa(pais),
        "04_brecha_oferta_demanda": C.fig_brecha_generos(gen),
        "05_matriz_peliculas": C.fig_matriz_oportunidad(gen, "Película"),
        "06_matriz_series": C.fig_matriz_oportunidad(gen, "Serie"),
        "07_mercados": C.fig_mercados(pais),
        "08_paises_nota": C.fig_paises_nota(pais),
        "09_dist_popularidad": C.fig_dist_popularidad(cat),
        "10_dist_nota": C.fig_dist_nota(cat),
        "11_pop_vs_nota": C.fig_pop_vs_nota(cat),
        "12_tendencia_nota": C.fig_tendencia_nota(cat),
        "13_mix_generos_peliculas": C.fig_mix_generos_tiempo(cat, "Película"),
        "14_mix_generos_series": C.fig_mix_generos_tiempo(cat, "Serie"),
        "15_heatmap_series": C.fig_heatmap_genero_anio(gen, "Serie"),
        "16_presupuesto_ingresos": C.fig_presupuesto_ingresos(cat),
        "17_roi_genero": C.fig_roi_genero(gen),
        "18_rentabilidad_tramo": C.fig_rentabilidad_tramo(cat),
        "19_top_populares": C.fig_top_titulos(cat, "popularity"),
        "20_top_evaluados": C.fig_top_titulos(cat, "nota_ponderada"),
        "21_top_directores": C.fig_top_personas(pers, "Director"),
        "22_top_actores": C.fig_top_personas(pers, "Actor/Actriz"),
        "23_incorporaciones_mes": C.fig_incorporaciones_mes(cat),
    }


def main(solo: list[str] | None = None) -> None:
    IMG.mkdir(exist_ok=True)
    figs = figuras(load())
    for name, fig in figs.items():
        if solo and not any(s in name for s in solo):
            continue
        fig.write_image(IMG / f"{name}.png", width=1200, height=fig.layout.height or 500, scale=2)
        print("ok", name)


SLIDES = ["01_treemap_generos", "11_pop_vs_nota", "04_brecha_oferta_demanda", "05_matriz_peliculas",
          "06_matriz_series", "07_mercados", "02_idiomas", "17_roi_genero", "16_presupuesto_ingresos", "00_calidad_datos"]


def slides() -> None:
    """Versiones sin título para la presentación: en la diapositiva el título-hallazgo lo pone el slide."""
    out = IMG / "slides"
    out.mkdir(parents=True, exist_ok=True)
    figs = figuras(load())
    for name in SLIDES:
        fig = figs[name]
        fig.update_layout(title=None, margin=dict(t=60 if fig.layout.showlegend is not False else 30, b=50),
                          font=dict(size=16))
        for a in fig.layout.annotations:  # etiquetas legibles en proyector
            a.font.size = max(a.font.size or 12, 13)
        fig.update_traces(textfont_size=17, selector=dict(type="bar"))
        fig.write_image(out / f"{name}.png", width=1250, height=640, scale=2)
        print("ok slide", name)


if __name__ == "__main__":
    if sys.argv[1:] == ["--slides"]:
        slides()
    else:
        main(sys.argv[1:] or None)
