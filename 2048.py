import curses
from random import randrange, choice
from collections import defaultdict

actions = ["Up", "Left", "Down", "Right", "Restart", "Exit"]
letter_codes = [ord(ch) for ch in "WASDRQwasdrq"]
actions_dict = dict(zip(letter_codes, actions * 2))


# 获得用户有效输入并返回对应行为
def get_user_action(keybord):
    char = 'N'
    while char not in actions_dict:
        char = keybord.getch()
    return actions_dict[char]


# 矩阵转置
def transpose(field):
    return [list(row) for row in zip(*field)]


# 矩阵逆转
def invert(field):
    return [row[::-1] for row in field]


#     field = [[1,2,3,4] for j in range(4)]
#     print(field)
#     print(list(zip(*field)))
#     transpose = [list(row) for row in zip(*field)]
#     invert = [row[::-1] for row in field]
#     print(transpose)
#     print(invert)

# 创建棋盘
class GameField(object):
    def __init__(self, height=4, width=4, win=2048):
        self.height = height
        self.width = width
        self.win_value = win
        self.score = 0
        #self.highscore = 0
        self.reset()

    # 随机生成一个2或4
    def spawn(self):
        new_element = 4 if randrange(100) > 89 else 2
        (i, j) = choice([(i, j) for i in range(self.width) for j in range(self.height) if self.field[i][j] == 0])
        self.field[i][j] = new_element

    # field = [[0 for i in range(4)] for j in range(4)]
    # (i, j) = choice([(i, j) for i in range(4) for j in range(4) if field[i][j] == 0])
    # print((i, j))

    # 重置棋盘
    def reset(self):
        # if self.score > self.highscore:
        #     self.highscore = self.score
        self.score = 0
        self.field = [[0 for i in range(self.width)] for j in range(self.height)]
        self.spawn()
        self.spawn()

    # 棋盘走一步
    def move(self, direction):
        # 一行向左合并
        def move_row_left(row):
            def tighten(row):  # 把零散的非0单元挤到一块
                new_row = [i for i in row if i != 0]
                new_row += [0 for i in range(len(row) - len(new_row))]
                return new_row

            def merge(row):  # 对邻近元素进行合并
                pair = False
                new_row = []
                for i in range(len(row)):
                    if pair:
                        new_row.append(row[i] * 2)
                        if (self.score < 2 * row[i]):
                            self.score = 2 * row[i]
                        pair = False
                    else:
                        if i + 1 < len(row) and row[i] == row[i + 1]:
                            pair = True
                            new_row.append(0)
                        else:
                            new_row.append(row[i])
                assert len(new_row) == len(row)
                return new_row

            # 先挤到一块再合并再挤到一块
            return tighten(merge(tighten(row)))

        move = {}
        move['Left'] = lambda field: [move_row_left(row) for row in field]
        move['Right'] = lambda field: invert(move['Left'](invert(field)))
        move['Up'] = lambda field: transpose(move['Left'](transpose(field)))
        move['Down'] = lambda field: transpose(move['Right'](transpose(field)))

        if direction in move:
            if self.move_is_possible(direction):
                self.field = move[direction](self.field)
                self.spawn()
                return True
            else:
                return False

    # 判断输赢
    def is_win(self):
        return any(any(i >= self.win_value for i in row) for row in self.field)

    def is_gameover(self):
        return not any(self.move_is_possible(move) for move in actions)

    # 判断能否移动
    def move_is_possible(self, direction):
        def row_is_left_movable(row):
            def change(i):
                if row[i] == 0 and row[i + 1] != 0:
                    return True
                if row[i] != 0 and row[i] == row[i + 1]:
                    return True
                else:
                    return False

            return any(change(i) for i in range(len(row) - 1))

        check = {}
        check["Left"] = lambda field: any(row_is_left_movable(row) for row in field)
        check["Right"] = lambda field: check["Left"](invert(field))
        check["Up"] = lambda field: check["Left"](transpose(field))
        check["Down"] = lambda field: check["Right"](transpose(field))

        if direction in check:
            return check[direction](self.field)
        else:
            return False

    def draw(self, screen):
        help_string1 = '(W)Up (S)Down (A)Left (D)Right'
        help_string2 = '     (R)Restart (Q)Exit'
        gameover_string = '           GAME OVER'
        win_string = '          YOU WIN!'

        def cast(string):
            screen.addstr(string + '\n')

        def draw_hor_separator():
            line = '+------' * self.width + '+'
            separator = defaultdict(lambda: line)
            if not hasattr(draw_hor_separator, "counter"):
                draw_hor_separator.counter = 0
            cast(separator[draw_hor_separator.counter])
            draw_hor_separator.counter += 1

        def draw_row(row):
            cast(''.join('|{: ^5} '.format(num) if num > 0 else '|      ' for num in row) + '|')

        screen.clear()
        cast('SCORE: ' + str(self.score))
        # if 0 != self.highscore:
        #     cast('HIGHSCORE: ' + str(self.highscore))
        for row in self.field:
            draw_hor_separator()
            draw_row(row)
        draw_hor_separator()
        if self.is_win():
            cast(win_string)
        else:
            if self.is_gameover():
                cast(gameover_string)
            else:
                cast(help_string1)
        cast(help_string2)


def main(stdscr):
    def init():
        game_field.reset()
        return "Game"

    def not_game(state):
        # 画出 GameOver 或者 Win 的界面
        game_field.draw(stdscr)
        # 读取用户输入得到action，判断是重启游戏还是结束游戏
        action = get_user_action(stdscr)
        responses = defaultdict(lambda: state)  # 默认是当前状态，没有行为就会一直在当前界面循环
        responses['Restart'], responses['Exit'] = 'Init', 'Exit'  # 对应不同的行为转换到不同的状态
        return responses[action]

    def game():
        # 画出当前棋盘状态
        game_field.draw(stdscr)
        # 读取用户输入得到action
        action = get_user_action(stdscr)

        if action == 'Restart':
            return 'Init'
        if action == 'Exit':
            return 'Exit'
        if game_field.move(action):  # move successful
            if game_field.is_win():
                return 'Win'
            if game_field.is_gameover():
                return 'Gameover'
        return 'Game'

    state_actions = {
        'Init': init,
        'Win': lambda: not_game('Win'),
        'Gameover': lambda: not_game('Gameover'),
        'Game': game
    }

    curses.use_default_colors()

    # 设置终结状态最大数值为 2048
    game_field = GameField(win=2048)

    state = 'Init'

    # 状态机开始循环
    while state != 'Exit':
        state = state_actions[state]()


curses.wrapper(main)
