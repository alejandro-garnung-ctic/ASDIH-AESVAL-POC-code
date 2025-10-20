#!/usr/bin/env python3
"""
Script de inicio multiplataforma para AESVAL Tasación App
"""

import os
import sys
import platform

def main():
    print("🚀 Iniciando aplicación de tasación AESVAL...")
    print("📦 Contenedor Docker - AESVAL Tasación App")
    print()
    
    # Configurar variables de entorno
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    os.environ['STREAMLIT_SERVER_PORT'] = '8502'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    print("⏳ Iniciando Streamlit...")
    print("✅ APLICACIÓN INICIADA CORRECTAMENTE")
    print("==========================================")
    print("🌐 ACCEDA A LA APLICACIÓN EN:")
    print("   http://localhost:8502")
    print("   http://127.0.0.1:8502")
    print()
    print("📊 Características:")
    print("   • Tasación individual de inmuebles")
    print("   • Tasación múltiple por lotes") 
    print("   • Análisis de contribuciones")
    print("   • Documentación del modelo ECO 805")
    print()
    print("⚙️  Para ver logs: docker-compose logs -f")
    print("🛑 Para detener: docker-compose down")
    print("==========================================")
    
    # Ejecutar Streamlit
    os.execvp("streamlit", [
        "streamlit", "run", "src/app.py",
        "--server.port=8502",
        "--server.address=0.0.0.0", 
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ])

if __name__ == "__main__":
    main()