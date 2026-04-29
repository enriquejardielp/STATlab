"""
STATlab - Análisis Estadístico con Lenguaje Natural
Interfaz profesional minimalista. Motor estadístico completo.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from io import BytesIO
import json
import os
import google.generativeai as genai

# -------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y ESTILOS
# -------------------------------------------------------------------
st.set_page_config(
    page_title="STATlab",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS profesional
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
        --success: #059669;
        --warning: #D97706;
        --error: #DC2626;
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
    """Genera un resumen completo del dataset para la IA."""
    info = {
        "filas": len(df),
        "columnas": list(df.columns),
        "tipos": {},
        "valores_unicos": {},
        "nulos": {},
        "muestra": {}
    }
    
    for col in df.columns:
        dtype = str(df[col].dtype)
        info["tipos"][col] = dtype
        info["valores_unicos"][col] = int(df[col].nunique())
        info["nulos"][col] = int(df[col].isna().sum())
        
        if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
            datos = df[col].dropna()
            info["muestra"][col] = {
                "tipo": "numérica",
                "min": float(datos.min()) if len(datos) > 0 else None,
                "max": float(datos.max()) if len(datos) > 0 else None,
                "media": float(datos.mean()) if len(datos) > 0 else None,
                "mediana": float(datos.median()) if len(datos) > 0 else None,
                "n_unicos": int(datos.nunique()),
                "ejemplos": datos.head(5).tolist() if len(datos) > 0 else []
            }
        else:
            datos = df[col].dropna()
            info["muestra"][col] = {
                "tipo": "categórica",
                "categorias": datos.unique()[:15].tolist() if len(datos) > 0 else [],
                "frecuencias": datos.value_counts().head(10).to_dict() if len(datos) > 0 else {},
                "ejemplos": datos.head(5).tolist() if len(datos) > 0 else []
            }
    
    return info

# -------------------------------------------------------------------
# MOTOR ESTADÍSTICO COMPLETO
# -------------------------------------------------------------------
def ejecutar_test_desde_json(accion, columnas, df, params=None):
    """
    Ejecuta cualquier test estadístico.
    
    Parámetros:
    - accion: tipo de análisis a ejecutar
    - columnas: lista de nombres de columna involucradas
    - df: DataFrame con los datos
    - params: parámetros adicionales (diccionario opcional)
    """
    if params is None:
        params = {}
    
    # ================================================================
    # DESCRIPTIVOS
    # ================================================================
    if accion == "descriptivos":
        col = columnas[0]
        datos = df[col].dropna()
        q1, q3 = datos.quantile(0.25), datos.quantile(0.75)
        return {
            "analisis": "Estadísticos descriptivos",
            "variable": col,
            "n": len(datos),
            "media": round(float(datos.mean()), 4),
            "mediana": round(float(datos.median()), 4),
            "moda": datos.mode().tolist() if not datos.mode().empty else None,
            "desviacion_estandar": round(float(datos.std()), 4),
            "varianza": round(float(datos.var()), 4),
            "minimo": round(float(datos.min()), 4),
            "maximo": round(float(datos.max()), 4),
            "rango": round(float(datos.max() - datos.min()), 4),
            "q1": round(float(q1), 4),
            "q3": round(float(q3), 4),
            "iqr": round(float(q3 - q1), 4),
            "asimetria": round(float(datos.skew()), 4),
            "curtosis": round(float(datos.kurtosis()), 4),
            "percentiles": {
                "5%": round(float(datos.quantile(0.05)), 4),
                "10%": round(float(datos.quantile(0.10)), 4),
                "25%": round(float(datos.quantile(0.25)), 4),
                "50%": round(float(datos.quantile(0.50)), 4),
                "75%": round(float(datos.quantile(0.75)), 4),
                "90%": round(float(datos.quantile(0.90)), 4),
                "95%": round(float(datos.quantile(0.95)), 4),
            }
        }
    
    elif accion == "frecuencia_categorica":
        col = columnas[0]
        datos = df[col].dropna()
        conteo = datos.value_counts()
        total = len(datos)
        return {
            "analisis": f"Distribución de frecuencias: {col}",
            "total": total,
            "categorias": [
                {
                    "categoria": str(cat),
                    "frecuencia": int(conteo[cat]),
                    "porcentaje": round(float(conteo[cat] / total * 100), 2)
                }
                for cat in conteo.index
            ]
        }
    
    elif accion == "tabla_contingencia":
        col1, col2 = columnas[0], columnas[1]
        tabla = pd.crosstab(df[col1], df[col2], margins=True)
        return {
            "analisis": f"Tabla de contingencia: {col1} vs {col2}",
            "tabla": tabla.to_dict()
        }
    
    # ================================================================
    # NORMALIDAD
    # ================================================================
    elif accion == "normalidad":
        col = columnas[0]
        datos = df[col].dropna()
        
        # Shapiro-Wilk (hasta 5000 obs) o Kolmogorov-Smirnov
        if len(datos) <= 5000:
            stat, p = stats.shapiro(datos)
            test_usado = "Shapiro-Wilk"
        else:
            stat, p = stats.kstest(datos, 'norm', args=(datos.mean(), datos.std()))
            test_usado = "Kolmogorov-Smirnov"
        
        return {
            "analisis": f"Prueba de normalidad: {col}",
            "test": test_usado,
            "estadistico": round(float(stat), 4),
            "p_valor": round(float(p), 4),
            "es_normal": p > 0.05,
            "interpretacion": "Los datos siguen una distribución normal" if p > 0.05 else "Los datos NO siguen una distribución normal"
        }
    
    # ================================================================
    # COMPARACIÓN DE 2 GRUPOS
    # ================================================================
    elif accion == "ttest_independiente":
        col_num = columnas[0]
        col_cat = columnas[1]
        grupos = df[col_cat].dropna().unique()
        
        if len(grupos) != 2:
            return {"error": f"Se necesitan 2 grupos. '{col_cat}' tiene {len(grupos)}."}
        
        g1 = df[df[col_cat] == grupos[0]][col_num].dropna()
        g2 = df[df[col_cat] == grupos[1]][col_num].dropna()
        
        stat, p = stats.ttest_ind(g1, g2)
        
        return {
            "analisis": f"t-test independiente: {col_num} por {col_cat}",
            "grupo_1": str(grupos[0]),
            "grupo_2": str(grupos[1]),
            "media_1": round(float(g1.mean()), 4),
            "media_2": round(float(g2.mean()), 4),
            "desviacion_1": round(float(g1.std()), 4),
            "desviacion_2": round(float(g2.std()), 4),
            "n_1": len(g1),
            "n_2": len(g2),
            "estadistico_t": round(float(stat), 4),
            "p_valor": round(float(p), 4),
            "significativo": p <= 0.05,
            "diferencia_medias": round(float(g1.mean() - g2.mean()), 4)
        }
    
    elif accion == "ttest_pareado":
        col1, col2 = columnas[0], columnas[1]
        mask = df[[col1, col2]].dropna().index
        stat, p = stats.ttest_rel(df.loc[mask, col1], df.loc[mask, col2])
        
        return {
            "analisis": f"t-test pareado: {col1} vs {col2}",
            "media_antes": round(float(df.loc[mask, col1].mean()), 4),
            "media_despues": round(float(df.loc[mask, col2].mean()), 4),
            "n_pares": len(mask),
            "estadistico_t": round(float(stat), 4),
            "p_valor": round(float(p), 4),
            "significativo": p <= 0.05
        }
    
    elif accion == "mann_whitney":
        col_num = columnas[0]
        col_cat = columnas[1]
        grupos = df[col_cat].dropna().unique()
        
        if len(grupos) != 2:
            return {"error": f"Se necesitan 2 grupos. '{col_cat}' tiene {len(grupos)}."}
        
        g1 = df[df[col_cat] == grupos[0]][col_num].dropna()
        g2 = df[df[col_cat] == grupos[1]][col_num].dropna()
        
        stat, p = stats.mannwhitneyu(g1, g2, alternative='two-sided')
        
        return {
            "analisis": f"Mann-Whitney U: {col_num} por {col_cat}",
            "grupo_1": str(grupos[0]),
            "grupo_2": str(grupos[1]),
            "mediana_1": round(float(g1.median()), 4),
            "mediana_2": round(float(g2.median()), 4),
            "estadistico_U": round(float(stat), 4),
            "p_valor": round(float(p), 4),
            "significativo": p <= 0.05
        }
    
    elif accion == "wilcoxon":
        col1, col2 = columnas[0], columnas[1]
        mask = df[[col1, col2]].dropna().index
        stat, p = stats.wilcoxon(df.loc[mask, col1], df.loc[mask, col2])
        
        return {
            "analisis": f"Wilcoxon signed-rank: {col1} vs {col2}",
            "n_pares": len(mask),
            "estadistico_W": round(float(stat), 4),
            "p_valor": round(float(p), 4),
            "significativo": p <= 0.05
        }
    
    # ================================================================
    # COMPARACIÓN DE 3+ GRUPOS
    # ================================================================
    elif accion == "anova":
        col_num = columnas[0]
        col_cat = columnas[1]
        grupos = df[col_cat].dropna().unique()
        
        if len(grupos) < 2:
            return {"error": f"Se necesitan al menos 2 grupos. '{col_cat}' tiene {len(grupos)}."}
        
        muestras = [df[df[col_cat] == g][col_num].dropna().values for g in grupos]
        f_stat, p = stats.f_oneway(*muestras)
        
        return {
            "analisis": f"ANOVA one-way: {col_num} por {col_cat}",
            "grupos": [str(g) for g in grupos],
            "medias_por_grupo": {str(g): round(float(df[df[col_cat] == g][col_num].mean()), 4) for g in grupos},
            "n_por_grupo": {str(g): int(len(df[df[col_cat] == g][col_num].dropna())) for g in grupos},
            "estadistico_F": round(float(f_stat), 4),
            "p_valor": round(float(p), 4),
            "significativo": p <= 0.05
        }
    
    elif accion == "kruskal_wallis":
        col_num = columnas[0]
        col_cat = columnas[1]
        grupos = df[col_cat].dropna().unique()
        
        if len(grupos) < 2:
            return {"error": f"Se necesitan al menos 2 grupos."}
        
        muestras = [df[df[col_cat] == g][col_num].dropna().values for g in grupos]
        h_stat, p = stats.kruskal(*muestras)
        
        return {
            "analisis": f"Kruskal-Wallis: {col_num} por {col_cat}",
            "grupos": [str(g) for g in grupos],
            "medianas_por_grupo": {str(g): round(float(df[df[col_cat] == g][col_num].median()), 4) for g in grupos},
            "estadistico_H": round(float(h_stat), 4),
            "p_valor": round(float(p), 4),
            "significativo": p <= 0.05
        }
    
    # ================================================================
    # ASOCIACIÓN DE CATEGÓRICAS
    # ================================================================
    elif accion == "chi_cuadrado":
        col1, col2 = columnas[0], columnas[1]
        tabla = pd.crosstab(df[col1], df[col2])
        chi2, p, dof, expected = stats.chi2_contingency(tabla)
        
        return {
            "analisis": f"Chi-cuadrado: {col1} vs {col2}",
            "chi_cuadrado": round(float(chi2), 4),
            "p_valor": round(float(p), 4),
            "grados_libertad": int(dof),
            "significativo": p <= 0.05,
            "tabla_contingencia": tabla.to_dict()
        }
    
    elif accion == "fisher_exacto":
        col1, col2 = columnas[0], columnas[1]
        tabla = pd.crosstab(df[col1], df[col2])
        
        if tabla.shape == (2, 2):
            odds_ratio, p = stats.fisher_exact(tabla)
            return {
                "analisis": f"Test exacto de Fisher: {col1} vs {col2}",
                "odds_ratio": round(float(odds_ratio), 4),
                "p_valor": round(float(p), 4),
                "significativo": p <= 0.05
            }
        else:
            return {"error": "Fisher requiere tabla 2x2. Usa Chi-cuadrado."}
    
    # ================================================================
    # CORRELACIÓN
    # ================================================================
    elif accion == "correlacion_pearson":
        col1, col2 = columnas[0], columnas[1]
        mask = df[[col1, col2]].dropna().index
        r, p = stats.pearsonr(df.loc[mask, col1], df.loc[mask, col2])
        
        fuerza = "muy débil" if abs(r) < 0.2 else "débil" if abs(r) < 0.4 else "moderada" if abs(r) < 0.6 else "fuerte" if abs(r) < 0.8 else "muy fuerte"
        direccion = "positiva" if r > 0 else "negativa"
        
        return {
            "analisis": f"Correlación de Pearson: {col1} vs {col2}",
            "coeficiente_r": round(float(r), 4),
            "r_cuadrado": round(float(r**2), 4),
            "p_valor": round(float(p), 4),
            "significativo": p <= 0.05,
            "fuerza": fuerza,
            "direccion": direccion,
            "n": len(mask)
        }
    
    elif accion == "correlacion_spearman":
        col1, col2 = columnas[0], columnas[1]
        mask = df[[col1, col2]].dropna().index
        rho, p = stats.spearmanr(df.loc[mask, col1], df.loc[mask, col2])
        
        return {
            "analisis": f"Correlación de Spearman: {col1} vs {col2}",
            "coeficiente_rho": round(float(rho), 4),
            "p_valor": round(float(p), 4),
            "significativo": p <= 0.05,
            "n": len(mask)
        }
    
    # ================================================================
    # REGRESIÓN
    # ================================================================
    elif accion == "regresion_lineal":
        col_y, col_x = columnas[0], columnas[1]
        mask = df[[col_x, col_y]].dropna().index
        x = df.loc[mask, col_x]
        y = df.loc[mask, col_y]
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        return {
            "analisis": f"Regresión lineal: {col_y} ~ {col_x}",
            "ecuacion": f"Y = {intercept:.4f} + {slope:.4f} * X",
            "intercepto": round(float(intercept), 4),
            "pendiente": round(float(slope), 4),
            "r_cuadrado": round(float(r_value**2), 4),
            "coeficiente_correlacion": round(float(r_value), 4),
            "p_valor": round(float(p_value), 4),
            "error_estandar": round(float(std_err), 4),
            "significativo": p_value <= 0.05,
            "n": len(mask)
        }
    
    elif accion == "regresion_logistica":
        col_y, col_x = columnas[0], columnas[1]
        import statsmodels.api as sm
        
        mask = df[[col_x, col_y]].dropna().index
        X = sm.add_constant(df.loc[mask, col_x])
        y = df.loc[mask, col_y]
        
        try:
            modelo = sm.Logit(y, X).fit(disp=False)
            return {
                "analisis": f"Regresión logística: {col_y} ~ {col_x}",
                "pseudo_r2": round(float(modelo.prsquared), 4),
                "coeficientes": modelo.params.to_dict(),
                "p_valores": modelo.pvalues.to_dict(),
                "n": len(mask)
            }
        except Exception as e:
            return {"error": f"No se pudo ajustar el modelo: {str(e)}"}
    
    # ================================================================
    # MEDIDAS EPIDEMIOLÓGICAS
    # ================================================================
    elif accion == "riesgo_relativo":
        # Usar params para tabla 2x2: {"a": VP, "b": FP, "c": FN, "d": VN}
        a = params.get("a", 0)
        b = params.get("b", 0)
        c = params.get("c", 0)
        d = params.get("d", 0)
        
        riesgo_exp = a / (a + b) if (a + b) > 0 else 0
        riesgo_noexp = c / (c + d) if (c + d) > 0 else 0
        rr = riesgo_exp / riesgo_noexp if riesgo_noexp > 0 else float('inf')
        
        return {
            "analisis": "Riesgo Relativo (RR)",
            "riesgo_expuestos": round(float(riesgo_exp), 4),
            "riesgo_no_expuestos": round(float(riesgo_noexp), 4),
            "riesgo_relativo": round(float(rr), 4),
            "interpretacion": f"El riesgo es {rr:.2f} veces mayor en expuestos" if rr > 1 else f"El riesgo es {1/rr:.2f} veces menor en expuestos" if rr < 1 else "No hay diferencia de riesgo"
        }
    
    elif accion == "odds_ratio":
        a = params.get("a", 0)
        b = params.get("b", 0)
        c = params.get("c", 0)
        d = params.get("d", 0)
        
        odds_exp = a / b if b > 0 else float('inf')
        odds_noexp = c / d if d > 0 else float('inf')
        or_val = odds_exp / odds_noexp if odds_noexp > 0 else float('inf')
        
        return {
            "analisis": "Odds Ratio (OR)",
            "odds_expuestos": round(float(odds_exp), 4),
            "odds_no_expuestos": round(float(odds_noexp), 4),
            "odds_ratio": round(float(or_val), 4)
        }
    
    elif accion == "nnt":
        a = params.get("a", 0)
        b = params.get("b", 0)
        c = params.get("c", 0)
        d = params.get("d", 0)
        
        riesgo_exp = a / (a + b) if (a + b) > 0 else 0
        riesgo_noexp = c / (c + d) if (c + d) > 0 else 0
        rar = riesgo_noexp - riesgo_exp
        nnt = 1 / rar if rar != 0 else float('inf')
        
        return {
            "analisis": "Número Necesario a Tratar (NNT)",
            "riesgo_expuestos": round(float(riesgo_exp), 4),
            "riesgo_no_expuestos": round(float(riesgo_noexp), 4),
            "rar": round(float(rar), 4),
            "nnt": round(float(nnt), 1) if nnt != float('inf') else "Infinito",
            "interpretacion": f"Se necesita tratar a {nnt:.0f} personas para prevenir un evento" if nnt != float('inf') else "No hay diferencia de riesgo"
        }
    
    # ================================================================
    # PRUEBAS DIAGNÓSTICAS
    # ================================================================
    elif accion == "sensibilidad_especificidad":
        a = params.get("a", 0)  # VP
        b = params.get("b", 0)  # FP
        c = params.get("c", 0)  # FN
        d = params.get("d", 0)  # VN
        
        sens = a / (a + c) if (a + c) > 0 else 0
        espec = d / (b + d) if (b + d) > 0 else 0
        vpp = a / (a + b) if (a + b) > 0 else 0
        vpn = d / (c + d) if (c + d) > 0 else 0
        lr_pos = sens / (1 - espec) if (1 - espec) > 0 else float('inf')
        lr_neg = (1 - sens) / espec if espec > 0 else float('inf')
        
        return {
            "analisis": "Pruebas diagnósticas",
            "sensibilidad": round(float(sens), 4),
            "especificidad": round(float(espec), 4),
            "vpp": round(float(vpp), 4),
            "vpn": round(float(vpn), 4),
            "lr_positivo": round(float(lr_pos), 2),
            "lr_negativo": round(float(lr_neg), 2),
            "precision": round(float((a + d) / (a + b + c + d)), 4)
        }
    
    # ================================================================
    # SUPERVIVENCIA
    # ================================================================
    elif accion == "kaplan_meier":
        try:
            from lifelines import KaplanMeierFitter
            
            col_tiempo = columnas[0]
            col_evento = columnas[1]
            
            kmf = KaplanMeierFitter()
            kmf.fit(df[col_tiempo], event_observed=df[col_evento])
            
            return {
                "analisis": "Kaplan-Meier",
                "mediana_supervivencia": round(float(kmf.median_survival_time_), 2),
                "tabla_supervivencia": {
                    str(t): round(float(s), 4)
                    for t, s in zip(kmf.survival_function_.index[:10], kmf.survival_function_.values[:10, 0])
                }
            }
        except ImportError:
            return {"error": "Instala lifelines: pip install lifelines"}
    
    elif accion == "log_rank":
        try:
            from lifelines.statistics import logrank_test
            
            col_tiempo = columnas[0]
            col_evento = columnas[1]
            col_grupo = columnas[2]
            
            grupos = df[col_grupo].dropna().unique()
            g1 = df[df[col_grupo] == grupos[0]]
            g2 = df[df[col_grupo] == grupos[1]]
            
            resultado = logrank_test(
                g1[col_tiempo], g2[col_tiempo],
                event_observed_A=g1[col_evento], event_observed_B=g2[col_evento]
            )
            
            return {
                "analisis": f"Log-rank test: {col_grupo}",
                "grupo_1": str(grupos[0]),
                "grupo_2": str(grupos[1]),
                "estadistico": round(float(resultado.test_statistic), 4),
                "p_valor": round(float(resultado.p_value), 4),
                "significativo": resultado.p_value <= 0.05
            }
        except ImportError:
            return {"error": "Instala lifelines: pip install lifelines"}
    
    # ================================================================
    # GRÁFICOS
    # ================================================================
    elif accion == "histograma":
        col = columnas[0]
        datos = df[col].dropna()
        fig = px.histogram(datos, nbins=30, title=f"Distribución de {col}",
                          color_discrete_sequence=["#2563EB"])
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                         font_family="Inter", bargap=0.05)
        return {"tipo": "grafico", "fig": fig}
    
    elif accion == "boxplot":
        col_num = columnas[0]
        if len(columnas) > 1:
            col_cat = columnas[1]
            fig = px.box(df, x=col_cat, y=col_num, title=f"Boxplot de {col_num} por {col_cat}",
                        color_discrete_sequence=["#2563EB"])
        else:
            fig = px.box(df, y=col_num, title=f"Boxplot de {col_num}",
                        color_discrete_sequence=["#2563EB"])
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", font_family="Inter")
        return {"tipo": "grafico", "fig": fig}
    
    elif accion == "dispersion":
        col_x, col_y = columnas[0], columnas[1]
        color_col = columnas[2] if len(columnas) > 2 else None
        fig = px.scatter(df, x=col_x, y=col_y, color=color_col, trendline='ols',
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
        min_val = min(teoricos.min(), datos.min())
        max_val = max(teoricos.max(), datos.max())
        fig.add_trace(go.Scatter(x=[min_val, max_val], y=[min_val, max_val],
                                mode='lines', line=dict(dash='dash', color='gray')))
        fig.update_layout(title=f"Q-Q Plot: {col}", xaxis_title="Cuantiles teóricos",
                         yaxis_title="Cuantiles observados",
                         plot_bgcolor="white", paper_bgcolor="white", font_family="Inter")
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
        fig.update_traces(marker=dict(colors=["#2563EB", "#3B82F6", "#60A5FA", "#93C5FD", "#BFDBFE"]))
        return {"tipo": "grafico", "fig": fig}
    
    elif accion == "heatmap_correlacion":
        cols_num = df.select_dtypes(include='number').columns
        if len(cols_num) < 2:
            return {"error": "Se necesitan al menos 2 variables numéricas"}
        
        corr = df[cols_num].corr()
        fig = px.imshow(corr, text_auto='.2f', aspect="auto",
                       title="Matriz de correlaciones",
                       color_continuous_scale="Blues")
        fig.update_layout(font_family="Inter")
        return {"tipo": "grafico", "fig": fig}
    
    # ================================================================
    # DEFAULT
    # ================================================================
    return {"error": f"Acción '{accion}' no implementada"}


# -------------------------------------------------------------------
# SIDEBAR
# -------------------------------------------------------------------
with st.sidebar:
    st.markdown("## STATlab")
    st.markdown("*Análisis estadístico inteligente*")
    
    st.divider()
    
    st.markdown("### Datos")
    archivo = st.file_uploader(
        "Cargar archivo de datos",
        type=["csv", "xlsx"],
        help="Formatos soportados: CSV y Excel (.xlsx)"
    )
    
    if archivo is not None:
        st.caption(f"Archivo cargado: {archivo.name}")
    
    st.divider()
    
    st.markdown("### API Key")
    api_key_input = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIzaSy...",
        help="Consíguela en aistudio.google.com"
    )
    
    if api_key_input:
        genai.configure(api_key=api_key_input)
        st.caption("API configurada")
    
    st.divider()
    
    st.markdown("### Sugerencias")
    sugerencias = [
        "Descriptivos de la edad",
        "¿Es normal la distribución del peso?",
        "Compara el colesterol entre fumadores y no fumadores",
        "¿Hay correlación entre edad y presión arterial?",
        "Muestra un histograma del IMC",
        "Haz un boxplot del peso por sexo",
        "ANOVA de la glucosa por grupo de tratamiento",
        "Chi-cuadrado entre sexo y grupo sanguíneo",
        "Regresión lineal: colesterol ~ edad",
        "Matriz de correlaciones",
        "Q-Q plot de la presión sistólica",
    ]
    for s in sugerencias:
        st.caption(s)

# -------------------------------------------------------------------
# ÁREA PRINCIPAL
# -------------------------------------------------------------------
st.title("STATlab")
st.caption("Análisis estadístico con lenguaje natural")

if archivo is not None:
    try:
        df = cargar_datos(archivo)
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.stop()
    
    # Guardar DataFrame en sesión
    if "df" not in st.session_state or st.session_state.get("archivo_nombre") != archivo.name:
        st.session_state.df = df
        st.session_state.archivo_nombre = archivo.name
        st.session_state.mensajes = []
        st.session_state.mensajes.append({
            "rol": "assistant",
            "contenido": (
                f"Archivo **{archivo.name}** cargado.  \n"
                f"**{len(df)}** registros, **{len(df.columns)}** variables: {', '.join(df.columns)}.  \n"
                f"Puedes pedirme cualquier análisis estadístico sobre estos datos."
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
        
        if not api_key_input:
            with st.chat_message("assistant"):
                st.error("Configura tu API Key de Gemini en la barra lateral.")
        else:
            modelo = genai.GenerativeModel("gemini-2.0-flash")
            
            with st.chat_message("assistant"):
                with st.spinner("Analizando..."):
                    try:
                        info = obtener_info_dataset(st.session_state.df)
                        
                        prompt_sistema = f"""
