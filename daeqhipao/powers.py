"""Powers of the pieces: what each power can target and what it does."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeGuard

from daeqhipao.illegal_moves import IllegalPower

if TYPE_CHECKING:
    import pygame

    from daeqhipao.barriers import Barrier, Barriers
    from daeqhipao.board import Board
    from daeqhipao.fields import Field
    from daeqhipao.pieces import Piece, Pieces
    from daeqhipao.players import Player
    from daeqhipao.turn_management import TurnManager

POTENCY = {
    "Perception",
    "Mind",
    "Blindness",
    "Oblivion",
    "Liberation",
    "Flame",
    "Communication",
    "Idea",
    "Illusion",
    "Director",
    "Wiper",
    "Connector",
    "Gifter",
    "Alchemist",
}

FREQUENCY = {
    "Life",
    "Perception",
    "Union",
    "Impression",
    "Familiarity",
    "Metamorphosis",
    "Death",
    "Blindness",
    "Liberation",
    "Earth",
    "Ocean",
    "Sky",
    "Sun",
    "Quake",
    "Wave",
    "Wind",
    "Shadow",
    "Metalmaker",
    "Bloodmaker",
    "Fog",
    "Void",
    "Drought",
    "End",
    "Night",
    "Gifter",
    "Connector",
    "Director",
    "Wiper",
    "Builder",
    "Mover",
    "Alchemist",
    "Consumer",
}


class Power:
    """Base class of the powers: tracks the targets being selected.

    Args:
        piece: The piece that has this power.
    """

    # Set by every concrete power class
    name: str
    confirm_message: str

    def __init__(self, piece: Piece) -> None:
        self.target_nr = 0
        self.target_types: list[str] = []
        self.piece = piece
        self.start_with_choice = False

        self.choice: str | None = None
        self.selected_piece_1: Piece | None = None
        self.selected_piece_2: Piece | None = None
        self.selected_field_1: Field | None = None
        self.selected_field_2: Field | None = None
        self.selected_barrier_1: Barrier | None = None
        self.selected_barrier_2: Barrier | None = None

        self.potency_or_frequency: str | None = None

        self.targets_1: list[Field] = []
        self.targets_2: list[Field] = []
        self.highlight_types: list[str] = []

        self.fixed_affected_area = False

    def check_power_usable(
        self, pieces: Pieces, barriers: Barriers, board: Board, players: list[Player]
    ) -> bool:
        """Return whether the piece is active and the power has a target."""
        if not self.piece.active:
            return False
        if self.fixed_affected_area:
            return True
        targets = self.get_target_fields(pieces, barriers, board, players)

        return bool(targets)

    def set_target_types(self, selection_types: list[str]) -> None:
        """Set the kinds of target ('piece', 'field' or 'barrier') to select, in order."""
        self.target_nr = len(selection_types)
        self.target_types = selection_types

    def highlight_all_targets(self, turn_manager: TurnManager) -> None:
        """Highlight all current targets, or switch the turn manager to hover highlighting."""
        highlight_type = self.get_highlight_type()
        if highlight_type == "highlight all targets":
            turn_manager.board.highlight_fields(
                self.piece.player, turn_manager.current_target_fields
            )
        elif highlight_type == "hover":
            turn_manager.hover = True

    def highlight_selected_fields(self, screen: pygame.Surface, board: Board) -> None:
        """Highlight the squares of the targets selected so far."""
        fields_to_highlight = []
        if self.selected_field_1:
            fields_to_highlight.append(self.selected_field_1)
        if self.selected_field_2:
            fields_to_highlight.append(self.selected_field_2)
        if self.selected_piece_1:
            fields_to_highlight.append(self.selected_piece_1.location)
        if self.selected_piece_2:
            fields_to_highlight.append(self.selected_piece_2.location)
        if self.selected_barrier_1:
            assert self.selected_barrier_1.location is not None
            fields_to_highlight.append(self.selected_barrier_1.location)
        if self.selected_barrier_2:
            assert self.selected_barrier_2.location is not None
            fields_to_highlight.append(self.selected_barrier_2.location)

        for field in fields_to_highlight:
            field.highlight_strong(screen, self.piece.player, board)

    def highlight_hover(
        self,
        screen: pygame.Surface,
        board: Board,
        target_fields: list[Field],
        mouse: tuple[int, int],
    ) -> None:
        """Highlight the target under the mouse; for Ocean and Drought also its neighbours."""
        if self.name == "Ocean" or self.name == "Drought":
            hovered_field = None
            for field in target_fields:
                if field.rectangle.collidepoint(mouse):
                    hovered_field = field
                    break

            if hovered_field:
                for field in board.fields:
                    if field.type != "temple square":
                        if field.rectangle.collidepoint(mouse):
                            hovered = True
                        else:
                            adjacent_fields = field.get_adjacent(board, type="all")

                            if hovered_field in adjacent_fields:
                                hovered = True
                            else:
                                hovered = False

                        field.draw(screen, hovered, self.piece.player.colour_rgb)
                        if field.piece == self.piece:
                            field.draw(screen, True)

                        board.draw_frame()
                        field.draw_conditions(screen)
                        if field.piece:
                            board.draw_piece(field.piece)
                        elif field.barrier:
                            board.draw_barrier(field.barrier)
            else:
                for field in board.fields:
                    field.draw(screen, False, self.piece.player.colour_rgb)
                    if field.piece == self.piece:
                        field.draw(screen, True)

                    board.draw_frame()
                    field.draw_conditions(screen)
                    if field.piece:
                        board.draw_piece(field.piece)
                    elif field.barrier:
                        board.draw_barrier(field.barrier)

        else:
            for field in target_fields:
                if field.rectangle.collidepoint(mouse):
                    hovered = True
                else:
                    hovered = False

                field.draw(screen, hovered, self.piece.player.colour_rgb)
                if field.piece == self.piece:
                    field.draw(screen, True)

                if field == self.selected_field_1:
                    field.draw(screen, True, self.piece.player.colour_rgb_strong)

                board.draw_frame()
                field.draw_conditions(screen)
                if field.piece:
                    board.draw_piece(field.piece)
                elif field.barrier:
                    board.draw_barrier(field.barrier)

    def reset_targets(self) -> None:
        """Clear the selected targets and choices."""
        self.selected_piece_1 = None
        self.selected_piece_2 = None
        self.selected_field_1 = None
        self.selected_field_2 = None
        self.selected_barrier_1 = None
        self.selected_barrier_2 = None
        self.target_nr = len(self.target_types)
        self.targets_1 = []
        self.targets_2 = []
        self.choice = None
        self.potency_or_frequency = None

    def select_piece_1(self, piece: Piece) -> None:
        """Select the first target piece."""
        self.selected_piece_1 = piece
        self.target_nr -= 1

    def select_piece_2(self, piece: Piece) -> None:
        """Select the second target piece."""
        self.selected_piece_2 = piece
        self.target_nr -= 1

    def select_field_1(self, field: Field) -> None:
        """Select the first target square."""
        self.selected_field_1 = field
        self.target_nr -= 1

    def select_field_2(self, field: Field) -> None:
        """Select the second target square."""
        self.selected_field_2 = field
        self.target_nr -= 1

    def select_barrier_1(self, barrier: Barrier) -> None:
        """Select the first target barrier."""
        self.selected_barrier_1 = barrier
        self.target_nr -= 1

    def select_barrier_2(self, barrier: Barrier) -> None:
        """Select the second target barrier."""
        self.selected_barrier_2 = barrier
        self.target_nr -= 1

    def get_choices(self, barriers: Barriers) -> tuple[str | None, str | None]:
        """Return the choices to offer before selecting targets, None for unused slots.

        Raises:
            IllegalPower: If Earth or Void can't be used with the current barriers.
        """
        choice_1 = None
        choice_2 = None

        if self.name == "Earth":
            if len(barriers.used_barriers) <= 1:
                choice_1 = "Place 1 barrier"
                choice_2 = "Place 2 barriers"
            elif len(barriers.used_barriers) == 2:
                choice_1 = "Place 1 barrier"
                choice_2 = None
            else:
                raise IllegalPower("Earth can't use its power!")

        elif self.name == "Void":
            if len(barriers.used_barriers) >= 2:
                choice_1 = "Remove 1 barrier"
                choice_2 = "Remove 2 barriers"
            elif len(barriers.used_barriers) == 1:
                choice_1 = "Remove 1 barrier"
                choice_2 = None
            else:
                raise IllegalPower("Void can't use its power!")

        if self.name == "Time" or self.name == "Legacy":
            choice_1 = "Increase potency"
            choice_2 = "Increase frequency"

        return choice_1, choice_2

    def get_target_type(self) -> str:
        """Return the kind of target to select next."""
        return self.target_types[-self.target_nr]

    def get_highlight_type(self) -> str:
        """Return how to highlight the next targets."""
        return self.highlight_types[-self.target_nr]

    # Each power overrides these with its own arguments, as called from
    # get_target_fields and activate_power
    def get_target_fields_1(self, *args: Any, **kwargs: Any) -> list[Field]:
        """Return the squares that can be chosen as the first target."""
        return []

    def get_target_fields_2(self, *args: Any, **kwargs: Any) -> list[Field]:
        """Return the squares that can be chosen as the second target."""
        return []

    def use_power(self, *args: Any, **kwargs: Any) -> None:
        """Apply the power to the selected targets."""

    def get_target_fields(
        self, pieces: Pieces, barriers: Barriers, board: Board, players: list[Player]
    ) -> list[Field]:
        """Return the squares that can be selected next, by power and remaining targets."""
        targets = []

        if self.name == "Union":
            if self.target_nr == 2:
                targets = self.get_target_fields_1(pieces)
            elif self.target_nr == 1:
                targets = self.get_target_fields_2(pieces)
        elif self.name == "Impression":
            if self.target_nr == 1:
                targets = self.get_target_fields_1(pieces)
        elif self.name == "Earth" or self.name == "Void":
            if self.target_nr == 2:
                targets = self.get_target_fields_1(board)
            elif self.target_nr == 1:
                targets = self.get_target_fields_2(board)
        elif self.name == "Ocean" or self.name == "Drought":
            targets = self.get_target_fields_1(board)
        elif self.name == "Life" or self.name == "Death":
            targets = self.get_target_fields_1(pieces)
        elif (
            self.name == "Sun"
            or self.name == "Wind"
            or self.name == "Sky"
            or self.name == "Shadow"
        ):
            targets = self.get_target_fields_1(board)
        elif self.name == "Idea" or self.name == "Illusion":
            targets = self.get_target_fields_1(players, pieces)
        elif self.name == "Quake":
            if self.target_nr == 2:
                targets = self.get_target_fields_1(board)
            elif self.target_nr == 1:
                targets = self.get_target_fields_2(board)
        elif self.name == "Wave" or self.name == "Fog":
            if self.target_nr == 2:
                targets = self.get_target_fields_1(board, pieces)
            elif self.target_nr == 1:
                targets = self.get_target_fields_2(board)
        elif self.name == "Bloodmaker":
            if self.target_nr == 2:
                targets = self.get_target_fields_1(board)
            elif self.target_nr == 1:
                targets = self.get_target_fields_2(board)
        elif self.name == "Metalmaker":
            targets = self.get_target_fields_1(board, barriers)
        elif self.name == "Night":
            targets = self.get_target_fields_1(board)
        elif self.name == "End":
            if self.target_nr == 2:
                targets = self.get_target_fields_1(pieces, board)
            elif self.target_nr == 1:
                targets = self.get_target_fields_2(board)
        elif self.name == "Time" or self.name == "Legacy":
            targets = self.get_target_fields_1(pieces)
        elif self.name == "Metamorphosis":
            if self.target_nr == 2:
                targets = self.get_target_fields_1(pieces)
            elif self.target_nr == 1:
                targets = self.get_target_fields_2(pieces)

        return targets

    def activate_power(self, pieces: Pieces, barriers: Barriers, board: Board) -> None:
        """Use the power, clear Idea and reset the targets; the piece sleeps unless it has frequency left."""
        if self.name == "Union":
            self.use_power()
        elif self.name == "Impression":
            self.use_power(board)
        elif self.name == "Earth" or self.name == "Void":
            self.use_power(barriers, board)
        elif self.name == "Communication":
            pass
        elif self.name == "Ocean" or self.name == "Drought":
            self.use_power(board)
        elif self.name == "Life" or self.name == "Death":
            self.use_power(pieces)
        elif (
            self.name == "Sun"
            or self.name == "Wind"
            or self.name == "Sky"
            or self.name == "Shadow"
        ):
            self.use_power(board)
        elif self.name == "Idea" or self.name == "Illusion":
            self.use_power()
        elif (
            self.name == "Quake"
            or self.name == "Wave"
            or self.name == "Fog"
            or self.name == "Bloodmaker"
        ):
            self.use_power(board)
        elif self.name == "Metalmaker":
            self.use_power(board, barriers)
        elif self.name == "Flame":
            self.use_power(board)
        elif self.name == "Night":
            self.use_power(board, barriers)
        elif self.name == "End" or self.name == "Mind":
            self.use_power(board)
        elif self.name == "Legacy" or self.name == "Time":
            self.use_power()
        elif self.name == "Metamorphosis":
            self.use_power(board, pieces)

        self.reset_targets()
        self.piece.deactivate_idea()
        if not self.piece.frequency:
            self.piece.sleep(pieces)


class UnionPower(Power):
    """Link the flip states of two pieces in the same state."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Union"
        self.set_target_types(["piece", "piece"])
        self.confirm_message = "Link the flip states of these pieces?"
        self.highlight_types = ["highlight all targets", "highlight all targets"]

    def use_power(self) -> None:
        """Link the two selected pieces.

        Raises:
            Immune: If a selected piece is immune to Union.
            IllegalPower: If one piece is active and the other passive.
        """
        assert self.selected_piece_1 is not None and self.selected_piece_2 is not None
        self.piece.select_piece(self.selected_piece_1, self.piece.name)
        self.piece.select_piece(self.selected_piece_2, self.piece.name)

        if self.selected_piece_1.active != self.selected_piece_2.active:
            raise IllegalPower("union")

        self.selected_piece_1.activate_union(self.selected_piece_2)
        self.selected_piece_2.activate_union(self.selected_piece_1)

    def get_target_fields_1(self, pieces: Pieces) -> list[Field]:
        """Return other non-immune pieces from the active and passive groups that have at least two."""
        true_active_targets = []
        true_passive_targets = []

        targets = []

        for piece in pieces.active_pieces:
            if piece != self.piece and not piece.immune("Union"):
                true_active_targets.append(piece.location)

        for piece in pieces.passive_pieces:
            if piece != self.piece and not piece.immune("Union"):
                true_passive_targets.append(piece.location)

        if len(true_active_targets) >= 2:
            targets += true_active_targets

        if len(true_passive_targets) >= 2:
            targets += true_passive_targets

        return targets

    def get_target_fields_2(self, pieces: Pieces) -> list[Field]:
        """Return other non-immune pieces in the same state as the first target."""
        targets = []

        assert self.selected_piece_1 is not None
        if self.selected_piece_1.active:
            for piece in pieces.active_pieces:
                if (
                    piece != self.selected_piece_1
                    and piece != self.piece
                    and not piece.immune("Union")
                ):
                    targets.append(piece.location)

        else:
            for piece in pieces.passive_pieces:
                if (
                    piece != self.selected_piece_1
                    and piece != self.piece
                    and not piece.immune("Union")
                ):
                    targets.append(piece.location)

        return targets


