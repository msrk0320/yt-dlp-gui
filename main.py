import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

def get_bundle_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)

def find_binary(name):
    bundle = get_bundle_path()
    local = os.path.join(bundle, name)
    if os.path.isfile(local):
        return local
    for path in os.environ.get("PATH", "").split(os.pathsep):
        full = os.path.join(path, name)
        if os.path.isfile(full):
            return full
    return None

os.environ["PATH"] = os.pathsep.join([
    get_bundle_path(),
    os.environ.get("PATH", ""),
])

from ui.main_window import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
