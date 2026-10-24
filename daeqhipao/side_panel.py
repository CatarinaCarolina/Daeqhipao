import pygame

from daeqhipao.style import BACKGROUND_PANEL, PANEL


class SidePanel:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen

    def draw_panel(self) -> None:
        pygame.draw.rect(self.screen, BACKGROUND_PANEL, PANEL)