class ImpressionPower(Power):
    """Switch places with another piece outside a temple area."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Impression"
        self.set_target_types(["piece"])
        self.confirm_message = "Switch position with this piece?"
        self.highlight_types = ["highlight all targets"]

    def use_power(self, board: Board, *args: Any) -> None:
        """Swap this piece with the selected piece.

        Raises:
            Immune: If the selected piece is immune to Impression.
        """
        assert self.selected_piece_1 is not None
        self.piece.select_piece(self.selected_piece_1, self.piece.name)

        board.swap_objects(self.piece, self.selected_piece_1)

    def get_target_fields_1(self, pieces: Pieces) -> list[Field]:
        """Return other non-immune pieces outside temple areas."""
        targets = []

        for piece in pieces.pieces:
            if (
                piece != self.piece
                and not piece.immune("Impression")
                and not piece.location.in_temple_area()
            ):
                targets.append(piece.location)

        return targets


class CommunicationPower(Power):
    """Give a piece extra moves next turn. Not playable yet: it never has targets."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Communication"
        self.set_target_types(["piece"])
        self.confirm_message = "Give this piece the option to move two extra times next turn (three times in total)_instead of using its power?"
        self.highlight_types = ["highlight all targets"]

    def use_power(self) -> None:
        """Give the selected piece Communication."""
        assert self.selected_piece_1 is not None
        self.selected_piece_1.activate_communication(self.piece, self.piece.potency)


