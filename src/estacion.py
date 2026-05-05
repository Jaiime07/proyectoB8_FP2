import math

class Estacion:
    """
    Representa una parada con su ubicación geográfica exacta.
    """
    def __init__(self, nombre: str, lat: float = 0.0, lon: float = 0.0):
        self.nombre: str = nombre
        self.lat: float = lat
        self.lon: float = lon
    
    def distancia_a(self, lat2: float, lon2: float) -> float:
        """
        Calcula la distancia en kilómetros usando la fórmula de Haversine.
        Es más precisa que la euclídea para la Tierra.
        """
        # Radio de la Tierra en kilómetros
        R = 6371.0 
        
        # Convertir grados a radianes
        phi1, phi2 = math.radians(self.lat), math.radians(lat2)
        dphi = math.radians(lat2 - self.lat)
        dlambda = math.radians(lon2 - self.lon)
        
        # Fórmula de Haversine
        a = math.sin(dphi / 2)**2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def __eq__(self, other) -> bool:
        if not isinstance(other, Estacion): return False
        return self.nombre == other.nombre

    def __hash__(self):
        return hash(self.nombre)

    def __repr__(self):
        return f"Estacion({self.nombre}, Lat: {self.lat}, Lon: {self.lon})"