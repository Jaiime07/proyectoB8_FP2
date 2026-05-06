# Guia de defensa - Proyecto Boletin 8 (Metro de Madrid)

## 1) Objetivo del proyecto
Este proyecto modela la red de Metro de Madrid como un **grafo no dirigido** y desarrolla una solucion orientada a objetos para:
- cargar y validar datos del Excel
- transformar entre dos vistas del problema
- resolver consultas de conectividad, rutas y cercania
- aplicar teoria de grafos (Euler, Hamilton y coloracion)
- visualizar grafos con interfaz grafica

## 2) Arquitectura OO

### 2.1 Clases principales
- `Estacion` ([src/estacion.py](c:\Users\Usuario\OneDrive\1º\2º cuatrimestre\FPII\proyectoB8_FP2\src\estacion.py))
- `Linea` ([src/linea.py](c:\Users\Usuario\OneDrive\1º\2º cuatrimestre\FPII\proyectoB8_FP2\src\linea.py))
- `RedLineas` ([src/red_lineas.py](c:\Users\Usuario\OneDrive\1º\2º cuatrimestre\FPII\proyectoB8_FP2\src\red_lineas.py))
- `RedEstaciones` ([src/red_estaciones.py](c:\Users\Usuario\OneDrive\1º\2º cuatrimestre\FPII\proyectoB8_FP2\src\red_estaciones.py))

### 2.2 Idea de diseño
- `RedLineas` representa la red como la entiende un viajero: **orden de paradas** por linea.
- `RedEstaciones` representa la red como la entiende la teoria de grafos: **vertices y aristas**.
- Esta separacion permite mantener el modelo limpio y aplicar algoritmos de forma natural.

## 3) Funciones por clase y por que estan ahi

### 3.1 Clase `Estacion`
Funciones:
- `__init__(nombre, lat, lon)`
- `distancia_a(lat2, lon2)`
- `__eq__(other)`
- `__hash__()`
- `__repr__()`

Por que estan en `Estacion`:
- Son comportamiento propio de una entidad estacion (identidad y geolocalizacion).
- `distancia_a` depende de `lat/lon`, por tanto no debe estar en `Linea` ni en `RedEstaciones`.

Por que no en otra clase:
- En `Linea` mezclaria logica de secuencia con geodesia.
- En `RedEstaciones` se perderia encapsulacion: la estacion debe saber calcular su propia distancia.

### 3.2 Clase `Linea`
Funciones:
- `__init__(nombre, paradas)`
- `es_circular()`
- `__eq__(other)`

Por que estan en `Linea`:
- `Linea` modela un recorrido ordenado y conoce sus extremos.
- `es_circular` es una propiedad estructural de una linea concreta.

Por que no en otra clase:
- En `Estacion` no hay contexto de lista ordenada.
- En `RedLineas` seria menos cohesivo: la regla usa solo datos internos de una linea.

### 3.3 Clase `RedLineas`
Funciones:
- `__init__(mapa_lineas)`
- `to_estaciones()`
- `eliminar_linea(nombre_linea)`
- `__eq__(other)`

Por que estan en `RedLineas`:
- Gestiona el conjunto global de lineas.
- `to_estaciones` transforma una vista global a otra vista global.
- `eliminar_linea` es una operacion sobre el contenedor de lineas.

Por que no en otra clase:
- `Linea` solo conoce su propia secuencia, no el conjunto total.
- `RedEstaciones` no es la fuente natural para quitar "una linea" porque su estructura esta centrada en estaciones.

### 3.4 Clase `RedEstaciones`
Funciones de transformacion y utilidades:
- `__init__(mapa)`
- `to_lineas()`
- `_resolver_nombre(nombre_estacion)`
- `lineas_comunes(estacion_a, estacion_b)`
- `estan_en_misma_linea(estacion_a, estacion_b)`
- `__eq__(other)`

Funciones de estructura de grafo:
- `construir_adyacencia(red_lin)`
- `obtener_adyacentes(nombre_est, red_lin)`
- `obtener_grados(red_lin)`
- `_alcanzables_desde(inicio, adyacencia)`
- `obtener_estadisticas_conexidad(red_lin)`

Funciones de teoria de grafos:
- `analizar_eulerianidad(red_lin)`
- `_dfs_articulaciones(...)`
- `obtener_puntos_articulacion(red_lin)`
- `resumen_hamiltoniano_teorico(red_lin)`
- `colorear_greedy(red_lin)`
- `colorear_dsatur(red_lin)`

Funciones de aplicacion:
- `encontrar_estacion_mas_cercana(lat, lon, red_lin)`
- `buscar_ruta_un_transbordo(origen, destino)`

Por que estan en `RedEstaciones`:
- Todas necesitan trabajar sobre vertices, adyacencias, grados o conectividad.
- Es la clase con la representacion idonea para algoritmos de grafos.

Por que no en otra clase:
- En `RedLineas` seria mas costoso y menos natural para BFS/DFS/coloracion.
- En `Linea` o `Estacion` no hay contexto global suficiente.

## 4) Estructuras de datos (pregunta tipica de profesor)

