import logging
from PySide6.QtCore import QThread, Signal
from music_player.services.metadata import MetadataService

logger = logging.getLogger(__name__)

class ArtworkLoader(QThread):
    """
    Background worker thread to load album art data asynchronously.
    """
    artwork_loaded = Signal(bytes, str)  # Emits (artwork_data, filepath)

    def __init__(self, filepath: str) -> None:
        super().__init__()
        self.filepath = filepath

    def run(self) -> None:
        try:
            logger.info(f"Extracting artwork in background for: {self.filepath}")
            song = MetadataService.extract_metadata(self.filepath)
            # Emit the artwork data (or empty bytes if none found) and the associated filepath
            self.artwork_loaded.emit(song.artwork_data or b"", self.filepath)
        except Exception as e:
            logger.error(f"Error loading artwork in background thread: {e}")
            self.artwork_loaded.emit(b"", self.filepath)