class FamiliarityPower(Power):
    """Borrow another piece's power. Not implemented yet."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Familiarity"
        self.set_target_types(["piece"])
        self.confirm_message = "Borrow this piece's power?"
        self.highlight_types = ["highlight all targets"]


class LifePower(Power):
    """Bring a passive piece back to life."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Life"
        self.set_target_types(["piece"])
        self.confirm_message = "Bring this piece back to life?"
        self.highlight_types = ["highlight all targets"]

    def get_target_fields_1(self, pieces: Pieces) -> list[Field]:
        """Return other passive, non-immune pieces."""
        targets = []

        for piece in pieces.pieces:
            if piece != self.piece and not piece.immune("Life") and not piece.active:
                targets.append(piece.location)

        return targets

    def use_power(self, pieces: Pieces) -> None:
        """Wake the selected piece."""
        assert self.selected_piece_1 is not None
        self.selected_piece_1.wake(pieces)


class PerceptionPower(Power):
    """Make a piece immune. Not playable yet: it never has targets."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Perception"
        self.set_target_types(["piece"])
        self.confirm_message = "Make this piece immune?"
        self.highlight_types = ["highlight all targets"]

    def use_power(self) -> None:
        """Give the selected piece Perception."""
        assert self.selected_piece_1 is not None
        self.selected_piece_1.activate_perception(self.piece)

    def get_target_fields_1(self, pieces: Pieces) -> list[Field]:
        """Return non-immune pieces."""
        target_fields = []

        for piece in pieces.pieces:
            if not piece.immune("Perception"):
                target_fields.append(piece.location)
        return target_fields


class MindPower(Power):
    """Protect the player's temple from powers."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Mind"
        self.set_target_types([])
        self.confirm_message = "Protect your temple from powers?"
        self.highlight_types = []
        self.fixed_affected_area = True

    def use_power(self, board: Board) -> None:
        """Protect the player's temple square with Mind."""
        board.temple_squares[self.piece.player].mind = True

    def get_target_fields_1(self, board: Board) -> list[Field]:
        """Return the player's temple square."""
        return [board.temple_squares[self.piece.player]]


