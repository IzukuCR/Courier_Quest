# Bitácora de Desarrollo - Courier Quest II
## Implementación de Sistema de Inteligencia Artificial

**Proyecto:** Courier Quest - Parte II  
**Curso:** EIF-207 Estructuras de Datos  
**Período:** II Ciclo 2025  
**Integrantes:** Isaac Rodriguez Aguero, Josué Ezequiel Ulloa Brenes  
**Fecha:** 17 de Noviembre, 2025

---

## 1. Implementación IA Fácil (Heurística Aleatoria)

### 1.2 Prompts Utilizados

**Prompt 1:** Implementación de cola para tracking
```
"En la clase EasyAI, implementa un sistema de tracking usando collections.deque 
para mantener historial de las últimas 20 decisiones. Almacena tuplas con 
(tiempo, acción, posición). Agrega método _is_stuck() que detecte si el AI está 
en un loop revisando las últimas 5 posiciones almacenadas en otra deque."
```

**Resultado:** Implementación de:
- `self.decision_history = deque(maxlen=20)` para historial
- `self.position_history = deque(maxlen=5)` para detección de loops

---

**Prompt 2:** Selección aleatoria de pedidos
```
"Implementa _select_random_order() que obtenga la lista de pedidos disponibles del 
JobsInventory del juego. Filtra los pedidos por estado 'available', verifica que 
el peso no exceda la capacidad usando self.weight, y usa random.choice() para 
seleccionar uno aleatoriamente."
```

**Código generado:**
```python
def _select_random_order(self, game_state):
    available_orders = game_state.get('available_orders', [])
    valid_orders = [
        order for order in available_orders
        if order.state == 'available' and order.weight + self.weight <= 8.0
    ]
    return random.choice(valid_orders) if valid_orders else None
```

---

**Prompt 3:** Movimiento aleatorio con validación
```
"Implementa _get_valid_random_directions() que genere las 4 direcciones cardinales 
y valide cada una usando city.is_valid_position() y city.is_blocked() del sistema 
existente. Retorna lista de direcciones válidas o IDLE si no hay opciones."
```

**Código generado:**
```python
def _get_valid_random_directions(self, city):
    directions = [(0,-1,'UP'), (0,1,'DOWN'), (-1,0,'LEFT'), (1,0,'RIGHT')]
    valid = [
        (dx, dy, name) for dx, dy, name in directions
        if city.is_valid_position(self.x+dx, self.y+dy) and 
           not city.is_blocked(self.x+dx, self.y+dy)
    ]
    return valid if valid else [(0, 0, 'IDLE')]
```

---

**Prompt 4:** Sistema de re-evaluación
```
"Implementa _should_change_target() que cuente cuántas decisiones han pasado desde 
el último cambio de objetivo. Si supera un threshold aleatorio entre 15-20, o si 
_is_stuck() detecta un loop, debe retornar True para cambiar de objetivo."
```

**Código generado:**
```python
def _should_change_target(self):
    if self.decisions_since_target_change >= self.target_change_threshold:
        self.target_change_threshold = random.randint(15, 20)
        self.decisions_since_target_change = 0
        return True
    return self._is_stuck()
```
**Última actualización:** 12 de Noviembre, 2025

---

## 2. Implementación IA Media (Evaluación Heurística Greedy)

### 2.1 Prompts Utilizados

**Prompt 1:** Estructura de árbol de decisión
```
"Crea una clase MediumAI que herede de AIPlayer. Implementa una estructura de árbol 
simple para explorar decisiones futuras. Define clase auxiliar DecisionNode que 
almacene: estado_actual, acción_tomada, score_evaluado, y lista de hijos (nodos_siguientes). 
El árbol debe tener profundidad máxima de 2-3 niveles para mantener rendimiento aceptable."
```

**Resultado:** Se creó `code/ai/medium_ai.py` con:
- Clase `DecisionNode` para representar nodos del árbol
- `self.lookahead_depth = 2` para horizonte de anticipación
- Método `_build_decision_tree()` que genera árbol de opciones

---

**Prompt 2:** Función de evaluación heurística
```
"Implementa _evaluate_state() que calcule un score para cada estado posible. La función 
debe considerar: 1) payout esperado del pedido (peso α=1.0), 2) distancia Manhattan hasta 
el objetivo usando abs(target_x - current_x) + abs(target_y - current_y) (peso β=0.5), 
3) penalización por condiciones climáticas usando weather.get_speed_multiplier() (peso γ=0.3). 
Retorna score = α*payout - β*distance - γ*weather_penalty."
```

