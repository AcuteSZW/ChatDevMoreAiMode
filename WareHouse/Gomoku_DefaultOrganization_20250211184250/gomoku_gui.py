'''
包含 Gomoku 游戏 GUI 逻辑的类。
'''
import tkinter as tk
from tkinter import messagebox
class GomokuGUI:
    def __init__(self, master, game):
        self.master = master
        self.game = game
        self.buttons = [[None for _ in range(15)] for _ in range(15)]
        self.draw_board()
    def draw_board(self):
        for x in range(15):
            for y in range(15):
                button = tk.Button(self.master, width=4, height=2,
                                   command=lambda x=x, y=y: self.on_click(x, y))
                button.grid(row=x, column=y)
                self.buttons[x][y] = button
    def on_click(self, x, y):
        self.game.make_move(x, y)
        self.update_buttons()
        if self.game.winner:
            messagebox.showinfo("Game Over", f"Player {self.game.winner} wins!")
            self.game.reset_game()
            self.update_buttons()
    def update_buttons(self):
        for x in range(15):
            for y in range(15):
                if self.game.board[x][y] is not None:
                    self.buttons[x][y].config(text=self.game.board[x][y])