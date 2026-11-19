/*
 * build_presentation.js
 * ---------------------
 * Genera la presentación ejecutiva (EP6, 10 minutos) en reports/Presentacion_Ejecutiva_StreamView.pptx
 * Requiere: npm install pptxgenjs   ·   imágenes previas: python src/export_images.py --slides
 *
 *   node src/build_presentation.js
 *
 * Cada diapositiva lleva notas del orador (guion para la defensa).
 */
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const IMG = (f) => path.join(ROOT, "images", f);
const OUT = path.join(ROOT, "reports", "Presentacion_Ejecutiva_StreamView.pptx");

// Paleta = la misma del dashboard (consistencia gráfica entre productos)
const K = {
  ink: "0B0B0B", ink2: "52514E", muted: "898781", surface: "FCFCFB", white: "FFFFFF",
  night: "1E1A4B", foco: "6250D6", focoSoft: "E9E6FA", movie: "2A78D6", serie: "EB6834",
  grid: "E1E0D9", card: "F3F2EE",
};
const THEME = {
  name: "StreamView Analytics", headFontFace: "Calibri", bodyFontFace: "Calibri",
  colors: { dk1: K.ink, lt1: K.white, dk2: K.night, lt2: K.surface, accent1: K.foco, accent2: K.movie,
    accent3: K.serie, accent4: "1BAF7A", accent5: "EDA100", accent6: "E34948", hlink: K.foco, folHlink: K.night },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13,33 x 7,5 in
pres.author = "Equipo consultor StreamView";
pres.title = "Catálogo audiovisual: dónde invertir y qué adquirir";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "PORTADA", background: { color: K.night },
  objects: [
    { placeholder: { options: { name: "tag", type: "body", x: 0.8, y: 1.6, w: 11.5, h: 0.5, fontSize: 14, bold: true, color: "B9B1F5", charSpacing: 2 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.15, w: 11.5, h: 1.9, fontSize: 48, bold: true, color: K.white, valign: "top", align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.1, w: 11.0, h: 0.9, fontSize: 20, color: "D9D6F5", valign: "top" }, text: "" } },
    { placeholder: { options: { name: "team", type: "body", x: 0.8, y: 6.2, w: 11.5, h: 0.6, fontSize: 13, color: "B9B1F5" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENIDO", background: { color: K.surface },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.3, w: 12.1, h: 1.05, fontSize: 30, bold: true, color: K.ink, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "StreamView Analytics · Gerencia de Contenidos y Adquisición", options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: K.muted, margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: K.muted, align: "right" },
});
pres.defineSlideMaster({
  title: "CIERRE", background: { color: K.night },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 1.0, fontSize: 32, bold: true, color: K.white, valign: "middle", align: "left", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: "B9B1F5", align: "right" },
});

// ------------------------------------------------------------------ helpers
let n = 0;
const name = (s) => `${s}_${++n}`;
const SEC = { a: "Contexto", b: "Hallazgos", c: "Solución", d: "Decisiones" };

function contenido(titulo, seccion) {
  const s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: seccion });
  s.addText(titulo, { placeholder: "title" });
  return s;
}

function grafico(s, file, alt, x = 0.6, y = 1.55, w = 8.5, h = 4.35) {
  s.addImage({ path: IMG(file), x, y, w, h, altText: alt, objectName: name("grafico") });
  s.addText("Fuente: catálogo StreamView (TMDB), estrenos 2010–2025", {
    x, y: y + h + 0.08, w, h: 0.3, fontSize: 10, color: K.muted, margin: 0, isTextBox: true, objectName: name("fuente"),
  });
}

// Callout numérico: número grande + etiqueta (columna derecha)
function stat(s, y, valor, etiqueta, color = K.foco) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 9.45, y, w: 3.25, h: 1.32, fill: { color: K.white },
    line: { color: K.grid, width: 1 }, rectRadius: 0.08, objectName: name("tarjeta") });
  s.addText(valor, { x: 9.65, y: y + 0.1, w: 2.95, h: 0.62, fontSize: 32, bold: true, color, margin: 0, isTextBox: true, objectName: name("valor") });
  s.addText(etiqueta, { x: 9.65, y: y + 0.7, w: 2.95, h: 0.56, fontSize: 12, color: K.ink2, margin: 0, valign: "top", isTextBox: true, objectName: name("etiqueta") });
}