class LegacyPower(Power):
    """Increase the potency or frequency of a spiritual piece's power."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Legacy"
        self.set_target_types(["piece"])
        self.confirm_message = "Allow this spiritual piece to increase the frequency or duration of its power next turn, or allow this Spiritual God piece to use two powers next turn?"
        self.highlight_types = ["highlight all targets"]
        self.start_with_choice = True

    def use_power(self) -> None:
        """Give the selected piece extra potency or frequency, as chosen."""
        if self.potency_or_frequency == "potency":
            assert self.selected_piece_1 is not None
            self.selected_piece_1.set_potency(self.piece)

        elif self.potency_or_frequency == "frequency":
            assert self.selected_piece_1 is not None
            self.selected_piece_1.set_frequency(self.piece)

    def get_target_fields_1(self, pieces: Pieces) -> list[Field]:
        """Return spiritual, non-immune pieces whose power can take the chosen increase."""
        target_fields = []
        for piece in pieces.spiritual_pieces:
            if not piece.immune("Legacy") and (
                (self.potency_or_frequency == "potency" and piece.name in POTENCY)
                or (
                    self.potency_or_frequency == "frequency" and piece.name in FREQUENCY
                )
                or (
                    not self.potency_or_frequency
                    and (piece.name in POTENCY or piece.name in FREQUENCY)
                )
            ):
                target_fields.append(piece.location)

        return target_fields


class TimePower(Power):
    """Increase the potency or frequency of a physical piece's power."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Time"
        self.set_target_types(["piece"])
        self.confirm_message = "Allow this physical piece to increase the frequency or duration of its power next turn, or allow this Physical God piece to use two powers next turn?"
        self.highlight_types = ["highlight all targets"]
        self.start_with_choice = True

    def use_power(self) -> None:
        """Give the selected piece extra potency or frequency, as chosen."""
        if self.potency_or_frequency == "potency":
            assert self.selected_piece_1 is not None
            self.selected_piece_1.set_potency(self.piece)

        elif self.potency_or_frequency == "frequency":
            assert self.selected_piece_1 is not None
            self.selected_piece_1.set_frequency(self.piece)

    def get_target_fields_1(self, pieces: Pieces) -> list[Field]:
        """Return physical, non-immune pieces whose power can take the chosen increase."""
        target_fields = []
        for piece in pieces.physical_pieces:
            if not piece.immune("Time") and (
                (self.potency_or_frequency == "potency" and piece.name in POTENCY)
                or (
                    self.potency_or_frequency == "frequency" and piece.name in FREQUENCY
                )
                or (
                    not self.potency_or_frequency
                    and (piece.name in POTENCY or piece.name in FREQUENCY)
                )
            ):
                target_fields.append(piece.location)

        return target_fields


class IllusionPower(Power):
    """Force an opponent's piece to move next turn."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Illusion"
        self.set_target_types(["piece"])
        self.confirm_message = "Force this piece to move next turn?"
        self.highlight_types = ["highlight all targets"]

    def use_power(self) -> None:
        """Put Illusion on the selected piece."""
        assert self.selected_piece_1 is not None
        self.selected_piece_1.activate_illusion()

    def get_target_fields_1(self, players: list[Player], pieces: Pieces) -> list[Field]:
        """Return active, non-immune pieces of opponents without Illusion.

        For an opponent with Idea, only their piece with Idea can be chosen.
        """
        idea_players = []
        legal_players = []

        for player in players:
            if player != self.piece.player and not player.illusion:
                if player.idea:
                    idea_players.append(player)
                else:
                    legal_players.append(player)

        target_fields = []

        for piece in pieces.pieces:
            if (
                piece.active
                and not piece.immune("Illusion")
                and (
                    piece.player in legal_players
                    or (piece.player in idea_players and piece.idea)
                )
            ):
                target_fields.append(piece.location)

        return target_fields


class IdeaPower(Power):
    """Force an opponent's piece to use its power next turn."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Idea"
        self.set_target_types(["piece"])
        self.confirm_message = "Force this piece to use its power next turn?"
        self.highlight_types = ["highlight all targets"]

    def use_power(self) -> None:
        """Put Idea on the selected piece."""
        assert self.selected_piece_1 is not None
        self.selected_piece_1.activate_idea()

    def get_target_fields_1(self, players: list[Player], pieces: Pieces) -> list[Field]:
        """Return active, non-immune pieces of opponents without Idea.

        For an opponent with Illusion, only their piece with Illusion can be chosen.
        """
        illusion_players = []
        legal_players = []

        for player in players:
            if player != self.piece.player and not player.idea:
                if player.illusion:
                    illusion_players.append(player)
                else:
                    legal_players.append(player)

        target_fields = []

        for piece in pieces.pieces:
            if (
                piece.active
                and not piece.immune("Idea")
                and (
                    piece.player in legal_players
                    or (piece.player in illusion_players and piece.illusion)
                )
            ):
                target_fields.append(piece.location)

        return target_fields


