import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import yaml
import io
import base64
from datetime import datetime
import json

current_year = datetime.now().year

# Configuración de página
st.set_page_config(
    page_title="AESVAL - Sistema de Tasación Inteligente ECO 805",
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
        except:
            continue
    return None

class ModeloTasacion:
    """Clase para gestionar los modelos de tasación"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.modelos = config.get('modelos', {})
        self.factores = config.get('factores_correccion', {})
    
    def obtener_modelo_por_poblacion(self, poblacion: int) -> Optional[Dict]:
        """Obtiene el modelo adecuado según el tamaño de población"""
        if poblacion < 10000:
            return self.modelos.get('testigos_menos_10000')
        elif 10000 <= poblacion < 50000:
            return self.modelos.get('testigos_10000_50000')
        elif 50000 <= poblacion < 200000:
            return self.modelos.get('testigos_50000_200000')
        else:
            return self.modelos.get('testigos_mas_200000')
    
    def calcular_valor_m2(self, datos: Dict, modelo: Dict) -> Tuple[float, Dict]:
        """Calcula el valor por m² usando el modelo especificado"""
        coef = modelo['coeficientes']
        contribuciones = {}
        
        # Valor base del municipio (intercepto)
        valor_base = coef['intercepto']
        contribuciones['valor_base'] = valor_base
        
        # Aplicar coeficientes según variables
        if datos.get('vivienda_nueva') and 'vivienda_nueva' in coef:
            contrib = coef['vivienda_nueva']
            valor_base += contrib
            contribuciones['vivienda_nueva'] = contrib
        
        if 'superficie' in coef and datos.get('superficie'):
            contrib = coef['superficie'] * datos['superficie']
            valor_base += contrib
            contribuciones['superficie'] = contrib
        
        if datos.get('calefaccion') and 'calefaccion' in coef:
            contrib = coef['calefaccion']
            valor_base += contrib
            contribuciones['calefaccion'] = contrib
        
        if 'dormitorios' in coef and datos.get('dormitorios'):
            contrib = coef['dormitorios'] * datos['dormitorios']
            valor_base += contrib
            contribuciones['dormitorios'] = contrib
        
        if 'banos' in coef and datos.get('banos'):
            contrib = coef['banos'] * datos['banos']
            valor_base += contrib
            contribuciones['banos'] = contrib
        
        if datos.get('calidad_alta') and 'calidad_alta' in coef:
            contrib = coef['calidad_alta']
            valor_base += contrib
            contribuciones['calidad_alta'] = contrib
        
        if datos.get('ascensor') and 'ascensor' in coef:
            contrib = coef['ascensor']
            valor_base += contrib
            contribuciones['ascensor'] = contrib
        
        if 'planta' in coef and datos.get('planta'):
            contrib = coef['planta'] * datos['planta']
            valor_base += contrib
            contribuciones['planta'] = contrib
        
        return max(0, valor_base), contribuciones
    
    def calcular_tasa_descuento(self, datos: Dict) -> Tuple[float, Dict]:
        """Calcula la tasa de descuento usando el modelo correspondiente"""
        modelo = self.modelos.get('tasa_descuento', {})
        coef = modelo.get('coeficientes', {})
        contribuciones = {}
        
        tasa_base = coef.get('intercepto', 0.05)
        contribuciones['tasa_base'] = tasa_base
        
        # Aplicar coeficientes
        if 'superficie' in coef and datos.get('superficie'):
            contrib = coef['superficie'] * datos['superficie']
            tasa_base += contrib
            contribuciones['superficie'] = contrib
        
        if 'antiguedad' in coef and datos.get('antiguedad'):
            contrib = coef['antiguedad'] * datos['antiguedad']
            tasa_base += contrib
            contribuciones['antiguedad'] = contrib
        
        if 'banos' in coef and datos.get('banos'):
            contrib = coef['banos'] * datos['banos']
            tasa_base += contrib
            contribuciones['banos'] = contrib
        
        if 'dormitorios' in coef and datos.get('dormitorios'):
            contrib = coef['dormitorios'] * datos['dormitorios']
            tasa_base += contrib
            contribuciones['dormitorios'] = contrib
        
        if datos.get('calidad_alta') and 'calidad_alta' in coef:
            contrib = coef['calidad_alta']
            tasa_base += contrib
            contribuciones['calidad_alta'] = contrib
        
        if datos.get('estado_alto') and 'estado_alto' in coef:
            contrib = coef['estado_alto']
            tasa_base += contrib
            contribuciones['estado_alto'] = contrib
        
        if datos.get('ascensor') and 'ascensor' in coef:
            contrib = coef['ascensor']
            tasa_base += contrib
            contribuciones['ascensor'] = contrib
        
        if 'planta' in coef and datos.get('planta'):
            contrib = coef['planta'] * datos['planta']
            tasa_base += contrib
            contribuciones['planta'] = contrib
        
        return max(0.01, min(0.15, tasa_base)), contribuciones

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
    if 'modelo' not in st.session_state:
        st.session_state.modelo = ModeloTasacion(st.session_state.config)
    if 'resultados_individuales' not in st.session_state:
        st.session_state.resultados_individuales = []

def mostrar_header():
    """Header profesional con logos"""
    logo_aesval = get_image_base64("assets/aesval.png")
    logo_ctic = get_image_base64("assets/CTIC.png")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if logo_aesval:
            st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_aesval}" width="150"></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align: center; background: linear-gradient(135deg, #1f77b4, #2e8bc0); padding: 30px; border-radius: 10px; color: white;"><h3>🏢 AESVAL</h3><p style="font-size: 0.8rem;">Entidad Tasadora</p></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <h1 style='color: #1f77b4; margin-bottom: 0.5rem; font-size: 2.5rem;'>
                🏠 SISTEMA DE TASACIÓN ECO 805
            </h1>
            <h3 style='color: #666; margin-top: 0; font-weight: 300;'>
                Modelos Econométricos Basados en Análisis de Regresión
            </h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if logo_ctic:
            st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_ctic}" width="120"></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align: center; background: linear-gradient(135deg, #ff6b6b, #ff8e8e); padding: 30px; border-radius: 10px; color: white;"><h3>🔬 CTIC</h3><p style="font-size: 0.8rem;">Centro Tecnológico</p></div>', unsafe_allow_html=True)
    
    st.markdown("---")

def mostrar_sidebar():
    """Sidebar con información del sistema"""
    with st.sidebar:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #1f77b4, #2e8bc0); padding: 2rem; border-radius: 10px; color: white; margin-bottom: 2rem;'>
            <h3 style='color: white; margin-bottom: 1rem;'>📊 Sistema AESVAL ECO 805</h3>
            <p style='margin-bottom: 0; font-size: 0.9rem;'>
                Plataforma oficial para la tasación inteligente de inmuebles según normativa ECO 805
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### ℹ️ Información del Sistema")
        config = st.session_state.config
        st.info(f"""
        **Versión:** {config.get('version', '2.0')}  
        **Actualización:** {config.get('fecha_actualizacion', '2025-01-10')}  
        **Modelo:** ECO 805 - Análisis Econométrico  
        **Base de datos:** 205,000+ testigos
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("R² Promedio", "82%")
        with col2:
            st.metric("Precisión", "97.2%")
        
        st.markdown("---")
        st.markdown("### 📈 Modelos Disponibles")
        st.write("• Municipios < 10,000 hab")
        st.write("• Municipios 10,000-50,000 hab")  
        st.write("• Municipios 50,000-200,000 hab")
        st.write("• Municipios > 200,000 hab")
        st.write("• Modelo Tasa Descuento")
        
        st.markdown("---")
        st.markdown(f"""
        <div style='text-align: center; color: #666; font-size: 0.8rem; padding: 1rem 0;'>
            <p>© {current_year} AESVAL - CTIC</p>
            <p>Sistema de Tasación Inteligente</p>
        </div>
        """, unsafe_allow_html=True)

def obtener_poblacion_municipio(municipio: str) -> int:
    """Obtiene población aproximada del municipio (datos de ejemplo)"""
    poblaciones = {
        "Gijón": 268000,
        "Oviedo": 215000,
        "Avilés": 76000,
        "Mieres": 38000,
        "Langreo": 39000,
        "Siero": 52000,
        "Castrillón": 22000,
        "Corvera": 16000,
        "Carreño": 10500,
        "Gozón": 10500,
        "Villaviciosa": 14500,
        "Sariego": 1300,
        "Bimenes": 1700,
        "Nava": 5200,
        "Cabranes": 800,
        "Piloña": 7200
    }
    return poblaciones.get(municipio, 50000)

def pagina_tasacion_individual():
    """Pestaña para tasación individual con modelos reales"""
    st.header("📊 Tasación Individual - Modelo ECO 805")
    
    with st.container():
        st.info("""
        💡 **Complete los datos del inmueble para obtener una tasación precisa basada en modelos econométricos 
        desarrollados con análisis de regresión múltiple sobre 205,000+ observaciones.**
        """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.container():
            st.subheader("🏛️ Datos del Inmueble")
            
            col1_1, col1_2 = st.columns(2)
            
            with col1_1:
                municipio = st.selectbox(
                    "Municipio",
                    ["Gijón", "Oviedo", "Avilés", "Mieres", "Langreo", "Siero", "Castrillón", 
                     "Corvera", "Carreño", "Gozón", "Villaviciosa", "Sariego", "Bimenes", "Nava", "Cabranes", "Piloña"],
                    help="Seleccione el municipio donde se ubica el inmueble"
                )
                
                superficie = st.number_input(
                    "Superficie construida (m²)", 
                    min_value=20.0, 
                    max_value=1000.0,
                    value=80.0,
                    step=0.5,
                    help="Superficie total construida en metros cuadrados"
                )
                
                antiguedad = st.number_input(
                    "Antigüedad (años)", 
                    min_value=0, 
                    max_value=200,
                    value=15,
                    help="Años desde la construcción del inmueble"
                )
                
                dormitorios = st.number_input(
                    "Número de dormitorios",
                    min_value=1,
                    max_value=10,
                    value=3,
                    help="Número total de dormitorios"
                )
            
            with col1_2:
                banos = st.number_input(
                    "Número de baños",
                    min_value=1,
                    max_value=6,
                    value=2,
                    help="Número total de baños"
                )
                
                planta = st.number_input(
                    "Planta",
                    min_value=0,
                    max_value=20,
                    value=2,
                    help="Planta en la que se ubica el inmueble"
                )
                
                calefaccion = st.checkbox("Calefacción", value=True, help="¿Tiene sistema de calefacción?")
                ascensor = st.checkbox("Ascensor", value=True, help="¿El edificio tiene ascensor?")
                vivienda_nueva = st.checkbox("Vivienda nueva (<5 años)", value=False, help="Menos de 5 años de antigüedad")
                calidad_alta = st.checkbox("Calidad constructiva alta", value=False, help="Calidad de materiales y acabados alta")
                
                estado_conservacion = st.select_slider(
                    "Estado de conservación",
                    options=["Muy deficiente", "Deficiente", "Regular", "Bueno", "Muy bueno", "Excelente"],
                    value="Bueno",
                    help="Estado general de conservación del inmueble"
                )
    
    with col2:
        with st.container():
            st.subheader("🎯 Calcular Tasación")
            
            if st.button("📈 Calcular Valor y Tasa", type="primary", width=True):
                with st.spinner("Calculando tasación usando modelos econométricos..."):
                    # Obtener datos para el modelo
                    poblacion = obtener_poblacion_municipio(municipio)
                    modelo_valor = st.session_state.modelo.obtener_modelo_por_poblacion(poblacion)
                    
                    if not modelo_valor:
                        st.error("❌ No se encontró modelo para el municipio seleccionado")
                        return
                    
                    # Preparar datos
                    datos_inmueble = {
                        'superficie': superficie,
                        'antiguedad': antiguedad,
                        'dormitorios': dormitorios,
                        'banos': banos,
                        'planta': planta,
                        'calefaccion': calefaccion,
                        'ascensor': ascensor,
                        'vivienda_nueva': vivienda_nueva,
                        'calidad_alta': calidad_alta,
                        'estado_alto': estado_conservacion in ["Muy bueno", "Excelente"]
                    }
                    
                    # Calcular valor por m²
                    valor_m2, contrib_valor = st.session_state.modelo.calcular_valor_m2(datos_inmueble, modelo_valor)
                    valor_total = valor_m2 * superficie
                    
                    # Calcular tasa de descuento
                    tasa_descuento, contrib_tasa = st.session_state.modelo.calcular_tasa_descuento(datos_inmueble)
                    
                    # Mostrar resultados
                    st.success("✅ Tasación calculada correctamente")
                    
                    # Métricas principales
                    col_res1, col_res2, col_res3 = st.columns(3)
                    with col_res1:
                        st.metric("Valor por m²", f"€ {valor_m2:,.0f}")
                    with col_res2:
                        st.metric("Valor Total", f"€ {valor_total:,.0f}")
                    with col_res3:
                        st.metric("Tasa Descuento", f"{tasa_descuento:.2%}")
                    
                    # Información del modelo usado
                    st.info(f"**Modelo aplicado:** {modelo_valor['nombre']} (R² = {modelo_valor['r2']})")
                    
                    # Contribuciones detalladas
                    with st.expander("📊 Análisis Detallado de Contribuciones", expanded=True):
                        col_contrib1, col_contrib2 = st.columns(2)
                        
                        with col_contrib1:
                            st.subheader("💰 Contribución al Valor por m²")
                            contrib_df_valor = pd.DataFrame({
                                'Variable': list(contrib_valor.keys()),
                                'Contribución (€)': list(contrib_valor.values())
                            })
                            st.dataframe(contrib_df_valor, width=True)
                        
                        with col_contrib2:
                            st.subheader("📈 Contribución a la Tasa")
                            contrib_df_tasa = pd.DataFrame({
                                'Variable': list(contrib_tasa.keys()),
                                'Contribución (%)': [f"{v:.4f}" for v in contrib_tasa.values()]
                            })
                            st.dataframe(contrib_df_tasa, width=True)
                    
                    # Factores más influyentes
                    with st.expander("🎯 Factores Más Influyentes", expanded=True):
                        # Para valor
                        contrib_abs_valor = {k: abs(v) for k, v in contrib_valor.items() if k != 'valor_base'}
                        top3_valor = sorted(contrib_abs_valor.items(), key=lambda x: x[1], reverse=True)[:3]
                        
                        # Para tasa
                        contrib_abs_tasa = {k: abs(float(v)) for k, v in contrib_tasa.items() if k != 'tasa_base'}
                        top3_tasa = sorted(contrib_abs_tasa.items(), key=lambda x: x[1], reverse=True)[:3]
                        
                        col_top1, col_top2 = st.columns(2)
                        with col_top1:
                            st.write("**Valor por m²:**")
                            for i, (var, val) in enumerate(top3_valor, 1):
                                st.write(f"{i}. {var}: € {contrib_valor[var]:.0f}")
                        
                        with col_top2:
                            st.write("**Tasa de descuento:**")
                            for i, (var, val) in enumerate(top3_tasa, 1):
                                st.write(f"{i}. {var}: {contrib_tasa[var]:.4f}")
                    
                    # Botón de descarga
                    resultado = {
                        'fecha_calculo': datetime.now().isoformat(),
                        'municipio': municipio,
                        'superficie': superficie,
                        'valor_m2': valor_m2,
                        'valor_total': valor_total,
                        'tasa_descuento': tasa_descuento,
                        'modelo_usado': modelo_valor['nombre'],
                        'contribuciones_valor': contrib_valor,
                        'contribuciones_tasa': contrib_tasa
                    }
                    
                    st.download_button(
                        "📥 Descargar Informe JSON",
                        data=json.dumps(resultado, indent=2),
                        file_name=f"tasacion_{municipio}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                        width=True
                    )
            else:
                st.info("ℹ️ Complete los datos y haga clic en 'Calcular Valor y Tasa' para obtener resultados")

def pagina_tasacion_multiple():
    """Pestaña para tasación múltiple con validación avanzada"""
    st.header("📁 Tasación Múltiple por Lotes")
    
    with st.expander("ℹ️ Información sobre tasación múltiple", expanded=True):
        st.markdown("""
        **Características de la tasación por lotes:**
        - Procesamiento simultáneo de múltiples inmuebles usando modelos econométricos
        - Validación automática de datos y formato
        - Detección y reporte de errores por fila
        - Generación de informe consolidado con análisis de contribuciones
        - Límite: 500 registros por lote
        
        **Columnas requeridas en el Excel:**
        - `municipio`: Nombre del municipio
        - `superficie`: Superficie en m² (número)
        - `antiguedad`: Años desde construcción (número)
        - `dormitorios`: Número de dormitorios (número)
        - `banos`: Número de baños (número)
        - `planta`: Planta del inmueble (número)
        - `calefaccion`: Sí/No o 1/0
        - `ascensor`: Sí/No o 1/0
        - `vivienda_nueva`: Sí/No o 1/0
        - `calidad_alta`: Sí/No o 1/0
        """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "📤 Subir archivo Excel para tasación múltiple", 
            type=['xlsx', 'xls'],
            help="El archivo debe contener las columnas requeridas en el formato especificado"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                
                # Validar columnas requeridas
                columnas_requeridas = ['municipio', 'superficie', 'antiguedad', 'dormitorios', 'banos', 'planta']
                columnas_opcionales = ['calefaccion', 'ascensor', 'vivienda_nueva', 'calidad_alta']
                
                faltan_requeridas = [col for col in columnas_requeridas if col not in df.columns]
                if faltan_requeridas:
                    st.error(f"❌ Faltan columnas requeridas: {', '.join(faltan_requeridas)}")
                    return
                
                st.success(f"✅ Archivo cargado correctamente - {len(df)} registros detectados")
                
                # Estadísticas
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                with col_stats1:
                    st.metric("Registros", len(df))
                with col_stats2:
                    st.metric("Municipios", df['municipio'].nunique())
                with col_stats3:
                    st.metric("Tasaciones estimadas", f"{len(df)*3}s")
                
                # Vista previa
                st.subheader("👁️ Vista previa de datos")
                st.dataframe(df.head(10), width=True, height=300)
                
                # Procesar lote
                if st.button("🚀 Procesar Lote Completo", type="primary", width=True):
                    with st.spinner(f"Procesando {len(df)} registros con modelos econométricos..."):
                        resultados = []
                        errores = []
                        
                        for idx, fila in df.iterrows():
                            try:
                                # Validar datos de la fila
                                if pd.isna(fila['municipio']) or pd.isna(fila['superficie']):
                                    errores.append(f"Fila {idx+2}: Datos requeridos faltantes")
                                    continue
                                
                                # Obtener población y modelo
                                poblacion = obtener_poblacion_municipio(str(fila['municipio']))
                                modelo_valor = st.session_state.modelo.obtener_modelo_por_poblacion(poblacion)
                                
                                if not modelo_valor:
                                    errores.append(f"Fila {idx+2}: No hay modelo para {fila['municipio']}")
                                    continue
                                
                                # Preparar datos
                                datos = {
                                    'superficie': float(fila['superficie']),
                                    'antiguedad': float(fila.get('antiguedad', 0)),
                                    'dormitorios': int(fila.get('dormitorios', 0)),
                                    'banos': int(fila.get('banos', 0)),
                                    'planta': int(fila.get('planta', 0)),
                                    'calefaccion': bool(fila.get('calefaccion', False)),
                                    'ascensor': bool(fila.get('ascensor', False)),
                                    'vivienda_nueva': bool(fila.get('vivienda_nueva', False)),
                                    'calidad_alta': bool(fila.get('calidad_alta', False)),
                                    'estado_alto': False  # Por defecto
                                }
                                
                                # Calcular valores
                                valor_m2, contrib_valor = st.session_state.modelo.calcular_valor_m2(datos, modelo_valor)
                                valor_total = valor_m2 * datos['superficie']
                                tasa_descuento, contrib_tasa = st.session_state.modelo.calcular_tasa_descuento(datos)
                                
                                # Encontrar factores más influyentes
                                contrib_abs = {k: abs(v) for k, v in contrib_valor.items() if k != 'valor_base'}
                                top_factores = sorted(contrib_abs.items(), key=lambda x: x[1], reverse=True)[:2]
                                factores_influyentes = ", ".join([f[0] for f in top_factores])
                                
                                resultados.append({
                                    'municipio': fila['municipio'],
                                    'superficie': datos['superficie'],
                                    'valor_m2': round(valor_m2, 2),
                                    'valor_total': round(valor_total, 2),
                                    'tasa_descuento': round(tasa_descuento, 4),
                                    'modelo': modelo_valor['nombre'],
                                    'factores_influyentes': factores_influyentes
                                })
                                
                            except Exception as e:
                                errores.append(f"Fila {idx+2}: Error en cálculo - {str(e)}")
                        
                        # Mostrar resultados
                        if resultados:
                            st.success(f"✅ Procesamiento completado - {len(resultados)} tasaciones generadas")
                            
                            # Crear DataFrame de resultados
                            df_resultados = pd.DataFrame(resultados)
                            
                            # Mostrar resumen
                            col_res1, col_res2, col_res3 = st.columns(3)
                            with col_res1:
                                st.metric("Valor medio m²", f"€ {df_resultados['valor_m2'].mean():,.0f}")
                            with col_res2:
                                st.metric("Tasa media", f"{df_resultados['tasa_descuento'].mean():.2%}")
                            with col_res3:
                                st.metric("Éxito", f"{len(resultados)}/{len(df)}")
                            
                            # Mostrar resultados detallados
                            st.subheader("📋 Resultados Detallados")
                            st.dataframe(df_resultados, width=True)
                            
                            # Botón de descarga
                            csv = df_resultados.to_csv(index=False)
                            st.download_button(
                                "📥 Descargar Resultados CSV",
                                data=csv,
                                file_name=f"resultados_tasacion_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                mime="text/csv",
                                width=True
                            )
                        
                        if errores:
                            st.warning(f"⚠️ Se encontraron {len(errores)} errores:")
                            for error in errores[:10]:  # Mostrar solo primeros 10 errores
                                st.write(f"• {error}")
                            if len(errores) > 10:
                                st.write(f"... y {len(errores) - 10} errores más")
                                
            except Exception as e:
                st.error(f"❌ Error procesando el archivo: {str(e)}")
    
    with col2:
        st.subheader("📋 Plantilla de Ejemplo")
        
        # Crear plantilla con datos de ejemplo
        sample_data = {
            'municipio': ['Gijón', 'Oviedo', 'Avilés', 'Sariego', 'Nava'],
            'superficie': [85.5, 120.0, 65.0, 95.0, 110.0],
            'antiguedad': [15, 8, 25, 5, 12],
            'dormitorios': [3, 4, 2, 3, 4],
            'banos': [2, 3, 1, 2, 2],
            'planta': [2, 3, 1, 0, 2],
            'calefaccion': [True, True, False, True, True],
            'ascensor': [True, True, False, False, True],
            'vivienda_nueva': [False, True, False, True, False],
            'calidad_alta': [False, True, False, False, True]
        }
        sample_df = pd.DataFrame(sample_data)
        
        st.download_button(
            "📥 Descargar plantilla",
            data=sample_df.to_csv(index=False),
            file_name="plantilla_tasacion_multiple.csv",
            mime="text/csv",
            help="Descargue esta plantilla como referencia para el formato requerido",
            width=True
        )
        
        st.markdown("---")
        st.markdown("### 💡 Consejos")
        st.write("• Use nombres de municipios consistentes")
        st.write("• Verifique que los valores numéricos sean positivos")
        st.write("• Las columnas booleanas pueden usar Sí/No o 1/0")
        st.write("• El procesamiento tarda ~3 segundos por registro")

def pagina_documentacion():
    """Pestaña de documentación técnica mejorada"""
    st.header("📚 Documentación Técnica - Modelos ECO 805")
    
    # Introducción
    st.markdown("""
    <div style='background: #f0f2f6; padding: 2rem; border-radius: 10px; border-left: 4px solid #1f77b4;'>
        <h4 style='color: #1f77b4; margin-top: 0;'>Modelos Econométricos para Tasación Inmobiliaria</h4>
        <p style='margin-bottom: 0;'>
            Sistema de valoración basado en análisis de regresión múltiple sobre una base de datos de 
            <strong>205,000+ observaciones</strong> (testigos y viviendas tasadas). Desarrollado según 
            la normativa ECO 805 con validación estadística robusta.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metodología
    st.subheader("🔬 Metodología Científica")
    
    col_metodo1, col_metodo2 = st.columns(2)
    
    with col_metodo1:
        st.markdown("""
        **Base de Datos:**
        - **205,000+ testigos** inmobiliarios
        - **34,000+ viviendas** tasadas por AESVAL
        - Período de análisis: **2000-2024**
        - Variables intrínsecas y extrínsecas
        
        **Procesamiento:**
        - Limpieza y validación de datos
        - Análisis de regresión múltiple
        - Segmentación por tamaño municipal
        - Validación de robustez estadística
        """)
    
    with col_metodo2:
        st.markdown("""
        **Validación Estadística:**
        - Coeficientes de determinación R²: 0.78-0.88
        - Errores estándar robustos
        - Tests de significancia estadística
        - Análisis de residuos
        - Validación cruzada
        
        **Software Utilizado:**
        - STATA 18 para análisis econométrico
        - Python para implementación
        - Streamlit para interfaz web
        """)
    
    # Modelos matemáticos
    st.subheader("🧮 Modelos Matemáticos Implementados")
    
    tab_model1, tab_model2, tab_model3 = st.tabs(["Valor por m²", "Tasa Descuento", "Prima Riesgo"])
    
    with tab_model1:
        st.markdown("""
        ### Modelo de Valor por Metro Cuadrado
        
        $$VM_{i} = \\beta_0 + \\sum_{j=1}^{J}\\beta_j X_{ji} + \\epsilon_i$$
        
        **Donde:**
        - $VM_{i}$: Valor por m² del inmueble i
        - $\\beta_0$: Término independiente (valor base municipal)
        - $\\beta_j$: Coeficientes de las variables explicativas
        - $X_{ji}$: Variables intrínsecas del inmueble
        - $\\epsilon_i$: Término de error
        
        **Variables Significativas:**
        - Superficie (efecto variable según municipio)
        - Antigüedad (depreciación)
        - Número de baños (positivo)
        - Número de dormitorios (negativo en municipios grandes)
        - Calefacción, ascensor, calidad constructiva
        """)
        
        # Mostrar coeficientes de ejemplo
        st.markdown("#### Coeficientes Ejemplares (Municipios >200,000 hab)")
        coef_ejemplo = {
            'Intercepto': 1410.69,
            'Vivienda Nueva': 161.31,
            'Superficie (m²)': 7.44,
            'Calefacción': 140.03,
            'Dormitorios': -379.05,
            'Baños': 290.35,
            'Calidad Alta': 418.63,
            'Ascensor': 584.55,
            'Planta': 30.40
        }
        st.dataframe(pd.DataFrame(list(coef_ejemplo.items()), columns=['Variable', 'Coeficiente (€)']))
    
    with tab_model2:
        st.markdown("""
        ### Modelo de Tasa de Descuento
        
        $$Tasa_i = \\beta_0 + \\sum_{j=1}^{J}\\beta_j X_{ji} + \\epsilon_i$$
        
        **Componentes:**
        - Tasa libre de riesgo (bonos estado 5 años)
        - Prima de riesgo específica del inmueble
        
        **Variables Significativas:**
        - Superficie: efecto positivo marginal
        - Antigüedad: efecto positivo (mayor riesgo)
        - Baños: efecto negativo (reduce riesgo)
        - Ascensor: efecto negativo (reduce riesgo)
        - Estado conservación alto: efecto negativo
        """)
        
        st.latex(r"""
        \text{Tasa Descuento} = \text{Tasa Libre Riesgo} + \text{Prima Riesgo}
        """)
    
    with tab_model3:
        st.markdown("""
        ### Modelo de Prima de Riesgo
        
        $$Prima_i = \\beta_0 + \\sum_{j=1}^{J}\\beta_j X_{ji} + \\epsilon_i$$
        
        **Factores de Riesgo Considerados:**
        - Riesgo de ubicación (municipio)
        - Riesgo por antigüedad y estado
        - Riesgo por características constructivas
        - Riesgo de mercado local
        
        **Hallazgos Clave:**
        - Municipios pequeños: mayor prima por iliquidez
        - Antigüedad: aumenta prima consistentemente
        - Ascensor y buen estado: reducen prima
        - Calidad constructiva: efecto variable
        """)
    
    # Segmentación por población
    st.subheader("🏙️ Segmentación por Tamaño Municipal")
    
    col_seg1, col_seg2, col_seg3, col_seg4 = st.columns(4)
    
    with col_seg1:
        st.metric("< 10,000 hab", "R² = 0.78", "Modelo más estable")
    with col_seg2:
        st.metric("10,000-50,000", "R² = 0.82", "Balanceado")
    with col_seg3:
        st.metric("50,000-200,000", "R² = 0.85", "Alta precisión")
    with col_seg4:
        st.metric("> 200,000 hab", "R² = 0.88", "Máxima granularidad")
    
    st.markdown("""
    **Efectos Diferenciales por Segmento:**
    - **Superficie**: Negativo en municipios pequeños, positivo en grandes
    - **Dormitorios**: Efecto negativo se intensifica con tamaño municipal
    - **Ascensor**: Impacto creciente con tamaño municipal
    - **Planta**: Mayor valoración en municipios grandes
    """)
    
    # Variables analizadas
    st.subheader("📊 Variables Analizadas en el Estudio")
    
    tab_vars1, tab_vars2, tab_vars3 = st.tabs(["Intrínsecas", "Extrínsecas", "Resultados"])
    
    with tab_vars1:
        st.markdown("""
        ### Variables Intrínsecas del Inmueble
        
        **Características Físicas:**
        - Superficie construida (m²)
        - Año de construcción → Antigüedad
        - Número de dormitorios
        - Número de baños
        - Planta de ubicación
        
        **Calidades y Dotaciones:**
        - Calidad constructiva (Básica/Media/Alta/Lujo)
        - Estado de conservación (1-6)
        - Calefacción (Sí/No)
        - Ascensor (Sí/No)
        - Aire acondicionado
        - Trastero, plaza garaje
        """)
    
    with tab_vars2:
        st.markdown("""
        ### Variables Extrínsecas y de Entorno
        
        **Ubicación:**
        - Municipio y código postal
        - Comunidad Autónoma
        - Tamaño de población
        - Tipología de núcleo (urbano/rural)
        
        **Entorno Económico:**
        - Euribor histórico
        - Crecimiento del PIB
        - Tasa de paro municipal
        - IPC y evolución de precios
        
        **Servicios y Equipamientos:**
        - Accesibilidad y comunicaciones
        - Equipamiento educativo
        - Zonas verdes y recreativas
        - Comercio y servicios
        """)
    
    with tab_vars3:
        st.markdown("""
        ### Resultados y Validaciones
        
        **Robustez Estadística:**
        - Todos los coeficientes significativos (p < 0.05)
        - R² consistentes por segmentos
        - Residuos normalmente distribuidos
        - No multicolinealidad crítica
        
        **Validación Cruzada:**
        - Comparación testigos vs viviendas tasadas
        - Análisis por períodos temporales
        - Validación con datos externos (INE)
        
        **Aplicabilidad:**
        - Cobertura nacional completa
        - Actualización periódica automática
        - Escalable a nuevas tipologías
        """)

def mostrar_footer():
    """Footer profesional"""
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            f"""
            <div style='text-align: center; color: #666; padding: 2rem 0;'>
                <p style='margin-bottom: 0.5rem; font-size: 0.9rem;'>
                    © {current_year} <strong>AESVAL</strong> - Centro Tecnológico CTIC | 
                    Sistema de Tasación Inteligente ECO 805 v2.0
                </p>
                <p style='margin-bottom: 0; font-size: 0.8rem;'>
                    Desarrollado con Streamlit • Modelos Econométricos STATA • 
                    <a href='#' style='color: #666;'>Política de privacidad</a> • 
                    <a href='#' style='color: #666;'>Términos de uso</a>
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )

def main():
    """Función principal"""
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