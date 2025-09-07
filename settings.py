import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel
from PyQt5.QtGui import QPixmap, QPainter, QCursor, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect

# Rutas de imágenes
SETTINGS_BG = "./assets/gui/catnipy_gui__settings.png"
SETTINGS_EXIT = "./assets/gui/catnipy_gui__settings_exit.png"
SETTINGS_SELECTOR = "./assets/gui/catnipy_gui__settings_selector.png"

# Configuración por defecto
DEFAULT_CONFIG = {
    "volumen_umbral": 0.005,  # Sensibilidad del micrófono
    "mouse_sensibilidad": 0.1  # Sensibilidad del movimiento del mouse
}

# Archivo de configuración
CONFIG_FILE = "./config.json"

class SettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Variables para el arrastre de la ventana
        self.dragging = None
        self.window_drag_position = None
        
        # Cargar o crear configuración
        self.config = self.load_config()
        
        # Inicializar UI
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("CatNipy Settings")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Cargar imágenes
        self.bg_pixmap = QPixmap(SETTINGS_BG)
        self.exit_pixmap = QPixmap(SETTINGS_EXIT)
        self.selector_pixmap = QPixmap(SETTINGS_SELECTOR)
        
        # Verificar que las imágenes se cargaron correctamente
        if self.bg_pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen {SETTINGS_BG}")
        else:
            print(f"Imagen cargada con éxito: {SETTINGS_BG}")
            
        if self.exit_pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen {SETTINGS_EXIT}")
        else:
            print(f"Imagen cargada con éxito: {SETTINGS_EXIT}")
            
        if self.selector_pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen {SETTINGS_SELECTOR}")
        else:
            print(f"Imagen cargada con éxito: {SETTINGS_SELECTOR}")
        
        # Configurar tamaño de la ventana basado en la imagen de fondo
        self.resize(self.bg_pixmap.size())
        
        # Crear botón de salida
        self.exit_button = QPushButton(self)
        self.exit_button.setIcon(QIcon(self.exit_pixmap))
        
        # Hacer el botón más grande para que las líneas no queden tan delgadas (ajustar al 60% del original)
        exit_width = int(self.exit_pixmap.width() *.90)
        exit_height = int(self.exit_pixmap.height() *.90)
        self.exit_button.setIconSize(QPixmap(self.exit_pixmap).scaled(exit_width, exit_height).size())
        
        # Posicionar el botón en la parte inferior central
        self.exit_button.setGeometry(
            (self.width() - exit_width) // 2,  # Centrado horizontalmente
            self.height() - exit_height, 
            exit_width,
            exit_height
        )
        self.exit_button.setFlat(True)
        self.exit_button.setToolTip("Guardar y salir")
        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 50);
                border-radius: 5px;
            }
        """)
        self.exit_button.clicked.connect(self.save_and_close)
        
        # Configurar posiciones de las barras y selectores
        # Posiciones para las barras de ajuste (definidas según el diseño de la imagen)
        self.bar_width = 250
        self.bar_height = 20
        
        # Posición Y de cada barra (ajustar según el diseño)
        self.mic_bar_y = 145
        self.mouse_bar_y = 220  # Posición más alta para el selector de mouse
        
        # Posición X común para ambas barras
        self.bar_x = (self.width() - self.bar_width) // 2
        
        # Inicializar posiciones de los selectores basado en los valores actuales
        self.mic_selector_pos = self.value_to_position(self.config["volumen_umbral"], 0.001, 0.02)
        self.mouse_selector_pos = self.value_to_position(self.config["mouse_sensibilidad"], 0.05, 0.5)
        
        # Variables para seguimiento de arrastre
        self.dragging = None  # 'mic' o 'mouse' o None
        self.dragging_offset = 0
        
        # Centrar la ventana en la pantalla
        self.center()
    
    def center(self):
        """Centra la ventana en la pantalla"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    def load_config(self):
        """Carga la configuración desde un archivo o usa los valores predeterminados"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Asegurar que todas las claves necesarias estén presentes
                    for key in DEFAULT_CONFIG:
                        if key not in config:
                            config[key] = DEFAULT_CONFIG[key]
                    return config
        except Exception as e:
            print(f"Error al cargar la configuración: {e}")
        
        return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """Guarda la configuración actual en un archivo"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
            print("Configuración guardada con éxito")
            return True
        except Exception as e:
            print(f"Error al guardar la configuración: {e}")
            return False
    
    def save_and_close(self):
        """Guarda la configuración y cierra la ventana"""
        if self.save_config():
            print("Configuración guardada al cerrar")
            self.close()
    
    def value_to_position(self, value, min_value, max_value):
        """Convierte un valor en una posición X para el selector"""
        ratio = (value - min_value) / (max_value - min_value)
        return int(self.bar_x + ratio * self.bar_width)
    
    def position_to_value(self, position, min_value, max_value):
        """Convierte una posición X en un valor"""
        ratio = max(0, min(1, (position - self.bar_x) / self.bar_width))
        return min_value + ratio * (max_value - min_value)
    
    def paintEvent(self, event):
        """Dibuja el fondo y los elementos de la interfaz"""
        painter = QPainter(self)
        
        # Dibujar fondo
        painter.drawPixmap(0, 0, self.bg_pixmap)
    
        
        # Dibujar selectores
        painter.drawPixmap(
            self.mic_selector_pos - self.selector_pixmap.width() // 2,
            self.mic_bar_y - self.selector_pixmap.height() // 2,
            self.selector_pixmap
        )
        
        painter.drawPixmap(
            self.mouse_selector_pos - self.selector_pixmap.width() // 2,
            self.mouse_bar_y - self.selector_pixmap.height() // 2,
            self.selector_pixmap
        )
        
        # Dibujar valores actuales
        painter.setPen(Qt.white)
        mic_value = self.config["volumen_umbral"]
        mouse_value = self.config["mouse_sensibilidad"]
        
        # Formatear con 4 decimales para micrófono y 2 para mouse
        painter.drawText(
            self.bar_x + self.bar_width + 5,
            self.mic_bar_y + 5,
            f"{mic_value:.3f}"
        )
        
        painter.drawText(
            self.bar_x + self.bar_width + 5,
            self.mouse_bar_y + 5,
            f"{mouse_value:.1f}"
        )
        
        # Dibujar etiquetas
        painter.drawText(
            self.bar_x - 120,
            self.mic_bar_y + 5,
            "Audio:"
        )
        
        painter.drawText(
            self.bar_x - 120,
            self.mouse_bar_y + 5,
            "Mouse:"
        )
    
    def mousePressEvent(self, event):
        """Maneja el evento de presionar el mouse"""
        if event.button() == Qt.LeftButton:
            # Verificar si el clic está en el área del selector de micrófono
            mic_rect = QRect(
                self.mic_selector_pos - self.selector_pixmap.width() // 2,
                self.mic_bar_y - self.selector_pixmap.height() // 2,
                self.selector_pixmap.width(),
                self.selector_pixmap.height()
            )
            
            # Verificar si el clic está en el área del selector de mouse
            mouse_rect = QRect(
                self.mouse_selector_pos - self.selector_pixmap.width() // 2,
                self.mouse_bar_y - self.selector_pixmap.height() // 2,
                self.selector_pixmap.width(),
                self.selector_pixmap.height()
            )
            
            if mic_rect.contains(event.pos()):
                self.dragging = 'mic'
                self.dragging_offset = event.pos().x() - self.mic_selector_pos
            elif mouse_rect.contains(event.pos()):
                self.dragging = 'mouse'
                self.dragging_offset = event.pos().x() - self.mouse_selector_pos
            # Para permitir arrastrar la ventana cuando se hace clic en cualquier otra parte
            elif not (self.bar_x <= event.pos().x() <= self.bar_x + self.bar_width and 
                    (abs(event.pos().y() - self.mic_bar_y) < 20 or abs(event.pos().y() - self.mouse_bar_y) < 20)):
                self.dragging = 'window'
                self.window_drag_position = event.globalPos() - self.frameGeometry().topLeft()
            
            # También permitir hacer clic directamente en la barra
            if self.bar_x <= event.pos().x() <= self.bar_x + self.bar_width:
                # Si el clic está cerca de la barra de micrófono
                if abs(event.pos().y() - self.mic_bar_y) < 20:
                    self.dragging = 'mic'
                    self.mic_selector_pos = event.pos().x()
                    self.update_mic_value()
                # Si el clic está cerca de la barra de mouse
                elif abs(event.pos().y() - self.mouse_bar_y) < 20:
                    self.dragging = 'mouse'
                    self.mouse_selector_pos = event.pos().x()
                    self.update_mouse_value()
    
    def mouseMoveEvent(self, event):
        """Maneja el evento de mover el mouse"""
        if self.dragging == 'mic':
            # Actualizar posición del selector de micrófono
            new_pos = event.pos().x() - self.dragging_offset
            self.mic_selector_pos = max(self.bar_x, min(self.bar_x + self.bar_width, new_pos))
            self.update_mic_value()
            self.update()
        elif self.dragging == 'mouse':
            # Actualizar posición del selector de mouse
            new_pos = event.pos().x() - self.dragging_offset
            self.mouse_selector_pos = max(self.bar_x, min(self.bar_x + self.bar_width, new_pos))
            self.update_mouse_value()
            self.update()
        elif self.dragging == 'window':
            # Mover la ventana
            self.move(event.globalPos() - self.window_drag_position)
    
    def mouseReleaseEvent(self, event):
        """Maneja el evento de soltar el mouse"""
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = None
    
    def update_mic_value(self):
        """Actualiza el valor de sensibilidad del micrófono basado en la posición del selector"""
        self.config["volumen_umbral"] = self.position_to_value(
            self.mic_selector_pos, 0.001, 0.02
        )
    
    def update_mouse_value(self):
        """Actualiza el valor de sensibilidad del mouse basado en la posición del selector"""
        self.config["mouse_sensibilidad"] = self.position_to_value(
            self.mouse_selector_pos, 0.05, 0.5
        )
    
    def closeEvent(self, event):
        """Se llama cuando se cierra la ventana con el botón X o Alt+F4"""
        self.save_config()
        print("Configuración guardada al cerrar ventana")
        event.accept()
        
    def keyPressEvent(self, event):
        """Captura eventos de teclado"""
        if event.key() == Qt.Key_Escape:
            self.save_and_close()
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def activateWindow(self):
        """Asegura que la ventana está activa y en primer plano"""
        super().activateWindow()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.raise_()

def open_settings():
    """Abre la ventana de configuración"""
    app = QApplication.instance()
    if not app:  # Si no hay una instancia de QApplication, crear una
        app = QApplication(sys.argv)
    
    settings_window = SettingsWindow()
    settings_window.show()
    settings_window.activateWindow()  # Asegurar que la ventana está activa
    settings_window.raise_()  # Traer la ventana al frente
    
    # No ejecutamos app.exec_() aquí, ya que el ciclo de eventos ya está en ejecución
    # Solo devolvemos la ventana para que el llamador pueda mantener una referencia
    return settings_window

if __name__ == "__main__":
    # Si se ejecuta directamente este archivo
    app = QApplication(sys.argv)
    settings_window = SettingsWindow()
    settings_window.show()
    sys.exit(app.exec_())
