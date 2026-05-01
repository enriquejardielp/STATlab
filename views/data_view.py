"""
Vista de Datos - Tabla de variables y metadatos.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database import import_dataset, get_dataframe


COLORS = {
    "bg_primary": "#FAFAFA",
    "bg_card": "#FFFFFF",
    "text_primary": "#1A1A1A",
    "text_secondary": "#6B7280",
    "text_muted": "#9CA3AF",
    "accent": "#2563EB",
    "accent_hover": "#1D4ED8",
    "border": "#E5E7EB",
}


class DataView(QWidget):
    """Vista de gestión de datos."""
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(28, 24, 28, 20)
        self.layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Gestión de Datos")
        title.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        header.addWidget(title)
        header.addStretch()
        
        btn_import = QPushButton("Importar nuevo dataset")
        btn_import.setFont(QFont("Inter", 12, QFont.Weight.Medium))
        btn_import.setFixedHeight(34)
        btn_import.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_import.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
        """)
        btn_import.clicked.connect(lambda: import_dataset(self.app))
        header.addWidget(btn_import)
        
        self.layout.addLayout(header)
        
        # Área de contenido
        self.content = QVBoxLayout()
        self.layout.addLayout(self.content)
        self.layout.addStretch()
    
    def refresh(self):
        """Refresca la vista."""
        # Limpiar
        while self.content.count():
            item = self.content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.app.dataset_loaded:
            self._show_empty()
            return
        
        # Info del dataset
        info = QFrame()
        info.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        info_layout = QGridLayout(info)
        info_layout.setSpacing(16)
        
        metrics = [
            ("DATASET", self.app.dataset_name),
            ("REGISTROS", str(len(get_dataframe(self.app.table_name)))),
            ("VARIABLES", str(len(self.app.variables))),
            ("BASE DE DATOS", "DuckDB (local)"),
        ]
        
        for i, (label, value) in enumerate(metrics):
            col = QVBoxLayout()
            l = QLabel(label)
            l.setFont(QFont("Inter", 9, QFont.Weight.Bold))
            l.setStyleSheet(f"color: {COLORS['text_secondary']};")
            col.addWidget(l)
            
            v = QLabel(value)
            v.setFont(QFont("Inter", 15, QFont.Weight.DemiBold))
            v.setStyleSheet(f"color: {COLORS['text_primary']};")
            col.addWidget(v)
            
            info_layout.addLayout(col, 0, i)
        
        self.content.addWidget(info)
        
        # Tabla de variables
        self.content.addSpacing(8)
        
        table_frame = QFrame()
        table_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        table_layout = QVBoxLayout(table_frame)
        
        title_vars = QLabel("Variables del dataset")
        title_vars.setFont(QFont("Inter", 14, QFont.Weight.DemiBold))
        title_vars.setStyleSheet(f"color: {COLORS['text_primary']};")
        table_layout.addWidget(title_vars)
        
        # Scroll con variables
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        vars_widget = QWidget()
        vars_layout = QVBoxLayout(vars_widget)
        vars_layout.setSpacing(2)
        
        tipo_labels = {
            "numérica_continua": "Numérica continua",
            "numérica_discreta": "Numérica discreta",
            "categórica_nominal": "Categórica nominal",
            "categórica_ordinal": "Categórica ordinal",
            "categórica_dicotómica": "Categórica dicotómica",
            "texto_libre": "Texto libre",
        }
        
        for var_name, info in self.app.variables.items():
            row = QFrame()
            row.setFixedHeight(34)
            row.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 0, 12, 0)
            
            tipo_display = tipo_labels.get(info.get("tipo", ""), info.get("tipo", "?"))
            n_unique = info.get("valores_unicos", "?")
            faltantes = "Sí" if info.get("tiene_valores_faltantes") else "No"
            desc = info.get("descripcion", "")[:30]
            
            name_lbl = QLabel(var_name)
            name_lbl.setFont(QFont("Inter", 11))
            name_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
            name_lbl.setMinimumWidth(180)
            row_layout.addWidget(name_lbl)
            
            tipo_lbl = QLabel(tipo_display)
            tipo_lbl.setFont(QFont("Inter", 10))
            tipo_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
            tipo_lbl.setMinimumWidth(150)
            row_layout.addWidget(tipo_lbl)
            
            uniq_lbl = QLabel(f"{n_unique} valores")
            uniq_lbl.setFont(QFont("Inter", 10))
            uniq_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
            row_layout.addWidget(uniq_lbl)
            
            null_lbl = QLabel(f"Faltantes: {faltantes}")
            null_lbl.setFont(QFont("Inter", 10))
            null_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
            row_layout.addWidget(null_lbl)
            
            desc_lbl = QLabel(desc)
            desc_lbl.setFont(QFont("Inter", 10))
            desc_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
            row_layout.addWidget(desc_lbl)
            
            row_layout.addStretch()
            vars_layout.addWidget(row)
        
        vars_layout.addStretch()
        scroll.setWidget(vars_widget)
        table_layout.addWidget(scroll)
        
        self.content.addWidget(table_frame)
    
    def _show_empty(self):
        """Muestra estado vacío."""
        empty = QFrame()
        empty.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        empty_layout = QVBoxLayout(empty)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        msg = QLabel("No hay ningún dataset cargado")
        msg.setFont(QFont("Inter", 14))
        msg.setStyleSheet(f"color: {COLORS['text_secondary']};")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(msg)
        
        self.content.addWidget(empty)
