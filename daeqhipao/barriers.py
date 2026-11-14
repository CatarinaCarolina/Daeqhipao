"""Barriers: up to three blocks that can be placed, moved and removed on the board."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from daeqhipao.style import (
    BACKGROUND_BOARD,
    BARRIER_PADDING,
    BARRIER_SIZE,
    SQUARE_WIDTH,
)

if TYPE_CHECKING:
    from daeqhipao.board import Board
    from daeqhipao.fields import Field


class Barrier:
    """A barrier that can occupy one square of the board.

    Args:
        barrier_id: Unique number of the barrier.
    """

    def __init__(self, barrier_id: int) -> None:
        self.id = barrier_id
        self.on_board = False
        self.location: Field | None = None
        self.rectangle: pygame.Rect | None = None

    def __repr__(self) -> str:
        return f"Barrier {self.id}"

    def __eq__(self, barrier: object) -> bool:
        if isinstance(barrier, Barrier):
            return self.id == barrier.id
        else:
            return False

    def __hash__(self) -> int:
        return self.id

    def set_rectangle(self) -> None:
        """Compute the barrier's screen rectangle from its location."""
        assert self.location is not None
        x = (1 + self.location.x) * SQUARE_WIDTH + BARRIER_PADDING
        y = (1 + self.location.y) * SQUARE_WIDTH + BARRIER_PADDING
        self.rectangle = pygame.Rect(x, y, BARRIER_SIZE, BARRIER_SIZE)

    def place_on_board(self, field: Field, board: Board, barriers: Barriers) -> None:
        """Place the barrier on field if it is empty and not a temple square, and draw it."""
        if not field.occupied and field.type != "temple square":
            self.on_board = True
            self.location = field
            field.place_barrier(self)
            barriers.set_used_and_unused_barriers()
            self.set_rectangle()
            board.draw_barrier(self)

    def remove_from_board(self, board: Board, barriers: Barriers) -> None:
        """Take the barrier off the board and redraw the square it was on."""
        assert self.location is not None
        original_x = self.location.x
        original_y = self.location.y

        original_field = board.get_field(original_x, original_y)
        assert original_field is not None

        self.on_board = False
        self.location.remove_barrier(self)
        self.location = None
        barriers.set_used_and_unused_barriers()
        self.rectangle = None

        board.redraw_field(original_field, BACKGROUND_BOARD)

    def move(self, field: Field, board: Board) -> None:
        """Move the barrier to field if it is empty, on the board and not a temple square."""
        if (
            not field.occupied
            and field.type != "temple square"
            and field.type != "no field"
        ):
            assert self.location is not None and self.rectangle is not None
            original_x = self.location.x
            original_y = self.location.y

            original_field = board.get_field(original_x, original_y)
            assert original_field is not None

            x_diff = field.x - self.location.x
            y_diff = field.y - self.location.y
            self.location.remove_barrier(self)
            self.location = field
            field.place_barrier(self)

            self.rectangle = self.rectangle.move(
                x_diff * SQUARE_WIDTH, y_diff * SQUARE_WIDTH
            )
            board.redraw_field(original_field, BACKGROUND_BOARD)
            board.draw_barrier(self)


class Barriers:
    """All barriers, split into those on the board and those still available.

    Args:
        barriers: Every barrier in the game.
    """

    def __init__(self, barriers: list[Barrier]) -> None:
        self.barriers = barriers
        self.used_barriers: list[Barrier] = []
        self.unused_barriers: list[Barrier] = []
        self.set_used_and_unused_barriers()

    def set_used_and_unused_barriers(self) -> None:
        """Recompute which barriers are on the board and which are unused."""
        self.used_barriers = []
        self.unused_barriers = []

        for barrier in self.barriers:
            if barrier.on_board:
                self.used_barriers.append(barrier)
            else:
                self.unused_barriers.append(barrier)


BARRIERS = Barriers([Barrier(1), Barrier(2), Barrier(3)])