function numero(s, x, y, txt, fill = K.foco, color = K.white, d = 0.55) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: name("circulo") });
  s.addText(txt, { x, y, w: d, h: d, fontSize: 16, bold: true, color, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: name("num") });
}

// Tabla con el estilo del deck (encabezado gris cálido, filas con separador)
function tablaSlide(s, filas, cab, opts) {
  const head = cab.map((t) => ({ text: t, options: { bold: true, color: K.ink, fill: { color: "EFEEE9" }, fontSize: 15 } }));
  const body = filas.map((f) => f.map((t, j) => ({ text: t, options: { color: j === 0 ? K.ink : K.ink2, bold: j === 0, fontSize: 15 } })));
  s.addTable([head, ...body], { x: 0.6, y: 1.6, w: 12.1, border: { type: "solid", pt: 0.75, color: K.grid },
    fill: { color: K.white }, margin: [9, 9, 9, 9], valign: "middle", objectName: name("tabla"), ...opts });
}
const SEC2 = { a: "Problema y datos", b: "Dashboard y hallazgos", c: "Evaluación crítica", d: "Decisiones e impacto", e: "Anexo (respaldo para preguntas)" };

// ================================================================== 1. PORTADA
pres.addSection({ title: SEC2.a });
let s = pres.addSlide({ masterName: "PORTADA", sectionTitle: SEC2.a });
s.addText("ADY1104 · VISUALIZACIÓN DE DATOS · PRESENTACIÓN EJECUTIVA", { placeholder: "tag" });
s.addText("Catálogo audiovisual: dónde invertir y qué adquirir", { placeholder: "title" });
s.addText("Visual Analytics para la Gerencia de Contenidos y Adquisición de StreamView Analytics", { placeholder: "body" });
s.addText("Equipo consultor: [Integrante 1] · [Integrante 2] · [Integrante 3]   |   Duoc UC · 2026", { placeholder: "team" });
s.addNotes("[0:00–0:15] Buenos días. Somos el equipo consultor de StreamView Analytics. Presentamos al Gerente de Contenidos y Adquisición una solución de Visual Analytics que responde qué contenido priorizar y qué evidencia respalda esa decisión.");

// ================================================================== 2. PROBLEMA Y AUDIENCIA (1 min)
s = contenido("El problema: se decide qué adquirir con información parcial", SEC2.a);
const cards = [
  ["Problema", "Cada área usa reportes distintos, hay varias versiones del mismo indicador y los dashboards actuales tienen exceso de información y poca interacción."],
  ["Audiencia", "Gerente de Contenidos y Adquisición: evalúa títulos, negocia licencias y define el catálogo. Secundarias: Gerencia General (resumen) y Marketing (rankings)."],
  ["Pregunta", "¿Qué géneros, mercados y tipos de contenido debería priorizar StreamView para tener un catálogo más popular y mejor evaluado?"],
];
cards.forEach(([t, d], i) => {
  const x = 0.6 + i * 4.1;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.9, w: 3.85, h: 3.9, fill: { color: i === 2 ? K.focoSoft : K.white },
    line: { color: K.grid, width: 1 }, rectRadius: 0.1, objectName: name("tarjeta") });
  numero(s, x + 0.35, 2.2, String(i + 1));
  s.addText(t, { x: x + 0.35, y: 2.95, w: 3.2, h: 0.5, fontSize: 22, bold: true, color: K.ink, margin: 0, isTextBox: true, objectName: name("cab") });
  s.addText(d, { x: x + 0.35, y: 3.55, w: 3.2, h: 2.1, fontSize: 16, color: K.ink2, margin: 0, valign: "top", isTextBox: true, objectName: name("txt") });
});
s.addNotes("[0:15–1:15] El problema: las decisiones de adquisición se toman con información parcial y dispersa (problemas 1, 3, 6 y 7 del caso). Audiencia principal: el Gerente de Contenidos y Adquisición, que conoce el negocio pero necesita respuestas rápidas y comparables. Gerencia General y Marketing son audiencias secundarias. Todo el proyecto responde una sola pregunta: qué priorizar y con qué evidencia.");

