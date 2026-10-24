"""Pieces: gods and heirs, their state and their movement."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pygame

from daeqhipao.illegal_moves import IllegalPower, Immune
from daeqhipao.powers import (
    BlindnessPower,
    BloodmakerPower,
    CommunicationPower,
    DeathPower,
    DroughtPower,
    EarthPower,
    EndPower,
    FamiliarityPower,
    FlamePower,
    FogPower,
    IdeaPower,
    IllusionPower,
    ImpressionPower,
    LegacyPower,
    LiberationPower,
    LifePower,
    MetalmakerPower,
    MetamorphosisPower,
    MindPower,
    NightPower,
    OblivionPower,
    OceanPower,
    PerceptionPower,
    QuakePower,
    ShadowPower,
    SkyPower,
    SunPower,
    TimePower,
    UnionPower,
    VoidPower,
    WavePower,
    WindPower,
)
from daeqhipao.style import (
    BACKGROUND_BOARD,
    PIECE_PADDING,
    PIECE_SIZE,
    SQUARE_WIDTH,
    SYMBOL_PADDING,
    SYMBOL_SIZE,
)

if TYPE_CHECKING:
    from daeqhipao.board import Board
    from daeqhipao.fields import Field
    from daeqhipao.players import Player
    from daeqhipao.powers import Power

SYMBOL_DIR = os.path.join(os.path.dirname(__file__), "images", "symbols")


class Pieces:
    """All pieces in the game, grouped by state, domain and god group.

    Args:
        pieces: Every piece in the game.
    """

    def __init__(self, pieces: list[Piece]) -> None:
        self.pieces = pieces
        self.active_pieces: list[Piece] = []
        self.passive_pieces: list[Piece] = []
        self.set_active_and_passive_pieces()
        self.set_domains()
        self.set_god_groups()

    def set_active_and_passive_pieces(self) -> None:
        """Recompute the lists of active and passive pieces."""
        self.active_pieces = []
        self.passive_pieces = []
        for piece in self.pieces:
            if piece.active:
                self.active_pieces.append(piece)
            else:
                self.passive_pieces.append(piece)

    def check_zaopeng(self, player: Player) -> bool:
        """Return whether all of player's pieces are passive."""
        for piece in self.pieces:
            if piece.player == player and piece.active:
                return False

        return True

    def zaopeng(self, player: Player) -> None:
        """Wake player's passive pieces; pieces under Oblivion count it down instead."""
        for piece in self.pieces:
            if piece.player == player and not piece.active:
                if not piece.oblivion:
                    piece.wake(self)
                else:
                    piece.countdown_oblivion()
        self.set_active_and_passive_pieces()

    def get_pieces_player(self, player: Player) -> list[Piece]:
        """Return player's pieces."""
        player_pieces = []
        for piece in self.pieces:
            if piece.player == player:
                player_pieces.append(piece)

        return player_pieces

    def set_domains(self) -> None:
        """Split the pieces into spiritual and physical ones."""
        self.spiritual_pieces: list[Piece] = []
        self.physical_pieces: list[Piece] = []
        for piece in self.pieces:
            if piece.domain == "spiritual":
                self.spiritual_pieces.append(piece)
            elif piece.domain == "physical":
                self.physical_pieces.append(piece)

    def set_god_groups(self) -> None:
        """Group the heirs by the god they belong to."""
        self.god_groups: dict[str, list[Piece]] = {
            "builder": [],
            "mover": [],
            "alchemist": [],
            "consumer": [],
            "gifter": [],
            "connector": [],
            "director": [],
            "wiper": [],
        }
        for piece in self.pieces:
            if piece.god_group:
                self.god_groups[piece.god_group].append(piece)