Eres un bioestadístico senior. Trabajas con este dataset:

{json.dumps(info, ensure_ascii=False, indent=2)}

Cuando el usuario pida un análisis, responde ÚNICAMENTE en JSON:

{{
    "respuesta_usuario": "Respuesta clara, profesional, en lenguaje natural. Sin emojis.",
    "accion": "nombre_de_la_accion",
    "columnas": ["col1", "col2"],
    "params": {{}}
}}

ACCIONES DISPONIBLES (elige la más adecuada):

DESCRIPTIVOS:
- descriptivos: estadísticos de UNA variable numérica
- frecuencia_categorica: distribución de UNA variable categórica
- tabla_contingencia: tabla de DOS variables categóricas

NORMALIDAD:
- normalidad: prueba de normalidad de UNA variable numérica

COMPARACIÓN 2 GRUPOS:
- ttest_independiente: comparar numérica entre 2 grupos independientes
- ttest_pareado: comparar 2 mediciones numéricas en los mismos sujetos
- mann_whitney: alternativa no paramétrica al t-test independiente
- wilcoxon: alternativa no paramétrica al t-test pareado

COMPARACIÓN 3+ GRUPOS:
- anova: comparar numérica entre 3+ grupos
- kruskal_wallis: alternativa no paramétrica al ANOVA

