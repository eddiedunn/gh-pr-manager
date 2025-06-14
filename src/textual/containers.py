from .widgets import Widget


class Container(Widget):
    def __init__(self, *children: Widget, id: str | None = None) -> None:
        super().__init__(id=id)
        for child in children:
            self.mount(child)