// ================================================================== 3. DATOS, RELACIONES Y LÍMITES (1 min)
s = contenido("Datos y límites: 32.000 títulos de catálogo, sin datos de usuarios", SEC2.a);
const box = (x, y, w, h, t1, t2, fill, col) => {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.1, objectName: name("caja") });
  s.addText([{ text: t1, options: { fontSize: 24, bold: true, color: col, breakLine: true } }, { text: t2, options: { fontSize: 13, color: col } }],
    { x, y, w, h, align: "center", valign: "middle", margin: 0.1, isTextBox: true, objectName: name("cajatxt") });
};
box(0.6, 1.65, 3.0, 1.15, "16.000", "películas · con budget y revenue", K.movie, K.white);
box(0.6, 3.25, 3.0, 1.15, "16.000", "series · sin datos financieros", K.serie, K.white);
box(4.35, 2.42, 3.1, 1.2, "32.000", "catálogo unificado · clave uid", K.night, K.white);
s.addShape(pres.shapes.LINE, { x: 3.6, y: 2.22, w: 0.75, h: 0.8, line: { color: K.muted, width: 1.5, endArrowType: "triangle" }, objectName: name("flecha") });
s.addShape(pres.shapes.LINE, { x: 3.6, y: 3.02, w: 0.75, h: 0.8, flipV: true, line: { color: K.muted, width: 1.5, endArrowType: "triangle" }, objectName: name("flecha") });
s.addText("1:N por uid → géneros · países · personas (campos multivalor)", { x: 0.6, y: 4.6, w: 6.9, h: 0.35, fontSize: 13, color: K.ink2, italic: true, margin: 0, isTextBox: true, objectName: name("nota") });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.15, w: 6.85, h: 1.45, fill: { color: "FDECE6" }, line: { color: "F4C4B2", width: 1 }, rectRadius: 0.08, objectName: name("alcance") });
s.addText([{ text: "Fuera de alcance", options: { bold: true, color: K.ink, fontSize: 15, breakLine: true } },
  { text: "Retención, engagement y comportamiento de usuarios: requieren datos de usuarios, suscripciones o reproducciones, que no están disponibles. No prometemos impacto en esas métricas.", options: { color: K.ink2, fontSize: 13 } }],
  { x: 0.8, y: 5.22, w: 6.5, h: 1.32, margin: 0, valign: "middle", isTextBox: true, objectName: name("alcancetxt") });
const dec = [
  ["rating copia a vote_average", "Sin clasificación etaria: esos KPIs no son calculables"],
  ["Pocos votos (mediana 4 en series)", "Calificación solo con ≥ 10 votos + ranking bayesiano"],
  ["Popularidad TMDB asimétrica", "Índice relativo, no reproducciones: popularidad relativa 0–100"],
  ["1.000 títulos por año (muestra)", "Se analiza composición, no crecimiento"],
  ["Presupuestos erróneos", "Finanzas solo con 3.500 películas válidas"],
];
s.addText("Decisiones de calidad", { x: 7.9, y: 1.6, w: 4.8, h: 0.45, fontSize: 18, bold: true, color: K.ink, margin: 0, isTextBox: true, objectName: name("cab") });
dec.forEach(([a, b], i) => {
  const y = 2.15 + i * 0.9;
  numero(s, 7.9, y + 0.05, String(i + 1), K.focoSoft, K.foco, 0.42);
  s.addText([{ text: a, options: { bold: true, color: K.ink, fontSize: 14, breakLine: true } }, { text: b, options: { color: K.ink2, fontSize: 13 } }],
    { x: 8.45, y, w: 4.25, h: 0.82, margin: 0, valign: "top", isTextBox: true, objectName: name("dec") });
});
s.addNotes("[1:15–2:15] Integramos los dos datasets oficiales en un catálogo de 32 mil títulos con una clave única, y separamos géneros, países y personas en tablas relacionadas. Límites que condicionan todo: rating es una copia de vote_average, así que no hay clasificación etaria; las series tienen muy pocos votos; la popularidad es un índice relativo de TMDB, no reproducciones; hay mil títulos por año, así que analizamos composición; y solo 3.500 películas tienen finanzas válidas. Lo más importante: no tenemos datos de usuarios, por lo que no analizamos ni prometemos impacto en retención o engagement.");

