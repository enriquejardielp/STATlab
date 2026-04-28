import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from io import BytesIO

# -------------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Estadística desde Excel",
    page_icon="📊",
    layout="wide"
)

# -------------------------------------------------------------------
# FUNCIONES AUXILIARES
# -------------------------------------------------------------------
def cargar_datos(archivo):
    """Carga un archivo CSV o Excel y devuelve un DataFrame."""
    if archivo.name.endswith('.csv'):
        return pd.read_csv(archivo)
    else:
        return pd.read_excel(archivo)

# -------------------------------------------------------------------
# INTERFAZ PRINCIPAL
# -------------------------------------------------------------------
st.title("📊 App de Estadística desde Excel")
st.markdown("Sube tu archivo y obtén análisis estadísticos al instante.")

# --- SIDEBAR: carga de archivo e información ---
with st.sidebar:
    st.header("📁 Carga de datos")
    archivo = st.file_uploader(
        "Selecciona un archivo",
        type=["csv", "xlsx"],
        help="Formatos soportados: CSV y Excel (.xlsx)"
    )
    
    if archivo is not None:
        st.success(f"✅ {archivo.name}")
        
        # Opciones avanzadas
        st.header("⚙️ Opciones")
        separador = st.text_input("Separador CSV", value=",", disabled=archivo.name.endswith('.xlsx'))
        tiene_encabezado = st.checkbox("Primera fila como encabezado", value=True)