- `dict[str, Linea]` en `RedLineas`.
- Permite acceso rapido por nombre de linea.

- `list[Estacion]` en `Linea.paradas`.
- Conserva el orden real de recorrido.

- `dict[str, dict[str, list[int]]]` en `RedEstaciones`.
- Para cada estacion guarda lineas donde aparece y posiciones.
- Esto hace posible la reconstruccion reciproca sin perder orden.

- `set[str]` para adyacencias.
- Evita duplicados de aristas y simplifica comprobaciones de vecindad.

## 5) Teoria de grafos aplicada al proyecto

### 5.1 Que significa que un grafo sea euleriano
En un grafo no dirigido conexo:
- hay **circuito euleriano** si todos los vertices tienen grado par
- hay **camino euleriano** (pero no circuito) si exactamente 2 vertices tienen grado impar
- en cualquier otro caso, no es euleriano

Interpretacion en metro:
- "euleriano" significa poder recorrer **todas las conexiones** exactamente una vez.

### 5.2 Resultado euleriano en esta red
Resultado del programa:
- la red completa es conexa
- hay **26 vertices de grado impar**

Conclusion:
- **no es euleriana**
- no existe ni circuito euleriano ni camino euleriano global

Explicacion defendible:
- al tener mas de 2 vertices impares, no se puede recorrer cada arista una unica vez sin repetir.

### 5.3 Hamiltoniano (enfoque teorico riguroso)
- Ciclo hamiltoniano: recorre **todos los vertices** exactamente una vez y vuelve al inicio.
- Decidirlo exactamente en grafos generales es NP-completo.

Por eso el proyecto usa criterios teoricos:
- condiciones suficientes (Dirac y Ore)
- condiciones necesarias (sin vertices de grado 1 y sin articulaciones)

Resultado obtenido:
- no cumple Dirac ni Ore
- existen vertices de grado 1 y muchas articulaciones

Lectura para defensa:
- con esas condiciones, un ciclo hamiltoniano global queda fuertemente descartado.

### 5.4 Coloracion de grafos: que significa y para que sirve
Colorar un grafo significa asignar un color a cada vertice de forma que:
- vertices adyacentes tengan colores distintos

Interpretacion en metro:
- cada color representa un grupo de estaciones que no son vecinas directas entre si.
- es una forma de particionar la red respetando restricciones de adyacencia.

Algoritmos aplicados:
- Greedy
- DSATUR

### 5.5 Cuantos colores se han usado
Resultados de tu ejecucion actual:
- Greedy: **3 colores**
- DSATUR: **3 colores**

Que significa este resultado:
- se ha encontrado una coloracion valida con 3 grupos de estaciones.
- DSATUR no mejora en numero de colores a Greedy en este caso concreto.
- 3 es una **cota superior** del numero cromatico real de esta red con este modelo.

## 6) Funcionalidades implementadas

- carga y validacion de datos del Excel
- reciprocidad `to_estaciones()` <-> `to_lineas()`
- estaciones con mas lineas y lineas circulares
- conectividad global y criticidad por eliminacion de linea
- rutas con 0 o 1 transbordo
- estacion mas cercana por Haversine
- eulerianidad, diagnostico hamiltoniano, coloracion greedy y DSATUR
- interfaz grafica para visualizar distintos grafos

## 7) Analisis de una funcion (pregunta tipica)
Funcion recomendada para explicar: `colorear_dsatur` en `RedEstaciones`.

Que hace:
- construye una coloracion valida intentando usar pocos colores.

Como lo hace:
1. Calcula el grado y la saturacion de cada vertice.
2. Elige el vertice no coloreado con mayor saturacion.
3. Le asigna el menor color no usado por sus vecinos.
4. Actualiza saturaciones y repite.

Por que esta bien para defender:
- mezcla estructuras de datos (`dict`, `set`) con una heuristica clasica de teoria de grafos.
- es facil justificar correctitud: nunca asigna a un vertice un color ya usado por un vecino.

Nota breve de coste:
- en esta implementacion, su coste dominante es aproximadamente cuadratico en el numero de vertices.

## 8) Preguntas cortas y respuestas

**Pregunta:** "¿Por que dos vistas de la red?"
**Respuesta:** porque por lineas es mejor para orden de paradas y por estaciones es mejor para algoritmos de grafo.

**Pregunta:** "¿Por que no matriz de adyacencia?"
**Respuesta:** porque para una red dispersa consume mas memoria y es menos flexible que listas de adyacencia con diccionarios.

**Pregunta:** "¿Como sabes que no es euleriano?"
**Respuesta:** porque es conexo pero tiene 26 vertices impares; para ser euleriano deberia tener 0 o 2.

**Pregunta:** "¿Que representan los colores?"
**Respuesta:** particiones de estaciones donde dentro del mismo color no hay adyacencias directas.

## 9) Como ejecutar

### Informe por consola
```bash
python src/main.py
```

### Interfaz grafica
```bash
python src/ui_grafos.py
```

## 10) Cierre
- Proyecto completo y funcional.
- Codigo comentado en funciones con "que hace" y "como lo hace".
- Documento orientado a defensa oral, con foco en teoria de grafos y preguntas probables.
