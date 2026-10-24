"""Colours and square coordinates for each player, keyed by player number (1-4)."""

from typing import ClassVar


class PlayerProperties:
    """Colours, starting squares, temple areas and temple squares per player."""

    player_to_colour_rgb: ClassVar[dict[int, tuple[int, int, int]]] = {
        1: (255, 204, 204),
        2: (255, 204, 102),
        3: (153, 204, 255),
        4: (204, 153, 255),
    }

    player_to_colour_rgb_strong: ClassVar[dict[int, tuple[int, int, int]]] = {
        1: (249, 133, 133),
        2: (255, 207, 108),
        3: (108, 128, 255),
        4: (187, 118, 255),
    }
    player_to_colour: ClassVar[dict[int, str]] = {
        1: "red",
        2: "orange",
        3: "blue",
        4: "purple",
    }
    player_to_starting_squares: ClassVar[dict[int, list[tuple[int, int]]]] = {
        1: [(3, 9), (4, 9), (5, 9), (6, 9), (7, 9)],
        2: [(1, 3), (1, 4), (1, 5), (1, 6), (1, 7)],
        3: [(3, 1), (4, 1), (5, 1), (6, 1), (7, 1)],
        4: [(9, 3), (9, 4), (9, 5), (9, 6), (9, 7)],
    }

    player_to_temple_area: ClassVar[dict[int, list[tuple[int, int]]]] = {
        1: [(3, 8), (4, 8), (5, 8), (6, 8), (7, 8)],
        2: [(2, 3), (2, 4), (2, 5), (2, 6), (2, 7)],
        3: [(3, 2), (4, 2), (5, 2), (6, 2), (7, 2)],
        4: [(8, 3), (8, 4), (8, 5), (8, 6), (8, 7)],
    }

    player_to_temple_square: ClassVar[dict[int, tuple[int, int]]] = {
        1: (5, 10),
        2: (0, 5),
        3: (5, 0),
        4: (10, 5),
    }


PLAYER_PROPERTIES = PlayerProperties()
