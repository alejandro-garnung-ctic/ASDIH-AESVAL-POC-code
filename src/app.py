import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
import yaml
import io

# SOLO UNA configuración de página - ELIMINA EL SEGUNDO st.set_page_config()
st.set_page_config(
    page_title="AESVAL - Sistema de Tasación",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

def cargar_configuracion() -> Dict:
    """Carga la configuración de modelos desde YAML"""
    try:
        with open('/app/config/models.yaml', 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        st.error(f"Error cargando configuración: {e}")
        return {}

def inicializar_session_state():
    """Inicializa variables de session state"""
    if 'config' not in st.session_state:
        st.session_state.config = cargar_configuracion()
    if 'resultados_individuales' not in st.session_state:
        st.session_state.resultados_individuales = []

def mostrar_header():
    """Muestra el encabezado de la aplicación"""
    st.title("🏠 AESVAL - Sistema de Tasación de Inmuebles")
    st.markdown("---")
    st.markdown("**Cálculo de tasas de descuento según normativa ECO 805**")

def pagina_tasacion_individual():
    """Pestaña para tasación individual"""
    st.header("📊 Tasación Individual")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Datos del Inmueble")
        st.text_input("Código Municipio")
        st.number_input("Superficie (m²)", min_value=0.0)
        st.number_input("Antigüedad (años)", min_value=0)
        
    with col2:
        st.subheader("Resultados")
        st.info("Complete los datos para calcular la tasa")

def pagina_tasacion_multiple():
    """Pestaña para tasación múltiple"""
    st.header("📁 Tasación Múltiple")
    
    uploaded_file = st.file_uploader(
        "Subir archivo Excel", 
        type=['xlsx'],
        help="El archivo debe contener las columnas requeridas"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.success(f"Archivo cargado correctamente - {len(df)} registros")
            st.dataframe(df.head())
            
        except Exception as e:
            st.error(f"Error leyendo el archivo: {e}")

def pagina_documentacion():
    """Pestaña de documentación del modelo"""
    st.header("📚 Documentación del Modelo")
    
    st.subheader("Modelo Matemático")
    st.latex(r"Tasa = \beta_0 + \beta_1 \cdot X_1 + \beta_2 \cdot X_2 + \cdots + \beta_n \cdot X_n")
    
    st.subheader("Variables del Modelo")
    st.write("""
    - **Variables intrínsecas**: Características propias del inmueble
    - **Variables extrínsecas**: Factores externos y de ubicación
    """)

def main():
    """Función principal de la aplicación"""
    inicializar_session_state()
    mostrar_header()
    
    # Crear pestañas
    tab1, tab2, tab3 = st.tabs([
        "🏠 Tasación Individual", 
        "📁 Tasación Múltiple", 
        "📚 Documentación"
    ])
    
    with tab1:
        pagina_tasacion_individual()
    
    with tab2:
        pagina_tasacion_multiple()
    
    with tab3:
        pagina_documentacion()

if __name__ == "__main__":
    main()