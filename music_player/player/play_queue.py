import random
from enum import Enum
from typing import List, Optional
from music_player.models.song import Song

class RepeatMode(Enum):
    OFF = 0       # Stop after the last song
    ALL = 1       # Loop the entire queue
    ONE = 2       # Loop the current song indefinitely

class PlayQueue:
    """
    Manages the list of songs in the queue, shuffle states, and repeat modes.
    """
    def __init__(self) -> None:
        self._original_songs: List[Song] = []
        self._shuffled_indices: List[int] = []
        self._current_pointer: int = -1  # Index in the active playlist (original or shuffled)
        self._shuffle_enabled: bool = False
        self._repeat_mode: RepeatMode = RepeatMode.OFF

    def clear(self) -> None:
        """Clears the playback queue."""
        self._original_songs = []
        self._shuffled_indices = []
        self._current_pointer = -1

    def set_songs(self, songs: List[Song], start_index: int = 0) -> None:
        """Sets a list of songs as the queue and sets the starting index."""
        self._original_songs = list(songs)
        self._generate_shuffled_indices()
        
        if not self._original_songs:
            self._current_pointer = -1
            return
            
        start_index = max(0, min(len(self._original_songs) - 1, start_index))
        if self._shuffle_enabled:
            # Find the position of the start_index in the shuffled list and make it the current pointer
            if start_index in self._shuffled_indices:
                self._current_pointer = self._shuffled_indices.index(start_index)
        else:
            self._current_pointer = start_index

    def add_song(self, song: Song) -> None:
        """Adds a single song to the end of the queue."""
        self._original_songs.append(song)
        if self._shuffle_enabled:
            # Insert the new index randomly into the shuffled queue
            new_index = len(self._original_songs) - 1
            insert_pos = random.randint(0, len(self._shuffled_indices))
            self._shuffled_indices.insert(insert_pos, new_index)
        else:
            if self._current_pointer == -1:
                self._current_pointer = 0

    def get_current_song(self) -> Optional[Song]:
        """Gets the currently playing song."""
        actual_index = self._get_actual_index()
        if 0 <= actual_index < len(self._original_songs):
            return self._original_songs[actual_index]
        return None

    def next_song(self) -> Optional[Song]:
        """
        Advances the pointer to the next song based on shuffle/repeat settings.
        Returns the next Song, or None if the end is reached and repeat is off.
        """
        if not self._original_songs:
            return None

        # Repeat ONE: Keep the same song
        if self._repeat_mode == RepeatMode.ONE:
            return self.get_current_song()

        total_songs = len(self._original_songs)
        
        # Advance pointer
        self._current_pointer += 1
        
        if self._current_pointer >= total_songs:
            if self._repeat_mode == RepeatMode.ALL:
                self._current_pointer = 0
                if self._shuffle_enabled:
                    # Re-shuffle on repeat all
                    self._generate_shuffled_indices()
            else:
                self._current_pointer = total_songs - 1  # Cap at the end
                return None  # Reached the end of queue

        return self.get_current_song()

    def prev_song(self) -> Optional[Song]:
        """
        Moves the pointer back to the previous song.
        Returns the previous Song, or the current song if already at the start.
        """
        if not self._original_songs:
            return None

        # Repeat ONE: Keep the same song
        if self._repeat_mode == RepeatMode.ONE:
            return self.get_current_song()

        # Retreat pointer
        self._current_pointer -= 1
        
        if self._current_pointer < 0:
            if self._repeat_mode == RepeatMode.ALL:
                self._current_pointer = len(self._original_songs) - 1
            else:
                self._current_pointer = 0  # Stay at the first song

        return self.get_current_song()

    def set_shuffle(self, enabled: bool) -> None:
        """Enables/disables shuffle mode. Translates the current index pointer."""
        if self._shuffle_enabled == enabled:
            return
            
        current_actual_index = self._get_actual_index()
        self._shuffle_enabled = enabled
        
        if not self._original_songs:
            return
            
        if enabled:
            self._generate_shuffled_indices()
            # Bring the currently playing song to the top of the shuffled stack or find its new pointer
            if current_actual_index in self._shuffled_indices:
                # Swap current playing song index to the beginning of list
                idx = self._shuffled_indices.index(current_actual_index)
                self._shuffled_indices[0], self._shuffled_indices[idx] = self._shuffled_indices[idx], self._shuffled_indices[0]
                self._current_pointer = 0
        else:
            # Map back to the original index
            self._current_pointer = current_actual_index

    def is_shuffle_enabled(self) -> bool:
        return self._shuffle_enabled

    def set_repeat_mode(self, mode: RepeatMode) -> None:
        self._repeat_mode = mode

    def get_repeat_mode(self) -> RepeatMode:
        return self._repeat_mode

    def get_songs(self) -> List[Song]:
        """Returns the list of songs in original queue order."""
        return self._original_songs

    def _get_actual_index(self) -> int:
        """Returns the index in the original list."""
        if not self._original_songs:
            return -1
        if self._shuffle_enabled:
            if 0 <= self._current_pointer < len(self._shuffled_indices):
                return self._shuffled_indices[self._current_pointer]
            return -1
        return self._current_pointer

    def _generate_shuffled_indices(self) -> None:
        """Generates a randomized permutation list of original indices."""
        indices = list(range(len(self._original_songs)))
        random.shuffle(indices)
        self._shuffled_indices = indices

    def remove_song(self, filepath: str) -> None:
        """Removes a song from the queue by its filepath and updates pointers."""
        target_idx = -1
        for i, s in enumerate(self._original_songs):
            if s.filepath == filepath:
                target_idx = i
                break
        
        if target_idx == -1:
            return

        current_actual = self._get_actual_index()
        
        # Remove from original list
        self._original_songs.pop(target_idx)
        
        if not self._original_songs:
            self.clear()
            return
            
        # Adjust indices and shuffle map
        if self._shuffle_enabled:
            # Re-generate shuffled indices for the new size
            if current_actual == target_idx:
                # The playing song was deleted
                self._generate_shuffled_indices()
                self._current_pointer = 0 if self._original_songs else -1
            else:
                new_actual = current_actual
                if current_actual > target_idx:
                    new_actual -= 1
                self._generate_shuffled_indices()
                if new_actual in self._shuffled_indices:
                    self._current_pointer = self._shuffled_indices.index(new_actual)
        else:
            if current_actual == target_idx:
                if self._current_pointer >= len(self._original_songs):
                    self._current_pointer = len(self._original_songs) - 1
            elif current_actual > target_idx:
                self._current_pointer -= 1

