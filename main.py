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
        last_move: Tuple[int, int, int] # последний ход (x, y, z)
    ) -> Tuple[int, int]:
        """3D Connect 4 ИИ - возвращает лучший ход (x, y)"""
        
        # 1. Выигрываем за 1 ход, если возможно
        winning_move = self.find_winning_move(board, player)
        if winning_move:
            return winning_move
            
        # 2. Блокируем выигрыш противника
        opponent = 3 - player
        blocking_move = self.find_winning_move(board, opponent)
        if blocking_move:
            return blocking_move
            
        # 3. Минимакс поиск оптимального хода
        best_move = self.minimax_search(board, player)
        return best_move if best_move else self.get_fallback_move(board)

    def find_winning_move(self, board: List[List[List[int]]], player: int) -> Tuple[int, int]:
        """Поиск немедленного выигрыша"""
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

    def get_drop_position(self, board: List[List[List[int]]], x: int, y: int) -> int:
        """Определяет высоту падения фишки"""
        for z in range(4):
            if board[z][y][x] == 0:
                return z
        return None

    def minimax_search(self, board: List[List[List[int]]], player: int) -> Tuple[int, int]:
        """Минимакс с альфа-бета отсечением"""
        best_score = float('-inf')
        best_move = None
        
        valid_moves = self.get_valid_moves(board)
        if not valid_moves:
            return None
        
        # Сортируем ходы по приоритету (центр важнее)
        valid_moves.sort(key=lambda move: abs(move[0]-1.5) + abs(move[1]-1.5))
        
        for x, y in valid_moves:
            drop_z = self.get_drop_position(board, x, y)
            if drop_z is None:
                continue
                
            board[drop_z][y][x] = player
            score = self.minimax(board, 3, False, player, float('-inf'), float('inf'))
            board[drop_z][y][x] = 0
            
            if score > best_score:
                best_score = score
                best_move = (x, y)
                
        return best_move

    def minimax(self, board, depth, is_maximizing, original_player, alpha, beta):
        """Рекурсивный минимакс"""
        if depth == 0:
            return self.evaluate_position(board, original_player)
            
        game_result = self.check_game_winner(board)
        if game_result == original_player:
            return 10000
        elif game_result == (3 - original_player):
            return -10000
        elif game_result == 0:
            return 0
        
        current_player = original_player if is_maximizing else (3 - original_player)
        valid_moves = self.get_valid_moves(board)
        
        if not valid_moves:
            return self.evaluate_position(board, original_player)
            
        if is_maximizing:
            max_score = float('-inf')
            for x, y in valid_moves:
                drop_z = self.get_drop_position(board, x, y)
                if drop_z is None:
                    continue
                    
                board[drop_z][y][x] = current_player
                score = self.minimax(board, depth-1, False, original_player, alpha, beta)
                board[drop_z][y][x] = 0
                
                max_score = max(max_score, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return max_score
        else:
            min_score = float('inf')
            for x, y in valid_moves:
                drop_z = self.get_drop_position(board, x, y)
                if drop_z is None:
                    continue
                    
                board[drop_z][y][x] = current_player
                score = self.minimax(board, depth-1, True, original_player, alpha, beta)
                board[drop_z][y][x] = 0
                
                min_score = min(min_score, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return min_score

    def evaluate_position(self, board: List[List[List[int]]], player: int) -> int:
        """Оценка позиции"""
        score = 0
        opponent = 3 - player
        
        for line in self.get_all_lines():
            player_count = sum(1 for x,y,z in line if board[z][y][x] == player)
            opponent_count = sum(1 for x,y,z in line if board[z][y][x] == opponent)
            empty_count = sum(1 for x,y,z in line if board[z][y][x] == 0)
            
            if player_count > 0 and opponent_count > 0:
                continue  # заблокированная линия
                
            if player_count == 3 and empty_count == 1:
                score += 500
            elif opponent_count == 3 and empty_count == 1:
                score -= 500
            elif player_count == 2 and empty_count == 2:
                score += 50
            elif opponent_count == 2 and empty_count == 2:
                score -= 50
            elif player_count == 1 and empty_count == 3:
                score += 5
            elif opponent_count == 1 and empty_count == 3:
                score -= 5
                
        return score

    def get_all_lines(self):
        """Все выигрышные линии"""
        lines = []
        
        # Горизонтальные в XY плоскостях
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
        
        # Диагонали XY
        for z in range(4):
            lines.append([(i, i, z) for i in range(4)])
            lines.append([(i, 3-i, z) for i in range(4)])
        
        # Диагонали XZ
        for y in range(4):
            lines.append([(i, y, i) for i in range(4)])
            lines.append([(i, y, 3-i) for i in range(4)])
        
        # Диагонали YZ
        for x in range(4):
            lines.append([(x, i, i) for i in range(4)])
            lines.append([(x, i, 3-i) for i in range(4)])
        
        # 3D диагонали
        lines.append([(i, i, i) for i in range(4)])
        lines.append([(i, i, 3-i) for i in range(4)])
        lines.append([(i, 3-i, i) for i in range(4)])
        lines.append([(3-i, i, i) for i in range(4)])
        
        return lines

    def check_win_from_position(self, board, x, y, z, player):
        """Проверка победы от позиции"""
        for line in self.get_all_lines():
            if (x, y, z) in line:
                if all(board[lz][ly][lx] == player for lx, ly, lz in line):
                    return True
        return False

    def check_game_winner(self, board):
        """Проверка победителя"""
        for line in self.get_all_lines():
            first_pos = line[0]
            first_cell = board[first_pos[2]][first_pos[1]][first_pos[0]]
            if first_cell != 0:
                if all(board[z][y][x] == first_cell for x, y, z in line):
                    return first_cell
        
        if not self.get_valid_moves(board):
            return 0  # ничья
        return None

    def get_valid_moves(self, board):
        """Доступные ходы"""
        moves = []
        for x in range(4):
            for y in range(4):
                if self.get_drop_position(board, x, y) is not None:
                    moves.append((x, y))
        return moves

    def get_fallback_move(self, board):
        """Запасной ход"""
        valid_moves = self.get_valid_moves(board)
        return valid_moves[0] if valid_moves else (0, 0)