class MetamorphosisPower(Power):
    """Switch two heirs of the same god group, and their owners."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Metamorphosis"
        self.set_target_types(["piece", "piece"])
        self.confirm_message = "Switch these two pieces and their ownership?"
        self.highlight_types = ["highlight all targets", "highlight all targets"]

    def use_power(self, board: Board, pieces: Pieces) -> None:
        """Swap the squares of the two selected pieces and, if they differ, their players."""
        assert self.selected_piece_1 is not None and self.selected_piece_2 is not None
        original_player_1 = self.selected_piece_1.player
        original_player_2 = self.selected_piece_2.player

        if original_player_1 != original_player_2:
            self.selected_piece_1.player = original_player_2
            self.selected_piece_2.player = original_player_1
        board.swap_objects(self.selected_piece_1, self.selected_piece_2)

    def get_target_fields_1(self, pieces: Pieces) -> list[Field]:
        """Return active, non-immune heirs in god groups with at least two of them."""
        targets = []

        for god_group in pieces.god_groups.values():
            true_targets = []
            if len(god_group) > 1:
                for piece in god_group:
                    if piece.active and not piece.immune("Metamorphosis"):
                        true_targets.append(piece.location)

            if len(true_targets) > 1:
                targets += true_targets

        return targets

    def get_target_fields_2(self, pieces: Pieces) -> list[Field]:
        """Return the other active, non-immune heirs in the first target's god group."""
        targets = []
        assert self.selected_piece_1 is not None
        assert self.selected_piece_1.god_group is not None
        for piece in pieces.god_groups[self.selected_piece_1.god_group]:
            if (
                piece.active
                and piece != self.selected_piece_1
                and not piece.immune("Metamorphosis")
            ):
                targets.append(piece.location)

        return targets


class DeathPower(Power):
    """Make an active piece passive."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Death"
        self.set_target_types(["piece"])
        self.confirm_message = "Kill this piece?"
        self.highlight_types = ["highlight all targets"]

    def get_target_fields_1(self, pieces: Pieces) -> list[Field]:
        """Return other active, non-immune pieces."""
        targets = []

        for piece in pieces.pieces:
            if piece != self.piece and not piece.immune("Death") and piece.active:
                targets.append(piece.location)

        return targets

    def use_power(self, pieces: Pieces) -> None:
        """Put the selected piece to sleep."""
        assert self.selected_piece_1 is not None
        self.selected_piece_1.sleep(pieces)


class BlindnessPower(Power):
    """Stop a piece from moving for two turns. Not implemented yet."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Blindness"
        self.set_target_types(["piece"])
        self.confirm_message = "Prevent this piece from moving in the next two turns?"
        self.highlight_types = ["highlight all targets"]


class OblivionPower(Power):
    """Stop a piece from resetting at the next Zaopeng. Not implemented yet."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Oblivion"
        self.set_target_types(["piece"])
        self.confirm_message = "Prevent this piece resetting next Zaopeng?"
        self.highlight_types = ["highlight all targets"]


class LiberationPower(Power):
    """Stop a piece from using its power for two turns. Not implemented yet."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Liberation"
        self.set_target_types(["piece"])
        self.confirm_message = (
            "Prevent this piece from using its power in the next two turns?"
        )
        self.highlight_types = ["highlight all targets"]


class EarthPower(Power):
    """Place one or two barriers on empty squares."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Earth"
        self.set_target_types(["field", "field"])
        self.confirm_message = "Place barriers here?"
        self.start_with_choice = True
        self.highlight_types = ["hover", "hover"]

    def check_power_usable(
        self, pieces: Pieces, barriers: Barriers, board: Board, players: list[Player]
    ) -> bool:
        """Return False when no barriers are left, otherwise check for targets as usual."""
        if not barriers.unused_barriers:
            return False
        return super().check_power_usable(pieces, barriers, board, players)

    def get_target_fields_1(self, board: Board) -> list[Field]:
        """Return empty squares that are not temple squares."""
        target_fields = []

        for field in board.fields:
            if not field.occupied and field.type != "temple square":
                target_fields.append(field)

        return target_fields

    def get_target_fields_2(self, board: Board) -> list[Field]:
        """Return empty non-temple squares other than the first target."""
        target_fields = []

        for field in board.fields:
            if (
                field != self.selected_field_1
                and not field.occupied
                and field.type != "temple square"
            ):
                target_fields.append(field)

        return target_fields

    def use_power(self, barriers: Barriers, board: Board) -> None:
        """Place unused barriers on the selected squares."""
        if self.selected_field_1:
            barrier = barriers.unused_barriers[0]
            barrier.place_on_board(self.selected_field_1, board, barriers)
        if self.selected_field_2:
            barrier = barriers.unused_barriers[0]
            barrier.place_on_board(self.selected_field_2, board, barriers)


class OceanPower(Power):
    """Flood a square and its neighbours with ocean."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Ocean"
        self.set_target_types(["field"])
        self.confirm_message = "Place ocean here?"
        self.highlight_types = ["hover"]

    def get_target_fields_1(self, board: Board) -> list[Field]:
        """Return squares outside temples and temple areas."""
        target_fields = []

        for field in board.fields:
            if field.type != "temple square" and not field.in_temple_area():
                target_fields.append(field)

        return target_fields

    def use_power(self, board: Board) -> None:
        """Put ocean on the selected square and its neighbours, except temple squares."""
        assert self.selected_field_1 is not None
        adjacent_squares = self.selected_field_1.get_adjacent(board)
        self.selected_field_1.activate_ocean(self.piece)
        for adjacent_square in adjacent_squares:
            if adjacent_square.type != "temple square":
                adjacent_square.activate_ocean(self.piece)


