from typing import List
from estacion import Estacion

class Linea:
    """
    Gestiona una línea específica (ej. L1). 
    Almacena las estaciones en una LISTA porque el orden es fundamental 
    para el transporte.
    """
    def __init__(self, nombre: str, paradas: List[Estacion]):
        self.nombre: str = nombre
        self.paradas: List[Estacion] = paradas 

    def es_circular(self) -> bool:
        """
        Una línea es circular si el trayecto se cierra sobre sí mismo.
        Técnicamente: la primera y la última estación son iguales[cite: 1].
        """
        if len(self.paradas) < 2:
            return False
        return self.paradas[0] == self.paradas[-1]

    def __eq__(self, other) -> bool:
        """
        Dos líneas son iguales si se llaman igual y tienen 
        exactamente las mismas paradas en el mismo orden[cite: 1].
        """
        if not isinstance(other, Linea):
            return False
        return (self.nombre == other.nombre and 
                self.paradas == other.paradas)