import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter, QColor, QLinearGradient, QBrush, QPainterPath
from PySide6.QtCore import Qt, QRectF

def main():
    # Make sure we have a QApplication instance
    app = QApplication(sys.argv)
    
    # We want a high-resolution icon (256x256)
    size = 256
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Draw a beautiful background gradient
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, QColor("#6366F1"))  # Indigo
    gradient.setColorAt(1.0, QColor("#4F46E5"))  # Darker Indigo
    
    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(0, 0, size, size, 48, 48)
    
    # Draw double music note in the center
    painter.setBrush(QColor("#FFFFFF"))
    
    # Scale geometry
    s = size / 256.0
    
    # Left note head
    painter.drawEllipse(QRectF(55 * s, 150 * s, 45 * s, 35 * s))
    # Right note head
    painter.drawEllipse(QRectF(135 * s, 130 * s, 45 * s, 35 * s))
    
    # Stems
    painter.drawRect(QRectF(90 * s, 65 * s, 10 * s, 100 * s))
    painter.drawRect(QRectF(170 * s, 45 * s, 10 * s, 100 * s))
    
    # Beam
    beam_path = QPainterPath()
    beam_path.moveTo(90 * s, 65 * s)
    beam_path.lineTo(180 * s, 45 * s)
    beam_path.lineTo(180 * s, 75 * s)
    beam_path.lineTo(90 * s, 95 * s)
    beam_path.closeSubpath()
    painter.drawPath(beam_path)
    
    painter.end()
    
    # Save files
    ico_path = "app_icon.ico"
    png_path = "app_icon.png"
    
    pixmap.save(ico_path, "ICO")
    pixmap.save(png_path, "PNG")
    print(f"Generated {ico_path} and {png_path} successfully!")

if __name__ == "__main__":
    main()