ASOCIACIÓN CATEGÓRICAS:
- chi_cuadrado: asociación entre 2 variables categóricas
- fisher_exacto: test exacto para tablas 2x2

CORRELACIÓN:
- correlacion_pearson: correlación lineal entre 2 numéricas
- correlacion_spearman: correlación no paramétrica entre 2 numéricas

REGRESIÓN:
- regresion_lineal: modelo Y ~ X
- regresion_logistica: modelo logístico Y binaria ~ X

MEDIDAS EPIDEMIOLÓGICAS (requiere tabla 2x2 en params: a, b, c, d):
- riesgo_relativo
- odds_ratio
- nnt

PRUEBAS DIAGNÓSTICAS (requiere tabla 2x2 en params):
- sensibilidad_especificidad

SUPERVIVENCIA:
- kaplan_meier: requiere columna tiempo y columna evento (0/1)
- log_rank: requiere tiempo, evento y grupo

GRÁFICOS:
- histograma: histograma de UNA numérica
- boxplot: boxplot de numérica, opcional categórica
- dispersion: dispersión de 2 numéricas
- qq_plot: Q-Q plot de UNA numérica
- barras: gráfico de barras de UNA categórica
- torta: gráfico de sectores de UNA categórica
- heatmap_correlacion: matriz de correlaciones (sin columnas)