class SkyPower(Power):
    """Jump over an adjacent piece."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Sky"
        self.set_target_types(["field"])
        self.confirm_message = "Jump here?"
        self.highlight_types = ["highlight all targets"]

    def use_power(self, board: Board) -> None:
        """Move this piece to the selected square."""
        assert self.selected_field_1 is not None
        self.piece.move(self.selected_field_1, board)

    def get_target_fields_1(self, board: Board) -> list[Field]:
        """Return legal squares reached by jumping over an adjacent non-immune piece."""
        adjacent_fields = self.piece.location.get_adjacent(board, type="all")
        adjacent_fields_with_pieces = []
        for adjacent_field in adjacent_fields:
            if adjacent_field.piece and not adjacent_field.piece.immune("Sky"):
                adjacent_fields_with_pieces.append(adjacent_field)

        jump_locations = []

        for field in adjacent_fields_with_pieces:
            diff_x = field.x - self.piece.location.x
            diff_y = field.y - self.piece.location.y
            jump_location = board.get_field(field.x + diff_x, field.y + diff_y)
            if jump_location and jump_location.check_legal_movement(
                self.piece, using_power=True
            ):
                jump_locations.append(jump_location)

        return jump_locations


class SunPower(Power):
    """Move two squares horizontally or vertically."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Sun"
        self.set_target_types(["field"])
        self.confirm_message = "Move here?"
        self.highlight_types = ["highlight all targets"]

    def use_power(self, board: Board) -> None:
        """Move this piece to the selected square."""
        assert self.selected_field_1 is not None
        self.piece.move(self.selected_field_1, board)

    def get_target_fields_1(self, board: Board) -> list[Field]:
        """Return legal squares two steps away in a straight line, past a legal square."""
        target_1 = board.get_field(self.piece.location.x + 2, self.piece.location.y)
        target_2 = board.get_field(self.piece.location.x - 2, self.piece.location.y)
        target_3 = board.get_field(self.piece.location.x, self.piece.location.y + 2)
        target_4 = board.get_field(self.piece.location.x, self.piece.location.y - 2)

        pass_1 = board.get_field(self.piece.location.x + 1, self.piece.location.y)
        pass_2 = board.get_field(self.piece.location.x - 1, self.piece.location.y)
        pass_3 = board.get_field(self.piece.location.x, self.piece.location.y + 1)
        pass_4 = board.get_field(self.piece.location.x, self.piece.location.y - 1)

        target_fields = []
        if self.check_target(target_1, pass_1):
            target_fields.append(target_1)
        if self.check_target(target_2, pass_2):
            target_fields.append(target_2)
        if self.check_target(target_3, pass_3):
            target_fields.append(target_3)
        if self.check_target(target_4, pass_4):
            target_fields.append(target_4)

        return target_fields

    def check_target(
        self, target_field: Field | None, pass_through_field: Field | None
    ) -> TypeGuard[Field]:
        """Return whether target_field and the square passed through are legal for this piece."""
        if not target_field:
            return False
        if target_field.type == "no field":
            return False
        if not pass_through_field:
            return False
        if pass_through_field.type == "no field":
            return False
        return target_field.check_legal_movement(
            self.piece, using_power=True
        ) and pass_through_field.check_legal_movement(self.piece, using_power=True)


class QuakePower(Power):
    """Move a barrier to an empty square."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Quake"
        self.set_target_types(["barrier", "field"])
        self.confirm_message = "Move barrier here?"
        self.highlight_types = ["highlight all targets", "hover"]

    def use_power(self, board: Board) -> None:
        """Move the selected barrier to the selected square."""
        assert self.selected_barrier_1 is not None and self.selected_field_1 is not None
        self.selected_barrier_1.move(self.selected_field_1, board)

    def get_target_fields_1(self, board: Board) -> list[Field]:
        """Return squares with a barrier."""
        target_fields = []

        for field in board.fields:
            if field.barrier:
                target_fields.append(field)

        return target_fields

    def get_target_fields_2(self, board: Board) -> list[Field]:
        """Return empty squares that are not temple squares."""
        target_fields = []

        for field in board.fields:
            if not field.occupied and field.type != "temple square":
                target_fields.append(field)

        return target_fields


class WavePower(Power):
    """Move another piece to an adjacent square."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Wave"
        self.set_target_types(["piece", "field"])
        self.confirm_message = "Move piece here?"
        self.highlight_types = ["highlight all targets", "highlight all targets"]

    def use_power(self, board: Board) -> None:
        """Move the selected piece to the selected square."""
        assert self.selected_piece_1 is not None and self.selected_field_1 is not None
        self.selected_piece_1.move(self.selected_field_1, board)

    def get_target_fields_1(self, board: Board, pieces: Pieces) -> list[Field]:
        """Return non-immune pieces with a legal adjacent square to move to."""
        target_fields = []
        for piece in pieces.pieces:
            if not piece.immune("Wave"):
                adjacent_fields = piece.location.get_adjacent(board, type="all")
                possible_movement = False
                for adjacent_field in adjacent_fields:
                    if adjacent_field.check_legal_movement(piece, using_power=True):
                        possible_movement = True
                        break
                if possible_movement:
                    target_fields.append(piece.location)

        return target_fields

    def get_target_fields_2(self, board: Board) -> list[Field]:
        """Return legal squares next to the selected piece."""
        target_fields = []

        assert self.selected_piece_1 is not None
        adjacent_fields = self.selected_piece_1.location.get_adjacent(board, type="all")

        for adjacent_field in adjacent_fields:
            if adjacent_field.check_legal_movement(
                self.selected_piece_1, using_power=True
            ):
                target_fields.append(adjacent_field)

        return target_fields


class WindPower(Power):
    """Move two squares diagonally."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Wind"
        self.set_target_types(["field"])
        self.confirm_message = "Move here?"
        self.highlight_types = ["highlight all targets"]

    def use_power(self, board: Board) -> None:
        """Move this piece to the selected square."""
        assert self.selected_field_1 is not None
        self.piece.move(self.selected_field_1, board)

    def get_target_fields_1(self, board: Board) -> list[Field]:
        """Return legal squares two steps away diagonally, past a legal square."""
        target_1 = board.get_field(self.piece.location.x + 2, self.piece.location.y + 2)
        target_2 = board.get_field(self.piece.location.x - 2, self.piece.location.y + 2)
        target_3 = board.get_field(self.piece.location.x + 2, self.piece.location.y - 2)
        target_4 = board.get_field(self.piece.location.x - 2, self.piece.location.y - 2)

        pass_1 = board.get_field(self.piece.location.x + 1, self.piece.location.y + 1)
        pass_2 = board.get_field(self.piece.location.x - 1, self.piece.location.y + 1)
        pass_3 = board.get_field(self.piece.location.x + 1, self.piece.location.y - 1)
        pass_4 = board.get_field(self.piece.location.x - 1, self.piece.location.y - 1)

        target_fields = []
        if self.check_target(target_1, pass_1):
            target_fields.append(target_1)
        if self.check_target(target_2, pass_2):
            target_fields.append(target_2)
        if self.check_target(target_3, pass_3):
            target_fields.append(target_3)
        if self.check_target(target_4, pass_4):
            target_fields.append(target_4)

        return target_fields

    def check_target(
        self, target_field: Field | None, pass_through_field: Field | None
    ) -> TypeGuard[Field]:
        """Return whether target_field and the square passed through are legal for this piece."""
        if not target_field:
            return False
        if target_field.type == "no field":
            return False
        if not pass_through_field:
            return False
        if pass_through_field.type == "no field":
            return False
        return target_field.check_legal_movement(
            self.piece, using_power=True
        ) and pass_through_field.check_legal_movement(self.piece, using_power=True)


class ShadowPower(Power):
    """Jump over an adjacent barrier."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Shadow"
        self.set_target_types(["field"])
        self.confirm_message = "Jump here?"
        self.highlight_types = ["highlight all targets"]

    def use_power(self, board: Board) -> None:
        """Move this piece to the selected square."""
        assert self.selected_field_1 is not None
        self.piece.move(self.selected_field_1, board)

    def get_target_fields_1(self, board: Board) -> list[Field]:
        """Return legal squares reached by jumping over an adjacent barrier."""
        adjacent_fields = self.piece.location.get_adjacent(board, type="all")
        adjacent_fields_with_barriers = []
        for adjacent_field in adjacent_fields:
            if adjacent_field.barrier:
                adjacent_fields_with_barriers.append(adjacent_field)

        jump_locations = []

        for field in adjacent_fields_with_barriers:
            diff_x = field.x - self.piece.location.x
            diff_y = field.y - self.piece.location.y
            jump_location = board.get_field(field.x + diff_x, field.y + diff_y)
            if jump_location and jump_location.check_legal_movement(
                self.piece, using_power=True
            ):
                jump_locations.append(jump_location)

        return jump_locations


