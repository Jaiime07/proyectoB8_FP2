from typing import Dict, List, Tuple, Set
from collections import deque
from estacion import Estacion
from linea import Linea  
class RedEstaciones:
    """
    Visión 'Estaciones': Organiza el grafo por paradas (Adyacencia).
    Ideal para algoritmos de búsqueda, conexidad y cercanía.
    """
    def __init__(self, mapa: Dict[str, Dict[str, List[int]]]):
        # Estructura: {nombre_estacion: {nombre_linea: [posiciones]}}[cite: 1]
        self.mapa = mapa

    def to_lineas(self):
        """
        RECIPROCIDAD: Reconstruye la 'RedLineas' original[cite: 1].
        Usa las posiciones guardadas para asegurar que el orden sea correcto.
        """
        from red_lineas import RedLineas # Import local para evitar importación circular
        lineas_temp = {}
        
        for nombre_est, dict_lineas in self.mapa.items():
            for nombre_linea, posiciones in dict_lineas.items():
                if nombre_linea not in lineas_temp:
                    lineas_temp[nombre_linea] = []
                for p in posiciones:
                    lineas_temp[nombre_linea].append((p, Estacion(nombre_est)))
        
        mapa_final = {}
        for nombre_linea, lista_tuplas in lineas_temp.items():
            # Ordenamos por la posición original (p)
            lista_tuplas.sort(key=lambda x: x[0])
            # Creamos el objeto Linea con las estaciones ya ordenadas[cite: 1]
            mapa_final[nombre_linea] = Linea(nombre_linea, [t[1] for t in lista_tuplas])
            
        return RedLineas(mapa_final)

    def estaciones_con_mas_lineas(self) -> Tuple[List[str], int]:
        """Identifica los nodos de mayor grado (intercambiadores)[cite: 1]."""
        if not self.mapa: return [], 0
        max_l = max(len(info_lineas) for info_lineas in self.mapa.values())
        tops = [nom for nom, info in self.mapa.items() if len(info) == max_l]
        return tops, max_l

    def obtener_adyacentes(self, nombre_est: str, red_lin) -> Set[str]:
        """Busca las paradas vecinas en todas las líneas que pasan por aquí[cite: 1]."""
        vecinos = set()
        lineas_pasan = self.mapa.get(nombre_est, {}).keys()
        for nom_linea in lineas_pasan:
            linea_obj = red_lin.mapa[nom_linea]
            for i, est in enumerate(linea_obj.paradas):
                if est.nombre == nombre_est:
                    if i > 0: vecinos.add(linea_obj.paradas[i-1].nombre)
                    if i < len(linea_obj.paradas) - 1: vecinos.add(linea_obj.paradas[i+1].nombre)
        return vecinos

    def obtener_estadisticas_conexidad(self, red_lin) -> Tuple[bool, int]:
        """Realiza un BFS para ver si todas las estaciones son alcanzables[cite: 1]."""
        nombres_est = list(self.mapa.keys())
        if not nombres_est: return True, 0
        
        visitados = {nombres_est[0]}
        cola = deque([nombres_est[0]])
        
        while cola:
            actual = cola.popleft()
            for v in self.obtener_adyacentes(actual, red_lin):
                if v not in visitados:
                    visitados.add(v)
                    cola.append(v)
        
        return len(visitados) == len(self.mapa), len(visitados)

    def encontrar_estacion_mas_cercana(self, lat: float, lon: float, red_lin) -> Tuple[str, float]:
        """Usa la fórmula de Haversine para hallar la estación más próxima[cite: 1]."""
        mejor_est = None
        dist_min = float('inf')
        
        for nombre in self.mapa.keys():
            # Buscamos el objeto Estacion en la red de líneas para obtener sus coordenadas
            est_obj = next((e for l in red_lin.mapa.values() for e in l.paradas if e.nombre == nombre), None)
            if est_obj and est_obj.lat != 0.0:
                d = est_obj.distancia_a(lat, lon)
                if d < dist_min:
                    dist_min, mejor_est = d, nombre
        return mejor_est, dist_min

    def buscar_ruta_un_transbordo(self, origen: str, destino: str):
        """Busca trayectos permitiendo pequeñas variaciones en el nombre."""
        # Normalizamos la búsqueda: quitamos espacios y pasamos a minúsculas
        orig_norm = origen.strip().lower()
        dest_norm = destino.strip().lower()
        
        # Encontramos la clave real en el diccionario que coincida
        nombre_real_origen = next((k for k in self.mapa.keys() if k.lower() == orig_norm), None)
        nombre_real_destino = next((k for k in self.mapa.keys() if k.lower() == dest_norm), None)

        if not nombre_real_origen or not nombre_real_destino:
            print(f"❌ Error: No se encontró '{origen}' o '{destino}' en la base de datos.")
            return

        # Una vez encontrados los nombres exactos, usamos la lógica anterior...
        l_orig = set(self.mapa[nombre_real_origen].keys())
        l_dest = set(self.mapa[nombre_real_destino].keys())
        
        # (Resto del código de transbordos...)
    def __eq__(self, other) -> bool:
        if not isinstance(other, RedEstaciones): return False
        return self.mapa == other.mapa