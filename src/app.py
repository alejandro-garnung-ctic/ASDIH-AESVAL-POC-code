import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import io
import base64
from datetime import datetime
import json
import yaml
import os

current_year = datetime.now().year

# Configuración de página
st.set_page_config(
    page_title="AESVAL - Sistema de Tasación Automático ECO 805",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ocultar menú de Streamlit
# hide_streamlit_style = """
#     <style>
    
#     /* Ocultar todo el header */
#     header {
#         opacity: 0;
#     }
    
#     /* Mostrar solo el botón de expandir/contraer sidebar */
#     button[data-testid="stExpandSidebarButton"] {
#         display: block !important;
#         position: fixed !important;
#         top: 10px !important;
#         left: 10px !important;
#         z-index: 999999 !important;
#         background: white !important;
#         border: 1px solid #ccc !important;
#         border-radius: 4px !important;
#         padding: 8px !important;
#         opacity: 1;
#     }
    
#     </style>
# """
# st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def cargar_configuracion_sistema():
    """Carga la configuración del sistema desde archivo YAML"""
    try:
        with open('config/info.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        st.error("❌ No se encontró el archivo de configuración del sistema: config/info.yaml")
        # Configuración por defecto
        return {
            'sistema': {
                'nombre': 'Sistema de Tasación Automático ECO 805',
                'version': '2.0',
                'actualizacion': '2025-01-10',
                'modelo': 'ECO 805 - Análisis Econométrico',
                'base_datos': '205,000+ testigos',
                'desarrollador': 'AESVAL - CTIC',
                'año': 2025
            },
            'metricas': {
                'r2_promedio': '82%',
                'precision': '97.2%',
                'tiempo_procesamiento': '3 segundos por registro',
                'limite_registros': 500
            },
            'modelos_disponibles': [
                {'clave': 'testigos_menos_10000', 'nombre': 'Municipios < 10,000 hab'},
                {'clave': 'testigos_10000_50000', 'nombre': 'Municipios 10,000-50,000 hab'},
                {'clave': 'testigos_50000_200000', 'nombre': 'Municipios 50,000-200,000 hab'},
                {'clave': 'testigos_mas_200000', 'nombre': 'Municipios > 200,000 hab'},
                {'clave': 'testigos_tasa', 'nombre': 'Modelo Tasa Descuento'},
                {'clave': 'testigos_prima', 'nombre': 'Modelo Prima Riesgo'}
            ]
        }
    except Exception as e:
        st.error(f"❌ Error cargando configuración del sistema: {e}")
        return None

def cargar_modelos_json():
    """Carga los modelos desde archivos JSON en config/"""
    modelos = {}
    
    # Mapeo exacto según los nombres de tus archivos
    mapeo_modelos = {
        'modelo_Testigos_menos_de_10000': 'testigos_menos_10000',
        'modelo_Testigos_10000-50000': 'testigos_10000_50000', 
        'modelo_Testigos_50000-200000': 'testigos_50000_200000',
        'modelo_Testigos_más_de_200000': 'testigos_mas_200000',
        'modelo_Testigos_Prima': 'testigos_prima',
        'modelo_Testigos_Tasa': 'testigos_tasa'
    }
    
    for archivo, clave in mapeo_modelos.items():
        try:
            ruta = f"config/{archivo}.json"
            if os.path.exists(ruta):
                with open(ruta, 'r', encoding='utf-8') as f:
                    modelos[clave] = json.load(f)
                    print(f"✅ Modelo {clave} cargado correctamente")
            else:
                # Buscar archivos similares
                archivos_disponibles = [f for f in os.listdir('config') if f.endswith('.json')]
                archivo_encontrado = None
                
                # Buscar coincidencias aproximadas
                for archivo_disp in archivos_disponibles:
                    archivo_sin_ext = archivo_disp.replace('.json', '')
                    if archivo_sin_ext.lower().replace('_', '-').replace('á', 'a') == archivo.lower().replace('_', '-').replace('á', 'a'):
                        archivo_encontrado = archivo_disp
                        break
                
                if archivo_encontrado:
                    ruta_alternativa = f"config/{archivo_encontrado}"
                    with open(ruta_alternativa, 'r', encoding='utf-8') as f:
                        modelos[clave] = json.load(f)
                    st.success(f"✅ Modelo {clave} cargado desde {archivo_encontrado}")
                else:
                    st.warning(f"⚠️ No se encontró {ruta} (archivos disponibles: {', '.join(archivos_disponibles)})")
                    
        except Exception as e:
            st.error(f"❌ Error cargando {archivo}: {e}")
    
    return modelos

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

def es_modelo_tasa_o_prima(nombre_modelo: str) -> bool:
    """Determina si el modelo es de Tasa o Prima"""
    return 'tasa' in nombre_modelo.lower() or 'prima' in nombre_modelo.lower()

def es_modelo_valor(nombre_modelo: str) -> bool:
    """Determina si el modelo es de valor normal"""
    return not es_modelo_tasa_o_prima(nombre_modelo)

class ModeloTasacion:
    """Clase para gestionar los modelos de tasación"""
    
    def __init__(self, modelos_json: Dict):
        self.modelos = modelos_json
    
    def obtener_modelos_disponibles(self) -> List[Tuple[str, str]]:
        """Retorna la lista de modelos disponibles con nombres legibles desde YAML"""
        # Intentar obtener desde la configuración YAML
        if hasattr(st.session_state, 'config_sistema') and st.session_state.config_sistema:
            modelos_config = st.session_state.config_sistema.get('modelos_disponibles', [])
            disponibles = []
            for modelo_config in modelos_config:
                clave = modelo_config.get('clave')
                nombre = modelo_config.get('nombre')
                if clave in self.modelos: # Solo incluir modelos que estén cargados
                    disponibles.append((clave, nombre))
            
            if disponibles:
                return disponibles
        
        # Fallback a nombres por defecto
        nombres_legibles = {
            'testigos_menos_10000': 'Municipios < 10,000 hab',
            'testigos_10000_50000': 'Municipios 10,000-50,000 hab',
            'testigos_50000_200000': 'Municipios 50,000-200,000 hab',
            'testigos_mas_200000': 'Municipios > 200,000 hab',
            'testigos_tasa': 'Modelo Tasa Descuento',
            'testigos_prima': 'Modelo Prima Riesgo'
        }
        
        disponibles = []
        for clave in self.modelos.keys():
            nombre = nombres_legibles.get(clave, clave)
            disponibles.append((clave, nombre))
        
        return disponibles

    def obtener_modelo(self, nombre_modelo: str) -> Optional[Dict]:
        """Obtiene el modelo por su nombre"""
        return self.modelos.get(nombre_modelo)
    
    def calcular_valor_m2(self, datos: Dict, modelo: Dict, codigo_municipio: str) -> Tuple[float, Dict]:
        """Calcula el valor por m² usando el modelo especificado"""
        coef_municipio = modelo['coeficientes_municipios'].get(str(codigo_municipio), 0)
        coef_variables = modelo['coeficientes_variables']
        _cons = modelo['_cons']
        
        contribuciones = {}
        contribuciones_porcentaje = {}
        
        # Valor base (constante + efecto municipio)
        valor_base = _cons + coef_municipio
        contribuciones['valor_base'] = valor_base
        contribuciones[f'municipio_{codigo_municipio}'] = coef_municipio
        
        # Aplicar coeficientes según variables disponibles
        if datos.get('vivienda_nueva') and 'Dnueva' in coef_variables and coef_variables['Dnueva'] is not None:
            contrib = coef_variables['Dnueva']
            valor_base += contrib
            contribuciones['vivienda_nueva'] = contrib
        
        if 'SU' in coef_variables and coef_variables['SU'] is not None and datos.get('superficie'):
            contrib = coef_variables['SU'] * datos['superficie']
            valor_base += contrib
            contribuciones['superficie'] = contrib
        
        if datos.get('calefaccion') and 'DCA' in coef_variables and coef_variables['DCA'] is not None:
            contrib = coef_variables['DCA']
            valor_base += contrib
            contribuciones['calefaccion'] = contrib
        
        if 'ND' in coef_variables and coef_variables['ND'] is not None and datos.get('dormitorios'):
            contrib = coef_variables['ND'] * datos['dormitorios']
            valor_base += contrib
            contribuciones['dormitorios'] = contrib
        
        if 'NB' in coef_variables and coef_variables['NB'] is not None and datos.get('banos'):
            contrib = coef_variables['NB'] * datos['banos']
            valor_base += contrib
            contribuciones['banos'] = contrib
        
        if datos.get('calidad_alta') and 'CC_Alta' in coef_variables and coef_variables['CC_Alta'] is not None:
            contrib = coef_variables['CC_Alta']
            valor_base += contrib
            contribuciones['calidad_alta'] = contrib
        
        if datos.get('ascensor') and 'DAS' in coef_variables and coef_variables['DAS'] is not None:
            contrib = coef_variables['DAS']
            valor_base += contrib
            contribuciones['ascensor'] = contrib
        
        if 'PLbis' in coef_variables and coef_variables['PLbis'] is not None and datos.get('planta'):
            contrib = coef_variables['PLbis'] * datos['planta']
            valor_base += contrib
            contribuciones['planta'] = contrib
        
        valor_final = max(0, valor_base)
        
        # CALCULAR PORCENTAJES RELATIVOS
        if valor_final > 0:
            for key, value in contribuciones.items():
                contribuciones_porcentaje[key] = (value / valor_final) * 100 # En porcentaje
        
        return valor_final, contribuciones_porcentaje # ← Devuelve porcentajes
    
    def calcular_tasa_descuento(self, datos: Dict, codigo_municipio: str) -> Tuple[float, Dict]:
        """Calcula la tasa de descuento usando el modelo correspondiente INCLUYENDO MUNICIPIO"""
        
        # Obtener el modelo de tasa desde los JSON cargados
        modelo_tasa = self.modelos.get('testigos_tasa')
        if not modelo_tasa:
            st.error("❌ No se encontró el modelo de tasa en los archivos JSON")
            return 0.05, {}
        
        # Usar los coeficientes reales del modelo JSON
        coef_municipio = modelo_tasa['coeficientes_municipios'].get(str(codigo_municipio), 0)
        coef_variables = modelo_tasa['coeficientes_variables']
        _cons = modelo_tasa['_cons']
        
        contribuciones = {}
        contribuciones_porcentaje = {}
        
        # Tasa base (constante + efecto municipio)
        tasa_base = _cons + coef_municipio
        contribuciones['tasa_base'] = tasa_base
        contribuciones[f'municipio_{codigo_municipio}'] = coef_municipio
        
        # Aplicar coeficientes según variables disponibles usando los coeficientes reales
        if 'SU' in coef_variables and coef_variables['SU'] is not None and datos.get('superficie'):
            contrib = coef_variables['SU'] * datos['superficie']
            tasa_base += contrib
            contribuciones['superficie'] = contrib
        
        if 'antig' in coef_variables and coef_variables['antig'] is not None and datos.get('antiguedad'):
            contrib = coef_variables['antig'] * datos['antiguedad']
            tasa_base += contrib
            contribuciones['antiguedad'] = contrib
        
        if datos.get('vivienda_nueva') and 'Dnueva' in coef_variables and coef_variables['Dnueva'] is not None:
            contrib = coef_variables['Dnueva']
            tasa_base += contrib
            contribuciones['vivienda_nueva'] = contrib
        
        if 'NB' in coef_variables and coef_variables['NB'] is not None and datos.get('banos'):
            contrib = coef_variables['NB'] * datos['banos']
            tasa_base += contrib
            contribuciones['banos'] = contrib
        
        if 'ND' in coef_variables and coef_variables['ND'] is not None and datos.get('dormitorios'):
            contrib = coef_variables['ND'] * datos['dormitorios']
            tasa_base += contrib
            contribuciones['dormitorios'] = contrib
        
        if datos.get('ascensor') and 'DAS' in coef_variables and coef_variables['DAS'] is not None:
            contrib = coef_variables['DAS']
            tasa_base += contrib
            contribuciones['ascensor'] = contrib
        
        if datos.get('estado_alto') and 'EC_Alto' in coef_variables and coef_variables['EC_Alto'] is not None:
            contrib = coef_variables['EC_Alto']
            tasa_base += contrib
            contribuciones['estado_alto'] = contrib
        
        if datos.get('rehabilitacion') and 'rehab' in coef_variables and coef_variables['rehab'] is not None:
            contrib = coef_variables['rehab']
            tasa_base += contrib
            contribuciones['rehabilitacion'] = contrib
        
        # Asegurar que la tasa esté en un rango razonable
        tasa_final = max(0.01, min(1.0, tasa_base))
        
        # CALCULAR PORCENTAJES RELATIVOS
        contribuciones_porcentaje = {}
        for key, value in contribuciones.items():
            contribuciones_porcentaje[key] = (value / tasa_final) * 100  
        
        return tasa_final, contribuciones_porcentaje

    def calcular_prima_riesgo(self, datos: Dict, codigo_municipio: str) -> Tuple[float, Dict]:
        """Calcula la prima de riesgo usando el modelo correspondiente INCLUYENDO MUNICIPIO"""
        
        # Obtener el modelo de prima desde los JSON cargados
        modelo_prima = self.modelos.get('testigos_prima')
        if not modelo_prima:
            st.error("❌ No se encontró el modelo de prima en los archivos JSON")
            return 0.02, {}
        
        # Usar los coeficientes reales del modelo JSON
        coef_municipio = modelo_prima['coeficientes_municipios'].get(str(codigo_municipio), 0)
        coef_variables = modelo_prima['coeficientes_variables']
        _cons = modelo_prima['_cons']
        
        contribuciones = {}
        contribuciones_porcentaje = {}
        
        # Prima base (constante + efecto municipio)
        prima_base = _cons + coef_municipio
        contribuciones['prima_base'] = prima_base
        contribuciones[f'municipio_{codigo_municipio}'] = coef_municipio
        
        # Aplicar coeficientes según variables disponibles usando los coeficientes reales
        if 'SU' in coef_variables and coef_variables['SU'] is not None and datos.get('superficie'):
            contrib = coef_variables['SU'] * datos['superficie']
            prima_base += contrib
            contribuciones['superficie'] = contrib
        
        if 'antig' in coef_variables and coef_variables['antig'] is not None and datos.get('antiguedad'):
            contrib = coef_variables['antig'] * datos['antiguedad']
            prima_base += contrib
            contribuciones['antiguedad'] = contrib
        
        if datos.get('vivienda_nueva') and 'Dnueva' in coef_variables and coef_variables['Dnueva'] is not None:
            contrib = coef_variables['Dnueva']
            prima_base += contrib
            contribuciones['vivienda_nueva'] = contrib
        
        if 'NB' in coef_variables and coef_variables['NB'] is not None and datos.get('banos'):
            contrib = coef_variables['NB'] * datos['banos']
            prima_base += contrib
            contribuciones['banos'] = contrib
        
        if 'ND' in coef_variables and coef_variables['ND'] is not None and datos.get('dormitorios'):
            contrib = coef_variables['ND'] * datos['dormitorios']
            prima_base += contrib
            contribuciones['dormitorios'] = contrib
        
        if datos.get('ascensor') and 'DAS' in coef_variables and coef_variables['DAS'] is not None:
            contrib = coef_variables['DAS']
            prima_base += contrib
            contribuciones['ascensor'] = contrib
        
        if datos.get('estado_alto') and 'EC_Alto' in coef_variables and coef_variables['EC_Alto'] is not None:
            contrib = coef_variables['EC_Alto']
            prima_base += contrib
            contribuciones['estado_alto'] = contrib
        
        if datos.get('rehabilitacion') and 'rehab' in coef_variables and coef_variables['rehab'] is not None:
            contrib = coef_variables['rehab']
            prima_base += contrib
            contribuciones['rehabilitacion'] = contrib
        
        # Asegurar que la prima esté en un rango razonable
        prima_final = max(0.01, min(1.0, prima_base))
        
        # CALCULAR PORCENTAJES RELATIVOS
        contribuciones_porcentaje = {}
        for key, value in contribuciones.items():
            contribuciones_porcentaje[key] = (value / prima_final) * 100 
        
        return prima_final, contribuciones_porcentaje

def inicializar_session_state():
    """Inicializa variables de session state"""
    if 'modelos_json' not in st.session_state:
        st.session_state.modelos_json = cargar_modelos_json()
    if 'modelo' not in st.session_state:
        st.session_state.modelo = ModeloTasacion(st.session_state.modelos_json)
    if 'resultados_individuales' not in st.session_state:
        st.session_state.resultados_individuales = []
    if 'config_sistema' not in st.session_state:
        st.session_state.config_sistema = cargar_configuracion_sistema()
    
    # Inicializar variables para persistencia de datos entre modelos
    if 'datos_persistentes' not in st.session_state:
        st.session_state.datos_persistentes = {
            'superficie': 80.0,
            'dormitorios': 3,
            'banos': 2,
            'planta': 2,
            'ascensor': True,
            'calidad_alta': False,
            'vivienda_nueva': False,
            'calefaccion': True,
            'antiguedad': 15,
            'rehabilitacion': False,
            'estado_conservacion': "Buena",
            'codigo_municipio': '2005', 
            'modelo_seleccionado': 'testigos_menos_10000' 
        }

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
            <h2 style='color: #1f77b4; margin-bottom: 0.5rem; font-size: 2.5rem;'>
                🏠 SISTEMA DE TASACIÓN
            </h2>
            <h4 style='color: #666; margin-top: 0; font-weight: 300;'>
                Modelos Econométricos Basados en Análisis de Regresión
            </h4>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if logo_ctic:
            st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_ctic}" width="120"></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align: center; background: linear-gradient(135deg, #ff6b6b, #ff8e8e); padding: 30px; border-radius: 10px; color: white;"><h3>🔬 CTIC</h3><p style="font-size: 0.8rem;">Centro Tecnológico</p></div>', unsafe_allow_html=True)
    
    st.markdown("---")

def mostrar_sidebar():
    """Sidebar con información del sistema cargada desde YAML"""
    if not st.session_state.config_sistema:
        st.error("No se pudo cargar la configuración del sistema")
        return
        
    config = st.session_state.config_sistema
    sistema = config.get('sistema', {})
    metricas = config.get('metricas', {})
    modelos_config = config.get('modelos_disponibles', [])
    
    with st.sidebar:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #1f77b4, #2e8bc0); padding: 2rem; border-radius: 10px; color: white; margin-bottom: 2rem;'>
            <h3 style='color: white; margin-bottom: 1rem;'>📊 {sistema.get('nombre', 'Sistema AESVAL ECO 805')}</h3>
            <p style='margin-bottom: 0; font-size: 0.9rem;'>
                Plataforma oficial para la tasación inteligente de inmuebles según normativa ECO 805
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### ℹ️ Información del Sistema")
        st.info(f"""
        **Versión:** {sistema.get('version', '2.0')}\n
        **Actualización:** {sistema.get('actualizacion', '2025-01-10')}\n
        **Modelo:** {sistema.get('modelo', 'ECO 805 - Análisis Econométrico')}\n
        **Base de datos:** {sistema.get('base_datos', '205,000+ testigos')}
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("R² Promedio", metricas.get('r2_promedio', '82%'))
        
        st.markdown("---")
        st.markdown("### 📈 Modelos Disponibles")
        
        # Mostrar modelos desde la configuración YAML
        for modelo in modelos_config:
            nombre = modelo.get('nombre', modelo.get('clave', ''))
            st.write(f"• {nombre}")
        
        st.markdown("---")
        st.markdown(f"""
        <div style='text-align: center; color: #666; font-size: 0.8rem; padding: 1rem 0;'>
            <p>© {sistema.get('año', current_year)} {sistema.get('desarrollador', 'AESVAL - CTIC')}</p>
            <p>Sistema de Tasación Automático</p>
        </div>
        """, unsafe_allow_html=True)

def pagina_tasacion_individual():
    """Pestaña para tasación individual con modelos reales - VERSIÓN CORREGIDA"""
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
                # Selección directa del modelo
                modelos_disponibles = st.session_state.modelo.obtener_modelos_disponibles()
                if not modelos_disponibles:
                    st.error("❌ No se cargaron modelos. Verifique los archivos JSON en config/")
                    st.stop()
                
                # Obtener modelo actual de datos persistentes
                modelo_actual = st.session_state.datos_persistentes.get('modelo_seleccionado', 'testigos_menos_10000')
                
                modelo_seleccionado = st.selectbox(
                    "Seleccione el modelo",
                    options=[clave for clave, _ in modelos_disponibles],
                    format_func=lambda x: next((nombre for clave, nombre in modelos_disponibles if clave == x), x),
                    help="Elija el modelo econométrico según el tamaño del municipio",
                    key="selectbox_modelo",
                    index=[clave for clave, _ in modelos_disponibles].index(modelo_actual) if modelo_actual in [clave for clave, _ in modelos_disponibles] else 0
                )
                
                # ACTUALIZAR DATOS PERSISTENTES INMEDIATAMENTE cuando cambia el modelo
                if modelo_seleccionado != st.session_state.datos_persistentes.get('modelo_seleccionado'):
                    st.session_state.datos_persistentes['modelo_seleccionado'] = modelo_seleccionado
                
                # Determinar tipo de modelo
                es_tasa_prima = es_modelo_tasa_o_prima(modelo_seleccionado)
                es_modelo_prima = modelo_seleccionado == 'testigos_prima'
                es_modelo_tasa = modelo_seleccionado == 'testigos_tasa'
                es_modelo_valor = not es_tasa_prima
                
                # Código del municipio (siempre visible)
                modelo_obj = st.session_state.modelo.obtener_modelo(modelo_seleccionado)
                codigos_disponibles = list(modelo_obj['coeficientes_municipios'].keys()) if modelo_obj and 'coeficientes_municipios' in modelo_obj else []
                
                if not codigos_disponibles:
                    st.error("❌ El modelo seleccionado no tiene códigos de municipio disponibles")
                    st.stop()
                
                # Obtener municipio actual de datos persistentes
                municipio_actual = st.session_state.datos_persistentes.get('codigo_municipio', '2005')
                
                # Si el municipio actual no está disponible en el nuevo modelo, resetear al primero disponible
                if municipio_actual not in codigos_disponibles:
                    municipio_actual = codigos_disponibles[0]
                    st.session_state.datos_persistentes['codigo_municipio'] = municipio_actual
                
                codigo_municipio = st.selectbox(
                    "Código de Municipio",
                    options=codigos_disponibles,
                    index=codigos_disponibles.index(municipio_actual),
                    help="Seleccione el código del municipio",
                    key="selectbox_municipio"
                )
                
                # ACTUALIZAR DATOS PERSISTENTES cuando cambia el municipio
                if codigo_municipio != st.session_state.datos_persistentes.get('codigo_municipio'):
                    st.session_state.datos_persistentes['codigo_municipio'] = codigo_municipio
                
                # CAMPOS COMUNES A TODOS LOS MODELOS (siempre visibles)
                # Usar valores de datos persistentes como valores por defecto
                datos_persistentes = st.session_state.datos_persistentes
                
                superficie = st.number_input(
                    "Superficie construida (m²)", 
                    min_value=20.0, 
                    max_value=1000.0,
                    value=datos_persistentes.get('superficie', 80.0),
                    step=0.5,
                    help="Superficie total construida en metros cuadrados",
                    key="input_superficie"
                )
                
                dormitorios = st.number_input(
                    "Número de dormitorios",
                    min_value=1,
                    max_value=10,
                    value=datos_persistentes.get('dormitorios', 3),
                    help="Número total de dormitorios (variable ND)",
                    key="input_dormitorios"
                )
                
                banos = st.number_input(
                    "Número de baños",
                    min_value=1,
                    max_value=6,
                    value=datos_persistentes.get('banos', 2),
                    help="Número total de baños (variable NB)",
                    key="input_banos"
                )
                
                # CAMPOS ESPECÍFICOS SEGÚN TIPO DE MODELO
                if es_modelo_valor:
                    # CAMPOS PARA MODELOS DE VALOR
                    vivienda_nueva = st.checkbox(
                        "Vivienda nueva (<5 años)", 
                        value=datos_persistentes.get('vivienda_nueva', False),
                        help="Menos de 5 años de antigüedad (variable Dnueva)",
                        key="input_vivienda_nueva"
                    )
                    
                    calefaccion = st.checkbox(
                        "Calefacción", 
                        value=datos_persistentes.get('calefaccion', True),
                        help="¿Tiene sistema de calefacción? (variable DCA)",
                        key="input_calefaccion"
                    )
                    
                    estado_conservacion_valor = st.select_slider(
                        "Estado de conservación",
                        options=["Muy deficiente", "Deficiente", "Regular", "Buena", "Muy buena", "Óptima"],
                        value=datos_persistentes.get('estado_conservacion', "Buena"),
                        help="Estado general de conservación del inmueble",
                        key="input_estado_conservacion_valor"
                    )
                
                else:
                    # CAMPOS PARA MODELOS DE TASA/PRIMA
                    antiguedad = st.number_input(
                        "Antigüedad (años)", 
                        min_value=0, 
                        max_value=200,
                        value=datos_persistentes.get('antiguedad', 15),
                        help="Años desde la construcción del inmueble (variable antig)",
                        key="input_antiguedad"
                    )
                    
                    rehabilitacion = st.checkbox(
                        "Rehabilitación del edificio", 
                        value=datos_persistentes.get('rehabilitacion', False),
                        help="¿El edificio ha sido rehabilitado? (variable rehab)",
                        key="input_rehabilitacion"
                    )
                    
                    estado_conservacion = st.select_slider(
                        "Estado de conservación",
                        options=["Muy deficiente", "Deficiente", "Regular", "Buena", "Muy buena", "Óptima"],
                        value=datos_persistentes.get('estado_conservacion', "Buena"),
                        help="Estado general de conservación del inmueble (variable EC_Alto)",
                        key="input_estado_conservacion_tasa"
                    )
            
            with col1_2:
                # CAMPOS COMUNES (continuación)
                planta = st.number_input(
                    "Planta",
                    min_value=0,
                    max_value=20,
                    value=datos_persistentes.get('planta', 2),
                    help="Planta en la que se ubica el inmueble (variable PLbis)",
                    key="input_planta"
                )
                
                ascensor = st.checkbox(
                    "Ascensor", 
                    value=datos_persistentes.get('ascensor', True),
                    help="¿El edificio tiene ascensor? (variable DAS)",
                    key="input_ascensor"
                )
                        
                calidad_alta = st.checkbox(
                    "Calidad constructiva alta", 
                    value=datos_persistentes.get('calidad_alta', False),
                    help="Calidad de materiales y acabados alta (variable CC_Alta)",
                    key="input_calidad_alta"
                )

                # Botón para actualizar datos persistentes
                if st.button("💾 Guardar valores actuales", use_container_width=True):
                    # Actualizar datos persistentes con los valores actuales
                    datos_actualizados = {
                        'superficie': superficie,
                        'dormitorios': dormitorios,
                        'banos': banos,
                        'planta': planta,
                        'ascensor': ascensor,
                        'calidad_alta': calidad_alta,
                        'codigo_municipio': codigo_municipio,
                        'modelo_seleccionado': modelo_seleccionado
                    }
                    
                    # Agregar campos específicos según el tipo de modelo
                    if es_modelo_valor:
                        datos_actualizados.update({
                            'vivienda_nueva': vivienda_nueva,
                            'calefaccion': calefaccion,
                            'estado_conservacion': estado_conservacion_valor
                        })
                    else:
                        datos_actualizados.update({
                            'antiguedad': antiguedad,
                            'rehabilitacion': rehabilitacion,
                            'estado_conservacion': estado_conservacion
                        })
                    
                    st.session_state.datos_persistentes.update(datos_actualizados)
                    st.success("✅ Valores guardados para uso entre modelos")
                    
                    # Forzar rerun para aplicar cambios inmediatamente
                    st.rerun()
    
    with col2:
        with st.container():
            st.subheader("🎯 Calcular Tasación")
            
            # Mostrar información del modelo seleccionado
            if es_modelo_prima:
                st.info("🛡️ **Modelo de Prima de Riesgo activado**")
                st.write("Calcula únicamente la prima de riesgo")
            elif es_modelo_tasa:
                st.info("📈 **Modelo de Tasa Descuento activado**")
                st.write("Calcula únicamente la tasa de descuento")
            else:
                st.info("💰 **Modelo de Valor activado**")
                st.write("Calcula únicamente el valor por m²")
            
            # Texto del botón según el tipo de modelo
            texto_boton = ""
            if es_modelo_prima:
                texto_boton = "🛡️ Calcular Prima de Riesgo"
            elif es_modelo_tasa:
                texto_boton = "📈 Calcular Tasa Descuento"
            else:
                texto_boton = "💰 Calcular Valor"
            
            if st.button(texto_boton, type="primary", use_container_width=True):
                with st.spinner("Calculando tasación usando modelos econométricos..."):
                    # Obtener el modelo seleccionado directamente
                    modelo_valor = st.session_state.modelo.obtener_modelo(modelo_seleccionado)
                    
                    if not modelo_valor:
                        st.error("❌ No se pudo cargar el modelo seleccionado")
                        return
                    
                    # Preparar datos según el tipo de modelo
                    if es_tasa_prima:
                        datos_inmueble = {
                            'superficie': superficie,
                            'antiguedad': antiguedad,
                            'dormitorios': dormitorios,
                            'banos': banos,
                            'planta': planta,
                            'ascensor': ascensor,
                            'rehabilitacion': rehabilitacion,
                            'calidad_alta': calidad_alta,
                            'estado_alto': estado_conservacion in ["Buena", "Muy buena", "Óptima"]
                        }
                    else:
                        datos_inmueble = {
                            'superficie': superficie,
                            'dormitorios': dormitorios,
                            'banos': banos,
                            'planta': planta,
                            'calefaccion': calefaccion,
                            'ascensor': ascensor,
                            'vivienda_nueva': vivienda_nueva,
                            'calidad_alta': calidad_alta,
                            'estado_alto': estado_conservacion_valor in ["Buena", "Muy buena", "Óptima"]
                        }
                    
                    # CALCULAR SÓLO LO QUE CORRESPONDA AL MODELO SELECCIONADO
                    resultados = {}
                    
                    if es_modelo_valor:
                        # Solo calcular valor para modelos de valor
                        valor_m2, contrib_valor = st.session_state.modelo.calcular_valor_m2(
                            datos_inmueble, modelo_valor, codigo_municipio
                        )
                        valor_total = valor_m2 * superficie
                        resultados.update({
                            'valor_m2': valor_m2,
                            'valor_total': valor_total,
                            'contrib_valor': contrib_valor
                        })
                    
                    elif es_modelo_tasa:
                        # Solo calcular tasa para modelo de tasa 
                        tasa_descuento, contrib_tasa = st.session_state.modelo.calcular_tasa_descuento(
                            datos_inmueble, codigo_municipio
                        )
                        resultados.update({
                            'tasa_descuento': tasa_descuento,
                            'contrib_tasa': contrib_tasa
                        })

                    elif es_modelo_prima:
                        # Solo calcular prima para modelo de prima 
                        prima_riesgo, contrib_prima = st.session_state.modelo.calcular_prima_riesgo(
                            datos_inmueble, codigo_municipio
                        )
                        resultados.update({
                            'prima_riesgo': prima_riesgo,
                            'contrib_prima': contrib_prima
                        })
                    
                    # Mostrar resultados
                    st.success("✅ Tasación calculada correctamente")
                    
                    # Métricas principales (solo lo que se calculó)
                    if es_modelo_prima:
                        col_res1, col_res2 = st.columns(2)
                        with col_res1:
                            st.metric("Prima de Riesgo", f"{resultados['prima_riesgo']:.2%}")
                        with col_res2:
                            st.metric("Tipo de Modelo", "Prima Riesgo")
                    
                    elif es_modelo_tasa:
                        col_res1, col_res2 = st.columns(2)
                        with col_res1:
                            st.metric("Tasa Descuento", f"{resultados['tasa_descuento']:.2%}")
                        with col_res2:
                            st.metric("Tipo de Modelo", "Tasa Descuento")
                    
                    else:
                        col_res1, col_res2, col_res3 = st.columns(3)
                        with col_res1:
                            st.metric("Valor por m²", f"€ {resultados['valor_m2']:,.0f}")
                        with col_res2:
                            st.metric("Valor Total", f"€ {resultados['valor_total']:,.0f}")
                        with col_res3:
                            st.metric("Tipo de Modelo", "Valor")
                    
                    # Información del modelo usado
                    st.info(f"**Modelo aplicado:** {modelo_valor['nombre_modelo']}")
                    
                    # Contribuciones detalladas (solo las relevantes)
                    with st.expander("📊 Análisis Detallado de Contribuciones", expanded=True):
                        if es_modelo_prima:
                            st.subheader("🛡️ Contribución a la Prima")
                            contrib_df_prima = pd.DataFrame({
                                'Variable': list(resultados['contrib_prima'].keys()),
                                'Impacto en Prima': [f"{v:+.1f}%" for v in resultados['contrib_prima'].values()],  
                                'Efecto': ['📈 Aumenta' if v > 0 else '📉 Reduce' for v in resultados['contrib_prima'].values()]
                            })
                            st.dataframe(contrib_df_prima, use_container_width=True, height=200, hide_index=True)
                        
                        elif es_modelo_tasa:
                            st.subheader("📈 Contribución a la Tasa")
                            contrib_df_tasa = pd.DataFrame({
                                'Variable': list(resultados['contrib_tasa'].keys()),
                                'Impacto en Tasa': [f"{v:+.1f}%" for v in resultados['contrib_tasa'].values()],
                                'Efecto': ['📈 Aumenta' if v > 0 else '📉 Reduce' for v in resultados['contrib_tasa'].values()]
                            })
                            st.dataframe(contrib_df_tasa, use_container_width=True, height=200, hide_index=True)
                        
                        else:
                            st.subheader("💰 Contribución al Valor por m²")
                            contrib_df_valor = pd.DataFrame({
                                'Variable': list(resultados['contrib_valor'].keys()),
                                'Impacto en Valor': [f"{v:+.1f}%" for v in resultados['contrib_valor'].values()],
                                'Efecto': ['📈 Aumenta' if v > 0 else '📉 Reduce' for v in resultados['contrib_valor'].values()]
                            })
                            st.dataframe(contrib_df_valor, use_container_width=True, height=200, hide_index=True)
                    
                    # Preparar resultado para descarga
                    resultado_descarga = {
                        'fecha_calculo': datetime.now().isoformat(),
                        'codigo_municipio': codigo_municipio,
                        'superficie': superficie,
                        'modelo_usado': modelo_valor['nombre_modelo'],
                    }
                    
                    # Agregar solo los resultados calculados
                    if es_modelo_valor:
                        resultado_descarga.update({
                            'valor_m2': resultados['valor_m2'],
                            'valor_total': resultados['valor_total'],
                            'contribuciones_valor': resultados['contrib_valor']
                        })
                    elif es_modelo_tasa:
                        resultado_descarga.update({
                            'tasa_descuento': resultados['tasa_descuento'],
                            'contribuciones_tasa': resultados['contrib_tasa']
                        })
                    elif es_modelo_prima:
                        resultado_descarga.update({
                            'prima_riesgo': resultados['prima_riesgo'],
                            'contribuciones_prima': resultados['contrib_prima']
                        })

                    st.download_button(
                        "📥 Descargar Informe JSON",
                        data=json.dumps(resultado_descarga, indent=2),
                        file_name=f"tasacion_{codigo_municipio}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
            else:
                st.info("ℹ️ Complete los datos y haga clic en el botón para obtener resultados")

def validar_fila_para_modelo(fila: pd.Series, modelo_clave: str) -> Tuple[bool, List[str]]:
    """Valida que una fila tenga las columnas requeridas para el modelo especificado"""
    errores = []
    
    # Columnas requeridas para todos los modelos
    columnas_requeridas_base = ['codigo_municipio', 'superficie', 'dormitorios', 'banos', 'planta']
    
    # Columnas específicas por tipo de modelo
    if es_modelo_tasa_o_prima(modelo_clave):
        # Modelos de tasa/prima requieren antiguedad
        columnas_requeridas = columnas_requeridas_base + ['antiguedad']
    else:
        # Modelos de valor requieren calefaccion, vivienda_nueva
        columnas_requeridas = columnas_requeridas_base + ['calefaccion', 'vivienda_nueva']
    
    # Verificar columnas requeridas
    for columna in columnas_requeridas:
        if columna not in fila.index:
            errores.append(f"Falta columna requerida: {columna}")
        elif pd.isna(fila[columna]):
            errores.append(f"Valor faltante en columna: {columna}")
    
    # Validar tipos de datos básicos
    if 'superficie' in fila and not pd.isna(fila['superficie']):
        try:
            float(fila['superficie'])
        except (ValueError, TypeError):
            errores.append("Superficie debe ser numérica")
    
    if 'codigo_municipio' in fila and not pd.isna(fila['codigo_municipio']):
        try:
            str(fila['codigo_municipio'])
        except (ValueError, TypeError):
            errores.append("Código municipio debe ser texto o número")
    
    return len(errores) == 0, errores

def procesar_fila_multiple(fila: pd.Series, modelo_tasacion, modelos_json: Dict) -> Tuple[bool, Dict, str]:
    """Procesa una fila individual del Excel y retorna resultado o error"""
    try:
        # Validar que la fila tenga modelo
        if 'modelo' not in fila or pd.isna(fila['modelo']):
            return False, {}, "Falta especificar el modelo"
        
        modelo_clave = str(fila['modelo'])
        
        # Validar fila para el modelo específico
        es_valida, errores_validacion = validar_fila_para_modelo(fila, modelo_clave)
        if not es_valida:
            return False, {}, f"Errores validación: {', '.join(errores_validacion)}"
        
        # Obtener modelo
        modelo_obj = modelos_json.get(modelo_clave)
        if not modelo_obj:
            return False, {}, f"Modelo '{modelo_clave}' no encontrado"
        
        # Preparar datos según tipo de modelo
        codigo_municipio = str(fila['codigo_municipio'])
        superficie = float(fila['superficie'])
        
        if es_modelo_tasa_o_prima(modelo_clave):
            # Modelo de tasa o prima
            datos = {
                'superficie': superficie,
                'antiguedad': float(fila.get('antiguedad', 0)),
                'dormitorios': int(fila.get('dormitorios', 0)),
                'banos': int(fila.get('banos', 0)),
                'planta': int(fila.get('planta', 0)),
                'ascensor': bool(fila.get('ascensor', False)),
                'rehabilitacion': bool(fila.get('rehabilitacion', False)),
                'calidad_alta': bool(fila.get('calidad_alta', False)),
                'estado_alto': fila.get('estado_conservacion', '') in ["Buena", "Muy buena", "Óptima"],
                'vivienda_nueva': bool(fila.get('vivienda_nueva', False))
            }
            
            if modelo_clave == 'testigos_tasa':
                resultado, contribuciones = modelo_tasacion.calcular_tasa_descuento(datos, codigo_municipio)
                return True, {
                    'tipo': 'tasa',
                    'valor': resultado,
                    'contribuciones': contribuciones,
                    'modelo': modelo_obj['nombre_modelo'],
                    'codigo_municipio': codigo_municipio,
                    'superficie': superficie
                }, ""
            else: # testigos_prima
                resultado, contribuciones = modelo_tasacion.calcular_prima_riesgo(datos, codigo_municipio)
                return True, {
                    'tipo': 'prima',
                    'valor': resultado,
                    'contribuciones': contribuciones,
                    'modelo': modelo_obj['nombre_modelo'],
                    'codigo_municipio': codigo_municipio,
                    'superficie': superficie
                }, ""
        else:
            # Modelo de valor (ya estaba correcto)
            datos = {
                'superficie': superficie,
                'dormitorios': int(fila.get('dormitorios', 0)),
                'banos': int(fila.get('banos', 0)),
                'planta': int(fila.get('planta', 0)),
                'calefaccion': bool(fila.get('calefaccion', False)),
                'ascensor': bool(fila.get('ascensor', False)),
                'vivienda_nueva': bool(fila.get('vivienda_nueva', False)),
                'calidad_alta': bool(fila.get('calidad_alta', False)),
                'estado_alto': fila.get('estado_conservacion', '') in ["Buena", "Muy buena", "Óptima"]
            }
            
            valor_m2, contribuciones = modelo_tasacion.calcular_valor_m2(datos, modelo_obj, codigo_municipio)
            valor_total = valor_m2 * superficie
            
            return True, {
                'tipo': 'valor',
                'valor_m2': valor_m2,
                'valor_total': valor_total,
                'contribuciones': contribuciones,
                'modelo': modelo_obj['nombre_modelo'],
                'codigo_municipio': codigo_municipio,
                'superficie': superficie
            }, ""
            
    except Exception as e:
        return False, {}, f"Error en procesamiento: {str(e)}"

def crear_plantilla_fallback():
    # Datos de ejemplo mínimos
    sample_data = {
        'modelo': ['testigos_menos_10000', 'testigos_tasa'],
        'codigo_municipio': ['2005', '2006'],
        'superficie': [85.5, 120.0],
        'dormitorios': [3, 4],
        'banos': [2, 3],
        'planta': [2, 3],
        'calefaccion': [True, ''],
        'ascensor': [True, False],
        'vivienda_nueva': [False, ''],
        'antiguedad': ['', 15],
        'rehabilitacion': ['', True],
        'calidad_alta': [False, False],
        'estado_conservacion': ['Buena', 'Buena']
    }
    
    df_fallback = pd.DataFrame(sample_data)
    
    # Crear Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_fallback.to_excel(writer, index=False, sheet_name='Plantilla')
    
    excel_data = output.getvalue()
    
    st.download_button(
        "📥 Descargar plantilla básica",
        data=excel_data,
        file_name="plantilla_tasacion_basica.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    
def pagina_tasacion_multiple():
    """Pestaña para tasación múltiple con validación avanzada por modelo"""
    st.header("📁 Tasación Múltiple por Lotes")
    
    with st.expander("ℹ️ Información sobre tasación múltiple", expanded=True):
        st.markdown("""
        **Características de la tasación por lotes:**
        - Procesamiento simultáneo de múltiples inmuebles usando modelos econométricos
        - Validación automática por tipo de modelo especificado en cada fila
        - Detección y reporte de errores por fila con mensajes específicos
        - Generación de informe consolidado con análisis de contribuciones
        - Límite: 500 registros por lote
        
        **Columnas comunes requeridas en el Excel:**
        - `modelo`: Tipo de modelo (testigos_menos_10000, testigos_tasa, testigos_prima, etc.)
        - `codigo_municipio`: Código del municipio (ej: 2005, 2006, etc.)
        - `superficie`: Superficie en m² (número)
        
        **Columnas requeridas según tipo de modelo:**
        
        **Para modelos de VALOR (testigos_menos_10000, testigos_10000_50000, etc.):**
        - `dormitorios`, `banos`, `planta`, `calefaccion`, `ascensor`, `vivienda_nueva`, `calidad_alta`, `estado_conservacion`
        
        **Para modelos de TASA/PRIMA (testigos_tasa, testigos_prima):**
        - `dormitorios`, `banos`, `planta`, `ascensor`, `antiguedad`, `rehabilitacion`, `calidad_alta`, `estado_conservacion`
        """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "📤 Subir archivo Excel para tasación múltiple", 
            type=['xlsx', 'xls'],
            help="El archivo debe contener las columnas requeridas según el tipo de modelo especificado en cada fila"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                
                # Validar que existe columna modelo
                if 'modelo' not in df.columns:
                    st.error("❌ El archivo debe contener la columna 'modelo' que especifique el tipo de modelo para cada fila")
                    return
                
                print(f"✅ Archivo cargado correctamente - {len(df)} registros detectados")
                
                # Estadísticas
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                with col_stats1:
                    st.metric("Registros", len(df))
                with col_stats2:
                    modelos_unicos = df['modelo'].unique() if 'modelo' in df.columns else []
                    st.metric("Tipos de modelo", len(modelos_unicos))
                with col_stats3:
                    st.metric("Municipios", df['codigo_municipio'].nunique() if 'codigo_municipio' in df.columns else 0)
                
                # Vista previa
                st.subheader("👁️ Vista previa de datos")
                st.dataframe(df.head(10), use_container_width=True, height=300)
                
                # Procesar lote
                if st.button("🚀 Procesar Lote Completo", type="primary", use_container_width=True):
                    with st.spinner(f"Procesando {len(df)} registros con modelos econométricos..."):
                        resultados_exitosos = []
                        resultados_detallados = []
                        errores_detallados = []
                        
                        for idx, fila in df.iterrows():
                            numero_fila = idx + 2  # +2 porque Excel empieza en 1 y tiene headers
                            
                            # Procesar fila individual
                            es_exitosa, resultado, mensaje_error = procesar_fila_multiple(
                                fila, st.session_state.modelo, st.session_state.modelos_json
                            )
                            
                            if es_exitosa:
                                resultados_exitosos.append(resultado)
                                resultados_detallados.append({
                                    'fila': numero_fila,
                                    'estado': '✅ ÉXITO',
                                    'modelo': resultado['modelo'],
                                    'codigo_municipio': resultado['codigo_municipio'],
                                    'superficie': resultado['superficie'],
                                    'resultado': format_resultado_multiple(resultado),
                                    'detalles': obtener_detalles_contribuciones(resultado)
                                })
                            else:
                                errores_detallados.append({
                                    'fila': numero_fila,
                                    'estado': '❌ ERROR',
                                    'modelo': str(fila.get('modelo', 'No especificado')),
                                    'codigo_municipio': str(fila.get('codigo_municipio', 'N/A')),
                                    'error': mensaje_error
                                })
                        
                        # MOSTRAR RESULTADOS DEL PROCESAMIENTO
                        st.subheader("📊 Resultados del Procesamiento")
                        
                        col_res1, col_res2, col_res3 = st.columns(3)
                        with col_res1:
                            st.metric("Procesadas correctamente", len(resultados_exitosos))
                        with col_res2:
                            st.metric("Errores", len(errores_detallados))
                        with col_res3:
                            tasa_exito = (len(resultados_exitosos) / len(df)) * 100 if len(df) > 0 else 0
                            st.metric("Tasa de éxito", f"{tasa_exito:.1f}%")
                        
                        # Pestañas para resultados detallados
                        tab_resultados, tab_errores, tab_consolidado = st.tabs([
                            f"✅ Resultados ({len(resultados_exitosos)})",
                            f"❌ Errores ({len(errores_detallados)})", 
                            "📋 Consolidado"
                        ])
                        
                        with tab_resultados:
                            if resultados_detallados:
                                df_resultados = pd.DataFrame(resultados_detallados)
                                st.dataframe(df_resultados, use_container_width=True)
                            else:
                                st.info("No hay resultados exitosos para mostrar")
                        
                        with tab_errores:
                            if errores_detallados:
                                df_errores = pd.DataFrame(errores_detallados)
                                st.dataframe(df_errores, use_container_width=True)
                                
                                # Mostrar análisis de errores
                                st.subheader("📈 Análisis de Errores")
                                errores_por_tipo = df_errores['error'].value_counts()
                                st.bar_chart(errores_por_tipo)
                            else:
                                st.success("🎉 No se encontraron errores en el procesamiento")
                        
                        with tab_consolidado:
                            st.markdown("""
                                **📊 Estructura del Excel generado:**
                                
                                - **Columnas básicas**: Modelo, código municipio, superficie
                                - **Resultados**: Valor m², valor total, tasa descuento o prima riesgo (según modelo)
                                - **Factores influyentes**: Los 2 factores que más impactan en el resultado con su porcentaje
                                
                                *Cada fila representa una tasación procesada correctamente*
                                """)
                            if resultados_exitosos:
                                # Crear DataFrame consolidado para descarga MEJORADO
                                datos_consolidados = []
                                for resultado in resultados_exitosos:
                                    fila_consolidada = {
                                        'modelo': resultado['modelo'],
                                        'codigo_municipio': resultado['codigo_municipio'],
                                        'superficie': resultado['superficie']
                                    }
                                    
                                    # Resultados específicos por tipo
                                    if resultado['tipo'] == 'valor':
                                        fila_consolidada.update({
                                            'valor_m2': round(resultado['valor_m2'], 2),
                                            'valor_total': round(resultado['valor_total'], 2),
                                            'tasa_descuento': '',
                                            'prima_riesgo': ''
                                        })
                                    elif resultado['tipo'] == 'tasa':
                                        fila_consolidada.update({
                                            'valor_m2': '',
                                            'valor_total': '',
                                            'tasa_descuento': round(resultado['valor'], 4),
                                            'prima_riesgo': ''
                                        })
                                    elif resultado['tipo'] == 'prima':
                                        fila_consolidada.update({
                                            'valor_m2': '',
                                            'valor_total': '',
                                            'tasa_descuento': '',
                                            'prima_riesgo': round(resultado['valor'], 4)
                                        })
                                    
                                    # Agregar factores más influyentes como columnas separadas
                                    factores = obtener_factores_influyentes_detallados(resultado['contribuciones'])
                                    fila_consolidada.update(factores)
                                    
                                    datos_consolidados.append(fila_consolidada)
                                
                                df_consolidado = pd.DataFrame(datos_consolidados)
                                
                                # Reordenar columnas para mejor presentación
                                column_order = ['modelo', 'codigo_municipio', 'superficie', 'valor_m2', 'valor_total', 
                                            'tasa_descuento', 'prima_riesgo', 'factor_1', 'impacto_1', 'factor_2', 'impacto_2']
                                # Solo incluir columnas que existan en el DataFrame
                                column_order = [col for col in column_order if col in df_consolidado.columns]
                                df_consolidado = df_consolidado[column_order]
                                
                                st.dataframe(df_consolidado, use_container_width=True)
                                
                                # Descargar como Excel
                                output = io.BytesIO()
                                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                    df_consolidado.to_excel(writer, index=False, sheet_name='Resultados_Tasacion')
                                
                                excel_data = output.getvalue()
                                st.download_button(
                                    "📊 Descargar Excel con Resultados",
                                    data=excel_data,
                                    file_name=f"resultados_tasacion_consolidado_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    use_container_width=True
                                )
                            else:
                                st.info("No hay datos consolidados para mostrar")

            except Exception as e:
                st.error(f"❌ Error procesando el archivo: {str(e)}")
    
    with col2:
        st.subheader("📋 Plantilla de Ejemplo")
        
        # Cargar plantilla existente desde assets
        plantilla_path = "assets/plantilla_tasacion_basica.xlsx"
        
        # Buscar la plantilla en diferentes ubicaciones posibles
        posibles_rutas = [
            plantilla_path,
            f"/app/{plantilla_path}",
            f"/app/assets/plantilla_tasacion_basica.xlsx",
            "./assets/plantilla_tasacion_basica.xlsx",
            "plantilla_tasacion_basica.xlsx"
        ]
        
        plantilla_encontrada = None
        for ruta in posibles_rutas:
            if os.path.exists(ruta):
                plantilla_encontrada = ruta
                break
        
        if plantilla_encontrada:
            try:
                # Leer el archivo Excel existente
                with open(plantilla_encontrada, "rb") as file:
                    excel_data = file.read()
                
                # Botón para descargar plantilla
                st.download_button(
                    "📥 Descargar plantilla básica",
                    data=excel_data,
                    file_name="plantilla_tasacion_basica.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Descargue la plantilla básica con el formato requerido",
                    use_container_width=True
                )
                
                # Mostrar vista previa de la plantilla
                with st.expander("👀 Ver estructura de la plantilla"):
                    try:
                        df_plantilla = pd.read_excel(plantilla_encontrada)
                        st.dataframe(df_plantilla.head(5), use_container_width=True)
                        st.caption(f"Plantilla con {len(df_plantilla)} filas de ejemplo y {len(df_plantilla.columns)} columnas")
                    except Exception as e:
                        st.warning(f"No se pudo mostrar vista previa: {e}")
                        
            except Exception as e:
                st.error(f"❌ Error cargando plantilla: {e}")
                # Fallback: crear plantilla básica
                st.warning("Usando plantilla básica de respaldo...")
                crear_plantilla_fallback()
        else:
            st.error("❌ No se encontró la plantilla en assets/")
            st.info("Creando plantilla de respaldo...")
            crear_plantilla_fallback()

        st.markdown("---")
        st.markdown("### 💡 Consejos para el formato")
        st.write("• **Columna 'modelo'**: Debe coincidir exactamente con los nombres de modelo")
        st.write("• **Validación automática**: Cada fila se valida según su tipo de modelo")
        st.write("• **Formato Excel**: Use el formato .xlsx para mejor compatibilidad")
        st.write("• **Codificación**: UTF-8 para caracteres especiales")

def obtener_factores_influyentes_detallados(contribuciones: Dict) -> Dict:
    """Obtiene los factores más influyentes como columnas separadas"""
    factores_dict = {}
    
    if contribuciones:
        # Excluir el valor base y ordenar por valor absoluto
        contribs_filtradas = {k: v for k, v in contribuciones.items() 
                             if 'base' not in k.lower() and 'municipio' not in k.lower()}
        
        if contribs_filtradas:
            # Ordenar por impacto absoluto y tomar top 2
            top_factores = sorted(contribs_filtradas.items(), 
                                key=lambda x: abs(x[1]), reverse=True)[:2]
            
            # Asignar a columnas separadas
            for i, (factor, impacto) in enumerate(top_factores, 1):
                # Limpiar nombre del factor
                nombre_limpio = factor.replace('contrib_', '').replace('_', ' ').title()
                factores_dict[f'factor_{i}'] = nombre_limpio
                factores_dict[f'impacto_{i}'] = f"{impacto:+.1f}%"
        
        # Rellenar con vacíos si hay menos de 2 factores
        for i in range(len(top_factores) + 1, 3):
            factores_dict[f'factor_{i}'] = ''
            factores_dict[f'impacto_{i}'] = ''
    
    return factores_dict

# Funciones auxiliares para el procesamiento múltiple
def format_resultado_multiple(resultado: Dict) -> str:
    """Formatea el resultado para mostrar en tabla"""
    if resultado['tipo'] == 'valor':
        return f"€{resultado['valor_m2']:,.0f}/m² (Total: €{resultado['valor_total']:,.0f})"
    elif resultado['tipo'] == 'tasa':
        return f"{resultado['valor']:.2%}"
    elif resultado['tipo'] == 'prima':
        return f"{resultado['valor']:.2%}"
    return "N/A"

def obtener_detalles_contribuciones(resultado: Dict) -> str:
    """Obtiene los detalles de contribuciones para mostrar"""
    if 'contribuciones' in resultado:
        contribs = resultado['contribuciones']
        top_3 = sorted(contribs.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
        return ", ".join([f"{k}: {v:+.1f}%" for k, v in top_3])
    return "Sin detalles"

def obtener_factores_influyentes(contribuciones: Dict) -> str:
    """Obtiene los factores más influyentes para el resultado consolidado"""
    if contribuciones:
        # Excluir el valor base y ordenar por valor absoluto
        contribs_filtradas = {k: v for k, v in contribuciones.items() if 'base' not in k.lower()}
        if contribs_filtradas:
            top_2 = sorted(contribs_filtradas.items(), key=lambda x: abs(x[1]), reverse=True)[:2]
            return " + ".join([k for k, v in top_2])
    return "Municipio"

def pagina_documentacion():
    """Pestaña de documentación técnica mejorada usando configuración YAML"""
    if not st.session_state.config_sistema:
        st.error("No se pudo cargar la configuración del sistema")
        return
        
    config = st.session_state.config_sistema
    doc_config = config.get('documentacion', {})
    
    st.header("📚 Documentación Técnica - Modelos ECO 805")
    
    # Introducción desde YAML
    introduccion = doc_config.get('introduccion', 'Sistema de valoración basado en análisis de regresión múltiple.')
    st.markdown(f"""
    <div style='background: #f0f2f6; padding: 2rem; border-radius: 10px; border-left: 4px solid #1f77b4;'>
        <h4 style='color: #1f77b4; margin-top: 0;'>Modelos Econométricos para Tasación Inmobiliaria</h4>
        <p style='margin-bottom: 0;'>{introduccion}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metodología desde YAML
    st.subheader("🔬 Metodología Científica")
    
    col_metodo1, col_metodo2 = st.columns(2)
    
    with col_metodo1:
        st.markdown("**Base de Datos:**")
        for item in doc_config.get('metodologia', {}).get('base_datos', []):
            st.write(f"- {item}")
        
        st.markdown("**Procesamiento:**")
        for item in doc_config.get('metodologia', {}).get('procesamiento', []):
            st.write(f"- {item}")
    
    with col_metodo2:
        st.markdown("**Validación Estadística:**")
        for item in doc_config.get('metodologia', {}).get('validacion', []):
            st.write(f"- {item}")
        
        st.markdown("**Software Utilizado:**")
        for item in doc_config.get('metodologia', {}).get('software', []):
            st.write(f"- {item}")
    
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
    
    # Segmentación por población - CORRECCIÓN: Leer R² desde modelos_disponibles
    st.subheader("🏙️ Segmentación por Tamaño Municipal")
    
    col_seg1, col_seg2, col_seg3, col_seg4 = st.columns(4)
    
    # Obtener modelos disponibles desde la configuración
    modelos_config = config.get('modelos_disponibles', [])
    
    # Buscar los R² específicos para cada modelo de valor
    r2_menos_10000 = next((modelo.get('r2', '76.32%') for modelo in modelos_config if modelo.get('clave') == 'testigos_menos_10000'), '76.32%')
    r2_10000_50000 = next((modelo.get('r2', '73.89%') for modelo in modelos_config if modelo.get('clave') == 'testigos_10000_50000'), '73.89%')
    r2_50000_200000 = next((modelo.get('r2', '67.18%') for modelo in modelos_config if modelo.get('clave') == 'testigos_50000_200000'), '67.18%')
    r2_mas_200000 = next((modelo.get('r2', '61.95%') for modelo in modelos_config if modelo.get('clave') == 'testigos_mas_200000'), '61.95%')

    with col_seg1:
        st.metric("< 10,000 hab", f"R² = {r2_menos_10000}", "Mayor poder explicativo")
    with col_seg2:
        st.metric("10,000-50,000", f"R² = {r2_10000_50000}", "Alta significatividad")
    with col_seg3:
        st.metric("50,000-200,000", f"R² = {r2_50000_200000}", "Modelo robusto")
    with col_seg4:
        st.metric("> 200,000 hab", f"R² = {r2_mas_200000}", "Máxima complejidad")

    st.markdown("""
    **Hallazgos clave de los modelos econométricos:**
    - **R² decreciente con tamaño municipal**: Mayor poder explicativo en municipios pequeños (76.32%) vs grandes (61.95%)
    - **Efecto superficie (SU)**: Negativo en municipios <200k hab, positivo en grandes ciudades
    - **Dormitorios (ND)**: Efecto negativo consistente en todos los modelos
    - **Variables positivas**: Baños (NB), ascensor (DAS), calidad alta (CC_Alta) y calefacción (DCA) siempre positivas
    - **Planta (PLbis)**: Efecto positivo que se intensifica con el tamaño municipal
    """)

def mostrar_footer():
    """Footer usando configuración YAML"""
    if not st.session_state.config_sistema:
        sistema_info = {'nombre': 'AESVAL - CTIC', 'version': 'v2.0'}
    else:
        sistema_info = st.session_state.config_sistema.get('sistema', {})
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            f"""
            <div style='text-align: center; color: #666; padding:0;'>
                <p style='margin-bottom: 0; font-size: 0.9rem;'>
                    © {sistema_info.get('año', current_year)} <strong>{sistema_info.get('desarrollador', 'AESVAL - CTIC')}</strong> | 
                    {sistema_info.get('nombre', 'Sistema de Tasación Automático')} {sistema_info.get('version', 'v2.0')}
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