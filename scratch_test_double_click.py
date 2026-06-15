import sys
import time
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QModelIndex

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])

from music_player.database.connection import DbConnection
from music_player.database.repository import MusicRepository
from music_player.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    DbConnection.initialize()
    songs = MusicRepository.get_all_songs()
    if not songs:
        print("No songs found in database. Scan first.")
        return
        
    print(f"Loaded {len(songs)} songs.")
    
    win = MainWindow()
    win.show()
    
    # Wait for UI to initialize
    for _ in range(50):
        app.processEvents()
        time.sleep(0.01)
        
    table = win.song_list.table_widget
    if table.rowCount() == 0:
        print("No rows in table view.")
        return
        
    print("Simulating double click on row 0...")
    table.setCurrentCell(0, 0)
    table.selectRow(0)
    model_idx = table.model().index(0, 0)
    table.doubleClicked.emit(model_idx)
    
    # Monitor for 4 seconds
    start = time.time()
    while time.time() - start < 4.0:
        app.processEvents()
        time.sleep(0.01)
        
    print("Finished simulation.")

if __name__ == "__main__":
    main()
