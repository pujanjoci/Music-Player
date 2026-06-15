from dataclasses import dataclass
from typing import Optional

@dataclass
class Song:
    """Represents a music track with its metadata and filepath."""
    filepath: str
    title: str
    artist: str = "Unknown Artist"
    album: str = "Unknown Album"
    duration: float = 0.0  # In seconds
    year: Optional[str] = None
    genre: Optional[str] = None
    track_number: Optional[str] = None
    artwork_data: Optional[bytes] = None  # Raw image data from tags
    favorite: bool = False
    play_count: int = 0
    
    @property
    def display_title(self) -> str:
        """Returns the song title, falling back to filepath's base name if empty."""
        if self.title:
            return self.title
        import os
        return os.path.splitext(os.path.basename(self.filepath))[0]