**Código generado:**
```python
def _evaluate_state(self, order, current_x, current_y, weather):
    if not order:
        return 0.0
    
    # α: Payout esperado
    payout_score = order.payout * 1.0
    
    # β: Costo de distancia Manhattan
    target_x, target_y = order.pickup if order.state == 'available' else order.dropoff
    distance = abs(target_x - current_x) + abs(target_y - current_y)
    distance_cost = distance * 0.5
    
    # γ: Penalización por clima
    weather_multiplier = weather.get_speed_multiplier() if weather else 1.0
    weather_penalty = (1.0 - weather_multiplier) * 0.3
    
    return payout_score - distance_cost - weather_penalty
```

---

**Prompt 3:** Exploración greedy de movimientos
```
"Implementa _explore_moves() que genere todos los movimientos posibles desde la posición 
actual usando las 4 direcciones cardinales. Para cada movimiento válido (verificado con 
city.is_valid_position() y city.is_blocked()), simula el nuevo estado y calcula su score 
con _evaluate_state(). Retorna lista de tuplas (movimiento, score) ordenada por score 
descendente."
```

**Código generado:**
```python
def _explore_moves(self, current_x, current_y, target_order, city, weather, depth):
    if depth <= 0 or not target_order:
        return []
    
    moves = []
    directions = [(0,-1,'UP'), (0,1,'DOWN'), (-1,0,'LEFT'), (1,0,'RIGHT')]
    
    for dx, dy, direction in directions:
        new_x, new_y = current_x + dx, current_y + dy
        
        if city.is_valid_position(new_x, new_y) and not city.is_blocked(new_x, new_y):
            score = self._evaluate_state(target_order, new_x, new_y, weather)
            moves.append(((new_x, new_y, direction), score))
    
    # Ordenar por score descendente (greedy)
    moves.sort(key=lambda x: x[1], reverse=True)
    return moves
```

---

**Prompt 4:** Selección de mejor pedido con heurística
```
"Implementa _select_best_order() que evalúe todos los pedidos disponibles del JobsInventory 
usando la función heurística. Para cada pedido válido (estado 'available', peso permitido), 
calcula el score considerando su payout y distancia actual. Retorna el pedido con el 
score más alto. Si hay empate, usa order.priority como desempate."
```

**Código generado:**
```python
def _select_best_order(self, game_state):
    available_orders = game_state.get('available_orders', [])
    weather = game_state.get('weather')
    
    best_order = None
    best_score = float('-inf')
    
    for order in available_orders:
        if order.state == 'available' and order.weight + self.weight <= 8.0:
            score = self._evaluate_state(order, self.x, self.y, weather)
            
            # Desempate por prioridad
            if score > best_score or (score == best_score and order.priority > getattr(best_order, 'priority', 0)):
                best_score = score
                best_order = order
    
    return best_order
```

---

**Prompt 5:** Algoritmo de decisión con lookahead
```
"Implementa make_decision() para MediumAI que use búsqueda greedy best-first con 
lookahead limitado. Si no tiene objetivo, llama _select_best_order(). Si tiene objetivo, 
usa _explore_moves() para explorar 2-3 movimientos adelante, evalúa cada rama del árbol, 
y selecciona la acción que maximiza el score acumulado. Implementa poda simple: si un 
nodo tiene score < 0, no explorar sus hijos."
```

**Código generado:**
```python
def make_decision(self, game_state):
    # Si no hay objetivo, seleccionar mejor pedido
    if not self.current_target_order:
        best_order = self._select_best_order(game_state)
        if best_order:
            return {
                'action_type': 'select_order',
                'target_order': best_order,
                'reasoning': f'Selected order {best_order.id} with score {self._evaluate_state(best_order, self.x, self.y, game_state.get("weather")):.2f}'
            }
    
    # Explorar movimientos con lookahead
    city = game_state.get('city')
    weather = game_state.get('weather')
    moves = self._explore_moves(self.x, self.y, self.current_target_order, city, weather, self.lookahead_depth)
    
    if moves:
        best_move, best_score = moves[0]  # Ya ordenado por score
        new_x, new_y, direction = best_move
        
        return {
            'action_type': 'move',
            'target_position': (new_x, new_y),
            'reasoning': f'Moving {direction} with projected score {best_score:.2f}'
        }
    
    return {'action_type': 'idle', 'reasoning': 'No valid moves available'}
```
**Última actualización:** 13 de Noviembre, 2025

