#!/bin/bash

echo "🚀 Iniciando aplicación de tasación AESVAL..."
echo "📦 Contenedor Docker - AESVAL Tasación App"
echo ""

# Configurar variables de entorno para Streamlit
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_PORT=8502
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

echo "⏳ Iniciando Streamlit..."
echo "✅ APLICACIÓN INICIADA CORRECTAMENTE"
echo "=========================================="
echo "🌐 ACCEDA A LA APLICACIÓN EN:"
echo "   http://127.0.0.1:8502"
echo ""
echo "📊 Características:"
echo "   • Tasación individual de inmuebles"
echo "   • Tasación múltiple por lotes"
echo "   • Análisis de contribuciones"
echo "   • Documentación del modelo ECO 805"
echo ""
echo "⚙️  Para ver logs: docker-compose logs -f"
echo "🛑 Para detener: docker-compose down"
echo "=========================================="

# Ejecutar Streamlit con configuración explícita
exec streamlit run src/app.py \
    --server.port=8502 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false