class Piece:
    """A piece on the board: the base class of gods and heirs.

    Args:
        piece_id: Unique number of the piece.
        player: The player who owns the piece.
    """

    # Set by every concrete piece class
    name: str
    type: str
    symbol: str
    powers: list[Power]
    power: Power

    def __init__(self, piece_id: int, player: Player) -> None:
        self.id = piece_id
        # Set by set_location when the piece is placed on the board
        self.location: Field
        self.gender: str | None = None
        self.domain: str | None = None
        self.god_group: str | None = None

        self.active = True
        self.player = player

        self.idea = False
        self.illusion = False
        self.perception = 0
        self.legacy = False
        self.legacy_frequency = False
        self.legacy_duration = False

        self.potency: int = False
        self.frequency: int = False

        self.union = False
        self.union_partners: set[Piece] = set()
        self.communication = 0
        self.communication_active = 0

        self.blindness = 0
        self.oblivion = 0
        self.liberation = 0

        self.ocean_fields: set[Field] = set()
        self.drought_fields: set[Field] = set()
        self.flame_fields: set[Field] = set()

        # Set by load_symbol_image and set_location
        self.symbol_image: pygame.Surface
        self.piece_rectangle: pygame.Rect
        self.symbol_rectangle: pygame.Rect
        self.selection_nr = 0
        self.perception = 0

        self.movement_type = "all"

    def __eq__(self, piece: object) -> bool:
        if isinstance(piece, Piece) and type(self) == type(piece):
            return self.id == piece.id
        else:
            return False

    def __hash__(self) -> int:
        return self.id

    def __repr__(self) -> str:
        return self.name

    def get_movement_options(self, board: Board) -> list[Field]:
        """Return the squares the piece can move to."""
        legal_fields = self.location.get_legal_adjacent(board, self)

        return legal_fields

    def is_last_active_piece(self, pieces: Pieces) -> bool:
        """Return whether this is the only active piece of its player."""
        if self.active:
            active_count = 0
            for piece in pieces.get_pieces_player(self.player):
                if piece.active:
                    active_count += 1

            return active_count == 1
        else:
            return False

    def countdown_frequency(self) -> None:
        """Count the frequency down by one, stopping at 0."""
        if self.frequency > 0:
            self.frequency -= 1

    def countdown_potency(self) -> None:
        """Count the potency down by one, stopping at 0."""
        if self.potency > 0:
            self.potency -= 1

    def set_piece_rectangle(self) -> None:
        """Compute the screen rectangle of the piece's body from its location."""
        x = (1 + self.location.x) * SQUARE_WIDTH + PIECE_PADDING
        y = (1 + self.location.y) * SQUARE_WIDTH + PIECE_PADDING
        self.piece_rectangle = pygame.Rect(x, y, PIECE_SIZE, PIECE_SIZE)

    def set_symbol_rectangle(self) -> None:
        """Compute the screen rectangle of the piece's symbol from its location."""
        x = (1 + self.location.x) * SQUARE_WIDTH + SYMBOL_PADDING
        y = (1 + self.location.y) * SQUARE_WIDTH + SYMBOL_PADDING
        self.symbol_rectangle = pygame.Rect(x, y, SYMBOL_SIZE, SYMBOL_SIZE)

    def load_symbol_image(self) -> None:
        """Load the symbol image images/symbols/<name>.png."""
        symbol = os.path.join(SYMBOL_DIR, f"{self.name}.png")
        self.symbol_image = pygame.image.load(symbol)

    def set_location(self, location: tuple[int, int], board: Board) -> None:
        """Place the piece on the square at location and compute its rectangles."""
        x, y = location

        field = board.get_field(x, y)

        if field:
            self.location = field
            field.piece = self
            field.check_occupied()

        self.set_piece_rectangle()
        self.set_symbol_rectangle()

    def choose_legacy_effect(self, choice: str, power: str) -> None:
        """Record a Legacy choice to extend the duration or frequency of a power.

        Args:
            choice: 'duration' or 'frequency'.
            power: Name of the power.

        Raises:
            IllegalPower: If that power's duration or frequency can't be altered.
        """
        assert self.legacy
        assert choice in ["duration", "frequency"]

        duration = {
            "Time",
            "Mind",
            "Perception",
            "Union",
            "Communication",
            "Oblivion",
            "Liberation",
            "Blindness",
            "Ocean",
            "Flame",
            "Drought",
            "Void",
        }
        frequency = {
            "Illusion",
            "Idea",
            "Time",
            "Life",
            "Death",
            "Wave",
            "Perception",
            "Union",
            "Impression",
            "Communication",
            "Metamorphosis",
            "Oblivion",
            "Liberation",
            "Blindness",
            "Earth",
            "Ocean",
            "Sun",
            "Sky",
            "Quake",
            "Wind",
            "Shadow",
            "Bloodmaker",
            "Metalmaker",
            "Fog",
            "Drought",
            "Void",
            "End",
            "Night",
        }

        if choice == "duration":
            if not power in duration:
                raise IllegalPower("duration")
            self.legacy_duration = True
        elif choice == "frequency":
            if not power in frequency:
                raise IllegalPower("frequency")
            self.legacy_frequency = True

    def set_potency(self, user: Piece) -> None:
        """Set the potency to 2 if user belongs to the same player, otherwise 1."""
        if self.player == user.player:
            self.potency = 2
        else:
            self.potency = 1

    def set_frequency(self, user: Piece) -> None:
        """Set the frequency to 2 if user belongs to the same player, otherwise 1."""
        if self.player == user.player:
            self.frequency = 2
        else:
            self.frequency = 1

    def activate_perception(self, user: Piece, potency: int = 0) -> None:
        """Make the piece immune for a number of turns that depends on user and potency."""
        if not potency:
            if self.player == user.player:
                self.perception = 3
            else:
                self.perception = 2
        else:
            if self.player == user.player:
                self.perception = 5
            else:
                self.perception = 4

    def countdown_perception(self) -> None:
        """Count down the Perception immunity."""
        if self.perception:
            self.perception -= 1

    def sleep(self, pieces: Pieces) -> None:
        """Make the piece passive, unless a legacy frequency keeps it active, with its Union partners."""
        if not self.legacy_frequency:
            self.active = False
            pieces.active_pieces.remove(self)
            pieces.passive_pieces.append(self)
            if self.union:
                self.trigger_union(pieces, "sleep")

    def wake(self, pieces: Pieces) -> None:
        """Make the piece active, lift its oceans and droughts, and wake its Union partners."""
        self.active = True
        for field in self.drought_fields:
            field.deactivate_drought(self)
        for field in self.ocean_fields:
            field.deactivate_ocean(self)
        self.ocean_fields = set()
        self.drought_fields = set()
        pieces.active_pieces.append(self)
        pieces.passive_pieces.remove(self)

        if self.union:
            self.trigger_union(pieces, "wake")

    def activate_union(self, piece: Piece) -> None:
        """Link the flip state of this piece to piece and piece's partners."""
        self.union = True
        self.union_partners.add(piece)
        for piece_2 in piece.union_partners:
            if piece_2 != self:
                self.union_partners.add(piece_2)

    def trigger_union(self, pieces: Pieces, wake_or_sleep: str) -> None:
        """Dissolve the union and wake or put to sleep every partner.

        Args:
            pieces: All pieces.
            wake_or_sleep: 'wake' or 'sleep'.
        """
        self.union = False
        for union_partner in self.union_partners:
            union_partner.union = False
            union_partner.union_partners = set()
            if wake_or_sleep == "wake":
                union_partner.wake(pieces)
            elif wake_or_sleep == "sleep":
                union_partner.sleep(pieces)
        self.union_partners = set()

    def deactivate_legacy(self, choice: str) -> None:
        """Clear the piece's Legacy effects."""
        self.legacy_duration = False
        self.legacy_frequency = False
        self.legacy = False

    def activate_communication(self, user: Piece, potency: int = 0) -> None:
        """Set the Communication counters from user's player and potency."""
        if self.player == user.player:
            self.communication_active = 2
        else:
            self.communication_active = 1

        if not potency:
            self.communication = 2
        else:
            self.communication = 4

    def countdown_communication(self) -> None:
        """Count Communication down by one, stopping at 1."""
        if self.communication > 1:
            self.communication -= 1

    def reset_communication(self) -> None:
        """Count down how long Communication stays active."""
        if self.communication_active > 0:
            self.communication_active -= 1

    def activate_illusion(self) -> None:
        """Mark the piece and its player with Illusion."""
        self.illusion = True
        self.player.illusion = True

    def deactivate_illusion(self) -> None:
        """Clear Illusion from the piece and its player."""
        self.illusion = False
        self.player.illusion = False

    def activate_idea(self) -> None:
        """Mark the piece and its player with Idea."""
        self.idea = True
        self.player.idea = True

    def deactivate_idea(self) -> None:
        """Clear Idea from the piece and its player."""
        self.idea = False
        self.player.idea = False

    def set_blindness(self, user: Piece) -> None:
        """Set Blindness to 2 turns, or 4 if user has a legacy duration."""
        if user.legacy_duration:
            self.blindness = 4
        else:
            self.blindness = 2

    def countdown_blindness(self) -> None:
        """Count down Blindness."""
        if self.blindness > 0:
            self.blindness -= 1

    def set_oblivion(self, user: Piece) -> None:
        """Set Oblivion to 1 Zaopeng, or 2 if user has a legacy duration."""
        if user.legacy_duration:
            self.oblivion = 2
        else:
            self.oblivion = 1

    def countdown_oblivion(self) -> None:
        """Count Oblivion down by one Zaopeng."""
        self.oblivion -= 1
        assert self.oblivion >= 0

    def set_liberation(self, user: Piece) -> None:
        """Set Liberation to 2 turns, or 3 if user has a legacy duration."""
        if user.legacy_duration:
            self.liberation = 3
        else:
            self.liberation = 2

    def countdown_liberation(self) -> None:
        """Count down Liberation."""
        if self.liberation > 0:
            self.liberation -= 1

    def immune(self, power: str) -> bool:
        """Return whether the piece is immune to the named power.

        A piece with Perception is immune to everything, a god to its own powers
        and an heir to its own power.
        """
        if self.perception:
            return True

        elif self.type == "God":
            return power in [p.name for p in self.powers]
        elif self.type == "Heir":
            return power == self.name
        return False

    def move(self, target_location: Field, board: Board) -> None:
        """Move the piece to target_location and redraw it."""
        original_x = self.location.x
        original_y = self.location.y

        x_diff = target_location.x - self.location.x
        y_diff = target_location.y - self.location.y

        self.location.piece = None
        self.location.check_occupied()

        self.location = target_location
        self.location.piece = self
        self.location.check_occupied()

        self.piece_rectangle = self.piece_rectangle.move(
            x_diff * SQUARE_WIDTH, y_diff * SQUARE_WIDTH
        )
        self.symbol_rectangle = self.symbol_rectangle.move(
            x_diff * SQUARE_WIDTH, y_diff * SQUARE_WIDTH
        )
        origin_square = board.get_field(original_x, original_y)
        assert origin_square is not None

        board.redraw_field(origin_square, BACKGROUND_BOARD)
        board.draw_piece(self)

    def select_piece(self, piece: Piece, power: str) -> None:
        """Check that piece can be targeted by power.

        Raises:
            Immune: If piece is immune to power.
        """
        if piece.immune(power):
            raise Immune(f"{piece} is immune to the power {power}.")


