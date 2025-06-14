class Pilot:
    def __init__(self, app):
        self.app = app

    async def pause(self):
        # no real async loop
        return None

    async def click(self, selector: str):
        widget = self.app.query_one(selector)
        if hasattr(widget, "click"):
            widget.click()

    async def press(self, key: str):
        # keyboard events ignored in this stub
        return None
