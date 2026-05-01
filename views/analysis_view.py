"""
Vista de Análisis - Selección de variables y ejecución de tests.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QComboBox, QScrollArea, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database import get_dataframe
import statistics as stats_engine
import json


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


class AnalysisView(QWidget):
    """Vista de análisis estadístico."""
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.df = None
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(28, 24, 28, 20)
        self.layout.setSpacing(12)
        
        # Header
        title = QLabel("Análisis Estadístico")
        title.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.layout.addWidget(title)
        
        # Contenido
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
        
        msg = QLabel("Importa un dataset para realizar análisis")
        msg.setFont(QFont("Inter", 14))
        msg.setStyleSheet(f"color: {COLORS['text_secondary']};")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)
        
        self.content.addWidget(empty)
    
    def _build_panel(self):
        """Construye el panel de análisis."""
        container = QHBoxLayout()
        container.setSpacing(12)
        
        # ---- Panel izquierdo ----
        left = QFrame()
        left.setFixedWidth(340)
        left.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(20, 16, 20, 16)
        left_layout.setSpacing(12)
        
        title_l = QLabel("Configuración del análisis")
        title_l.setFont(QFont("Inter", 14, QFont.Weight.DemiBold))
        title_l.setStyleSheet(f"color: {COLORS['text_primary']};")
        left_layout.addWidget(title_l)
        
        # Tipo de análisis
        label1 = QLabel("Tipo de análisis")
        label1.setFont(QFont("Inter", 11, QFont.Weight.DemiBold))
        label1.setStyleSheet(f"color: {COLORS['text_secondary']};")
        left_layout.addWidget(label1)
        
        self.analisis_combo = QComboBox()
        self.analisis_combo.setFont(QFont("Inter", 12))
        self.analisis_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['input_bg']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
            }}
            QComboBox:hover {{ border-color: {COLORS['accent']}; }}
            QComboBox::drop-down {{ border: none; }}
        """)
        self.analisis_combo.addItems([
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
        ])
        self.analisis_combo.currentTextChanged.connect(self._toggle_var2)
        left_layout.addWidget(self.analisis_combo)
        
        # Variable 1
        label2 = QLabel("Variable")
        label2.setFont(QFont("Inter", 11, QFont.Weight.DemiBold))
        label2.setStyleSheet(f"color: {COLORS['text_secondary']};")
        left_layout.addWidget(label2)
        
        self.var1_combo = QComboBox()
        self.var1_combo.setFont(QFont("Inter", 12))
        self.var1_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['input_bg']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
            }}
        """)
        self.var1_combo.addItems(list(self.app.variables.keys()))
        left_layout.addWidget(self.var1_combo)
        
        # Variable 2 (opcional)
        self.var2_label = QLabel("Variable secundaria")
        self.var2_label.setFont(QFont("Inter", 11, QFont.Weight.DemiBold))
        self.var2_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        left_layout.addWidget(self.var2_label)
        
        self.var2_combo = QComboBox()
        self.var2_combo.setFont(QFont("Inter", 12))
        self.var2_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['input_bg']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
            }}
        """)
        self.var2_combo.addItems(list(self.app.variables.keys()))
        left_layout.addWidget(self.var2_combo)
        
        self._toggle_var2("Descriptivos")
        
        left_layout.addSpacing(12)
        
        # Botón ejecutar
        btn = QPushButton("Ejecutar análisis")
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
        btn.clicked.connect(self._run_analysis)
        left_layout.addWidget(btn)
        
        left_layout.addStretch()
        
        container.addWidget(left)
        
        # ---- Panel derecho: resultados ----
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
        
        title_r = QLabel("Resultados")
        title_r.setFont(QFont("Inter", 14, QFont.Weight.DemiBold))
        title_r.setStyleSheet(f"color: {COLORS['text_primary']};")
        right_layout.addWidget(title_r)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(QFont("SF Mono", 11))
        self.result_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: {COLORS['text_primary']};
                border: none;
                padding: 8px;
            }}
        """)
        self.result_text.setPlaceholderText("Selecciona variables y haz clic en 'Ejecutar análisis'.")
        right_layout.addWidget(self.result_text)
        
        container.addWidget(right, 1)
        
        self.content.addLayout(container)
    
    def _toggle_var2(self, text):
        """Muestra u oculta el selector de segunda variable."""
        necesita = text not in ["Descriptivos", "Frecuencias (categórica)", "Prueba de normalidad"]
        self.var2_label.setVisible(necesita)
        self.var2_combo.setVisible(necesita)
    
    def _run_analysis(self):
        """Ejecuta el análisis seleccionado."""
        if not self.app.dataset_loaded:
            return
        
        analisis = self.analisis_combo.currentText()
        var1 = self.var1_combo.currentText()
        var2 = self.var2_combo.currentText() if self.var2_combo.isVisible() else None
        
        if not var1:
            self.result_text.setText("Selecciona al menos una variable.")
            return
        
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
            
            self.result_text.setText(json.dumps(result, indent=2, ensure_ascii=False))
        
        except Exception as e:
            self.result_text.setText(f"Error: {str(e)}")
