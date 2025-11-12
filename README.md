# Courier Quest - Part 2: AI Implementation

Un videojuego de entrega desarrollado en Python usando Pygame donde el jugador controla un repartidor en bicicleta que debe completar pedidos en una ciudad mientras gestiona tiempo, clima, inventario y reputación. **Ahora con jugador CPU (IA) en tres niveles de dificultad.**

# Integrantes del Grupo
- Isaac Rodriguez Aguero
- Josué Ezequiel Ulloa Brenes

# Bitacora
https://docs.google.com/document/d/1YgJ_xAt9MFufSFnJceTfLrB9dwXMMx64OqryTdlHwSA/edit?usp=sharing

# Descripción

Este proyecto implementa un videojuego donde el jugador es un repartidor que debe completar pedidos en una ciudad. El objetivo es alcanzar una meta de ingresos antes de que termine el tiempo, mientras se gestionan varios factores como resistencia del jugador, cambios climáticos, peso del inventario y sistema de reputación.

**Nuevo en Parte 2:** Competencia contra un jugador CPU (IA) con tres niveles de dificultad que utiliza diferentes algoritmos y estructuras de datos.

# Instrucciones de Instalación

# Requisitos del Sistema
- Python 3.8 o superior
- Librería Pygame
- Librería Requests

# Instalación de Dependencias
pip install pygame requests

# Ejecutar el Juego

python -m code.main

# Estructuras de Datos Utilizadas

# 1. Lista 
**Ubicación en el código:**
- `JobsInventory._orders: List[Order]` - Almacena todos los pedidos disponibles
- `PlayerInventory.accepted: List[Order]` - Pedidos aceptados por el jugador  
- `UndoSystem.position_history: List[PositionSnapshot]` - Historial de posiciones para deshacer movimientos
- `City.tiles: List[List[str]]` - Matriz bidimensional que representa el mapa de la ciudad
- `Weather.bursts: List[dict]` - Lista de eventos climáticos programados

**Complejidad:**
- Inserción al final: O(1)
- Búsqueda por índice: O(1)
- Búsqueda por valor: O(n)
- Eliminación por índice: O(n)

**Justificación de uso:**
Se utilizan listas porque necesitamos mantener el orden de los elementos y acceder a ellos por índice de manera eficiente. Son especialmente útiles para el inventario de pedidos y el historial de movimientos del jugador.

# 2. Diccionario 
**Ubicación en el código:**
- `Weather.transition_matrix: Dict[str, Dict[str, float]]` - Matriz de transición de Markov para cambios climáticos
- `City.legend: Dict[str, Dict]` - Mapeo de tipos de casillas y sus propiedades
- `Weather.SPEED_MULTIPLIERS: Dict[str, float]` - Multiplicadores de velocidad según condición climática

**Complejidad:**
- Búsqueda: O(1) promedio
- Inserción: O(1) promedio  
- Eliminación: O(1) promedio

**Justificación de uso:**
Los diccionarios permiten acceso rápido a los datos usando una clave. Son ideales para buscar multiplicadores de velocidad según el clima o las propiedades de las casillas del mapa.

# 3. Dataclass
**Ubicación en el código:**
- `Order` - Representa un pedido de entrega con sus atributos (ID, ubicaciones, pago, prioridad, etc.)
- `PositionSnapshot` - Almacena una posición del jugador para el sistema de deshacer

**Complejidad:**
- Creación: O(1)
- Acceso a atributos: O(1)
- Comparación: O(k) donde k es el número de campos

**Justificación de uso:**
Las dataclasses nos permiten crear estructuras de datos simples y organizadas con menos código que las clases tradicionales.

# 4. Patrón Singleton
**Ubicación en el código:**
- `DataManager` - Gestor único de datos para toda la aplicación
- `Game` - Instancia única del estado principal del juego

**Complejidad:**
- Acceso: O(1)
- Inicialización: O(1)

**Justificación de uso:**
Asegura que solo exista una instancia de componentes importantes como el gestor de datos y el estado del juego.

# 5. Cola FIFO (implementada con List)
**Ubicación en el código:**
- `UndoSystem.position_history` - Historial limitado de posiciones del jugador

**Complejidad:**
- Agregar elemento: O(1)
- Quitar elemento: O(n)

**Justificación de uso:**
Mantiene un historial ordenado por tiempo con un límite máximo de elementos para el sistema de deshacer movimientos.

# Algoritmos Implementados y su Complejidad

# 1. Algoritmo de Ordenamiento (TimSort)
**Ubicaciones en el código:**

# JobsInventory._load_orders()
orders.sort(key=lambda order: (-order.priority, -order.payout))

# DataManager._add_version_to_json()
file_data["versions"].sort(
    key=lambda x: tuple(map(int, x["api_version"].split('.'))), 
    reverse=True
)

