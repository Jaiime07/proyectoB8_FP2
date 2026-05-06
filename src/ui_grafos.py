import random
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List, Optional, Sequence, Set, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from linea import Linea
from main import cargar_y_validar, resolver_ruta_excel, texto_bool
from red_lineas import RedLineas


def construir_lista_adyacencia(red_lineas: RedLineas) -> Dict[str, Set[str]]:
    """Construye adyacencia estacion->vecinos para toda la red.

    Como lo hace:
    - Inicializa todas las estaciones detectadas en la vista por estaciones.
    - Recorre cada linea y conecta paradas consecutivas en ambos sentidos.
    """
    vision = red_lineas.to_estaciones()
    adyacencia = {nombre: set() for nombre in vision.mapa.keys()}

    for linea in red_lineas.mapa.values():
        for i in range(len(linea.paradas) - 1):
            origen = linea.paradas[i].nombre
            destino = linea.paradas[i + 1].nombre
            adyacencia[origen].add(destino)
            adyacencia[destino].add(origen)

    return adyacencia


def lista_a_aristas(adyacencia: Dict[str, Set[str]]) -> List[Tuple[str, str]]:
    """Convierte adyacencia en lista de aristas sin duplicados."""
    aristas = set()
    for origen, vecinos in adyacencia.items():
        for destino in vecinos:
            aristas.add(tuple(sorted((origen, destino))))
    return sorted(aristas)


def layout_circular(nodos: Sequence[str]) -> Dict[str, np.ndarray]:
    """Calcula posicion circular para cada nodo.

    Como lo hace:
    - Distribuye nodos uniformemente en [0, 2pi).
    - Usa cos/sin para obtener coordenadas en un circulo unitario.
    """
    total = len(nodos)
    if total == 0:
        return {}

    posiciones = {}
    for i, nodo in enumerate(nodos):
        angulo = 2 * np.pi * i / total
        posiciones[nodo] = np.array([np.cos(angulo), np.sin(angulo)], dtype=float)
    return posiciones


def layout_force_directed(
    nodos: Sequence[str],
    aristas: Sequence[Tuple[str, str]],
    iteraciones: int = 180,
    semilla: int = 42,
) -> Dict[str, np.ndarray]:
    """Calcula un layout por fuerzas tipo Fruchterman-Reingold simplificado.

    Como lo hace:
    - Inicializa nodos en posiciones aleatorias reproducibles.
    - Aplica fuerzas de repulsion entre todos los nodos.
    - Aplica fuerzas de atraccion sobre nodos conectados por arista.
    - Enfria el sistema gradualmente para estabilizar posiciones.
    """
    total = len(nodos)
    if total == 0:
        return {}
    if total == 1:
        return {nodos[0]: np.array([0.0, 0.0], dtype=float)}

    random.seed(semilla)
    np.random.seed(semilla)

    indice = {nodo: i for i, nodo in enumerate(nodos)}
    pos = np.random.rand(total, 2) - 0.5

    area = 1.0
    k = np.sqrt(area / total)
    temperatura = 0.15

    for _ in range(iteraciones):
        desplazamiento = np.zeros((total, 2), dtype=float)

        # Repulsion global O(V^2).
        delta = pos[:, None, :] - pos[None, :, :]
        distancias = np.linalg.norm(delta, axis=2) + 1e-9
        repulsion = (k * k) / distancias
        direccion = delta / distancias[:, :, None]
        desplazamiento += np.sum(direccion * repulsion[:, :, None], axis=1)

        # Atraccion sobre aristas O(E).
        for u, v in aristas:
            i = indice[u]
            j = indice[v]
            vector = pos[i] - pos[j]
            distancia = np.linalg.norm(vector) + 1e-9
            fuerza = (distancia * distancia) / k
            direccion_uv = vector / distancia
            desplazamiento[i] -= direccion_uv * fuerza
            desplazamiento[j] += direccion_uv * fuerza

        norma = np.linalg.norm(desplazamiento, axis=1) + 1e-9
        paso = np.minimum(norma, temperatura)[:, None]
        pos += (desplazamiento / norma[:, None]) * paso

        temperatura *= 0.98

    return {nodo: pos[indice[nodo]] for nodo in nodos}


def color_por_mapa(colores: Optional[Dict[str, int]], nodos: Sequence[str]) -> List[str]:
    """Convierte un mapa nodo->id_color en colores hex para Matplotlib."""
    if not colores:
        return ["#4f81bd" for _ in nodos]

    paleta = list(plt.get_cmap("tab20").colors)
    resultado = []
    for nodo in nodos:
        color_id = colores.get(nodo, 0)
        resultado.append(paleta[color_id % len(paleta)])
    return resultado


