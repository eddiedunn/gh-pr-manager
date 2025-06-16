from textual.app import App
from textual.widgets import Static

class MinimalApp(App):
    def compose(self):
        yield Static("If you see this, Textual is working!")

if __name__ == "__main__":
    MinimalApp().run()