class God(Piece):
    """Base class of the gods, which move in all 8 directions and have four powers."""

    def __init__(self, nr: int, player: Player) -> None:
        Piece.__init__(self, nr, player)
        self.type = "God"
        self.movement_type = "all"


# ==============================================================================


class Builder(God):
    """Builder god (female, physical): Earth, Ocean, Sky and Sun powers."""

    def __init__(self, nr: int, player: Player) -> None:
        God.__init__(self, nr, player)
        self.gender = "female"
        self.name = "Builder"
        self.powers = [
            EarthPower(self),
            OceanPower(self),
            SkyPower(self),
            SunPower(self),
        ]
        self.symbol = "e"
        self.load_symbol_image()
        self.domain = "physical"


class Alchemist(God):
    """Alchemist god (female, physical): Metalmaker, Bloodmaker, Fog and Flame powers."""

    def __init__(self, nr: int, player: Player) -> None:
        God.__init__(self, nr, player)
        self.gender = "female"
        self.name = "Alchemist"
        self.powers = [
            MetalmakerPower(self),
            BloodmakerPower(self),
            FogPower(self),
            FlamePower(self),
        ]
        self.symbol = "g"
        self.load_symbol_image()
        self.domain = "physical"


class Connector(God):
    """Connector god (female, spiritual): Union, Impression, Communication and Familiarity powers."""

    def __init__(self, nr: int, player: Player) -> None:
        God.__init__(self, nr, player)
        self.gender = "female"
        self.name = "Connector"
        self.powers = [
            UnionPower(self),
            ImpressionPower(self),
            CommunicationPower(self),
            FamiliarityPower(self),
        ]
        self.symbol = "b"
        self.load_symbol_image()
        self.domain = "spiritual"


