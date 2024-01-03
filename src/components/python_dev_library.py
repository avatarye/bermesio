from pathlib import Path


class PythonDevLibrary:
    def __init__(self, library_path):
        self.library_path = Path(library_path)
        if self.library_path.exists():
            self.name = self.library_path.name

    def __eq__(self, other):
        return super().__eq__(other) and self.library_path == other.library_path

    def __hash__(self):
        return hash(self.library_path)
