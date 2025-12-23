'''
包含 Gomoku 游戏逻辑的类。
'''
class GomokuGame:
    def __init__(self):
        self.board = [[None for _ in range(15)] for _ in range(15)]
        self.current_player = "X"
        self.winner = None
    def make_move(self, x, y):
        if self.board[x][y] is None and self.winner is None:
            self.board[x][y] = self.current_player
            if self.check_winner():
                self.winner = self.current_player
                return  # 添加此行以防止继续进行游戏
            self.current_player = "O" if self.current_player == "X" else "X"
    def check_winner(self):
        # 检查行、列和对角线
        for x in range(15):
            for y in range(15):
                if self.board[x][y] is not None:
                    if self.check_direction(x, y, 1, 0) or \
                       self.check_direction(x, y, 0, 1) or \
                       self.check_direction(x, y, 1, 1) or \
                       self.check_direction(x, y, 1, -1):
                        return True
        return False
    def check_direction(self, x, y, dx, dy):
        count = 0
        for i in range(5):
            nx, ny = x + i * dx, y + i * dy
            if 0 <= nx < 15 and 0 <= ny < 15 and self.board[nx][ny] == self.board[x][y]:
                count += 1
            else:
                break
        # 检查是否有五个棋子
        if count == 5:
            return True
        return False
    def reset_game(self):
        self.board = [[None for _ in range(15)] for _ in range(15)]
        self.current_player = "X"
        self.winner = None