// ================================================================== 4. HALLAZGO 1 (dashboard y hallazgos: 3 min en total)
pres.addSection({ title: SEC2.b });
s = contenido("Qué ocurre: lo más ofertado no es lo más demandado", SEC2.b);
grafico(s, "slides/04_brecha_oferta_demanda.png", "Barras divergentes: brecha entre participación en el 20% más popular y participación en el catálogo por género");
stat(s, 1.55, "−5,1 pp", "Drama (películas): el género más ofertado, sub-representado entre los populares", K.ink2);
stat(s, 3.0, "+6,0 pp", "Acción y aventura (películas): más presente entre los populares que en el catálogo", K.movie);
stat(s, 4.45, "+3,4 pp", "Telenovela (series): la mayor brecha de demanda en series", K.serie);
s.addNotes("[2:15–3:00] Hallazgo principal. Creamos una métrica de brecha: el porcentaje de un género entre el 20% más popular menos su porcentaje en el catálogo. Barras divergentes desde cero, con color solo en las oportunidades y gris en la sobre-oferta. Drama, el género más ofertado, está sobre-representado; Acción y aventura y Telenovela tienen más demanda que oferta.");

// ================================================================== 5. HALLAZGO 2
s = contenido("Animación y Familiar: populares, bien evaluadas y rentables", SEC2.b);
grafico(s, "slides/05_matriz_peliculas.png", "Matriz de oportunidad de películas: popularidad relativa versus calificación, tamaño por cantidad de títulos");
stat(s, 1.55, "65 · 6,95", "Animación: popularidad relativa (típico = 50) y la mejor nota de los géneros masivos", K.movie);
stat(s, 3.0, "4,3%", "de la oferta de películas: burbuja pequeña en el cuadrante de oportunidad", K.movie);
stat(s, 4.45, "2,3x · 2,2x", "ROI mediano de Animación y Familiar (Drama: 1,3x)", K.movie);
s.addNotes("[3:00–3:50] La matriz de oportunidad cruza popularidad y calificación porque casi no se relacionan (correlación 0,23): mirar una sola deja oportunidades fuera. El tamaño es la oferta actual. Buscamos burbujas pequeñas arriba a la derecha: Animación es el caso más claro, seguida por Familiar, y además tienen el mejor retorno mediano en taquilla.");

// ================================================================== 6. HALLAZGO 3
s = contenido("Latinoamérica está sub-representada pese a su alta popularidad", SEC2.b);
grafico(s, "slides/07_mercados.png", "Ranking de países por popularidad relativa con el porcentaje del catálogo anotado; Latinoamérica destacada");
stat(s, 1.55, "5,1%", "del catálogo está en español, con popularidad relativa 58 (típico = 50; inglés 55)");
stat(s, 3.0, "66 / 100", "México: popularidad sobre el típico con solo 1,5% de las producciones");
stat(s, 4.45, "67 / 100", "Chile; Colombia 60, ambos con menos de 0,5% de la oferta");
s.addNotes("[3:50–4:30] Este ranking ordena los países por qué tan popular es su contenido: 50 es el título típico. El texto de cada barra dice cuánto pesa ese país en el catálogo. Latinoamérica en violeta porque es nuestro mercado: Chile, México y Colombia están entre los más populares pero suman menos del 2,5% del catálogo. Lo mismo con el idioma: el español es solo 5,1% del catálogo pero está sobre la mediana de popularidad.");

// ================================================================== 7. DASHBOARD
s = contenido("Un dashboard para explorar, comprender y decidir", SEC2.b);
s.addImage({ path: IMG("dashboard_tab1_vista.png"), x: 0.6, y: 1.55, w: 8.4, h: 4.81, altText: "Captura del dashboard: vista Oportunidades de adquisición con filtros y matriz interactiva", objectName: name("captura") });
const feats = [
  ["7 páginas con propósito", "Cada una declara audiencia, pregunta y decisión"],
  ["5 filtros globales", "Tipo, año, género, idioma y país en todas las vistas"],
  ["Drill-down", "Clic en una burbuja → títulos del género"],
  ["Títulos dinámicos", "El hallazgo se recalcula con cada filtro"],
  ["Exportación", "PNG de cada gráfico y CSV del alcance filtrado"],
];
feats.forEach(([a, b], i) => {
  const y = 1.55 + i * 0.97;
  numero(s, 9.4, y + 0.05, String(i + 1), K.focoSoft, K.foco, 0.45);
  s.addText([{ text: a, options: { bold: true, fontSize: 15, color: K.ink, breakLine: true } }, { text: b, options: { fontSize: 12, color: K.ink2 } }],
    { x: 9.98, y, w: 2.75, h: 0.9, margin: 0, valign: "top", isTextBox: true, objectName: name("feat") });
});
s.addNotes("[4:30–5:15] Todo vive en un dashboard en Streamlit y Plotly. Cada página abre con su audiencia, la pregunta que responde y la decisión que habilita. Los filtros se propagan a todo y los títulos se recalculan, así el hallazgo siempre es verdadero para lo que se está mirando. Demostración breve: filtrar Serie y hacer clic en Telenovela para ver los títulos.");

