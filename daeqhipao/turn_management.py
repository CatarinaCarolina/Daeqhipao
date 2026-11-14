"""Turn flow: what each click does in each state of a turn."""

from __future__ import annotations

from typing import TYPE_CHECKING

from daeqhipao.buttons import (
    PLACE_BARRIER_BUTTON,
    REMOVE_BARRIER_BUTTON,
    Button,
    ChoiceButton,
    PowerButton,
    get_mouse_button,
    hide_move_button,
    hide_piece_buttons,
    make_buttons,
    show_confirm_button,
    show_end_turn_button,
    show_move_button,
    show_piece_buttons,
    show_place_barrier_button,
    show_power_button,
    show_power_choice_button,
    show_remove_barrier_button,
    show_reset_selection_button,
)
from daeqhipao.fields import Field
from daeqhipao.style import BACKGROUND_BOARD, HEIGHT, HIGHLIGHT_BOARD

if TYPE_CHECKING:
    import pygame

    from daeqhipao.barriers import Barrier, Barriers
    from daeqhipao.board import Board
    from daeqhipao.pieces import Piece, Pieces
    from daeqhipao.players import Player
    from daeqhipao.powers import Power


class TurnManager:
    """Runs the turns, reacting to clicks according to the current state.

    Args:
        players: The players, in turn order.
        board: The board.
        screen: The pygame surface to draw on.
        pieces: All pieces.
        barriers: All barriers.

    States:
        select piece
        select move or use power
        select move
        move communication
        select use power or end turn
        make choice
        select power
        select power target
        confirm or reset
        place barrier
        remove barrier
    """

    def __init__(
        self,
        players: list[Player],
        board: Board,
        screen: pygame.Surface,
        pieces: Pieces,
        barriers: Barriers,
    ) -> None:
        self.turn = 0
        self.players = players

        self.board = board
        self.screen = screen
        self.pieces = pieces
        self.barriers = barriers

        self.used_barriers: list[Barrier] = []
        self.unused_barriers: list[Barrier] = []

        self.current_player = players[0]
        self.current_piece: Piece | None = None

        self.has_moved = False
        self.has_used_power = False

        self.active_buttons = make_buttons()
        self.current_target_fields: list[Field] = []

        self.set_selectable_fields()
        self.movement_options: list[Field] = []

        self.power: Power | None = None

        self.states = ["select piece"]
        self.state_nr = 0
        self.hover = False

    def reset_states(self) -> None:
        """Start a new state history at 'select piece'."""
        self.states = ["select piece"]
        self.state_nr = 0

    def get_current_state(self) -> str:
        """Return the current state."""
        state = self.states[-1]
        return state

    def get_state(self, state_nr: int) -> str:
        """Return the state at position state_nr in the history."""
        state = self.states[state_nr]
        return state

    def select_target(self, target: Field) -> None:
        """Select target as the next target of the current power."""
        hide_piece_buttons(self.screen, self.active_buttons)
        show_reset_selection_button(self.screen, self.active_buttons)
        assert self.power is not None and self.current_piece is not None
        target_type = self.power.get_target_type()

        self.board.highlight_field_strong(self.current_piece.player, target)

        if target_type == "field":
            if self.power.selected_field_1:
                self.power.select_field_2(target)
            else:
                self.power.select_field_1(target)

        elif target_type == "piece":
            assert target.piece is not None
            if self.power.selected_piece_1:
                self.power.select_piece_2(target.piece)
            else:
                self.power.select_piece_1(target.piece)

        elif target_type == "barrier":
            assert target.barrier is not None
            if self.power.selected_barrier_1:
                self.power.select_barrier_2(target.barrier)
            else:
                self.power.select_barrier_1(target.barrier)

    def penalty_zaopeng(self) -> None:
        """Force a Zaopeng for the current player and offer a barrier action."""
        hide_piece_buttons(self.screen, self.active_buttons)
        self.pieces.zaopeng(self.current_player)
        for piece in self.pieces.pieces:
            if piece.player == self.current_player:
                self.board.draw_piece(piece)
        if self.barriers.unused_barriers:
            show_place_barrier_button(self.screen, self.active_buttons)
        if self.barriers.used_barriers:
            show_remove_barrier_button(self.screen, self.active_buttons)

        self.current_piece = None
        self.new_state("zaopeng")

    def zaopeng(self) -> bool:
        """Wake the current player's pieces if all are passive, and offer a barrier action.

        Returns:
            Whether a Zaopeng happened.
        """
        if self.pieces.check_zaopeng(self.current_player):
            hide_piece_buttons(self.screen, self.active_buttons)
            self.pieces.zaopeng(self.current_player)
            for piece in self.pieces.pieces:
                if piece.player == self.current_player:
                    self.board.draw_piece(piece)
            if self.barriers.unused_barriers:
                show_place_barrier_button(self.screen, self.active_buttons)
            if self.barriers.used_barriers:
                show_remove_barrier_button(self.screen, self.active_buttons)

            self.current_piece = None
            self.new_state("zaopeng")

            return True

        else:
            return False

    def place_zaopeng_barrier(self, field: Field) -> None:
        """Place an unused barrier on field."""
        barrier_to_place = self.barriers.unused_barriers[0]
        barrier_to_place.place_on_board(field, self.board, self.barriers)
        PLACE_BARRIER_BUTTON.selected = False

    def remove_zaopeng_barrier(self, field: Field) -> None:
        """Remove the barrier on field."""
        barrier_to_remove = field.barrier
        assert barrier_to_remove is not None
        barrier_to_remove.remove_from_board(self.board, self.barriers)
        REMOVE_BARRIER_BUTTON.selected = False

    def next_turn(self) -> None:
        """Count down effects and pass the turn to the next player."""
        hide_piece_buttons(self.screen, self.active_buttons)

        self.turn += 1
        for field in self.board.fields:
            if field.flame:
                field.countdown_flame(self.current_player)

        for piece in self.pieces.get_pieces_player(self.current_player):
            piece.countdown_frequency()
            piece.countdown_potency()
            piece.countdown_blindness()
            piece.countdown_liberation()
            piece.countdown_perception()

        self.current_player = self.players[self.turn % len(self.players)]
        self.current_piece = None
        self.has_moved = False
        self.has_used_power = False
        self.reset_states()

        if self.zaopeng():
            self.new_state("zaopeng start turn")

        self.set_selectable_fields()

    def reset_piece_selection(self) -> None:
        """Deselect the current piece and go back to 'select piece'."""
        if self.current_piece and self.power:
            self.power.reset_targets()
        self.current_piece = None
        self.has_moved = False
        self.has_used_power = False
        self.new_state("select piece")

    def set_selectable_fields(self) -> None:
        """Work out which of the current player's pieces can be selected this turn.

        Applies Idea and Illusion, and the penalty for having no usable power.
        """
        self.selectable_fields: list[Field] = []

        pieces_able_to_use_power = []

        for piece in self.pieces.get_pieces_player(self.current_player):
            if piece.active:
                movement_options = piece.get_movement_options(self.board)
                can_use_power_from_current_pos = self.power_usable_from_square(
                    piece.location, piece
                )
                can_use_power_from_other_pos = False

                if not piece.illusion and not can_use_power_from_current_pos:
                    for power_cast_location in movement_options:
                        if self.power_usable_from_square(power_cast_location, piece):
                            can_use_power_from_other_pos = True
                            break

                if can_use_power_from_current_pos or can_use_power_from_other_pos:
                    pieces_able_to_use_power.append(piece)
                if piece.idea:
                    if can_use_power_from_current_pos or can_use_power_from_other_pos:
                        self.selectable_fields = [piece.location]
                        break
                    else:
                        piece.deactivate_idea()

                if piece.illusion and piece.idea:
                    can_use_power_from_other_pos = False

                    for power_cast_location in movement_options:
                        if self.power_usable_from_square(power_cast_location, piece):
                            can_use_power_from_other_pos = True
                            break

                    if can_use_power_from_other_pos:
                        self.selectable_fields = [piece.location]
                        break
                    else:
                        piece.deactivate_idea()

                if piece.illusion:
                    if movement_options:
                        self.selectable_fields = [piece.location]
                        break
                    else:
                        piece.deactivate_illusion()

                if movement_options or can_use_power_from_current_pos:
                    self.selectable_fields.append(piece.location)

        if not pieces_able_to_use_power:
            self.current_player.penalty_turns -= 1
            if not self.selectable_fields and not self.current_player.penalty_turns:
                self.penalty_zaopeng()
        else:
            self.current_player.penalty_turns = 2

    def select_piece(self, piece: Piece) -> None:
        """Select piece and show the buttons for what it can do."""
        self.current_piece = piece
        self.movement_options = self.current_piece.get_movement_options(self.board)
        if self.current_piece.idea:
            legal_moves = []
            for movement_option in self.movement_options:
                if self.power_usable_from_square(movement_option, self.current_piece):
                    legal_moves.append(movement_option)
            self.movement_options = legal_moves

        if self.current_piece.illusion:
            show_move_button(self.screen, self.active_buttons)
        else:
            if not self.power_usable_from_square(
                self.current_piece.location, self.current_piece
            ):
                show_move_button(self.screen, self.active_buttons)
            elif not self.movement_options:
                show_power_button(self.screen, self.active_buttons)
            else:
                show_piece_buttons(self.screen, self.active_buttons)

        self.current_piece.location.highlight_colour(
            self.screen, self.board, HIGHLIGHT_BOARD
        )

        self.new_state("select move or use power")

    def show_movement_options(self) -> None:
        """Highlight the squares the selected piece can move to."""
        self.board.highlight_fields(self.current_player, self.movement_options)

    def display_choices(self) -> None:
        """Show a button for each choice of the current power."""
        hide_piece_buttons(self.screen, self.active_buttons)

        x = int(0.7 * HEIGHT)
        relative_position = 0.85
        dimensions = (int(0.2 * HEIGHT), int(HEIGHT / 25))

        assert self.power is not None
        for choice in self.power.get_choices(self.barriers):
            if choice:
                y = int(relative_position * HEIGHT)
                position = (x, y)
                button = ChoiceButton(choice, position, dimensions)
                show_power_choice_button(self.screen, self.active_buttons, button)

                relative_position += 0.05

    def show_power_targets(self) -> None:
        """Highlight the selected targets and the squares that can be selected next."""
        if self.current_target_fields:
            for field in self.current_target_fields:
                self.board.redraw_field(field, BACKGROUND_BOARD)

        assert self.power is not None
        self.power.highlight_selected_fields(self.screen, self.board)

        self.current_target_fields = self.power.get_target_fields(
            self.pieces, self.barriers, self.board, self.players
        )
        self.power.highlight_all_targets(self)

    def show_power_options(self) -> None:
        """Show a button for each usable power of the selected god."""
        print("er hi?")
        hide_piece_buttons(self.screen, self.active_buttons)
        print(self.active_buttons)
        x = int(0.7 * HEIGHT)

        relative_position = 0.75

        dimensions = (int(0.2 * HEIGHT), int(HEIGHT / 25))

        assert self.current_piece is not None
        for power in self.current_piece.powers:
            y = int(relative_position * HEIGHT)
            position = (x, y)

            if power.check_power_usable(
                self.pieces, self.barriers, self.board, self.players
            ):
                button = PowerButton(position, dimensions, power)
                show_power_choice_button(self.screen, self.active_buttons, button)
                relative_position += 0.05

    def power_usable_from_square(self, square: Field, piece: Piece) -> bool:
        """Return whether piece could use a power if it stood on square.

        The piece is moved there temporarily and moved back.
        """
        square_of_origin = self.board.get_field(piece.location.x, piece.location.y)
        assert square_of_origin is not None
        piece.move(square, self.board)
        power_usable = False

        if piece.type == "Heir":
            if piece.power.check_power_usable(
                self.pieces, self.barriers, self.board, self.players
            ):
                power_usable = True
            else:
                power_usable = False
        elif piece.type == "God":
            for power in piece.powers:
                if power.check_power_usable(
                    self.pieces, self.barriers, self.board, self.players
                ):
                    power_usable = True
                    break

        piece.move(square_of_origin, self.board)

        return power_usable

    def move_piece(self, target_square: Field) -> None:
        """Move the selected piece to target_square and show what it can do next."""
        for field in self.movement_options:
            self.board.redraw_field(field, BACKGROUND_BOARD)

        assert self.current_piece is not None
        self.current_piece.move(target_square, self.board)
        hide_move_button(self.screen, self.active_buttons)

        if self.current_piece.idea:
            power_usable = False
            if self.current_piece.type == "Heir":
                if self.current_piece.power.check_power_usable(
                    self.pieces, self.barriers, self.board, self.players
                ):
                    power_usable = True
                else:
                    power_usable = False
            elif self.current_piece.type == "God":
                for power in self.current_piece.powers:
                    if power.check_power_usable(
                        self.pieces, self.barriers, self.board, self.players
                    ):
                        power_usable = True
                        break
            if not power_usable:
                self.current_piece.deactivate_idea()

        if not self.current_piece.idea:
            show_end_turn_button(self.screen, self.active_buttons)

        if self.current_piece.idea or self.power_usable_from_square(
            self.current_piece.location, self.current_piece
        ):
            show_power_button(self.screen, self.active_buttons)
        self.has_moved = True
        self.current_piece.deactivate_illusion()
        self.new_state("select use power or end turn")
        self.board.redraw_field(target_square, colour=HIGHLIGHT_BOARD)

    def random_click(self) -> None:
        """Handle a click that doesn't hit a valid target, resetting the selection if needed."""
        state = self.get_current_state()

        if state in {
            "zaopeng",
            "place barrier",
            "place barrier start turn",
            "remove barrier",
            "remove barrier start turn",
        }:
            pass
        else:
            self.hover = False
            hide_piece_buttons(self.screen, self.active_buttons)
            if self.current_piece and self.has_moved:
                if not self.current_piece.idea:
                    show_end_turn_button(self.screen, self.active_buttons)
                if self.power_usable_from_square(
                    self.current_piece.location, self.current_piece
                ):
                    show_power_button(self.screen, self.active_buttons)

            if (
                self.current_piece
                and self.power
                and state in {"select power target", "make choice"}
            ):
                self.reset_power()
            elif (
                self.current_piece
                and self.has_moved
                and state == "select use power or end turn"
            ) or (self.current_piece and self.has_moved and state == "select power"):
                pass

            else:
                self.reset_piece_selection()

    def detect_click_location(self, mouse: tuple[int, int]) -> Button | Field | None:
        """Return the button or square under the mouse, or None."""
        field = self.board.get_mouse_field(mouse)
        button = get_mouse_button(self.active_buttons, mouse)

        if button:
            return button
        elif field:
            return field
        else:
            return None

    def new_state(self, state_type: str) -> None:
        """Move to state_type, keeping the history."""
        self.state_nr += 1
        self.states.append(state_type)

    def remove_highlighting_targets(self) -> None:
        """Remove the highlighting from the current target squares."""
        for field in self.current_target_fields:
            field.highlight_colour(self.screen, self.board, BACKGROUND_BOARD)

    def reset_power(self) -> None:
        """Cancel the current power selection and show the selected piece's options again."""
        self.hover = False

        fields_to_redraw = []

        # No power is chosen yet when a god's power menu is open on the first power use
        if self.power:
            for possible_target in [
                self.power.selected_piece_1,
                self.power.selected_piece_2,
                self.power.selected_barrier_1,
                self.power.selected_barrier_2,
                self.power.selected_field_1,
                self.power.selected_field_2,
            ]:
                if possible_target:
                    if isinstance(possible_target, Field):
                        fields_to_redraw.append(possible_target)

                    else:
                        assert possible_target.location is not None
                        fields_to_redraw.append(possible_target.location)

        fields_to_redraw += self.current_target_fields

        hide_piece_buttons(self.screen, self.active_buttons)

        if self.power:
            self.power.reset_targets()
        self.has_used_power = False

        for field in fields_to_redraw:
            self.board.redraw_field(field, BACKGROUND_BOARD)

        assert self.current_piece is not None
        if self.has_moved:
            if not self.current_piece.idea:
                show_end_turn_button(self.screen, self.active_buttons)
            if self.power_usable_from_square(
                self.current_piece.location, self.current_piece
            ):
                show_power_button(self.screen, self.active_buttons)
            self.new_state("select use power or end turn")
        else:
            if self.current_piece.illusion:
                show_move_button(self.screen, self.active_buttons)
            else:
                if self.movement_options:
                    show_move_button(self.screen, self.active_buttons)
                if self.power_usable_from_square(
                    self.current_piece.location, self.current_piece
                ):
                    show_power_button(self.screen, self.active_buttons)
            self.new_state("select move or use power")

    def do_click_action(self, mouse: tuple[int, int]) -> None:
        """Handle a mouse click at mouse."""
        state = self.get_current_state()
        selected_entity = self.detect_click_location(mouse)
        if selected_entity:
            if isinstance(selected_entity, Field):
                self.do_field_action(selected_entity)
            elif isinstance(selected_entity, Button):
                self.do_button_action(selected_entity, mouse)
        else:
            if state in {"select power target", "confirm or reset"}:
                self.reset_power()

            else:
                self.random_click()

    def ask_confirmation(self) -> None:
        """Show the CONFIRM and RESET SELECTION buttons."""
        hide_piece_buttons(self.screen, self.active_buttons)
        show_confirm_button(self.screen, self.active_buttons)
        show_reset_selection_button(self.screen, self.active_buttons)
        self.new_state("confirm or reset")

    def do_field_action(self, field: Field) -> None:
        """Handle a click on field according to the current state."""
        state = self.get_current_state()
        if state == "select piece":
            if field in self.selectable_fields:
                assert field.piece is not None
                self.select_piece(field.piece)
            else:
                self.random_click()

        elif state == "select move":
            if field in self.movement_options:
                self.move_piece(field)
            else:
                self.random_click()

        elif state == "select power target":
            if field in self.current_target_fields:
                print("make selection")
                self.select_target(field)
                assert self.power is not None
                if self.power.target_nr > 0:
                    self.show_power_targets()
                    self.new_state("select power target")
                else:
                    self.ask_confirmation()
                    self.hover = False
            else:
                self.reset_power()

        elif state == "place barrier" or state == "place barrier start turn":
            if not field.occupied and field.type != "temple square":
                self.place_zaopeng_barrier(field)
                if state == "place barrier":
                    self.next_turn()
                else:
                    self.reset_piece_selection()
                    hide_piece_buttons(self.screen, self.active_buttons)

        elif state == "remove barrier" or state == "remove barrier start turn":
            if field.barrier:
                self.remove_zaopeng_barrier(field)
                if state == "remove barrier":
                    self.next_turn()
                else:
                    self.reset_piece_selection()
                    hide_piece_buttons(self.screen, self.active_buttons)

        elif state == "select use power or end turn":
            self.random_click()

        elif state in {"select power", "confirm or reset", "make choice"}:
            self.reset_power()

        else:
            self.random_click()

    def select_power(self, button: PowerButton, mouse: tuple[int, int]) -> None:
        """Start using the power of the clicked power button."""
        self.power = button.power
        hide_piece_buttons(self.screen, self.active_buttons)

        if self.power.fixed_affected_area:
            self.current_target_fields = self.power.get_target_fields_1(self.board)
            self.board.highlight_fields_strong(
                self.current_player, self.current_target_fields
            )
            self.ask_confirmation()
        else:
            if not self.power.start_with_choice:
                self.show_power_targets()
                self.new_state("select power target")
            else:
                self.display_choices()
                self.new_state("make choice")

    def make_choice(self, button: Button) -> None:
        """Apply the clicked choice to the current power."""
        assert self.power is not None
        self.power.choice = button.text
        if (
            self.power.choice == "Place 1 barrier"
            or self.power.choice == "Remove 1 barrier"
        ):
            self.power.target_nr -= 1
        elif self.power.choice == "Increase potency":
            self.power.potency_or_frequency = "potency"
        elif self.power.choice == "Increase frequency":
            self.power.potency_or_frequency = "frequency"

        hide_piece_buttons(self.screen, self.active_buttons)
        self.new_state("select power target")

    def do_button_action(self, button: Button, mouse: tuple[int, int]) -> None:
        """Handle a click on button according to the current state."""
        state = self.get_current_state()
        if button.text == "MOVE":
            self.show_movement_options()
            self.new_state("select move")
        elif button.text == "USE POWER":
            for field in self.movement_options:
                if field.piece != self.current_piece:
                    self.board.redraw_field(field, BACKGROUND_BOARD)

            assert self.current_piece is not None
            if self.current_piece.type == "God":
                self.new_state("select power")
                self.show_power_options()
            elif self.current_piece.type == "Heir":
                self.power = self.current_piece.power
                hide_piece_buttons(self.screen, self.active_buttons)
                show_reset_selection_button(self.screen, self.active_buttons)

                if self.power.fixed_affected_area:
                    self.current_target_fields = self.power.get_target_fields_1(
                        self.board
                    )
                    self.board.highlight_fields_strong(
                        self.current_player, self.current_target_fields
                    )
                    self.ask_confirmation()

                elif not self.power.start_with_choice:
                    self.show_power_targets()
                    self.new_state("select power target")

                else:
                    self.display_choices()
                    self.new_state("make choice")

        elif isinstance(button, PowerButton):
            self.select_power(button, mouse)

        elif isinstance(button, ChoiceButton):
            self.make_choice(button)
            self.show_power_targets()

        elif button.text == "CONFIRM":
            assert self.power is not None and self.current_piece is not None
            self.power.activate_power(self.pieces, self.barriers, self.board)
            self.remove_highlighting_targets()
            self.current_target_fields = []

            if not self.current_piece.frequency:
                if not self.zaopeng():
                    self.next_turn()

            else:
                self.current_piece.countdown_frequency()
                print("Frequency", self.current_piece.frequency)
                hide_piece_buttons(self.screen, self.active_buttons)
                if self.power_usable_from_square(
                    self.current_piece.location, self.current_piece
                ):
                    show_power_button(self.screen, self.active_buttons)
                show_end_turn_button(self.screen, self.active_buttons)

                self.new_state("select use power or end turn")

        elif button.text == "END TURN":
            if not self.current_player.penalty_turns:
                self.penalty_zaopeng()
            else:
                self.next_turn()
        elif button.text == "RESET SELECTION":
            self.reset_power()
        elif button.text == "PLACE BARRIER":
            button.selected = True
            REMOVE_BARRIER_BUTTON.selected = False
            if state in {"zaopeng", "remove barrier"}:
                self.new_state("place barrier")
            elif state in {"zaopeng start turn", "remove barrier start turn"}:
                self.new_state("place barrier start turn")
        elif button.text == "REMOVE BARRIER":
            button.selected = True
            PLACE_BARRIER_BUTTON.selected = False
            if state in {"zaopeng", "place barrier"}:
                self.new_state("remove barrier")
            elif state in {"zaopeng start turn", "place barrier start turn"}:
                self.new_state("remove barrier start turn")

        else:
            if state in {"select power", "confirm or reset"}:
                self.reset_power()

            else:
                self.random_click()
