"""
STATlab - Clasificación inteligente de variables usando Ollama.
"""

import ollama
import pandas as pd
import json
import numpy as np


def classify_variables(df):
    """
    Usa Ollama para clasificar cada variable del dataset.
    
    Retorna un diccionario con:
    {
        "nombre_variable": {
            "tipo": "numérica_continua" | "numérica_discreta" | 
                    "categórica_nominal" | "categórica_ordinal" | "categórica_dicotómica",
            "valores_unicos": N,
            "tiene_valores_faltantes": bool,
            "sugerencia_rol": "dependiente" | "independiente" | "ambos" | "id",
            "descripcion": "texto corto"
        }
    }
    """
    
    # Preparar información ligera para la IA
    info = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        n_unique = int(df[col].nunique())
        n_null = int(df[col].isna().sum())
        
        if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
            datos = df[col].dropna()
            info[col] = {
                "tipo_python": "numérica",
                "valores_unicos": n_unique,
                "nulos": n_null,
                "min": float(datos.min()) if not datos.empty else None,
                "max": float(datos.max()) if not datos.empty else None,
                "ejemplos": datos.head(5).tolist() if not datos.empty else [],
            }
        else:
            datos = df[col].dropna()
            info[col] = {
                "tipo_python": "texto",
                "valores_unicos": n_unique,
                "nulos": n_null,
                "categorias": datos.unique()[:15].tolist() if not datos.empty else [],
                "ejemplos": datos.head(5).tolist() if not datos.empty else [],
            }
    
    # Intentar clasificar con Ollama
    try:
        prompt = f"""
Clasifica cada variable del siguiente dataset. Para cada una, determina:

1. tipo: "numérica_continua", "numérica_discreta", "categórica_nominal", "categórica_ordinal", "categórica_dicotómica"
2. sugerencia_rol: "dependiente", "independiente", "ambos", "id", "fecha", "texto_libre"
3. descripcion: descripción breve (máx 10 palabras)

Variables: {json.dumps(info, ensure_ascii=False, indent=2)}

Responde SOLO en JSON: {{"nombre_variable": {{"tipo": "...", "sugerencia_rol": "...", "descripcion": "..."}}}}
"""

        respuesta = ollama.chat(
            model="llama3.2:1b",
            messages=[{"role": "user", "content": prompt}]
        )
        
        texto = respuesta['message']['content'].strip()
        
        # Extraer JSON
        if "```json" in texto:
            texto = texto.split("```json")[1].split("```")[0].strip()
        elif "```" in texto:
            texto = texto.split("```")[1].split("```")[0].strip()
        
        clasificacion = json.loads(texto)
        
        # Añadir info adicional y convertir tipos
        for col, data in clasificacion.items():
            if col in info:
                data["valores_unicos"] = int(info[col]["valores_unicos"])
                data["tiene_valores_faltantes"] = bool(info[col]["nulos"] > 0)
                data["tipo_python"] = info[col]["tipo_python"]
        
        return clasificacion
    
    except Exception:
        # Fallback: clasificación heurística sin IA
        return _heuristic_classification(df)


def _convert_to_native(obj):
    """Convierte tipos numpy a tipos nativos de Python para serialización JSON."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: _convert_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_to_native(i) for i in obj]
    return obj


def _heuristic_classification(df):
    """Clasificación heurística si Ollama falla."""
    result = {}
    
    for col in df.columns:
        dtype = df[col].dtype
        n_unique = int(df[col].nunique())
        n_total = len(df)
        n_nulls = int(df[col].isna().sum())
        
        # ID detection
        if n_unique == n_total and df[col].dtype in ['int64', 'float64']:
            tipo = "numérica_discreta"
            rol = "id"
            desc = "Posible identificador único"
        elif dtype in ['int64', 'float64']:
            if n_unique <= 2:
                tipo = "categórica_dicotómica"
                rol = "independiente"
                desc = "Variable binaria numérica"
            elif n_unique <= 15:
                tipo = "categórica_ordinal"
                rol = "independiente"
                desc = "Variable discreta con pocos valores"
            elif df[col].dropna().apply(lambda x: x == int(x)).all():
                tipo = "numérica_discreta"
                rol = "ambos"
                desc = "Variable numérica discreta"
            else:
                tipo = "numérica_continua"
                rol = "ambos"
                desc = "Variable numérica continua"
        else:
            if n_unique <= 2:
                tipo = "categórica_dicotómica"
                rol = "independiente"
                desc = "Variable categórica binaria"
            elif n_unique <= 15:
                tipo = "categórica_nominal"
                rol = "independiente"
                desc = "Variable categórica nominal"
            else:
                tipo = "texto_libre"
                rol = "texto_libre"
                desc = "Texto libre o ID de texto"
        
        result[col] = {
            "tipo": tipo,
            "sugerencia_rol": rol,
            "descripcion": desc,
            "valores_unicos": n_unique,
            "tiene_valores_faltantes": bool(n_nulls > 0),
            "tipo_python": str(dtype),
        }
    
    return result