// ================================================================== 8. JUSTIFICACIÓN TÉCNICA (IE26) — evaluación crítica: 3 min
pres.addSection({ title: SEC2.c });
s = contenido("Por qué estos gráficos: forma según dato, pregunta y audiencia", SEC2.c);
tablaSlide(s, [
  ["Barras divergentes", "Diferencia con signo (pp)", "Se lee desde 0; color solo en oportunidades (preatentivo)", "Barras agrupadas: obliga a restar"],
  ["Burbujas en cuadrantes", "3 variables cuantitativas", "Cuadrantes con nombre de decisión", "Tabla: oculta relaciones"],
  ["Ranking + anotación", "Popularidad y oferta por país", "Se lee sin escala log: largo = popularidad, texto = oferta", "Dispersión log (la simplificamos)"],
  ["Treemap", "Parte-todo jerárquico", "Peso de 30+ géneros en un vistazo", "Torta: ilegible > 5 partes"],
  ["Áreas 100% (3 grupos)", "Composición en el tiempo", "'De cada 10 estrenos, 2 son Drama'", "6 bandas: difícil de leer"],
  ["Small multiples", "2 métricas de escala distinta", "Evita el eje dual (anti-patrón)", "Gráfico de doble eje"],
], ["Gráfico", "Tipo de dato", "Por qué", "Alternativa descartada"], { colW: [2.6, 2.9, 4.1, 2.5] });
s.addText("Color: película azul, serie naranjo en todo el proyecto · paleta validada para daltonismo · un color de foco sobre gris · sin 3D ni ejes duales",
  { x: 0.6, y: 6.25, w: 12.1, h: 0.5, fontSize: 13, color: K.ink2, italic: true, margin: 0, isTextBox: true, objectName: name("color") });
s.addNotes("[5:15–6:00] Cada forma se eligió por el tipo de dato y la pregunta, no por estética. Barras divergentes porque la brecha tiene signo; burbujas en cuadrantes porque son tres variables y los cuadrantes se traducen en decisiones; escala logarítmica porque la popularidad es muy asimétrica; áreas al 100% porque el volumen es fijo por la muestra. El color se asignó al final: el mismo significado en todos los gráficos y validado para daltonismo.");

// ================================================================== 9. FORTALEZAS (IE31)
s = contenido("Fortalezas, con evidencia", SEC2.c);
const fort = [
  ["Enfocado en una decisión", "Las 7 páginas responden '¿qué priorizar?'; cada una declara audiencia, pregunta y decisión."],
  ["Mensajes siempre verdaderos", "Los títulos se calculan desde los datos: al filtrar 'Serie' o 'México', el hallazgo se actualiza."],
  ["Accesible y legible", "Paleta validada (ΔE ≥ 9 en daltonismo), identidad nunca solo por color, formato numérico chileno."],
  ["Métricas robustas", "Mediana, popularidad relativa por tipo, ≥ 10 votos, nota bayesiana, ROI mediano: los extremos no distorsionan."],
];
fort.forEach(([a, b], i) => {
  const x = 0.6 + (i % 2) * 6.15, y = 1.65 + Math.floor(i / 2) * 2.45;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 5.95, h: 2.2, fill: { color: K.white }, line: { color: K.grid, width: 1 }, rectRadius: 0.1, objectName: name("fort") });
  numero(s, x + 0.3, y + 0.3, "✓", K.movie, K.white, 0.5);
  s.addText(a, { x: x + 1.0, y: y + 0.28, w: 4.7, h: 0.55, fontSize: 19, bold: true, color: K.ink, margin: 0, valign: "middle", isTextBox: true, objectName: name("fa") });
  s.addText(b, { x: x + 1.0, y: y + 0.9, w: 4.7, h: 1.15, fontSize: 17, color: K.ink2, margin: 0, valign: "top", isTextBox: true, objectName: name("fb") });
});
s.addNotes("[6:00–6:40] Fortalezas, cada una con evidencia: está enfocada en una decisión; los mensajes se recalculan y nunca quedan falsos al filtrar; es accesible, con una paleta validada computacionalmente para daltonismo; y usa métricas robustas que no se distorsionan por valores extremos.");

