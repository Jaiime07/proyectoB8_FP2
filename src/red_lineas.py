from typing import Dict

from linea import Linea


class RedLineas:
    """Vista del dominio centrada en lineas de metro.

    Guarda cada linea con sus paradas ordenadas, lo que permite modelar
    directamente el recorrido real de la red.
    """

    def __init__(self, mapa_lineas: Dict[str, Linea]):
        """Inicializa la red con un diccionario {nombre_linea: Linea}."""
        self.mapa: Dict[str, Linea] = mapa_lineas

    def to_estaciones(self):
        """Convierte la vista por lineas en una vista por estaciones.

        Como lo hace:
        - Recorre todas las lineas y sus paradas con su indice.
        - Para cada estacion, registra en que linea aparece y en que posiciones.
        """
        from red_estaciones import RedEstaciones  # Import local para evitar dependencia circular.

        mapa_estaciones = {}
        for nombre_linea, linea_obj in self.mapa.items():
            for posicion, estacion in enumerate(linea_obj.paradas):
                if estacion.nombre not in mapa_estaciones:
                    mapa_estaciones[estacion.nombre] = {}
                if nombre_linea not in mapa_estaciones[estacion.nombre]:
                    mapa_estaciones[estacion.nombre][nombre_linea] = []
                mapa_estaciones[estacion.nombre][nombre_linea].append(posicion)

        return RedEstaciones(mapa_estaciones)

    def eliminar_linea(self, nombre_linea: str) -> "RedLineas":
        """Devuelve una copia de la red sin la linea indicada.

        Como lo hace:
        - Filtra el diccionario original excluyendo la clave solicitada.
        - Construye una nueva instancia RedLineas con el resultado.
        """
        nuevo_mapa = {nombre: linea for nombre, linea in self.mapa.items() if nombre != nombre_linea}
        return RedLineas(nuevo_mapa)

    def __eq__(self, other) -> bool:
        """Compara dos redes por igualdad estructural de su mapa."""
        if not isinstance(other, RedLineas):
            return False
        return self.mapa == other.mapa
