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
        st.subheader("🔍 Primeras y últimas filas")
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("**Primeras 5 filas:**")
            st.dataframe(df.head(), use_container_width=True)
        with col_b:
            st.write("**Últimas 5 filas:**")
            st.dataframe(df.tail(), use_container_width=True)
        
        st.subheader("ℹ️ Información de columnas")
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
        
        if cols_numericas:
            test_seleccionado = st.selectbox(
                "Selecciona una prueba:",
                [
                    "Test de Normalidad (Shapiro-Wilk)",
                    "Test t para una muestra",
                    "Test t para muestras independientes",
                    "Correlación de Pearson",
                    "Correlación de Spearman"
                ]
            )
            
            # --- TEST DE NORMALIDAD ---
            if test_seleccionado == "Test de Normalidad (Shapiro-Wilk)":
                col_norm = st.selectbox("Columna a evaluar", cols_numericas, key="norm_col")
                
                if st.button("🔬 Ejecutar Shapiro-Wilk", type="primary"):
                    stat, p = stats.shapiro(df[col_norm].dropna())
                    
                    col_r1, col_r2 = st.columns(2)
                    col_r1.metric("Estadístico W", f"{stat:.4f}")
                    col_r2.metric("p-valor", f"{p:.4f}")
                    
                    st.write("---")
                    st.write("**Hipótesis:**")
                    st.write("- H₀: Los datos provienen de una distribución normal")
                    st.write("- H₁: Los datos NO provienen de una distribución normal")
                    
                    alpha = st.slider("Nivel de significancia (α)", 0.01, 0.10, 0.05, 0.01)
                    
                    if p > alpha:
                        st.success(f"✅ No se rechaza H₀ (p={p:.4f} > α={alpha}). Los datos parecen normales.")
                    else:
                        st.warning(f"⚠️ Se rechaza H₀ (p={p:.4f} ≤ α={alpha}). Los datos NO parecen normales.")
            
            # --- TEST T UNA MUESTRA ---
            elif test_seleccionado == "Test t para una muestra":
                col_ttest1 = st.selectbox("Columna", cols_numericas, key="ttest1_col")
                media_hip = st.number_input("Media hipotética (H₀)", value=0.0, step=0.1)
                
                if st.button("🔬 Ejecutar t-test", type="primary"):
                    stat, p = stats.ttest_1samp(df[col_ttest1].dropna(), popmean=media_hip)
                    
                    col_r1, col_r2 = st.columns(2)
                    col_r1.metric("Estadístico t", f"{stat:.4f}")
                    col_r2.metric("p-valor", f"{p:.4f}")
                    
                    alpha = st.slider("Nivel de significancia (α)", 0.01, 0.10, 0.05, 0.01, key="alpha_ttest1")
                    
                    if p > alpha:
                        st.success(f"✅ No se rechaza H₀. La media no difiere significativamente de {media_hip}.")
                    else:
                        st.warning(f"⚠️ Se rechaza H₀. La media difiere significativamente de {media_hip}.")
            
            # --- TEST T INDEPENDIENTE ---
            elif test_seleccionado == "Test t para muestras independientes":
                col_num = st.selectbox("Columna numérica", cols_numericas, key="ttestind_num")
                cols_cat = df.select_dtypes(include=['object', 'category']).columns.tolist()
                
                if cols_cat:
                    col_cat = st.selectbox("Columna categórica (2 grupos)", cols_cat, key="ttestind_cat")
                    grupos = df[col_cat].dropna().unique()
                    
                    if len(grupos) == 2:
                        grupo1 = df[df[col_cat] == grupos[0]][col_num].dropna()
                        grupo2 = df[df[col_cat] == grupos[1]][col_num].dropna()
                        
                        if st.button("🔬 Ejecutar t-test independiente", type="primary"):
                            stat, p = stats.ttest_ind(grupo1, grupo2)
                            
                            col_r1, col_r2, col_r3 = st.columns(3)
                            col_r1.metric("Estadístico t", f"{stat:.4f}")
                            col_r2.metric("p-valor", f"{p:.4f}")
                            col_r3.metric(f"Media {grupos[0]} vs {grupos[1]}", f"{grupo1.mean():.2f} vs {grupo2.mean():.2f}")
                            
                            alpha = st.slider("Nivel α", 0.01, 0.10, 0.05, 0.01, key="alpha_ttestind")
                            
                            if p > alpha:
                                st.success("✅ No se rechaza H₀. No hay diferencia significativa entre grupos.")
                            else:
                                st.warning("⚠️ Se rechaza H₀. Hay diferencia significativa entre grupos.")
                    else:
                        st.error(f"❌ La columna '{col_cat}' debe tener exactamente 2 grupos. Tiene {len(grupos)}.")
                else:
                    st.warning("⚠️ No se encontraron columnas categóricas para agrupar.")
            
            # --- CORRELACIÓN DE PEARSON ---
            elif test_seleccionado == "Correlación de Pearson":
                if len(cols_numericas) >= 2:
                    col_x = st.selectbox("Variable X", cols_numericas, key="pearson_x")
                    col_y = st.selectbox("Variable Y", cols_numericas, key="pearson_y")
                    
                    if st.button("🔬 Calcular correlación", type="primary"):
                        datos_x = df[col_x].dropna()
                        datos_y = df[col_y].dropna()
                        
                        # Usar solo filas donde ambas columnas tienen datos
                        mask = df[[col_x, col_y]].dropna().index
                        r, p = stats.pearsonr(df.loc[mask, col_x], df.loc[mask, col_y])
                        
                        col_r1, col_r2 = st.columns(2)
                        col_r1.metric("Coef. Pearson (r)", f"{r:.4f}")
                        col_r2.metric("p-valor", f"{p:.4f}")
                        
                        # Interpretación
                        if abs(r) < 0.3:
                            fuerza = "débil"
                        elif abs(r) < 0.7:
                            fuerza = "moderada"
                        else:
                            fuerza = "fuerte"
                        direccion = "positiva" if r > 0 else "negativa"
                        
                        st.info(f"📌 Correlación **{fuerza}** y **{direccion}** (r={r:.3f}, p={p:.4f})")
                        
                        # Scatter plot
                        fig = px.scatter(
                            x=df.loc[mask, col_x], y=df.loc[mask, col_y],
                            trendline='ols',
                            title=f"{col_x} vs {col_y}",
                            labels={'x': col_x, 'y': col_y}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("⚠️ Se necesitan al menos 2 columnas numéricas.")
            
            # --- CORRELACIÓN DE SPEARMAN ---
            elif test_seleccionado == "Correlación de Spearman":
                if len(cols_numericas) >= 2:
                    col_x = st.selectbox("Variable X", cols_numericas, key="spearman_x")
                    col_y = st.selectbox("Variable Y", cols_numericas, key="spearman_y")
                    
                    if st.button("🔬 Calcular correlación", type="primary"):
                        mask = df[[col_x, col_y]].dropna().index
                        rho, p = stats.spearmanr(df.loc[mask, col_x], df.loc[mask, col_y])
                        
                        col_r1, col_r2 = st.columns(2)
                        col_r1.metric("Coef. Spearman (ρ)", f"{rho:.4f}")
                        col_r2.metric("p-valor", f"{p:.4f}")
                        
                        st.info(f"📌 Correlación de Spearman: ρ={rho:.3f}, p={p:.4f}")
                        
                        fig = px.scatter(
                            x=df.loc[mask, col_x], y=df.loc[mask, col_y],
                            title=f"{col_x} vs {col_y} (Spearman)",
                            labels={'x': col_x, 'y': col_y}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("⚠️ Se necesitan al menos 2 columnas numéricas.")
        
        else:
            st.warning("⚠️ No hay columnas numéricas para realizar tests.")
    
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
