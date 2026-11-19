"""
data.py
-------
Carga de las tablas procesadas y filtrado común (lo usan notebooks, export de imágenes y dashboard).
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"


def load() -> dict[str, pd.DataFrame]:
    archivos = ["catalogo.csv", "catalogo_generos.csv", "catalogo_paises.csv", "catalogo_personas.csv", "calidad_datos.csv"]
    if not all((PROC / a).exists() for a in archivos):
        # Primera ejecución (p. ej. en Streamlit Cloud): se generan desde data/raw
        import prepare_data
        prepare_data.main()
    cat = pd.read_csv(PROC / "catalogo.csv", low_memory=False, parse_dates=["date_added"])
    cat["generos"] = cat["generos"].fillna("")
    return {
        "cat": cat,
        "gen": pd.read_csv(PROC / "catalogo_generos.csv"),
        "pais": pd.read_csv(PROC / "catalogo_paises.csv"),
        "pers": pd.read_csv(PROC / "catalogo_personas.csv"),
        "calidad": pd.read_csv(PROC / "calidad_datos.csv"),
    }


def filtrar(d: dict, tipos=None, anios=None, generos=None, idiomas=None, paises=None) -> dict:
    """Aplica los filtros globales y propaga el subconjunto de títulos (uid) a todas las tablas."""
    cat = d["cat"]
    m = pd.Series(True, index=cat.index)
    if tipos:
        m &= cat["tipo"].isin(tipos)
    if anios:
        m &= cat["release_year"].between(*anios)
    if idiomas:
        m &= cat["idioma"].isin(idiomas)
    uids = set(cat.loc[m, "uid"])
    if generos:
        uids &= set(d["gen"].loc[d["gen"]["genero"].isin(generos), "uid"])
    if paises:
        uids &= set(d["pais"].loc[d["pais"]["pais"].isin(paises), "uid"])
    out = {k: (v[v["uid"].isin(uids)] if "uid" in v.columns else v) for k, v in d.items()}
    return out