class Wiper(God):
    """Wiper god (female, spiritual): Death, Blindness, Oblivion and Liberation powers."""

    def __init__(self, nr: int, player: Player) -> None:
        God.__init__(self, nr, player)
        self.gender = "female"
        self.name = "Wiper"
        self.powers = [
            DeathPower(self),
            BlindnessPower(self),
            OblivionPower(self),
            LiberationPower(self),
        ]
        self.symbol = "d"
        self.load_symbol_image()
        self.domain = "spiritual"


class Mover(God):
    """Mover god (male, physical): Quake, Wave, Wind and Shadow powers."""

    def __init__(self, nr: int, player: Player) -> None:
        God.__init__(self, nr, player)
        self.gender = "male"
        self.name = "Mover"
        self.powers = [
            QuakePower(self),
            WavePower(self),
            WindPower(self),
            ShadowPower(self),
        ]
        self.symbol = "f"
        self.load_symbol_image()
        self.domain = "physical"


class Consumer(God):
    """Consumer god (male, physical): Void, Drought, End and Night powers."""

    def __init__(self, nr: int, player: Player) -> None:
        God.__init__(self, nr, player)
        self.gender = "male"
        self.name = "Consumer"
        self.powers = [
            VoidPower(self),
            DroughtPower(self),
            EndPower(self),
            NightPower(self),
        ]
        self.symbol = "h"
        self.load_symbol_image()
        self.domain = "physical"


