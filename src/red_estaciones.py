from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from estacion import Estacion
from linea import Linea


class RedEstaciones:
    """Vista del grafo centrada en estaciones.

    La estructura interna guarda, para cada estacion, las lineas en las que aparece
    y las posiciones de esa estacion dentro de cada linea.
    """

    def __init__(self, mapa: Dict[str, Dict[str, List[int]]]):
        """Inicializa la vista por estaciones.

        Como lo hace:
        - Guarda directamente el diccionario recibido.
        - Formato esperado: {estacion: {linea: [posiciones]}}.
        """
        self.mapa = mapa

    def to_lineas(self):
        """Reconstruye la vista RedLineas preservando el orden de paradas.

        Como lo hace:
        - Recorre cada estacion y sus lineas.
        - Acumula pares (posicion, estacion) por nombre de linea.
        - Ordena por posicion y construye objetos Linea.
        """
        from red_lineas import RedLineas  # Import local para evitar dependencia circular.

        lineas_temp: Dict[str, List[Tuple[int, Estacion]]] = {}

        for nombre_est, dict_lineas in self.mapa.items():
            for nombre_linea, posiciones in dict_lineas.items():
                if nombre_linea not in lineas_temp:
                    lineas_temp[nombre_linea] = []
                for posicion in posiciones:
                    lineas_temp[nombre_linea].append((posicion, Estacion(nombre_est)))

        mapa_final = {}
        for nombre_linea, lista_tuplas in lineas_temp.items():
            lista_tuplas.sort(key=lambda x: x[0])
            mapa_final[nombre_linea] = Linea(nombre_linea, [tupla[1] for tupla in lista_tuplas])

        return RedLineas(mapa_final)

    def estaciones_con_mas_lineas(self) -> Tuple[List[str], int]:
        """Devuelve las estaciones con mayor numero de lineas incidentes.

        Como lo hace:
        - Calcula len(info_lineas) para cada estacion.
        - Obtiene el maximo y filtra todas las estaciones que lo alcanzan.
        """
        if not self.mapa:
            return [], 0
        maximo = max(len(info_lineas) for info_lineas in self.mapa.values())
        tops = [nombre for nombre, info in self.mapa.items() if len(info) == maximo]
        return tops, maximo

    def _resolver_nombre(self, nombre_estacion: str) -> Optional[str]:
        """Resuelve una estacion ignorando mayusculas/minusculas y espacios extremos.

        Como lo hace:
        - Normaliza la entrada a minusculas.
        - Busca una clave existente con la misma normalizacion.
        """
        nombre_normalizado = nombre_estacion.strip().lower()
        return next((k for k in self.mapa.keys() if k.lower() == nombre_normalizado), None)

    def lineas_comunes(self, estacion_a: str, estacion_b: str) -> List[str]:
        """Obtiene las lineas compartidas por dos estaciones.

        Como lo hace:
        - Resuelve nombres reales en el grafo.
        - Interseca los conjuntos de lineas de ambas estaciones.
        """
        nombre_a = self._resolver_nombre(estacion_a)
        nombre_b = self._resolver_nombre(estacion_b)

        if not nombre_a or not nombre_b:
            return []

        comunes = set(self.mapa[nombre_a].keys()) & set(self.mapa[nombre_b].keys())
        return sorted(comunes)

    def estan_en_misma_linea(self, estacion_a: str, estacion_b: str) -> bool:
        """Indica si dos estaciones comparten al menos una linea.

        Como lo hace:
        - Reutiliza lineas_comunes y comprueba si el resultado no esta vacio.
        """
        return bool(self.lineas_comunes(estacion_a, estacion_b))

    def construir_adyacencia(self, red_lin) -> Dict[str, Set[str]]:
        """Construye la lista de adyacencia del grafo de estaciones.

        Como lo hace:
        - Inicializa cada estacion con conjunto vacio.
        - Recorre cada linea y conecta paradas consecutivas en ambos sentidos.
        """
        adyacencia = {nombre_est: set() for nombre_est in self.mapa.keys()}

        for linea in red_lin.mapa.values():
            paradas = linea.paradas
            for i in range(len(paradas) - 1):
                origen = paradas[i].nombre
                destino = paradas[i + 1].nombre

                if origen in adyacencia and destino in adyacencia:
                    adyacencia[origen].add(destino)
                    adyacencia[destino].add(origen)

        return adyacencia

    def obtener_adyacentes(self, nombre_est: str, red_lin) -> Set[str]:
        """Devuelve las estaciones vecinas de una estacion dada.

        Como lo hace:
        - Construye adyacencia global.
        - Devuelve el conjunto asociado a la estacion solicitada.
        """
        adyacencia = self.construir_adyacencia(red_lin)
        return adyacencia.get(nombre_est, set())

    def obtener_grados(self, red_lin) -> Dict[str, int]:
        """Calcula el grado de cada estacion del grafo.

        Como lo hace:
        - Usa la adyacencia y cuenta vecinos por estacion.
        """
        adyacencia = self.construir_adyacencia(red_lin)
        return {estacion: len(vecinos) for estacion, vecinos in adyacencia.items()}

    def _alcanzables_desde(self, inicio: str, adyacencia: Dict[str, Set[str]]) -> Set[str]:
        """Calcula vertices alcanzables desde un origen mediante BFS.

        Como lo hace:
        - Usa cola FIFO (deque).
        - Marca visitados para no repetir nodos.
        """
        visitados = {inicio}
        cola = deque([inicio])

        while cola:
            actual = cola.popleft()
            for vecino in adyacencia[actual]:
                if vecino not in visitados:
                    visitados.add(vecino)
                    cola.append(vecino)

        return visitados

    def obtener_estadisticas_conexidad(self, red_lin) -> Tuple[bool, int]:
        """Comprueba si todo el grafo esta conectado.

        Como lo hace:
        - Construye adyacencia.
        - Ejecuta BFS desde una estacion cualquiera.
        - Compara visitados con total de estaciones.
        """
        if not self.mapa:
            return True, 0

        adyacencia = self.construir_adyacencia(red_lin)
        inicio = next(iter(adyacencia.keys()))
        visitados = self._alcanzables_desde(inicio, adyacencia)

        return len(visitados) == len(adyacencia), len(visitados)

    def analizar_eulerianidad(self, red_lin) -> Dict[str, object]:
        """Determina si el grafo admite camino o circuito euleriano.

        Como lo hace:
        - Verifica conexidad global.
        - Calcula grados de todos los vertices.
        - Cuenta vertices de grado impar y aplica el criterio clasico:
          0 impares -> circuito euleriano, 2 impares -> camino euleriano.
        """
        es_conexo, _ = self.obtener_estadisticas_conexidad(red_lin)
        grados = self.obtener_grados(red_lin)
        impares = sorted([est for est, grado in grados.items() if grado % 2 == 1])

        if not es_conexo:
            clasificacion = "No euleriano (grafo no conexo)"
        elif len(impares) == 0:
            clasificacion = "Tiene circuito euleriano"
        elif len(impares) == 2:
            clasificacion = "Tiene camino euleriano (no circuito)"
        else:
            clasificacion = "No euleriano"

        return {
            "es_conexo": es_conexo,
            "vertices_impares": impares,
            "num_impares": len(impares),
            "clasificacion": clasificacion,
            "grados": grados,
        }

    def _dfs_articulaciones(
        self,
        nodo: str,
        adyacencia: Dict[str, Set[str]],
        tiempo: List[int],
        visitado: Set[str],
        padre: Dict[str, Optional[str]],
        descubrimiento: Dict[str, int],
        bajo: Dict[str, int],
        articulaciones: Set[str],
    ) -> None:
        """DFS de Tarjan para detectar puntos de articulacion.

        Como lo hace:
        - Asigna tiempo de descubrimiento y low-link.
        - Aplica reglas de articulacion para raiz y no raiz.
        """
        visitado.add(nodo)
        descubrimiento[nodo] = tiempo[0]
        bajo[nodo] = tiempo[0]
        tiempo[0] += 1

        hijos = 0

        for vecino in adyacencia[nodo]:
            if vecino not in visitado:
                padre[vecino] = nodo
                hijos += 1
                self._dfs_articulaciones(
                    vecino,
                    adyacencia,
                    tiempo,
                    visitado,
                    padre,
                    descubrimiento,
                    bajo,
                    articulaciones,
                )

                bajo[nodo] = min(bajo[nodo], bajo[vecino])

                if padre[nodo] is None and hijos > 1:
                    articulaciones.add(nodo)
                if padre[nodo] is not None and bajo[vecino] >= descubrimiento[nodo]:
                    articulaciones.add(nodo)
            elif vecino != padre[nodo]:
                bajo[nodo] = min(bajo[nodo], descubrimiento[vecino])

    def obtener_puntos_articulacion(self, red_lin) -> List[str]:
        """Calcula estaciones de corte (articulaciones) del grafo.

        Como lo hace:
        - Construye adyacencia.
        - Ejecuta Tarjan DFS por componentes.
        - Devuelve vertices cuya eliminacion desconecta el grafo.
        """
        adyacencia = self.construir_adyacencia(red_lin)
        visitado: Set[str] = set()
        padre: Dict[str, Optional[str]] = {nodo: None for nodo in adyacencia.keys()}
        descubrimiento: Dict[str, int] = {}
        bajo: Dict[str, int] = {}
        articulaciones: Set[str] = set()
        tiempo = [0]

        for nodo in adyacencia.keys():
            if nodo not in visitado:
                self._dfs_articulaciones(
                    nodo,
                    adyacencia,
                    tiempo,
                    visitado,
                    padre,
                    descubrimiento,
                    bajo,
                    articulaciones,
                )

        return sorted(articulaciones)

    def resumen_hamiltoniano_teorico(self, red_lin) -> Dict[str, object]:
        """Genera un diagnostico teorico sobre ciclo hamiltoniano.

        Como lo hace:
        - Obtiene grados y puntos de articulacion.
        - Aplica condicion suficiente de Dirac.
        - Aplica condicion suficiente de Ore sobre pares no adyacentes.
        - Aplica condicion necesaria: un ciclo hamiltoniano no puede tener
          puntos de articulacion ni vertices de grado 1.
        """
        adyacencia = self.construir_adyacencia(red_lin)
        grados = {nodo: len(vecinos) for nodo, vecinos in adyacencia.items()}
        n = len(adyacencia)
        min_grado = min(grados.values()) if grados else 0
        articulaciones = self.obtener_puntos_articulacion(red_lin)
        tiene_grado_uno = any(grado <= 1 for grado in grados.values())

        cumple_dirac = n >= 3 and min_grado >= n / 2

        cumple_ore = n >= 3
        if cumple_ore:
            nodos = list(adyacencia.keys())
            for i in range(len(nodos)):
                for j in range(i + 1, len(nodos)):
                    u, v = nodos[i], nodos[j]
                    if v not in adyacencia[u] and grados[u] + grados[v] < n:
                        cumple_ore = False
                        break
                if not cumple_ore:
                    break

        ciclo_descartado = tiene_grado_uno or len(articulaciones) > 0

        return {
            "num_vertices": n,
            "min_grado": min_grado,
            "num_articulaciones": len(articulaciones),
            "articulaciones": articulaciones,
            "tiene_vertice_grado_1": tiene_grado_uno,
            "cumple_dirac": cumple_dirac,
            "cumple_ore": cumple_ore,
            "ciclo_hamiltoniano_descartado_por_necesaria": ciclo_descartado,
        }

    def colorear_greedy(self, red_lin) -> Dict[str, int]:
        """Colorea el grafo con estrategia greedy simple.

        Como lo hace:
        - Ordena vertices por grado descendente.
        - Para cada vertice elige el menor color no usado por vecinos.
        """
        adyacencia = self.construir_adyacencia(red_lin)
        orden = sorted(adyacencia.keys(), key=lambda nodo: len(adyacencia[nodo]), reverse=True)
        color_de: Dict[str, int] = {}

        for nodo in orden:
            usados = {color_de[v] for v in adyacencia[nodo] if v in color_de}
            color = 0
            while color in usados:
                color += 1
            color_de[nodo] = color

        return color_de

    def colorear_dsatur(self, red_lin) -> Dict[str, int]:
        """Colorea el grafo con DSATUR (heuristica avanzada).

        Como lo hace:
        - Mantiene saturacion: numero de colores distintos en vecinos coloreados.
        - Selecciona en cada paso el nodo no coloreado con mayor saturacion.
        - Desempata por mayor grado y por nombre para estabilidad.
        - Asigna el menor color valido disponible.
        """
        adyacencia = self.construir_adyacencia(red_lin)
        color_de: Dict[str, int] = {}
        grados = {nodo: len(vecinos) for nodo, vecinos in adyacencia.items()}
        saturacion: Dict[str, Set[int]] = {nodo: set() for nodo in adyacencia.keys()}

        while len(color_de) < len(adyacencia):
            candidatos = [nodo for nodo in adyacencia.keys() if nodo not in color_de]
            nodo = max(candidatos, key=lambda n: (len(saturacion[n]), grados[n], n))

            usados = {color_de[v] for v in adyacencia[nodo] if v in color_de}
            color = 0
            while color in usados:
                color += 1
            color_de[nodo] = color

            for vecino in adyacencia[nodo]:
                if vecino not in color_de:
                    saturacion[vecino].add(color)

        return color_de

    def encontrar_estacion_mas_cercana(self, lat: float, lon: float, red_lin) -> Tuple[Optional[str], float]:
        """Busca la estacion con menor distancia Haversine a un punto dado.

        Como lo hace:
        - Indexa estaciones con coordenadas disponibles (lat/lon no nulas).
        - Calcula distancia para cada una y conserva el minimo global.
        """
        mejor_estacion = None
        distancia_minima = float("inf")

        estaciones_por_nombre: Dict[str, Estacion] = {}
        for linea in red_lin.mapa.values():
            for estacion in linea.paradas:
                if estacion.nombre not in estaciones_por_nombre and (estacion.lat != 0.0 or estacion.lon != 0.0):
                    estaciones_por_nombre[estacion.nombre] = estacion

        for nombre, estacion in estaciones_por_nombre.items():
            if nombre in self.mapa:
                distancia = estacion.distancia_a(lat, lon)
                if distancia < distancia_minima:
                    distancia_minima = distancia
                    mejor_estacion = nombre

        return mejor_estacion, distancia_minima

    def buscar_ruta_un_transbordo(self, origen: str, destino: str) -> Optional[Dict[str, str]]:
        """Busca ruta entre dos estaciones con 0 o 1 transbordo.

        Como lo hace:
        - Si comparten linea, devuelve ruta directa.
        - Si no, busca una estacion que pertenezca a una linea del origen y
          otra del destino para usarla como punto de intercambio.
        """
        nombre_origen = self._resolver_nombre(origen)
        nombre_destino = self._resolver_nombre(destino)

        if not nombre_origen or not nombre_destino:
            return None

        if nombre_origen == nombre_destino:
            return {
                "tipo": "misma_estacion",
                "origen": nombre_origen,
                "destino": nombre_destino,
            }

        lineas_origen = set(self.mapa[nombre_origen].keys())
        lineas_destino = set(self.mapa[nombre_destino].keys())

        directas = sorted(lineas_origen & lineas_destino)
        if directas:
            return {
                "tipo": "directo",
                "origen": nombre_origen,
                "destino": nombre_destino,
                "linea": directas[0],
            }

        for linea_origen in sorted(lineas_origen):
            for linea_destino in sorted(lineas_destino):
                if linea_origen == linea_destino:
                    continue
                for estacion_intercambio, lineas_estacion in self.mapa.items():
                    if linea_origen in lineas_estacion and linea_destino in lineas_estacion:
                        return {
                            "tipo": "transbordo",
                            "origen": nombre_origen,
                            "destino": nombre_destino,
                            "linea_origen": linea_origen,
                            "linea_destino": linea_destino,
                            "transbordo": estacion_intercambio,
                        }

        return None

    def __eq__(self, other) -> bool:
        """Compara dos vistas de estaciones por su estructura interna."""
        if not isinstance(other, RedEstaciones):
            return False
        return self.mapa == other.mapa
