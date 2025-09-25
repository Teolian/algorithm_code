from typing import List, Tuple
# from local_driver import Alg3D, Board # Для локального тестирования
from framework import Alg3D, Board # Для финальной отправки

class MyAI(Alg3D):
    def __init__(self):
        self.board_size = 4
        
    def get_move(
        self,
        board: List[List[List[int]]], # 3D доска [z][y][x], 0=пусто, 1=игрок1, 2=игрок2
        player: int, # 1=мы(чёрные), 2=противник(белые)
        last_move: Tuple[int, int, int] # последний ход (x, y, z) - может быть None!
    ) -> Tuple[int, int]:
        """3D Connect 4 ИИ - возвращает лучший ход (x, y)"""
        
        try:
            # Безопасная обработка last_move
            if last_move is None or last_move == (None, None, None):
                last_move = (-1, -1, -1)  # Безопасное значение для первого хода
            
            # 1. Выигрываем за 1 ход, если возможно
            winning_move = self.find_winning_move(board, player)
            if winning_move:
                return winning_move
                
            # 2. Блокируем выигрыш противника
            opponent = 3 - player
            blocking_move = self.find_winning_move(board, opponent)
            if blocking_move:
                return blocking_move
                
            # 3. Быстрый поиск оптимального хода (уменьшена глубина)
            best_move = self.smart_move_selection(board, player)
            return best_move
            
        except Exception as e:
            # Экстренный безопасный ход при любой ошибке
            return self.emergency_move(board)

    def find_winning_move(self, board: List[List[List[int]]], player: int) -> Tuple[int, int]:
        """Поиск немедленного выигрыша"""
        try:
            for x in range(4):
                for y in range(4):
                    drop_z = self.get_drop_position(board, x, y)
                    if drop_z is not None:
                        board[drop_z][y][x] = player
                        if self.check_win_from_position(board, x, y, drop_z, player):
                            board[drop_z][y][x] = 0
                            return (x, y)
                        board[drop_z][y][x] = 0
            return None
        except:
            return None

    def get_drop_position(self, board: List[List[List[int]]], x: int, y: int) -> int:
        """Определяет высоту падения фишки"""
        try:
            if x < 0 or x >= 4 or y < 0 or y >= 4:
                return None
            for z in range(4):
                if board[z][y][x] == 0:
                    return z
            return None
        except:
            return None

    def smart_move_selection(self, board: List[List[List[int]]], player: int) -> Tuple[int, int]:
        """Умный выбор хода без глубокой рекурсии"""
        try:
            valid_moves = self.get_valid_moves(board)
            if not valid_moves:
                return self.emergency_move(board)
            
            # Оцениваем каждый ход простым способом
            best_move = None
            best_score = float('-inf')
            
            for x, y in valid_moves:
                score = self.evaluate_move_simple(board, x, y, player)
                if score > best_score:
                    best_score = score
                    best_move = (x, y)
            
            return best_move if best_move else valid_moves[0]
        except:
            return self.emergency_move(board)

    def evaluate_move_simple(self, board, x, y, player):
        """Простая оценка хода без рекурсии"""
        try:
            drop_z = self.get_drop_position(board, x, y)
            if drop_z is None:
                return -1000
                
            score = 0
            
            # Приоритет центральным позициям
            center_bonus = 10 - (abs(x - 1.5) + abs(y - 1.5)) * 2
            score += center_bonus
            
            # Бонус за высоту (выше = лучше для блокировки)
            height_bonus = drop_z * 5
            score += height_bonus
            
            # Проверяем, создаёт ли ход угрозы
            board[drop_z][y][x] = player
            threats = self.count_threats(board, player)
            board[drop_z][y][x] = 0
            score += threats * 50
            
            return score
        except:
            return 0

    def count_threats(self, board, player):
        """Подсчёт количества угроз (3 в ряд + пустое место)"""
        try:
            threats = 0
            for line in self.get_key_lines():
                player_count = 0
                empty_count = 0
                
                for x, y, z in line:
                    if x < 0 or x >= 4 or y < 0 or y >= 4 or z < 0 or z >= 4:
                        continue
                    cell = board[z][y][x]
                    if cell == player:
                        player_count += 1
                    elif cell == 0:
                        empty_count += 1
                    else:
                        break  # есть фишки противника
                
                if player_count == 3 and empty_count == 1:
                    threats += 1
            
            return threats
        except:
            return 0

    def get_key_lines(self):
        """Основные выигрышные линии (сокращённый список)"""
        lines = []
        
        # Только самые важные линии для скорости
        try:
            # Вертикальные по Z (самые важные)
            for x in range(4):
                for y in range(4):
                    lines.append([(x, y, z) for z in range(4)])
            
            # Горизонтальные в центральных плоскостях
            for z in [1, 2]:  # только средние уровни
                for y in range(4):
                    for x in range(1):
                        lines.append([(x+i, y, z) for i in range(4)])
                for x in range(4):
                    for y in range(1):
                        lines.append([(x, y+i, z) for i in range(4)])
            
            # Основные диагонали
            lines.append([(i, i, i) for i in range(4)])  # главная диагональ
            lines.append([(i, i, 3-i) for i in range(4)])
            
        except:
            pass
            
        return lines

    def check_win_from_position(self, board, x, y, z, player):
        """Проверка победы от позиции"""
        try:
            # Быстрая проверка только ключевых направлений
            directions = [
                # Вертикаль по Z
                [(x, y, z+dz) for dz in range(-3, 1)],
                [(x, y, z+dz) for dz in range(-2, 2)],
                [(x, y, z+dz) for dz in range(-1, 3)],
                [(x, y, z+dz) for dz in range(0, 4)],
                # Горизонталь по X
                [(x+dx, y, z) for dx in range(-3, 1)],
                [(x+dx, y, z) for dx in range(-2, 2)],
                [(x+dx, y, z) for dx in range(-1, 3)],
                [(x+dx, y, z) for dx in range(0, 4)],
                # Горизонталь по Y
                [(x, y+dy, z) for dy in range(-3, 1)],
                [(x, y+dy, z) for dy in range(-2, 2)],
                [(x, y+dy, z) for dy in range(-1, 3)],
                [(x, y+dy, z) for dy in range(0, 4)],
            ]
            
            for line in directions:
                if len(line) == 4:
                    valid_line = True
                    for lx, ly, lz in line:
                        if lx < 0 or lx >= 4 or ly < 0 or ly >= 4 or lz < 0 or lz >= 4:
                            valid_line = False
                            break
                        if board[lz][ly][lx] != player:
                            valid_line = False
                            break
                    if valid_line:
                        return True
            
            return False
        except:
            return False

    def get_valid_moves(self, board):
        """Доступные ходы"""
        try:
            moves = []
            for x in range(4):
                for y in range(4):
                    if self.get_drop_position(board, x, y) is not None:
                        moves.append((x, y))
            return moves
        except:
            return [(1, 1), (1, 2), (2, 1), (2, 2)]  # запасные центральные ходы

    def emergency_move(self, board):
        """Экстренный безопасный ход"""
        try:
            # Пробуем центральные позиции
            safe_moves = [(1, 1), (1, 2), (2, 1), (2, 2), (0, 0), (0, 1), (1, 0)]
            
            for x, y in safe_moves:
                if 0 <= x < 4 and 0 <= y < 4:
                    if self.get_drop_position(board, x, y) is not None:
                        return (x, y)
            
            # Последняя попытка - любой валидный ход
            for x in range(4):
                for y in range(4):
                    if self.get_drop_position(board, x, y) is not None:
                        return (x, y)
            
            return (0, 0)  # совсем крайний случай
        except:
            return (0, 0)