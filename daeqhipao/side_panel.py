"""The grey panel to the right of the board."""

import pygame

from daeqhipao.style import BACKGROUND_PANEL, PANEL


class SidePanel:
    """The panel next to the board.

    Args:
        screen: The pygame surface to draw on.
    """

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen

    def draw_panel(self) -> None:
        """Fill the side panel area with the panel colour."""
        pygame.draw.rect(self.screen, BACKGROUND_PANEL, PANEL)
