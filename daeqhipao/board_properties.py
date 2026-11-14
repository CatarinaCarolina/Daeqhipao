"""Coordinates of the special squares of the board."""

from typing import ClassVar


class BoardProperties:
    """Coordinates of all starting squares, temple squares and temple areas."""

    starting_squares: ClassVar[list[tuple[int, int]]] = [
        (3, 9),
        (4, 9),
        (5, 9),
        (6, 9),
        (7, 9),
        (1, 3),
        (1, 4),
        (1, 5),
        (1, 6),
        (1, 7),
        (3, 1),
        (4, 1),
        (5, 1),
        (6, 1),
        (7, 1),
        (9, 3),
        (9, 4),
        (9, 5),
        (9, 6),
        (9, 7),
    ]

    temple_squares: ClassVar[list[tuple[int, int]]] = [(0, 5), (10, 5), (5, 0), (5, 10)]

    temple_area_squares: ClassVar[list[tuple[int, int]]] = [
        (3, 8),
        (4, 8),
        (5, 8),
        (6, 8),
        (7, 8),
        (2, 3),
        (2, 4),
        (2, 5),
        (2, 6),
        (2, 7),
        (3, 2),
        (4, 2),
        (5, 2),
        (6, 2),
        (7, 2),
        (8, 3),
        (8, 4),
        (8, 5),
        (8, 6),
        (8, 7),
    ]


BOARD_PROPERTIES = BoardProperties()
