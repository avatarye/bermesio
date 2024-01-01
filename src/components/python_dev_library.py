from pathlib import Path


class PythonDevLibrary:
    def __init__(self, library_path):
        self.library_path = Path(library_path)
        if self.library_path.exists():
            self.name = self.library_path.name