class Gifter(God):
    """Gifter god (male, spiritual): Life, Perception, Mind and Legacy powers."""

    def __init__(self, nr: int, player: Player) -> None:
        God.__init__(self, nr, player)
        self.gender = "male"
        self.name = "Gifter"
        self.powers = [
            LifePower(self),
            PerceptionPower(self),
            MindPower(self),
            LegacyPower(self),
        ]
        self.symbol = "a"
        self.load_symbol_image()
        self.domain = "spiritual"


class Director(God):
    """Director god (male, spiritual): Time, Illusion, Idea and Metamorphosis powers."""

    def __init__(self, nr: int, player: Player) -> None:
        God.__init__(self, nr, player)
        self.gender = "male"
        self.name = "Director"
        self.powers = [
            TimePower(self),
            IllusionPower(self),
            IdeaPower(self),
            MetamorphosisPower(self),
        ]
        self.symbol = "c"
        self.load_symbol_image()
        self.domain = "spiritual"


# ==============================================================================


class FemaleHeir(Piece):
    """Base class of the female heirs, which move horizontally and vertically."""

    def __init__(self, nr: int, player: Player) -> None:
        Piece.__init__(self, nr, player)
        self.gender = "female"
        self.type = "Heir"
        self.movement_type = "horizontal"


class MaleHeir(Piece):
    """Base class of the male heirs, which move diagonally."""

    def __init__(self, nr: int, player: Player) -> None:
        Piece.__init__(self, nr, player)
        self.gender = "male"
        self.type = "Heir"
        self.movement_type = "diagonal"


# ==============================================================================


class Union(FemaleHeir):
    """Union heir of the Connector (spiritual)."""

    def __init__(self, nr: int, player: Player) -> None:
        FemaleHeir.__init__(self, nr, player)
        self.name = "Union"
        self.symbol = "m"
        self.load_symbol_image()
        self.power = UnionPower(self)
        self.domain = "spiritual"
        self.god_group = "connector"