class MetalmakerPower(Power):
    """Move to an adjacent square and leave a barrier behind."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Metalmaker"
        self.set_target_types(["field"])
        self.confirm_message = "Move and leave barrier?"
        self.highlight_types = ["highlight all targets"]

    def use_power(self, board: Board, barriers: Barriers) -> None:
        """Move this piece to the selected square and place a barrier where it was."""
        field_of_origin = board.get_field(self.piece.location.x, self.piece.location.y)
        assert field_of_origin is not None and self.selected_field_1 is not None
        self.piece.move(self.selected_field_1, board)
        barrier = barriers.unused_barriers[0]
        barrier.place_on_board(field_of_origin, board, barriers)

    def get_target_fields_1(self, board: Board, barriers: Barriers) -> list[Field]:
        """Return legal adjacent squares, if a barrier is available."""
        targets = []

        if barriers.unused_barriers:
            adjacent_fields = self.piece.location.get_adjacent(board, type="all")
            for field in adjacent_fields:
                if field.check_legal_movement(self.piece, using_power=True):
                    targets.append(field)

        return targets


class BloodmakerPower(Power):
    """Switch a barrier with an adjacent piece."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Bloodmaker"
        self.set_target_types(["barrier", "piece"])
        self.confirm_message = "Switch this barrier with this piece?"
        self.highlight_types = ["highlight all targets", "highlight all targets"]

    def use_power(self, board: Board) -> None:
        """Swap the selected barrier and piece."""
        assert self.selected_barrier_1 is not None and self.selected_piece_1 is not None
        board.swap_objects(self.selected_barrier_1, self.selected_piece_1)

    def get_target_fields_1(self, board: Board) -> list[Field]:
        """Return squares with a barrier next to a piece it can swap with."""
        targets = []

        for field in board.fields:
            if field.barrier:
                assert field.barrier.location is not None
                adjacent_fields = field.barrier.location.get_adjacent(board, type="all")
                potential_target = False
                for adjacent_field in adjacent_fields:
                    if adjacent_field.piece and self.check_swap_legal(
                        field.barrier, adjacent_field.piece
                    ):
                        potential_target = True
                        break
                if potential_target:
                    targets.append(field.barrier.location)

        return targets

    def get_target_fields_2(self, board: Board) -> list[Field]:
        """Return squares next to the selected barrier with a piece it can swap with."""
        targets = []
        assert self.selected_barrier_1 is not None
        assert self.selected_barrier_1.location is not None
        adjacent_fields = self.selected_barrier_1.location.get_adjacent(
            board, type="all"
        )
        for adjacent_field in adjacent_fields:
            if adjacent_field.piece and self.check_swap_legal(
                self.selected_barrier_1, adjacent_field.piece
            ):
                targets.append(adjacent_field)

        return targets

    def check_swap_legal(self, barrier: Barrier, piece: Piece) -> bool:
        """Return whether piece is not immune and may stand on barrier's square."""
        if piece.immune("Bloodmaker"):
            return False
        assert barrier.location is not None
        return barrier.location.permitted_area_condition(piece)


class FogPower(Power):
    """Switch two adjacent pieces."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Fog"
        self.set_target_types(["piece", "piece"])
        self.confirm_message = "Switch these pieces?"
        self.highlight_types = ["highlight all targets", "highlight all targets"]

    def use_power(self, board: Board) -> None:
        """Swap the two selected pieces."""
        assert self.selected_piece_1 is not None and self.selected_piece_2 is not None
        board.swap_objects(self.selected_piece_1, self.selected_piece_2)

    def get_target_fields_1(self, board: Board, pieces: Pieces) -> list[Field]:
        """Return non-immune pieces next to a piece they can swap with."""
        targets = []

        for piece in pieces.pieces:
            if not piece.immune("Fog"):
                adjacent_fields = piece.location.get_adjacent(board, type="all")
                potential_target = False
                for adjacent_field in adjacent_fields:
                    if adjacent_field.piece and self.check_swap_legal(
                        piece, adjacent_field.piece
                    ):
                        potential_target = True
                        break
                if potential_target:
                    targets.append(piece.location)

        return targets

    def get_target_fields_2(self, board: Board) -> list[Field]:
        """Return squares next to the first piece with a piece it can swap with."""
        targets = []
        assert self.selected_piece_1 is not None
        adjacent_fields = self.selected_piece_1.location.get_adjacent(board, type="all")
        for adjacent_field in adjacent_fields:
            if adjacent_field.piece and self.check_swap_legal(
                self.selected_piece_1, adjacent_field.piece
            ):
                targets.append(adjacent_field)

        return targets

    def check_swap_legal(self, piece_1: Piece, piece_2: Piece) -> bool:
        """Return whether neither piece is immune and each may stand on the other's square."""
        if piece_1.immune("Fog"):
            return False
        if piece_2.immune("Fog"):
            return False
        if not piece_1.location.permitted_area_condition(piece_2):
            return False
        return piece_2.location.permitted_area_condition(piece_1)


