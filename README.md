# ASDIH-AESVAL - Sistema de Tasación Automático

Sistema web para cálculo de **Tasa de Descuento** y **Prima de Riesgo** de inmuebles según normativa ECO 805, basado en modelos econométricos desarrollados con análisis de regresión múltiple.

## Características Principales

### 🎯 Funcionalidades
- **Cálculo Individual**: Tasación en tiempo real para un único inmueble
- **Procesamiento por Lotes**: Cálculo masivo mediante archivos Excel
- **Modelos Especializados**: 
  - Modelo de Tasa Descuento
  - Modelo de Prima de Riesgo
- **Análisis Detallado**: Desglose de contribuciones por variable
- **Validación Robusta**: Verificación automática de datos y formatos

### 📊 Modelos Implementados
- **Tasa de Descuento**: Cálculo de la tasa aplicable considerando riesgo específico del inmueble
- **Prima de Riesgo**: Evaluación del riesgo adicional por características particulares
- **Base de datos**: Modelos entrenados con 205,000+ observaciones reales

## Uso de la Aplicación

### Tasación Individual
1. Seleccione el modelo (Tasa Descuento o Prima Riesgo)
2. Complete las características del inmueble
3. Haga clic en "Calcular"
4. Revise resultados y análisis de contribuciones

### Tasación Múltiple
1. Descargue la plantilla Excel disponible
2. Complete los datos de múltiples inmuebles
3. Suba el archivo y procese el lote
4. Descargue resultados consolidados

## Variables del Modelo

### Variables Comunes a Todos los Modelos
- **SU**: Superficie construida (m²)
- **ND**: Número de dormitorios  
- **NB**: Número de baños
- **PLbis**: Planta del inmueble
- **DAS**: Ascensor (booleano)
- **CC_Alta**: Calidad constructiva alta (booleano)
- **Dnueva**: Vivienda nueva <5 años (booleano)

### Variables Específicas Tasa/Prima
- **antig**: Antigüedad del inmueble (años)
- **EC_Alto**: Estado de conservación alto (booleano)
- **rehab**: Rehabilitación del edificio (booleano)

## Instalación y Despliegue

### Con Docker Compose (Recomendado)

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```
La aplicación estará disponible en: `http://localhost:8502`

Para ver los logs de la aplicación:

```bash
docker-compose logs -f tasacion-app
```

> [!WARNING]
> Se recomienda que la aplicación se ejecute en una ruta que no contenga espacios, e.g. `C:\User\Desktop\folder`.

### Desarrollo Local

```bash
pip install -r requirements.txt
streamlit run src/app.py
```

## Configuración

- **Modelos**: Archivos JSON en `config/modelo_*.json`
- **Sistema**: Configuración general en `config/info.yaml`
- **Coeficientes**: Definidos por modelo econométrico en archivos de configuración

## Estructura Técnica

- **Frontend**: Streamlit
- **Procesamiento**: Pandas, NumPy
- **Modelos**: Coeficientes pre-calculados desde análisis econométrico
- **Persistencia**: Session state para datos entre recargas

---

*Sistema desarrollado por AESVAL - CTIC para la tasación automatizada según normativa ECO 805*
