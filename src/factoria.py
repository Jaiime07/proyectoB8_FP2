import pandas as pd
from EstructuraClases import Linea, RedLineas, Estacion, RedEstaciones

def cargar_red_desde_excel(ruta_archivo: str) -> RedLineas:
    """
    Lee el archivo Excel del Metro de Madrid, valida la cantidad de paradas
    y construye el objeto RedLineas.
    """
    print(f"Cargando datos desde: {ruta_archivo}...")
    
    # 1. Leer el Excel (requiere tener instaladas las librerías pandas y openpyxl)
    try:
        df = pd.read_excel(ruta_archivo)
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo en la ruta '{ruta_archivo}'.")
        return None

    mapa_lineas = {}

    # 2. Iterar por cada fila (cada línea de metro)
    for index, row in df.iterrows():
        nombre_linea = str(row['Línea'])
        estaciones_str = str(row['Estaciones'])
        total_paradas_excel = int(row['Total Paradas'])
        
        # 3. Separar el texto de las estaciones en una lista de strings
        # Usamos split(',') y luego strip() para quitar espacios en blanco sobrantes
        nombres_estaciones = [nombre.strip() for nombre in estaciones_str.split(',')]
        
        # 4. VALIDACIÓN: Comprobar que el recuento coincide (Requisito del boletín)
        total_paradas_reales = len(nombres_estaciones)
        
        if total_paradas_reales != total_paradas_excel:
            # Si hay un error, lo notificamos claramente
            print(f"⚠️ ERROR de validación en {nombre_linea}: ")
            print(f"   - Estaciones contadas: {total_paradas_reales}")
            print(f"   - Estaciones esperadas (Columna C): {total_paradas_excel}")
        else:
            print(f"✅ {nombre_linea} validada correctamente ({total_paradas_reales} paradas).")

        # 5. Construir los objetos de nuestro dominio
        lista_objetos_estacion = [Estacion(nombre) for nombre in nombres_estaciones]
        nueva_linea = Linea(nombre=nombre_linea, paradas=lista_objetos_estacion)
        
        # 6. Almacenar en nuestro diccionario
        mapa_lineas[nombre_linea] = nueva_linea

    # 7. Devolver el contenedor final
    print("Carga finalizada.\n")
    return RedLineas(mapa_lineas)

# ==========================================
# CÓDIGO DE PRUEBA (Main)
# ==========================================
if __name__ == "__main__":
    # 1. Definimos la ruta
    ruta_excel = "data/líneas_y_estaciones_Metro_Madrid.xlsx"
    
    # 2. CREAMOS la variable red_madrid (aquí es donde se soluciona el NameError)
    red_madrid = cargar_red_desde_excel(ruta_excel)

    if red_madrid:
        print("\n--- Verificación de Reciprocidad ---")
        
        # 3. Convertimos: Líneas -> Estaciones
        vision_estaciones = red_madrid.to_estaciones()
        
        # 4. Convertimos: Estaciones -> Líneas[cite: 1]
        red_reconstruida = vision_estaciones.to_lineas()
        
        # 5. Las pruebas de fuego:
        print(f"¿Identidad (is)? {red_madrid is red_reconstruida}") # False
        print(f"¿Igualdad (==)? {red_madrid == red_reconstruida}") # True[cite: 1]
        
        if red_madrid == red_reconstruida:
            print("✨ ¡Éxito! La conversión es 100% recíproca.")
        else:
            print("❌ Algo falló en la comparación lógica.")