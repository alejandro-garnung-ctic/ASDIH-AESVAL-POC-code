from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict
from enum import Enum

class TipoInmueble(str, Enum):
    PISO = "piso"
    CASA = "casa"
    OFICINA = "oficina"
    LOCAL = "local"

class TasacionIndividual(BaseModel):
    """Modelo para validar datos de tasación individual"""
    codigo_municipio: str = Field(..., min_length=5, max_length=10)
    superficie: float = Field(..., gt=0, le=1000)
    antiguedad: int = Field(..., ge=0, le=200)
    habitaciones: int = Field(..., ge=0, le=20)
    banyos: int = Field(..., ge=0, le=10)
    tipo_inmueble: TipoInmueble
    # ... más campos según el Excel
    
    @validator('codigo_municipio')
    def validar_codigo_municipio(cls, v):
        # Validar formato del código de municipio
        if not v.isalnum():
            raise ValueError('El código de municipio debe ser alfanumérico')
        return v

class ResultadoTasacion(BaseModel):
    """Modelo para resultados de tasación"""
    tasa_descuento: float
    contribuciones: Dict[str, float]
    variables_destacadas: List[str]
    modelo_aplicado: str