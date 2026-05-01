"""
Vista de Gráficos - Generación de visualizaciones.
"""

import customtkinter as ctk
from database import get_dataframe, get_variable_data
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import numpy as np
from pathlib import Path
import tempfile
import webbrowser
import os


class GraphsView:
    """Vista de gráficos estadísticos."""
    
    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        
        self._build()
    
    def _build(self):
        header = ctk.CTkFrame(self.parent, fg_color="transparent", height=50)
        header.pack(fill="x", padx=28, pady=(24, 12))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="Gráficos",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color="#1A1A1A",
        ).pack(side="left")
        
        if not self.app.dataset_loaded:
            self._show_empty()
            return
        
        self._build_graph_panel()
    
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
            text="Importa un dataset para generar gráficos",
            font=ctk.CTkFont(family="Inter", size=14),
            text_color="#6B7280",
        ).pack(expand=True)
    
    def _build_graph_panel(self):
        """Panel de selección de gráficos."""
        container = ctk.CTkFrame(self.parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=28, pady=8)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=3)
        
        # Panel izquierdo
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
            text="Tipo de gráfico",
            font=ctk.CTkFont(family="Inter", size=14, weight="600"),
            text_color="#1A1A1A",
        ).pack(anchor="w", padx=20, pady=(16, 12))
        
        graph_types = [
            "Histograma",
            "Boxplot",
            "Dispersión",
            "Q-Q Plot",
            "Barras (categórica)",
            "Kaplan-Meier",
        ]
        
        self.graph_var = ctk.StringVar(value=graph_types[0])
        for gtype in graph_types:
            ctk.CTkRadioButton(
                left,
                text=gtype,
                variable=self.graph_var,
                value=gtype,
                font=ctk.CTkFont(family="Inter", size=12),
                fg_color="#2563EB",
                hover_color="#1D4ED8",
            ).pack(anchor="w", padx=20, pady=4)
        
        # Selectores de variables
        ctk.CTkLabel(
            left,
            text="Variables",
            font=ctk.CTkFont(family="Inter", size=12, weight="600"),
            text_color="#6B7280",
        ).pack(anchor="w", padx=20, pady=(20, 8))
        
        vars_list = list(self.app.variables.keys())
        
        ctk.CTkLabel(
            left,
            text="Variable X / Principal",
            font=ctk.CTkFont(family="Inter", size=10),
            text_color="#9CA3AF",
        ).pack(anchor="w", padx=20)
        
        self.x_var = ctk.StringVar()
        ctk.CTkOptionMenu(
            left,
            values=vars_list,
            variable=self.x_var,
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color="#F9FAFB",
            text_color="#1A1A1A",
            corner_radius=8,
            height=34,
        ).pack(fill="x", padx=20, pady=(2, 10))
        
        ctk.CTkLabel(
            left,
            text="Variable Y / Secundaria (opcional)",
            font=ctk.CTkFont(family="Inter", size=10),
            text_color="#9CA3AF",
        ).pack(anchor="w", padx=20)
        
        self.y_var = ctk.StringVar()
        ctk.CTkOptionMenu(
            left,
            values=["(ninguna)"] + vars_list,
            variable=self.y_var,
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color="#F9FAFB",
            text_color="#1A1A1A",
            corner_radius=8,
            height=34,
        ).pack(fill="x", padx=20, pady=(2, 16))
        
        ctk.CTkButton(
            left,
            text="Generar gráfico",
            font=ctk.CTkFont(family="Inter", size=13, weight="500"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            corner_radius=8,
            height=38,
            command=self._generate_graph,
        ).pack(fill="x", padx=20, pady=(8, 16))
        
        # Panel derecho para el gráfico
        self.right = ctk.CTkFrame(
            container,
            fg_color="#FFFFFF",
            corner_radius=12,
            border_width=1,
            border_color="#E5E7EB",
        )
        self.right.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        
        ctk.CTkLabel(
            self.right,
            text="Vista previa",
            font=ctk.CTkFont(family="Inter", size=14, weight="600"),
            text_color="#1A1A1A",
        ).pack(anchor="w", padx=20, pady=(16, 8))
        
        self.graph_status = ctk.CTkLabel(
            self.right,
            text="Selecciona variables y haz clic en 'Generar gráfico'.",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color="#6B7280",
        )
        self.graph_status.pack(expand=True)
    
    def _generate_graph(self):
        """Genera el gráfico y lo abre en el navegador."""
        df = get_dataframe(self.app.table_name)
        gtype = self.graph_var.get()
        x = self.x_var.get()
        y = self.y_var.get() if self.y_var.get() != "(ninguna)" else None
        
        if not x:
            self.graph_status.configure(text="Selecciona al menos la variable X.")
            return
        
        try:
            if gtype == "Histograma":
                fig = px.histogram(df[x].dropna(), nbins=30, title=f"Histograma de {x}",
                                  color_discrete_sequence=["#2563EB"])
            elif gtype == "Boxplot":
                if y:
                    fig = px.box(df, x=y, y=x, title=f"Boxplot de {x} por {y}",
                                color_discrete_sequence=["#2563EB"])
                else:
                    fig = px.box(df, y=x, title=f"Boxplot de {x}",
                                color_discrete_sequence=["#2563EB"])
            elif gtype == "Dispersión":
                if not y:
                    self.graph_status.configure(text="Selecciona variable Y para dispersión.")
                    return
                fig = px.scatter(df, x=x, y=y, trendline='ols',
                                title=f"{y} vs {x}")
            elif gtype == "Q-Q Plot":
                datos = df[x].dropna().sort_values()
                teoricos = stats.norm.ppf((np.arange(1, len(datos)+1) - 0.5) / len(datos))
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=teoricos, y=datos, mode='markers',
                                        marker=dict(color="#2563EB", size=4)))
                fig.add_trace(go.Scatter(
                    x=[teoricos.min(), teoricos.max()],
                    y=[teoricos.min(), teoricos.max()],
                    mode='lines', line=dict(dash='dash', color='gray')
                ))
                fig.update_layout(title=f"Q-Q Plot: {x}")
            elif gtype == "Barras (categórica)":
                conteo = df[x].value_counts().head(20)
                fig = px.bar(x=conteo.index, y=conteo.values,
                            title=f"Frecuencia de {x}",
                            labels={'x': x, 'y': 'Frecuencia'},
                            color_discrete_sequence=["#2563EB"])
            elif gtype == "Kaplan-Meier":
                if not y:
                    self.graph_status.configure(text="Selecciona variable de evento (0/1) en Y.")
                    return
                from lifelines import KaplanMeierFitter
                kmf = KaplanMeierFitter()
                kmf.fit(df[x], event_observed=df[y], label="Global")
                fig = kmf.plot_survival_function()
                fig = fig.figure  # Convertir a figura matplotlib
            
            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font_family="Inter",
                title_font_size=16,
            )
            
            # Guardar HTML temporal y abrir en navegador
            tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
            fig.write_html(tmp.name)
            webbrowser.open(f"file://{tmp.name}")
            
            self.graph_status.configure(text=f"Grafico '{gtype}' generado y abierto en el navegador.")
        
        except Exception as e:
            self.graph_status.configure(text=f"Error: {str(e)}")
