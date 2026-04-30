"""
STATlab - Ventana principal y navegación.
Framework: CustomTkinter
Base de datos: DuckDB interna
"""

import customtkinter as ctk
from pathlib import Path
import threading

# Configuración global de apariencia
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Paleta corporativa
COLORS = {
    "bg_primary": "#FAFAFA",
    "bg_secondary": "#FFFFFF",
    "bg_sidebar": "#F5F5F5",
    "bg_card": "#FFFFFF",
    "text_primary": "#1A1A1A",
    "text_secondary": "#6B7280",
    "text_muted": "#9CA3AF",
    "accent": "#2563EB",
    "accent_hover": "#1D4ED8",
    "accent_light": "#EFF6FF",
    "border": "#E5E7EB",
    "border_focus": "#2563EB",
    "success": "#059669",
    "success_light": "#ECFDF5",
    "warning": "#D97706",
    "warning_light": "#FFFBEB",
    "error": "#DC2626",
    "error_light": "#FEF2F2",
    "shadow": "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
}


class STATlabApp(ctk.CTk):
    """Ventana principal de STATlab."""
    
    def __init__(self):
        super().__init__()
        
        # Configuración de ventana
        self.title("STATlab")
        self.geometry("1280x800")
        self.minsize(1024, 600)
        self.configure(fg_color=COLORS["bg_primary"])
        
        # Centrar ventana
        self.after(150, self._center_window)
        
        # Estado de la aplicación
        self.dataset_loaded = False
        self.dataset_name = ""
        self.table_name = ""
        self.variables = {}
        
        # Construir UI
        self._build_sidebar()
        self._build_main_layout()
        
        # Cargar vista inicial
        self._show_welcome()
    
    def _center_window(self):
        """Centra la ventana en la pantalla."""
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
    
    # -------------------------------------------------------------------
    # SIDEBAR
    # -------------------------------------------------------------------
    def _build_sidebar(self):
        """Construye la barra lateral de navegación."""
        self.sidebar = ctk.CTkFrame(
            self,
            width=240,
            corner_radius=0,
            fg_color=COLORS["bg_sidebar"],
            border_width=0,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=56)
        logo_frame.pack(fill="x", padx=20, pady=(28, 8))
        logo_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            logo_frame,
            text="STATlab",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(side="left")
        
        # Separador
        ctk.CTkFrame(
            self.sidebar, height=1, fg_color=COLORS["border"]
        ).pack(fill="x", padx=16, pady=(8, 20))
        
        # Navegación
        nav_items = [
            ("Datos", "data"),
            ("Análisis", "analysis"),
            ("Gráficos", "graphs"),
        ]
        
        self.nav_buttons = {}
        for text, key in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                fg_color="transparent",
                text_color=COLORS["text_secondary"],
                font=ctk.CTkFont(family="Inter", size=13, weight="500"),
                hover_color=COLORS["border"],
                corner_radius=8,
                height=38,
                anchor="w",
                command=lambda k=key: self._navigate(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn
        
        # Espaciador
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="both", expand=True)
        
        # Footer
        ctk.CTkLabel(
            self.sidebar,
            text="v2.0 · Desktop",
            font=ctk.CTkFont(family="Inter", size=10),
            text_color=COLORS["text_muted"],
        ).pack(pady=(0, 16))
    
    # -------------------------------------------------------------------
    # NAVEGACIÓN
    # -------------------------------------------------------------------
    def _navigate(self, key):
        """Cambia entre vistas."""
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color=COLORS["accent"], text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_secondary"])
        
        # Limpiar área principal
        for widget in self.main_area.winfo_children():
            widget.destroy()
        
        if key == "data":
            from views.data_view import DataView
            DataView(self, self.main_area)
        elif key == "analysis":
            from views.analysis_view import AnalysisView
            AnalysisView(self, self.main_area)
        elif key == "graphs":
            from views.graphs_view import GraphsView
            GraphsView(self, self.main_area)
    
    # -------------------------------------------------------------------
    # ÁREA PRINCIPAL
    # -------------------------------------------------------------------
    def _build_main_layout(self):
        """Construye el área de contenido principal con scroll."""
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(side="right", fill="both", expand=True)
        
        # Área con scroll
        self.main_area = ctk.CTkScrollableFrame(
            self.main_container,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["text_secondary"],
        )
        self.main_area.pack(fill="both", expand=True, padx=0, pady=0)
    
    def _show_welcome(self):
        """Muestra pantalla de bienvenida."""
        frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Contenedor centrado
        inner = ctk.CTkFrame(
            frame,
            fg_color=COLORS["bg_card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        inner.pack(expand=True, padx=60, pady=60)
        
        ctk.CTkLabel(
            inner,
            text="STATlab",
            font=ctk.CTkFont(family="Inter", size=28, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(pady=(40, 8))
        
        ctk.CTkLabel(
            inner,
            text="Análisis estadístico profesional",
            font=ctk.CTkFont(family="Inter", size=14),
            text_color=COLORS["text_secondary"],
        ).pack()
        
        ctk.CTkLabel(
            inner,
            text="Importa tus datos desde Excel o CSV y comienza a analizar.\n"
                 "Todas las operaciones se ejecutan localmente en tu ordenador.",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=COLORS["text_muted"],
            justify="center",
        ).pack(pady=(16, 30))
        
        # Botón de importar
        btn = ctk.CTkButton(
            inner,
            text="Importar dataset",
            font=ctk.CTkFont(family="Inter", size=13, weight="500"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=8,
            height=38,
            command=self._on_import_click,
        )
        btn.pack(pady=(0, 40))
    
    def _on_import_click(self):
        """Abre diálogo de importación."""
        from database import import_dataset
        import_dataset(self)
