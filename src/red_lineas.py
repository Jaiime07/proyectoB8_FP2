from typing import Dict, List
from linea import Linea
from estacion import Estacion

class RedLineas:
    """
    Contenedor global que organiza el metro por líneas.
    Estructura: { "Linea 1": ObjetoLinea1, ... }[cite: 1]
    """
    def __init__(self, mapa_lineas: Dict[str, Linea]):
        self.mapa: Dict[str, Linea] = mapa_lineas

    def to_estaciones(self):
        """
        TRANSFORMACIÓN: Convierte esta visión en una 'RedEstaciones'.
        Recorre cada línea y anota en qué posición aparece cada estación[cite: 1].
        """
        # Import local para evitar 'Circular Import Error'
        from red_estaciones import RedEstaciones 
        
        mapa_est = {}
        for nombre_linea, linea_obj in self.mapa.items():
            for pos, est in enumerate(linea_obj.paradas):
                if est.nombre not in mapa_est:
                    mapa_est[est.nombre] = {}
                
                # Guardamos la posición para poder reconstruir el orden después
                if nombre_linea not in mapa_est[est.nombre]:
                    mapa_est[est.nombre][nombre_linea] = []
                mapa_est[est.nombre][nombre_linea].append(pos)
                
        return RedEstaciones(mapa_est)

    def eliminar_linea(self, nombre_linea: str) -> 'RedLineas':
        """
        Crea una copia de la red SIN una línea específica. 
        Útil para el análisis de criticidad y conexidad[cite: 1].
        """
        nuevo_mapa = {k: v for k, v in self.mapa.items() if k != nombre_linea}
        return RedLineas(nuevo_mapa)

    def __eq__(self, other) -> bool:
        """Compara si dos redes tienen el mismo contenido[cite: 1]."""
        if not isinstance(other, RedLineas):
            return False
        return self.mapa == other.mapa
    
    def analizar_criticidad(self):
        """
        Simula la eliminación de cada línea y calcula el impacto en la red.
        Calcula cuántas estaciones quedarían aisladas del componente principal.
        """
        print(f"\n{'LÍNEA':<15} | {'¿CONEXO?':<10} | {'EST. AISLADAS':<15} | {'CRITICIDAD (%)'}")
        print("-" * 65)
        
        total_estaciones_global = len(self.to_estaciones().mapa)
        
        for nombre_linea in self.mapa.keys():
            # 1. Creamos una copia de la red sin esta línea
            red_reducida = self.eliminar_linea(nombre_linea)
            
            # 2. Generamos la visión de estaciones de la red resultante
            vision_est_reducida = red_reducida.to_estaciones()
            
            # 3. Calculamos la conexidad
            # Nota: Necesitamos que es_conexo nos devuelva cuántas estaciones alcanzó
            conexo, estaciones_alcanzadas = vision_est_reducida.obtener_estadisticas_conexidad(red_reducida)
            
            # 4. Cálculo de estaciones aisladas
            # Las estaciones que no están en el componente principal
            aisladas = total_estaciones_global - estaciones_alcanzadas
            proporcion = (aisladas / total_estaciones_global) * 100
            
            print(f"{nombre_linea:<15} | {str(conexo):<10} | {aisladas:<15} | {proporcion:.2f}%")