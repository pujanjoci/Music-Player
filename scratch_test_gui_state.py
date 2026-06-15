import sys
import time
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtMultimedia import QMediaPlayer

logging.basicConfig(level=logging.INFO)

from music_player.database.connection import DbConnection
from music_player.database.repository import MusicRepository
from music_player.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    DbConnection.initialize()
    songs = MusicRepository.get_all_songs()
    if not songs:
        print("No songs found")
        return
        
    win = MainWindow()
    win.show()
    
    # Process initial events
    for _ in range(50):
        app.processEvents()
        time.sleep(0.01)
        
    print(f"Initial play button is_playing: {win.player_controls._is_playing}")
    print(f"Initial play button tooltip: {win.player_controls.btn_play_pause.toolTip()}")
    
    # Play the first song using _play_song
    song = songs[0]
    print(f"\nPlaying song: {song.title}")
    win._play_song(song)
    
    # Process events for 2 seconds to let it load and play
    start = time.time()
    while time.time() - start < 2.0:
        app.processEvents()
        time.sleep(0.01)
        
    print(f"After play, player state: {win.audio_player.get_state()}")
    print(f"After play, player controls is_playing: {win.player_controls._is_playing}")
    print(f"After play, player controls tooltip: {win.player_controls.btn_play_pause.toolTip()}")
    
    # Click play/pause button (which should pause it)
    print("\nClicking Play/Pause button...")
    win.player_controls.btn_play_pause.click()
    
    # Process events for 1 second
    start = time.time()
    while time.time() - start < 1.0:
        app.processEvents()
        time.sleep(0.01)
        
    print(f"After click, player state: {win.audio_player.get_state()}")
    print(f"After click, player controls is_playing: {win.player_controls._is_playing}")
    print(f"After click, player controls tooltip: {win.player_controls.btn_play_pause.toolTip()}")
    
    # Click again (should resume)
    print("\nClicking Play/Pause button again...")
    win.player_controls.btn_play_pause.click()
    
    # Process events for 1 second
    start = time.time()
    while time.time() - start < 1.0:
        app.processEvents()
        time.sleep(0.01)
        
    print(f"After second click, player state: {win.audio_player.get_state()}")
    print(f"After second click, player controls is_playing: {win.player_controls._is_playing}")
    print(f"After second click, player controls tooltip: {win.player_controls.btn_play_pause.toolTip()}")

if __name__ == "__main__":
    main()
