import unicodedata
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import pandas as pd

from estacion import Estacion
from linea import Linea
from red_lineas import RedLineas


def normalizar_texto(texto: str) -> str:
    """Normaliza texto para comparaciones robustas.

    Como lo hace:
    - Convierte a minusculas.
    - Elimina tildes y signos diacriticos.
    - Quita espacios al principio y al final.
    """
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def resolver_columna(df: pd.DataFrame, candidatos: Sequence[str]) -> str:
    """Busca la columna real de un DataFrame a partir de aliases.

    Como lo hace:
    - Normaliza el nombre de cada columna del Excel.
    - Devuelve la primera coincidencia con los aliases esperados.
    - Lanza error explicito si no encuentra ninguna.
    """
    mapa = {normalizar_texto(col): col for col in df.columns}

    for candidato in candidatos:
        clave = normalizar_texto(candidato)
        if clave in mapa:
            return mapa[clave]

    raise KeyError(f"No se encontro ninguna columna compatible con: {candidatos}")


def imprimir_seccion(titulo: str) -> None:
    """Imprime una cabecera visual para separar bloques del informe."""
    print("\n" + "=" * 88)
    print(titulo)
    print("=" * 88)


def imprimir_contexto(texto: str) -> None:
    """Imprime una nota explicativa corta para interpretar resultados."""
    print(f"[INFO] {texto}")


def imprimir_tabla(cabeceras: Sequence[str], filas: Sequence[Tuple[object, ...]]) -> None:
    """Imprime una tabla ASCII con ancho automatico por columna.

    Como lo hace:
    - Calcula ancho maximo entre cabecera y celdas.
    - Renderiza separadores y filas alineadas a la izquierda.
    """
    anchos = [len(str(cabecera)) for cabecera in cabeceras]
    for fila in filas:
        for i, valor in enumerate(fila):
            anchos[i] = max(anchos[i], len(str(valor)))

    separador = "+-" + "-+-".join("-" * ancho for ancho in anchos) + "-+"
    print(separador)
    print("| " + " | ".join(f"{str(cabeceras[i]):<{anchos[i]}}" for i in range(len(cabeceras))) + " |")
    print(separador)
    for fila in filas:
        print("| " + " | ".join(f"{str(fila[i]):<{anchos[i]}}" for i in range(len(fila))) + " |")
    print(separador)


def cargar_y_validar(ruta_excel: str) -> Tuple[RedLineas, List[Tuple[str, str, str]]]:
    """Carga el Excel y valida el numero de paradas por linea.

    Como lo hace:
    - Detecta columnas con nombres robustos ante tildes/codificacion.
    - Separa las estaciones de cada fila por comas.
    - Compara conteo calculado contra la columna "Total Paradas".
    - Construye objetos de dominio (Estacion, Linea, RedLineas).
    """
    df = pd.read_excel(ruta_excel)

    col_linea = resolver_columna(df, ["Linea", "Línea"])
    col_estaciones = resolver_columna(df, ["Estaciones"])
    col_total = resolver_columna(df, ["Total Paradas", "Total"])

    mapa_lineas: Dict[str, Linea] = {}
    filas_validacion: List[Tuple[str, str, str]] = []

    for _, fila in df.iterrows():
        nombre_linea = str(fila[col_linea]).strip()
        nombres_estaciones = [nombre.strip() for nombre in str(fila[col_estaciones]).split(",")]
        total_excel = int(fila[col_total])
        total_real = len(nombres_estaciones)

        estado = "OK" if total_real == total_excel else "ERROR"
        detalle = f"Excel={total_excel}, calculado={total_real}"
        filas_validacion.append((nombre_linea, estado, detalle))

        mapa_lineas[nombre_linea] = Linea(nombre_linea, [Estacion(nombre) for nombre in nombres_estaciones])

    return RedLineas(mapa_lineas), filas_validacion


def texto_bool(valor: bool) -> str:
    """Convierte un booleano a SI/NO para la salida del informe."""
    return "SI" if valor else "NO"


def asignar_coordenadas(red_lineas: RedLineas, coordenadas: Dict[str, Tuple[float, float]]) -> int:
    """Asigna coordenadas a estaciones conocidas por nombre.

    Como lo hace:
    - Recorre todas las estaciones de todas las lineas.
    - Si el nombre existe en el diccionario de coordenadas, actualiza lat/lon.
    - Devuelve cuantas asignaciones realizo.
    """
    contador = 0
    for linea in red_lineas.mapa.values():
        for estacion in linea.paradas:
            if estacion.nombre in coordenadas:
                lat, lon = coordenadas[estacion.nombre]
                estacion.lat = lat
                estacion.lon = lon
                contador += 1
    return contador


