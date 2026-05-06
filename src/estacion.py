import math


class Estacion:
    """Entidad de dominio para una estacion con nombre y coordenadas."""

    def __init__(self, nombre: str, lat: float = 0.0, lon: float = 0.0):
        """Inicializa nombre y coordenadas geograficas de la estacion."""
        self.nombre: str = nombre
        self.lat: float = lat
        self.lon: float = lon

    def distancia_a(self, lat2: float, lon2: float) -> float:
        """Calcula distancia a otro punto con formula de Haversine.

        Como lo hace:
        - Convierte grados a radianes.
        - Aplica la formula sobre una esfera de radio medio terrestre.
        - Devuelve distancia en kilometros.
        """
        radio_tierra_km = 6371.0

        phi1 = math.radians(self.lat)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - self.lat)
        dlambda = math.radians(lon2 - self.lon)

        a = (
            math.sin(dphi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radio_tierra_km * c

    def __eq__(self, other) -> bool:
        """Define igualdad logica por nombre de estacion."""
        if not isinstance(other, Estacion):
            return False
        return self.nombre == other.nombre

    def __hash__(self):
        """Permite usar estaciones en sets/dicts mediante hash por nombre."""
        return hash(self.nombre)

    def __repr__(self):
        """Representacion legible para depuracion."""
        return f"Estacion({self.nombre}, Lat: {self.lat}, Lon: {self.lon})"
