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
    page_title="AESVAL - Modelos de tasa de descuento",
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
    posibles_rutas = [
        '/app/config/info.yaml',  # Ruta en contenedor Docker
        '/app/config/info.yml',   # Alternativa con .yml
        'config/info.yaml',       # Ruta relativa
        'config/info.yml',        # Alternativa relativa
    ]
    
    for ruta in posibles_rutas:
        try:
            if os.path.exists(ruta):
                print(f"✅ Cargando configuración desde: {ruta}")
                with open(ruta, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"❌ Error cargando {ruta}: {e}")
            continue
    
    st.error("❌ No se encontró ningún archivo de configuración válido")
    # Configuración por defecto - SOLO TASA Y PRIMA
    return {
        'sistema': {
            'nombre': 'Sistema de Tasación Automático',
            'version': '1.0',
            'actualizacion': '2025-01-10',
            'modelo': 'Análisis Econométrico Regresivo',
            'base_datos': '205,000+ testigos',
            'desarrollador': 'AESVAL - CTIC',
            'año': 2025
        },
        'metricas': {
            'r2_promedio': '69.83%',
            'precision': '97.2%',
            'tiempo_procesamiento': '0.1 ms por registro',
            'limite_registros': 50000
        },
        'modelos_disponibles': [
            # {'clave': 'testigos_menos_10000', 'nombre': 'Municipios < 10,000 hab'},
            # {'clave': 'testigos_10000_50000', 'nombre': 'Municipios 10,000-50,000 hab'},
            # {'clave': 'testigos_50000_200000', 'nombre': 'Municipios 50,000-200,000 hab'},
            # {'clave': 'testigos_mas_200000', 'nombre': 'Municipios > 200,000 hab'},
            {'clave': 'testigos_tasa', 'nombre': 'Modelo Tasa Descuento'},
            {'clave': 'testigos_prima', 'nombre': 'Modelo Prima Riesgo'}
        ]
    }

