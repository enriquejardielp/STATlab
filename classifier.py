"""
STATlab - Clasificación inteligente de variables usando Ollama.
"""

import ollama
import pandas as pd
import json


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
        n_unique = df[col].nunique()
        n_null = df[col].isna().sum()
        
        if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
            info[col] = {
                "tipo_python": "numérica",
                "valores_unicos": int(n_unique),
                "nulos": int(n_null),
                "min": float(df[col].min()) if not df[col].dropna().empty else None,
                "max": float(df[col].max()) if not df[col].dropna().empty else None,
                "ejemplos": df[col].dropna().head(5).tolist(),
            }
        else:
            info[col] = {
                "tipo_python": "texto",
                "valores_unicos": int(n_unique),
                "nulos": int(n_null),
                "categorias": df[col].dropna().unique()[:15].tolist(),
                "ejemplos": df[col].dropna().head(5).tolist(),
            }
    
    # Prompt para Ollama
    prompt = f"""
Clasifica cada variable del siguiente dataset. Para cada una, determina:

1. tipo: "numérica_continua", "numérica_discreta", "categórica_nominal", "categórica_ordinal", "categórica_dicotómica"
2. sugerencia_rol: "dependiente", "independiente", "ambos", "id", "fecha", "texto_libre"
3. descripcion: descripción breve (máx 10 palabras)

Variables: {json.dumps(info, ensure_ascii=False, indent=2)}

Responde SOLO en JSON: {{"nombre_variable": {{"tipo": "...", "sugerencia_rol": "...", "descripcion": "..."}}}}
"""

    try:
        respuesta = ollama.chat(
            model="llama3.2:1b",
            messages=[{"role": "user", "content": prompt}]
        )
        
        texto = respuesta['message']['content'].strip()
        
        # Extraer JSON
        if "```json" in texto:
            texto = texto.split("```json")[1].split("```")[0]
        elif "```" in texto:
            texto = texto.split("```")[1].split("```")[0]
        
        clasificacion = json.loads(texto)
        
        # Añadir info adicional
        for col, data in clasificacion.items():
            if col in info:
                data["valores_unicos"] = info[col]["valores_unicos"]
                data["tiene_valores_faltantes"] = info[col]["nulos"] > 0
                data["tipo_python"] = info[col]["tipo_python"]
        
        return clasificacion
    
    except Exception as e:
        # Fallback: clasificación heurística sin IA
        return _heuristic_classification(df)


def _heuristic_classification(df):
    """Clasificación heurística si Ollama falla."""
    result = {}
    
    for col in df.columns:
        dtype = df[col].dtype
        n_unique = df[col].nunique()
        n_total = len(df)
        
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
            "tiene_valores_faltantes": df[col].isna().sum() > 0,
            "tipo_python": str(dtype),
        }
    
    return result
