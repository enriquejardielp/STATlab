"""
STATlab - Análisis Estadístico con Lenguaje Natural
Motor estadístico completo. IA local con Ollama.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from io import BytesIO
import json
import ollama

# -------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y ESTILOS
# -------------------------------------------------------------------
st.set_page_config(
    page_title="STATlab",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
    
    :root {
        --bg-primary: #FAFAFA;
        --bg-secondary: #FFFFFF;
        --bg-sidebar: #F5F5F5;
        --text-primary: #1A1A1A;
        --text-secondary: #6B7280;
        --accent: #2563EB;
        --accent-hover: #1D4ED8;
        --border: #E5E7EB;
        --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
        --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07);
        --radius-sm: 8px;
        --radius-md: 12px;
    }
    
    .stApp { background-color: var(--bg-primary); }
    
    [data-testid="stSidebar"] {
        background-color: var(--bg-sidebar);
        border-right: 1px solid var(--border);
    }
    
    h1, h2, h3 { font-weight: 600; letter-spacing: -0.02em; color: var(--text-primary); }
    h1 { font-size: 1.75rem; margin-bottom: 0.5rem; }
    h3 { font-size: 1.1rem; color: var(--text-secondary); font-weight: 500; }
    
    [data-testid="stMetric"] {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1rem;
        box-shadow: var(--shadow-sm);
    }
    
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        overflow: hidden;
        box-shadow: var(--shadow-sm);
    }
    
    .stButton > button {
        font-weight: 500;
        border-radius: var(--radius-sm);
        padding: 0.5rem 1.25rem;
        transition: all 0.2s ease;
        border: 1px solid var(--border);
        background-color: var(--bg-secondary);
        color: var(--text-primary);
    }
    
    .stButton > button:hover {
        border-color: var(--accent);
        color: var(--accent);
        background-color: #F0F5FF;
    }
    
    .stButton > button[kind="primary"] {
        background-color: var(--accent);
        color: white;
        border: none;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: var(--accent-hover);
    }
    
    [data-testid="stChatMessage"] {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        box-shadow: var(--shadow-sm);
    }
    
    hr { border-color: var(--border); margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# FUNCIONES AUXILIARES
# -------------------------------------------------------------------
def cargar_datos(archivo):
    """Carga un archivo CSV o Excel."""
    if archivo.name.endswith('.csv'):
        return pd.read_csv(archivo)
    else:
        return pd.read_excel(archivo)

def obtener_info_dataset(df):
    """Resumen ligero del dataset para la IA."""
    info = {
        "filas": len(df),
        "columnas": list(df.columns),
        "tipos": {col: str(df[col].dtype) for col in df.columns},
        "valores_unicos": {col: int(df[col].nunique()) for col in df.columns},
    }
    # Muestra ligera
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
            datos = df[col].dropna()
            info["tipos"][col] = "numérica"
            info[f"stats_{col}"] = f"min={datos.min():.2f}, max={datos.max():.2f}, media={datos.mean():.2f}"
            info[f"ejemplos_{col}"] = datos.head(3).tolist()
        else:
            datos = df[col].dropna()
            info["tipos"][col] = "categórica"
            info[f"categorias_{col}"] = datos.unique()[:10].tolist()
    return info

# -------------------------------------------------------------------
# MOTOR ESTADÍSTICO COMPLETO
# -------------------------------------------------------------------
def ejecutar_test(accion, columnas, df, params=None):
    """Ejecuta cualquier test estadístico."""
    if params is None:
        params = {}
    
    # --- DESCRIPTIVOS ---
    if accion == "descriptivos":
        col = columnas[0]
        datos = df[col].dropna()
        q1, q3 = datos.quantile(0.25), datos.quantile(0.75)
        return {
            "analisis": f"Descriptivos de {col}",
            "n": len(datos), "media": round(float(datos.mean()), 4),
            "mediana": round(float(datos.median()), 4),
            "desviacion": round(float(datos.std()), 4),
            "min": round(float(datos.min()), 4), "max": round(float(datos.max()), 4),
            "q1": round(float(q1), 4), "q3": round(float(q3), 4),
            "iqr": round(float(q3 - q1), 4),
            "asimetria": round(float(datos.skew()), 4),
            "curtosis": round(float(datos.kurtosis()), 4)
        }
    
    elif accion == "frecuencia_categorica":
        col = columnas[0]
        datos = df[col].dropna()
        conteo = datos.value_counts()
        return {
            "analisis": f"Frecuencias de {col}",
            "total": len(datos),
            "categorias": [{"categoria": str(c), "n": int(conteo[c]), 
                          "pct": round(float(conteo[c]/len(datos)*100), 1)} 
                         for c in conteo.index[:15]]
        }
    
    # --- NORMALIDAD ---
    elif accion == "normalidad":
        col = columnas[0]
        datos = df[col].dropna()
        if len(datos) <= 5000:
            stat, p = stats.shapiro(datos)
            test = "Shapiro-Wilk"
        else:
            stat, p = stats.kstest(datos, 'norm', args=(datos.mean(), datos.std()))
            test = "Kolmogorov-Smirnov"
        return {
            "analisis": f"Normalidad de {col}",
            "test": test, "estadistico": round(float(stat), 4),
            "p_valor": round(float(p), 4),
            "es_normal": p > 0.05
        }
    
    # --- COMPARACIÓN 2 GRUPOS ---
    elif accion == "ttest_independiente":
        col_num, col_cat = columnas[0], columnas[1]
        grupos = df[col_cat].dropna().unique()
        if len(grupos) != 2:
            return {"error": f"Se necesitan 2 grupos. Hay {len(grupos)}."}
        g1 = df[df[col_cat] == grupos[0]][col_num].dropna()
        g2 = df[df[col_cat] == grupos[1]][col_num].dropna()
        stat, p = stats.ttest_ind(g1, g2)
        return {
            "analisis": f"t-test: {col_num} por {col_cat}",
            "media_1": round(float(g1.mean()), 4),
            "media_2": round(float(g2.mean()), 4),
            "t": round(float(stat), 4), "p_valor": round(float(p), 4),
            "significativo": p <= 0.05
        }
    
    elif accion == "mann_whitney":
        col_num, col_cat = columnas[0], columnas[1]
        grupos = df[col_cat].dropna().unique()
        if len(grupos) != 2:
            return {"error": f"Se necesitan 2 grupos."}
        g1 = df[df[col_cat] == grupos[0]][col_num].dropna()
        g2 = df[df[col_cat] == grupos[1]][col_num].dropna()
        stat, p = stats.mannwhitneyu(g1, g2, alternative='two-sided')
        return {
            "analisis": f"Mann-Whitney: {col_num} por {col_cat}",
            "mediana_1": round(float(g1.median()), 4),
            "mediana_2": round(float(g2.median()), 4),
            "U": round(float(stat), 4), "p_valor": round(float(p), 4),
            "significativo": p <= 0.05
        }
    
    # --- COMPARACIÓN 3+ GRUPOS ---
    elif accion == "anova":
        col_num, col_cat = columnas[0], columnas[1]
        grupos = df[col_cat].dropna().unique()
        muestras = [df[df[col_cat] == g][col_num].dropna().values for g in grupos]
        f_stat, p = stats.f_oneway(*muestras)
        return {
            "analisis": f"ANOVA: {col_num} por {col_cat}",
            "grupos": [str(g) for g in grupos],
            "F": round(float(f_stat), 4), "p_valor": round(float(p), 4),
            "significativo": p <= 0.05
        }
    
    elif accion == "kruskal_wallis":
        col_num, col_cat = columnas[0], columnas[1]
        grupos = df[col_cat].dropna().unique()
        muestras = [df[df[col_cat] == g][col_num].dropna().values for g in grupos]
        h_stat, p = stats.kruskal(*muestras)
        return {
            "analisis": f"Kruskal-Wallis: {col_num} por {col_cat}",
            "H": round(float(h_stat), 4), "p_valor": round(float(p), 4),
            "significativo": p <= 0.05
        }
    
    # --- ASOCIACIÓN CATEGÓRICAS ---
    elif accion == "chi_cuadrado":
        col1, col2 = columnas[0], columnas[1]
        tabla = pd.crosstab(df[col1], df[col2])
        chi2, p, dof, _ = stats.chi2_contingency(tabla)
        return {
            "analisis": f"Chi-cuadrado: {col1} vs {col2}",
            "chi2": round(float(chi2), 4), "p_valor": round(float(p), 4),
            "gl": int(dof), "significativo": p <= 0.05
        }
    
    elif accion == "fisher_exacto":
        col1, col2 = columnas[0], columnas[1]
        tabla = pd.crosstab(df[col1], df[col2])
        if tabla.shape == (2, 2):
            or_val, p = stats.fisher_exact(tabla)
            return {
                "analisis": f"Fisher: {col1} vs {col2}",
                "odds_ratio": round(float(or_val), 4),
                "p_valor": round(float(p), 4), "significativo": p <= 0.05
            }
        return {"error": "Fisher requiere tabla 2x2."}
    
    # --- CORRELACIÓN ---
    elif accion == "correlacion_pearson":
        col1, col2 = columnas[0], columnas[1]
        mask = df[[col1, col2]].dropna().index
        r, p = stats.pearsonr(df.loc[mask, col1], df.loc[mask, col2])
        return {
            "analisis": f"Pearson: {col1} vs {col2}",
            "r": round(float(r), 4), "r2": round(float(r**2), 4),
            "p_valor": round(float(p), 4), "significativo": p <= 0.05
        }
    
    elif accion == "correlacion_spearman":
        col1, col2 = columnas[0], columnas[1]
        mask = df[[col1, col2]].dropna().index
        rho, p = stats.spearmanr(df.loc[mask, col1], df.loc[mask, col2])
        return {
            "analisis": f"Spearman: {col1} vs {col2}",
            "rho": round(float(rho), 4), "p_valor": round(float(p), 4),
            "significativo": p <= 0.05
        }
    
    # --- REGRESIÓN ---
    elif accion == "regresion_lineal":
        col_y, col_x = columnas[0], columnas[1]
        mask = df[[col_x, col_y]].dropna().index
        x, y = df.loc[mask, col_x], df.loc[mask, col_y]
        slope, intercept, r_val, p_val, std_err = stats.linregress(x, y)
        return {
            "analisis": f"Regresión: {col_y} ~ {col_x}",
            "ecuacion": f"Y = {intercept:.4f} + {slope:.4f}*X",
            "r2": round(float(r_val**2), 4), "p_valor": round(float(p_val), 4),
            "significativo": p_val <= 0.05
        }
    
    # --- GRÁFICOS ---
    elif accion == "histograma":
        col = columnas[0]
        fig = px.histogram(df[col].dropna(), nbins=30, title=f"Distribución de {col}",
                          color_discrete_sequence=["#2563EB"])
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", font_family="Inter")
        return {"tipo": "grafico", "fig": fig}
    
    elif accion == "boxplot":
        col_num = columnas[0]
        col_cat = columnas[1] if len(columnas) > 1 else None
        if col_cat:
            fig = px.box(df, x=col_cat, y=col_num, title=f"Boxplot de {col_num} por {col_cat}",
                        color_discrete_sequence=["#2563EB"])
        else:
            fig = px.box(df, y=col_num, title=f"Boxplot de {col_num}",
                        color_discrete_sequence=["#2563EB"])
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", font_family="Inter")
        return {"tipo": "grafico", "fig": fig}
    
    elif accion == "dispersion":
        col_x, col_y = columnas[0], columnas[1]
        fig = px.scatter(df, x=col_x, y=col_y, trendline='ols',
                        title=f"{col_y} vs {col_x}")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", font_family="Inter")
        return {"tipo": "grafico", "fig": fig}
    
    elif accion == "qq_plot":
        col = columnas[0]
        datos = df[col].dropna().sort_values()
        teoricos = stats.norm.ppf((np.arange(1, len(datos)+1) - 0.5) / len(datos))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=teoricos, y=datos, mode='markers',
                                marker=dict(color="#2563EB", size=4)))
        fig.add_trace(go.Scatter(x=[teoricos.min(), teoricos.max()],
                                y=[teoricos.min(), teoricos.max()],
                                mode='lines', line=dict(dash='dash', color='gray')))
        fig.update_layout(title=f"Q-Q Plot: {col}", plot_bgcolor="white",
                         paper_bgcolor="white", font_family="Inter")
        return {"tipo": "grafico", "fig": fig}
    
    elif accion == "barras":
        col = columnas[0]
        datos = df[col].value_counts().head(20)
        fig = px.bar(x=datos.index, y=datos.values, title=f"Frecuencia de {col}",
                    labels={'x': col, 'y': 'Frecuencia'},
                    color_discrete_sequence=["#2563EB"])
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", font_family="Inter")
        return {"tipo": "grafico", "fig": fig}
    
    elif accion == "torta":
        col = columnas[0]
        datos = df[col].value_counts()
        fig = px.pie(values=datos.values, names=datos.index, title=f"Proporción de {col}")
        fig.update_layout(font_family="Inter")
        return {"tipo": "grafico", "fig": fig}
    
    elif accion == "heatmap_correlacion":
        cols_num = df.select_dtypes(include='number').columns
        if len(cols_num) < 2:
            return {"error": "Se necesitan al menos 2 variables numéricas"}
        corr = df[cols_num].corr()
        fig = px.imshow(corr, text_auto='.2f', aspect="auto",
                       title="Matriz de correlaciones", color_continuous_scale="Blues")
        fig.update_layout(font_family="Inter")
        return {"tipo": "grafico", "fig": fig}
    
    return {"error": f"Acción '{accion}' no implementada"}


# -------------------------------------------------------------------
# SIDEBAR
# -------------------------------------------------------------------
with st.sidebar:
    st.markdown("## STATlab")
    st.markdown("*Análisis estadístico — IA local*")
    
    st.divider()
    
    st.markdown("### Datos")
    archivo = st.file_uploader(
        "Cargar archivo de datos",
        type=["csv", "xlsx"],
        help="Formatos soportados: CSV y Excel (.xlsx)"
    )
    
    if archivo is not None:
        st.caption(f"Cargado: {archivo.name}")
    
    st.divider()
    
    # Selector de modelo Ollama
    st.markdown("### Modelo local")
    
    try:
        modelos_disponibles = ollama.list()
        nombres_modelos = [m['name'] for m in modelos_disponibles['models']]
    except:
        nombres_modelos = ["llama3.2"]
    
    modelo_seleccionado = st.selectbox(
        "Modelo Ollama",
        nombres_modelos,
        help="Modelo de IA local a utilizar"
    )
    st.caption(f"Usando: {modelo_seleccionado}")
    
    st.divider()
    
    st.markdown("### Sugerencias")
    for s in [
        "Descriptivos de la edad",
        "Es normal la distribucion del peso?",
        "Compara el colesterol entre fumadores y no fumadores",
        "Hay correlacion entre edad y presion arterial?",
        "Muestra un histograma del IMC",
        "Haz un boxplot del peso por sexo",
        "ANOVA de la glucosa por grupo",
        "Chi-cuadrado entre sexo y grupo sanguineo",
        "Regresion lineal: colesterol ~ edad",
        "Matriz de correlaciones",
        "Q-Q plot de la presion sistolica",
    ]:
        st.caption(s)

# -------------------------------------------------------------------
# ÁREA PRINCIPAL
# -------------------------------------------------------------------
st.title("STATlab")
st.caption("Análisis estadístico con inteligencia artificial local")

if archivo is not None:
    try:
        df = cargar_datos(archivo)
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.stop()
    
    # Guardar en sesión
    if "df" not in st.session_state or st.session_state.get("archivo_nombre") != archivo.name:
        st.session_state.df = df
        st.session_state.archivo_nombre = archivo.name
        st.session_state.mensajes = []
        st.session_state.mensajes.append({
            "rol": "assistant",
            "contenido": (
                f"Archivo **{archivo.name}** cargado.  \n"
                f"**{len(df)}** registros, **{len(df.columns)}** variables.  \n"
                f"Columnas: {', '.join(df.columns)}.  \n"
                f"Puedes pedirme cualquier análisis estadístico."
            )
        })
    
    # Mostrar mensajes
    for msg in st.session_state.mensajes:
        with st.chat_message(msg["rol"]):
            st.write(msg["contenido"])
    
    # Input
    pregunta = st.chat_input("Describe el análisis que necesitas...")
    
    if pregunta:
        st.session_state.mensajes.append({"rol": "user", "contenido": pregunta})
        
        with st.chat_message("user"):
            st.write(pregunta)
        
        with st.chat_message("assistant"):
            with st.spinner("Procesando con IA local..."):
                try:
                    info = obtener_info_dataset(st.session_state.df)
                    
                    prompt_sistema = f"""
