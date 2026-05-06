from typing import List

from estacion import Estacion


class Linea:
    """Representa una linea de metro como lista ordenada de estaciones."""

    def __init__(self, nombre: str, paradas: List[Estacion]):
        """Inicializa nombre de linea y su secuencia de paradas."""
        self.nombre: str = nombre
        self.paradas: List[Estacion] = paradas

    def es_circular(self) -> bool:
        """Indica si la linea es circular.

        Como lo hace:
        - Una linea es circular si su primera y ultima parada coinciden.
        - Si hay menos de 2 paradas, no puede formar ciclo.
        """
        if len(self.paradas) < 2:
            return False
        return self.paradas[0] == self.paradas[-1]

    def __eq__(self, other) -> bool:
        """Compara dos lineas por nombre y orden exacto de paradas."""
        if not isinstance(other, Linea):
            return False
        return self.nombre == other.nombre and self.paradas == other.paradas
