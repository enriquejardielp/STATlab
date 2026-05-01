"""
Vista de Gráficos - Generación de visualizaciones.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QComboBox, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database import get_dataframe
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import numpy as np
import tempfile
import webbrowser


COLORS = {
    "bg_primary": "#FAFAFA",
    "bg_card": "#FFFFFF",
    "text_primary": "#1A1A1A",
    "text_secondary": "#6B7280",
    "text_muted": "#9CA3AF",
    "accent": "#2563EB",
    "accent_hover": "#1D4ED8",
    "border": "#E5E7EB",
    "input_bg": "#F9FAFB",
}


class GraphsView(QWidget):
    """Vista de gráficos estadísticos."""
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(28, 24, 28, 20)
        self.layout.setSpacing(12)
        
        title = QLabel("Gráficos")
        title.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.layout.addWidget(title)
        
        self.content = QVBoxLayout()
        self.layout.addLayout(self.content)
        self.layout.addStretch()
    
    def refresh(self):
        """Refresca la vista."""
        while self.content.count():
            item = self.content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.app.dataset_loaded:
            self._show_empty()
            return
        
        self.df = get_dataframe(self.app.table_name)
        self._build_panel()
    
    def _show_empty(self):
        empty = QFrame()
        empty.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(empty)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg = QLabel("Importa un dataset para generar gráficos")
        msg.setFont(QFont("Inter", 14))
        msg.setStyleSheet(f"color: {COLORS['text_secondary']};")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)
        self.content.addWidget(empty)
    
    def _build_panel(self):
        """Construye el panel de gráficos."""
        container = QHBoxLayout()
        container.setSpacing(12)
        
        # Panel izquierdo
        left = QFrame()
        left.setFixedWidth(300)
        left.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(20, 16, 20, 16)
        left_layout.setSpacing(8)
        
        title_l = QLabel("Tipo de gráfico")
        title_l.setFont(QFont("Inter", 14, QFont.Weight.DemiBold))
        title_l.setStyleSheet(f"color: {COLORS['text_primary']};")
        left_layout.addWidget(title_l)
        
        self.graph_group = QButtonGroup(self)
        tipos = ["Histograma", "Boxplot", "Dispersión", "Q-Q Plot", "Barras", "Kaplan-Meier"]
        
        for i, tipo in enumerate(tipos):
            radio = QRadioButton(tipo)
            radio.setFont(QFont("Inter", 12))
            radio.setStyleSheet(f"color: {COLORS['text_primary']}; margin: 4px 0;")
            if i == 0:
                radio.setChecked(True)
            self.graph_group.addButton(radio, i)
            left_layout.addWidget(radio)
        
        left_layout.addSpacing(16)
        
        # Variable X
        label_x = QLabel("Variable X / Principal")
        label_x.setFont(QFont("Inter", 11, QFont.Weight.DemiBold))
        label_x.setStyleSheet(f"color: {COLORS['text_secondary']};")
        left_layout.addWidget(label_x)
        
        self.combo_x = QComboBox()
        self.combo_x.setFont(QFont("Inter", 12))
        self.combo_x.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['input_bg']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
            }}
        """)
        self.combo_x.addItems(list(self.app.variables.keys()))
        left_layout.addWidget(self.combo_x)
        
        # Variable Y
        label_y = QLabel("Variable Y / Secundaria (opcional)")
        label_y.setFont(QFont("Inter", 11, QFont.Weight.DemiBold))
        label_y.setStyleSheet(f"color: {COLORS['text_secondary']};")
        left_layout.addWidget(label_y)
        
        self.combo_y = QComboBox()
        self.combo_y.setFont(QFont("Inter", 12))
        self.combo_y.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['input_bg']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
            }}
        """)
        vars_list = ["(ninguna)"] + list(self.app.variables.keys())
        self.combo_y.addItems(vars_list)
        left_layout.addWidget(self.combo_y)
        
        left_layout.addSpacing(16)
        
        btn = QPushButton("Generar gráfico")
        btn.setFont(QFont("Inter", 13, QFont.Weight.Medium))
        btn.setFixedHeight(38)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
        """)
        btn.clicked.connect(self._generate_graph)
        left_layout.addWidget(btn)
        
        left_layout.addStretch()
        
        container.addWidget(left)
        
        # Panel derecho
        right = QFrame()
        right.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 16, 20, 16)
        
        title_r = QLabel("Vista previa")
        title_r.setFont(QFont("Inter", 14, QFont.Weight.DemiBold))
        title_r.setStyleSheet(f"color: {COLORS['text_primary']};")
        right_layout.addWidget(title_r)
        
        self.status = QLabel("Selecciona variables y haz clic en 'Generar gráfico'.")
        self.status.setFont(QFont("Inter", 12))
        self.status.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.status)
        
        container.addWidget(right, 1)
        
        self.content.addLayout(container)
    
    def _generate_graph(self):
        """Genera gráfico y lo abre en navegador."""
        if not self.app.dataset_loaded:
            return
        
        tipo_idx = self.graph_group.checkedId()
        tipos = ["histograma", "boxplot", "dispersion", "qq", "barras", "kaplan"]
        tipo = tipos[tipo_idx]
        
        x = self.combo_x.currentText()
        y = self.combo_y.currentText()
        if y == "(ninguna)":
            y = None
        
        if not x:
            self.status.setText("Selecciona al menos la variable X.")
            return
        
        try:
            if tipo == "histograma":
                fig = px.histogram(self.df[x].dropna(), nbins=30, title=f"Histograma de {x}",
                                  color_discrete_sequence=["#2563EB"])
            elif tipo == "boxplot":
                if y:
                    fig = px.box(self.df, x=y, y=x, title=f"Boxplot de {x} por {y}",
                                color_discrete_sequence=["#2563EB"])
                else:
                    fig = px.box(self.df, y=x, title=f"Boxplot de {x}",
                                color_discrete_sequence=["#2563EB"])
            elif tipo == "dispersion":
                if not y:
                    self.status.setText("Selecciona variable Y.")
                    return
                fig = px.scatter(self.df, x=x, y=y, trendline='ols', title=f"{y} vs {x}")
            elif tipo == "qq":
                datos = self.df[x].dropna().sort_values()
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
            elif tipo == "barras":
                conteo = self.df[x].value_counts().head(20)
                fig = px.bar(x=conteo.index, y=conteo.values,
                            title=f"Frecuencia de {x}",
                            labels={'x': x, 'y': 'Frecuencia'},
                            color_discrete_sequence=["#2563EB"])
            elif tipo == "kaplan":
                if not y:
                    self.status.setText("Selecciona variable de evento (0/1) en Y.")
                    return
                from lifelines import KaplanMeierFitter
                kmf = KaplanMeierFitter()
                kmf.fit(self.df[x], event_observed=self.df[y], label="Global")
                fig = kmf.plot_survival_function()
                fig = fig.figure
            
            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font_family="Inter",
                title_font_size=16,
            )
            
            tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
            fig.write_html(tmp.name)
            webbrowser.open(f"file://{tmp.name}")
            
            self.status.setText(f"Gráfico '{tipo}' generado y abierto en el navegador.")
        
        except Exception as e:
            self.status.setText(f"Error: {str(e)}")
