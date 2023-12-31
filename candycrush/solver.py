import utils
from copy import deepcopy
import numpy as np


class Solver:
    def __init__(self):
        self.board_size = 9
        # c(n,s_h,s_v,w)    blue, green, orange, purple, red, yellow
        self.match_list = [(1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12),
                           (13, 14, 15, 16), (17, 18, 19, 20), (21, 22, 23, 24)]

        self.special_candies = [2, 3, 4, 6, 7, 8, 10,
                                11, 12, 14, 15, 16, 18, 19, 20, 22, 23, 24, 25]
        self.simple_candies = [1, 5, 9, 13, 17, 21]
        self.striped_candies_h = [2, 6, 10, 16, 18, 22]
        self.striped_candies_v = [3, 7, 11, 14, 15, 19, 23]

        self.striped_candies = self.striped_candies_h[:]
        self.striped_candies.extend(self.striped_candies_v)

        self.wrapped_candies = [4, 8, 12, 20, 24]
        self.chocolate = 25
        self.game_board = None
        self.potential_start_coords = set()
        self.directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # horizontal

    def get_score(self, candy_type):
        if candy_type in self.simple_candies:
            return 20
        if candy_type in self.striped_candies:
            return 120
        if candy_type in self.wrapped_candies:
            return 300

        return 0

    def compute_score(self, board, candies_coords):
        score = 0
        for coords in candies_coords:
            candy_value = board[coords[0]][coords[1]]
            score += self.get_score(candy_value)

        if len(candies_coords) == 4:
            score *= 3
        if len(candies_coords) >= 5:
            score *= 10
        return score

    def compute_explosions_chocolate(self, board, color):
        to_explode = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.candy_matches(board[i][j], color):
                    to_explode.append((i, j))

        return to_explode

    def get_striped_explosion(self, board, coords):
        to_explode = []
        candy_type = board[coords[0]][coords[1]]
        if candy_type in self.striped_candies_h:
            for k in range(self.board_size):
                to_explode.append((coords[0], k))
        if candy_type in self.striped_candies_v:
            for k in range(self.board_size):
                to_explode.append((k, coords[1]))

        return to_explode

    def candy_matches(self, type1, type2):
        if type1 == type2:
            return True
        else:
            for match in self.match_list:
                if type1 in match and type2 in match:
                    return True

        return False

    def compute_explosions_lines(self, board, start):

        directions = [[(-1, 0), (1, 0)],  # vertical
                      [(0, -1), (0, 1)]]  # horizontal
        to_explode = []
        for dirs in directions:
            open_list = [start]
            for d in dirs:
                i = start[0] + d[0]
                j = start[1] + d[1]
                while 0 <= i < self.board_size and 0 <= j < self.board_size and board[i][j] != -1 \
                        and self.candy_matches(board[i][j], board[start[0]][start[1]]):
                    open_list.append((i, j))
                    i += d[0]
                    j += d[1]

            if len(open_list) >= 3:
                # if (start[0] == 2 and start[1] == 5):
                #    print("2,5-compute_explosions_lines")
                #    print("open_list:", open_list)
                for element in open_list:
                    if element not in to_explode:
                        if board[element[0]][element[1]] in self.striped_candies:
                            to_explode.extend(
                                self.get_striped_explosion(board, element))
                        else:
                            to_explode.append(element)

        return to_explode

    def compute_explosions(self, start, end, board):
        chocolate_multiplier = 1
        to_explode = []

        if board[start[0]][start[1]] in self.special_candies and board[end[0]][end[1]] in self.special_candies:
            score = 500000
            to_explode = [start, end]
        else:
            if board[start[0]][start[1]] == self.chocolate:
                to_explode = self.compute_explosions_chocolate(
                    board, board[end[0]][end[1]])
                chocolate_multiplier = 100
            else:

                to_explode = self.compute_explosions_lines(board, start)
                # if end[0] == 2 and end[1] == 4 and len(to_explode) > 0:
                #    print("2,4-compute_explosions_lines")
                #    print("start: ", start)
            to_explode.sort(key=(lambda x: x[0]))
            score = self.compute_score(
                board, to_explode) * chocolate_multiplier

        # if end[0] == 2 and end[1] == 4 and len(to_explode) > 0:
        #    print("2,4-compute_explosions")
        #    print("score:", score)
        #    print("to_explode:", to_explode)
        #    utils.print_board(board)

        # striped candy
        if len(to_explode) == 4 and board[start[0]][start[1]] != self.chocolate:
            board[start[0]][start[1]] += 1
            to_explode.remove(start)

        # Slide the other candies down after explosions take place
        for coord in to_explode:
            i, j = coord

            while i > 0:
                if board[i-1][j] != -1 and (i-1, j) not in self.potential_start_coords:
                    self.potential_start_coords.add((i, j))
                board[i][j], board[i-1][j] = board[i-1][j], board[i][j]
                i -= 1
            board[i][j] = -1

        return score, board

    def evaluate_board(self, start, end, board):
        total_score, new_board = self.compute_explosions(start, end, board)
        score = total_score
        multiplier = 1
        while score > 0:
            use_new = False
            if use_new:
                potential_start = deepcopy(self.potential_start_coords)
                self.potential_start_coords = set()
                score = 0
                for coord in potential_start:
                    score, new_board = self.compute_explosions(
                        (coord[0], coord[1]), end, new_board)
                    if score > 0:
                        total_score += score + multiplier * 60
                        multiplier += 2
            else:
                for i in range(0, self.board_size):
                    for j in range(0, self.board_size):
                        score, new_board = self.compute_explosions(
                            (i, j), end, new_board)
                        if score > 0:
                            total_score += score + multiplier * 60
                            multiplier += 2

        return total_score, new_board

    def check_direction(self, start, end):
        board = deepcopy(self.game_board)
        # swap
        board[start[0]][start[1]], board[end[0]][end[1]
                                                 ] = board[end[0]][end[1]], board[start[0]][start[1]]

        score_start, start_board = self.evaluate_board(start, end, board)
        score_end, end_board = self.evaluate_board(end, start, board)

        if score_start > score_end:
            return score_start, [start, end], start_board
        else:
            return score_end, [end, start], end_board

    def solve_board(self, board):
        self.game_board = board
        max_score = 0
        chosen_move = []
        possible_moves = []
        for i in reversed(range(1, 9)):

            for j in range(0, 8):
                r, c = i-1, j
                for d in self.directions:
                    nr, nc = r+d[0], c+d[1]
                    if nr >= 0 and nr <= self.board_size and nc >= 0 and nc <= self.board_size:
                        score, move, b = self.check_direction((r, c), (nr, nc))
                        # if r == 2 and c == 4:
                        # print("2,4")
                        # print("score:", score)
                        # print("move:", move)
                        if score > max_score:
                            possible_moves.append([score, move])
                            max_score = score
                            chosen_move = move
        # print("possible_moves:")
        # for move in possible_moves:
        #    print(move[0], move[1])
        #    print("\n")
        return max_score, chosen_move
