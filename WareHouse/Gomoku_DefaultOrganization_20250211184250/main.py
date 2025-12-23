'''
主程序入口，创建游戏实例并启动 GUI。
'''
from gomoku_game import GomokuGame
from gomoku_gui import GomokuGUI
import tkinter as tk
def main():
    root = tk.Tk()
    root.title("Gomoku Game")
    game = GomokuGame()
    gui = GomokuGUI(root, game)
    root.mainloop()
if __name__ == "__main__":
    main()