// ================================================================== 10. LIMITACIONES (IE32)
s = contenido("Limitaciones, sesgos y riesgos, con su mitigación", SEC2.c);
tablaSlide(s, [
  ["Popularidad TMDB ≠ consumo propio", "Sesgo de fuente: interés global, no reproducciones", "Uso como proxy relativo; no se afirma impacto en retención"],
  ["Sesgo de recencia", "Estrenos 2024–25 inflados; 2025 con ~8% de votos suficientes", "2025 marcado incompleto; popularidad relativa dentro del tipo"],
  ["Supervivencia financiera", "Solo 22% de películas con finanzas (las más exitosas)", "Universo explícito; ROI mediano; no extrapolar"],
  ["Muestra de 1.000 títulos/año", "No mide crecimiento real del catálogo", "Se analiza composición, no volumen"],
  ["Faltantes en series", "69% sin director, 11% sin país", "Advertido en gráficos; análisis por tipo separado"],
  ["Sin clasificación etaria", "KPIs de clasificación del caso no calculables", "Reportado; corrección en la fuente (mejora 2)"],
], ["Limitación / sesgo", "Riesgo para la decisión", "Mitigación"], { colW: [3.4, 4.5, 4.2] });
s.addNotes("[6:40–7:30] Lo que limita el uso. El sesgo principal es de fuente: la popularidad mide interés global, no consumo de nuestros usuarios; por eso la usamos como proxy relativo y no prometemos impacto en retención. Hay sesgo de recencia y de supervivencia financiera, y faltantes en series. Cada riesgo tiene una mitigación aplicada en el dashboard.");

// ================================================================== 11. MEJORAS (IE33) - matriz impacto/esfuerzo
s = contenido("Mejoras priorizadas por impacto y esfuerzo", SEC2.c);
const MX = 0.9, MY = 1.75, MW = 7.4, MH = 4.6;
[[0, 0, K.focoSoft], [1, 0, K.white], [0, 1, K.white], [1, 1, K.white]].forEach(([cx, cy, f]) =>
  s.addShape(pres.shapes.RECTANGLE, { x: MX + cx * MW / 2, y: MY + cy * MH / 2, w: MW / 2, h: MH / 2, fill: { color: f }, line: { color: K.grid, width: 1 }, objectName: name("q") }));
s.addText("Impacto en la decisión →", { x: -1.75, y: MY + MH / 2 - 0.2, w: 4.6, h: 0.4, fontSize: 12, color: K.ink2, rotate: 270, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: name("eje") });
s.addText("Esfuerzo →", { x: MX, y: MY + MH + 0.05, w: MW, h: 0.35, fontSize: 12, color: K.ink2, align: "center", margin: 0, isTextBox: true, objectName: name("eje") });
s.addText("HACER PRIMERO", { x: MX + 0.15, y: MY + 0.1, w: 3, h: 0.3, fontSize: 11, bold: true, color: K.foco, margin: 0, isTextBox: true, objectName: name("ql") });
s.addText("PLANIFICAR", { x: MX + MW / 2 + 0.15, y: MY + 0.1, w: 3, h: 0.3, fontSize: 11, bold: true, color: K.muted, margin: 0, isTextBox: true, objectName: name("ql") });
s.addText("RÁPIDAS", { x: MX + 0.15, y: MY + MH / 2 + 0.1, w: 3, h: 0.3, fontSize: 11, bold: true, color: K.muted, margin: 0, isTextBox: true, objectName: name("ql") });
const pts = [["1", 0.8, 0.22], ["2", 0.22, 0.28], ["3", 0.62, 0.42], ["4", 0.55, 0.68], ["5", 0.2, 0.82]];
pts.forEach(([t, fx, fy]) => numero(s, MX + fx * MW - 0.25, MY + fy * MH - 0.25, t, K.foco, K.white, 0.5));
const mej = [
  ["Integrar datos de reproducciones y suscripciones", "Mayor impacto · alto esfuerzo · requiere fuentes de usuarios"],
  ["Corregir clasificación etaria y duración", "Habilita KPIs del caso · bajo esfuerzo"],
  ["Costo de licencia por título", "El retorno real de StreamView no es la taquilla"],
  ["Vista 'lista de compra' de candidatos", "Del diagnóstico a la acción"],
  ["Modo oscuro y texturas", "Accesibilidad extendida · inmediato"],
];
mej.forEach(([a, b], i) => {
  const y = 1.7 + i * 1.0;
  numero(s, 8.75, y + 0.04, String(i + 1), K.focoSoft, K.foco, 0.42);
  s.addText([{ text: a, options: { bold: true, fontSize: 14, color: K.ink, breakLine: true } }, { text: b, options: { fontSize: 12, color: K.ink2 } }],
    { x: 9.3, y, w: 3.45, h: 0.95, margin: 0, valign: "top", isTextBox: true, objectName: name("mej") });
});
s.addNotes("[7:30–8:15] Las mejoras están priorizadas en una matriz de impacto y esfuerzo. Hacer primero: corregir la clasificación etaria y la duración en la fuente, que es barato y habilita KPIs del caso. La de mayor impacto es integrar datos de reproducciones y suscripciones, pero requiere que la empresa entregue esas fuentes. Luego costo de licencia y una vista de lista de compra.");