---

## 3. Implementación IA Difícil (Pathfinding con A*)

### 3.1 Prompts Utilizados

**Prompt 1:** Implementación de algoritmo A*
```
"Implementa _get_best_next_move_astar() en MediumAI que use A* pathfinding para encontrar 
el camino óptimo al objetivo. Usa heapq como cola de prioridad con tuplas (f_score, g_score, 
position, first_direction). La heurística debe ser distancia Manhattan. Limita iteraciones 
a 50 para mantener rendimiento en tiempo real. Retorna solo la primera dirección del camino 
óptimo encontrado."
```

**Código generado:**
```python
def _get_best_next_move_astar(self, game, target_pos):
    if not target_pos:
        return None
    
    import heapq
    city = game.get_city()
    start = (self.x, self.y)
    goal = target_pos
    
    # Priority queue: (f_score, g_score, position, first_direction)
    open_set = []
    heapq.heappush(open_set, (0, 0, start, None))
    
    visited = set()
    max_iterations = 50
    iterations = 0
    
    while open_set and iterations < max_iterations:
        iterations += 1
        f_score, g_score, current, first_dir = heapq.heappop(open_set)
        
        if current in visited:
            continue
        visited.add(current)
        
        if current == goal:
            return first_dir
        
        # Explorar vecinos
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            new_x = current[0] + dx
            new_y = current[1] + dy
            next_pos = (new_x, new_y)
            
            if next_pos in visited:
                continue
            if not city.is_valid_position(new_x, new_y):
                continue
            if city.is_blocked(new_x, new_y):
                continue
            
            new_g_score = g_score + 1
            h_score = abs(next_pos[0] - goal[0]) + abs(next_pos[1] - goal[1])
            new_f_score = new_g_score + h_score
            
            new_first_dir = first_dir if first_dir else (dx, dy)
            heapq.heappush(open_set, (new_f_score, new_g_score, next_pos, new_first_dir))
    
    return None
```

---

**Prompt 2:** Representación de ciudad como grafo ponderado
```
"Modifica el sistema para que la ciudad se trate como un grafo ponderado donde cada tile 
es un nodo y las conexiones entre tiles adyacentes son aristas. El peso de cada arista debe 
ser el surface_weight del tile destino (obtenido de city.get_surface_weight()). Carreteras 
('C') tienen peso 1.0, parques ('P') peso 1.5, edificios bloqueados peso infinito. Integra 
esto en la función de costo de A*."
```

**Código generado:**
```python
def _get_edge_weight(self, city, x, y):
    """Get the cost of moving to a specific tile"""
    if not city.is_valid_position(x, y):
        return float('inf')
    if city.is_blocked(x, y):
        return float('inf')
    
    surface_weight = city.get_surface_weight(x, y)
    return surface_weight
```

---

**Prompt 3:** Score mejorado con distancia exponencial
```
"Mejora _evaluate_position_score() para que use penalización exponencial por distancia en 
lugar de lineal. Si distance==0, score=1000 (llegó al objetivo). Si distance==1, score=500. 
Si distance<=3, score=200-(distance*50). Para distancias mayores, usa score=-distance*80. 
Agrega bonus de +20 si está alineado en un eje (dx==0 o dy==0) con el objetivo."
```

**Código generado:**
```python
def _evaluate_position_score(self, game, position, target_pos):
    city = game.get_city()
    x, y = position
    
    if not city.is_valid_position(x, y) or city.is_blocked(x, y):
        return float('-inf')
    
    distance = self._manhattan_distance(position, target_pos)
    
    # Penalización exponencial por distancia
    if distance == 0:
        score = 1000.0
    elif distance == 1:
        score = 500.0
    elif distance <= 3:
        score = 200.0 - (distance * 50.0)
    else:
        score = -distance * 80.0
    
    # Bonus por alineación en eje
    target_x, target_y = target_pos
    dx_to_target = target_x - x
    dy_to_target = target_y - y
    
    if dx_to_target == 0 or dy_to_target == 0:
        score += 20.0
    
    return score
```

---

**Prompt 4:** Sistema Multi-tier de pathfinding
```
"Crea _move_towards_target() que use pathfinding multi-tier: Tier 1 usa A* con 70% probabilidad 
para caminos óptimos. Tier 2 usa lookahead Expectimax con 90% si A* falla. Tier 3 usa greedy 
simple como fallback. Tier 4 usa movimiento random. Cada tier solo se ejecuta si el anterior 
falló en encontrar dirección válida."
```

