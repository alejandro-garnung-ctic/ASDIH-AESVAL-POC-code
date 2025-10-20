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

### Variable Contribution Calculation

Each variable contributes to the final result by multiplying its **value** by its **coefficient** from the econometric model. The impact is shown as a percentage of the total calculated value:

- **Surface area**: `80 m² × -4.145 €/m² = -331.6 €` → `-2.2% 📉 Reduces value`
- **Additional bathroom**: `1 bathroom × 90.862 € = +90.86 €` → `+3.0% 📈 Increases value`  
- **Elevator**: `Yes × 116.861 € = +116.86 €` → `+16.0% 📈 Increases value`

Coefficients come from regression analysis on 205000+ observations and represent the marginal impact of each characteristic. The percentage shows each variable's relative contribution to the final calculated value/rate.

## Instalación y Ejecución

### Con Docker Compose (Recomendado)

```bash
docker compose up -d --build
```

La aplicación estará disponible en: `http://localhost:8501`

### Configuración

Los modelos y coeficientes se configuran en los ficheros `config/modelo_*.yaml`.

La información mostrada sobre la aplicación se configura en `config/info.yaml`.

## Desarrollo

Para el desarrollador, instale las dependencias y ejecute el proyecto con streamlit:

```bash
pip install -r requirements.txt
streamlit run src/app.py
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
- Cambiar completamente el enfoque del código para que cómo se calcule el valor, y los parámetros del modelo, no estén en el código. Ello se especificaría directamente en los archivos json o yaml de config (ecuación, parámetros, modelo...), así todo queda configurable incluso en tiempo real, sin necesidad de recompilar para añadir o quitar parámetros o ecuaciones o modelos. Esto resolvería problema de si queremos cambiar e.g. que Los modelos de valor muestran: Dnueva, SU, DCA, ND, NB, CC_Alta, DAS, PLbis y Los modelos de Tasa/Prima muestran: SU, antig, NB, ND, CC_Alta, EC_Alto, rehab, DAS, PLbis
- Añadir una Root MSE promedio además de la precisión al lateral de información?
- Arreglar lo de ocultar lo de Deploy y header de streamlit excepto el botón de desplegar sidebar de nuevo.
- Añadir una Política de privacidad y Términos de uso
- Revisar qué rangos razonables de tasa y prima de los valores (clamp) poner, si es que se requieren poner.