// ================================================================== 12. RECOMENDACIONES (IE35) — 2 min
pres.addSection({ title: SEC2.d });
s = pres.addSlide({ masterName: "CIERRE", sectionTitle: SEC2.d });
s.addText("Recomendaciones para la Gerencia de Contenidos", { placeholder: "title" });
const recs = [
  ["Adquirir más Animación y Familiar", "Evidencia: popularidad relativa 65, nota 6,95, ROI 2,2–2,3x, solo 4,3% de la oferta"],
  ["Crecer en contenido latinoamericano", "Evidencia: español 5,1% del catálogo con popularidad 58 (típico 50); Telenovela +3,4 pp; México, Chile y Colombia"],
  ["Reducir la adquisición incremental de Drama", "Evidencia: −5,1 pp de brecha y ROI 1,3x; libera presupuesto para 1 y 2"],
  ["Mantener un pipeline asiático de calidad", "Evidencia: Japón (7,22) y Corea del Sur (7,10), mejor calificación por país"],
  ["Portafolio de películas balanceado", "Evidencia: blockbusters 85% rentables; joyas de bajo costo con ROI 20–95x"],
];
recs.forEach(([a, b], i) => {
  const y = 1.6 + i * 1.0;
  numero(s, 0.6, y + 0.1, String(i + 1), K.foco, K.white, 0.6);
  s.addText([{ text: a, options: { bold: true, fontSize: 19, color: K.white, breakLine: true } }, { text: b, options: { fontSize: 14, color: "D9D6F5" } }],
    { x: 1.45, y, w: 11.2, h: 0.9, margin: 0, valign: "middle", isTextBox: true, objectName: name("rec") });
});
s.addNotes("[8:15–9:15] Cinco recomendaciones, cada una con evidencia medida en los datos. Uno: más Animación y Familiar. Dos: crecer en contenido latinoamericano, nuestro mercado sub-representado. Tres: reducir la adquisición incremental de Drama para financiar lo anterior sin aumentar el gasto. Cuatro: mantener el contenido asiático de calidad. Cinco: un portafolio de películas balanceado.");

// ================================================================== 13. IMPACTO ESPERADO (IE36)
s = contenido("Impacto esperado y cómo lo vamos a medir", SEC2.d);
tablaSlide(s, [
  ["1 · Animación y Familiar", "Más títulos en el cuadrante de oportunidad", "% del catálogo en Animación/Familiar", "18,6%"],
  ["2 · Latinoamérica", "Catálogo más relevante para el mercado propio", "% del catálogo en español/portugués", "6,7%"],
  ["3 · Menos Drama", "Presupuesto reasignado sin gasto adicional", "Brecha de Drama en películas", "−5,1 pp"],
  ["4 · Asia de calidad", "Mantener la calificación del catálogo", "Nota media Japón + Corea del Sur", "7,18"],
  ["5 · Portafolio balanceado", "Menos películas que no recuperan inversión", "% de películas con ROI ≥ 1", "63%"],
], ["Recomendación", "Impacto esperado (proyección)", "Indicador de seguimiento", "Línea base hoy"], { colW: [2.9, 4.0, 3.6, 1.6] });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.35, w: 12.1, h: 1.2, fill: { color: K.focoSoft }, line: { color: K.focoSoft }, rectRadius: 0.08, objectName: name("aviso") });
s.addText([{ text: "Esperado ≠ medido. ", options: { bold: true, color: K.ink, fontSize: 15 } },
  { text: "La evidencia ya está medida en el catálogo; el impacto es una proyección. Se verificará con estos indicadores en el dashboard en cada actualización, comparando contra la línea base. No se proyecta impacto en retención ni engagement.", options: { color: K.ink2, fontSize: 14 } }],
  { x: 0.85, y: 5.4, w: 11.6, h: 1.1, margin: 0, valign: "middle", isTextBox: true, objectName: name("avisotxt") });
