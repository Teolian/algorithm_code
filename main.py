from typing import List, Tuple, Optional, Set
import time
# from local_driver import Alg3D, Board # Для локального тестирования
from framework import Alg3D, Board # Для финальной отправки

class MyAI(Alg3D):
    def __init__(self):
        self.max_time = 8.5  # Используем максимум времени
        self.evaluated_positions = {}  # Кэш позиций
        
    def get_move(
        self,
        board: List[List[List[int]]],  # [z][y][x]
        player: int,
        last_move: Tuple[int, int, int]
    ) -> Tuple[int, int]:
        """
        Продвинутый ИИ основанный на математическом решении Connect 4
        Использует threat space analysis и продвинутые стратегии
        """
        
        start_time = time.time()
        
        try:
            # ФАЗА 1: КРИТИЧЕСКИЕ ПРОВЕРКИ
            
            # Немедленная победа
            win_move = self.find_immediate_win(board, player)
            if win_move:
                return win_move
                
            # Блокировка немедленного проигрыша
            opponent = 3 - player
            block_move = self.find_immediate_win(board, opponent)
            if block_move:
                return block_move
                
            # ФАЗА 2: СТРАТЕГИЧЕСКИЕ РЕШЕНИЯ
            
            # Если первый ход - играем оптимально (математически доказано)
            if self.is_early_game(board):
                opening_move = self.get_opening_move(board, player)
                if opening_move:
                    return opening_move
            
            # ФАЗА 3: THREAT SPACE ANALYSIS
            
            # Поиск двойных угроз (неблокируемых комбинаций)
            double_threat = self.find_double_threat_move(board, player, start_time)
            if double_threat:
                return double_threat
                
            # Блокировка двойных угроз противника
            block_double = self.find_double_threat_move(board, opponent, start_time)
            if block_double:
                return block_double
            
            # ФАЗА 4: ПРОДВИНУТЫЙ АНАЛИЗ
            
            # Поиск лучшего хода с глубоким анализом
            best_move = self.advanced_move_search(board, player, start_time)
            return best_move if best_move else self.strategic_fallback(board)
            
        except Exception:
            return self.safe_emergency_move(board)

    def find_immediate_win(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """Поиск немедленной победы"""
        try:
            for x in range(4):
                for y in range(4):
                    drop_z = self.get_drop_position(board, x, y)
                    if drop_z is not None:
                        # Симулируем ход
                        board[drop_z][y][x] = player
                        if self.check_win_fast(board, player, x, y, drop_z):
                            board[drop_z][y][x] = 0
                            return (x, y)
                        board[drop_z][y][x] = 0
            return None
        except:
            return None

    def is_early_game(self, board: List[List[List[int]]]) -> bool:
        """Определяет, ранняя ли стадия игры"""
        try:
            move_count = 0
            for x in range(4):
                for y in range(4):
                    for z in range(4):
                        if board[z][y][x] != 0:
                            move_count += 1
            return move_count <= 4
        except:
            return False

    def get_opening_move(self, board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int]]:
        """
        Оптимальные дебютные ходы основанные на математическом решении
        Первый игрок: центр гарантирует победу
        Второй игрок: оптимальная защита
        """
        try:
            move_count = sum(1 for x in range(4) for y in range(4) for z in range(4) if board[z][y][x] != 0)
            
            if move_count == 0 and player == 1:
                # Первый ход - центр (математически доказано лучший)
                return (1, 1)  # Центральная позиция для 4x4
                
            elif move_count == 1 and player == 2:
                # Оптимальный ответ на центральный ход противника
                if board[0][1][1] == 1:  # Противник взял центр
                    # Контролируем второй центральный квадрат
                    return (2, 2)
                    
            elif move_count == 2 and player == 1:
                # Развиваем центральную стратегию
                center_positions = [(1, 2), (2, 1), (2, 2)]
                for x, y in center_positions:
                    if self.get_drop_position(board, x, y) is not None:
                        return (x, y)
                        
            return None
        except:
            return None

    def find_double_threat_move(self, board: List[List[List[int]]], player: int, start_time: float) -> Optional[Tuple[int, int]]:
        """
        Threat Space Analysis - поиск ходов, создающих двойные угрозы
        Двойная угроза = две возможности выиграть одновременно (неблокируемо)
        """
        try:
            if time.time() - start_time > self.max_time - 2.0:
                return None
                
            best_move = None
            max_threat_score = 0
            
            for x in range(4):
                for y in range(4):
                    drop_z = self.get_drop_position(board, x, y)
                    if drop_z is None:
                        continue
                        
                    # Симулируем ход
                    board[drop_z][y][x] = player
                    
                    # Анализируем создаваемые угрозы
                    threat_score = self.analyze_threat_space(board, player)
                    
                    board[drop_z][y][x] = 0
                    
                    if threat_score > max_threat_score:
                        max_threat_score = threat_score
                        best_move = (x, y)
            
            # Возвращаем только если создаём серьёзные угрозы
            return best_move if max_threat_score >= 2000 else None
            
        except:
            return None

    def analyze_threat_space(self, board: List[List[List[int]]], player: int) -> int:
        """
        Анализ пространства угроз - ключевая стратегия из исследований Алиса
        """
        try:
            score = 0
            opponent = 3 - player
            
            # Подсчитываем различные типы угроз
            immediate_threats = 0
            potential_threats = 0
            blocking_opportunities = 0
            
            # Анализируем все возможные выигрышные линии
            for line in self.get_all_winning_lines():
                line_analysis = self.analyze_line_threats(board, line, player, opponent)
                
                if line_analysis['immediate_threat']:
                    immediate_threats += 1
                    score += 10000  # Критически важно
                elif line_analysis['potential_threat']:
                    potential_threats += 1
                    score += 1000
                elif line_analysis['blocking_needed']:
                    blocking_opportunities += 1
                    score -= 500
                    
                # Бонус за "Figure 7" паттерны
                if line_analysis['figure_7_setup']:
                    score += 2000
                    
            # Двойная угроза = 2+ немедленных угрозы
            if immediate_threats >= 2:
                score += 5000  # Гарантированная победа
                
            # Контроль центра (математически важно)
            center_control = self.evaluate_center_control(board, player)
            score += center_control * 10
            
            return score
            
        except:
            return 0

    def analyze_line_threats(self, board: List[List[List[int]]], line: List[Tuple[int, int, int]], player: int, opponent: int) -> dict:
        """Детальный анализ угроз в линии"""
        try:
            our_count = 0
            their_count = 0
            empty_positions = []
            
            for x, y, z in line:
                if not (0 <= x < 4 and 0 <= y < 4 and 0 <= z < 4):
                    return {'immediate_threat': False, 'potential_threat': False, 'blocking_needed': False, 'figure_7_setup': False}
                    
                cell = board[z][y][x]
                if cell == player:
                    our_count += 1
                elif cell == opponent:
                    their_count += 1
                else:
                    empty_positions.append((x, y, z))
            
            # Линия заблокирована
            if our_count > 0 and their_count > 0:
                return {'immediate_threat': False, 'potential_threat': False, 'blocking_needed': False, 'figure_7_setup': False}
            
            # Немедленная угроза (3 + 1 пустое, доступное для хода)
            immediate_threat = (our_count == 3 and len(empty_positions) == 1 and 
                              self.is_position_playable(board, empty_positions[0]))
            
            # Нужно блокировать противника
            blocking_needed = (their_count == 3 and len(empty_positions) == 1 and 
                             self.is_position_playable(board, empty_positions[0]))
            
            # Потенциальная угроза (2 + 2 пустых)
            potential_threat = (our_count == 2 and len(empty_positions) == 2 and
                              any(self.is_position_playable(board, pos) for pos in empty_positions))
            
            # Figure 7 setup (специальный паттерн)
            figure_7_setup = self.detect_figure_7_pattern(board, line, player)
            
            return {
                'immediate_threat': immediate_threat,
                'potential_threat': potential_threat,
                'blocking_needed': blocking_needed,
                'figure_7_setup': figure_7_setup
            }
        except:
            return {'immediate_threat': False, 'potential_threat': False, 'blocking_needed': False, 'figure_7_setup': False}

    def detect_figure_7_pattern(self, board: List[List[List[int]]], line: List[Tuple[int, int, int]], player: int) -> bool:
        """Обнаружение паттерна Figure 7 - мощная стратегия"""
        try:
            # Figure 7: 3 по диагонали + верхний является частью горизонтальной линии
            if len(line) != 4:
                return False
                
            # Проверяем, является ли линия диагональю
            is_diagonal = self.is_diagonal_line(line)
            if not is_diagonal:
                return False
                
            # Проверяем наличие наших фишек в диагонали
            our_positions = []
            for i, (x, y, z) in enumerate(line):
                if board[z][y][x] == player:
                    our_positions.append(i)
            
            if len(our_positions) >= 2:
                # Проверяем возможность горизонтального расширения от верхних позиций
                for pos_idx in our_positions:
                    x, y, z = line[pos_idx]
                    if self.has_horizontal_potential(board, x, y, z, player):
                        return True
                        
            return False
        except:
            return False

    def is_diagonal_line(self, line: List[Tuple[int, int, int]]) -> bool:
        """Проверяет, является ли линия диагональю"""
        try:
            if len(line) != 4:
                return False
                
            # Проверяем различные типы диагоналей
            x_diff = line[1][0] - line[0][0]
            y_diff = line[1][1] - line[0][1] 
            z_diff = line[1][2] - line[0][2]
            
            # Диагональ если есть изменения по двум или трём осям
            non_zero_diffs = sum(1 for diff in [x_diff, y_diff, z_diff] if diff != 0)
            return non_zero_diffs >= 2
        except:
            return False

    def has_horizontal_potential(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> bool:
        """Проверяет потенциал горизонтального расширения"""
        try:
            # Проверяем горизонтальные направления от данной позиции
            directions = [
                [(0, 1, 0), (0, -1, 0)],  # Y направления
                [(1, 0, 0), (-1, 0, 0)]   # X направления
            ]
            
            for dir_pair in directions:
                count = 1  # текущая позиция
                for dx, dy, dz in dir_pair:
                    nx, ny, nz = x + dx, y + dy, z + dz
                    while (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4):
                        if board[nz][ny][nx] == player:
                            count += 1
                            nx += dx
                            ny += dy
                            nz += dz
                        elif board[nz][ny][nx] == 0:
                            # Пустое место - потенциал для расширения
                            break
                        else:
                            # Противник блокирует
                            break
                
                if count >= 2:  # Есть потенциал
                    return True
                    
            return False
        except:
            return False

    def is_position_playable(self, board: List[List[List[int]]], pos: Tuple[int, int, int]) -> bool:
        """Проверяет, можно ли реально поставить фишку в позицию"""
        try:
            x, y, z = pos
            expected_drop_z = self.get_drop_position(board, x, y)
            return expected_drop_z == z
        except:
            return False

    def evaluate_center_control(self, board: List[List[List[int]]], player: int) -> int:
        """Оценка контроля центра (математически критично)"""
        try:
            score = 0
            center_positions = [
                (1, 1), (1, 2), (2, 1), (2, 2)  # центральные 4 позиции
            ]
            
            for x, y in center_positions:
                for z in range(4):
                    cell = board[z][y][x]
                    if cell == player:
                        score += (z + 1) * 2  # Выше = лучше
                    elif cell == (3 - player):
                        score -= (z + 1) * 2
                        
            return score
        except:
            return 0

    def advanced_move_search(self, board: List[List[List[int]]], player: int, start_time: float) -> Optional[Tuple[int, int]]:
        """Продвинутый поиск хода с ограничением времени"""
        try:
            if time.time() - start_time > self.max_time - 1.0:
                return self.strategic_fallback(board)
                
            best_move = None
            best_score = float('-inf')
            
            # Получаем все возможные ходы
            moves = self.get_ordered_moves(board)
            
            for x, y in moves:
                if time.time() - start_time > self.max_time - 0.5:
                    break
                    
                drop_z = self.get_drop_position(board, x, y)
                if drop_z is None:
                    continue
                    
                # Оцениваем ход
                score = self.evaluate_move_advanced(board, x, y, drop_z, player)
                
                if score > best_score:
                    best_score = score
                    best_move = (x, y)
            
            return best_move
        except:
            return None

    def evaluate_move_advanced(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> float:
        """Продвинутая оценка хода"""
        try:
            # Симулируем ход
            board[z][y][x] = player
            
            score = 0.0
            opponent = 3 - player
            
            # Threat space analysis
            threat_score = self.analyze_threat_space(board, player)
            score += threat_score
            
            # Контроль позиции
            position_score = self.evaluate_position_control(board, x, y, z, player)
            score += position_score
            
            # Стратегическая ценность
            strategic_score = self.evaluate_strategic_value(board, x, y, z, player)
            score += strategic_score
            
            board[z][y][x] = 0  # откат
            
            return score
        except:
            return 0.0

    def evaluate_position_control(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> float:
        """Оценка контроля позиции"""
        try:
            score = 0.0
            
            # Центральные позиции важнее
            center_distance = abs(x - 1.5) + abs(y - 1.5)
            score += (3 - center_distance) * 50
            
            # Высота дает преимущество
            score += z * 20
            
            # Количество линий, проходящих через позицию
            lines_through_pos = sum(1 for line in self.get_all_winning_lines() if (x, y, z) in line)
            score += lines_through_pos * 30
            
            return score
        except:
            return 0.0

    def evaluate_strategic_value(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> float:
        """Стратегическая ценность хода"""
        try:
            score = 0.0
            
            # Связность с другими нашими фишками
            connectivity = self.calculate_connectivity(board, x, y, z, player)
            score += connectivity * 25
            
            # Блокировка противника
            blocking_value = self.calculate_blocking_value(board, x, y, z, 3 - player)
            score += blocking_value * 40
            
            # Создание будущих возможностей
            future_potential = self.calculate_future_potential(board, x, y, z, player)
            score += future_potential * 15
            
            return score
        except:
            return 0.0

    def calculate_connectivity(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> int:
        """Подсчёт связности с другими фишками"""
        try:
            connectivity = 0
            directions = [
                (1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1),
                (1,1,0), (-1,-1,0), (1,-1,0), (-1,1,0),
                (1,0,1), (-1,0,-1), (1,0,-1), (-1,0,1),
                (0,1,1), (0,-1,-1), (0,1,-1), (0,-1,1),
                (1,1,1), (-1,-1,-1), (1,1,-1), (-1,-1,1),
                (1,-1,1), (-1,1,-1), (1,-1,-1), (-1,1,1)
            ]
            
            for dx, dy, dz in directions:
                nx, ny, nz = x + dx, y + dy, z + dz
                if (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4 and 
                    board[nz][ny][nx] == player):
                    connectivity += 1
                    
            return connectivity
        except:
            return 0

    def calculate_blocking_value(self, board: List[List[List[int]]], x: int, y: int, z: int, opponent: int) -> int:
        """Ценность блокировки противника"""
        try:
            # Временно ставим фишку противника и считаем его угрозы
            board[z][y][x] = opponent
            opponent_threats = self.analyze_threat_space(board, opponent)
            board[z][y][x] = 0
            
            # Чем больше угроз блокируем, тем лучше
            return min(opponent_threats // 100, 50)  # Ограничиваем максимум
        except:
            return 0

    def calculate_future_potential(self, board: List[List[List[int]]], x: int, y: int, z: int, player: int) -> int:
        """Потенциал для будущих ходов"""
        try:
            potential = 0
            
            # Проверяем, создаём ли основу для будущих угроз
            for line in self.get_all_winning_lines():
                if (x, y, z) in line:
                    our_count = sum(1 for lx, ly, lz in line if board[lz][ly][lx] == player)
                    empty_count = sum(1 for lx, ly, lz in line if board[lz][ly][lx] == 0)
                    
                    if our_count == 1 and empty_count == 3:
                        potential += 10
                    elif our_count == 2 and empty_count == 2:
                        potential += 25
                        
            return potential
        except:
            return 0

    def get_ordered_moves(self, board: List[List[List[int]]]) -> List[Tuple[int, int]]:
        """Упорядоченные ходы (центр первым)"""
        try:
            moves = []
            
            # Сначала центральные
            center_moves = [(1, 1), (1, 2), (2, 1), (2, 2)]
            for x, y in center_moves:
                if self.get_drop_position(board, x, y) is not None:
                    moves.append((x, y))
            
            # Затем остальные
            for x in range(4):
                for y in range(4):
                    if (x, y) not in center_moves and self.get_drop_position(board, x, y) is not None:
                        moves.append((x, y))
                        
            return moves
        except:
            return [(1, 1), (2, 2)]

    # Вспомогательные функции

    def get_drop_position(self, board: List[List[List[int]]], x: int, y: int) -> Optional[int]:
        """Позиция падения фишки"""
        try:
            if not (0 <= x < 4 and 0 <= y < 4):
                return None
            for z in range(4):
                if board[z][y][x] == 0:
                    return z
            return None
        except:
            return None

    def check_win_fast(self, board: List[List[List[int]]], player: int, x: int, y: int, z: int) -> bool:
        """Быстрая проверка победы от позиции"""
        try:
            # Проверяем основные направления
            directions = [
                [(1,0,0), (-1,0,0)],  # X
                [(0,1,0), (0,-1,0)],  # Y  
                [(0,0,1), (0,0,-1)],  # Z
                [(1,1,0), (-1,-1,0)], # XY диагонали
                [(1,-1,0), (-1,1,0)],
                [(1,0,1), (-1,0,-1)], # XZ диагонали
                [(1,0,-1), (-1,0,1)],
                [(0,1,1), (0,-1,-1)], # YZ диагонали
                [(0,1,-1), (0,-1,1)],
                [(1,1,1), (-1,-1,-1)], # 3D диагонали
                [(1,1,-1), (-1,-1,1)],
                [(1,-1,1), (-1,1,-1)],
                [(1,-1,-1), (-1,1,1)]
            ]
            
            for dir_pair in directions:
                count = 1
                for dx, dy, dz in dir_pair:
                    nx, ny, nz = x + dx, y + dy, z + dz
                    while (0 <= nx < 4 and 0 <= ny < 4 and 0 <= nz < 4 and 
                           board[nz][ny][nx] == player):
                        count += 1
                        nx += dx
                        ny += dy
                        nz += dz
                        
                if count >= 4:
                    return True
                    
            return False
        except:
            return False

    def get_all_winning_lines(self) -> List[List[Tuple[int, int, int]]]:
        """Все выигрышные линии"""
        lines = []
        
        try:
            # Вертикальные
            for x in range(4):
                for y in range(4):
                    lines.append([(x, y, z) for z in range(4)])
            
            # Горизонтальные X
            for z in range(4):
                for y in range(4):
                    for x in range(1):
                        lines.append([(x+i, y, z) for i in range(4)])
            
            # Горизонтальные Y
            for z in range(4):
                for x in range(4):
                    for y in range(1):
                        lines.append([(x, y+i, z) for i in range(4)])
            
            # Диагонали в плоскостях XY
            for z in range(4):
                lines.append([(i, i, z) for i in range(4)])
                lines.append([(i, 3-i, z) for i in range(4)])
            
            # Диагонали в плоскостях XZ  
            for y in range(4):
                lines.append([(i, y, i) for i in range(4)])
                lines.append([(i, y, 3-i) for i in range(4)])
            
            # Диагонали в плоскостях YZ
            for x in range(4):
                lines.append([(x, i, i) for i in range(4)])
                lines.append([(x, i, 3-i) for i in range(4)])
            
            # Пространственные диагонали
            lines.append([(i, i, i) for i in range(4)])
            lines.append([(i, i, 3-i) for i in range(4)])
            lines.append([(i, 3-i, i) for i in range(4)])
            lines.append([(3-i, i, i) for i in range(4)])
            
        except:
            pass
            
        return lines

    def strategic_fallback(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Стратегический запасной ход"""
        try:
            # Приоритет центральным позициям
            priority_moves = [
                (1, 1), (2, 2), (1, 2), (2, 1),  # центр
                (0, 1), (1, 0), (3, 2), (2, 3),  # около центра
                (0, 0), (3, 3), (0, 3), (3, 0)   # углы
            ]
            
            for x, y in priority_moves:
                if self.get_drop_position(board, x, y) is not None:
                    return (x, y)
                    
            # Любой доступный ход
            for x in range(4):
                for y in range(4):
                    if self.get_drop_position(board, x, y) is not None:
                        return (x, y)
                        
            return (0, 0)
        except:
            return (0, 0)

    def safe_emergency_move(self, board: List[List[List[int]]]) -> Tuple[int, int]:
        """Экстренный безопасный ход"""
        try:
            safe_positions = [(1, 1), (2, 2), (0, 0)]
            for x, y in safe_positions:
                if self.get_drop_position(board, x, y) is not None:
                    return (x, y)
            return (0, 0)
        except:
            return (0, 0)