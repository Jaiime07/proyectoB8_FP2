import pandas as pd
from red_lineas import RedLineas
from red_estaciones import RedEstaciones
from estacion import Estacion
from linea import Linea

def imprimir_cabecera(titulo):
    print(f"\n{'='*60}")
    print(f" {titulo.upper()} ")
    print(f"{'='*60}")

def cargar_y_validar(ruta: str) -> RedLineas:
    """Carga los datos y realiza la validación de conteo del boletín."""
    df = pd.read_excel(ruta)
    mapa = {}
    print(f"{'Línea':<12} | {'Estado':<12} | {'Detalle'}")
    print("-" * 60)
    
    for _, fila in df.iterrows():
        nombre_l = str(fila['Línea'])
        nombres_e = [n.strip() for n in str(fila['Estaciones']).split(',')]
        total_excel = int(fila['Total Paradas'])
        
        # Validación requerida: coincidencia de número de estaciones
        if len(nombres_e) == total_excel:
            estado = "✅ OK"
            detalle = f"{len(nombres_e)} paradas"
        else:
            estado = "⚠️ ERROR"
            detalle = f"Excel: {total_excel} vs Real: {len(nombres_e)}"
        
        print(f"{nombre_l:<12} | {estado:<12} | {detalle}")
        mapa[nombre_l] = Linea(nombre_l, [Estacion(n) for n in nombres_e])
    
    return RedLineas(mapa)

def main():
    ruta_datos = "data/líneas_y_estaciones_Metro_Madrid.xlsx"
    
    # 1. CARGA Y VALIDACIÓN
    imprimir_cabecera("1. Carga de Datos y Validación de Integridad")
    red_madrid = cargar_y_validar(ruta_datos)
    
    # 2. PRUEBA DE RECIPROCIDAD (Igualdad vs Identidad)
    imprimir_cabecera("2. Prueba de Reciprocidad y Estructuras Duales")
    vision_est = red_madrid.to_estaciones()
    red_reconstruida = vision_est.to_lineas()
    
    print(f"¿Son el mismo objeto en memoria (Identidad 'is')?  {red_madrid is red_reconstruida}")
    print(f"¿Contienen la misma información (Igualdad '==')?    {red_madrid == red_reconstruida}")
    
    # 3. ANÁLISIS DE LA RED
    imprimir_cabecera("3. Análisis Estático de la Red")
    
    # Intercambiadores[cite: 1]
    tops, num = vision_est.estaciones_con_mas_lineas()
    print(f"Estaciones con más conexiones (Grado {num}): {', '.join(tops)}[cite: 1]")
    
    # Líneas Circulares[cite: 1]
    circulares = [n for n, l in red_madrid.mapa.items() if l.es_circular()]
    print(f"Líneas con estructura circular: {', '.join(circulares)}[cite: 1]")
    
    # 4. CONEXIDAD Y CRITICIDAD[cite: 1]
    imprimir_cabecera("4. Análisis de Conexidad y Criticidad")
    es_conexo_ini, _ = vision_est.obtener_estadisticas_conexidad(red_madrid)
    print(f"¿Es la red de Metro de Madrid conexa inicialmente? {es_conexo_ini}[cite: 1]")
    
    # Ejecutar simulación de eliminación de líneas[cite: 1]
    red_madrid.analizar_criticidad()
    
    # 5. COORDENADAS Y DISTANCIA NO EUCLÍDEA[cite: 1]
    imprimir_cabecera("5. Geolocalización y Proximidad (Haversine)")
    # Simulamos coordenadas para demostrar la funcionalidad[cite: 1]
    for linea in red_madrid.mapa.values():
        for est in linea.paradas:
            if est.nombre == "Sol": est.lat, est.lon = 40.4169, -3.7033
            if est.nombre == "Atocha": est.lat, est.lon = 40.4066, -3.6941
            if est.nombre == "Moncloa": est.lat, est.lon = 40.4352, -3.7188

    # Consulta de ejemplo[cite: 1]
    lat_user, lon_user = 40.4153, -3.7074 # Cerca de Plaza Mayor
    est_cercana, dist = vision_est.encontrar_estacion_mas_cercana(lat_user, lon_user, red_madrid)
    print(f"Desde Plaza Mayor ({lat_user}, {lon_user}):")
    print(f"La estación más cercana es {est_cercana} a {dist:.3f} km[cite: 1]")

    # 6. TRAYECTOS Y TRANSBORDOS[cite: 1]
    imprimir_cabecera("6. Planificador de Trayectos (Max 1 Transbordo)")
    casos = [
        ("Sol", "Gran Vía"),      # Directo[cite: 1]
        ("Sol", "Laguna"),        # 1 Transbordo[cite: 1]
        ("Atocha", "Moncloa")     # 1 Transbordo[cite: 1]
    ]
    
    for o, d in casos:
        print(f"\nTrayecto: {o} -> {d}")
        vision_est.buscar_ruta_un_transbordo(o, d)

    imprimir_cabecera("Fin del Informe - Boletín 8")

if __name__ == "__main__":
    main()