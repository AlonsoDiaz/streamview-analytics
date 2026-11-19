"""
prepare_data.py
---------------
Integra y prepara los datasets de StreamView Analytics para el análisis visual.

Entrada : data/raw/movies_clean.csv, data/raw/tvshows_clean.csv
Salida  : data/processed/*.csv  (catálogo unificado + tablas "explotadas")
          data/processed/calidad_datos.csv (bitácora de calidad)

Ejecutar desde la raíz del proyecto:
    python src/prepare_data.py

Todas las decisiones están documentadas en el README y en el notebook 01.
No se modifica la estructura de los archivos originales (regla del caso):
solo se agregan columnas derivadas en una copia procesada.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"

SIN_INFO = "Sin información"

# Umbrales de negocio (justificados en el informe, sección Calidad de datos)
MIN_VOTOS = 10            # vote_average con < 10 votos no es una valoración confiable
MIN_BUDGET = 100_000      # presupuestos < USD 100 mil se consideran errores de registro
WR_M = 100                # votos "de confianza" para la calificación ponderada bayesiana

# --------------------------------------------------------------------------
# Diccionarios de traducción (la audiencia es la Gerencia de Contenidos, en español)
# --------------------------------------------------------------------------
# Géneros armonizados: películas y series usan taxonomías TMDB distintas.
# Para comparar ambos tipos (regla de negocio 2) se agrupan en una taxonomía común.
GENERO_ES = {
    # Películas
    "Drama": "Drama", "Comedy": "Comedia", "Thriller": "Suspenso",
    "Action": "Acción y aventura", "Adventure": "Acción y aventura",
    "Romance": "Romance", "Horror": "Terror", "Crime": "Crimen",
    "Animation": "Animación", "Family": "Familiar",
    "Science Fiction": "Ciencia ficción y fantasía", "Fantasy": "Ciencia ficción y fantasía",
    "Mystery": "Misterio", "Documentary": "Documental", "History": "Historia",
    "TV Movie": "Película para TV", "Music": "Música", "War": "Bélico y política",
    "Western": "Western",
    # Series
    "Action & Adventure": "Acción y aventura", "Sci-Fi & Fantasy": "Ciencia ficción y fantasía",
    "Reality": "Reality", "Kids": "Infantil", "Talk": "Talk show", "Soap": "Telenovela",
    "War & Politics": "Bélico y política", "News": "Noticias", "Unknown": None,
}

IDIOMA_ES = {
    "en": "Inglés", "es": "Español", "fr": "Francés", "ja": "Japonés", "ko": "Coreano",
    "zh": "Chino", "cn": "Cantonés", "it": "Italiano", "de": "Alemán", "hi": "Hindi",
    "pt": "Portugués", "ru": "Ruso", "tl": "Tagalo", "tr": "Turco", "th": "Tailandés",
    "sv": "Sueco", "da": "Danés", "no": "Noruego", "nb": "Noruego", "nl": "Neerlandés",
    "pl": "Polaco", "ar": "Árabe", "id": "Indonesio", "ta": "Tamil", "te": "Telugu",
    "ml": "Malayalam", "fi": "Finés", "he": "Hebreo", "fa": "Persa", "uk": "Ucraniano",
    "cs": "Checo", "hu": "Húngaro", "el": "Griego", "ro": "Rumano", "vi": "Vietnamita",
    "ms": "Malayo", "bn": "Bengalí", "kn": "Canarés", "mr": "Maratí", "is": "Islandés",
    "ca": "Catalán", "xx": "Sin idioma",
}

PAIS_ES = {
    "United States of America": "Estados Unidos", "United Kingdom": "Reino Unido",
    "France": "Francia", "Canada": "Canadá", "Japan": "Japón", "South Korea": "Corea del Sur",
    "Germany": "Alemania", "Spain": "España", "India": "India", "Belgium": "Bélgica",
    "China": "China", "Italy": "Italia", "Australia": "Australia", "Hong Kong": "Hong Kong",
    "Mexico": "México", "Philippines": "Filipinas", "Turkey": "Turquía", "Brazil": "Brasil",
    "Argentina": "Argentina", "Colombia": "Colombia", "Chile": "Chile", "Sweden": "Suecia",
    "Denmark": "Dinamarca", "Norway": "Noruega", "Netherlands": "Países Bajos",
    "Taiwan": "Taiwán", "Thailand": "Tailandia", "Ireland": "Irlanda", "Poland": "Polonia",
    "Russia": "Rusia", "Indonesia": "Indonesia", "New Zealand": "Nueva Zelanda",
    "Switzerland": "Suiza", "Finland": "Finlandia", "Austria": "Austria",
    "South Africa": "Sudáfrica", "Israel": "Israel", "Egypt": "Egipto", "Nigeria": "Nigeria",
    "Peru": "Perú", "Czech Republic": "República Checa", "Luxembourg": "Luxemburgo",
    "Greece": "Grecia", "Hungary": "Hungría", "Iceland": "Islandia", "Malaysia": "Malasia",
    "Pakistan": "Pakistán", "Romania": "Rumania", "Serbia": "Serbia", "Singapore": "Singapur",
    "Slovakia": "Eslovaquia", "Ukraine": "Ucrania", "United Arab Emirates": "Emiratos Árabes Unidos",
    "Bulgaria": "Bulgaria", "Uruguay": "Uruguay", "Venezuela": "Venezuela", "Ecuador": "Ecuador",
    "Cuba": "Cuba", "Puerto Rico": "Puerto Rico", "Dominican Republic": "República Dominicana",
    "Guatemala": "Guatemala", "Costa Rica": "Costa Rica", "Panama": "Panamá", "Bolivia": "Bolivia",
    "Paraguay": "Paraguay", "Vietnam": "Vietnam", "Lebanon": "Líbano", "Morocco": "Marruecos",
    "Iran": "Irán", "Saudi Arabia": "Arabia Saudita", "Croatia": "Croacia", "Estonia": "Estonia",
    "Lithuania": "Lituania", "Latvia": "Letonia", "Slovenia": "Eslovenia", "Kenya": "Kenia",
}

TIPO_ES = {"Movie": "Película", "TV Show": "Serie"}


ISO_FIX = {
    "South Korea": "KOR", "Russia": "RUS", "Macedonia": "MKD", "Palestinian Territory": "PSE",
    "Kyrgyz Republic": "KGZ", "Faeroe Islands": "FRO", "Congo": "COG", "Macao": "MAC",
    "Syrian Arab Republic": "SYR", "Cote D'Ivoire": "CIV", "Turkey": "TUR", "Czech Republic": "CZE",
    "Taiwan": "TWN", "Kosovo": "XKX", "Guadaloupe": "GLP", "St. Kitts and Nevis": "KNA",
    "US Virgin Islands": "VIR", "St. Lucia": "LCA", "St. Pierre and Miquelon": "SPM",
}


def iso3(nombre: str):
    """Nombre de país (inglés) -> código ISO-3 para el mapa coroplético."""
    if nombre in ISO_FIX:
        return ISO_FIX[nombre]
    try:
        import pycountry
        try:
            return pycountry.countries.lookup(nombre).alpha_3
        except LookupError:
            return pycountry.countries.search_fuzzy(nombre)[0].alpha_3
    except Exception:
        return None


def _split(series: pd.Series) -> pd.Series:
    """Convierte un campo multivalor 'a, b, c' en listas (NaN -> lista vacía)."""
    return series.fillna("").apply(lambda s: [x.strip() for x in s.split(",") if x.strip()])


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    movies = pd.read_csv(RAW / "movies_clean.csv")
    tv = pd.read_csv(RAW / "tvshows_clean.csv")
    return movies, tv


def quality_log(movies: pd.DataFrame, tv: pd.DataFrame) -> pd.DataFrame:
    """Bitácora de calidad: un renglón por (dataset, variable, problema)."""
    rows = []
    for name, d in [("Películas", movies), ("Series", tv)]:
        n = len(d)
        for col in d.columns:
            if d[col].dtype == object or str(d[col].dtype).startswith("str"):
                k = int((d[col] == SIN_INFO).sum())
                if k:
                    rows.append([name, col, "Valor 'Sin información'", k, k / n])
        rows.append([name, "rating", "Idéntica a vote_average (no es clasificación etaria)",
                     int((d["rating"] == d["vote_average"]).sum()), (d["rating"] == d["vote_average"]).mean()])
        rows.append([name, "vote_count", "Títulos con 0 votos (vote_average=0 no es una nota real)",
                     int((d["vote_count"] == 0).sum()), (d["vote_count"] == 0).mean()])
        rows.append([name, "vote_count", f"Títulos con < {MIN_VOTOS} votos (valoración poco confiable)",
                     int((d["vote_count"] < MIN_VOTOS).sum()), (d["vote_count"] < MIN_VOTOS).mean()])
        rows.append([name, "release_year", "Muestra estratificada: exactamente 1.000 títulos por año",
                     int(d["release_year"].value_counts().nunique() == 1), np.nan])
        rows.append([name, "date_added", "Año de date_added = release_year en el 100% de los casos",
                     int((pd.to_datetime(d["date_added"]).dt.year == d["release_year"]).sum()),
                     (pd.to_datetime(d["date_added"]).dt.year == d["release_year"]).mean()])
        rows.append([name, "show_id", "IDs duplicados dentro del dataset", int(d["show_id"].duplicated().sum()), 0])
        rows.append([name, "title", "Títulos homónimos (distinto show_id; se conservan)",
                     int(d["title"].duplicated().sum()), d["title"].duplicated().mean()])
        rows.append([name, "popularity", "Asimetría (media / mediana)",
                     np.nan, d["popularity"].mean() / d["popularity"].median()])
    rows.append(["Ambos", "show_id", "IDs repetidos entre películas y series (espacios de ID distintos)",
                 len(set(movies["show_id"]) & set(tv["show_id"])), np.nan])
    b, r = movies["budget"], movies["revenue"]
    rows.append(["Películas", "budget", "budget = 0 (sin dato)", int((b == 0).sum()), (b == 0).mean()])
    rows.append(["Películas", "revenue", "revenue = 0 (sin dato)", int((r == 0).sum()), (r == 0).mean()])
    rows.append(["Películas", "budget", f"0 < budget < USD {MIN_BUDGET:,} (error de registro probable)",
                 int(((b > 0) & (b < MIN_BUDGET)).sum()), ((b > 0) & (b < MIN_BUDGET)).mean()])
    rows.append(["Películas", "budget/revenue", "Universo financiero válido (budget>=100k y revenue>0)",
                 int(((b >= MIN_BUDGET) & (r > 0)).sum()), ((b >= MIN_BUDGET) & (r > 0)).mean()])
    return pd.DataFrame(rows, columns=["dataset", "variable", "hallazgo", "registros", "proporcion"])


def build_catalog(movies: pd.DataFrame, tv: pd.DataFrame) -> pd.DataFrame:
    tv = tv.copy()
    tv["budget"] = np.nan          # no existe para series (regla de negocio 3 y 9)
    tv["revenue"] = np.nan
    cat = pd.concat([movies, tv], ignore_index=True)

    # Clave única: los show_id se repiten entre datasets (397 casos)
    cat.insert(0, "uid", np.where(cat["type"] == "Movie", "M-", "T-") + cat["show_id"].astype(str))

    # 'Sin información' -> nulo explícito
    cat = cat.replace(SIN_INFO, np.nan)

    # Variables sin valor analítico (documentado): rating duplica vote_average,
    # duration es constante ("Sin información" / "1 Seasons").
    cat = cat.drop(columns=["rating", "duration"])

    cat["tipo"] = cat["type"].map(TIPO_ES)
    cat["date_added"] = pd.to_datetime(cat["date_added"])
    cat["mes_incorporacion"] = cat["date_added"].dt.month
    cat["idioma"] = cat["language"].map(IDIOMA_ES).fillna(cat["language"].str.upper())

    # Listas de valores multivalor
    cat["generos_lista"] = _split(cat["genres"]).apply(
        lambda gs: sorted({GENERO_ES.get(g, g) for g in gs if GENERO_ES.get(g, g)}))
    cat["paises_lista"] = _split(cat["country"]).apply(lambda cs: [PAIS_ES.get(c, c) for c in cs])
    cat["genero_principal"] = _split(cat["genres"]).apply(
        lambda gs: next((GENERO_ES[g] for g in gs if GENERO_ES.get(g)), np.nan))
    cat["pais_principal"] = cat["paises_lista"].apply(lambda cs: cs[0] if cs else np.nan)
    cat["coproduccion"] = cat["paises_lista"].apply(len) > 1
    cat["n_generos"] = cat["generos_lista"].apply(len)

    # Valoración: solo confiable con un mínimo de votos
    cat["valoracion_valida"] = cat["vote_count"] >= MIN_VOTOS
    cat["nota"] = cat["vote_average"].where(cat["valoracion_valida"])
    # Calificación ponderada (fórmula bayesiana tipo IMDb) para rankings justos
    for t in cat["type"].unique():
        mask = (cat["type"] == t) & cat["valoracion_valida"]
        C = cat.loc[mask, "vote_average"].mean()
        v, R = cat.loc[mask, "vote_count"], cat.loc[mask, "vote_average"]
        cat.loc[mask, "nota_ponderada"] = (v / (v + WR_M)) * R + (WR_M / (v + WR_M)) * C

    # Popularidad: índice relativo muy asimétrico -> se trabaja en log y percentiles por tipo
    cat["log_popularidad"] = np.log10(cat["popularity"])
    cat["pct_popularidad"] = cat.groupby("type")["popularity"].rank(pct=True)

    # Finanzas (solo películas, universo válido)
    fin = (cat["type"] == "Movie") & (cat["budget"] >= MIN_BUDGET) & (cat["revenue"] > 0)
    cat["fin_valido"] = fin
    cat["roi"] = (cat["revenue"] / cat["budget"]).where(fin)
    cat["ganancia"] = (cat["revenue"] - cat["budget"]).where(fin)
    cat["rentable"] = (cat["roi"] >= 1).where(fin)
    cat["tramo_presupuesto"] = pd.cut(
        cat["budget"].where(fin), [0, 5e6, 20e6, 60e6, np.inf],
        labels=["Bajo (< 5M)", "Medio (5–20M)", "Alto (20–60M)", "Blockbuster (> 60M)"])
    return cat


def explode(cat: pd.DataFrame, col: str, name: str) -> pd.DataFrame:
    keep = ["uid", "type", "tipo", "title", "release_year", "popularity", "log_popularidad",
            "pct_popularidad", "vote_count", "nota", "nota_ponderada", "valoracion_valida",
            "budget", "revenue", "roi", "fin_valido", "idioma", "pais_principal", "genero_principal"]
    out = cat[keep + [col]].explode(col).rename(columns={col: name})
    return out.dropna(subset=[name])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    movies, tv = load_raw()

    q = quality_log(movies, tv)
    q.to_csv(OUT / "calidad_datos.csv", index=False, encoding="utf-8-sig")

    cat = build_catalog(movies, tv)
    flat = cat.drop(columns=["generos_lista", "paises_lista", "paises_en"], errors="ignore").copy()
    flat["generos"] = cat["generos_lista"].str.join("|")
    flat["paises"] = cat["paises_lista"].str.join("|")
    flat.to_csv(OUT / "catalogo.csv", index=False, encoding="utf-8-sig")

    explode(cat, "generos_lista", "genero").to_csv(OUT / "catalogo_generos.csv", index=False, encoding="utf-8-sig")
    cat["paises_en"] = _split(cat["country"])
    paises = explode(cat, "paises_en", "pais_en")
    paises["pais"] = paises["pais_en"].map(PAIS_ES).fillna(paises["pais_en"])
    paises["iso3"] = paises["pais_en"].map({n: iso3(n) for n in paises["pais_en"].unique()})
    paises.to_csv(OUT / "catalogo_paises.csv", index=False, encoding="utf-8-sig")

    people = []
    for col, rol, top in [("director", "Director", None), ("cast", "Actor/Actriz", 5)]:
        tmp = cat[["uid", "type", "tipo", "title", "popularity", "nota"]].copy()
        tmp["persona"] = _split(cat[col]).apply(lambda xs: xs[:top] if top else xs)
        tmp = tmp.explode("persona").dropna(subset=["persona"])
        tmp["rol"] = rol
        people.append(tmp)
    pd.concat(people).to_csv(OUT / "catalogo_personas.csv", index=False, encoding="utf-8-sig")

    print(f"Catálogo unificado: {len(cat):,} títulos "
          f"({(cat.type=='Movie').sum():,} películas, {(cat.type=='TV Show').sum():,} series)")
    print(f"Con valoración válida (>= {MIN_VOTOS} votos): {cat.valoracion_valida.sum():,}")
    print(f"Universo financiero válido: {cat.fin_valido.sum():,} películas")
    print(f"Archivos escritos en {OUT}")


if __name__ == "__main__":
    main()