**Código generado:**
```python
def _move_towards_target(self, game, target_pos):
    if not target_pos:
        return False
    
    city = game.get_city()
    weather = game.get_weather()
    direction = None
    
    # Tier 1: A* (70%)
    if random.random() < 0.70:
        direction = self._get_best_next_move_astar(game, target_pos)
    
    # Tier 2: Expectimax lookahead (90%)
    if not direction and random.random() < 0.90:
        direction = self._get_best_direction_with_lookahead(game, target_pos)
    
    # Tier 3: Greedy
    if not direction:
        direction = self._get_greedy_direction(game, target_pos)
    
    # Tier 4: Random fallback
    if not direction:
        direction = self._get_random_valid_direction(game)
    
    if direction:
        dx, dy = direction
        new_x = self.x + dx
        new_y = self.y + dy
        self.last_direction = (dx, dy)
        return self.move_to(new_x, new_y, city, weather)
    
    return False
```

---

**Prompt 5:** Detección y escape de loops mejorado
```
"Implementa sistema anti-loop que detecte 3 patrones: 1) Loop apretado de 2 posiciones únicas 
en 8 movimientos → forzar 8 random moves. 2) Loop pequeño de 3-4 posiciones visitadas 3+ veces 
→ forzar 6 random moves. 3) Patrón back-and-forth A→B→A→B→A→B → forzar 5 random moves. Usa 
deque(maxlen=12) para tracking. Durante escape, evitar posiciones de los últimos 4 movimientos."
```

**Código generado:**
```python
def _detect_and_handle_loops(self, current_pos):
    self.recent_positions.append(current_pos)
    
    if len(self.recent_positions) >= 8:
        recent_list = list(self.recent_positions)[-10:]
        unique_recent = set(recent_list)
        
        # Patrón 1: Loop apretado (2 posiciones)
        if len(unique_recent) <= 2:
            if not self.stuck_in_loop:
                self.stuck_in_loop = True
                self.random_moves_remaining = 8
                print(f"[AI] Loop apretado detectado!")
        
        # Patrón 2: Loop pequeño (3-4 posiciones, visitadas 3+ veces)
        elif len(unique_recent) <= 4:
            current_count = recent_list[-8:].count(current_pos)
            if current_count >= 3:
                if not self.stuck_in_loop:
                    self.stuck_in_loop = True
                    self.random_moves_remaining = 6
        
        # Patrón 3: Back-and-forth
        if len(recent_list) >= 6:
            if (recent_list[-1] == recent_list[-3] == recent_list[-5] and 
                recent_list[-2] == recent_list[-4] == recent_list[-6]):
                if not self.stuck_in_loop:
                    self.stuck_in_loop = True
                    self.random_moves_remaining = 5
```
**Última actualización:** 14 de Noviembre, 2025

---

## 4. Optimizaciones y Debugging

### 4.1 Corrección de Navegación (Medium AI)

**Prompt 1:** Corrección de IA que no llega al dropoff
```
"La IA Medium recoge pedidos pero después no llega a dejar el pedido. 
Diagnostica el problema: cuando recoge el pedido, actualiza target_position al dropoff pero 
el sistema anti-loop probablemente se activa porque las posiciones recientes están cerca del 
pickup. Implementa limpieza de estado: cuando recoge pedido, hacer clear() de recent_positions, 
resetear stuck_in_loop=False, random_moves_remaining=0, y last_direction=None para reiniciar 
la navegación limpia hacia el dropoff."
```

**Código generado:**
```python
# En _check_pickup_delivery() después de recoger:
if distance <= 1 and self.weight + self.active_order.weight <= 8.0:
    self.active_order.state = "carrying"
    self.active_order.picked_at = elapsed_game_time
    self.weight += self.active_order.weight
    
    # Update target to dropoff
    self.target_position = self.active_order.dropoff
    self.target_type = "dropoff"
    
    # CRITICAL: Limpiar estado de navegación para nueva ruta
    self.recent_positions.clear()
    self.stuck_in_loop = False
    self.random_moves_remaining = 0
    self.last_direction = None
    
    print(f"[AI] Picked up {self.active_order.id} - heading to dropoff")
```

---

