"""
STATlab - Gestión de base de datos interna con DuckDB.
"""

import duckdb
import pandas as pd
from pathlib import Path
from tkinter import filedialog
import json
import os
import tkinter.messagebox as messagebox

DB_PATH = Path(__file__).parent / "statlab.db"


def get_connection():
    """Obtiene conexión a DuckDB."""
    return duckdb.connect(str(DB_PATH))


def init_db():
    """Inicializa la base de datos."""
    # DuckDB no requiere inicialización explícita
    pass


def import_dataset(app):
    """
    Importa un dataset desde Excel/CSV a la base de datos interna.
    Clasifica variables usando Ollama.
    """
    filetypes = [
        ("Archivos de datos", "*.xlsx *.csv"),
        ("Excel", "*.xlsx"),
        ("CSV", "*.csv"),
    ]
    
    filename = filedialog.askopenfilename(
        title="Importar dataset",
        filetypes=filetypes,
    )
    
    if not filename:
        return
    
    try:
        # Cargar datos
        if filename.endswith('.csv'):
            df = pd.read_csv(filename)
        else:
            df = pd.read_excel(filename)
        
        # Nombre de la tabla
        table_name = Path(filename).stem.replace(" ", "_").replace("-", "_")
        
        # Guardar en DuckDB
        con = get_connection()
        con.execute(f"DROP TABLE IF EXISTS {table_name}")
        con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
        
        # Clasificar variables con Ollama
        from classifier import classify_variables
        variables_info = classify_variables(df)
        
        # Guardar metadata
        metadata = {
            "table_name": table_name,
            "filename": Path(filename).name,
            "rows": len(df),
            "columns": len(df.columns),
            "variables": variables_info,
        }
        
        metadata_path = Path(__file__).parent / f"metadata_{table_name}.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # Actualizar estado de la app
        app.dataset_loaded = True
        app.dataset_name = Path(filename).name
        app.table_name = table_name
        app.variables = variables_info
        
        # Recargar vista de datos
        app._navigate("data")
        
        messagebox.showinfo(
            "Importación exitosa",
            f"Dataset '{Path(filename).name}' importado.\n"
            f"{len(df)} filas, {len(df.columns)} columnas."
        )
        
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo importar:\n{str(e)}")


def get_dataframe(table_name, limit=None):
    """Obtiene DataFrame desde DuckDB."""
    con = get_connection()
    if limit:
        return con.execute(f"SELECT * FROM {table_name} LIMIT {limit}").df()
    return con.execute(f"SELECT * FROM {table_name}").df()


def get_variable_data(table_name, variable):
    """Obtiene datos de una variable específica."""
    con = get_connection()
    return con.execute(f"SELECT \"{variable}\" FROM {table_name}").df()[variable].dropna()


def execute_query(query):
    """Ejecuta consulta SQL arbitraria."""
    con = get_connection()
    return con.execute(query).df()
