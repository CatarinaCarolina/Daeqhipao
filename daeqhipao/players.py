from daeqhipao.illegal_moves import PlayerError
from daeqhipao.player_properties import PLAYER_PROPERTIES


class Players:
    def __init__(self, players):
        self.players = {}
        for player in players:
            self.players[player.id] = player

    def get_player(self, player_id):
        return self.players[player_id]


class Player:
    def __init__(self, player_id):
        if not type(player_id) == int or player_id < 1 or player_id > 4:
            raise PlayerError("illegal number")
        self.id = player_id
        self.colour = PLAYER_PROPERTIES.player_to_colour[self.id]
        self.colour_rgb = PLAYER_PROPERTIES.player_to_colour_rgb[self.id]
        self.colour_rgb_strong = PLAYER_PROPERTIES.player_to_colour_rgb_strong[self.id]
        self.heirs = []
        self.god = None
        self.name = None

        self.idea = False
        self.illusion = False
        self.time = 0
        self.time_pieces = 0
        self.penalty_turns = 2

        self.temple = PLAYER_PROPERTIES.player_to_temple_square[self.id]
        self.starting_squares = PLAYER_PROPERTIES.player_to_starting_squares[self.id]
        self.temple_area = PLAYER_PROPERTIES.player_to_temple_area[self.id]

        self.free_positions = {1, 2, 3, 4, 5}

    def __eq__(self, player):
        if type(self) == type(player):
            return self.id == player.id
        else:
            return False

    def __hash__(self):
        return self.id

    def __repr__(self):
        if self.name:
            return self.name
        else:
            return f"Player {self.id}"

    def set_name(self, name):
        self.name = name

    def set_time_pieces(self, user):
        if user.legacy_duration:
            self.time_pieces = 3
        else:
            self.time_pieces = 2

    def set_time_count(self):
        self.time += 1

    def get_all_pieces(self):
        all_pieces = self.heirs + [self.god]
        return all_pieces

    def set_field_ownership(self, board):
        x, y = self.temple
        board.board[x][y].set_ownership(self)
        board.temple_squares[self] = board.board[x][y]

        for x, y in self.starting_squares:
            board.board[x][y].set_ownership(self)

        for x, y in self.temple_area:
            board.board[x][y].set_ownership(self)