class FlamePower(Power):
    """Set fire to the squares around the piece."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Flame"
        self.set_target_types([])
        self.confirm_message = "Activate flame?"
        self.highlight_types = []
        self.fixed_affected_area = True

    def use_power(self, board: Board) -> None:
        """Set a flame on every affected square."""
        for field in self.get_affected_fields(board):
            field.activate_flame(self.piece)

    def get_target_fields_1(self, board: Board) -> list[Field]:
        """Return the affected squares."""
        target_fields = self.get_affected_fields(board)
        return target_fields

    def get_affected_fields(self, board: Board) -> list[Field]:
        """Return the squares the flame reaches.

        These are the piece's own square, its neighbours except owned temple
        squares, and the squares two steps away in a straight line except temple
        squares.
        """
        affected_fields = [self.piece.location]
        adjacent_fields = self.piece.location.get_adjacent(board, type="all")
        for field in adjacent_fields:
            if not (field.type == "temple square" and field.owner):
                affected_fields.append(field)

        field_1 = board.get_field(self.piece.location.x, self.piece.location.y + 2)
        if field_1 and field_1.type != "temple square":
            affected_fields.append(field_1)

        field_2 = board.get_field(self.piece.location.x, self.piece.location.y - 2)
        if field_2 and field_2.type != "temple square":
            affected_fields.append(field_2)

        field_3 = board.get_field(self.piece.location.x + 2, self.piece.location.y)
        if field_3 and field_3.type != "temple square":
            affected_fields.append(field_3)

        field_4 = board.get_field(self.piece.location.x - 2, self.piece.location.y)
        if field_4 and field_4.type != "temple square":
            affected_fields.append(field_4)

        return affected_fields


class VoidPower(Power):
    """Remove one or two barriers."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Void"
        self.set_target_types(["barrier", "barrier"])
        self.confirm_message = "Remove these barriers?"
        self.highlight_types = ["highlight all targets", "highlight all targets"]
        self.start_with_choice = True

    def get_target_fields_1(self, board: Board) -> list[Field]:
        """Return squares with a barrier."""
        target_fields = []

        for field in board.fields:
            if field.barrier:
                target_fields.append(field)

        return target_fields

    def get_target_fields_2(self, board: Board) -> list[Field]:
        """Return squares with a barrier other than the first target."""
        target_fields = []

        for field in board.fields:
            if field.barrier and field.barrier != self.selected_barrier_1:
                target_fields.append(field)

        return target_fields

    def use_power(self, barriers: Barriers, board: Board) -> None:
        """Remove the selected barriers."""
        if self.selected_barrier_1:
            self.selected_barrier_1.remove_from_board(board, barriers)
        if self.selected_barrier_2:
            self.selected_barrier_2.remove_from_board(board, barriers)


class DroughtPower(Power):
    """Put drought on a square and its neighbours."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Drought"
        self.set_target_types(["field"])
        self.confirm_message = "Place drought here?"
        self.highlight_types = ["hover"]

    def get_target_fields_1(self, board: Board) -> list[Field]:
        """Return squares outside temples and temple areas."""
        target_fields = []

        for field in board.fields:
            if field.type != "temple square" and not field.in_temple_area():
                target_fields.append(field)

        return target_fields

    def use_power(self, board: Board) -> None:
        """Put drought on the selected square and its neighbours, except temple squares."""
        assert self.selected_field_1 is not None
        adjacent_squares = self.selected_field_1.get_adjacent(board)
        self.selected_field_1.activate_drought(self.piece)
        for adjacent_square in adjacent_squares:
            if adjacent_square.type != "temple square":
                adjacent_square.activate_drought(self.piece)


class EndPower(Power):
    """Send a piece back to its temple area."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "End"
        self.set_target_types(["piece", "field"])
        self.confirm_message = "Move this piece back to their temple area?"
        self.highlight_types = ["highlight all targets", "highlight all targets"]

    def use_power(self, board: Board) -> None:
        """Move the selected piece to the selected square."""
        assert self.selected_piece_1 is not None and self.selected_field_1 is not None
        self.selected_piece_1.move(self.selected_field_1, board)

    def get_target_fields_1(self, pieces: Pieces, board: Board) -> list[Field]:
        """Return non-immune pieces outside temple areas with a free square in their temple area."""
        target_fields = []
        for piece in pieces.pieces:
            if not piece.immune("End") and not piece.location.in_temple_area():
                temple_area = board.get_temple_area(piece.player)
                for field in temple_area:
                    if field.check_legal_movement(piece, using_power=True):
                        target_fields.append(piece.location)
                        break

        return target_fields

    def get_target_fields_2(self, board: Board) -> list[Field]:
        """Return the legal squares in the selected piece's temple area."""
        target_fields = []
        assert self.selected_piece_1 is not None
        temple_area = board.get_temple_area(self.selected_piece_1.player)
        for field in temple_area:
            if field.check_legal_movement(self.selected_piece_1, using_power=True):
                target_fields.append(field)

        return target_fields


class NightPower(Power):
    """Consume an adjacent barrier and take its place."""

    def __init__(self, piece: Piece) -> None:
        super().__init__(piece)
        self.name = "Night"
        self.set_target_types(["barrier"])
        self.confirm_message = "Consume this barrier?"
        self.highlight_types = ["highlight all targets"]

    def use_power(self, board: Board, barriers: Barriers) -> None:
        """Remove the selected barrier and move this piece to its square."""
        assert self.selected_barrier_1 is not None
        assert self.selected_barrier_1.location is not None
        target_location = board.get_field(
            self.selected_barrier_1.location.x, self.selected_barrier_1.location.y
        )
        assert target_location is not None
        self.selected_barrier_1.remove_from_board(board, barriers)
        self.piece.move(target_location, board)

    def get_target_fields_1(self, board: Board) -> list[Field]:
        """Return adjacent squares with a barrier that this piece may stand on."""
        target_fields = []

        adjacent_fields = self.piece.location.get_adjacent(board, type="all")
        for adjacent_field in adjacent_fields:
            if adjacent_field.barrier and adjacent_field.permitted_area_condition(
                self.piece
            ):
                target_fields.append(adjacent_field)

        return target_fields
