from typing import List, Tuple, Optional
import time
# from local_driver import Alg3D, Board # Для локального тестирования
from framework import Alg3D, Board # Для финальной отправки

class MyAI(Alg3D):
    def __init__(self):
        self.board_size = 4
        self.max_time = 8.5  # Используем почти всё время
        self.transposition_table = {}  # Кэш для избежания повторных вычислений
        
        # Порядок исследования колонок (центр важнее!)
        self.column_order = [1, 2, 0, 3]  # для 4x4 доски
        
    def get_move(
        self,
        board: List[List[List[int]]],  # [z][y][x]
        player: int,
        last_move: Tuple[int, int, int]
    ) -> Tuple[int, int]:
        """ULTIMATE 3D Connect 4 AI using advanced Negamax"""
        
        self.start_time = time.time()
        self.nodes_explored = 0
        
        try:
            # Очищаем кэш каждые несколько ходов для избежания переполнения
            if len(self.transposition_table) > 10000:
                self.transposition_table.clear()
            
            # 1. Немедленная победа
            winning_move = self.find_immediate_win(board, player)
            if winning_move:
                return winning_move
                
            # 2. Критическая блокировка
            opponent = 3 - player
            blocking_move = self.find_immediate_win(board, opponent)
            if blocking_move:
                return blocking_move
                
            # 3. NEGAMAX с итеративным углублением
            best_move = self.iterative_deepening_negamax(board, player)
            return best_move if best_move else self.safe_move(board)
            
        except Exception:
            return self.safe_move(board)

    def find_immediate_win(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Поиск немедленной победы"""
        for x in self.column_order:
            for y in self.column_order:
                drop_z = self.get_drop_position(board, x, y)
                if drop_z is None:
                    continue
                    
                # Пробуем ход
                board[drop_z][y][x] = player
                if self.is_winning_position(board, player):
                    board[drop_z][y][x] = 0
                    return (x, y)
                board[drop_z][y][x] = 0
        return None

    def iterative_deepening_negamax(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Итеративное углубление с Negamax"""
        best_move = None
        
        # Начинаем с малой глубины и увеличиваем
        for depth in range(1, 15):  # максимум 15 уровней
            if time.time() - self.start_time > self.max_time:
                break
                
            current_best = self.negamax_root(board, player, depth)
            if current_best:
                best_move = current_best
                
        return best_move

    def negamax_root(self, board: List[List[List[int]]], player: int, max_depth: int) -> Optional[Tuple[int, int]]:
        """Корневая функция Negamax"""
        best_score = float('-inf')
        best_move = None
        alpha = float('-inf')
        beta = float('inf')
        
        # Исследуем ходы в оптимальном порядке
        moves = self.get_ordered_moves(board)
        
        for x, y in moves:
            if time.time() - self.start_time > self.max_time:
                break
                
            drop_z = self.get_drop_position(board, x, y)
            if drop_z is None:
                continue
                
            # Делаем ход
            board[drop_z][y][x] = player
            
            # Negamax для противника (с инверсией знака)
            score = -self.negamax(board, max_depth - 1, -beta, -alpha, 3 - player)
            
            # Откатываем ход
            board[drop_z][y][x] = 0
            
            if score > best_score:
                best_score = score
                best_move = (x, y)
                alpha = max(alpha, score)
                
        return best_move

    def negamax(self, board: List[List[List[int]]], depth: int, alpha: int, beta: int, player: int) -> int:
        """
        NEGAMAX алгоритм - сердце нашего ИИ
        Возвращает оценку позиции с точки зрения текущего игрока
        """
        
        # Проверка времени
        if time.time() - self.start_time > self.max_time:
            return self.quick_evaluate(board, player)
            
        self.nodes_explored += 1
        
        # Создаём хэш позиции для транспозиционной таблицы
        position_hash = self.hash_position(board, player, depth)
        if position_hash in self.transposition_table:
            cached_result = self.transposition_table[position_hash]
            if cached_result['depth'] >= depth:
                return cached_result['score']
        
        # Проверка терминальных состояний
        winner = self.check_winner(board)
        if winner is not None:
            if winner == player:
                return (self.board_size * self.board_size * self.board_size + 1 - self.count_moves(board)) // 2
            elif winner == (3 - player):
                return -(self.board_size * self.board_size * self.board_size + 1 - self.count_moves(board)) // 2
            else:  # ничья
                return 0
        
        # Проверка глубины
        if depth <= 0:
            return self.evaluate_position(board, player)
        
        # Проверка заполненности доски
        if self.count_moves(board) >= self.board_size ** 3:
            return 0  # ничья
        
        best_score = float('-inf')
        moves = self.get_ordered_moves(board)
        
        for x, y in moves:
            drop_z = self.get_drop_position(board, x, y)
            if drop_z is None:
                continue
                
            # Делаем ход
            board[drop_z][y][x] = player
            
            # Рекурсивно вызываем negamax для противника
            score = -self.negamax(board, depth - 1, -beta, -alpha, 3 - player)
            
            # Откатываем ход
            board[drop_z][y][x] = 0
            
            best_score = max(best_score, score)
            alpha = max(alpha, score)
            
            # Альфа-бета отсечение
            if alpha >= beta:
                break
        
        # Сохраняем в транспозиционной таблице
        self.transposition_table[position_hash] = {
            'score': best_score,
            'depth': depth
        }
        
        return best_score

    def evaluate_position(self, board: List[List[List[int]]], player: int) -> int:
        """
        Продвинутая оценка позиции
        Основана на анализе угроз и возможностей
        """
        score = 0
        opponent = 3 - player
        
        # Анализируем все возможные линии
        lines = self.get_all_lines()
        
        for line in lines:
            our_pieces = 0
            their_pieces = 0
            empty_spots = []
            
            valid_line = True
            for x, y, z in line:
                if not (0 <= x < 4 and 0 <= y < 4 and 0 <= z < 4):
                    valid_line = False
                    break
                    
                cell = board[z][y][x]
                if cell == player:
                    our_pieces += 1
                elif cell == opponent:
                    their_pieces += 1
                else:
                    empty_spots.append((x, y, z))
            
            if not valid_line or (our_pieces > 0 and their_pieces > 0):
                continue  # Заблокированная линия
            
            # Система оценки основана на количестве фишек в линии
            if our_pieces == 3 and len(empty_spots) == 1:
                # Проверяем, можем ли реально сделать выигрышный ход
                if self.can_play_in_position(board, empty_spots[0]):
                    score += 5000  # Очень сильная позиция
            elif their_pieces == 3 and len(empty_spots) == 1:
                if self.can_play_in_position(board, empty_spots[0]):
                    score -= 5000  # Нужно блокировать
            elif our_pieces == 2 and len(empty_spots) == 2:
                playable_spots = sum(1 for pos in empty_spots if self.can_play_in_position(board, pos))
                score += playable_spots * 100
            elif their_pieces == 2 and len(empty_spots) == 2:
                playable_spots = sum(1 for pos in empty_spots if self.can_play_in_position(board, pos))
                score -= playable_spots * 100
            elif our_pieces == 1 and len(empty_spots) == 3:
                playable_spots = sum(1 for pos in empty_spots if self.can_play_in_position(board, pos))
                score += playable_spots * 10
            elif their_pieces == 1 and len(empty_spots) == 3:
                playable_spots = sum(1 for pos in empty_spots if self.can_play_in_position(board, pos))
                score -= playable_spots * 10
        
        # Дополнительные факторы
        score += self.evaluate_center_control(board, player)
        score += self.evaluate_height_control(board, player)
        
        return score

    def can_play_in_position(self, board: List[List[List[int]]], pos: Tuple[int, int, int]) -> bool:
        """Проверяет, можем ли реально поставить фишку в указанную позицию"""
        x, y, z = pos
        expected_z = self.get_drop_position(board, x, y)
        return expected_z == z

    def evaluate_center_control(self, board: List[List[List[int]]], player: int) -> int:
        """Оценка контроля центра"""
        score = 0
        center_positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
        
        for x, y in center_positions:
            for z in range(4):
                cell = board[z][y][x]
                if cell == player:
                    score += (z + 1) * 5  # Выше = лучше
                elif cell == (3 - player):
                    score -= (z + 1) * 5
        
        return score

    def evaluate_height_control(self, board: List[List[List[int]]], player: int) -> int:
        """Оценка контроля высоты"""
        score = 0
        
        for x in range(4):
            for y in range(4):
                our_height = 0
                their_height = 0
                
                for z in range(4):
                    if board[z][y][x] == player:
                        our_height = z + 1
                    elif board[z][y][x] == (3 - player):
                        their_height = z + 1
                
                score += (our_height - their_height) * 2
        
        return score

    def get_ordered_moves(self, board: List[List[List[int]]]) -> List[Tuple[int, int]]:
        """Получение ходов в оптимальном порядке (центр первым)"""
        moves = []
        
        # Сначала центральные позиции
        center_moves = [(1, 1), (2, 2), (1, 2), (2, 1)]
        for x, y in center_moves:
            if self.get_drop_position(board, x, y) is not None:
                moves.append((x, y))
        
        # Затем остальные
        for x in range(4):
            for y in range(4):
                if (x, y) not in center_moves and self.get_drop_position(board, x, y) is not None:
                    moves.append((x, y))
        
        return moves

    def get_all_lines(self) -> List[List[Tuple[int, int, int]]]:
        """Все выигрышные линии"""
        lines = []
        
        # Вертикальные (самые важные в Connect 4)
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
        
        # Диагонали в плоскостях
        for z in range(4):
            lines.append([(i, i, z) for i in range(4)])
            lines.append([(i, 3-i, z) for i in range(4)])
        
        for y in range(4):
            lines.append([(i, y, i) for i in range(4)])
            lines.append([(i, y, 3-i) for i in range(4)])
        
        for x in range(4):
            lines.append([(x, i, i) for i in range(4)])
            lines.append([(x, i, 3-i) for i in range(4)])
        
        # Пространственные диагонали
        lines.extend([
            [(i, i, i) for i in range(4)],
            [(i, i, 3-i) for i in range(4)],
            [(i, 3-i, i) for i in range(4)],
            [(3-i, i, i) for i in range(4)]
        ])
        
        return lines

    # Вспомогательные функции
    
    def get_drop_position(self, board: List[List[List[int]]], x: int, y: int) -> Optional[int]:
        """Позиция падения фишки"""
        if not (0 <= x < 4 and 0 <= y < 4):
            return None
        for z in range(4):
            if board[z][y][x] == 0:
                return z
        return None

    def is_winning_position(self, board: List[List[List[int]]], player: int) -> bool:
        """Быстрая проверка победы"""
        for line in self.get_all_lines():
            if all(0 <= x < 4 and 0 <= y < 4 and 0 <= z < 4 and 
                   board[z][y][x] == player for x, y, z in line):
                return True
        return False

    def check_winner(self, board: List[List[List[int]]]) -> Optional[int]:
        """Проверка победителя"""
        for line in self.get_all_lines():
            if all(0 <= x < 4 and 0 <= y < 4 and 0 <= z < 4 for x, y, z in line):
                first_cell = board[line[0][2]][line[0][1]][line[0][0]]
                if first_cell != 0:
                    if all(board[z][y][x] == first_cell for x, y, z in line):
                        return first_cell
        return None

    def count_moves(self, board: List[List[List[int]]]) -> int:
        """Подсчёт количества сделанных ходов"""
        count = 0
        for x in range(4):
            for y in range(4):
                for z in range(4):
                    if board[z][y][x] != 0:
                        count += 1
        return count

    def hash_position(self, board: List[List[List[int]]], player: int, depth: int) -> str:
        """Хэш позиции для транспозиционной таблицы"""
        board_str = ""
        for z in range(4):
            for y in range(4):
                for x in range(4):
                    board_str += str(board[z][y][x])
        return f"{board_str}_{player}_{depth}"

    def quick_evaluate(self, board: List[List[List[int]]], player: int) -> int:
        """Быстрая оценка при нехватке времени"""
        return self.evaluate_center_control(board, player)

    def safe_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Безопасный ход"""
        safe_moves = [(1, 1), (2, 2), (1, 2), (2, 1), (0, 0)]
        
        for x, y in safe_moves:
            if self.get_drop_position(board, x, y) is not None:
                return (x, y)
        
        # Любой доступный ход
        for x in range(4):
            for y in range(4):
                if self.get_drop_position(board, x, y) is not None:
                    return (x, y)
        
        return (0, 0)