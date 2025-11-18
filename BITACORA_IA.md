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