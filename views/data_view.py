"""
Vista de Datos - Tabla, tipos de variables, metadatos.
"""

import customtkinter as ctk
import pandas as pd
from database import get_dataframe, DB_PATH
from tkinter import messagebox
import os
import json


class DataView:
    """Vista de gestión de datos."""
    
    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        
        self._build()
    
    def _build(self):
        # Título
        header = ctk.CTkFrame(self.parent, fg_color="transparent", height=50)
        header.pack(fill="x", padx=28, pady=(24, 8))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="Gestión de Datos",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color="#1A1A1A",
        ).pack(side="left")
        
        # Botón importar
        ctk.CTkButton(
            header,
            text="Importar nuevo dataset",
            font=ctk.CTkFont(family="Inter", size=12, weight="500"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            corner_radius=8,
            height=34,
            command=lambda: self.app._on_import_click(),
        ).pack(side="right", padx=(8, 0))
        
        if not self.app.dataset_loaded:
            self._show_empty()
            return
        
        # Info del dataset
        info_frame = ctk.CTkFrame(
            self.parent,
            fg_color="#FFFFFF",
            corner_radius=12,
            border_width=1,
            border_color="#E5E7EB",
        )
        info_frame.pack(fill="x", padx=28, pady=8)
        
        # Usar grid para las métricas
        info_frame.columnconfigure((0, 1, 2, 3), weight=1)
        
        metrics = [
            ("Dataset", self.app.dataset_name),
            ("Registros", str(len(get_dataframe(self.app.table_name)))),
            ("Variables", str(len(self.app.variables))),
            ("Base de datos", "DuckDB (local)"),
        ]
        
        for i, (label, value) in enumerate(metrics):
            card = ctk.CTkFrame(info_frame, fg_color="transparent")
            card.grid(row=0, column=i, padx=16, pady=14, sticky="nsew")
            
            ctk.CTkLabel(
                card,
                text=label.upper(),
                font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                text_color="#6B7280",
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(family="Inter", size=15, weight="600"),
                text_color="#1A1A1A",
            ).pack(anchor="w", pady=(2, 0))
        
        # Tabla de variables
        self._build_variables_table()
    
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
            text="No hay ningún dataset cargado",
            font=ctk.CTkFont(family="Inter", size=14),
            text_color="#6B7280",
        ).pack(expand=True)
    
    def _build_variables_table(self):
        """Tabla de variables con sus tipos."""
        # Contenedor
        container = ctk.CTkFrame(
            self.parent,
            fg_color="#FFFFFF",
            corner_radius=12,
            border_width=1,
            border_color="#E5E7EB",
        )
        container.pack(fill="both", expand=True, padx=28, pady=8)
        
        # Encabezado
        ctk.CTkLabel(
            container,
            text="Variables del dataset",
            font=ctk.CTkFont(family="Inter", size=14, weight="600"),
            text_color="#1A1A1A",
        ).pack(anchor="w", padx=20, pady=(16, 12))
        
        # Cabeceras de tabla
        cols_frame = ctk.CTkFrame(container, fg_color="#F9FAFB", height=36)
        cols_frame.pack(fill="x", padx=12)
        cols_frame.pack_propagate(False)
        
        headers = [
            ("Variable", 25),
            ("Tipo", 18),
            ("Rol sugerido", 18),
            ("Valores únicos", 13),
            ("Faltantes", 10),
            ("Descripción", 16),
        ]
        
        for text, width_pct in headers:
            ctk.CTkLabel(
                cols_frame,
                text=text,
                font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
                text_color="#6B7280",
                width=int(width_pct * 5),
            ).pack(side="left", padx=8, pady=8)
        
        # Scroll de variables
        var_scroll = ctk.CTkScrollableFrame(
            container,
            fg_color="transparent",
            scrollbar_button_color="#E5E7EB",
        )
        var_scroll.pack(fill="both", expand=True, padx=4, pady=(0, 8))
        
        # Traducción de tipos para mostrar
        tipo_labels = {
            "numérica_continua": "Numérica continua",
            "numérica_discreta": "Numérica discreta",
            "categórica_nominal": "Categórica nominal",
            "categórica_ordinal": "Categórica ordinal",
            "categórica_dicotómica": "Categórica dicotómica",
            "texto_libre": "Texto libre",
        }
        
        rol_labels = {
            "dependiente": "Dependiente",
            "independiente": "Independiente",
            "ambos": "Ambos",
            "id": "ID",
            "fecha": "Fecha",
            "texto_libre": "Texto libre",
        }
        
        for var_name, info in self.app.variables.items():
            row = ctk.CTkFrame(var_scroll, fg_color="transparent", height=34)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            
            tipo_display = tipo_labels.get(info.get("tipo", ""), info.get("tipo", "?"))
            rol_display = rol_labels.get(info.get("sugerencia_rol", ""), info.get("sugerencia_rol", "?"))
            n_unique = info.get("valores_unicos", "?")
            faltantes = "Sí" if info.get("tiene_valores_faltantes") else "No"
            desc = info.get("descripcion", "")[:30]
            
            valores = [
                (var_name[:25], 25),
                (tipo_display, 18),
                (rol_display, 18),
                (str(n_unique), 13),
                (faltantes, 10),
                (desc, 16),
            ]
            
            for text, width_pct in valores:
                ctk.CTkLabel(
                    row,
                    text=text,
                    font=ctk.CTkFont(family="Inter", size=11),
                    text_color="#1A1A1A" if width_pct > 15 else "#6B7280",
                    width=int(width_pct * 5),
                    anchor="w",
                ).pack(side="left", padx=8, pady=6)
