from __future__ import annotations

from typing import Any, List, Type, Iterable

from .css.query import NoMatches


class Query(List["Widget"]):
    def first(self) -> "Widget":
        if not self:
            raise NoMatches("No matches")
        return self[0]


class Widget:
    def __init__(self, id: str | None = None) -> None:
        self.id = id
        self.parent: Widget | None = None
        self.children: List[Widget] = []

    # composition
    def compose(self) -> Iterable[Widget]:
        return []

    def _compose_children(self) -> None:
        for child in self.compose():
            self.mount(child)

    def mount(self, widget: "Widget") -> None:
        widget.parent = self
        widget._compose_children()
        self.children.append(widget)

    def remove(self) -> None:
        if self.parent:
            self.parent.children.remove(self)
            self.parent = None

    def call_after_refresh(self, func) -> None:
        func()

    # query helpers
    def _find_by_id(self, widget_id: str) -> "Widget" | None:
        if self.id == widget_id:
            return self
        for child in self.children:
            result = child._find_by_id(widget_id)
            if result is not None:
                return result
        return None

    def _find_by_type(self, cls: Type[Widget]) -> "Widget" | None:
        if isinstance(self, cls):
            return self
        for child in self.children:
            result = child._find_by_type(cls)
            if result is not None:
                return result
        return None

    def query_one(self, selector: str | Type["Widget"]) -> "Widget":
        if isinstance(selector, str):
            parts = selector.strip().split()
            node: Widget = self
            for part in parts:
                if not part.startswith("#"):
                    raise NoMatches(part)
                node = node._find_by_id(part[1:])
                if node is None:
                    raise NoMatches(part)
            return node
        else:
            result = self._find_by_type(selector)
            if result is None:
                raise NoMatches(str(selector))
            return result

    def query(self, cls: Type["Widget"] | str) -> Query:
        """Return all widgets matching the given class or selector."""
        if isinstance(cls, str):
            parts = cls.strip().split()
            if len(parts) > 1:
                node = self.query_one(parts[0])
                return node.query(" ".join(parts[1:]))
            if cls.startswith("#"):
                widget = self._find_by_id(cls[1:])
                return Query([widget] if widget else [])
            cls_obj = globals().get(cls)
            if isinstance(cls_obj, type):
                cls = cls_obj  # type: ignore
            else:
                raise NoMatches(cls)
        results: List[Widget] = []
        if isinstance(self, cls):
            results.append(self)
        for child in self.children:
            results.extend(child.query(cls))
        return Query(results)


class Static(Widget):
    def __init__(self, renderable: str = "", id: str | None = None) -> None:
        super().__init__(id=id)
        self.renderable = renderable
        self.display = True

    def update(self, text: str) -> None:
        self.renderable = text


class Button(Widget):
    def __init__(self, label: str = "", id: str | None = None) -> None:
        super().__init__(id=id)
        self.label = label

    def click(self) -> None:
        parent = self.parent
        while parent:
            if hasattr(parent, "on_button_pressed"):
                parent.on_button_pressed(type("_Evt", (), {"button": self})())
                break
            parent = parent.parent


class Select(Widget):
    def __init__(self, options: List[tuple[str, Any]] | None = None, id: str | None = None) -> None:
        super().__init__(id=id)
        self._options: List[tuple[str, Any]] = options or []
        self.value: Any | None = None

    @property
    def options(self) -> List[tuple[str, Any]]:
        return self._options

    @options.setter
    def options(self, value: List[tuple[str, Any]]) -> None:
        self._options = value

    def clear(self) -> None:
        self._options = []
        self.value = None


class Input(Widget):
    def __init__(self, value: str = "", placeholder: str = "", id: str | None = None) -> None:
        super().__init__(id=id)
        self.value = value
        self.placeholder = placeholder


class Checkbox(Widget):
    def __init__(self, label: str = "", id: str | None = None) -> None:
        super().__init__(id=id)
        self.label = label
        self.value: bool = False

    def click(self) -> None:
        self.value = not self.value


class Header(Widget):
    pass


class Footer(Widget):
    pass
