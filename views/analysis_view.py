"""
Vista de Análisis - Selección de variables y ejecución de tests.
"""

import customtkinter as ctk
from database import get_dataframe
import statistics as stats_engine
import json


class AnalysisView:
    """Vista de análisis estadístico."""
    
    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        self.df = None
        
        if self.app.dataset_loaded:
            self.df = get_dataframe(self.app.table_name)
        
        self._build()
    
    def _build(self):
        # Título
        header = ctk.CTkFrame(self.parent, fg_color="transparent", height=50)
        header.pack(fill="x", padx=28, pady=(24, 12))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="Análisis Estadístico",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color="#1A1A1A",
        ).pack(side="left")
        
        if not self.app.dataset_loaded:
            self._show_empty()
            return
        
        # Panel de selección de análisis
        self._build_analysis_panel()
    
    def _show_empty(self):
        empty = ctk.CTkFrame(
            self.parent,
            fg_color="#FFFFFF",
            corner_radius=12,
            border_width=1,
            border_color="#E5E7EB",
        )
        empty.pack(fill="both", expand=True, padx=28, pady=20)
        
        ctk.CTkLabel(
            empty,
            text="Primero importa un dataset para comenzar el análisis",
            font=ctk.CTkFont(family="Inter", size=14),
            text_color="#6B7280",
        ).pack(expand=True)
    
    def _build_analysis_panel(self):
        """Panel principal de análisis."""
        # Contenedor principal con dos columnas
        container = ctk.CTkFrame(self.parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=28)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=2)
        
        # --- COLUMNA IZQUIERDA: Selectores ---
        left = ctk.CTkFrame(
            container,
            fg_color="#FFFFFF",
            corner_radius=12,
            border_width=1,
            border_color="#E5E7EB",
        )
        left.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        
        ctk.CTkLabel(
            left,
            text="Configuración del análisis",
            font=ctk.CTkFont(family="Inter", size=14, weight="600"),
            text_color="#1A1A1A",
        ).pack(anchor="w", padx=20, pady=(16, 12))
        
        # Tipo de análisis
        ctk.CTkLabel(
            left,
            text="Tipo de análisis",
            font=ctk.CTkFont(family="Inter", size=11, weight="600"),
            text_color="#6B7280",
        ).pack(anchor="w", padx=20, pady=(8, 4))
        
        analisis_options = [
            "Descriptivos",
            "Frecuencias (categórica)",
            "Prueba de normalidad",
            "Comparar 2 grupos (t-test)",
            "Comparar 2 grupos (Mann-Whitney)",
            "ANOVA",
            "Correlación de Pearson",
            "Correlación de Spearman",
            "Regresión lineal",
            "Chi-cuadrado",
        ]
        
        self.analisis_var = ctk.StringVar(value=analisis_options[0])
        self.analisis_menu = ctk.CTkOptionMenu(
            left,
            values=analisis_options,
            variable=self.analisis_var,
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color="#F9FAFB",
            text_color="#1A1A1A",
            button_color="#E5E7EB",
            button_hover_color="#D1D5DB",
            corner_radius=8,
            height=36,
            command=self._on_analisis_change,
        )
        self.analisis_menu.pack(fill="x", padx=20, pady=(0, 16))
        
        # Variables numéricas disponibles
        self.vars_numericas = [
            v for v, info in self.app.variables.items()
            if "numérica" in info.get("tipo", "")
        ]
        self.vars_categoricas = [
            v for v, info in self.app.variables.items()
            if "categórica" in info.get("tipo", "")
        ]
        self.vars_todas = list(self.app.variables.keys())
        
        # Selector variable principal
        ctk.CTkLabel(
            left,
            text="Variable",
            font=ctk.CTkFont(family="Inter", size=11, weight="600"),
            text_color="#6B7280",
        ).pack(anchor="w", padx=20, pady=(8, 4))
        
        self.var1_var = ctk.StringVar()
        self.var1_menu = ctk.CTkOptionMenu(
            left,
            values=self.vars_todas,
            variable=self.var1_var,
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color="#F9FAFB",
            text_color="#1A1A1A",
            button_color="#E5E7EB",
            button_hover_color="#D1D5DB",
            corner_radius=8,
            height=36,
        )
        self.var1_menu.pack(fill="x", padx=20, pady=(0, 12))
        
        # Selector variable secundaria (visible según análisis)
        self.var2_label = ctk.CTkLabel(
            left,
            text="Variable secundaria",
            font=ctk.CTkFont(family="Inter", size=11, weight="600"),
            text_color="#6B7280",
        )
        
        self.var2_var = ctk.StringVar()
        self.var2_menu = ctk.CTkOptionMenu(
            left,
            values=self.vars_todas,
            variable=self.var2_var,
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color="#F9FAFB",
            text_color="#1A1A1A",
            button_color="#E5E7EB",
            button_hover_color="#D1D5DB",
            corner_radius=8,
            height=36,
        )
        
        self._toggle_var2(analisis_options[0])
        
        # Botón ejecutar
        ctk.CTkButton(
            left,
            text="Ejecutar análisis",
            font=ctk.CTkFont(family="Inter", size=13, weight="500"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            corner_radius=8,
            height=38,
            command=self._run_analysis,
        ).pack(fill="x", padx=20, pady=(20, 16))
        
        # --- COLUMNA DERECHA: Resultados ---
        right = ctk.CTkFrame(
            container,
            fg_color="#FFFFFF",
            corner_radius=12,
            border_width=1,
            border_color="#E5E7EB",
        )
        right.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        
        ctk.CTkLabel(
            right,
            text="Resultados",
            font=ctk.CTkFont(family="Inter", size=14, weight="600"),
            text_color="#1A1A1A",
        ).pack(anchor="w", padx=20, pady=(16, 12))
        
        self.resultados_frame = ctk.CTkScrollableFrame(
            right,
            fg_color="transparent",
            scrollbar_button_color="#E5E7EB",
        )
        self.resultados_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        self.resultados_label = ctk.CTkLabel(
            self.resultados_frame,
            text="Selecciona las variables y haz clic en 'Ejecutar análisis'.",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color="#6B7280",
            wraplength=400,
        )
        self.resultados_label.pack(padx=16, pady=20)
    
    def _on_analisis_change(self, value):
        """Muestra/oculta selector de segunda variable según el análisis."""
        self._toggle_var2(value)
    
    def _toggle_var2(self, analisis):
        """Controla visibilidad del segundo selector."""
        necesita_var2 = analisis not in [
            "Descriptivos",
            "Frecuencias (categórica)",
            "Prueba de normalidad",
        ]
        
        if necesita_var2:
            self.var2_label.pack(anchor="w", padx=20, pady=(12, 4))
            self.var2_menu.pack(fill="x", padx=20, pady=(0, 12))
        else:
            self.var2_label.pack_forget()
            self.var2_menu.pack_forget()
    
    def _run_analysis(self):
        """Ejecuta el análisis seleccionado."""
        analisis = self.analisis_var.get()
        var1 = self.var1_var.get()
        var2 = self.var2_var.get() if self.var2_menu.winfo_ismapped() else None
        
        if not var1:
            self._show_result("Selecciona al menos una variable.")
            return
        
        if not self.var2_menu.winfo_ismapped():
            var2 = None
        
        try:
            if analisis == "Descriptivos":
                result = stats_engine.descriptivos(self.df, var1)
            elif analisis == "Frecuencias (categórica)":
                result = stats_engine.frecuencia_categorica(self.df, var1)
            elif analisis == "Prueba de normalidad":
                result = stats_engine.normalidad(self.df, var1)
            elif analisis == "Comparar 2 grupos (t-test)":
                result = stats_engine.comparar_dos_grupos(self.df, var1, var2, "ttest")
            elif analisis == "Comparar 2 grupos (Mann-Whitney)":
                result = stats_engine.comparar_dos_grupos(self.df, var1, var2, "mannwhitney")
            elif analisis == "ANOVA":
                result = stats_engine.anova(self.df, var1, var2)
            elif analisis == "Correlación de Pearson":
                result = stats_engine.correlacion(self.df, var1, var2, "pearson")
            elif analisis == "Correlación de Spearman":
                result = stats_engine.correlacion(self.df, var1, var2, "spearman")
            elif analisis == "Regresión lineal":
                result = stats_engine.regresion_lineal(self.df, var1, var2)
            elif analisis == "Chi-cuadrado":
                result = stats_engine.chi_cuadrado(self.df, var1, var2)
            
            self._show_result(json.dumps(result, indent=2, ensure_ascii=False))
        
        except Exception as e:
            self._show_result(f"Error: {str(e)}")
    
    def _show_result(self, text):
        """Muestra resultado en el panel derecho."""
        for widget in self.resultados_frame.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(
            self.resultados_frame,
            text=text,
            font=ctk.CTkFont(family="SF Mono", size=11),
            text_color="#1A1A1A",
            justify="left",
            wraplength=420,
        ).pack(padx=16, pady=12, anchor="w")
