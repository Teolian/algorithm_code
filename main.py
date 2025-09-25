from typing import List, Tuple, Optional
import time
import random
import math
# from local_driver import Alg3D, Board # Для локального тестирования
from framework import Alg3D, Board # Для финальной отправки

class MCTSNode:
    """Узел дерева MCTS"""
    def __init__(self, state: List[List[List[int]]], parent=None, action=None):
        self.state = [[[cell for cell in row] for row in level] for level in state]
        self.parent = parent
        self.action = action  # (x, y) действие, которое привело к этому состоянию
        self.children = []
        self.visits = 0
        self.wins = 0.0
        self.untried_actions = []
        self.player = None  # будет установлено при создании
        
    def is_fully_expanded(self):
        return len(self.untried_actions) == 0
    
    def is_terminal(self):
        return len(self.get_legal_actions()) == 0 or self.check_winner() is not None
    
    def get_legal_actions(self):
        """Получить все возможные действия"""
        actions = []
        for x in range(4):
            for y in range(4):
                if self.can_place_piece(x, y):
                    actions.append((x, y))
        return actions
    
    def can_place_piece(self, x: int, y: int) -> bool:
        """Проверить, можно ли поставить фишку в (x, y)"""
        for z in range(4):
            if self.state[z][y][x] == 0:
                return True
        return False
    
    def place_piece(self, x: int, y: int, player: int) -> Optional[int]:
        """Поставить фишку и вернуть Z координату"""
        for z in range(4):
            if self.state[z][y][x] == 0:
                self.state[z][y][x] = player
                return z
        return None
    
    def check_winner(self) -> Optional[int]:
        """Проверить победителя"""
        # Все выигрышные линии
        lines = []
        
        # Вертикальные
        for x in range(4):
            for y in range(4):
                lines.append([(x, y, z) for z in range(4)])
        
        # Горизонтальные
        for z in range(4):
            for y in range(4):
                for x in range(1):
                    lines.append([(x+i, y, z) for i in range(4)])
            for x in range(4):
                for y in range(1):
                    lines.append([(x, y+i, z) for i in range(4)])
        
        # Диагонали
        for z in range(4):
            lines.append([(i, i, z) for i in range(4)])
            lines.append([(i, 3-i, z) for i in range(4)])
        
        for y in range(4):
            lines.append([(i, y, i) for i in range(4)])
            lines.append([(i, y, 3-i) for i in range(4)])
        
        for x in range(4):
            lines.append([(x, i, i) for i in range(4)])
            lines.append([(x, i, 3-i) for i in range(4)])
        
        # 3D диагонали
        lines.extend([
            [(i, i, i) for i in range(4)],
            [(i, i, 3-i) for i in range(4)],
            [(i, 3-i, i) for i in range(4)],
            [(3-i, i, i) for i in range(4)]
        ])
        
        for line in lines:
            first_cell = self.state[line[0][2]][line[0][1]][line[0][0]]
            if first_cell != 0:
                if all(self.state[z][y][x] == first_cell for x, y, z in line):
                    return first_cell
        
        return None

