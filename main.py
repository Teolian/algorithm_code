from typing import List, Tuple
import time
# from local_driver import Alg3D, Board # Для локального тестирования
from framework import Alg3D, Board # Для финальной отправки

class MyAI(Alg3D):
    def __init__(self):
        self.board_size = 4
        self.max_depth = 6  # Увеличена глубина поиска
        self.time_limit = 9.0  # Оставляем 1 сек запаса
        self.transposition_table = {}  # Таблица транспозиций для ускорения
        
    def get_move(
        self,
        board: List[List[List[int]]],
        player: int,
        last_move: Tuple[int, int, int]
    ) -> Tuple[int, int]:
        """Продвинутый 3D Connect 4 ИИ с глубокой стратегией"""
        
        start_time = time.time()
        self.start_time = start_time
        
        try:
            # Безопасная обработка first move
            if last_move is None or last_move == (None, None, None):
                # Первый ход - захватываем центр с небольшой рандомизацией
                return self.opening_move(board)
            
            # 1. НЕМЕДЛЕННАЯ ПОБЕДА - наивысший приоритет
            winning_move = self.find_winning_move(board, player)
            if winning_move:
                return winning_move
                
            # 2. КРИТИЧЕСКАЯ ЗАЩИТА - блокируем выигрыш противника
            opponent = 3 - player
            blocking_move = self.find_winning_move(board, opponent)
            if blocking_move:
                return blocking_move
                
            # 3. ТАКТИЧЕСКИЕ УГРОЗЫ - создаём двойные угрозы
            threat_move = self.find_threat_creation_move(board, player)
            if threat_move:
                return threat_move
                
            # 4. ГЛУБОКИЙ АНАЛИЗ - итеративный минимакс с увеличением глубины
            best_move = self.iterative_deepening_search(board, player, start_time)
            if best_move:
                return best_move
                
            # 5. ЗАПАСНОЙ РАЗУМНЫЙ ХОД
            return self.strategic_fallback_move(board, player)
            
        except Exception as e:
            return self.emergency_safe_move(board)

    def opening_move(self, board):
        """Оптимальный дебютный ход"""
        # Центральные позиции с приоритетом
        opening_priorities = [
            (1, 1), (2, 2), (1, 2), (2, 1),  # центр
            (0, 1), (1, 0), (3, 2), (2, 3),  # околоцентральные
            (0, 0), (3, 3), (0, 3), (3, 0)   # углы
        ]
        
        for x, y in opening_priorities:
            if self.get_drop_position(board, x, y) is not None:
                return (x, y)
        
        return (1, 1)  # запасной центральный ход

    def find_threat_creation_move(self, board, player):
        """Поиск ходов, создающих множественные угрозы"""
        try:
            opponent = 3 - player
            best_move = None
            max_threats_created = 0
            
            for x in range(4):
                for y in range(4):
                    drop_z = self.get_drop_position(board, x, y)
                    if drop_z is None:
                        continue
                        
                    # Делаем пробный ход
                    board[drop_z][y][x] = player
                    
                    # Считаем созданные угрозы
                    our_threats = self.count_immediate_threats(board, player)
                    their_threats = self.count_immediate_threats(board, opponent)
                    
                    # Оцениваем позицию
                    threat_value = our_threats * 3 - their_threats
                    
                    board[drop_z][y][x] = 0  # откатываем
                    
                    # Если создаём 2+ угрозы одновременно - это очень сильно!
                    if our_threats >= 2 and threat_value > max_threats_created:
                        max_threats_created = threat_value
                        best_move = (x, y)
            
            # Возвращаем только если создаём серьёзные угрозы
            return best_move if max_threats_created >= 2 else None
            
        except:
            return None

    def count_immediate_threats(self, board, player):
        """Подсчёт немедленных угроз (3 в ряд + пустое место)"""
        threats = 0
        try:
            for line in self.get_all_winning_lines():
                player_count = 0
                empty_positions = []
                blocked = False
                
                for x, y, z in line:
                    if not (0 <= x < 4 and 0 <= y < 4 and 0 <= z < 4):
                        blocked = True
                        break
                        
                    cell = board[z][y][x]
                    if cell == player:
                        player_count += 1
                    elif cell == 0:
                        empty_positions.append((x, y, z))
                    else:  # противник
                        blocked = True
                        break
                
                # Угроза = 3 наших + 1 пустое место (и это место доступно для хода)
                if not blocked and player_count == 3 and len(empty_positions) == 1:
                    empty_x, empty_y, empty_z = empty_positions[0]
                    # Проверяем, можем ли мы реально сделать этот ход
                    expected_drop_z = self.get_drop_position(board, empty_x, empty_y)
                    if expected_drop_z == empty_z:
                        threats += 1
            
            return threats
        except:
            return 0

    def iterative_deepening_search(self, board, player, start_time):
        """Итеративное углубление поиска с ограничением времени"""
        best_move = None
        
        try:
            # Начинаем с глубины 2 и увеличиваем
            for depth in range(2, self.max_depth + 1):
                if time.time() - start_time > self.time_limit - 1.0:
                    break
                    
                current_best = self.minimax_search_advanced(board, player, depth)
                if current_best:
                    best_move = current_best
                    
            return best_move
        except:
            return best_move

    def minimax_search_advanced(self, board, player, max_depth):
        """Продвинутый минимакс с альфа-бета и транспозициями"""
        try:
            best_score = float('-inf')
            best_move = None
            
            # Получаем ходы и сортируем их по эвристике
            moves = self.get_ordered_moves(board, player)
            
            for x, y in moves:
                if time.time() - self.start_time > self.time_limit:
                    break
                    
                drop_z = self.get_drop_position(board, x, y)
                if drop_z is None:
                    continue
                    
                # Делаем ход
                board[drop_z][y][x] = player
                
                # Минимакс с отсечением
                score = self.minimax_ab(board, max_depth - 1, False, player, 
                                      float('-inf'), float('inf'))
                
                # Откатываем ход
                board[drop_z][y][x] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (x, y)
            
            return best_move
        except:
            return None

    def get_ordered_moves(self, board, player):
        """Получение ходов, отсортированных по эвристической ценности"""
        moves_with_scores = []
        
        try:
            for x in range(4):
                for y in range(4):
                    drop_z = self.get_drop_position(board, x, y)
                    if drop_z is not None:
                        score = self.quick_move_evaluation(board, x, y, drop_z, player)
                        moves_with_scores.append(((x, y), score))
            
            # Сортируем по убыванию ценности
            moves_with_scores.sort(key=lambda x: x[1], reverse=True)
            return [move for move, score in moves_with_scores]
        except:
            return [(x, y) for x in range(4) for y in range(4) 
                   if self.get_drop_position(board, x, y) is not None]

    def quick_move_evaluation(self, board, x, y, z, player):
        """Быстрая эвристическая оценка хода"""
        score = 0
        
        try:
            # Приоритет центру
            center_score = 10 - (abs(x - 1.5) + abs(y - 1.5)) * 2
            score += center_score
            
            # Бонус за высоту (контроль верхних уровней)
            height_score = z * 3
            score += height_score
            
            # Делаем пробный ход для глубокой оценки
            board[z][y][x] = player
            
            # Оцениваем все линии, проходящие через эту позицию
            line_score = self.evaluate_position_lines(board, x, y, z, player)
            score += line_score
            
            board[z][y][x] = 0  # откатываем
            
            return score
        except:
            return 0

    def evaluate_position_lines(self, board, pos_x, pos_y, pos_z, player):
        """Оценка всех линий, проходящих через позицию"""
        total_score = 0
        opponent = 3 - player
        
        try:
            # Все возможные направления от данной позиции
            directions = [
                (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
                (1, 1, 0), (-1, -1, 0), (1, -1, 0), (-1, 1, 0),
                (1, 0, 1), (-1, 0, -1), (1, 0, -1), (-1, 0, 1),
                (0, 1, 1), (0, -1, -1), (0, 1, -1), (0, -1, 1),
                (1, 1, 1), (-1, -1, -1), (1, 1, -1), (-1, -1, 1),
                (1, -1, 1), (-1, 1, -1), (1, -1, -1), (-1, 1, 1)
            ]
            
            for dx, dy, dz in directions:
                line_score = self.evaluate_line_direction(board, pos_x, pos_y, pos_z, 
                                                        dx, dy, dz, player, opponent)
                total_score += line_score
                
            return total_score
        except:
            return 0

    def evaluate_line_direction(self, board, start_x, start_y, start_z, 
                               dx, dy, dz, player, opponent):
        """Оценка линии в конкретном направлении"""
        try:
            # Собираем 4 позиции в направлении
            for start_offset in range(-3, 1):
                line = []
                for i in range(4):
                    x = start_x + (start_offset + i) * dx
                    y = start_y + (start_offset + i) * dy
                    z = start_z + (start_offset + i) * dz
                    
                    if 0 <= x < 4 and 0 <= y < 4 and 0 <= z < 4:
                        line.append((x, y, z))
                    else:
                        break
                
                if len(line) == 4:
                    score = self.evaluate_line_pattern(board, line, player, opponent)
                    if score != 0:
                        return score
            
            return 0
        except:
            return 0

    def evaluate_line_pattern(self, board, line, player, opponent):
        """Оценка паттерна в линии из 4 позиций"""
        try:
            player_count = 0
            opponent_count = 0
            empty_count = 0
            
            for x, y, z in line:
                cell = board[z][y][x]
                if cell == player:
                    player_count += 1
                elif cell == opponent:
                    opponent_count += 1
                else:
                    empty_count += 1
            
            # Если есть фишки обеих сторон - линия заблокирована
            if player_count > 0 and opponent_count > 0:
                return 0
            
            # Оценочная таблица паттернов
            if player_count == 4:
                return 100000  # победа
            elif opponent_count == 4:
                return -100000  # поражение
            elif player_count == 3 and empty_count == 1:
                return 5000  # серьёзная угроза
            elif opponent_count == 3 and empty_count == 1:
                return -5000  # нужно блокировать
            elif player_count == 2 and empty_count == 2:
                return 200  # хорошая позиция
            elif opponent_count == 2 and empty_count == 2:
                return -200  # позиция противника
            elif player_count == 1 and empty_count == 3:
                return 20  # потенциал
            elif opponent_count == 1 and empty_count == 3:
                return -20  # потенциал противника
            
            return 0
        except:
            return 0

    def minimax_ab(self, board, depth, is_maximizing, original_player, alpha, beta):
        """Минимакс с альфа-бета отсечением"""
        try:
            # Проверка времени
            if time.time() - self.start_time > self.time_limit:
                return self.fast_position_evaluation(board, original_player)
            
            # Проверка глубины
            if depth <= 0:
                return self.advanced_position_evaluation(board, original_player)
            
            # Проверка окончания игры
            winner = self.check_game_winner(board)
            if winner == original_player:
                return 100000 + depth  # победа быстрее = лучше
            elif winner == (3 - original_player):
                return -100000 - depth  # поражение позже = лучше
            elif winner == 0:
                return 0  # ничья
            
            current_player = original_player if is_maximizing else (3 - original_player)
            moves = self.get_valid_moves(board)
            
            if not moves:
                return self.advanced_position_evaluation(board, original_player)
            
            if is_maximizing:
                max_score = float('-inf')
                for x, y in moves:
                    drop_z = self.get_drop_position(board, x, y)
                    if drop_z is None:
                        continue
                        
                    board[drop_z][y][x] = current_player
                    score = self.minimax_ab(board, depth - 1, False, original_player, alpha, beta)
                    board[drop_z][y][x] = 0
                    
                    max_score = max(max_score, score)
                    alpha = max(alpha, score)
                    
                    if beta <= alpha:
                        break  # альфа-бета отсечение
                        
                return max_score
            else:
                min_score = float('inf')
                for x, y in moves:
                    drop_z = self.get_drop_position(board, x, y)
                    if drop_z is None:
                        continue
                        
                    board[drop_z][y][x] = current_player
                    score = self.minimax_ab(board, depth - 1, True, original_player, alpha, beta)
                    board[drop_z][y][x] = 0
                    
                    min_score = min(min_score, score)
                    beta = min(beta, score)
                    
                    if beta <= alpha:
                        break  # альфа-бета отсечение
                        
                return min_score
        except:
            return 0

    def advanced_position_evaluation(self, board, player):
        """Продвинутая оценка позиции"""
        try:
            score = 0
            opponent = 3 - player
            
            # Анализируем все выигрышные линии
            for line in self.get_all_winning_lines():
                line_score = self.evaluate_line_pattern(board, line, player, opponent)
                score += line_score
            
            # Дополнительные стратегические факторы
            
            # Контроль центра
            center_control = 0
            for x in [1, 2]:
                for y in [1, 2]:
                    for z in range(4):
                        cell = board[z][y][x]
                        if cell == player:
                            center_control += (z + 1) * 2  # выше = лучше
                        elif cell == opponent:
                            center_control -= (z + 1) * 2
            
            score += center_control
            
            # Контроль высот (важно в 3D Connect 4)
            height_control = 0
            for x in range(4):
                for y in range(4):
                    our_height = 0
                    their_height = 0
                    
                    for z in range(4):
                        if board[z][y][x] == player:
                            our_height = z + 1
                        elif board[z][y][x] == opponent:
                            their_height = z + 1
                    
                    height_control += (our_height - their_height)
            
            score += height_control * 5
            
            return score
        except:
            return 0

    def fast_position_evaluation(self, board, player):
        """Быстрая оценка для случаев нехватки времени"""
        try:
            score = 0
            opponent = 3 - player
            
            # Только самые важные линии
            key_lines = self.get_critical_lines()
            
            for line in key_lines:
                line_score = self.evaluate_line_pattern(board, line, player, opponent)
                score += line_score
            
            return score
        except:
            return 0

    def get_critical_lines(self):
        """Критически важные выигрышные линии"""
        lines = []
        
        try:
            # Вертикальные (самые важные в Connect 4)
            for x in range(4):
                for y in range(4):
                    lines.append([(x, y, z) for z in range(4)])
            
            # Центральные горизонтальные
            for z in [1, 2]:
                for y in [1, 2]:
                    for x in range(1):
                        lines.append([(x+i, y, z) for i in range(4)])
                for x in [1, 2]:
                    for y in range(1):
                        lines.append([(x, y+i, z) for i in range(4)])
            
            # Главные диагонали
            lines.append([(i, i, i) for i in range(4)])
            lines.append([(i, i, 3-i) for i in range(4)])
            lines.append([(i, 3-i, i) for i in range(4)])
            lines.append([(3-i, i, i) for i in range(4)])
            
        except:
            pass
            
        return lines

    # Вспомогательные функции (оптимизированные версии)
    
    def find_winning_move(self, board, player):
        """Поиск выигрышного хода"""
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

    def get_drop_position(self, board, x, y):
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

    def check_win_from_position(self, board, x, y, z, player):
        """Проверка победы от позиции"""
        try:
            for line in self.get_all_winning_lines():
                if (x, y, z) in line:
                    if all(0 <= lx < 4 and 0 <= ly < 4 and 0 <= lz < 4 and 
                          board[lz][ly][lx] == player for lx, ly, lz in line):
                        return True
            return False
        except:
            return False

    def get_all_winning_lines(self):
        """Все выигрышные линии (полный список)"""
        lines = []
        
        try:
            # Горизонтальные в плоскостях XY
            for z in range(4):
                for y in range(4):
                    for x in range(1):
                        lines.append([(x+i, y, z) for i in range(4)])
                for x in range(4):
                    for y in range(1):
                        lines.append([(x, y+i, z) for i in range(4)])
            
            # Вертикальные по Z
            for x in range(4):
                for y in range(4):
                    lines.append([(x, y, z) for z in range(4)])
            
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

    def check_game_winner(self, board):
        """Проверка победителя"""
        try:
            for line in self.get_all_winning_lines():
                if all(0 <= x < 4 and 0 <= y < 4 and 0 <= z < 4 for x, y, z in line):
                    first_cell = board[line[0][2]][line[0][1]][line[0][0]]
                    if first_cell != 0:
                        if all(board[z][y][x] == first_cell for x, y, z in line):
                            return first_cell
            
            if not self.get_valid_moves(board):
                return 0  # ничья
            return None
        except:
            return None

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
            return [(1, 1), (2, 2)]

    def strategic_fallback_move(self, board, player):
        """Стратегический запасной ход"""
        try:
            moves = self.get_valid_moves(board)
            if not moves:
                return (1, 1)
            
            # Приоритет центральным позициям
            center_moves = [(x, y) for x, y in moves if 1 <= x <= 2 and 1 <= y <= 2]
            if center_moves:
                return center_moves[0]
            
            return moves[0]
        except:
            return (1, 1)

    def emergency_safe_move(self, board):
        """Экстренный безопасный ход"""
        safe_positions = [(1, 1), (2, 2), (1, 2), (2, 1), (0, 0), (3, 3)]
        
        for x, y in safe_positions:
            try:
                if self.get_drop_position(board, x, y) is not None:
                    return (x, y)
            except:
                continue
        
        return (0, 0)