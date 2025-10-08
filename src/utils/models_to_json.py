import pandas as pd
import json

def excel_to_json(excel_file, sheet_name, output_file=None):
    df = pd.read_excel(excel_file, sheet_name=sheet_name)

    modelo_json = {
        "nombre_modelo": sheet_name,
        "coeficientes_municipios": {},
        "coeficientes_variables": {},
        "_cons": None
    }

    row_vars = df.iloc[0]
    
    coef_columns = [col for col in df.columns if col.startswith('Coef.')]
    
    coeficientes_variables = {}
    for col in coef_columns:
        if col != 'Coef.' and col != 'Coef. _cons':
            variable_name = col.replace('Coef. ', '').strip()
            coeficientes_variables[variable_name] = row_vars.get(col)
    
    modelo_json["coeficientes_variables"] = coeficientes_variables
    modelo_json["_cons"] = row_vars.get("Coef. _cons")

    for index, row in df.iterrows():
        codigo = row.iloc[0]

        if pd.notna(codigo) and pd.notna(row.get("Coef.")):
            if codigo != "VMma" and codigo != "CODIGOINTEGRADO" and not isinstance(codigo, str):
                try:
                    codigo_int = int(float(codigo))
                    modelo_json["coeficientes_municipios"][str(codigo_int)] = row["Coef."]
                except (ValueError, TypeError):
                    modelo_json["coeficientes_municipios"][str(codigo)] = row["Coef."]

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(modelo_json, f, indent=2, ensure_ascii=False)
        print(f"JSON guardado: {output_file}")

    return modelo_json

def procesar_todas_hojas(excel_file, output_prefix="modelo"):
    excel_file_obj = pd.ExcelFile(excel_file)
    hojas = excel_file_obj.sheet_names
    
    resultados = {}
    
    for hoja in hojas:
        print(f"Procesando: {hoja}")
        
        output_file = f"{output_prefix}_{hoja.replace(' ', '_').replace('.', '')}.json"
        
        try:
            modelo_json = excel_to_json(excel_file, hoja, output_file)
            resultados[hoja] = modelo_json
        except Exception as e:
            print(f"Error en {hoja}: {e}")
    
    return resultados

if __name__ == "__main__":
    excel_file = "assets/Coeficientes_modelos.xlsx"

    modelo = excel_to_json(
        excel_file=excel_file,
        sheet_name="Testigos_menos de 10.000",
        output_file="config/modelo_testigos_menos_10000.json"
    )
    
    print("Estructura generada:")
    print(json.dumps({
        "nombre_modelo": modelo["nombre_modelo"],
        "coeficientes_municipios_ejemplo": dict(list(modelo["coeficientes_municipios"].items())[:3]),
        "coeficientes_variables": modelo["coeficientes_variables"],
        "_cons": modelo["_cons"]
    }, indent=2))
    
    resultados = procesar_todas_hojas(excel_file, "config/modelo")