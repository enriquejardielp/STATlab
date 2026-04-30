"""
STATlab - Aplicación de Escritorio para Análisis Estadístico
Punto de entrada principal.
"""

import sys
import os

# Añadir directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import STATlabApp

if __name__ == "__main__":
    app = STATlabApp()
    app.mainloop()
