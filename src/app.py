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
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

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
                if clave in self.modelos:  # Solo incluir modelos que estén cargados
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
        
        return max(0, valor_base), contribuciones
    
    def calcular_tasa_descuento(self, datos: Dict) -> Tuple[float, Dict]:
        """Calcula la tasa de descuento usando el modelo correspondiente"""
        
        # Obtener el modelo de tasa desde los JSON cargados
        modelo_tasa = self.modelos.get('testigos_tasa')
        if not modelo_tasa:
            st.error("❌ No se encontró el modelo de tasa en los archivos JSON")
            return 0.05, {}
        
        # Usar los coeficientes reales del modelo JSON
        coef_variables = modelo_tasa['coeficientes_variables']
        _cons = modelo_tasa['_cons']
        
        contribuciones = {}
        tasa_base = _cons
        contribuciones['tasa_base'] = tasa_base
        
        # Aplicar coeficientes según variables disponibles usando los coeficientes reales
        if 'SU' in coef_variables and coef_variables['SU'] is not None and datos.get('superficie'):
            contrib = coef_variables['SU'] * datos['superficie']
            tasa_base += contrib
            contribuciones['superficie'] = contrib
        
        # Para modelos de tasa/prima usar 'antig' (variable continua)
        if 'antig' in coef_variables and coef_variables['antig'] is not None and datos.get('antiguedad'):
            contrib = coef_variables['antig'] * datos['antiguedad']
            tasa_base += contrib
            contribuciones['antiguedad'] = contrib
        
        # Para modelos de valor usar 'Dnueva' (variable dicotómica)
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
        return max(0.01, min(0.15, tasa_base)), contribuciones

    def calcular_prima_riesgo(self, datos: Dict) -> Tuple[float, Dict]:
        """Calcula la prima de riesgo usando el modelo correspondiente"""
        
        # Obtener el modelo de prima desde los JSON cargados
        modelo_prima = self.modelos.get('testigos_prima')
        if not modelo_prima:
            st.error("❌ No se encontró el modelo de prima en los archivos JSON")
            return 0.02, {}
        
        # Usar los coeficientes reales del modelo JSON
        coef_variables = modelo_prima['coeficientes_variables']
        _cons = modelo_prima['_cons']
        
        contribuciones = {}
        prima_base = _cons
        contribuciones['prima_base'] = prima_base
        
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
        return max(0.005, min(0.10, prima_base)), contribuciones

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
        **Versión:** {sistema.get('version', '2.0')}
        **Actualización:** {sistema.get('actualizacion', '2025-01-10')}
        **Modelo:** {sistema.get('modelo', 'ECO 805 - Análisis Econométrico')}
        **Base de datos:** {sistema.get('base_datos', '205,000+ testigos')}
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("R² Promedio", metricas.get('r2_promedio', '82%'))
        with col2:
            st.metric("Precisión", metricas.get('precision', '97.2%'))
        
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
            <p>Sistema de Tasación Inteligente</p>
        </div>
        """, unsafe_allow_html=True)

def obtener_codigos_disponibles():
    """Obtiene todos los códigos de municipio disponibles en los modelos"""
    modelos = st.session_state.modelos_json
    codigos = set()
    
    for modelo in modelos.values():
        if 'coeficientes_municipios' in modelo:
            codigos.update(modelo['coeficientes_municipios'].keys())
    
    return sorted(list(codigos))

def obtener_poblacion_por_codigo(codigo_municipio: str) -> int:
    """Obtiene población aproximada basada en el código del municipio"""
    # Mapeo simplificado de códigos a poblaciones (ejemplo)
    poblaciones_por_codigo = {
        # Códigos para municipios grandes (>200,000 hab)
        "33021": 268000,  # Gijón
        "33044": 215000,  # Oviedo
        "33004": 76000,   # Avilés
        # Códigos para municipios medianos (50,000-200,000)
        "33036": 38000,   # Mieres
        "33032": 39000,   # Langreo
        "33066": 52000,   # Siero
        # Códigos para municipios pequeños (<50,000)
        "33016": 22000,   # Castrillón
        "33020": 16000,   # Corvera
        "33015": 10500,   # Carreño
        "33025": 10500,   # Gozón
        "33076": 14500,   # Villaviciosa
        "33063": 1300,    # Sariego
        "33006": 1700,    # Bimenes
        "33042": 5200,    # Nava
        "33008": 800,     # Cabranes
        "33049": 7200     # Piloña
    }
    
    return poblaciones_por_codigo.get(codigo_municipio, 50000)

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
                # Selección directa del modelo
                modelos_disponibles = st.session_state.modelo.obtener_modelos_disponibles()
                if not modelos_disponibles:
                    st.error("❌ No se cargaron modelos. Verifique los archivos JSON en config/")
                    st.stop()
                
                # CORRECCIÓN: Usar la lista de tuplas correctamente
                modelo_seleccionado = st.selectbox(
                    "Seleccione el modelo",
                    options=[clave for clave, nombre in modelos_disponibles],
                    format_func=lambda x: next((nombre for clave, nombre in modelos_disponibles if clave == x), x),
                    help="Elija el modelo econométrico según el tamaño del municipio"
                )
                
                # Determinar tipo de modelo
                es_tasa_prima = es_modelo_tasa_o_prima(modelo_seleccionado)
                es_modelo_prima = modelo_seleccionado == 'testigos_prima'
                es_modelo_tasa = modelo_seleccionado == 'testigos_tasa'
                
                # Código del municipio (siempre visible)
                modelo_obj = st.session_state.modelo.obtener_modelo(modelo_seleccionado)
                codigos_disponibles = list(modelo_obj['coeficientes_municipios'].keys()) if modelo_obj and 'coeficientes_municipios' in modelo_obj else []
                
                if not codigos_disponibles:
                    st.error("❌ El modelo seleccionado no tiene códigos de municipio disponibles")
                    st.stop()
                
                codigo_municipio = st.selectbox(
                    "Código de Municipio",
                    options=codigos_disponibles,
                    help="Seleccione el código del municipio"
                )
                
                # SUPERFICIE - siempre visible pero con diferente comportamiento
                superficie = st.number_input(
                    "Superficie construida (m²)", 
                    min_value=20.0, 
                    max_value=1000.0,
                    value=80.0,
                    step=0.5,
                    help="Superficie total construida en metros cuadrados"
                )
                
                # INICIALIZAR AMBAS VARIABLES FUERA DE LOS BLOQUES CONDICIONALES
                estado_conservacion = "Buena"  # Valor por defecto
                estado_conservacion_valor = "Buena"  # Valor por defecto
                
                # Campos para modelos de VALOR (ocultos para Tasa/Prima)
                if not es_tasa_prima:
                    # Dnueva: Vivienda nueva (<5 años)
                    vivienda_nueva = st.checkbox(
                        "Vivienda nueva (<5 años)", 
                        value=False, 
                        help="Menos de 5 años de antigüedad (variable Dnueva)"
                    )
                    
                    # DCA: Calefacción
                    calefaccion = st.checkbox(
                        "Calefacción", 
                        value=True, 
                        help="¿Tiene sistema de calefacción? (variable DCA)"
                    )
                
                # Campos para modelos de TASA/PRIMA (ocultos para Valor)
                if es_tasa_prima:
                    # antig: Antigüedad (variable continua para tasa/prima)
                    antiguedad = st.number_input(
                        "Antigüedad (años)", 
                        min_value=0, 
                        max_value=200,
                        value=15,
                        help="Años desde la construcción del inmueble (variable antig)"
                    )
                    
                    # rehab: Rehabilitación
                    rehabilitacion = st.checkbox(
                        "Rehabilitación del edificio", 
                        value=False, 
                        help="¿El edificio ha sido rehabilitado? (variable rehab)"
                    )
                    
                    # EC_Alto: Estado de conservación alto
                    estado_conservacion = st.select_slider(
                        "Estado de conservación",
                        options=["Muy deficiente", "Deficiente", "Regular", "Buena", "Muy buena", "Óptima"],
                        value="Buena",
                        help="Estado general de conservación del inmueble (variable EC_Alto)"
                    )
            
            with col1_2:
                # CAMPOS COMUNES A TODOS LOS MODELOS
                
                # ND: Número de dormitorios
                dormitorios = st.number_input(
                    "Número de dormitorios",
                    min_value=1,
                    max_value=10,
                    value=3,
                    help="Número total de dormitorios (variable ND)"
                )
                
                # NB: Número de baños
                banos = st.number_input(
                    "Número de baños",
                    min_value=1,
                    max_value=6,
                    value=2,
                    help="Número total de baños (variable NB)"
                )
                
                # PLbis: Planta
                planta = st.number_input(
                    "Planta",
                    min_value=0,
                    max_value=20,
                    value=2,
                    help="Planta en la que se ubica el inmueble (variable PLbis)"
                )
                
                # DAS: Ascensor
                ascensor = st.checkbox(
                    "Ascensor", 
                    value=True, 
                    help="¿El edificio tiene ascensor? (variable DAS)"
                )
                
                # CC_Alta: Calidad constructiva alta
                calidad_alta = st.checkbox(
                    "Calidad constructiva alta", 
                    value=False, 
                    help="Calidad de materiales y acabados alta (variable CC_Alta)"
                )
                
                # Campos específicos para modelos de VALOR
                if not es_tasa_prima:
                    # Estado de conservación para modelos de valor
                    estado_conservacion_valor = st.select_slider(
                        "Estado de conservación",
                        options=["Muy deficiente", "Deficiente", "Regular", "Buena", "Muy buena", "Óptima"],
                        value="Buena",
                        help="Estado general de conservación del inmueble"
                    )
    
    with col2:
        with st.container():
            st.subheader("🎯 Calcular Tasación")
            
            # Mostrar información del modelo seleccionado
            if es_tasa_prima:
                if es_modelo_prima:
                    st.info("🛡️ **Modelo de Prima de Riesgo activado**")
                    st.write("Variables: SU, antig, NB, ND, CC_Alta, EC_Alto, rehab, DAS, PLbis")
                else:
                    st.info("📈 **Modelo de Tasa Descuento activado**")
                    st.write("Variables: SU, antig, NB, ND, CC_Alta, EC_Alto, rehab, DAS, PLbis")
            else:
                st.info("💰 **Modelo de Valor activado**")
                st.write("Variables: Dnueva, SU, DCA, ND, NB, CC_Alta, DAS, PLbis")
            
            if st.button("📈 Calcular Valor y Tasa", type="primary", use_container_width=True):
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
                            'antiguedad': antiguedad,  # Variable continua para tasa/prima
                            'dormitorios': dormitorios,
                            'banos': banos,
                            'planta': planta,
                            'ascensor': ascensor,
                            'rehabilitacion': rehabilitacion,  # Solo para tasa/prima
                            'calidad_alta': calidad_alta,
                            # CONDICIÓN ACTUALIZADA: "Alta", "Buena", "Muy buena", "Óptima" = True
                            'estado_alto': estado_conservacion in ["Alta", "Buena", "Muy buena", "Óptima"]
                        }
                    else:
                        datos_inmueble = {
                            'superficie': superficie,
                            'dormitorios': dormitorios,
                            'banos': banos,
                            'planta': planta,
                            'calefaccion': calefaccion,  # DCA - solo para valor
                            'ascensor': ascensor,
                            'vivienda_nueva': vivienda_nueva,  # Dnueva - solo para valor
                            'calidad_alta': calidad_alta,
                            # CONDICIÓN ACTUALIZADA: "Alta", "Buena", "Muy buena", "Óptima" = True
                            'estado_alto': estado_conservacion_valor in ["Alta", "Buena", "Muy buena", "Óptima"]
                        }
                    
                    # Calcular valor por m² (solo para modelos de valor)
                    if not es_tasa_prima:
                        valor_m2, contrib_valor = st.session_state.modelo.calcular_valor_m2(
                            datos_inmueble, modelo_valor, codigo_municipio
                        )
                        valor_total = valor_m2 * superficie
                    else:
                        valor_m2 = 0
                        valor_total = 0
                        contrib_valor = {}
                    
                    # Calcular tasa de descuento y prima de riesgo
                    tasa_descuento, contrib_tasa = st.session_state.modelo.calcular_tasa_descuento(datos_inmueble)
                    prima_riesgo, contrib_prima = st.session_state.modelo.calcular_prima_riesgo(datos_inmueble)

                    # Mostrar resultados
                    st.success("✅ Tasación calculada correctamente")
                    
                    # Métricas principales (adaptadas al tipo de modelo)
                    if es_modelo_prima:
                        # Mostrar resultados para modelo de PRIMA
                        col_res1, col_res2, col_res3 = st.columns(3)
                        with col_res1:
                            st.metric("Prima de Riesgo", f"{prima_riesgo:.2%}")
                        with col_res2:
                            st.metric("Tasa Descuento", f"{tasa_descuento:.2%}")
                        with col_res3:
                            st.metric("Tipo de Modelo", "Prima Riesgo")
                    
                    elif es_modelo_tasa:
                        # Mostrar resultados para modelo de TASA
                        col_res1, col_res2, col_res3 = st.columns(3)
                        with col_res1:
                            st.metric("Tasa Descuento", f"{tasa_descuento:.2%}")
                        with col_res2:
                            st.metric("Prima de Riesgo", f"{prima_riesgo:.2%}")
                        with col_res3:
                            st.metric("Tipo de Modelo", "Tasa Descuento")
                    
                    else:
                        # Mostrar resultados para modelos de VALOR
                        col_res1, col_res2, col_res3 = st.columns(3)
                        with col_res1:
                            st.metric("Valor por m²", f"€ {valor_m2:,.0f}")
                        with col_res2:
                            st.metric("Valor Total", f"€ {valor_total:,.0f}")
                        with col_res3:
                            st.metric("Tasa Descuento", f"{tasa_descuento:.2%}")

                    # Información del modelo usado
                    st.info(f"**Modelo aplicado:** {modelo_valor['nombre_modelo']}")
                    
                    # Contribuciones detalladas
                    with st.expander("📊 Análisis Detallado de Contribuciones", expanded=True):
                        if es_modelo_prima:
                            # Para modelo de PRIMA: mostrar contribuciones de prima y tasa
                            col_contrib1, col_contrib2 = st.columns(2)
                            
                            with col_contrib1:
                                st.subheader("🛡️ Contribución a la Prima")
                                contrib_df_prima = pd.DataFrame({
                                    'Variable': list(contrib_prima.keys()),
                                    'Contribución (%)': [f"{v:.4f}" for v in contrib_prima.values()]
                                })
                                st.dataframe(contrib_df_prima, width=True)
                            
                            with col_contrib2:
                                st.subheader("📈 Contribución a la Tasa")
                                contrib_df_tasa = pd.DataFrame({
                                    'Variable': list(contrib_tasa.keys()),
                                    'Contribución (%)': [f"{v:.4f}" for v in contrib_tasa.values()]
                                })
                                st.dataframe(contrib_df_tasa, width=True)
                        
                        elif es_modelo_tasa:
                            # Para modelo de TASA: mostrar contribuciones de tasa
                            st.subheader("📈 Contribución a la Tasa")
                            contrib_df_tasa = pd.DataFrame({
                                'Variable': list(contrib_tasa.keys()),
                                'Contribución (%)': [f"{v:.4f}" for v in contrib_tasa.values()]
                            })
                            st.dataframe(contrib_df_tasa, width=True)
                        
                        else:
                            # Para modelos de VALOR: mostrar contribuciones de valor y tasa
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
                        if es_modelo_prima:
                            # Para prima
                            contrib_abs_prima = {k: abs(float(v)) for k, v in contrib_prima.items() if k != 'prima_base'}
                            top3_prima = sorted(contrib_abs_prima.items(), key=lambda x: x[1], reverse=True)[:3]
                            
                            # Para tasa
                            contrib_abs_tasa = {k: abs(float(v)) for k, v in contrib_tasa.items() if k != 'tasa_base'}
                            top3_tasa = sorted(contrib_abs_tasa.items(), key=lambda x: x[1], reverse=True)[:3]
                            
                            col_top1, col_top2 = st.columns(2)
                            with col_top1:
                                st.write("**Prima de riesgo:**")
                                for i, (var, val) in enumerate(top3_prima, 1):
                                    st.write(f"{i}. {var}: {contrib_prima[var]:.4f}")
                            
                            with col_top2:
                                st.write("**Tasa de descuento:**")
                                for i, (var, val) in enumerate(top3_tasa, 1):
                                    st.write(f"{i}. {var}: {contrib_tasa[var]:.4f}")
                        
                        elif es_modelo_tasa:
                            # Solo para tasa
                            contrib_abs_tasa = {k: abs(float(v)) for k, v in contrib_tasa.items() if k != 'tasa_base'}
                            top3_tasa = sorted(contrib_abs_tasa.items(), key=lambda x: x[1], reverse=True)[:3]
                            
                            st.write("**Tasa de descuento:**")
                            for i, (var, val) in enumerate(top3_tasa, 1):
                                st.write(f"{i}. {var}: {contrib_tasa[var]:.4f}")
                        
                        else:
                            # Para valor y tasa
                            contrib_abs_valor = {k: abs(v) for k, v in contrib_valor.items() if k != 'valor_base'}
                            top3_valor = sorted(contrib_abs_valor.items(), key=lambda x: x[1], reverse=True)[:3]
                            
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
                        'codigo_municipio': codigo_municipio,
                        'superficie': superficie,
                        'valor_m2': valor_m2,
                        'valor_total': valor_total,
                        'tasa_descuento': tasa_descuento,
                        'prima_riesgo': prima_riesgo,
                        'modelo_usado': modelo_valor['nombre_modelo'],
                        'contribuciones_valor': contrib_valor,
                        'contribuciones_tasa': contrib_tasa,
                        'contribuciones_prima': contrib_prima
                    }

                    st.download_button(
                        "📥 Descargar Informe JSON",
                        data=json.dumps(resultado, indent=2),
                        file_name=f"tasacion_{codigo_municipio}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                        use_container_width=True
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
        - `modelo`: Nombre del modelo (testigos_menos_10000, testigos_10000_50000, etc.)
        - `codigo_municipio`: Código del municipio (ej: 2005, 2006, etc.)
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
                columnas_requeridas = ['codigo_municipio', 'superficie', 'antiguedad', 'dormitorios', 'banos', 'planta']
                columnas_opcionales = ['calefaccion', 'ascensor', 'vivienda_nueva', 'calidad_alta']
                
                faltan_requeridas = [col for col in columnas_requeridas if col not in df.columns]
                if faltan_requeridas:
                    st.error(f"❌ Faltan columnas requeridas: {', '.join(faltan_requeridas)}")
                    return
                
                print(f"✅ Archivo cargado correctamente - {len(df)} registros detectados")
                
                # Estadísticas
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                with col_stats1:
                    st.metric("Registros", len(df))
                with col_stats2:
                    st.metric("Municipios", df['codigo_municipio'].nunique())
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
                                if pd.isna(fila['codigo_municipio']) or pd.isna(fila['superficie']):
                                    errores.append(f"Fila {idx+2}: Datos requeridos faltantes")
                                    continue
                                
                                codigo_municipio = str(fila['codigo_municipio'])
                                
                                # Obtener modelo directamente
                                modelo_nombre = str(fila['modelo'])
                                modelo_valor = st.session_state.modelo.obtener_modelo(modelo_nombre)
                                
                                if not modelo_valor:
                                    errores.append(f"Fila {idx+2}: Modelo {modelo_nombre} no encontrado")
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
                                valor_m2, contrib_valor = st.session_state.modelo.calcular_valor_m2(
                                    datos, modelo_valor, codigo_municipio
                                )
                                valor_total = valor_m2 * datos['superficie']
                                tasa_descuento, contrib_tasa = st.session_state.modelo.calcular_tasa_descuento(datos)
                                
                                # Encontrar factores más influyentes
                                contrib_abs = {k: abs(v) for k, v in contrib_valor.items() if k != 'valor_base'}
                                top_factores = sorted(contrib_abs.items(), key=lambda x: x[1], reverse=True)[:2]
                                factores_influyentes = ", ".join([f[0] for f in top_factores])
                                
                                resultados.append({
                                    'codigo_municipio': codigo_municipio,
                                    'superficie': datos['superficie'],
                                    'valor_m2': round(valor_m2, 2),
                                    'valor_total': round(valor_total, 2),
                                    'tasa_descuento': round(tasa_descuento, 4),
                                    'modelo': modelo_valor['nombre_modelo'],
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
        
        # Crear plantilla con datos de ejemplo usando códigos
        sample_data = {
            'modelo': ['testigos_menos_10000', 'testigos_menos_10000', 'testigos_menos_10000', 'testigos_menos_10000', 'testigos_menos_10000'],
            'codigo_municipio': ['2005', '2006', '2007', '2008', '2010'],
            'superficie': [85.5, 120.0, 65.0, 95.0, 110.0],
            'dormitorios': [3, 4, 2, 3, 4],
            'banos': [2, 3, 1, 2, 2],
            'planta': [2, 3, 1, 0, 2],
            'calefaccion': [True, True, False, True, True],
            'ascensor': [True, True, False, False, True],
            'vivienda_nueva': [False, True, False, True, False],
            'rehabilitacion': [False, False, True, False, True],
            'calidad_alta': [False, True, False, False, True]
        }
        sample_df = pd.DataFrame(sample_data)
        
        st.download_button(
            "📥 Descargar plantilla",
            data=sample_df.to_csv(index=False),
            file_name="plantilla_tasacion_multiple.csv",
            mime="text/csv",
            help="Descargue esta plantilla como referencia para el formato requerido"
        )

        st.markdown("---")
        st.markdown("### 💡 Consejos")
        st.write("• Use códigos de municipio válidos")
        st.write("• Verifique que los valores numéricos sean positivos")
        st.write("• Las columnas booleanas pueden usar Sí/No o 1/0")
        st.write("• El procesamiento tarda ~3 segundos por registro")

def pagina_documentacion():
    """Pestaña de documentación técnica mejorada usando configuración YAML"""
    if not st.session_state.config_sistema:
        st.error("No se pudo cargar la configuración del sistema")
        return
        
    config = st.session_state.config_sistema
    doc_config = config.get('documentacion', {})
    modelos_config = config.get('modelos_disponibles', [])
    
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
            <div style='text-align: center; color: #666; padding: 2rem 0;'>
                <p style='margin-bottom: 0.5rem; font-size: 0.9rem;'>
                    © {sistema_info.get('año', current_year)} <strong>{sistema_info.get('desarrollador', 'AESVAL - CTIC')}</strong> | 
                    {sistema_info.get('nombre', 'Sistema de Tasación Inteligente')} {sistema_info.get('version', 'v2.0')}
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