def cargar_modelos_json():
    """Carga los modelos desde archivos JSON en config/"""
    modelos = {}
    
    mapeo_modelos = {
        # 'modelo_Testigos_menos_de_10000': 'testigos_menos_10000',
        # 'modelo_Testigos_10000-50000': 'testigos_10000_50000', 
        # 'modelo_Testigos_50000-200000': 'testigos_50000_200000',
        # 'modelo_Testigos_más_de_200000': 'testigos_mas_200000',
        'modelo_Testigos_Prima': 'testigos_prima',
        'modelo_Testigos_Tasa': 'testigos_tasa'
    }
    
    posibles_rutas_base = [
        '/app/config/',  # Ruta en contenedor
        'config/',       # Ruta relativa
        './config/'      # Ruta relativa alternativa
    ]
    
    for archivo, clave in mapeo_modelos.items():
        encontrado = False
        for ruta_base in posibles_rutas_base:
            ruta_completa = f"{ruta_base}{archivo}.json"
            try:
                if os.path.exists(ruta_completa):
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        modelos[clave] = json.load(f)
                    print(f"✅ Modelo {clave} cargado desde: {ruta_completa}")
                    encontrado = True
                    break
            except Exception as e:
                print(f"❌ Error cargando {ruta_completa}: {e}")
                continue
        
        if not encontrado:
            print(f"⚠️ No se encontró el archivo para modelo {clave}")
            # Listar archivos disponibles para debugging
            for ruta_base in posibles_rutas_base:
                if os.path.exists(ruta_base):
                    archivos_disponibles = os.listdir(ruta_base)
                    print(f"📁 Archivos en {ruta_base}: {archivos_disponibles}")
    
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
        
        # Fallback a nombres por defecto - SOLO TASA Y PRIMA
        nombres_legibles = {
            # 'testigos_menos_10000': 'Municipios < 10,000 hab',
            # 'testigos_10000_50000': 'Municipios 10,000-50,000 hab',
            # 'testigos_50000_200000': 'Municipios 50,000-200,000 hab',
            # 'testigos_mas_200000': 'Municipios > 200,000 hab',
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
    
    # def calcular_valor_m2(self, datos: Dict, modelo: Dict, codigo_municipio: str) -> Tuple[float, Dict]:
    #     #Calcula el valor por m² usando el modelo especificado
    #     coef_municipio = modelo['coeficientes_municipios'].get(str(codigo_municipio), 0)
    #     coef_variables = modelo['coeficientes_variables']
    #     _cons = modelo['_cons']
        
    #     contribuciones = {}
    #     contribuciones_porcentaje = {}
        
    #     # Valor base (constante + efecto municipio)
    #     valor_base = _cons + coef_municipio
    #     contribuciones['valor_base'] = valor_base
    #     contribuciones[f'municipio_{codigo_municipio}'] = coef_municipio
        
    #     # Aplicar coeficientes según variables disponibles
    #     if datos.get('vivienda_nueva') and 'Dnueva' in coef_variables and coef_variables['Dnueva'] is not None:
    #         contrib = coef_variables['Dnueva']
    #         valor_base += contrib
    #         contribuciones['vivienda_nueva'] = contrib
        
    #     if 'SU' in coef_variables and coef_variables['SU'] is not None and datos.get('superficie'):
    #         contrib = coef_variables['SU'] * datos['superficie']
    #         valor_base += contrib
    #         contribuciones['superficie'] = contrib
        
    #     if datos.get('calefaccion') and 'DCA' in coef_variables and coef_variables['DCA'] is not None:
    #         contrib = coef_variables['DCA']
    #         valor_base += contrib
    #         contribuciones['calefaccion'] = contrib
        
    #     if 'ND' in coef_variables and coef_variables['ND'] is not None and datos.get('dormitorios'):
    #         contrib = coef_variables['ND'] * datos['dormitorios']
    #         valor_base += contrib
    #         contribuciones['dormitorios'] = contrib
        
    #     if 'NB' in coef_variables and coef_variables['NB'] is not None and datos.get('banos'):
    #         contrib = coef_variables['NB'] * datos['banos']
    #         valor_base += contrib
    #         contribuciones['banos'] = contrib
        
    #     if datos.get('calidad_alta') and 'CC_Alta' in coef_variables and coef_variables['CC_Alta'] is not None:
    #         contrib = coef_variables['CC_Alta']
    #         valor_base += contrib
    #         contribuciones['calidad_alta'] = contrib
        
    #     if datos.get('ascensor') and 'DAS' in coef_variables and coef_variables['DAS'] is not None:
    #         contrib = coef_variables['DAS']
    #         valor_base += contrib
    #         contribuciones['ascensor'] = contrib
        
    #     if 'PLbis' in coef_variables and coef_variables['PLbis'] is not None and datos.get('planta'):
    #         contrib = coef_variables['PLbis'] * datos['planta']
    #         valor_base += contrib
    #         contribuciones['planta'] = contrib
        
    #     valor_final = max(0, valor_base)
        
    #     # CALCULAR PORCENTAJES RELATIVOS
    #     if valor_final > 0:
    #         for key, value in contribuciones.items():
    #             contribuciones_porcentaje[key] = (value / valor_final) * 100 # En porcentaje
        
    #     return valor_final, contribuciones_porcentaje # ← Devuelve porcentajes
    
    def calcular_tasa_descuento(self, datos: Dict, codigo_municipio: str) -> Tuple[float, Dict]:
        """Calcula la tasa de descuento"""
        
        modelo_tasa = self.modelos.get('testigos_tasa')
        if not modelo_tasa:
            return 0.0, {}, "❌ No se encontró el modelo de tasa en los archivos JSON"
        
        # VERIFICAR SI EL MUNICIPIO EXISTE
        codigo_str = str(codigo_municipio)
        municipios_disponibles = list(modelo_tasa['coeficientes_municipios'].keys())
        
        if codigo_str not in municipios_disponibles:
            return 0.0, {}, f"❌ Municipio '{codigo_municipio}' no existe en este modelo."
        
        # Resto del código igual (sin st.error)
        coef_municipio = modelo_tasa['coeficientes_municipios'].get(codigo_str, 0)
        coef_variables = modelo_tasa['coeficientes_variables']
        _cons = modelo_tasa['_cons']
        
        contribuciones = {}
        contribuciones_porcentaje = {}
        
        # Tasa base (constante + efecto municipio)
        tasa_base = _cons + coef_municipio
        contribuciones['tasa_base'] = tasa_base
        contribuciones[f'municipio_{codigo_municipio}'] = coef_municipio
        
        # Aplicar coeficientes según variables disponibles usando los coeficientes reales
        # Solo usar variables que existen en el modelo (variables subrayadas amarillo)
        if 'SU' in coef_variables and coef_variables['SU'] is not None and datos.get('superficie'):
            contrib = coef_variables['SU'] * datos['superficie']
            tasa_base += contrib
            contribuciones['superficie'] = contrib
        
        if datos.get('vivienda_nueva') and 'Dnueva' in coef_variables and coef_variables['Dnueva'] is not None:
            contrib = coef_variables['Dnueva']
            tasa_base += contrib
            contribuciones['vivienda_nueva'] = contrib
        
        if datos.get('calefaccion') and 'DCA' in coef_variables and coef_variables['DCA'] is not None:
            contrib = coef_variables['DCA']
            tasa_base += contrib
            contribuciones['calefaccion'] = contrib
        
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
        
        if datos.get('calidad_alta') and 'CC_Alta' in coef_variables and coef_variables['CC_Alta'] is not None:
            contrib = coef_variables['CC_Alta']
            tasa_base += contrib
            contribuciones['calidad_alta'] = contrib
        
        # Variables sociales y ambientales (dummies: 0 o 1)
        # creci: 1 si evolución del entorno es creciente, 0 en caso contrario
        if datos.get('creci') and 'creci' in coef_variables and coef_variables['creci'] is not None:
            contrib = coef_variables['creci'] * 1  # Dummy: 1 si True, 0 si False
            tasa_base += contrib
            contribuciones['creci'] = contrib
        
        # renta: 1 si nivel de renta del entorno es media o alta, 0 en caso contrario
        if datos.get('renta') and 'renta' in coef_variables and coef_variables['renta'] is not None:
            contrib = coef_variables['renta'] * 1  # Dummy: 1 si True, 0 si False
            tasa_base += contrib
            contribuciones['renta'] = contrib
        
        # No aplicar thresholding - usar el valor calculado directamente
        tasa_final = tasa_base
        
        # CALCULAR PORCENTAJES RELATIVOS
        contribuciones_porcentaje = {}
        for key, value in contribuciones.items():
            contribuciones_porcentaje[key] = (value / tasa_final) * 100  
        
        return tasa_final, contribuciones_porcentaje, ""  # ← Devuelve string vacío para éxito

    def calcular_prima_riesgo(self, datos: Dict, codigo_municipio: str) -> Tuple[float, Dict]:
        """Calcula la prima de riesgo"""
        
        modelo_prima = self.modelos.get('testigos_prima')
        if not modelo_prima:
            return 0.0, {}, "❌ No se encontró el modelo de prima en los archivos JSON"
        
        # VERIFICAR SI EL MUNICIPIO EXISTE
        codigo_str = str(codigo_municipio)
        municipios_disponibles = list(modelo_prima['coeficientes_municipios'].keys())
        
        if codigo_str not in municipios_disponibles:
            return 0.0, {}, f"❌ Municipio '{codigo_municipio}' no existe en este modelo."
        
        # Resto del código igual (sin st.error)
        coef_municipio = modelo_prima['coeficientes_municipios'].get(codigo_str, 0)
        coef_variables = modelo_prima['coeficientes_variables']
        _cons = modelo_prima['_cons']
        
        contribuciones = {}
        contribuciones_porcentaje = {}
        
        # Prima base (constante + efecto municipio)
        prima_base = _cons + coef_municipio
        contribuciones['prima_base'] = prima_base
        contribuciones[f'municipio_{codigo_municipio}'] = coef_municipio
        
        # Aplicar coeficientes según variables disponibles usando los coeficientes reales
        # Solo usar variables que existen en el modelo (variables subrayadas amarillo)
        if 'SU' in coef_variables and coef_variables['SU'] is not None and datos.get('superficie'):
            contrib = coef_variables['SU'] * datos['superficie']
            prima_base += contrib
            contribuciones['superficie'] = contrib
        
        if datos.get('vivienda_nueva') and 'Dnueva' in coef_variables and coef_variables['Dnueva'] is not None:
            contrib = coef_variables['Dnueva']
            prima_base += contrib
            contribuciones['vivienda_nueva'] = contrib
        
        if datos.get('calefaccion') and 'DCA' in coef_variables and coef_variables['DCA'] is not None:
            contrib = coef_variables['DCA']
            prima_base += contrib
            contribuciones['calefaccion'] = contrib
        
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
        
        if datos.get('calidad_alta') and 'CC_Alta' in coef_variables and coef_variables['CC_Alta'] is not None:
            contrib = coef_variables['CC_Alta']
            prima_base += contrib
            contribuciones['calidad_alta'] = contrib
        
        # No aplicar thresholding - usar el valor calculado directamente
        prima_final = prima_base
        
        # CALCULAR PORCENTAJES RELATIVOS
        contribuciones_porcentaje = {}
        for key, value in contribuciones.items():
            contribuciones_porcentaje[key] = (value / prima_final) * 100 
        
        return prima_final, contribuciones_porcentaje, ""  # ← Devuelve string vacío para éxito

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
            'creci': False,
            'renta': False,
            'codigo_municipio': '2005', 
            'modelo_seleccionado': 'testigos_tasa',
            'ocultar_variables_no_correspondientes': False 
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
                Modelos de Tasa Descuento y Prima de Riesgo (ECO/805)
            </h2>
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
                Plataforma oficial para cálculo de Tasa Descuento y Prima de Riesgo según normativa ECO 805
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### ℹ️ Información del sistema")
        st.info(f"""
        **Versión:** {sistema.get('version', '1.0')}\n
        **Actualización:** {sistema.get('actualizacion', '2025-01-10')}\n
        **Modelo:** {sistema.get('modelo', 'ECO 805 - Análisis Econométrico')}\n
        **Base de datos:** {sistema.get('base_datos', '205,000+ testigos')}\n
        **R² Promedio:** {metricas.get('r2_promedio', '69.83%')}
        """)

        st.markdown("---")
        st.markdown("### 📈 Modelos disponibles")
        
        # Mostrar solo modelos de tasa y prima

        # COMENTAR modelos de testigos
        # for modelo in modelos_config:
        #     nombre = modelo.get('nombre', modelo.get('clave', ''))
        #     st.write(f"• {nombre}")
        
        for modelo in modelos_config:
            nombre = modelo.get('nombre', modelo.get('clave', ''))
            st.write(f"• {nombre}")
        
        st.markdown("---")
        st.markdown(f"""
        <div style='text-align: center; color: #666; font-size: 0.8rem; padding: 1rem 0;'>
            <p>© {sistema.get('año', current_year)} {sistema.get('desarrollador', 'AESVAL - CTIC')}</p>
        </div>
        """, unsafe_allow_html=True)
def pagina_tasacion_individual():
    """Pestaña para tasación individual - SOLO TASA Y PRIMA"""
    st.header("Cálculo individual - Tasa y Prima ECO 805")
    
    with st.container():
        st.info("""
        💡 **Complete los datos del inmueble para calcular la Tasa de Descuento o Prima de Riesgo 
        basada en modelos econométricos desarrollados con análisis de regresión múltiple.**
        """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.container():
            st.subheader("Datos del inmueble")
            
            col1_1, col1_2 = st.columns(2)
            
            with col1_1:
                # Selección directa del modelo - SOLO TASA Y PRIMA
                modelos_disponibles = st.session_state.modelo.obtener_modelos_disponibles()
                if not modelos_disponibles:
                    st.error("❌ No se cargaron modelos. Verifique los archivos JSON en config/")
                    st.stop()
                
                # Obtener modelo actual de datos persistentes
                modelo_actual = st.session_state.datos_persistentes.get('modelo_seleccionado', 'testigos_tasa')
                
                modelo_seleccionado = st.selectbox(
                    "Seleccione el modelo",
                    options=[clave for clave, _ in modelos_disponibles],
                    format_func=lambda x: next((nombre for clave, nombre in modelos_disponibles if clave == x), x),
                    help="Elija entre Tasa de Descuento o Prima de Riesgo",
                    key="selectbox_modelo",
                    index=[clave for clave, _ in modelos_disponibles].index(modelo_actual) if modelo_actual in [clave for clave, _ in modelos_disponibles] else 0
                )
                
                # ACTUALIZAR DATOS PERSISTENTES INMEDIATAMENTE cuando cambia el modelo
                if modelo_seleccionado != st.session_state.datos_persistentes.get('modelo_seleccionado'):
                    st.session_state.datos_persistentes['modelo_seleccionado'] = modelo_seleccionado
                
                # Determinar tipo de modelo
                es_modelo_prima = modelo_seleccionado == 'testigos_prima'
                es_modelo_tasa = modelo_seleccionado == 'testigos_tasa'
                
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
                
                # CAMPOS PARA MODELOS DE TASA/PRIMA
                calefaccion = st.checkbox(
                    "Calefacción", 
                    value=datos_persistentes.get('calefaccion', True),
                    help="¿El inmueble tiene calefacción? (variable DCA)",
                    key="input_calefaccion"
                )
                
                # Toggle para controlar si se ocultan variables que no corresponden al modelo
                ocultar_variables = st.checkbox(
                    "Ocultar variables no correspondientes al modelo",
                    value=datos_persistentes.get('ocultar_variables_no_correspondientes', True),
                    help="Si está activado, oculta las variables que no se usan en el modelo seleccionado. Si está desactivado, muestra todas las variables pero solo usa las correspondientes en el cálculo.",
                    key="input_ocultar_variables"
                )
                
                # Actualizar datos persistentes cuando cambia el toggle
                if ocultar_variables != datos_persistentes.get('ocultar_variables_no_correspondientes'):
                    st.session_state.datos_persistentes['ocultar_variables_no_correspondientes'] = ocultar_variables
                
                # Variables sociales y ambientales (creci y renta solo para modelo de tasa)
                # Son variables dummy (0 o 1)
                # Mostrar según el toggle y el modelo
                mostrar_creci_renta = not ocultar_variables or es_modelo_tasa
                
                if mostrar_creci_renta:
                    creci = st.checkbox(
                        "Evolución del entorno creciente (creci)", 
                        value=datos_persistentes.get('creci', False),
                        help="Variable dummy: 1 si la evolución del entorno es creciente, 0 en caso contrario" + (" - Solo para modelo Tasa" if not es_modelo_tasa else ""),
                        key="input_creci",
                        disabled=(not es_modelo_tasa and ocultar_variables)
                    )
                    
                    renta = st.checkbox(
                        "Nivel de renta media o alta (renta)", 
                        value=datos_persistentes.get('renta', False),
                        help="Variable dummy: 1 si el nivel de renta del entorno es media o alta, 0 en caso contrario" + (" - Solo para modelo Tasa" if not es_modelo_tasa else ""),
                        key="input_renta",
                        disabled=(not es_modelo_tasa and ocultar_variables)
                    )
                else:
                    # Para modelo prima cuando está oculto, usar valores por defecto (no se usan en el cálculo)
                    creci = False
                    renta = False
                
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

                vivienda_nueva = st.checkbox(
                    "Vivienda nueva (<5 años)", 
                    value=datos_persistentes.get('vivienda_nueva', False),
                    help="Menos de 5 años de antigüedad (variable Dnueva)",
                    key="input_vivienda_nueva"
                )

    with col2:
        with st.container():
            st.subheader("🎯 Calcular")
            
            # Mostrar información del modelo seleccionado
            if es_modelo_prima:
                st.info("🛡️ **Modelo de Prima de Riesgo activado**")
                st.write("Calcula únicamente la prima de riesgo")
            else:
                st.info("📈 **Modelo de Tasa Descuento activado**")
                st.write("Calcula únicamente la tasa de descuento")
            
            # Texto del botón según el tipo de modelo
            texto_boton = ""
            if es_modelo_prima:
                texto_boton = "🛡️ Calcular Prima de Riesgo"
            else:
                texto_boton = "📈 Calcular Tasa Descuento"
            
            if st.button(texto_boton, type="primary", width='stretch'):
                with st.spinner("Calculando usando modelos econométricos..."):
                    # Obtener el modelo seleccionado directamente
                    modelo_valor = st.session_state.modelo.obtener_modelo(modelo_seleccionado)
                    
                    if not modelo_valor:
                        st.error("❌ No se pudo cargar el modelo seleccionado")
                        return
                    
                    # Preparar datos para tasa/prima
                    datos_inmueble = {
                        'superficie': superficie,
                        'dormitorios': dormitorios,
                        'banos': banos,
                        'planta': planta,
                        'ascensor': ascensor,
                        'calefaccion': calefaccion,
                        'calidad_alta': calidad_alta,
                        'vivienda_nueva': vivienda_nueva
                    }
                    
                    # Solo añadir creci y renta para modelo de tasa
                    if es_modelo_tasa:
                        datos_inmueble['creci'] = creci
                        datos_inmueble['renta'] = renta
                    
                    # CALCULAR SÓLO LO QUE CORRESPONDA AL MODELO SELECCIONADO
                    resultados = {}
                    error_calculo = None
                    
                    if es_modelo_tasa:
                        tasa_descuento, contrib_tasa, mensaje_error = st.session_state.modelo.calcular_tasa_descuento(
                            datos_inmueble, codigo_municipio
                        )
                        if mensaje_error:
                            error_calculo = mensaje_error
                        else:
                            resultados.update({
                                'tasa_descuento': tasa_descuento,
                                'contrib_tasa': contrib_tasa
                            })

                    elif es_modelo_prima:
                        prima_riesgo, contrib_prima, mensaje_error = st.session_state.modelo.calcular_prima_riesgo(
                            datos_inmueble, codigo_municipio
                        )
                        if mensaje_error:
                            error_calculo = mensaje_error
                        else:
                            resultados.update({
                                'prima_riesgo': prima_riesgo,
                                'contrib_prima': contrib_prima
                            })
                    
                    # VERIFICAR SI HUBO ERROR
                    if error_calculo:
                        st.error(f"❌ Error en el cálculo: {error_calculo}")
                        return
                    
                    # Si no hay error, mostrar resultados normalmente
                    st.success("✅ Cálculo realizado correctamente")
                    
                    # Métricas principales (solo lo que se calculó)
                    if es_modelo_prima:
                        col_res1, col_res2 = st.columns(2)
                        with col_res1:
                            st.metric("Prima de Riesgo", f"{resultados['prima_riesgo']:.2%}")
                        with col_res2:
                            st.metric("Tipo de Modelo", "Prima")
                    
                    else:
                        col_res1, col_res2 = st.columns(2)
                        with col_res1:
                            st.metric("Tasa Descuento", f"{resultados['tasa_descuento']:.2%}")
                        with col_res2:
                            st.metric("Tipo de Modelo", "Tasa")
                    
                    # Información del modelo usado
                    st.info(f"**Modelo aplicado:** {modelo_valor['nombre_modelo']}")
                    
                    # Contribuciones detalladas (solo las relevantes)
                    with st.expander("📊 Análisis detallado de contribuciones", expanded=True):
                        if es_modelo_prima:
                            st.subheader("Contribución a la Prima")
                            contrib_df_prima = pd.DataFrame({
                                'Variable': list(resultados['contrib_prima'].keys()),
                                'Impacto en Prima': [f"{v:+.1f}%" for v in resultados['contrib_prima'].values()],  
                                'Efecto': ['📈 Aumenta' if v > 0 else '📉 Reduce' for v in resultados['contrib_prima'].values()]
                            })
                            st.dataframe(contrib_df_prima, width='stretch', height=200, hide_index=True)
                        
                        else:
                            st.subheader("Contribución a la Tasa")
                            contrib_df_tasa = pd.DataFrame({
                                'Variable': list(resultados['contrib_tasa'].keys()),
                                'Impacto en Tasa': [f"{v:+.1f}%" for v in resultados['contrib_tasa'].values()],
                                'Efecto': ['📈 Aumenta' if v > 0 else '📉 Reduce' for v in resultados['contrib_tasa'].values()]
                            })
                            st.dataframe(contrib_df_tasa, width='stretch', height=200, hide_index=True)
                    
                    # Preparar resultado para descarga
                    resultado_descarga = {
                        'fecha_calculo': datetime.now().isoformat(),
                        'codigo_municipio': codigo_municipio,
                        'superficie': superficie,
                        'modelo_usado': modelo_valor['nombre_modelo'],
                    }
                    
                    # Agregar solo los resultados calculados
                    if es_modelo_tasa:
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
                        data=json.dumps(resultado_descarga, indent=2, ensure_ascii=False),
                        file_name=f"calculo_{codigo_municipio}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                        width='stretch'
                    )
            else:
                st.info("ℹ️ Complete los datos y haga clic en el botón para obtener resultados")

def validar_fila_para_modelo(fila: pd.Series, modelo_clave: str) -> Tuple[bool, List[str]]:
    """Valida que una fila tenga las columnas requeridas para el modelo especificado"""
    errores = []
    
    # Columnas requeridas para todos los modelos
    columnas_requeridas_base = ['codigo_municipio', 'superficie', 'dormitorios', 'banos', 'planta']
    
    # Columnas específicas por tipo de modelo - SOLO TASA/PRIMA
    # Nota: Las variables sociales/ambientales (creci, renta) son opcionales
    columnas_requeridas = columnas_requeridas_base + ['ascensor', 'calefaccion', 'calidad_alta', 'vivienda_nueva']
    
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

def procesar_fila_multiple(fila: pd.Series, modelo_tasacion, modelo_seleccionado: str) -> Tuple[bool, Dict, str]:
    """Procesa una fila individual del Excel y retorna resultado o error"""
    try:
        # Validar que la fila tenga datos básicos
        if pd.isna(fila['codigo_municipio']) or pd.isna(fila['superficie']):
            return False, {}, "Datos básicos faltantes (código municipio o superficie)"
        
        # Obtener modelo
        modelo_obj = modelo_tasacion.modelos.get(modelo_seleccionado)
        if not modelo_obj:
            return False, {}, f"Modelo '{modelo_seleccionado}' no encontrado"
        
        # Preparar datos según tipo de modelo
        codigo_municipio = str(fila['codigo_municipio'])
        superficie = float(fila['superficie'])
        
        # Modelo de tasa o prima
        datos = {
            'superficie': superficie,
            'dormitorios': int(fila.get('dormitorios', 0)),
            'banos': int(fila.get('banos', 0)),
            'planta': int(fila.get('planta', 0)),
            'ascensor': bool(fila.get('ascensor', False)),
            'calefaccion': bool(fila.get('calefaccion', True)),
            'calidad_alta': bool(fila.get('calidad_alta', False)),
            'vivienda_nueva': bool(fila.get('vivienda_nueva', False))
        }
        
        # Solo añadir creci y renta para modelo de tasa (variables dummy: 0 o 1)
        if modelo_seleccionado == 'testigos_tasa':
            # Convertir a booleano: True si es 1, True, "Sí", etc., False en caso contrario
            creci_val = fila.get('creci', False)
            if pd.notna(creci_val):
                datos['creci'] = bool(creci_val) if isinstance(creci_val, (bool, int, float)) else str(creci_val).lower() in ['true', '1', 'sí', 'si', 'yes', 'verdadero']
            else:
                datos['creci'] = False
            
            renta_val = fila.get('renta', False)
            if pd.notna(renta_val):
                datos['renta'] = bool(renta_val) if isinstance(renta_val, (bool, int, float)) else str(renta_val).lower() in ['true', '1', 'sí', 'si', 'yes', 'verdadero']
            else:
                datos['renta'] = False
        
        if modelo_seleccionado == 'testigos_tasa':
            resultado, contribuciones, mensaje_error = modelo_tasacion.calcular_tasa_descuento(datos, codigo_municipio)
            if mensaje_error:  # Si hay mensaje de error, retornar error
                return False, {}, mensaje_error
                
            return True, {
                'tipo': 'tasa',
                'valor': resultado,
                'contribuciones': contribuciones,
                'modelo': modelo_obj['nombre_modelo'],
                'codigo_municipio': codigo_municipio,
                'superficie': superficie
            }, ""
        else: # testigos_prima
            resultado, contribuciones, mensaje_error = modelo_tasacion.calcular_prima_riesgo(datos, codigo_municipio)
            if mensaje_error:  # Si hay mensaje de error, retornar error
                return False, {}, mensaje_error
                
            return True, {
                'tipo': 'prima',
                'valor': resultado,
                'contribuciones': contribuciones,
                'modelo': modelo_obj['nombre_modelo'],
                'codigo_municipio': codigo_municipio,
                'superficie': superficie
            }, ""
            
    except Exception as e:
        return False, {}, f"Error en procesamiento: {str(e)}"

def crear_plantilla_fallback(modelo_tipo: str = "tasa"):
    """Crea una plantilla básica según el tipo de modelo"""
    # Datos de ejemplo para tasa/prima
    sample_data = {
        'codigo_municipio': ['2005', '2006', '2007'],
        'superficie': [85.5, 120.0, 65.0],
        'dormitorios': [3, 4, 2],
        'banos': [2, 3, 1],
        'planta': [2, 3, 1],
        'ascensor': [True, True, False],
        'calefaccion': [True, True, False],
        'calidad_alta': [False, True, False],
        'vivienda_nueva': [False, True, False],
        'creci': [True, False, True],
        'renta': [True, True, False]
    }
    
    df_fallback = pd.DataFrame(sample_data)
    
    # Crear Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_fallback.to_excel(writer, index=False, sheet_name='Plantilla')
    
    excel_data = output.getvalue()
    
    nombre_archivo = f"plantilla_{modelo_tipo}_basica.xlsx"
    
    st.download_button(
        f"📥 Descargar plantilla para {modelo_tipo}",
        data=excel_data,
        file_name=nombre_archivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width='stretch'
    )
    
def pagina_tasacion_multiple():
    """Pestaña para cálculo múltiple por lotes - SOLO TASA Y PRIMA"""
    st.header("Cálculo múltiple por lotes")
    
    limite_registros = f"{st.session_state.config_sistema['metricas'].get('limite_registros', 50000)}"

    with st.expander("ℹ️ Información sobre cálculo múltiple", expanded=False):
        st.markdown(f"""
        **Características del cálculo por lotes:**
        - Procesamiento simultáneo de múltiples inmuebles
        - Validación automática de datos
        - Detección y reporte de errores por fila
        - Generación de informe consolidado
        - Límite: {limite_registros} registros por lote
        
        **Columnas requeridas en el Excel:**
        - `codigo_municipio`: Código del municipio (ej: 2005, 2006, etc.)
        - `superficie`: Superficie en m² (número)
        - `dormitorios`: Número de dormitorios
        - `banos`: Número de baños
        - `planta`: Planta del inmueble
        - `ascensor`: Sí/No o 1/0
        - `calefaccion`: Sí/No o 1/0
        - `calidad_alta`: Sí/No o 1/0
        - `vivienda_nueva`: Sí/No o 1/0
        
        **Columnas opcionales (solo para modelo Tasa):**
        - `creci`: Variable dummy - 1/True/Sí si la evolución del entorno es creciente, 0/False/No en caso contrario - Solo se usa en modelo Tasa
        - `renta`: Variable dummy - 1/True/Sí si el nivel de renta del entorno es media o alta, 0/False/No en caso contrario - Solo se usa en modelo Tasa
        """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Selector de modelo para el lote completo
        modelo_lote = st.selectbox(
            "Seleccione el modelo a aplicar:",
            options=['testigos_tasa', 'testigos_prima'],
            format_func=lambda x: "Tasa Descuento" if x == 'testigos_tasa' else "Prima Riesgo",
            help="Elija el modelo a aplicar a todo el lote de datos",
            key="select_modelo_lote"
        )
        
        uploaded_file = st.file_uploader(
            "📤 Subir archivo Excel para cálculo múltiple", 
            type=['xlsx', 'xls'],
            help=f"El archivo debe contener las columnas requeridas para {modelo_lote}"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                
                print(f"✅ Archivo cargado correctamente - {len(df)} registros detectados")
                
                # Estadísticas
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                with col_stats1:
                    st.metric("Registros", len(df))
                with col_stats2:
                    st.metric("Modelo", "Tasa" if modelo_lote == 'testigos_tasa' else "Prima")
                with col_stats3:
                    st.metric("Municipios", df['codigo_municipio'].nunique() if 'codigo_municipio' in df.columns else 0)
                
                # Procesar lote
                if st.button("🚀 Procesar Lote Completo", type="primary", width='stretch'):
                    with st.spinner(f"Procesando {len(df)} registros..."):
                        resultados_exitosos = []
                        resultados_detallados = []
                        errores_detallados = []
                        
                        for idx, fila in df.iterrows():
                            numero_fila = idx + 2  # +2 porque Excel empieza en 1 y tiene headers
                            
                            # Validar fila primero
                            es_valida, errores_validacion = validar_fila_para_modelo(fila, modelo_lote)
                            
                            if not es_valida:
                                errores_detallados.append({
                                    'fila': numero_fila,
                                    'estado': '❌ ERROR',
                                    'codigo_municipio': str(fila.get('codigo_municipio', 'N/A')),
                                    'error': f"Errores validación: {', '.join(errores_validacion)}"
                                })
                                continue
                            
                            # Procesar fila individual
                            es_exitosa, resultado, mensaje_error = procesar_fila_multiple(
                                fila, st.session_state.modelo, modelo_lote
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
                        
                        # Pestañas para resultados detallados - ELIMINAR CONSOLIDADO
                        tab_resultados, tab_errores = st.tabs([
                            f"✅ Resultados ({len(resultados_exitosos)})",
                            f"❌ Errores ({len(errores_detallados)})"
                        ])
                        
                        with tab_resultados:
                            if resultados_detallados:
                                df_resultados = pd.DataFrame(resultados_detallados)
                                st.dataframe(df_resultados, width='stretch')
                                
                                # BOTÓN DE DESCARGA EN RESULTADOS
                                if resultados_exitosos:
                                    # Crear DataFrame para descarga
                                    datos_descarga = []
                                    for resultado in resultados_exitosos:
                                        fila_descarga = {
                                            'fila': resultados_detallados[resultados_exitosos.index(resultado)]['fila'],
                                            'modelo': resultado['modelo'],
                                            'codigo_municipio': resultado['codigo_municipio'],
                                            'superficie': resultado['superficie'],
                                            'resultado': resultado['valor']
                                        }
                                        
                                        # Agregar factores más influyentes
                                        todas_contribuciones = obtener_detalles_contribuciones(resultado['contribuciones'])
                                        fila_descarga.update(todas_contribuciones)
                                        
                                        datos_descarga.append(fila_descarga)
                                    
                                    df_descarga = pd.DataFrame(datos_descarga)
                                    
                                    # Descargar como Excel
                                    output = io.BytesIO()
                                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                        df_descarga.to_excel(writer, index=False, sheet_name='Resultados')
                                    
                                    excel_data = output.getvalue()
                                    st.download_button(
                                        "📊 Descargar Excel con Resultados",
                                        data=excel_data,
                                        file_name=f"resultados_{modelo_lote}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        width='stretch'
                                    )
                            else:
                                st.info("No hay resultados exitosos para mostrar")
                        
                        with tab_errores:
                            if errores_detallados:
                                df_errores = pd.DataFrame(errores_detallados)
                                st.dataframe(df_errores, width='stretch')
                                
                                # COMENTAR Mostrar análisis de errores
                                # st.subheader("📈 Análisis de Errores")
                                # errores_por_tipo = df_errores['error'].value_counts()
                                # st.bar_chart(errores_por_tipo)
                            else:
                                st.success("🎉 No se encontraron errores en el procesamiento")

            except Exception as e:
                st.error(f"❌ Error procesando el archivo: {str(e)}")
    
    with col2:
        st.subheader("📋 Plantilla de ejemplo")
        
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
                tipo_modelo = "tasa" if modelo_lote == 'testigos_tasa' else "prima"
                st.download_button(
                    f"📥 Descargar plantilla para {tipo_modelo}",
                    data=excel_data,
                    file_name=f"plantilla_{tipo_modelo}_basica.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help=f"Descargue la plantilla para cálculo de {tipo_modelo}",
                    width='stretch'
                )
                
            except Exception as e:
                st.error(f"❌ Error cargando plantilla: {e}")
                # Fallback: crear plantilla básica
                st.warning("Usando plantilla básica de respaldo...")
                crear_plantilla_fallback(modelo_lote.split('_')[-1])  # 'tasa' o 'prima'
        else:
            st.error("❌ No se encontró la plantilla en assets/")
            st.info("Creando plantilla de respaldo...")
            crear_plantilla_fallback(modelo_lote.split('_')[-1])

        st.markdown("---")
        st.markdown("### 💡 Consejos para el formato")
        st.write("• **Formato Excel**: Use .xlsx para mejor compatibilidad")
        st.write("• **Booleanos**: Use VERDADERO/FALSO, True/False, Sí/No, o 1/0")
        st.write("• **Variables dummy**: Use 1/0, True/False, o Sí/No para creci y renta (solo para modelo Tasa)")
        st.write("• **Codificación**: UTF-8 para caracteres especiales")

# Funciones auxiliares para el procesamiento múltiple
def format_resultado_multiple(resultado: Dict) -> str:
    """Formatea el resultado para mostrar en tabla"""
    if resultado['tipo'] == 'tasa':
        return f"{resultado['valor']:.2%}"
    elif resultado['tipo'] == 'prima':
        return f"{resultado['valor']:.2%}"
    return "N/A"

def obtener_detalles_contribuciones(contribuciones: Dict) -> str:
    """Obtiene todas las contribuciones como columnas separadas"""
    factores_dict = {}
    
    if contribuciones:
        # Convertir los valores de porcentaje a números flotantes para ordenar
        contribs_numericas = []
        for factor, impacto in contribuciones.items():
            try:
                # Remover el símbolo % y convertir a float
                if isinstance(impacto, str):
                    valor_numerico = float(impacto.replace('%', '').replace('+', ''))
                else:
                    valor_numerico = float(impacto)
                contribs_numericas.append((factor, valor_numerico, impacto))
            except (ValueError, TypeError):
                # Si no se puede convertir, usar 0
                contribs_numericas.append((factor, 0.0, impacto))
        
        # Ordenar por impacto absoluto (de mayor a menor)
        contribs_ordenadas = sorted(contribs_numericas, 
                                  key=lambda x: abs(x[1]), reverse=True)
        
        # Agregar TODAS las contribuciones
        for i, (factor, valor_numerico, impacto_str) in enumerate(contribs_ordenadas, 1):
            # Limpiar nombre del factor
            nombre_limpio = factor.replace('contrib_', '').replace('_', ' ').title()
            # Reemplazar nombres específicos para mejor legibilidad
            nombre_limpio = nombre_limpio.replace('Tasa Base', 'Componente Base')
            nombre_limpio = nombre_limpio.replace('Prima Base', 'Componente Base')
            nombre_limpio = nombre_limpio.replace('Municipio', 'Efecto Municipio')
            
            factores_dict[f'factor_{i}'] = nombre_limpio
            factores_dict[f'impacto_{i}'] = f"{valor_numerico:+.1f}%"
    
    return factores_dict

def pagina_documentacion():
    """Pestaña de documentación técnica """
    if not st.session_state.config_sistema:
        st.error("No se pudo cargar la configuración del sistema")
        return
        
    config = st.session_state.config_sistema
    doc_config = config.get('documentacion', {})
    
    st.header("Documentación técnica")
    
    # Introducción desde YAML 
    introduccion = doc_config.get('introduccion', 'Sistema para cálculo de Tasa de Descuento y Prima de Riesgo basado en análisis de regresión múltiple.')
    st.markdown(f"""
    <div style='background: #f0f2f6; padding: 2rem; border-radius: 10px; border-left: 4px solid #1f77b4;'>
        <h4 style='color: #1f77b4; margin-top: 0;'>Modelos Econométricos para Tasa y Prima</h4>
        <p style='margin-bottom: 0;'>{introduccion}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metodología desde YAML
    st.subheader("🔬 Metodología científica")
    
    col_metodo1, col_metodo2 = st.columns(2)
    
    with col_metodo1:
        st.markdown("**Bases de datos:**")
        for item in doc_config.get('metodologia', {}).get('base_datos', []):
            st.write(f"- {item}")
        
        st.markdown("**Procesamiento:**")
        for item in doc_config.get('metodologia', {}).get('procesamiento', []):
            st.write(f"- {item}")
    
    with col_metodo2:
        st.markdown("**Validación estadística:**")
        for item in doc_config.get('metodologia', {}).get('validacion', []):
            st.write(f"- {item}")
        
        st.markdown("**Software utilizado:**")
        for item in doc_config.get('metodologia', {}).get('software', []):
            st.write(f"- {item}")
    
    # Modelos matemáticos - SOLO TASA Y PRIMA
    st.subheader("🧮 Modelos matemáticos implementados")
    
    tab_model1, tab_model2 = st.tabs(["Tasa Descuento", "Prima Riesgo"])
        
    with tab_model1:
        st.markdown("""
        ### Modelo de Tasa de Descuento
        
        $$Tasa_i = \\beta_0 + \\sum_{j=1}^{J}\\beta_j X_{ji} + \\epsilon_i$$
        
        **Componentes:**
        - Tasa libre de riesgo (bonos estado 5 años)
        - Prima de riesgo específica del inmueble
        
        **Variables significativas:**
        - **SU**: Superficie construida
        - **Dnueva**: Vivienda nueva (< 5 años) - dummy
        - **DCA**: Calefacción - dummy
        - **NB**: Número de baños
        - **ND**: Número de dormitorios
        - **DAS**: Ascensor - dummy
        - **CC_Alta**: Calidad constructiva alta - dummy
        - **creci**: Variable dummy - 1 si la evolución del entorno es creciente, 0 en caso contrario
        - **renta**: Variable dummy - 1 si el nivel de renta del entorno es media o alta, 0 en caso contrario
        - **_cons**: Término constante (tasa base)
        """)
        
        st.latex(r"""
        \text{Tasa Descuento} = \text{Tasa Libre Riesgo} + \text{Prima Riesgo}
        """)

    with tab_model2:
        st.markdown("""
        ### Modelo de Prima de Riesgo
        
        $$Prima_i = \\beta_0 + \\sum_{j=1}^{J}\\beta_j X_{ji} + \\epsilon_i$$
        
        **Factores de riesgo considerados:**
        - Riesgo de ubicación (municipio)
        - Riesgo por antigüedad y estado
        - Riesgo por características constructivas
        - Riesgo de mercado local
        
        **Variables significativas:**
        - **SU**: Superficie construida
        - **Dnueva**: Vivienda nueva (< 5 años) - dummy
        - **DCA**: Calefacción - dummy
        - **NB**: Número de baños
        - **ND**: Número de dormitorios
        - **DAS**: Ascensor - dummy
        - **CC_Alta**: Calidad constructiva alta - dummy
        - **_cons**: Término constante (prima base)
        
        **Hallazgos clave:**
        - Municipios pequeños: mayor prima por iliquidez
        - Ascensor y calidad constructiva: reducen prima
        - Calefacción: efecto en la prima
        """)

    # st.subheader("🏙️ Segmentación por Tamaño Municipal")
    
    # col_seg1, col_seg2, col_seg3, col_seg4 = st.columns(4)
    
    # # Obtener modelos disponibles desde la configuración
    # modelos_config = config.get('modelos_disponibles', [])
    
    # # Buscar los R² específicos para cada modelo de valor
    # r2_menos_10000 = next((modelo.get('r2', '76.32%') for modelo in modelos_config if modelo.get('clave') == 'testigos_menos_10000'), '76.32%')
    # r2_10000_50000 = next((modelo.get('r2', '73.89%') for modelo in modelos_config if modelo.get('clave') == 'testigos_10000_50000'), '73.89%')
    # r2_50000_200000 = next((modelo.get('r2', '67.18%') for modelo in modelos_config if modelo.get('clave') == 'testigos_50000_200000'), '67.18%')
    # r2_mas_200000 = next((modelo.get('r2', '61.95%') for modelo in modelos_config if modelo.get('clave') == 'testigos_mas_200000'), '61.95%')

    # with col_seg1:
    #     st.metric("< 10,000 hab", f"R² = {r2_menos_10000}", "Mayor poder explicativo")
    # with col_seg2:
    #     st.metric("10,000-50,000", f"R² = {r2_10000_50000}", "Alta significatividad")
    # with col_seg3:
    #     st.metric("50,000-200,000", f"R² = {r2_50000_200000}", "Modelo robusto")
    # with col_seg4:
    #     st.metric("> 200,000 hab", f"R² = {r2_mas_200000}", "Máxima complejidad")

    # st.markdown('''
    # **Hallazgos clave de los modelos econométricos:**
    # - **R² decreciente con tamaño municipal**: Mayor poder explicativo en municipios pequeños (76.32%) vs grandes (61.95%)
    # - **Efecto superficie (SU)**: Negativo en municipios < 200k hab, positivo en grandes ciudades
    # - **Dormitorios (ND)**: Efecto negativo consistente en todos los modelos
    # - **Variables positivas**: Baños (NB), ascensor (DAS), calidad alta (CC_Alta) y calefacción (DCA) siempre positivas
    # - **Planta (PLbis)**: Efecto positivo que se intensifica con el tamaño municipal
    # ''')

def mostrar_footer():
    """Footer usando configuración YAML"""
    import datetime
    current_year = datetime.datetime.now().year

    if not st.session_state.config_sistema:
        sistema_info = {'nombre': 'AESVAL - CTIC', 'version': 'v1.0'}
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
                    {sistema_info.get('nombre', 'Sistema de Cálculo de Tasa y Prima')} {sistema_info.get('version', 'v21.0')}
                </p>
                <p style='margin-bottom: 0; font-size: 0.8rem;'>
                    Desarrollado con Streamlit • Modelos Econométricos STATA • 
                    <a href='https://www.boe.es/buscar/pdf/2003/BOE-A-2003-7253-consolidado.pdf' style='color: blue; text-decoration: underline;' target='_blank'>Normativa ECO/805</a> • 
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
        "📚 Documentación técnica", 
        "🏠 Cálculo individual", 
        "📁 Cálculo por lotes"
    ])
    
    with tab1:
        pagina_documentacion()
    
    with tab2:
        pagina_tasacion_individual()
    
    with tab3:
        pagina_tasacion_multiple()
    
    mostrar_footer()

if __name__ == "__main__":
    main()