Eres un bioestadístico. Analiza este dataset:
- Filas: {info['filas']}
- Columnas y tipos: {json.dumps({col: info['tipos'][col] for col in info['columnas']})}

Responde ÚNICAMENTE en JSON sin texto adicional:
{{"respuesta_usuario": "tu respuesta clara y profesional", "accion": "nombre_accion", "columnas": ["col1", "col2"], "params": {{}}}}

Acciones disponibles:
- descriptivos, frecuencia_categorica: para 1 variable
- normalidad: prueba de normalidad
- ttest_independiente, mann_whitney: comparar numérica entre 2 grupos
- anova, kruskal_wallis: comparar numérica entre 3+ grupos
- chi_cuadrado, fisher_exacto: asociación entre categóricas
- correlacion_pearson, correlacion_spearman: relación entre 2 numéricas
- regresion_lineal: modelo Y ~ X
- histograma, boxplot, dispersion, qq_plot, barras, torta, heatmap_correlacion: gráficos
- solo_texto: preguntas conceptuales

Usa nombres EXACTOS de columna. Para gráficos, accion debe ser el tipo de gráfico.
"""

                    respuesta = ollama.chat(
                        model=modelo_seleccionado,
                        messages=[
                            {"role": "system", "content": prompt_sistema},
                            {"role": "user", "content": pregunta}
                        ]
                    )
                    
                    texto = respuesta['message']['content'].strip()
                    
                    # Extraer JSON
                    if "```json" in texto:
                        texto = texto.split("```json")[1].split("```")[0].strip()
                    elif "```" in texto:
                        texto = texto.split("```")[1].split("```")[0].strip()
                    
                    datos_json = json.loads(texto)
                    
                    # Mostrar respuesta
                    st.write(datos_json.get("respuesta_usuario", ""))
                    
                    # Ejecutar acción
                    accion = datos_json.get("accion", "solo_texto")
                    columnas = datos_json.get("columnas", [])
                    params = datos_json.get("params", {})
                    
                    if accion != "solo_texto":
                        with st.spinner("Ejecutando análisis..."):
                            resultado = ejecutar_test(accion, columnas, st.session_state.df, params)
                            
                            if resultado.get("tipo") == "grafico":
                                st.plotly_chart(resultado["fig"], use_container_width=True)
                            elif "error" in resultado:
                                st.warning(resultado["error"])
                            else:
                                st.json(resultado)
                    
                    st.session_state.mensajes.append({
                        "rol": "assistant",
                        "contenido": datos_json.get("respuesta_usuario", "")
                    })
                
                except json.JSONDecodeError:
                    st.error("La IA no devolvió un formato válido. Intenta reformular tu pregunta.")
                    st.caption(f"Respuesta recibida: {texto[:300]}...")
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.caption("Asegúrate de que Ollama está abierto y el modelo descargado.")

else:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%);
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 2.5rem;
        margin-top: 2rem;
    ">
        <h2 style="margin-top:0; font-weight:600;">Analisis estadistico inteligente</h2>
        <p style="color:#6B7280; font-size:1rem; max-width:600px;">
            Carga un archivo de datos y describe el analisis que necesitas.
            La IA local (Ollama) interpretara tu pregunta, ejecutara la prueba
            estadistica adecuada y te mostrara los resultados.
        </p>
        <p style="color:#6B7280; font-size:0.9rem;">
            Todo funciona en tu ordenador, sin enviar datos a internet.
        </p>
    </div>
    """, unsafe_allow_html=True)
