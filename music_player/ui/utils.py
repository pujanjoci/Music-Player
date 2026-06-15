import logging
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPainterPath, QPen
from PySide6.QtCore import Qt, QRectF

logger = logging.getLogger(__name__)

def round_pixmap(pixmap: QPixmap, radius: int) -> QPixmap:
    """
    Returns a copy of the given QPixmap cropped with smooth rounded corners.
    """
    if pixmap.isNull():
        return pixmap
    
    rounded = QPixmap(pixmap.size())
    rounded.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    
    path = QPainterPath()
    path.addRoundedRect(0, 0, pixmap.width(), pixmap.height(), radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    
    return rounded

def create_vector_icon(icon_type: str, color_str: str = "#CBD5E1", size: int = 32, extra: int = 0) -> QIcon:
    """
    Draws custom clean vector icons using QPainter.
    Avoids outdated standard system icons.
    
    icon_type: 'heart_filled', 'heart_outline', 'play', 'pause', 'stop', 'prev', 'next',
               'shuffle', 'repeat', 'volume_mute', 'volume_low', 'volume_medium', 'volume_high',
               'folder', 'cd'
    extra: Used for states (e.g. shuffle enabled, repeat mode index, volume level)
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Scale coordinates to fit the target size (base is 32x32)
    s = size / 32.0
    
    color = QColor(color_str)
    
    if icon_type == "heart_filled":
        # Draw filled red heart
        path = QPainterPath()
        path.moveTo(16 * s, 10 * s)
        path.cubicTo(12 * s, 5 * s, 5 * s, 6 * s, 5 * s, 14 * s)
        path.cubicTo(5 * s, 21 * s, 12 * s, 25 * s, 16 * s, 28 * s)
        path.cubicTo(16 * s, 28 * s, 20 * s, 25 * s, 27 * s, 14 * s)
        path.cubicTo(27 * s, 6 * s, 20 * s, 5 * s, 16 * s, 10 * s)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#EF4444")) # Vibrant Rose Red
        painter.drawPath(path)
        
    elif icon_type == "heart_outline":
        # Draw outline heart
        path = QPainterPath()
        path.moveTo(16 * s, 10 * s)
        path.cubicTo(12 * s, 5 * s, 5 * s, 6 * s, 5 * s, 14 * s)
        path.cubicTo(5 * s, 21 * s, 12 * s, 25 * s, 16 * s, 28 * s)
        path.cubicTo(16 * s, 28 * s, 20 * s, 25 * s, 27 * s, 14 * s)
        path.cubicTo(27 * s, 6 * s, 20 * s, 5 * s, 16 * s, 10 * s)
        
        pen = QPen(color, 2.0 * s, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        
    elif icon_type == "play":
        # Play Triangle
        path = QPainterPath()
        path.moveTo(11 * s, 8 * s)
        path.lineTo(25 * s, 16 * s)
        path.lineTo(11 * s, 24 * s)
        path.closeSubpath()
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPath(path)
        
    elif icon_type == "pause":
        # Pause dual bars
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(QRectF(10 * s, 8 * s, 4 * s, 16 * s), 1.5 * s, 1.5 * s)
        painter.drawRoundedRect(QRectF(18 * s, 8 * s, 4 * s, 16 * s), 1.5 * s, 1.5 * s)
        
    elif icon_type == "stop":
        # Stop Square
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(QRectF(9 * s, 9 * s, 14 * s, 14 * s), 2.0 * s, 2.0 * s)
        
    elif icon_type == "prev":
        # Skip backward
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        # Vertical bar
        painter.drawRoundedRect(QRectF(8 * s, 9 * s, 3 * s, 14 * s), 1.0 * s, 1.0 * s)
        # Left-pointing triangle
        path = QPainterPath()
        path.moveTo(24 * s, 9 * s)
        path.lineTo(12 * s, 16 * s)
        path.lineTo(24 * s, 23 * s)
        path.closeSubpath()
        painter.drawPath(path)
        
    elif icon_type == "next":
        # Skip forward
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        # Right-pointing triangle
        path = QPainterPath()
        path.moveTo(8 * s, 9 * s)
        path.lineTo(20 * s, 16 * s)
        path.lineTo(8 * s, 23 * s)
        path.closeSubpath()
        painter.drawPath(path)
        # Vertical bar
        painter.drawRoundedRect(QRectF(21 * s, 9 * s, 3 * s, 14 * s), 1.0 * s, 1.0 * s)
        
    elif icon_type == "shuffle":
        # Shuffle crossover arrows
        is_enabled = bool(extra)
        pen_color = QColor("#6366F1") if is_enabled else color
        pen = QPen(pen_color, 2.0 * s, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Draw crossovers
        painter.drawLine(6 * s, 8 * s, 12 * s, 8 * s)
        painter.drawLine(12 * s, 8 * s, 20 * s, 24 * s)
        painter.drawLine(20 * s, 24 * s, 26 * s, 24 * s)
        
        painter.drawLine(6 * s, 24 * s, 12 * s, 24 * s)
        painter.drawLine(12 * s, 24 * s, 20 * s, 8 * s)
        painter.drawLine(20 * s, 8 * s, 26 * s, 8 * s)
        
        # Arrow heads
        painter.drawLine(22 * s, 21 * s, 26 * s, 24 * s)
        painter.drawLine(22 * s, 27 * s, 26 * s, 24 * s)
        
        painter.drawLine(22 * s, 5 * s, 26 * s, 8 * s)
        painter.drawLine(22 * s, 11 * s, 26 * s, 8 * s)
        
    elif icon_type == "repeat":
        # Repeat circular loop
        repeat_mode = extra # 0 = OFF, 1 = ALL, 2 = ONE
        is_active = repeat_mode != 0
        pen_color = QColor("#6366F1") if is_active else color
        pen = QPen(pen_color, 2.0 * s, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Circular arc
        painter.drawArc(QRectF(8 * s, 8 * s, 16 * s, 16 * s), int(45 * 16), int(270 * 16))
        
        # Arrow head
        painter.drawLine(20 * s, 10 * s, 24 * s, 6 * s)
        painter.drawLine(24 * s, 6 * s, 24 * s, 12 * s)
        
        if repeat_mode == 2: # Repeat ONE: draw '1' in center
            font = painter.font()
            font.setPointSize(int(7 * s))
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(pen_color)
            painter.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "1")
            
    elif icon_type.startswith("volume"):
        # Speaker Icon
        pen = QPen(color, 2.0 * s, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(color)
        
        # Speaker body
        path = QPainterPath()
        path.moveTo(6 * s, 12 * s)
        path.lineTo(11 * s, 12 * s)
        path.lineTo(16 * s, 7 * s)
        path.lineTo(16 * s, 25 * s)
        path.lineTo(11 * s, 20 * s)
        path.lineTo(6 * s, 20 * s)
        path.closeSubpath()
        painter.drawPath(path)
        
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        if icon_type == "volume_mute":
            # Draw X next to speaker
            painter.drawLine(21 * s, 13 * s, 27 * s, 19 * s)
            painter.drawLine(27 * s, 13 * s, 21 * s, 19 * s)
        else:
            # Low, Medium, High waves
            # Wave 1 (Low, Medium, High)
            painter.drawArc(QRectF(11 * s, 11 * s, 10 * s, 10 * s), int(-40 * 16), int(80 * 16))
            if icon_type in ("volume_medium", "volume_high"):
                # Wave 2
                painter.drawArc(QRectF(9 * s, 8 * s, 16 * s, 16 * s), int(-40 * 16), int(80 * 16))
            if icon_type == "volume_high":
                # Wave 3
                painter.drawArc(QRectF(7 * s, 5 * s, 22 * s, 22 * s), int(-40 * 16), int(80 * 16))
                
    elif icon_type == "folder":
        # Folder Icon
        pen = QPen(color, 2.0 * s, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        path = QPainterPath()
        path.moveTo(4 * s, 26 * s)
        path.lineTo(4 * s, 8 * s)
        path.lineTo(11 * s, 8 * s)
        path.lineTo(14 * s, 11 * s)
        path.lineTo(28 * s, 11 * s)
        path.lineTo(28 * s, 26 * s)
        path.closeSubpath()
        painter.drawPath(path)
        
    elif icon_type == "cd":
        # CD/Library Icon
        pen = QPen(color, 2.0 * s, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Outer circle
        painter.drawEllipse(QRectF(6 * s, 6 * s, 20 * s, 20 * s))
        # Inner circle
        painter.drawEllipse(QRectF(13 * s, 13 * s, 6 * s, 6 * s))

    elif icon_type == "artist":
        # User/Artist Icon
        pen = QPen(color, 2.0 * s, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        # Head
        painter.drawEllipse(QRectF(12 * s, 6 * s, 8 * s, 8 * s))
        # Shoulders
        painter.drawArc(QRectF(6 * s, 16 * s, 20 * s, 16 * s), 0, int(180 * 16))

    elif icon_type == "genre":
        # Slider/Equalizer/Genre Icon
        pen = QPen(color, 2.0 * s, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        # Horizontal lines
        painter.drawLine(6 * s, 10 * s, 26 * s, 10 * s)
        painter.drawLine(6 * s, 16 * s, 26 * s, 16 * s)
        painter.drawLine(6 * s, 22 * s, 26 * s, 22 * s)
        # slider knobs
        painter.setBrush(color)
        painter.drawEllipse(QRectF(11 * s, 8 * s, 4 * s, 4 * s))
        painter.drawEllipse(QRectF(20 * s, 14 * s, 4 * s, 4 * s))
        painter.drawEllipse(QRectF(14 * s, 20 * s, 4 * s, 4 * s))

    elif icon_type == "refresh":
        # Circular refresh arrow
        pen = QPen(color, 2.0 * s, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        # Circular arc from 45 degrees to 315 degrees (bounding rect 8, 8, 16, 16)
        painter.drawArc(QRectF(8 * s, 8 * s, 16 * s, 16 * s), int(45 * 16), int(270 * 16))
        # Arrow head pointing clockwise (at x=20, y=10)
        painter.drawLine(20 * s, 10 * s, 24 * s, 6 * s)
        painter.drawLine(24 * s, 6 * s, 24 * s, 12 * s)
        
    painter.end()
    return QIcon(pixmap)

def get_track_placeholder_art(title: str, size: int = 32) -> QPixmap:
    """
    Generates a solid rounded placeholder image with a color derived from a hash of the title.
    """
    h = abs(hash(title)) % 360
    # HSL color: hue=h, saturation=110, lightness=110 for a muted, premium look
    color = QColor.fromHsl(h, 110, 110)
    
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    # Draw small rounded rect
    painter.drawRoundedRect(0, 0, size, size, 6, 6)
    
    # Draw a subtle musical note in the center
    painter.setPen(QColor(255, 255, 255, 120))
    font = painter.font()
    font.setPointSize(int(size * 0.45))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "♪")
    
    painter.end()
    return pixmap
