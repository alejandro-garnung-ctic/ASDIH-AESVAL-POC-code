# ASDIH-AESVAL-POC-code
A test web for AESVAL ASDIH

Sistema de tasación de inmuebles

Aplicación web para el cálculo de tasas de descuento de inmuebles según normativa ECO 805.

## Uso

Tasación Individual: Complete el formulario con las características del inmueble, pulse el botón de calcular y vea el resultado de la tasación

Tasación Múltiple: Suba un archivo Excel con múltiples registros, pulse calcular, descargue el resultado y vea las tasaciones

Documentación: Consulte la explicación del modelo matemático

## Modalidades

- Modalidad 1: **Tasación Individual**: Cálculo de tasa para un único inmueble
- Modalidad 2: **Tasación Múltiple**: Procesamiento por lotes mediante archivos Excel

## Features:

- **Análisis de Contribuciones**: Identificación de variables más influyentes
- **Validación de Datos**: Verificación de formatos y completitud

## Instalación y Ejecución

### Con Docker Compose (Recomendado)

```bash
docker compose up --build
```

La aplicación estará disponible en: `http://localhost:8501`

Configuración
Los modelos y coeficientes se configuran en config/modelos.yaml.


## Estructura del Proyecto
src/app.py: Aplicación principal Streamlit

src/models/: Modelos de datos y validadores Pydantic

src/utils/: Utilidades para cálculos

config/modelos.yaml: Configuración de modelos y coeficientes

## Desarrollo

Para el desarrollador, instale las dependencias y ejecute el proyecto con streamlit:

pip install -r requirements.txt
streamlit run src/app.py


Ejemplo de configutración de modelos: config/modelos.yaml

```yaml
version: "1.0"
fecha_actualizacion: "2025-01-10"

modelos:
  testigos_rango_1:
    nombre: "Municipios pequeños (< 5,000 hab)"
    rango_poblacion: [0, 5000]
    coeficientes:
      intercepto: 1000.0
      superficie: 150.5
      antiguedad: -10.2
      habitaciones: 25.3
      banyos: 30.1
      # ... más coeficientes según el Excel
    variables:
      - nombre: "superficie"
        tipo: "float"
        descripcion: "Superficie útil en m²"
        rango: [0, 1000]
      
      - nombre: "antiguedad" 
        tipo: "int"
        descripcion: "Años de antigüedad"
        rango: [0, 200]
      
      - nombre: "habitaciones"
        tipo: "int"
        descripcion: "Número de habitaciones"
        rango: [0, 20]

  testigos_rango_2:
    nombre: "Municipios medianos (5,000 - 20,000 hab)"
    # ... estructura similar
```

# Troubleshooting:

Verificar puertos:

```bash
# Ver qué procesos usan el puerto 8501
sudo lsof -i :8501

# O usar netstat
sudo netstat -tulpn | grep 8501
```

# TODO

- Hacer un comando agnóstico a SO para lanzar el contenedor sea con .sh o .bat
- Meter la ecuación correcta de los modelos y sus parámetros, bien diferenciados en /models
- Arreglar la generación de pdf
- Arreglar la descarga de la plantilla tipo, o bien ponerla como asset y añadirla estáticamente como recurso
- Eliminar los .py del models/? Igual teniendo el yaml no hace falta ya