# -------------------------------------------------------------------
# LÓGICA PRINCIPAL
# -------------------------------------------------------------------
if archivo is not None:
    # Cargar datos
    try:
        if archivo.name.endswith('.csv'):
            df = pd.read_csv(archivo, sep=separador) if not separador == ',' else pd.read_csv(archivo)
        else:
            df = pd.read_excel(archivo)
    except Exception as e:
        st.error(f"❌ Error al leer el archivo: {e}")
        st.stop()
    
    # Si no tiene encabezado, asignar nombres genéricos
    if not tiene_encabezado:
        df.columns = [f"Columna_{i+1}" for i in range(len(df.columns))]
    
    # -------------------------------------------------------------------
    # MÉTRICAS GENERALES
    # -------------------------------------------------------------------
    st.header("📋 Resumen del Dataset")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📏 Filas", df.shape[0])
    col2.metric("📐 Columnas", df.shape[1])
    col3.metric("🕳️ Valores nulos", df.isna().sum().sum())
    col4.metric("🔢 Numéricas", len(df.select_dtypes(include='number').columns))
    
    # Tipos de columnas detectados
    tipos = pd.DataFrame({
        'Columna': df.columns,
        'Tipo': df.dtypes.values,
        'No Nulos': df.notna().sum().values,
        'Nulos': df.isna().sum().values,
        '% Completo': (df.notna().sum() / len(df) * 100).round(1).values
    })
    
    # -------------------------------------------------------------------
    # PESTAÑAS DE ANÁLISIS
    # -------------------------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Vista Previa",
        "📊 Descriptivos",
        "📈 Gráficos",
        "🔬 Tests Estadísticos"
    ])
    
    # ---------------------------------------------------- TAB 1: VISTA PREVIA
    with tab1:
        st.subheader("🔍 Vista previa de los datos")
        st.dataframe(df, use_container_width=True, height=400)
        
        st.subheader("ℹ️ Información de columnas")
        
        # Traducir tipos de datos a lenguaje normal
        traduccion_tipos = {
            'int64': 'Número entero',
            'int32': 'Número entero',
            'float64': 'Número decimal',
            'float32': 'Número decimal',
            'object': 'Texto / Categoría',
            'bool': 'Verdadero/Falso',
            'datetime64': 'Fecha',
            'category': 'Categoría'
        }
        
        tipos['Tipo'] = tipos['Tipo'].apply(
            lambda x: traduccion_tipos.get(str(x), str(x))
        )
        
        st.dataframe(tipos, use_container_width=True, hide_index=True)
    
    # ---------------------------------------------------- TAB 2: DESCRIPTIVOS
    with tab2:
        st.subheader("📊 Estadísticos Descriptivos")
        
        cols_numericas = df.select_dtypes(include='number').columns.tolist()
        
        if cols_numericas:
            col_sel = st.selectbox("Selecciona una columna numérica", cols_numericas, key="desc_col")
            datos = df[col_sel].dropna()
            
            # Tarjetas de estadísticos
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("📊 N", len(datos))
            c2.metric("📈 Media", f"{datos.mean():.3f}")
            c3.metric("📉 Mediana", f"{datos.median():.3f}")
            c4.metric("📏 Desv. Est.", f"{datos.std():.3f}")
            c5.metric("📐 Varianza", f"{datos.var():.3f}")
            
            c6, c7, c8, c9 = st.columns(4)
            c6.metric("⬇️ Mínimo", f"{datos.min():.3f}")
            c7.metric("⬆️ Máximo", f"{datos.max():.3f}")
            c8.metric("📊 Rango", f"{datos.max() - datos.min():.3f}")
            c9.metric("📐 IQR", f"{datos.quantile(0.75) - datos.quantile(0.25):.3f}")
            
            # Percentiles
            st.write("**Percentiles:**")
            percentiles = [0, 10, 25, 50, 75, 90, 100]
            valores = np.percentile(datos, percentiles)
            st.dataframe(
                pd.DataFrame({'Percentil': [f"{p}%" for p in percentiles], 'Valor': valores.round(3)}),
                hide_index=True,
                use_container_width=True
            )
            
            # Asimetría y curtosis
            st.write(f"**Asimetría:** {datos.skew():.3f} | **Curtosis:** {datos.kurtosis():.3f}")
            
        else:
            st.warning("⚠️ No se encontraron columnas numéricas en el archivo.")
    
    # ---------------------------------------------------- TAB 3: GRÁFICOS
    with tab3:
        st.subheader("📈 Visualizaciones")
        
        if cols_numericas:
            tipo_grafico = st.radio(
                "Tipo de gráfico:",
                ["Histograma", "Boxplot", "Densidad (KDE)", "QQ-Plot"],
                horizontal=True
            )
            
            col_graf = st.selectbox("Selecciona columna", cols_numericas, key="graf_col")
            datos_graf = df[col_graf].dropna()
            
            if tipo_grafico == "Histograma":
                bins = st.slider("Número de bins", 5, 100, 30)
                fig = px.histogram(
                    x=datos_graf, nbins=bins,
                    title=f"Histograma de {col_graf}",
                    labels={'x': col_graf, 'y': 'Frecuencia'},
                    color_discrete_sequence=['#1f77b4']
                )
                fig.update_layout(bargap=0.1)
                st.plotly_chart(fig, use_container_width=True)
                
            elif tipo_grafico == "Boxplot":
                fig = px.box(
                    y=datos_graf,
                    title=f"Boxplot de {col_graf}",
                    labels={'y': col_graf},
                    color_discrete_sequence=['#ff7f0e']
                )
                st.plotly_chart(fig, use_container_width=True)
                
            elif tipo_grafico == "Densidad (KDE)":
                # Calcular KDE
                from scipy.stats import gaussian_kde
                kde = gaussian_kde(datos_graf)
                x_range = np.linspace(datos_graf.min(), datos_graf.max(), 500)
                densidad = kde(x_range)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=x_range, y=densidad,
                    fill='tozeroy',
                    name='Densidad',
                    line=dict(color='#2ca02c')
                ))
                fig.update_layout(
                    title=f"Densidad (KDE) de {col_graf}",
                    xaxis_title=col_graf,
                    yaxis_title='Densidad'
                )
                st.plotly_chart(fig, use_container_width=True)
                
            elif tipo_grafico == "QQ-Plot":
                # Gráfico Q-Q para evaluar normalidad
                datos_ord = np.sort(datos_graf)
                cuantiles_teoricos = stats.norm.ppf(
                    (np.arange(1, len(datos_ord) + 1) - 0.5) / len(datos_ord)
                )
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=cuantiles_teoricos, y=datos_ord,
                    mode='markers',
                    name='Datos',
                    marker=dict(color='#d62728', size=6)
                ))
                # Línea de referencia
                min_val = min(cuantiles_teoricos.min(), datos_ord.min())
                max_val = max(cuantiles_teoricos.max(), datos_ord.max())
                fig.add_trace(go.Scatter(
                    x=[min_val, max_val], y=[min_val, max_val],
                    mode='lines',
                    name='Normal teórica',
                    line=dict(dash='dash', color='gray')
                ))
                fig.update_layout(
                    title=f"QQ-Plot de {col_graf}",
                    xaxis_title='Cuantiles teóricos (Normal)',
                    yaxis_title='Cuantiles observados'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.warning("⚠️ No hay columnas numéricas para graficar.")
    
    # ---------------------------------------------------- TAB 4: TESTS
      
    with tab4:
        st.subheader("🔬 Tests Estadísticos")
        
        # Selector de categoría
        categoria = st.selectbox(
            "Selecciona una categoría:",
            [
                "📊 Descriptivos y Frecuencia",
                "⚖️ Medidas de Asociación y Efecto",
                "🧪 Inferencia",
                "🧬 Pruebas Estadísticas",
                "📈 Modelos",
                "⏳ Supervivencia",
                "🧫 Pruebas Diagnósticas"
            ]
        )
        
        st.divider()
        
        # ============================================================
        # 📊 DESCRIPTIVOS Y FRECUENCIA
        # ============================================================
        if categoria == "📊 Descriptivos y Frecuencia":
            test_desc = st.selectbox(
                "Selecciona un análisis:",
                [
                    "Media, mediana y moda",
                    "Desviación estándar, varianza y rango",
                    "Percentiles y cuartiles",
                    "Proporciones y tasas"
                ]
            )
            
            if cols_numericas:
                # --- Media, mediana y moda ---
                if test_desc == "Media, mediana y moda":
                    col_sel = st.selectbox("Columna numérica", cols_numericas, key="desc_mmm")
                    datos = df[col_sel].dropna()
                    
                    # Calcular moda
                    moda_vals = datos.mode()
                    if len(moda_vals) > 0:
                        moda_str = ", ".join([f"{v:.2f}" for v in moda_vals.values])
                    else:
                        moda_str = "No hay moda"
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Media", f"{datos.mean():.3f}")
                    c2.metric("Mediana", f"{datos.median():.3f}")
                    c3.metric("Moda", moda_str)
                    
                    # Histograma con líneas
                    fig = px.histogram(datos, nbins=30, title=f"Distribución de {col_sel}")
                    fig.add_vline(x=datos.mean(), line_color="red", annotation_text="Media")
                    fig.add_vline(x=datos.median(), line_color="green", annotation_text="Mediana")
                    st.plotly_chart(fig, use_container_width=True)
                
                # --- Desviación estándar, varianza y rango ---
                elif test_desc == "Desviación estándar, varianza y rango":
                    col_sel = st.selectbox("Columna numérica", cols_numericas, key="desc_dvr")
                    datos = df[col_sel].dropna()
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Desviación Estándar", f"{datos.std():.4f}")
                    c2.metric("Varianza", f"{datos.var():.4f}")
                    c3.metric("Rango", f"{datos.max() - datos.min():.4f}")
                    c4.metric("Rango Intercuartílico", f"{datos.quantile(0.75) - datos.quantile(0.25):.4f}")
                    
                    st.write(f"**Mínimo:** {datos.min():.4f} | **Máximo:** {datos.max():.4f}")
                    
                    # Boxplot
                    fig = px.box(datos, title=f"Boxplot de {col_sel}")
                    st.plotly_chart(fig, use_container_width=True)
                
                # --- Percentiles y cuartiles ---
                elif test_desc == "Percentiles y cuartiles":
                    col_sel = st.selectbox("Columna numérica", cols_numericas, key="desc_perc")
                    datos = df[col_sel].dropna()
                    
                    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
                    valores = np.percentile(datos, percentiles)
                    
                    df_perc = pd.DataFrame({
                        'Percentil': [f"{p}%" for p in percentiles],
                        'Valor': valores.round(4)
                    })
                    st.dataframe(df_perc, hide_index=True, use_container_width=True)
                    
                    # Gráfico de percentiles
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=percentiles, y=valores, mode='lines+markers', name='Percentiles'))
                    fig.update_layout(title=f"Curva de percentiles - {col_sel}", xaxis_title="Percentil (%)", yaxis_title="Valor")
                    st.plotly_chart(fig, use_container_width=True)
                
                # --- Proporciones y tasas ---
                elif test_desc == "Proporciones y tasas":
                    cols_cat = df.select_dtypes(include=['object', 'category']).columns.tolist()
                    
                    if cols_cat:
                        col_sel = st.selectbox("Columna categórica", cols_cat, key="desc_prop")
                        conteo = df[col_sel].value_counts()
                        total = len(df)
                        
                        st.write(f"**Total de observaciones:** {total}")
                        
                        df_prop = pd.DataFrame({
                            'Categoría': conteo.index,
                            'Frecuencia': conteo.values,
                            'Proporción': (conteo.values / total).round(4),
                            'Porcentaje (%)': (conteo.values / total * 100).round(2)
                        })
                        st.dataframe(df_prop, hide_index=True, use_container_width=True)
                        
                        # Gráfico de barras
                        fig = px.bar(df_prop, x='Categoría', y='Porcentaje (%)', title=f"Distribución de {col_sel}")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No se encontraron columnas categóricas.")
            else:
                st.warning("No hay columnas numéricas en el dataset.")
        
        # ============================================================
        # ⚖️ MEDIDAS DE ASOCIACIÓN Y EFECTO
        # ============================================================
        elif categoria == "⚖️ Medidas de Asociación y Efecto":
            test_asoc = st.selectbox(
                "Selecciona un análisis:",
                [
                    "Riesgo Relativo (RR)",
                    "Odds Ratio (OR)",
                    "Diferencia de Riesgos",
                    "RAR y RRR",
                    "NNT y NNH"
                ]
            )
            
            st.markdown("""
            ### 📋 Tabla 2x2 requerida
            
            Para estos análisis necesitas dos variables dicotómicas (sí/no, expuesto/no expuesto, enfermo/sano).
            
            |  | Enfermo | Sano |
            |--|---------|------|
            | **Expuesto** | a | b |
            | **No expuesto** | c | d |
            """)
            
            # Input manual de tabla 2x2
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("**Expuestos**")
                a = st.number_input("Enfermos (a)", min_value=0, value=10, step=1)
                b = st.number_input("Sanos (b)", min_value=0, value=90, step=1)
            with col_b:
                st.write("**No expuestos**")
                c = st.number_input("Enfermos (c)", min_value=0, value=5, step=1)
                d = st.number_input("Sanos (d)", min_value=0, value=95, step=1)
            
            # Cálculos automáticos
            total_exp = a + b
            total_noexp = c + d
            total_enf = a + c
            total_sano = b + d
            
            if total_exp > 0 and total_noexp > 0:
                riesgo_exp = a / total_exp
                riesgo_noexp = c / total_noexp
                rr = riesgo_exp / riesgo_noexp if riesgo_noexp > 0 else float('inf')
                odds_exp = a / b if b > 0 else float('inf')
                odds_noexp = c / d if d > 0 else float('inf')
                or_val = odds_exp / odds_noexp if odds_noexp > 0 else float('inf')
                diff_riesgo = riesgo_exp - riesgo_noexp
                rar = riesgo_noexp - riesgo_exp
                rrr = (riesgo_noexp - riesgo_exp) / riesgo_noexp if riesgo_noexp > 0 else 0
                nnt = 1 / rar if rar != 0 else float('inf')
                
                if test_asoc == "Riesgo Relativo (RR)":
                    st.metric("Riesgo Relativo (RR)", f"{rr:.4f}")
                    st.write(f"**Riesgo en expuestos:** {riesgo_exp:.4f} ({a}/{total_exp})")
                    st.write(f"**Riesgo en no expuestos:** {riesgo_noexp:.4f} ({c}/{total_noexp})")
                    if rr > 1:
                        st.warning(f"RR > 1: La exposición aumenta el riesgo {(rr-1)*100:.1f}%")
                    elif rr < 1:
                        st.success(f"RR < 1: La exposición reduce el riesgo {(1-rr)*100:.1f}%")
                    else:
                        st.info("RR = 1: No hay asociación")
                
                elif test_asoc == "Odds Ratio (OR)":
                    st.metric("Odds Ratio (OR)", f"{or_val:.4f}")
                    st.write(f"**Odds en expuestos:** {odds_exp:.4f}")
                    st.write(f"**Odds en no expuestos:** {odds_noexp:.4f}")
                    if or_val > 1:
                        st.warning(f"OR > 1: Mayor odds de enfermedad en expuestos")
                    elif or_val < 1:
                        st.success(f"OR < 1: Menor odds de enfermedad en expuestos")
                    else:
                        st.info("OR = 1: No hay asociación")
                
                elif test_asoc == "Diferencia de Riesgos":
                    st.metric("Diferencia de Riesgos (Riesgo Absoluto)", f"{diff_riesgo:.4f}")
                    st.write(f"Riesgo expuestos: {riesgo_exp:.4f}")
                    st.write(f"Riesgo no expuestos: {riesgo_noexp:.4f}")
                
                elif test_asoc == "RAR y RRR":
                    c1, c2 = st.columns(2)
                    c1.metric("Reducción Absoluta del Riesgo (RAR)", f"{rar:.4f}")
                    c2.metric("Reducción Relativa del Riesgo (RRR)", f"{rrr:.4f} ({rrr*100:.1f}%)")
                
                elif test_asoc == "NNT y NNH":
                    st.metric("Número Necesario a Tratar (NNT)", f"{nnt:.1f}" if nnt != float('inf') else "∞")
                    st.write(f"Se necesita tratar a **{nnt:.0f}** personas para prevenir un evento." if nnt != float('inf') else "No se puede calcular (RAR = 0)")
        
        # ============================================================
        # 🧪 INFERENCIA
        # ============================================================
        elif categoria == "🧪 Inferencia":
            test_inf = st.selectbox(
                "Selecciona un análisis:",
                ["Valor p e Intervalos de Confianza", "Error Estándar"]
            )
            
            if cols_numericas:
                col_sel = st.selectbox("Columna numérica", cols_numericas, key="inf_col")
                datos = df[col_sel].dropna()
                
                if test_inf == "Valor p e Intervalos de Confianza":
                    confianza = st.slider("Nivel de confianza (%)", 80, 99, 95)
                    
                    # IC para la media
                    media = datos.mean()
                    error_std = datos.std() / np.sqrt(len(datos))
                    z = stats.norm.ppf((1 + confianza/100) / 2)
                    ic_inf = media - z * error_std
                    ic_sup = media + z * error_std
                    
                    st.write(f"**Media muestral:** {media:.4f}")
                    st.write(f"**Error estándar:** {error_std:.4f}")
                    st.metric(f"IC {confianza}%", f"[{ic_inf:.4f}, {ic_sup:.4f}]")
                    
                    # Visualización
                    x = np.linspace(media - 4*error_std, media + 4*error_std, 500)
                    y = stats.norm.pdf(x, media, error_std)
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=x, y=y, fill='tozeroy', name='Distribución de la media'))
                    fig.add_vline(x=ic_inf, line_dash="dash", line_color="red", annotation_text=f"IC inf")
                    fig.add_vline(x=ic_sup, line_dash="dash", line_color="red", annotation_text=f"IC sup")
                    fig.add_vline(x=media, line_color="blue", annotation_text="Media")
                    fig.update_layout(title=f"Intervalo de Confianza {confianza}% para la media de {col_sel}")
                    st.plotly_chart(fig, use_container_width=True)
                
                elif test_inf == "Error Estándar":
                    error_std = datos.std() / np.sqrt(len(datos))
                    st.metric("Error Estándar de la Media", f"{error_std:.4f}")
                    st.write(f"**Desviación estándar:** {datos.std():.4f}")
                    st.write(f"**Tamaño muestral (n):** {len(datos)}")
                    st.write(f"**Fórmula:** SE = σ / √n = {datos.std():.4f} / √{len(datos)} = {error_std:.4f}")
            else:
                st.warning("No hay columnas numéricas.")
        
        # ============================================================
        # 🧬 PRUEBAS ESTADÍSTICAS
        # ============================================================
        elif categoria == "🧬 Pruebas Estadísticas":
            test_prueba = st.selectbox(
                "Selecciona un test:",
                ["t de Student", "ANOVA", "Chi-cuadrado", "Test exacto de Fisher",
                 "Mann-Whitney U", "Wilcoxon", "Kruskal-Wallis"]
            )
            
            # --- t de Student ---
            if test_prueba == "t de Student":
                tipo_t = st.radio("Tipo de t-test:", ["Una muestra", "Independiente (2 grupos)"], horizontal=True)
                
                if tipo_t == "Una muestra":
                    col_sel = st.selectbox("Columna", cols_numericas, key="t_una")
                    media_hip = st.number_input("Media hipotética (H₀)", value=0.0)
                    
                    if st.button("Ejecutar t-test", type="primary", key="btn_t1"):
                        stat, p = stats.ttest_1samp(df[col_sel].dropna(), media_hip)
                        c1, c2 = st.columns(2)
                        c1.metric("Estadístico t", f"{stat:.4f}")
                        c2.metric("p-valor", f"{p:.4f}")
                        alpha = st.slider("α", 0.01, 0.10, 0.05, key="alpha_t1")
                        if p > alpha:
                            st.success(f"No se rechaza H₀ (p={p:.4f} > α={alpha})")
                        else:
                            st.warning(f"Se rechaza H₀ (p={p:.4f} ≤ α={alpha})")
                
                elif tipo_t == "Independiente (2 grupos)":
                    col_num = st.selectbox("Columna numérica", cols_numericas, key="t_ind_num")
                    cols_cat = df.select_dtypes(include=['object', 'category']).columns.tolist()
                    
                    if cols_cat:
                        col_cat = st.selectbox("Columna categórica", cols_cat, key="t_ind_cat")
                        grupos = df[col_cat].dropna().unique()
                        
                        if len(grupos) == 2:
                            g1 = df[df[col_cat] == grupos[0]][col_num].dropna()
                            g2 = df[df[col_cat] == grupos[1]][col_num].dropna()
                            
                            if st.button("Ejecutar t-test independiente", type="primary", key="btn_t2"):
                                stat, p = stats.ttest_ind(g1, g2)
                                c1, c2, c3 = st.columns(3)
                                c1.metric("t", f"{stat:.4f}")
                                c2.metric("p-valor", f"{p:.4f}")
                                c3.metric(f"Medias", f"{g1.mean():.2f} vs {g2.mean():.2f}")
                                if p <= 0.05:
                                    st.warning("Diferencia significativa (p ≤ 0.05)")
                                else:
                                    st.success("No hay diferencia significativa (p > 0.05)")
                                
                                fig = px.box(df[df[col_cat].isin(grupos)], x=col_cat, y=col_num, title=f"{col_num} por {col_cat}")
                                st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.error(f"La columna '{col_cat}' debe tener 2 grupos. Tiene {len(grupos)}.")
            
            # --- ANOVA ---
            elif test_prueba == "ANOVA":
                col_num = st.selectbox("Columna numérica", cols_numericas, key="anova_num")
                cols_cat = df.select_dtypes(include=['object', 'category']).columns.tolist()
                
                if cols_cat:
                    col_cat = st.selectbox("Columna categórica (grupos)", cols_cat, key="anova_cat")
                    grupos = df[col_cat].dropna().unique()
                    
                    if len(grupos) >= 2:
                        st.write(f"**Grupos detectados ({len(grupos)}):** {', '.join(grupos)}")
                        
                        if st.button("Ejecutar ANOVA (one-way)", type="primary", key="btn_anova"):
                            muestras = [df[df[col_cat] == g][col_num].dropna().values for g in grupos]
                            f_stat, p = stats.f_oneway(*muestras)
                            
                            c1, c2 = st.columns(2)
                            c1.metric("F", f"{f_stat:.4f}")
                            c2.metric("p-valor", f"{p:.4f}")
                            
                            if p <= 0.05:
                                st.warning(f"Diferencias significativas entre grupos (p={p:.4f})")
                            else:
                                st.success(f"No hay diferencias significativas (p={p:.4f})")
                            
                            fig = px.box(df, x=col_cat, y=col_num, title=f"ANOVA: {col_num} por {col_cat}")
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error(f"Se necesitan al menos 2 grupos. '{col_cat}' tiene {len(grupos)}.")
            
            # --- Chi-cuadrado ---
            elif test_prueba == "Chi-cuadrado":
                cols_cat = df.select_dtypes(include=['object', 'category']).columns.tolist()
                
                if len(cols_cat) >= 2:
                    col1 = st.selectbox("Variable 1", cols_cat, key="chi_col1")
                    col2 = st.selectbox("Variable 2", cols_cat, key="chi_col2")
                    
                    if st.button("Ejecutar Chi-cuadrado", type="primary", key="btn_chi"):
                        tabla = pd.crosstab(df[col1], df[col2])
                        st.write("**Tabla de contingencia:**")
                        st.dataframe(tabla, use_container_width=True)
                        
                        chi2, p, dof, expected = stats.chi2_contingency(tabla)
                        c1, c2, c3 = st.columns(3)
                        c1.metric("χ²", f"{chi2:.4f}")
                        c2.metric("p-valor", f"{p:.4f}")
                        c3.metric("Grados de libertad", dof)
                        
                        if p <= 0.05:
                            st.warning("Asociación significativa (p ≤ 0.05)")
                        else:
                            st.success("No hay asociación significativa (p > 0.05)")
                else:
                    st.warning("Se necesitan al menos 2 columnas categóricas.")
            
            # --- Test exacto de Fisher ---
            elif test_prueba == "Test exacto de Fisher":
                cols_cat = df.select_dtypes(include=['object', 'category']).columns.tolist()
                
                if len(cols_cat) >= 2:
                    col1 = st.selectbox("Variable 1", cols_cat, key="fish_col1")
                    col2 = st.selectbox("Variable 2", cols_cat, key="fish_col2")
                    
                    if st.button("Ejecutar Fisher", type="primary", key="btn_fish"):
                        tabla = pd.crosstab(df[col1], df[col2])
                        st.dataframe(tabla, use_container_width=True)
                        
                        if tabla.shape == (2, 2):
                            odds_ratio, p = stats.fisher_exact(tabla)
                            c1, c2 = st.columns(2)
                            c1.metric("Odds Ratio", f"{odds_ratio:.4f}")
                            c2.metric("p-valor", f"{p:.4f}")
                        else:
                            st.error("Fisher requiere tabla 2x2. Usa Chi-cuadrado para tablas más grandes.")
                else:
                    st.warning("Se necesitan al menos 2 columnas categóricas.")
            
            # --- Mann-Whitney U ---
            elif test_prueba == "Mann-Whitney U":
                col_num = st.selectbox("Columna numérica", cols_numericas, key="mw_num")
                cols_cat = df.select_dtypes(include=['object', 'category']).columns.tolist()
                
                if cols_cat:
                    col_cat = st.selectbox("Columna categórica (2 grupos)", cols_cat, key="mw_cat")
                    grupos = df[col_cat].dropna().unique()
                    
                    if len(grupos) == 2:
                        g1 = df[df[col_cat] == grupos[0]][col_num].dropna()
                        g2 = df[df[col_cat] == grupos[1]][col_num].dropna()
                        
                        if st.button("Ejecutar Mann-Whitney", type="primary", key="btn_mw"):
                            stat, p = stats.mannwhitneyu(g1, g2, alternative='two-sided')
                            st.write(f"**U = {stat:.4f}, p = {p:.4f}**")
                            if p <= 0.05:
                                st.warning("Diferencia significativa entre grupos")
                            else:
                                st.success("No hay diferencia significativa")
                    else:
                        st.error(f"Se necesitan 2 grupos. '{col_cat}' tiene {len(grupos)}.")
            
            # --- Wilcoxon ---
            elif test_prueba == "Wilcoxon":
                if len(cols_numericas) >= 2:
                    col1 = st.selectbox("Variable 1 (antes)", cols_numericas, key="wilx_1")
                    col2 = st.selectbox("Variable 2 (después)", cols_numericas, key="wilx_2")
                    
                    if st.button("Ejecutar Wilcoxon", type="primary", key="btn_wilx"):
                        mask = df[[col1, col2]].dropna().index
                        stat, p = stats.wilcoxon(df.loc[mask, col1], df.loc[mask, col2])
                        c1, c2 = st.columns(2)
                        c1.metric("W", f"{stat:.4f}")
                        c2.metric("p-valor", f"{p:.4f}")
                else:
                    st.warning("Se necesitan 2 columnas numéricas (medidas pareadas).")
            
            # --- Kruskal-Wallis ---
            elif test_prueba == "Kruskal-Wallis":
                col_num = st.selectbox("Columna numérica", cols_numericas, key="kw_num")
                cols_cat = df.select_dtypes(include=['object', 'category']).columns.tolist()
                
                if cols_cat:
                    col_cat = st.selectbox("Columna categórica", cols_cat, key="kw_cat")
                    grupos = df[col_cat].dropna().unique()
                    
                    if len(grupos) >= 2:
                        if st.button("Ejecutar Kruskal-Wallis", type="primary", key="btn_kw"):
                            muestras = [df[df[col_cat] == g][col_num].dropna().values for g in grupos]
                            h, p = stats.kruskal(*muestras)
                            st.write(f"**H = {h:.4f}, p = {p:.4f}**")
        
        # ============================================================
        # 📈 MODELOS
        # ============================================================
        elif categoria == "📈 Modelos":
            test_modelo = st.selectbox(
                "Selecciona un modelo:",
                ["Regresión lineal", "Regresión logística"]
            )
            
            if test_modelo == "Regresión lineal":
                if len(cols_numericas) >= 2:
                    col_y = st.selectbox("Variable dependiente (Y)", cols_numericas, key="reg_y")
                    col_x = st.selectbox("Variable independiente (X)", cols_numericas, key="reg_x")
                    
                    if st.button("Ejecutar regresión", type="primary", key="btn_reg"):
                        mask = df[[col_x, col_y]].dropna().index
                        x = df.loc[mask, col_x]
                        y = df.loc[mask, col_y]
                        
                        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                        
                        c1, c2, c3 = st.columns(3)
                        c1.metric("R²", f"{r_value**2:.4f}")
                        c2.metric("Pendiente", f"{slope:.4f}")
                        c3.metric("p-valor", f"{p_value:.4f}")
                        
                        st.write(f"**Ecuación:** Y = {intercept:.4f} + {slope:.4f} · X")
                        
                        fig = px.scatter(x=x, y=y, trendline='ols', title=f"Regresión: {col_y} ~ {col_x}")
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Se necesitan al menos 2 columnas numéricas.")
            
            elif test_modelo == "Regresión logística":
                st.info("La regresión logística requiere `statsmodels`. Ya está instalada en tu entorno.")
                
                col_y_bin = st.selectbox("Variable dependiente (0/1)", cols_numericas, key="log_y")
                col_x = st.selectbox("Variable independiente", cols_numericas, key="log_x")
                
                if st.button("Ejecutar regresión logística", type="primary", key="btn_log"):
                    import statsmodels.api as sm
                    mask = df[[col_x, col_y_bin]].dropna().index
                    X = sm.add_constant(df.loc[mask, col_x])
                    y = df.loc[mask, col_y_bin]
                    
                    try:
                        modelo = sm.Logit(y, X).fit(disp=False)
                        st.text(modelo.summary())
                    except Exception as e:
                        st.error(f"Error: {e}. Asegúrate de que Y sea binaria (0/1).")
        
        # ============================================================
        # ⏳ SUPERVIVENCIA
        # ============================================================
        elif categoria == "⏳ Supervivencia":
            st.info("""
            ### Análisis de Supervivencia
            
            Para Kaplan-Meier, Hazard Ratio y Log-rank test se necesita:
            - **Columna de tiempo:** días/semanas/meses hasta el evento
            - **Columna de evento:** 1 si ocurrió el evento, 0 si censurado
            - **Columna de grupo:** (opcional) para comparar curvas
            
            Se requiere la librería `lifelines`.
            """)
            
            st.code("pip install lifelines", language="bash")
            
            # Placeholder para cuando instalen lifelines
            col_tiempo = st.selectbox("Columna de tiempo", cols_numericas, key="surv_t")
            col_evento = st.selectbox("Columna de evento (0/1)", cols_numericas, key="surv_e")
            
            cols_cat = df.select_dtypes(include=['object', 'category']).columns.tolist()
            col_grupo = st.selectbox("Columna de grupo (opcional)", ["Ninguno"] + cols_cat, key="surv_g")
            
            if st.button("Ejecutar Kaplan-Meier", type="primary", key="btn_km"):
                try:
                    from lifelines import KaplanMeierFitter
                    
                    kmf = KaplanMeierFitter()
                    kmf.fit(df[col_tiempo], event_observed=df[col_evento])
                    
                    fig = kmf.plot_survival_function()
                    st.pyplot(fig.figure)
                except ImportError:
                    st.error("Instala lifelines: `pip install lifelines`")
        
        # ============================================================
        # 🧫 PRUEBAS DIAGNÓSTICAS
        # ============================================================
        elif categoria == "🧫 Pruebas Diagnósticas":
            st.markdown("""
            ### Matriz de Confusión
            
            |  | Prueba + | Prueba - |
            |--|----------|----------|
            | **Enfermo** | VP | FN |
            | **Sano** | FP | VN |
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                vp = st.number_input("Verdaderos Positivos (VP)", min_value=0, value=80)
                fn = st.number_input("Falsos Negativos (FN)", min_value=0, value=20)
            with col2:
                fp = st.number_input("Falsos Positivos (FP)", min_value=0, value=10)
                vn = st.number_input("Verdaderos Negativos (VN)", min_value=0, value=90)
            
            total_enf = vp + fn
            total_sano = fp + vn
            
            if total_enf > 0 and total_sano > 0:
                sens = vp / total_enf
                espec = vn / total_sano
                vpp = vp / (vp + fp) if (vp + fp) > 0 else 0
                vpn = vn / (vn + fn) if (vn + fn) > 0 else 0
                lr_pos = sens / (1 - espec) if (1 - espec) > 0 else float('inf')
                lr_neg = (1 - sens) / espec if espec > 0 else float('inf')
                
                st.subheader("Resultados")
                c1, c2, c3 = st.columns(3)
                c1.metric("Sensibilidad", f"{sens:.4f} ({sens*100:.1f}%)")
                c2.metric("Especificidad", f"{espec:.4f} ({espec*100:.1f}%)")
                c3.metric("Precisión", f"{(vp+vn)/(vp+vn+fp+fn):.4f}")
                
                c4, c5, c6 = st.columns(3)
                c4.metric("VPP", f"{vpp:.4f}")
                c5.metric("VPN", f"{vpn:.4f}")
                c6.metric("Tasa de error", f"{(fp+fn)/(vp+vn+fp+fn):.4f}")
                
                c7, c8 = st.columns(2)
                c7.metric("LR+", f"{lr_pos:.2f}")
                c8.metric("LR−", f"{lr_neg:.2f}")
                
                # Interpretación de LR
                st.write("**Interpretación de Razones de Verosimilitud:**")
                if lr_pos > 10:
                    st.success(f"LR+ = {lr_pos:.1f}: Aumento grande en la probabilidad post-prueba")
                elif lr_pos > 5:
                    st.info(f"LR+ = {lr_pos:.1f}: Aumento moderado")
                elif lr_pos > 2:
                    st.warning(f"LR+ = {lr_pos:.1f}: Aumento pequeño")
                else:
                    st.warning(f"LR+ = {lr_pos:.1f}: Cambio mínimo")
    
    # -------------------------------------------------------------------
    # EXPORTACIÓN DE RESULTADOS
    # -------------------------------------------------------------------
    st.header("📥 Exportar")
    st.markdown("Descarga los estadísticos descriptivos de todas las columnas numéricas.")
    
    if cols_numericas:
        resumen = df[cols_numericas].describe()
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            resumen.to_excel(writer, sheet_name='Descriptivos')
        buffer.seek(0)
        
        st.download_button(
            label="📥 Descargar descriptivos (Excel)",
            data=buffer,
            file_name="estadisticos_descriptivos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    # -------------------------------------------------------------------
    # PANTALLA INICIAL (sin archivo cargado)
    # -------------------------------------------------------------------
    st.info("👈 **Sube un archivo** desde el panel lateral para comenzar el análisis.")
    
    st.markdown("""
    ### 📊 ¿Qué puedes hacer con esta app?
    
    - **Descriptivos:** Media, mediana, desviación estándar, percentiles, asimetría, curtosis
    - **Gráficos:** Histogramas, boxplots, densidad (KDE) y QQ-plots interactivos
    - **Tests estadísticos:**
        - Shapiro-Wilk (normalidad)
        - t-test (una muestra e independiente)
        - Correlación de Pearson y Spearman
    - **Exportación:** Descarga los resultados en Excel
    
    ### 📁 Formatos soportados
    - CSV (.csv)
    - Excel (.xlsx)
    
    ### 🚀 Cómo empezar
    1. Arrastra tu archivo al panel lateral o haz clic en "Browse files"
    2. Explora las pestañas de análisis
    3. Descarga los resultados cuando termines
    """)
