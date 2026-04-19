"""
main.py
Entry point — run with:  python main.py
"""

import sys
import os

# Add the project root to sys.path so that flat imports (e.g. `from constants import`)
# resolve correctly when running main.py directly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