class Impression(FemaleHeir):
    """Impression heir of the Connector (spiritual)."""

    def __init__(self, nr: int, player: Player) -> None:
        FemaleHeir.__init__(self, nr, player)
        self.name = "Impression"
        self.symbol = "n"
        self.load_symbol_image()
        self.power = ImpressionPower(self)
        self.domain = "spiritual"
        self.god_group = "connector"


class Communication(FemaleHeir):
    """Communication heir of the Connector (spiritual)."""

    def __init__(self, nr: int, player: Player) -> None:
        FemaleHeir.__init__(self, nr, player)
        self.name = "Communication"
        self.symbol = "o"
        self.load_symbol_image()
        self.selections = ["piece"]
        self.power = CommunicationPower(self)
        self.domain = "spiritual"
        self.god_group = "connector"


class Familiarity(FemaleHeir):
    """Familiarity heir of the Connector (spiritual)."""

    def __init__(self, nr: int, player: Player) -> None:
        FemaleHeir.__init__(self, nr, player)
        self.name = "Familiarity"
        self.symbol = "p"
        self.load_symbol_image()
        self.power = FamiliarityPower(self)
        self.domain = "spiritual"
        self.god_group = "connector"


class Death(FemaleHeir):
    """Death heir of the Wiper (spiritual)."""

    def __init__(self, nr: int, player: Player) -> None:
        FemaleHeir.__init__(self, nr, player)
        self.name = "Death"
        self.symbol = "u"
        self.load_symbol_image()
        self.power = DeathPower(self)
        self.domain = "spiritual"
        self.god_group = "wiper"


class Blindness(FemaleHeir):
    """Blindness heir of the Wiper (spiritual)."""

    def __init__(self, nr: int, player: Player) -> None:
        FemaleHeir.__init__(self, nr, player)
        self.name = "Blindness"
        self.symbol = "v"
        self.load_symbol_image()
        self.power = BlindnessPower(self)
        self.domain = "spiritual"
        self.god_group = "wiper"


class Oblivion(FemaleHeir):
    """Oblivion heir of the Wiper (spiritual)."""

    def __init__(self, nr: int, player: Player) -> None:
        FemaleHeir.__init__(self, nr, player)
        self.name = "Oblivion"
        self.symbol = "w"
        self.load_symbol_image()
        self.selections = ["piece"]
        self.power = OblivionPower(self)
        self.domain = "spiritual"
        self.god_group = "wiper"


class Liberation(FemaleHeir):
    """Liberation heir of the Wiper (spiritual)."""

    def __init__(self, nr: int, player: Player) -> None:
        FemaleHeir.__init__(self, nr, player)
        self.name = "Liberation"
        self.symbol = "x"
        self.load_symbol_image()
        self.selections = ["piece"]
        self.power = LiberationPower(self)
        self.domain = "spiritual"
        self.god_group = "wiper"


class Earth(FemaleHeir):
    """Earth heir of the Builder (physical)."""

    def __init__(self, nr: int, player: Player) -> None:
        FemaleHeir.__init__(self, nr, player)
        self.name = "Earth"
        self.symbol = "y"
        self.load_symbol_image()
        self.selections = ["field"]
        self.power = EarthPower(self)
        self.domain = "physical"
        self.god_group = "builder"


class Ocean(FemaleHeir):
    """Ocean heir of the Builder (physical)."""

    def __init__(self, nr: int, player: Player) -> None:
        FemaleHeir.__init__(self, nr, player)
        self.name = "Ocean"
        self.symbol = "z"
        self.load_symbol_image()
        self.power = OceanPower(self)
        self.domain = "physical"
        self.god_group = "builder"


class Sky(FemaleHeir):
    """Sky heir of the Builder (physical)."""

    def __init__(self, nr: int, player: Player) -> None:
        FemaleHeir.__init__(self, nr, player)
        self.name = "Sky"
        self.symbol = "A"
        self.load_symbol_image()
        self.power = SkyPower(self)
        self.domain = "physical"
        self.god_group = "builder"