s.addNotes("[9:15–10:00] Distinguimos impacto esperado de resultados medidos. La evidencia de las recomendaciones ya está medida; el impacto es una proyección, y para cada recomendación definimos un indicador con su línea base de hoy, que el dashboard permite seguir en cada actualización del catálogo. No proyectamos retención ni engagement porque no tenemos datos de usuarios. Quedamos atentos a sus preguntas.");

// ================================================================== ANEXO (respaldo para preguntas)
pres.addSection({ title: SEC2.e });
s = contenido("Anexo A · El catálogo se concentra en Drama y en inglés", SEC2.e);
grafico(s, "slides/01_treemap_generos.png", "Treemap de títulos por tipo y género: Drama y Comedia ocupan las mayores áreas en películas y series");
stat(s, 1.55, "23%", "de las asignaciones de género son Drama", K.ink);
stat(s, 3.0, "44%", "del catálogo está en inglés; español 5,1%", K.ink);
stat(s, 4.45, "29%", "de las producciones vienen de Estados Unidos", K.ink);
s.addNotes("Respaldo para preguntas sobre composición del catálogo. Treemap: parte-todo jerárquico, el área es la cantidad de títulos.");

s = contenido("Anexo B · Popularidad y calidad casi no se relacionan", SEC2.e);
grafico(s, "slides/11_pop_vs_nota.png", "Dispersión popularidad (escala log) versus calificación: nube sin tendencia clara, correlación débil");
stat(s, 1.55, "0,23", "correlación popularidad–calificación en películas: débil (0,17 en series)");
stat(s, 3.0, "7,29", "calificación media de series vs 6,35 de películas", K.serie);
stat(s, 4.45, "3,3x", "popularidad mediana de series vs películas (índices por tipo)", K.serie);
s.addNotes("Respaldo: por qué la matriz usa dos ejes. Spearman porque es robusta a la asimetría de la popularidad.");

s = contenido("Anexo C · Riesgo financiero de las películas", SEC2.e);
grafico(s, "slides/17_roi_genero.png", "Barras horizontales de ROI mediano por género de película", 0.6, 1.55, 8.0, 4.1);
s.addChart(pres.charts.BAR, [{ name: "% rentables", labels: ["< 5M", "5–20M", "20–60M", "> 60M"], values: [58, 56, 64, 85] }], {
  x: 8.9, y: 1.55, w: 3.85, h: 3.4, barDir: "col", chartColors: [K.movie],
  showTitle: true, title: "% de películas rentables por presupuesto (USD)", titleFontSize: 12, titleColor: K.ink, titleFontFace: "+mn-lt",
  showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '0"%"', dataLabelFontSize: 12, dataLabelColor: K.ink2, dataLabelFontFace: "+mn-lt",
  catAxisLabelColor: K.ink2, catAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt",
  valAxisHidden: true, valAxisMaxVal: 100, valAxisMinVal: 0, valGridLine: { style: "none" }, catGridLine: { style: "none" },
  catAxisLineShow: true, showLegend: false, barGapWidthPct: 45, objectName: name("chart_tramo"),
  altText: "Gráfico de columnas: 58% de películas rentables bajo 5M, 56% entre 5 y 20M, 64% entre 20 y 60M y 85% sobre 60M",
});
s.addText([{ text: "37% ", options: { bold: true, color: K.ink, fontSize: 22 } }, { text: "de las películas no recupera su inversión (3.500 películas con datos válidos).", options: { color: K.ink2, fontSize: 14 } }],
  { x: 8.95, y: 5.1, w: 3.75, h: 1.0, margin: 0, valign: "top", isTextBox: true, objectName: name("nota") });
s.addNotes("Respaldo financiero: ROI mediano (no promedio) por los éxitos extremos. Solo películas con presupuesto ≥ USD 100 mil e ingresos > 0 (reglas 3 y 6).");

// ------------------------------------------------------------------ escribir + tema
(async () => {
  await pres.writeFile({ fileName: OUT });
  try {
    const at = process.env.APPLY_THEME_JS;
    if (at) {
      const { applyTheme } = require(at);
      await applyTheme(OUT, THEME);
      console.log("tema aplicado");
    }
  } catch (e) { console.log("tema no aplicado:", e.message); }
  console.log("ok", OUT);
})();