**Complejidad:** O(n log n)
**Uso:** Ordenar pedidos por prioridad y pago, ordenar versiones de datos de la API

### 2. Búsqueda Lineal
**Ubicación en el código:**

# JobsInventory.selectable()
for o in self._orders:
    if o.state == "available" and not o.is_expired(t):
        # Procesar pedido

**Complejidad:** O(n)
**Uso:** Filtrar pedidos disponibles, buscar elementos que cumplan ciertas condiciones

### 3. Algoritmo de Cadena de Markov
**Ubicación en el código:**
# Weather.next_weather()
transitions = self.transition_matrix.get(self.current_condition, {})
conditions = list(transitions.keys())
probabilities = list(transitions.values())
self.current_condition = random.choices(conditions, weights=probabilities)[0]

**Complejidad:** O(k) donde k es el número de estados climáticos
**Uso:** Generar cambios climáticos basados en probabilidades

### 4. Algoritmo de Búsqueda de Ruta Simple
**Ubicación en el código:**

# Player.find_final_position()
for step in range(1, max_distance + 1):
    next_x = start_x + (dir_x * step)
    next_y = start_y + (dir_y * step)
    if city.is_valid_position(next_x, next_y) and not city.is_blocked(next_x, next_y):
        current_x, current_y = next_x, next_y
    else:
        break

**Complejidad:** O(d) donde d es la distancia máxima de movimiento
**Uso:** Determinar la posición final del jugador considerando obstáculos

### 5. Gestión de Cache con Versionado
**Ubicación en el código:**

# DataManager._add_version_to_json()
for existing_version in file_data["versions"]:
    if existing_version.get("api_version") == api_version:
        existing_content = existing_version.get("data")
        if existing_content == new_content:
            should_save = False

**Complejidad:** O(v × c) donde v es número de versiones y c es el tamaño del contenido
**Uso:** Evitar guardar datos duplicados en el cache de la API

## AI Implementation (Part 2)

### Easy AI - Random Decision Making
**Archivo:** `code/game/abstract_AI.py` - clase `EasyAI`

**Descripción:** IA que toma decisiones aleatorias usando lógica probabilística simple y colas FIFO.

**Estructuras de datos:**
- `List[Order]` - Lista de pedidos aceptados por la IA
- `deque(maxlen=5)` - Cola FIFO para gestionar direcciones de movimiento

**Algoritmos:**
- Selección aleatoria de trabajos: O(n) donde n = trabajos disponibles
- Movimiento aleatorio: O(1) por decisión
- Movimiento hacia objetivo: 70% probabilidad hacia target, 30% aleatorio

**Complejidad temporal:** O(n) donde n = número de trabajos disponibles
**Complejidad espacial:** O(k) donde k = número de órdenes aceptadas (max 3)

**Características:**
- Selección completamente aleatoria de trabajos disponibles
- Movimiento probabilístico hacia objetivos (70% dirigido, 30% aleatorio)
- No planifica rutas ni optimiza decisiones
- Usa cola FIFO para evitar retrocesos inmediatos

**Documentación completa:** Ver `EASY_AI_DOCUMENTATION.md`

### Medium AI - Greedy Evaluation (Coming Soon)
**Archivo:** `code/game/abstract_AI.py` - clase `MediumAI`

**Descripción:** IA que evalúa movimientos futuros usando heurísticas y árboles de decisión.

**Estructuras de datos planeadas:**
- Árboles de decisión (2-3 niveles de profundidad)
- Listas de acciones candidatas

**Algoritmos planeados:**
- Búsqueda Greedy con evaluación heurística
- Función de scoring: `score = α*payout - β*distance - γ*weather_penalty`

### Hard AI - Graph-Based Optimization (Coming Soon)
**Archivo:** `code/game/abstract_AI.py` - clase `HardAI`

**Descripción:** IA que usa algoritmos de grafos para encontrar rutas óptimas.

**Estructuras de datos planeadas:**
- Grafo ponderado representando la ciudad
- Cola de prioridad (heap) para Dijkstra/A*
- Tabla de distancias mínimas

**Algoritmos planeados:**
- Dijkstra o A* para búsqueda de camino más corto
- TSP aproximado para secuenciar entregas
- Replanificación dinámica según clima

## Arquitectura del Proyecto
### Organización de Módulos:
- `core/` - Contiene las clases principales (Order, City)
- `game/` - Lógica principal del juego (Game, Player, inventarios, **AI**)
- `interface/` - Interfaz gráfica y menús (usando Pygame)
- `services/` - Servicios externos (API, gestión de datos)
- `weather/` - Sistema de clima dinámico
- `ai/` - Recursos visuales para el bot de IA