class Sun(FemaleHeir):
    """Sun heir of the Builder (physical)."""

    def __init__(self, nr: int, player: Player) -> None:
        FemaleHeir.__init__(self, nr, player)
        self.name = "Sun"
        self.symbol = "B"
        self.load_symbol_image()
        self.power = SunPower(self)
        self.domain = "physical"
        self.god_group = "builder"


class Metalmaker(FemaleHeir):
    """Metalmaker heir of the Alchemist (physical)."""

    def __init__(self, nr: int, player: Player) -> None:
        FemaleHeir.__init__(self, nr, player)
        self.name = "Metalmaker"
        self.symbol = "G"
        self.load_symbol_image()
        self.power = MetalmakerPower(self)
        self.domain = "physical"
        self.god_group = "alchemist"


class Bloodmaker(FemaleHeir):
    """Bloodmaker heir of the Alchemist (physical)."""

    def __init__(self, nr: int, player: Player) -> None:
        FemaleHeir.__init__(self, nr, player)
        self.name = "Bloodmaker"
        self.symbol = "H"
        self.load_symbol_image()
        self.power = BloodmakerPower(self)
        self.domain = "physical"
        self.god_group = "alchemist"


class Fog(FemaleHeir):
    """Fog heir of the Alchemist (physical)."""

    def __init__(self, nr: int, player: Player) -> None:
        FemaleHeir.__init__(self, nr, player)
        self.name = "Fog"
        self.symbol = "I"
        self.load_symbol_image()
        self.power = FogPower(self)
        self.domain = "physical"
        self.god_group = "alchemist"


class Flame(FemaleHeir):
    """Flame heir of the Alchemist (physical)."""

    def __init__(self, nr: int, player: Player) -> None:
        FemaleHeir.__init__(self, nr, player)
        self.name = "Flame"
        self.symbol = "J"
        self.load_symbol_image()
        self.power = FlamePower(self)
        self.domain = "physical"
        self.god_group = "alchemist"


# ==============================================================================


class Life(MaleHeir):
    """Life heir of the Gifter (spiritual)."""

    def __init__(self, nr: int, player: Player) -> None:
        MaleHeir.__init__(self, nr, player)
        self.name = "Life"
        self.symbol = "i"
        self.load_symbol_image()
        self.power = LifePower(self)
        self.domain = "spiritual"
        self.god_group = "gifter"


class Perception(MaleHeir):
    """Perception heir of the Gifter (spiritual)."""

    def __init__(self, nr: int, player: Player) -> None:
        MaleHeir.__init__(self, nr, player)
        self.name = "Perception"
        self.symbol = "j"
        self.load_symbol_image()
        self.power = PerceptionPower(self)
        self.domain = "spiritual"
        self.god_group = "gifter"


class Mind(MaleHeir):
    """Mind heir of the Gifter (spiritual)."""

    def __init__(self, nr: int, player: Player) -> None:
        MaleHeir.__init__(self, nr, player)
        self.name = "Mind"
        self.symbol = "k"
        self.load_symbol_image()
        self.power = MindPower(self)
        self.domain = "spiritual"
        self.god_group = "gifter"


class Legacy(MaleHeir):
    """Legacy heir of the Gifter (spiritual)."""

    def __init__(self, nr: int, player: Player) -> None:
        MaleHeir.__init__(self, nr, player)
        self.name = "Legacy"
        self.symbol = "l"
        self.load_symbol_image()
        self.power = LegacyPower(self)
        self.domain = "spiritual"
        self.god_group = "gifter"


class Time(MaleHeir):
    """Time heir of the Director (spiritual)."""

    def __init__(self, nr: int, player: Player) -> None:
        MaleHeir.__init__(self, nr, player)
        self.name = "Time"
        self.symbol = "q"
        self.load_symbol_image()
        self.power = TimePower(self)
        self.domain = "spiritual"
        self.god_group = "director"


