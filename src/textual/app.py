from __future__ import annotations

from typing import Iterable

from .pilot import Pilot
from .widgets import Widget


class ComposeResult(list):
    pass


class _TestContext:
    def __init__(self, app: "App"):
        self.app = app
        self.pilot = Pilot(app)

    async def __aenter__(self):
        return self.pilot

    async def __aexit__(self, exc_type, exc, tb):
        return False


class App(Widget):
    CSS_PATH = None
    BINDINGS = []

    def __init__(self) -> None:
        super().__init__(id=None)
        self._composed = False

    def compose(self) -> Iterable[Widget]:
        return []

    def _compose_app(self) -> None:
        if not self._composed:
            for child in self.compose():
                self.mount(child)
            self._composed = True

    def run(self) -> None:  # pragma: no cover - not used in tests
        self._compose_app()

    def run_test(self) -> _TestContext:
        self._compose_app()
        return _TestContext(self)