def analizar_criticidad(red_lineas: RedLineas):
    """Evalua el impacto de eliminar cada linea sobre la conectividad global.

    Como lo hace:
    - Para cada linea, construye una red reducida sin ella.
    - Mide estaciones alcanzables en la componente principal.
    - Calcula estaciones aisladas y dos porcentajes de criticidad.
    """
    total_estaciones = len(red_lineas.to_estaciones().mapa)
    resultados = []

    for nombre_linea, linea in sorted(red_lineas.mapa.items()):
        red_reducida = red_lineas.eliminar_linea(nombre_linea)
        vision_reducida = red_reducida.to_estaciones()
        conexo_reducida, alcanzadas = vision_reducida.obtener_estadisticas_conexidad(red_reducida)

        aisladas = total_estaciones - alcanzadas
        # Criterio del boletin: al quitar una linea no desaparecen estaciones,
        # simplemente pueden quedar aisladas. Por tanto, la red solo se
        # considera conexa si no queda ninguna aislada.
        conexo_total = aisladas == 0
        proporcion_red = (aisladas / total_estaciones * 100) if total_estaciones else 0.0
        proporcion_linea = (aisladas / len(linea.paradas) * 100) if linea.paradas else 0.0

        resultados.append(
            {
                "linea": nombre_linea,
                "conexo": conexo_total,
                "conexo_reducida": conexo_reducida,
                "aisladas": aisladas,
                "proporcion_red": proporcion_red,
                "proporcion_linea": proporcion_linea,
            }
        )

    resultados.sort(key=lambda r: (r["aisladas"], r["proporcion_red"]), reverse=True)
    return resultados


def describir_ruta(resultado_ruta) -> str:
    """Traduce la estructura de ruta a texto legible para consola."""
    if not resultado_ruta:
        return "No hay ruta con 1 transbordo o menos"

    tipo = resultado_ruta["tipo"]
    if tipo == "misma_estacion":
        return "Origen y destino son la misma estacion"
    if tipo == "directo":
        return f"Directo por {resultado_ruta['linea']}"
    if tipo == "transbordo":
        return (
            f"{resultado_ruta['linea_origen']} -> transbordo en {resultado_ruta['transbordo']} -> "
            f"{resultado_ruta['linea_destino']}"
        )
    return "Ruta no disponible"


def resumen_colores(colores: Dict[str, int]) -> Dict[int, int]:
    """Cuenta cuantas estaciones tiene cada color de una coloracion dada."""
    conteo: Dict[int, int] = {}
    for color in colores.values():
        conteo[color] = conteo.get(color, 0) + 1
    return dict(sorted(conteo.items()))


def resolver_ruta_excel() -> str:
    """Localiza el Excel de entrada en la carpeta data.

    Como lo hace:
    - Primero prueba dos rutas frecuentes (con y sin tilde).
    - Si fallan, busca cualquier .xlsx con palabras clave del enunciado.
    - Como ultimo recurso, usa el primer .xlsx disponible.
    """
    candidatas = [
        Path("data/líneas_y_estaciones_Metro_Madrid.xlsx"),
        Path("data/lineas_y_estaciones_Metro_Madrid.xlsx"),
    ]

    for ruta in candidatas:
        if ruta.exists():
            return str(ruta)

    xlsx_data = sorted(Path("data").glob("*.xlsx"))
    for ruta in xlsx_data:
        nombre = normalizar_texto(ruta.name)
        if "metro" in nombre and "estaciones" in nombre:
            return str(ruta)

    if xlsx_data:
        return str(xlsx_data[0])

    raise FileNotFoundError("No se encontro ningun archivo Excel .xlsx en la carpeta data.")


