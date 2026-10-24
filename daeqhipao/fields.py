from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pygame

from daeqhipao.style import BACKGROUND_BOARD, CONDITION_SIZE, HIGHLIGHT_BOARD

if TYPE_CHECKING:
    from daeqhipao.barriers import Barrier
    from daeqhipao.board import Board
    from daeqhipao.pieces import Piece
    from daeqhipao.players import Player

CONDITION_IMAGE_DIR = os.path.join(os.path.dirname(__file__), "images", "conditions")
OCEAN_IMAGE = pygame.image.load(os.path.join(CONDITION_IMAGE_DIR, "ocean.svg"))
DROUGHT_IMAGE = pygame.image.load(os.path.join(CONDITION_IMAGE_DIR, "drought.svg"))
FLAME_IMAGE = pygame.image.load(os.path.join(CONDITION_IMAGE_DIR, "flame.svg"))


class Field:
    """
    Field types:
        field
        no field
        temple square
        temple area
        starting square
        barrier square

    Owners:
        Player (1, 2, 3, 4)
        None

    """

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self.owner: Player | None = None
        self.type = "field"

        self.piece: Piece | None = None
        self.barrier: Barrier | None = None
        self.occupied = False

        self.ocean = False
        self.drought = False
        self.flame = False
        self.flame_casters: set[Piece] = set()
        self.flame_counts: dict[Player, int] = {}
        self.ocean_casters: set[Piece] = set()
        self.drought_casters: set[Piece] = set()
        self.mind = False

        self.type = "Regular"
        # Set by Board.set_rectangles for every square on the board
        self.rectangle: pygame.Rect
        self.ocean_rectangle: pygame.Rect
        self.drought_rectangle: pygame.Rect
        self.flame_rectangle: pygame.Rect

    def __repr__(self) -> str:
        return f"{self.x}-{self.y}"

    def __eq__(self, field: object) -> bool:
        if isinstance(field, Field):
            return self.x == field.x and self.y == field.y
        else:
            return False

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def draw_conditions(self, screen: pygame.Surface) -> None:
        if self.ocean:
            ocean_image_scaled = pygame.transform.smoothscale(
                OCEAN_IMAGE, (CONDITION_SIZE, CONDITION_SIZE)
            )
            screen.blit(ocean_image_scaled, self.ocean_rectangle)
        if self.drought:
            drought_image_scaled = pygame.transform.smoothscale(
                DROUGHT_IMAGE, (CONDITION_SIZE, CONDITION_SIZE)
            )
            screen.blit(drought_image_scaled, self.drought_rectangle)
        if self.flame:
            flame_image_scaled = pygame.transform.smoothscale(
                FLAME_IMAGE, (CONDITION_SIZE, CONDITION_SIZE)
            )
            screen.blit(flame_image_scaled, self.flame_rectangle)

    def activate_ocean(self, piece: Piece) -> None:
        self.ocean = True
        self.ocean_casters.add(piece)
        piece.ocean_fields.add(self)

    def deactivate_ocean(self, piece: Piece) -> None:
        self.ocean_casters.remove(piece)
        if not self.ocean_casters:
            self.ocean = False

    def activate_drought(self, piece: Piece) -> None:
        self.drought = True
        self.drought_casters.add(piece)
        piece.drought_fields.add(self)

    def deactivate_drought(self, piece: Piece) -> None:
        self.drought_casters.remove(piece)
        if not self.drought_casters:
            self.drought = False

    def redraw(self, screen: pygame.Surface, colour: tuple[int, int, int]) -> None:
        pygame.draw.rect(screen, colour, self.rectangle)

    def place_barrier(self, barrier: Barrier) -> None:
        self.occupied = True
        self.barrier = barrier

    def remove_barrier(self, barrier: Barrier) -> None:
        self.occupied = False
        self.barrier = None

    def set_rectangle(self, square_width: int) -> None:
        x = (self.x + 1) * square_width
        y = (self.y + 1) * square_width
        self.rectangle = pygame.Rect(x, y, square_width, square_width)
        self.ocean_rectangle = pygame.Rect(
            x, y + 4 * CONDITION_SIZE, CONDITION_SIZE, CONDITION_SIZE
        )
        self.drought_rectangle = pygame.Rect(
            x + 4 * CONDITION_SIZE,
            y + 4 * CONDITION_SIZE,
            CONDITION_SIZE,
            CONDITION_SIZE,
        )
        self.flame_rectangle = pygame.Rect(x, y, CONDITION_SIZE, CONDITION_SIZE)

    def draw(
        self,
        screen: pygame.Surface,
        hovered: bool,
        highlight_colour: tuple[int, int, int] = HIGHLIGHT_BOARD,
    ) -> None:
        if hovered:
            pygame.draw.rect(screen, highlight_colour, self.rectangle)
        else:
            pygame.draw.rect(screen, BACKGROUND_BOARD, self.rectangle)

    def highlight_colour(
        self, screen: pygame.Surface, board: Board, colour: tuple[int, int, int]
    ) -> None:
        pygame.draw.rect(screen, colour, self.rectangle)
        self.draw_conditions(screen)
        if self.piece:
            board.draw_piece(self.piece)
        elif self.barrier:
            board.draw_barrier(self.barrier)
        board.draw_frame()

    def highlight(self, screen: pygame.Surface, player: Player, board: Board) -> None:
        pygame.draw.rect(screen, player.colour_rgb, self.rectangle)
        self.draw_conditions(screen)
        if self.piece:
            board.draw_piece(self.piece)
        elif self.barrier:
            board.draw_barrier(self.barrier)

    def highlight_strong(
        self, screen: pygame.Surface, player: Player, board: Board
    ) -> None:
        pygame.draw.rect(screen, player.colour_rgb_strong, self.rectangle)
        self.draw_conditions(screen)
        if self.piece:
            board.draw_piece(self.piece)
        elif self.barrier:
            board.draw_barrier(self.barrier)

    def set_ownership(self, player: Player) -> None:
        self.owner = player

    def in_temple_area(self) -> bool:
        return self.type == "temple area" or self.type == "starting square"

    def activate_flame(self, piece: Piece) -> None:
        self.flame = True
        self.flame_counts[piece.player] = 3

    def countdown_flame(self, player: Player) -> None:
        try:
            self.flame_counts[player] -= 1
            if self.flame_counts[player] == 0:
                self.deactivate_flame(player)
        except KeyError:
            pass

    def deactivate_flame(self, player: Player) -> None:
        del self.flame_counts[player]
        if not self.flame_counts:
            self.flame = False

    def check_occupied(self) -> None:
        if self.piece or self.barrier:
            self.occupied = True
        else:
            self.occupied = False

    def check_adjacent(self, field: Field, board: Board) -> bool:
        diff_x = abs(self.x - field.x)
        diff_y = abs(self.y - field.y)

        return not (diff_x > 1 or diff_y > 1 or (diff_x == 0 and diff_y == 0))

    def get_adjacent(self, board: Board, type: str = "all") -> list[Field]:

        adjacent = []
        if type == "horizontal":
            coord_combinations = [
                (self.x - 1, self.y),
                (self.x + 1, self.y),
                (self.x, self.y - 1),
                (self.x, self.y + 1),
            ]

        elif type == "diagonal":
            coord_combinations = [
                (self.x - 1, self.y - 1),
                (self.x + 1, self.y - 1),
                (self.x - 1, self.y + 1),
                (self.x + 1, self.y + 1),
            ]

        elif type == "all":
            coord_combinations = [
                (self.x - 1, self.y),
                (self.x + 1, self.y),
                (self.x, self.y - 1),
                (self.x, self.y + 1),
                (self.x - 1, self.y - 1),
                (self.x + 1, self.y - 1),
                (self.x - 1, self.y + 1),
                (self.x + 1, self.y + 1),
            ]

        for coord_combination in coord_combinations:
            x = coord_combination[0]
            y = coord_combination[1]

            field = board.get_field(x, y)

            if field:
                adjacent.append(field)

        print(adjacent)

        return adjacent

    def check_legal_movement(self, piece: Piece, using_power: bool = False) -> bool:
        return not (
            self.type == "no field"
            or self.occupied
            or (self.type == "temple square" and self.owner == piece.player)
            or not self.permitted_area_condition(piece)
            or (self.mind and using_power and not piece.immune("Mind"))
        )

    def check_flame(self, piece: Piece) -> bool:
        if self.flame:
            if piece.player in self.flame_counts and len(self.flame_counts) == 1:
                return False
            return not piece.immune("Flame")

        else:
            return False

    def permitted_area_condition(self, piece: Piece) -> bool:
        if self.ocean and piece.gender == "female" and not piece.immune("Ocean"):
            return False
        if self.drought and piece.gender == "male" and not piece.immune("Drought"):
            return False
        return not self.check_flame(piece)

    def get_legal_adjacent(self, board: Board, piece: Piece) -> list[Field]:

        adjacent = []

        fields = self.get_adjacent(board, type=piece.movement_type)

        for field in fields:
            if field.check_legal_movement(piece):
                adjacent.append(field)

        return adjacent