class MyAI(Alg3D):
    def __init__(self):
        self.computation_time = 8.0  # Используем почти всё время
        
    def get_move(
        self,
        board: List[List[List[int]]],  # [z][y][x]
        player: int,
        last_move: Tuple[int, int, int]
    ) -> Tuple[int, int]:
        """MCTS ИИ основанный на мировых исследованиях"""
        
        try:
            # КРИТИЧЕСКИЕ ПРОВЕРКИ СНАЧАЛА
            
            # 1. Немедленная победа
            win_move = self.find_immediate_win(board, player)
            if win_move:
                return win_move
                
            # 2. Блокировка противника
            opponent = 3 - player
            block_move = self.find_immediate_win(board, opponent)
            if block_move:
                return block_move
            
            # 3. Если первый ход - играем в центр (научно доказано!)
            if self.is_first_move(board) and player == 1:
                center_moves = [(1, 1), (2, 2), (1, 2), (2, 1)]
                for x, y in center_moves:
                    if self.can_place_piece(board, x, y):
                        return (x, y)
                        
            # 4. MCTS поиск лучшего хода
            best_move = self.mcts_search(board, player)
            return best_move if best_move else self.safe_fallback(board)
            
        except Exception:
            return self.safe_fallback(board)

    def mcts_search(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Monte Carlo Tree Search - сердце алгоритма"""
        
        try:
            root = MCTSNode(board)
            root.player = player
            root.untried_actions = root.get_legal_actions()
            
            start_time = time.time()
            iterations = 0
            
            # Итерации MCTS
            while time.time() - start_time < self.computation_time:
                # 1. SELECTION - выбираем лучший узел для расширения
                leaf = self.select(root)
                
                # 2. EXPANSION - расширяем если возможно
                if not leaf.is_terminal() and leaf.untried_actions:
                    leaf = self.expand(leaf)
                
                # 3. SIMULATION - симуляция до конца игры
                result = self.simulate(leaf)
                
                # 4. BACKPROPAGATION - распространяем результат
                self.backpropagate(leaf, result, player)
                
                iterations += 1
            
            # Выбираем лучший ход
            if not root.children:
                return None
                
            # Ребёнок с наивысшим win rate
            best_child = max(root.children, key=lambda c: c.wins / c.visits if c.visits > 0 else 0)
            return best_child.action
            
        except Exception:
            return None

    def select(self, node: MCTSNode) -> MCTSNode:
        """SELECTION: спускаемся по дереву, выбирая лучшие узлы"""
        
        while not node.is_terminal():
            if not node.is_fully_expanded():
                return node
            else:
                node = self.best_child_ucb1(node)
        return node

    def best_child_ucb1(self, node: MCTSNode, c: float = 1.4) -> MCTSNode:
        """Выбор лучшего ребёнка по UCB1 формуле"""
        
        def ucb1_value(child):
            if child.visits == 0:
                return float('inf')  # Неизученные узлы имеют высший приоритет
            
            exploitation = child.wins / child.visits
            exploration = c * math.sqrt(math.log(node.visits) / child.visits)
            return exploitation + exploration
        
        return max(node.children, key=ucb1_value)

    def expand(self, node: MCTSNode) -> MCTSNode:
        """EXPANSION: добавляем новый узел в дерево"""
        
        action = node.untried_actions.pop()
        x, y = action
        
        # Создаём новое состояние
        new_state = [[[cell for cell in row] for row in level] for level in node.state]
        current_player = self.get_current_player(new_state)
        
        # Применяем действие
        for z in range(4):
            if new_state[z][y][x] == 0:
                new_state[z][y][x] = current_player
                break
        
        # Создаём новый узел
        child = MCTSNode(new_state, parent=node, action=action)
        child.player = 3 - current_player  # следующий игрок
        child.untried_actions = child.get_legal_actions()
        
        node.children.append(child)
        return child

    def simulate(self, node: MCTSNode) -> int:
        """SIMULATION: случайная симуляция до конца игры"""
        
        # Копируем состояние
        state = [[[cell for cell in row] for row in level] for level in node.state]
        current_player = self.get_current_player(state)
        
        # Играем до конца случайными ходами
        for _ in range(100):  # лимит на случай зацикливания
            winner = self.check_winner_state(state)
            if winner is not None:
                return winner
            
            # Получаем доступные ходы
            actions = self.get_legal_actions_state(state)
            if not actions:
                return 0  # ничья
            
            # Случайный ход (с лёгким улучшением - приоритет центру)
            action = self.smart_random_action(state, actions, current_player)
            x, y = action
            
            # Применяем ход
            for z in range(4):
                if state[z][y][x] == 0:
                    state[z][y][x] = current_player
                    break
            
            current_player = 3 - current_player
        
        return 0  # ничья если не завершилось

    def smart_random_action(self, state, actions, player):
        """Улучшенный случайный ход с приоритетом центру"""
        
        # Сначала проверяем немедленные выигрыши/блокировки
        for x, y in actions:
            # Пробуем выиграть
            temp_state = [[[cell for cell in row] for row in level] for level in state]
            for z in range(4):
                if temp_state[z][y][x] == 0:
                    temp_state[z][y][x] = player
                    if self.check_winner_state(temp_state) == player:
                        return (x, y)
                    temp_state[z][y][x] = 0
                    break
            
            # Пробуем заблокировать
            temp_state = [[[cell for cell in row] for row in level] for level in state]
            for z in range(4):
                if temp_state[z][y][x] == 0:
                    temp_state[z][y][x] = 3 - player
                    if self.check_winner_state(temp_state) == (3 - player):
                        return (x, y)
                    temp_state[z][y][x] = 0
                    break
        
        # Приоритет центральным позициям
        center_actions = [(x, y) for x, y in actions if 1 <= x <= 2 and 1 <= y <= 2]
        if center_actions:
            return random.choice(center_actions)
        
        return random.choice(actions)

    def backpropagate(self, node: MCTSNode, result: int, original_player: int):
        """BACKPROPAGATION: распространяем результат вверх по дереву"""
        
        while node is not None:
            node.visits += 1
            
            # Считаем выигрыш с точки зрения original_player
            if result == original_player:
                node.wins += 1.0
            elif result == 0:
                node.wins += 0.5  # ничья = половина очка
            # иначе поражение = 0 очков
            
            node = node.parent

    # Вспомогательные функции
    
    def find_immediate_win(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Поиск немедленного выигрыша"""
        try:
            for x in range(4):
                for y in range(4):
                    if self.can_place_piece(board, x, y):
                        # Пробуем ход
                        temp_board = [[[cell for cell in row] for row in level] for level in board]
                        for z in range(4):
                            if temp_board[z][y][x] == 0:
                                temp_board[z][y][x] = player
                                if self.check_winner_state(temp_board) == player:
                                    return (x, y)
                                break
            return None
        except:
            return None

    def can_place_piece(self, board: List[List[List[int]]], x: int, y: int) -> bool:
        """Можно ли поставить фишку"""
        try:
            for z in range(4):
                if board[z][y][x] == 0:
                    return True
            return False
        except:
            return False

    def is_first_move(self, board: List[List[List[int]]]) -> bool:
        """Проверяет, первый ли это ход в игре"""
        try:
            count = 0
            for x in range(4):
                for y in range(4):
                    for z in range(4):
                        if board[z][y][x] != 0:
                            count += 1
            return count == 0
        except:
            return False

    def get_current_player(self, state: List[List[List[int]]]) -> int:
        """Определяет, кто ходит сейчас"""
        try:
            count1 = 0
            count2 = 0
            for x in range(4):
                for y in range(4):
                    for z in range(4):
                        if state[z][y][x] == 1:
                            count1 += 1
                        elif state[z][y][x] == 2:
                            count2 += 1
            return 1 if count1 == count2 else 2
        except:
            return 1

    def check_winner_state(self, state: List[List[List[int]]]) -> Optional[int]:
        """Проверка победителя для состояния"""
        try:
            # Вертикальные линии
            for x in range(4):
                for y in range(4):
                    if state[0][y][x] != 0:
                        if all(state[z][y][x] == state[0][y][x] for z in range(4)):
                            return state[0][y][x]
            
            # Горизонтальные X
            for z in range(4):
                for y in range(4):
                    for start_x in range(1):
                        if state[z][y][start_x] != 0:
                            if all(state[z][y][start_x + i] == state[z][y][start_x] for i in range(4)):
                                return state[z][y][start_x]
            
            # Горизонтальные Y  
            for z in range(4):
                for x in range(4):
                    for start_y in range(1):
                        if state[z][start_y][x] != 0:
                            if all(state[z][start_y + i][x] == state[z][start_y][x] for i in range(4)):
                                return state[z][start_y][x]
            
            # Диагонали XY
            for z in range(4):
                if state[z][0][0] != 0:
                    if all(state[z][i][i] == state[z][0][0] for i in range(4)):
                        return state[z][0][0]
                if state[z][0][3] != 0:
                    if all(state[z][i][3-i] == state[z][0][3] for i in range(4)):
                        return state[z][0][3]
            
            # 3D диагонали
            if state[0][0][0] != 0:
                if all(state[i][i][i] == state[0][0][0] for i in range(4)):
                    return state[0][0][0]
            
            return None
        except:
            return None

    def get_legal_actions_state(self, state: List[List[List[int]]]) -> List[Tuple[int, int]]:
        """Получить доступные ходы для состояния"""
        try:
            actions = []
            for x in range(4):
                for y in range(4):
                    for z in range(4):
                        if state[z][y][x] == 0:
                            actions.append((x, y))
                            break
            return actions
        except:
            return [(1, 1), (2, 2)]

    def safe_fallback(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Безопасный запасной ход"""
        try:
            safe_moves = [(1, 1), (2, 2), (1, 2), (2, 1), (0, 0), (3, 3)]
            
            for x, y in safe_moves:
                if self.can_place_piece(board, x, y):
                    return (x, y)
            
            # Любой доступный ход
            for x in range(4):
                for y in range(4):
                    if self.can_place_piece(board, x, y):
                        return (x, y)
            
            return (0, 0)
        except:
            return (0, 0)