class Illusion(MaleHeir):
    """Illusion heir of the Director (spiritual)."""

    def __init__(self, nr: int, player: Player) -> None:
        MaleHeir.__init__(self, nr, player)
        self.name = "Illusion"
        self.symbol = "r"
        self.load_symbol_image()
        self.power = IllusionPower(self)
        self.domain = "spiritual"
        self.god_group = "director"


class Idea(MaleHeir):
    """Idea heir of the Director (spiritual)."""

    def __init__(self, nr: int, player: Player) -> None:
        MaleHeir.__init__(self, nr, player)
        self.name = "Idea"
        self.symbol = "s"
        self.load_symbol_image()
        self.power = IdeaPower(self)
        self.domain = "spiritual"
        self.god_group = "director"


class Metamorphosis(MaleHeir):
    """Metamorphosis heir of the Director (spiritual)."""

    def __init__(self, nr: int, player: Player) -> None:
        MaleHeir.__init__(self, nr, player)
        self.name = "Metamorphosis"
        self.symbol = "t"
        self.load_symbol_image()
        self.power = MetamorphosisPower(self)
        self.domain = "spiritual"
        self.god_group = "director"


class Quake(MaleHeir):
    """Quake heir of the Mover (physical)."""

    def __init__(self, nr: int, player: Player) -> None:
        MaleHeir.__init__(self, nr, player)
        self.name = "Quake"
        self.symbol = "C"
        self.load_symbol_image()
        self.power = QuakePower(self)
        self.domain = "physical"
        self.god_group = "mover"


class Wave(MaleHeir):
    """Wave heir of the Mover (physical)."""

    def __init__(self, nr: int, player: Player) -> None:
        MaleHeir.__init__(self, nr, player)
        self.name = "Wave"
        self.symbol = "D"
        self.load_symbol_image()
        self.power = WavePower(self)
        self.domain = "physical"
        self.god_group = "mover"


class Wind(MaleHeir):
    """Wind heir of the Mover (physical)."""

    def __init__(self, nr: int, player: Player) -> None:
        MaleHeir.__init__(self, nr, player)
        self.name = "Wind"
        self.symbol = "E"
        self.load_symbol_image()
        self.power = WindPower(self)
        self.domain = "physical"
        self.god_group = "mover"


class Shadow(MaleHeir):
    """Shadow heir of the Mover (physical)."""

    def __init__(self, nr: int, player: Player) -> None:
        MaleHeir.__init__(self, nr, player)
        self.name = "Shadow"
        self.symbol = "F"
        self.load_symbol_image()
        self.power = ShadowPower(self)
        self.domain = "physical"
        self.god_group = "mover"


class Void(MaleHeir):
    """Void heir of the Consumer (physical)."""

    def __init__(self, nr: int, player: Player) -> None:
        MaleHeir.__init__(self, nr, player)
        self.name = "Void"
        self.symbol = "K"
        self.load_symbol_image()
        self.power = VoidPower(self)
        self.domain = "physical"
        self.god_group = "consumer"


class Drought(MaleHeir):
    """Drought heir of the Consumer (physical)."""

    def __init__(self, nr: int, player: Player) -> None:
        MaleHeir.__init__(self, nr, player)
        self.name = "Drought"
        self.symbol = "L"
        self.load_symbol_image()
        self.power = DroughtPower(self)
        self.domain = "physical"
        self.god_group = "consumer"


class End(MaleHeir):
    """End heir of the Consumer (physical)."""

    def __init__(self, nr: int, player: Player) -> None:
        MaleHeir.__init__(self, nr, player)
        self.name = "End"
        self.symbol = "M"
        self.load_symbol_image()
        self.power = EndPower(self)
        self.domain = "physical"
        self.god_group = "consumer"


class Night(MaleHeir):
    """Night heir of the Consumer (physical)."""

    def __init__(self, nr: int, player: Player) -> None:
        MaleHeir.__init__(self, nr, player)
        self.name = "Night"
        self.symbol = "N"
        self.load_symbol_image()
        self.power = NightPower(self)
        self.domain = "physical"
        self.god_group = "consumer"