SOLO TEXTO (sin ejecutar código):
- solo_texto: preguntas conceptuales, explicaciones, recomendaciones

REGLAS IMPORTANTES:
1. Los nombres de columna deben ser EXACTOS a los del dataset
2. Para tablas 2x2 manuales, incluye los valores en params: {{"a": VP, "b": FP, "c": FN, "d": VN}}
3. Si el usuario pide un gráfico, accion debe ser el tipo de gráfico
4. Si detectas no normalidad, sugiere pruebas no paramétricas
"""

                        respuesta = modelo.generate_content(
                            f"{prompt_sistema}\n\nPregunta: {pregunta}"
                        )
                        
                        texto = respuesta.text.strip()
                        
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
                            with st.spinner("Ejecutando..."):
                                resultado = ejecutar_test_desde_json(accion, columnas, st.session_state.df, params)
                                
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
                    
                    except Exception as e:
                        st.error(f"Error: {e}")
                        st.session_state.mensajes.append({
                            "rol": "assistant",
                            "contenido": "Ocurrió un error. Intenta reformular tu pregunta."
                        })

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
            Carga un archivo de datos en la barra lateral y describe el analisis que necesitas.
            La aplicacion ejecutara la prueba estadistica adecuada y te mostrara los resultados.
        </p>
        <p style="color:#6B7280; font-size:0.9rem;">
            Para comenzar, sube tu archivo Excel o CSV y configura tu API Key de Gemini.
        </p>
    </div>
    """, unsafe_allow_html=True)
