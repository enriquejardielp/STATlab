"""
STATlab - Ventana principal con navegación lateral.
Framework: PyQt6
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QAction
from database import import_dataset, get_dataframe
from views.data_view import DataView
from views.analysis_view import AnalysisView
from views.graphs_view import GraphsView


# Paleta corporativa
COLORS = {
    "bg_primary": "#FAFAFA",
    "bg_sidebar": "#F5F5F5",
    "bg_card": "#FFFFFF",
    "text_primary": "#1A1A1A",
    "text_secondary": "#6B7280",
    "text_muted": "#9CA3AF",
    "accent": "#2563EB",
    "accent_hover": "#1D4ED8",
    "accent_light": "#EFF6FF",
    "border": "#E5E7EB",
    "success": "#059669",
    "warning": "#D97706",
    "error": "#DC2626",
}


class MainWindow(QMainWindow):
    """Ventana principal de STATlab."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("STATlab")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 600)
        
        # Estado
        self.dataset_loaded = False
        self.dataset_name = ""
        self.table_name = ""
        self.variables = {}
        
        self._build_ui()
        self._apply_styles()
    
    def _build_ui(self):
        """Construye la interfaz."""
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ---- SIDEBAR ----
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_sidebar']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Logo
        logo = QLabel("STATlab")
        logo.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        logo.setStyleSheet(f"color: {COLORS['text_primary']}; padding: 28px 20px 12px 20px;")
        sidebar_layout.addWidget(logo)
        
        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {COLORS['border']}; margin: 0 16px;")
        sep.setFixedHeight(1)
        sidebar_layout.addWidget(sep)
        sidebar_layout.addSpacing(16)
        
        # Navegación
        nav_items = [
            ("Datos", "data"),
            ("Análisis", "analysis"),
            ("Gráficos", "graphs"),
        ]
        
        self.nav_buttons = {}
        for text, key in nav_items:
            btn = QPushButton(text)
            btn.setFont(QFont("Inter", 13, QFont.Weight.Medium))
            btn.setFixedHeight(38)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['text_secondary']};
                    text-align: left;
                    padding-left: 20px;
                    border: none;
                    border-radius: 8px;
                    margin: 2px 10px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['border']};
                    color: {COLORS['text_primary']};
                }}
            """)
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))
            sidebar_layout.addWidget(btn)
            self.nav_buttons[key] = btn
        
        sidebar_layout.addStretch()
        
        # Footer
        footer = QLabel("v2.0 · Desktop")
        footer.setFont(QFont("Inter", 10))
        footer.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 0 0 16px 20px;")
        sidebar_layout.addWidget(footer)
        
        main_layout.addWidget(self.sidebar)
        
        # ---- ÁREA PRINCIPAL ----
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        
        # Vistas
        self.data_view = DataView(self)
        self.analysis_view = AnalysisView(self)
        self.graphs_view = GraphsView(self)
        self.welcome_view = self._build_welcome()
        
        self.stack.addWidget(self.welcome_view)    # 0
        self.stack.addWidget(self.data_view)       # 1
        self.stack.addWidget(self.analysis_view)   # 2
        self.stack.addWidget(self.graphs_view)     # 3
        
        main_layout.addWidget(self.stack)
    
    def _build_welcome(self):
        """Pantalla de bienvenida."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card = QFrame()
        card.setFixedSize(500, 320)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(8)
        
        title = QLabel("STATlab")
        title.setFont(QFont("Inter", 28, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)
        
        subtitle = QLabel("Análisis estadístico profesional")
        subtitle.setFont(QFont("Inter", 14))
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(subtitle)
        
        desc = QLabel("Importa tus datos desde Excel o CSV y comienza a analizar.\nTodas las operaciones se ejecutan localmente.")
        desc.setFont(QFont("Inter", 12))
        desc.setStyleSheet(f"color: {COLORS['text_muted']};")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        card_layout.addWidget(desc)
        
        card_layout.addSpacing(16)
        
        btn = QPushButton("Importar dataset")
        btn.setFont(QFont("Inter", 13, QFont.Weight.Medium))
        btn.setFixedSize(200, 38)
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
        btn.clicked.connect(lambda: import_dataset(self))
        card_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(card)
        return widget
    
    def _navigate(self, key):
        """Cambia entre vistas."""
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['accent']};
                        color: white;
                        text-align: left;
                        padding-left: 20px;
                        border: none;
                        border-radius: 8px;
                        margin: 2px 10px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {COLORS['text_secondary']};
                        text-align: left;
                        padding-left: 20px;
                        border: none;
                        border-radius: 8px;
                        margin: 2px 10px;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['border']};
                        color: {COLORS['text_primary']};
                    }}
                """)
        
        if key == "data":
            self.data_view.refresh()
            self.stack.setCurrentIndex(1)
        elif key == "analysis":
            self.analysis_view.refresh()
            self.stack.setCurrentIndex(2)
        elif key == "graphs":
            self.graphs_view.refresh()
            self.stack.setCurrentIndex(3)
    
    def _apply_styles(self):
        """Estilos globales."""
        self.setStyleSheet(f"""
            * {{
                font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
            }}
        """)