def main() -> None:
    """Ejecuta un informe integral del Boletin 8 + analisis avanzados de grafos."""
    ruta_datos = resolver_ruta_excel()

    imprimir_seccion("1) Carga y validacion de datos")
    imprimir_contexto(
        "Comparamos el numero de paradas declarado en el Excel con el numero de paradas realmente leidas en cada linea."
    )
    red_madrid, filas_validacion = cargar_y_validar(ruta_datos)
    imprimir_tabla(["Linea", "Estado", "Detalle"], filas_validacion)

    errores = [fila for fila in filas_validacion if fila[1] == "ERROR"]
    print(f"Lineas leidas: {len(red_madrid.mapa)}")
    print(f"Lineas con error de conteo: {len(errores)}")
    if errores:
        print("Interpretacion: hay lineas con datos inconsistentes en el origen (requieren revision del Excel).")
    else:
        print("Interpretacion: los datos de entrada son consistentes para todas las lineas.")

    imprimir_seccion("2) Doble vision del grafo y reciprocidad")
    imprimir_contexto(
        "Transformamos la red Lineas -> Estaciones -> Lineas para comprobar que no se pierde informacion estructural."
    )
    vision_estaciones = red_madrid.to_estaciones()
    red_reconstruida = vision_estaciones.to_lineas()

    filas_reciprocidad = [
        ("Numero de lineas", len(red_madrid.mapa)),
        ("Numero de estaciones unicas", len(vision_estaciones.mapa)),
        ("Identidad (is)", red_madrid is red_reconstruida),
        ("Igualdad (==)", red_madrid == red_reconstruida),
    ]
    imprimir_tabla(["Comprobacion", "Resultado"], filas_reciprocidad)
    print("Interpretacion: 'is' suele ser NO (objeto distinto), pero '==' debe ser SI (contenido equivalente).")

    imprimir_seccion("3) Consultas basicas de la red")
    imprimir_contexto(
        "Mostramos indicadores rapidos de estructura: intercambiadores, lineas circulares y estaciones que comparten linea."
    )
    estaciones_top, grado = vision_estaciones.estaciones_con_mas_lineas()
    print(f"Estaciones con mas lineas ({grado}): {', '.join(estaciones_top)}")

    lineas_circulares = sorted([nombre for nombre, linea in red_madrid.mapa.items() if linea.es_circular()])
    print("Lineas circulares:", ", ".join(lineas_circulares) if lineas_circulares else "Ninguna")

    casos_misma_linea = [
        ("Sol", "Gran Vía"),
        ("Sol", "Laguna"),
        ("Moncloa", "Argüelles"),
    ]
    filas_misma_linea = []
    for origen, destino in casos_misma_linea:
        comunes = vision_estaciones.lineas_comunes(origen, destino)
        filas_misma_linea.append((f"{origen} <-> {destino}", texto_bool(bool(comunes)), ", ".join(comunes) or "-"))

    imprimir_tabla(["Pareja", "Comparten linea", "Lineas"], filas_misma_linea)
    print("Interpretacion: si 'Comparten linea' es SI, existe trayecto directo sin transbordo entre esa pareja.")

    imprimir_seccion("4) Conexidad y criticidad")
    imprimir_contexto(
        "Comprobamos si toda la red esta conectada y medimos el impacto de quitar cada linea (estaciones que quedan fuera)."
    )
    es_conexa, visitadas = vision_estaciones.obtener_estadisticas_conexidad(red_madrid)
    print(f"Red inicial conexa: {texto_bool(es_conexa)} ({visitadas}/{len(vision_estaciones.mapa)} estaciones alcanzadas)")

    criticidad = analizar_criticidad(red_madrid)
    filas_criticidad = [
        (
            item["linea"],
            texto_bool(item["conexo"]),
            item["aisladas"],
            f"{item['proporcion_red']:.2f}%",
            f"{item['proporcion_linea']:.2f}%",
        )
        for item in criticidad
    ]
    imprimir_tabla(
        ["Linea eliminada", "Sigue conexa", "Est. aisladas", "% sobre red", "% sobre paradas linea"],
        filas_criticidad,
    )

    lineas_no_criticas = sorted([item["linea"] for item in criticidad if item["conexo"]])
    print("Lineas que se pueden eliminar sin romper la conexidad:", ", ".join(lineas_no_criticas) or "Ninguna")

    if criticidad:
        mas_critica = criticidad[0]
        print(
            "Linea mas critica:",
            f"{mas_critica['linea']} ({mas_critica['aisladas']} estaciones aisladas, {mas_critica['proporcion_red']:.2f}% de la red)",
        )
    print("Interpretacion: cuanto mayor sea 'Est. aisladas', mas dependiente es la red de esa linea.")

    imprimir_seccion("5) Coordenadas y estacion mas cercana (Haversine)")
    imprimir_contexto(
        "Asignamos coordenadas de ejemplo y usamos distancia geodesica (Haversine) para buscar la estacion mas proxima."
    )
    coordenadas = {
        "Sol": (40.4169, -3.7033),
        "Gran Vía": (40.4200, -3.7056),
        "Atocha – Renfe": (40.4066, -3.6890),
        "Moncloa": (40.4352, -3.7188),
        "Nuevos Ministerios": (40.4464, -3.6924),
        "Príncipe Pío": (40.4200, -3.7202),
        "Plaza de España": (40.4238, -3.7113),
        "Cuatro Caminos": (40.4470, -3.7038),
    }
    actualizadas = asignar_coordenadas(red_madrid, coordenadas)
    print(f"Estaciones con coordenadas cargadas en objetos de linea: {actualizadas}")

    lat_comercio, lon_comercio = 40.4155, -3.7074  # Zona Plaza Mayor.
    estacion_cercana, distancia = vision_estaciones.encontrar_estacion_mas_cercana(lat_comercio, lon_comercio, red_madrid)

    if estacion_cercana:
        print(f"Ubicacion comercio: ({lat_comercio}, {lon_comercio})")
        print(f"Estacion mas cercana: {estacion_cercana} ({distancia:.3f} km)")
        print("Interpretacion: esta consulta simula un recomendador de estacion para un punto de interes.")
    else:
        print("No hay estaciones con coordenadas para calcular cercania")

    imprimir_seccion("6) Trayectos con 0 o 1 transbordo")
    imprimir_contexto(
        "Para cada par origen-destino mostramos si hay ruta directa o con un unico transbordo, indicando lineas implicadas."
    )
    casos_ruta = [
        ("Sol", "Gran Vía"),
        ("Sol", "Laguna"),
        ("Atocha – Renfe", "Moncloa"),
        ("Sol", "Puerta del Sur"),
    ]

    filas_ruta = []
    for origen, destino in casos_ruta:
        ruta = vision_estaciones.buscar_ruta_un_transbordo(origen, destino)
        filas_ruta.append((f"{origen} -> {destino}", describir_ruta(ruta)))

    imprimir_tabla(["Caso", "Resultado"], filas_ruta)
    print("Interpretacion: si no hay ruta, el par necesita mas de 1 transbordo (o no existe en datos).")

    imprimir_seccion("7) Analisis avanzado: Euler, Hamilton y coloracion")
    imprimir_contexto(
        "Aplicamos criterios clasicos de teoria de grafos: eulerianidad, condiciones hamiltonianas y coloracion valida."
    )

    euler = vision_estaciones.analizar_eulerianidad(red_madrid)
    muestra_impares = ", ".join(euler["vertices_impares"][:8])
    if len(euler["vertices_impares"]) > 8:
        muestra_impares += ", ..."
    filas_euler = [
        ("Conexo", texto_bool(euler["es_conexo"])),
        ("Numero de vertices impares", euler["num_impares"]),
        ("Clasificacion", euler["clasificacion"]),
        ("Muestra vertices impares", muestra_impares or "Ninguno"),
    ]
    imprimir_tabla(["Metricas eulerianas", "Valor"], filas_euler)
    print(
        "Interpretacion Euler: 0 impares -> circuito euleriano, 2 impares -> camino euleriano, mas de 2 -> no euleriano."
    )

    hamilton = vision_estaciones.resumen_hamiltoniano_teorico(red_madrid)
    filas_hamilton = [
        ("Numero de vertices", hamilton["num_vertices"]),
        ("Grado minimo", hamilton["min_grado"]),
        ("Cumple Dirac (suficiente)", texto_bool(hamilton["cumple_dirac"])),
        ("Cumple Ore (suficiente)", texto_bool(hamilton["cumple_ore"])),
        ("Tiene vertice de grado <= 1", texto_bool(hamilton["tiene_vertice_grado_1"])),
        ("Numero de articulaciones", hamilton["num_articulaciones"]),
        (
            "Ciclo hamiltoniano descartado por condicion necesaria",
            texto_bool(hamilton["ciclo_hamiltoniano_descartado_por_necesaria"]),
        ),
    ]
    imprimir_tabla(["Chequeo hamiltoniano", "Valor"], filas_hamilton)

    if hamilton["articulaciones"]:
        print("Muestra de articulaciones:", ", ".join(hamilton["articulaciones"][:10]))
    print("Interpretacion Hamilton: Dirac/Ore son condiciones suficientes; articulaciones y grado 1 descartan ciclo.")

    colores_greedy = vision_estaciones.colorear_greedy(red_madrid)
    colores_dsatur = vision_estaciones.colorear_dsatur(red_madrid)
    resumen_greedy = resumen_colores(colores_greedy)
    resumen_dsatur = resumen_colores(colores_dsatur)

    filas_coloracion = [
        ("Greedy", max(colores_greedy.values()) + 1 if colores_greedy else 0, resumen_greedy),
        ("DSATUR", max(colores_dsatur.values()) + 1 if colores_dsatur else 0, resumen_dsatur),
    ]
    imprimir_tabla(["Algoritmo", "Numero de colores", "Distribucion color:estaciones"], filas_coloracion)
    print(
        "Interpretacion coloracion: estaciones adyacentes no comparten color; menos colores suele indicar mejor calidad."
    )


if __name__ == "__main__":
    main()