class AplicacionGrafo:
    """Interfaz para visualizar grafos de la red del Metro de Madrid."""

    def __init__(self, raiz: tk.Tk):
        """Inicializa UI, carga datos y prepara eventos.

        Como lo hace:
        - Carga la red desde Excel reutilizando la logica del proyecto.
        - Crea controles de seleccion de vista.
        - Embebe una figura Matplotlib dentro de Tkinter.
        """
        self.raiz = raiz
        self.raiz.title("Visualizador de Grafos - Metro de Madrid")
        self.raiz.geometry("1280x800")

        ruta_excel = resolver_ruta_excel()
        self.red_lineas, self.validacion = cargar_y_validar(ruta_excel)
        self.vision = self.red_lineas.to_estaciones()

        self.combo_tipo = None
        self.combo_linea = None
        self.combo_layout = None
        self.var_etiquetas = tk.BooleanVar(value=False)
        self.info_texto = None

        self.figura = plt.Figure(figsize=(10, 7), dpi=100)
        self.ax = self.figura.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figura, master=self.raiz)

        self._construir_layout()
        self._dibujar_actual()

    def _construir_layout(self) -> None:
        """Construye controles y contenedores principales de la ventana."""
        panel_controles = ttk.Frame(self.raiz, padding=8)
        panel_controles.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(panel_controles, text="Tipo de grafo:").pack(side=tk.LEFT, padx=4)
        self.combo_tipo = ttk.Combobox(
            panel_controles,
            state="readonly",
            values=[
                "Red completa",
                "Linea concreta",
                "Red sin una linea",
                "Subgrafo de intercambiadores",
                "Red coloreada (DSATUR)",
            ],
            width=32,
        )
        self.combo_tipo.current(0)
        self.combo_tipo.pack(side=tk.LEFT, padx=4)
        self.combo_tipo.bind("<<ComboboxSelected>>", lambda _: self._on_tipo_change())

        ttk.Label(panel_controles, text="Linea:").pack(side=tk.LEFT, padx=4)
        self.combo_linea = ttk.Combobox(
            panel_controles,
            state="readonly",
            values=sorted(self.red_lineas.mapa.keys()),
            width=20,
        )
        self.combo_linea.current(0)
        self.combo_linea.pack(side=tk.LEFT, padx=4)

        ttk.Label(panel_controles, text="Layout:").pack(side=tk.LEFT, padx=4)
        self.combo_layout = ttk.Combobox(
            panel_controles,
            state="readonly",
            values=["Force-directed", "Circular"],
            width=16,
        )
        self.combo_layout.current(0)
        self.combo_layout.pack(side=tk.LEFT, padx=4)

        ttk.Checkbutton(panel_controles, text="Mostrar etiquetas", variable=self.var_etiquetas).pack(side=tk.LEFT, padx=8)
        ttk.Button(panel_controles, text="Dibujar", command=self._dibujar_actual).pack(side=tk.LEFT, padx=8)

        panel_info = ttk.Frame(self.raiz, padding=8)
        panel_info.pack(side=tk.TOP, fill=tk.X)
        self.info_texto = tk.StringVar(value="")
        ttk.Label(panel_info, textvariable=self.info_texto, justify=tk.LEFT).pack(side=tk.LEFT)

        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _on_tipo_change(self) -> None:
        """Habilita/deshabilita selector de linea segun el tipo de grafo."""
        tipo = self.combo_tipo.get()
        necesita_linea = tipo in {"Linea concreta", "Red sin una linea"}
        self.combo_linea.configure(state="readonly" if necesita_linea else "disabled")

    def _grafo_red_completa(self):
        """Genera nodos/aristas de toda la red de estaciones."""
        ady = construir_lista_adyacencia(self.red_lineas)
        nodos = sorted(ady.keys())
        aristas = lista_a_aristas(ady)
        return "Red completa de estaciones", nodos, aristas, None

    def _grafo_linea(self, nombre_linea: str):
        """Genera el subgrafo camino de una linea concreta."""
        linea: Linea = self.red_lineas.mapa[nombre_linea]
        nodos = [est.nombre for est in linea.paradas]
        # Evita duplicado en lineas circulares cerradas.
        nodos_unicos = []
        vistos = set()
        for nodo in nodos:
            if nodo not in vistos:
                nodos_unicos.append(nodo)
                vistos.add(nodo)

        aristas = []
        for i in range(len(linea.paradas) - 1):
            aristas.append(tuple(sorted((linea.paradas[i].nombre, linea.paradas[i + 1].nombre))))
        aristas = sorted(set(aristas))
        return f"Subgrafo de {nombre_linea}", nodos_unicos, aristas, None

    def _grafo_red_sin_linea(self, nombre_linea: str):
        """Genera grafo global tras eliminar una linea dada."""
        reducida = self.red_lineas.eliminar_linea(nombre_linea)
        ady = construir_lista_adyacencia(reducida)
        nodos = sorted(ady.keys())
        aristas = lista_a_aristas(ady)
        return f"Red sin {nombre_linea}", nodos, aristas, None

    def _grafo_intercambiadores(self):
        """Genera subgrafo inducido por estaciones con grado >= 3."""
        ady = construir_lista_adyacencia(self.red_lineas)
        grados = {nodo: len(vecinos) for nodo, vecinos in ady.items()}
        nodos = sorted([nodo for nodo, grado in grados.items() if grado >= 3])
        conjunto = set(nodos)

        aristas = []
        for nodo in nodos:
            for vecino in ady[nodo]:
                if vecino in conjunto:
                    aristas.append(tuple(sorted((nodo, vecino))))

        return "Subgrafo de intercambiadores (grado >= 3)", nodos, sorted(set(aristas)), None

    def _grafo_coloreado_dsatur(self):
        """Genera red completa y aplica coloracion DSATUR."""
        ady = construir_lista_adyacencia(self.red_lineas)
        nodos = sorted(ady.keys())
        aristas = lista_a_aristas(ady)
        colores = self.vision.colorear_dsatur(self.red_lineas)
        return "Red completa coloreada con DSATUR", nodos, aristas, colores

    def _obtener_grafo(self):
        """Despacha la construccion del grafo segun opcion elegida."""
        tipo = self.combo_tipo.get()
        linea = self.combo_linea.get()

        if tipo == "Red completa":
            return self._grafo_red_completa()
        if tipo == "Linea concreta":
            return self._grafo_linea(linea)
        if tipo == "Red sin una linea":
            return self._grafo_red_sin_linea(linea)
        if tipo == "Subgrafo de intercambiadores":
            return self._grafo_intercambiadores()
        if tipo == "Red coloreada (DSATUR)":
            return self._grafo_coloreado_dsatur()

        raise ValueError(f"Tipo de grafo no soportado: {tipo}")

    def _layout(self, nodos: Sequence[str], aristas: Sequence[Tuple[str, str]]) -> Dict[str, np.ndarray]:
        """Selecciona y ejecuta el algoritmo de layout solicitado."""
        modo = self.combo_layout.get()
        if modo == "Circular":
            return layout_circular(nodos)
        return layout_force_directed(nodos, aristas)

    def _estadisticas(self, nodos: Sequence[str], aristas: Sequence[Tuple[str, str]]) -> str:
        """Calcula y formatea estadisticas basicas del grafo mostrado."""
        if not nodos:
            return "Grafo vacio"

        ady = {n: set() for n in nodos}
        for u, v in aristas:
            if u in ady and v in ady:
                ady[u].add(v)
                ady[v].add(u)

        # BFS para conectividad del subgrafo mostrado.
        inicio = nodos[0]
        visitados = {inicio}
        cola = [inicio]
        while cola:
            actual = cola.pop(0)
            for vecino in ady[actual]:
                if vecino not in visitados:
                    visitados.add(vecino)
                    cola.append(vecino)

        grados = [len(ady[n]) for n in nodos]
        media_grado = sum(grados) / len(grados) if grados else 0.0
        return (
            f"Vertices: {len(nodos)} | Aristas: {len(aristas)} | "
            f"Conexo: {texto_bool(len(visitados) == len(nodos))} | "
            f"Grado medio: {media_grado:.2f}"
        )

    def _dibujar_actual(self) -> None:
        """Redibuja el grafo actual en la figura Matplotlib.

        Como lo hace:
        - Construye nodos/aristas segun filtros de UI.
        - Calcula layout.
        - Dibuja aristas, nodos y etiquetas opcionales.
        - Actualiza bloque de estadisticas.
        """
        try:
            titulo, nodos, aristas, mapa_colores = self._obtener_grafo()
        except Exception as exc:  # pragma: no cover - proteccion de UI.
            messagebox.showerror("Error al construir grafo", str(exc))
            return

        posiciones = self._layout(nodos, aristas)
        colores = color_por_mapa(mapa_colores, nodos)

        self.ax.clear()
        self.ax.set_title(titulo)
        self.ax.axis("off")

        # Dibujo de aristas.
        for u, v in aristas:
            p1 = posiciones.get(u)
            p2 = posiciones.get(v)
            if p1 is None or p2 is None:
                continue
            self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#9aa4b2", linewidth=0.8, alpha=0.7, zorder=1)

        # Dibujo de nodos.
        for i, nodo in enumerate(nodos):
            p = posiciones[nodo]
            self.ax.scatter(p[0], p[1], s=36, color=colores[i], edgecolors="black", linewidths=0.3, zorder=2)

        # Etiquetas opcionales (o automaticas para subgrafos pequenos).
        mostrar_etiquetas = self.var_etiquetas.get() or len(nodos) <= 35
        if mostrar_etiquetas:
            for nodo in nodos:
                p = posiciones[nodo]
                self.ax.text(p[0], p[1], nodo, fontsize=7, ha="center", va="bottom", zorder=3)

        self.info_texto.set(self._estadisticas(nodos, aristas))
        self.canvas.draw()


def lanzar_ui() -> None:
    """Punto de entrada para abrir la interfaz de visualizacion."""
    raiz = tk.Tk()
    AplicacionGrafo(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    lanzar_ui()