**Prompt 2:** Optimización de movimiento cerca del objetivo
```
"Agrega optimización para cuando la IA está a 2-3 tiles del objetivo. En lugar de usar 
pathfinding complejo, usa aproximación directa simple: calcula dx y dy hacia el target, 
intenta movimiento en X primero, si está bloqueado intenta Y. Solo usa pathfinding normal 
si ambos están bloqueados. Esto hace la IA más rápida y directa en distancias cortas."
```

**Código generado:**
```python
if distance_to_target <= 3:
    city = game.get_city()
    weather = game.get_weather()
    
    target_x, target_y = self.target_position
    dx = 1 if target_x > self.x else (-1 if target_x < self.x else 0)
    dy = 1 if target_y > self.y else (-1 if target_y < self.y else 0)
    
    moved = False
    if dx != 0:
        new_x = self.x + dx
        if city.is_valid_position(new_x, self.y) and not city.is_blocked(new_x, self.y):
            moved = self.move_to(new_x, self.y, city, weather)
    
    if not moved and dy != 0:
        new_y = self.y + dy
        if city.is_valid_position(self.x, new_y) and not city.is_blocked(self.x, new_y):
            moved = self.move_to(self.x, new_y, city, weather)
    
    if not moved:
        self._move_towards_target(game, self.target_position)
```

---

**Prompt 3:** Validación de consistencia target/state
```
"Implementa validación cada frame que verifique si el target_type coincide con el estado 
de la orden activa. Si active_order.state=='accepted' pero target_type!='pickup', corregir 
automáticamente. Si active_order.state=='carrying' pero target_type!='dropoff', corregir. 
Agrega logs de advertencia cuando se detecte inconsistencia."
```

**Código generado:**
```python
# En run_bot_logic(), después de _check_pickup_delivery()
if self.active_order:
    if self.active_order.state == "accepted" and self.target_type != "pickup":
        print(f"[AI] ⚠️ Corrigiendo target: debería ser pickup, era {self.target_type}")
        self.target_position = self.active_order.pickup
        self.target_type = "pickup"
    elif self.active_order.state == "carrying" and self.target_type != "dropoff":
        print(f"[AI] ⚠️ Corrigiendo target: debería ser dropoff, era {self.target_type}")
        self.target_position = self.active_order.dropoff
        self.target_type = "dropoff"
```

**Última actualización:** 15 de Noviembre, 2025

---

## 6. Análisis de Rendimiento y Complejidad

### 6.1 Análisis por Nivel de Dificultad

#### Nivel Fácil (EasyAI)
**Estructuras de datos:**
- `list`: Almacenamiento de jobs y direcciones - O(n) acceso
- `deque(maxlen=5)`: Cola FIFO para dirección - O(1) enqueue/dequeue
- Random selection: O(1) amortizado

**Complejidad temporal:**
- Selección de pedido: O(n) donde n = número de pedidos disponibles
- Movimiento aleatorio: O(1) por decisión
- Detección de bloqueos: O(1) verificación

**Complejidad espacial:** O(n + k) donde k=5 (tamaño cola)

#### Nivel Medio (MediumAI)
**Estructuras de datos:**
- `deque(maxlen=12)`: Tracking de posiciones recientes - O(1) operaciones
- `TreeNode`: Árbol de decisión - O(4^d) nodos donde d=profundidad
- `heapq`: Cola de prioridad para A* - O(log n) push/pop
- `set`: Visitados en búsqueda - O(1) lookup

**Complejidad temporal:**
- Selección con heurística: O(n log n) por sorting
- Lookahead Expectimax: O(4^d) donde d=3 (profundidad) = O(64) constante
- A* pathfinding: O(b^d) donde b=4, d limitado a 50 = O(4^50) worst case, típicamente O(n log n) con buena heurística
- Evaluación de posición: O(1)

**Complejidad espacial:** O(4^d + n) para árbol + jobs evaluados

#### Nivel Difícil (HardAI)
**Estructuras de datos:**
- Grafo implícito: Ciudad como grafo ponderado - O(V + E)
- Priority queue: heapq para Dijkstra/A* - O(log V)
- Path storage: Lista de posiciones - O(k) donde k = longitud del camino

**Complejidad temporal:**
- Dijkstra: O((V + E) log V) con heap
- A* optimizado: O(b^d) pero típicamente mucho mejor que Dijkstra
- Replanificación: O(V log V) cuando cambia el clima

**Complejidad espacial:** O(V + E) para representación del grafo
---

**Fecha de entrega:** 17 de Noviembre, 2025  
**Última actualización:** 17 de Noviembre, 2025 - 11:30 PM