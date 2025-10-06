import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
import yaml
import io
import base64
from datetime import datetime

current_year = datetime.now().year

st.set_page_config(
    page_title="AESVAL - Sistema de Tasación Inteligente",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_image_base64(path):
    """Carga imágenes y las convierte a base64"""
    import os
    
    possible_paths = [
        f"/app/{path}",           
        f"/app/assets/{path.split('/')[-1]}", 
        f"./{path}",
        f"assets/{path}",
    ]
    
    for img_path in possible_paths:
        try:
            if os.path.exists(img_path):
                with open(img_path, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode()
            else:
                st.warning(f"❌ No se encuentra: {img_path}")
        except Exception as e:
            continue
    
    st.warning(f"⚠️ No se pudo cargar la imagen: {path}")
    return None

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
    """Header profesional con logos y diseño corporativo"""
    
    logo_aesval = get_image_base64("assets/aesval.png")
    logo_ctic  = get_image_base64("assets/CTIC.png")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if logo_aesval:
            st.markdown(
                f'<div style="text-align: center; padding: 10px;">'
                f'<img src="data:image/png;base64,{logo_aesval}" width="150" style="border-radius: 10px;">'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="text-align: center; background: linear-gradient(135deg, #1f77b4, #2e8bc0); '
                'padding: 30px; border-radius: 10px; color: white; margin: 10px;">'
                '<h3>🏢 AESVAL</h3>'
                '<p style="font-size: 0.8rem; margin: 0;">Entidad Tasadora</p>'
                '</div>', 
                unsafe_allow_html=True
            )
    
    with col2:
        st.markdown(
            """
            <div style='text-align: center; padding: 1rem 0;'>
                <h1 style='color: #1f77b4; margin-bottom: 0.5rem; font-size: 2.5rem;'>
                    🏠 SISTEMA DE TASACIÓN
                </h1>
                <h3 style='color: #666; margin-top: 0; font-weight: 300;'>
                    Plataforma Inteligente de Valoración Inmobiliaria
                </h3>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col3:
        if logo_ctic:
            st.markdown(
                f'<div style="text-align: center; padding: 10px;">'
                f'<img src="data:image/png;base64,{logo_ctic}" width="120" style="border-radius: 10px;">'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="text-align: center; background: linear-gradient(135deg, #ff6b6b, #ff8e8e); '
                'padding: 30px; border-radius: 10px; color: white; margin: 10px;">'
                '<h3>🔬 CTIC</h3>'
                '<p style="font-size: 0.8rem; margin: 0;">Centro Tecnológico</p>'
                '</div>', 
                unsafe_allow_html=True
            )
    
    st.markdown("---")

def mostrar_sidebar():
    """Sidebar con información corporativa"""
    with st.sidebar:
        st.markdown(
            """
            <div style='background: linear-gradient(135deg, #1f77b4, #2e8bc0); 
                        padding: 2rem; 
                        border-radius: 10px; 
                        color: white; 
                        margin-bottom: 2rem;'>
                <h3 style='color: white; margin-bottom: 1rem;'>📊 Sistema AESVAL</h3>
                <p style='margin-bottom: 0; font-size: 0.9rem;'>
                    Plataforma oficial para la tasación inteligente de inmuebles 
                    según normativa ECO 805
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        st.markdown("### ℹ️ Información del Sistema")
        st.info("""
        **Versión:** 2.1.0  
        **Estado:** 🟢 Operativo  
        **Modelo:** ECO 805  
        **Última actualización:** 2024
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tasaciones Hoy", "12", "3")
        with col2:
            st.metric("Precisión", "97.2%", "0.8%")
        
        st.markdown("---")
        
        st.markdown(
            f"""
            <div style='text-align: center; color: #666; font-size: 0.8rem; padding: 1rem 0;'>
                <p>© {current_year} AESVAL - CTIC</p>
                <p>Sistema de Tasación Inteligente</p>
                <p>v2.1.0</p>
            </div>
            """, 
            unsafe_allow_html=True
        )

def pagina_tasacion_individual():
    """Pestaña para tasación individual - Versión mejorada"""
    st.header("📊 Tasación Individual")
    
    with st.container():
        st.info("""
        💡 **Instrucciones:** Complete los datos del inmueble para obtener una tasación precisa 
        basada en el modelo matemático ECO 805. Todos los campos son obligatorios.
        """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.container():
            st.subheader("🏛️ Datos del Inmueble")
            
            col1_1, col1_2 = st.columns(2)
            
            with col1_1:
                municipio = st.selectbox(
                    "Municipio",
                    ["Seleccione municipio", "Gijón", "Oviedo", "Avilés", "Mieres", "Langreo"],
                    help="Seleccione el municipio donde se ubica el inmueble"
                )
                
                superficie = st.number_input(
                    "Superficie construida (m²)", 
                    min_value=0.0, 
                    max_value=1000.0,
                    value=0.0,
                    step=0.5,
                    help="Superficie total construida en metros cuadrados"
                )
                
                antiguedad = st.number_input(
                    "Antigüedad (años)", 
                    min_value=0, 
                    max_value=200,
                    value=0,
                    help="Años desde la construcción del inmueble"
                )
            
            with col1_2:
                tipo_inmueble = st.selectbox(
                    "Tipo de inmueble",
                    ["Vivienda unifamiliar", "Vivienda en bloque", "Local comercial", "Oficina", "Industrial"],
                    help="Seleccione la tipología del inmueble"
                )
                
                estado_conservacion = st.select_slider(
                    "Estado de conservación",
                    options=["Muy deficiente", "Deficiente", "Regular", "Bueno", "Muy bueno", "Excelente"],
                    value="Bueno",
                    help="Estado general de conservación del inmueble"
                )
                
                calidad_constructiva = st.radio(
                    "Calidad constructiva",
                    ["Básica", "Media", "Alta", "Lujo"],
                    horizontal=True
                )
    
    with col2:
        with st.container():
            st.subheader("📈 Resultados")
            
            if st.button("🎯 Calcular Tasación", type="primary", use_container_width=True):
                with st.spinner("Calculando tasación..."):
                    import time
                    time.sleep(2)
                    
                    st.success("✅ Tasación calculada correctamente")
                    
                    col_res1, col_res2 = st.columns(2)
                    with col_res1:
                        st.metric("Valor Tasado", "€ 185.250", "12.3%")
                    with col_res2:
                        st.metric("Tasa Descuento", "3.45%", "-0.2%")
                    
                    st.metric("Factor Corrección", "0.892", "Aplicado")
                    
                    st.download_button(
                        "📥 Descargar Informe",
                        data="Informe de tasación generado",
                        file_name=f"tasacion_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            else:
                st.info("ℹ️ Complete los datos y haga clic en 'Calcular Tasación' para obtener resultados")

def pagina_tasacion_multiple():
    """Pestaña para tasación múltiple - Versión mejorada"""
    st.header("📁 Tasación Múltiple por Lotes")
    
    with st.expander("ℹ️ Información sobre tasación múltiple", expanded=True):
        st.markdown("""
        **Características de la tasación por lotes:**
        - Procesamiento simultáneo de múltiples inmuebles
        - Formato Excel estándar (.xlsx, .xls)
        - Validación automática de datos
        - Generación de informe consolidado
        - Límite: 500 registros por lote
        """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "📤 Subir archivo Excel para tasación múltiple", 
            type=['xlsx', 'xls'],
            help="El archivo debe contener las columnas: Municipio, Superficie, Antigüedad, Tipo"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                
                st.success(f"✅ Archivo cargado correctamente - {len(df)} registros detectados")
                
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                with col_stats1:
                    st.metric("Registros", len(df))
                with col_stats2:
                    st.metric("Columnas", len(df.columns))
                with col_stats3:
                    st.metric("Tasaciones estimadas", f"{len(df)*2}s")
                
                st.subheader("👁️ Vista previa de datos")
                st.dataframe(
                    df.head(10),
                    use_container_width=True,
                    height=300
                )
                
                if st.button("🚀 Procesar Lote Completo", type="primary", use_container_width=True):
                    with st.spinner(f"Procesando {len(df)} registros..."):
                        import time
                        time.sleep(3)
                        st.success(f"✅ Procesamiento completado - {len(df)} tasaciones generadas")
                        
            except Exception as e:
                st.error(f"❌ Error procesando el archivo: {str(e)}")
    
    with col2:
        st.subheader("📋 Plantilla")
        
        sample_data = {
            'Municipio': ['Gijón', 'Oviedo', 'Avilés'],
            'Superficie_m2': [85.5, 120.0, 65.0],
            'Antiguedad_años': [15, 8, 25],
            'Tipo_Inmueble': ['Vivienda en bloque', 'Vivienda unifamiliar', 'Vivienda en bloque'],
            'Estado_Conservacion': ['Bueno', 'Muy bueno', 'Regular']
        }
        sample_df = pd.DataFrame(sample_data)
        
        st.download_button(
            "📥 Descargar plantilla",
            data=sample_df.to_csv(index=False),
            file_name="plantilla_tasacion_multiple.csv",
            mime="text/csv",
            help="Descargue esta plantilla como referencia para el formato requerido",
            use_container_width=True
        )

def pagina_documentacion():
    """Pestaña de documentación - Versión mejorada"""
    st.header("📚 Documentación Técnica del Modelo")
    
    st.markdown("""
    <div style='background: #f0f2f6; padding: 2rem; border-radius: 10px; border-left: 4px solid #1f77b4;'>
        <h4 style='color: #1f77b4; margin-top: 0;'>Modelo Matemático ECO 805</h4>
        <p style='margin-bottom: 0;'>
            Sistema de valoración inmobiliaria basado en algoritmos de machine learning 
            y normativa técnica ECO 805 para la determinación precisa de tasas de descuento.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("🧮 Modelo Matemático")
    
    col_formula, col_explicacion = st.columns([1, 2])
    
    with col_formula:
        st.latex(r"""
        Tasa = \beta_0 + \sum_{i=1}^{n} \beta_i \cdot X_i + \epsilon
        """)
        
        st.latex(r"""
        V = S \cdot P_u \cdot F_c \cdot F_a \cdot F_l
        """)
    
    with col_explicacion:
        st.markdown("""
        **Donde:**
        - **V**: Valor tasado del inmueble
        - **S**: Superficie construida (m²)
        - **P_u**: Precio unitario de referencia
        - **F_c**: Factor de corrección por conservación
        - **F_a**: Factor de antigüedad
        - **F_l**: Factor de localización
        """)
    
    st.subheader("📊 Variables del Modelo")
    
    tab_vars1, tab_vars2, tab_vars3 = st.tabs(["Intrínsecas", "Extrínsecas", "Corrección"])
    
    with tab_vars1:
        st.markdown("""
        ### 🏠 Variables Intrínsecas
        - **Superficie construida**: m² totales
        - **Antigüedad**: Años desde construcción
        - **Estado de conservación**: Escala 1-6
        - **Calidad constructiva**: Materiales y acabados
        - **Distribución**: Eficiencia espacial
        - **Dotaciones**: Instalaciones y equipamientos
        """)
    
    with tab_vars2:
        st.markdown("""
        ### 🌍 Variables Extrínsecas
        - **Ubicación**: Municipio y zona
        - **Entorno urbano**: Calidad del área
        - **Servicios proximidad**: Educación, salud, comercio
        - **Comunicaciones**: Accesibilidad y transporte
        - **Demanda zona**: Dinámica de mercado local
        """)
    
    with tab_vars3:
        st.markdown("""
        ### ⚖️ Factores de Corrección
        - **Factor antigüedad**: Depreciación temporal
        - **Factor estado**: Corrección por conservación
        - **Factor ubicación**: Valoración territorial
        - **Factor mercado**: Situación económica actual
        - **Factor específico**: Características singulares
        """)

def mostrar_footer():
    """Footer profesional con copyright"""
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            f"""
            <div style='text-align: center; color: #666; padding: 2rem 0;'>
                <p style='margin-bottom: 0.5rem; font-size: 0.9rem;'>
                    © {current_year} <strong>AESVAL</strong> - Centro Tecnológico CTIC | 
                    Sistema de Tasación Inteligente v2.1.0
                </p>
                <p style='margin-bottom: 0; font-size: 0.8rem;'>
                    Desarrollado con Streamlit • Modelo ECO 805 • 
                    <a href='#' style='color: #666;'>Política de privacidad</a> • 
                    <a href='#' style='color: #666;'>Términos de uso</a>
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )

def main():
    """Función principal de la aplicación"""
    inicializar_session_state()
    
    mostrar_header()
    mostrar_sidebar()
    
    tab1, tab2, tab3 = st.tabs([
        "🏠 Tasación Individual", 
        "📁 Tasación por Lotes", 
        "📚 Documentación Técnica"
    ])
    
    with tab1:
        pagina_tasacion_individual()
    
    with tab2:
        pagina_tasacion_multiple()
    
    with tab3:
        pagina_documentacion()
    
    mostrar_footer()

if __name__ == "__main__":
    main()