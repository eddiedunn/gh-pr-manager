print("DEBUG: main.py starting up")
from gh_pr_manager.main import PRManagerApp


if __name__ == "__main__":
    print("DEBUG: PRManagerApp.__init__")
    print("DEBUG: About to run PRManagerApp")
    try:
        PRManagerApp().run()
    except Exception as e:
        print(f"FATAL: Exception in PRManagerApp.run(): {e}")
        import traceback; traceback.print_exc()
    print("DEBUG: PRManagerApp.run() returned")
