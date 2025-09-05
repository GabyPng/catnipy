import sys
import time
import threading
import keyboard
import mouse
import sounddevice as sd
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, Qt

class MadTuber(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MadTuber Demo")
        self.setGeometry(200, 200, 300, 300)
        self.setWindowFlags(Qt.FramelessWindowHint)  # Ventana sin bordes
        self.setAttribute(Qt.WA_TranslucentBackground)  # Fondo transparente

        # Crear etiquetas para las imágenes
        self.base_label = QLabel(self)  # Imagen base (gato)
        self.typing_label = QLabel(self)  # Manos para teclado
        self.mouse_label = QLabel(self)  # Manos para ratón
        self.talking_label = QLabel(self)  # Boca para hablar

        # Configurar fondo transparente para los QLabel
        for label in [self.base_label, self.typing_label, self.mouse_label, self.talking_label]:
            label.setStyleSheet("background: transparent;")

        # Posiciones de las imágenes (coordenadas en píxeles)
        self.image_positions = {
            "base": (50, 0, 200, 200),  # (x, y, ancho, alto) - Centrado arriba
            "typing": (0, 200, 100, 100),  # Abajo a la izquierda
            "mouse": (200, 200, 100, 100),  # Abajo a la derecha
            "talking": (100, 100, 100, 100)  # Superpuesta al rostro
        }

        # Aplicar posiciones
        self.base_label.setGeometry(*self.image_positions["base"])
        self.typing_label.setGeometry(*self.image_positions["typing"])
        self.mouse_label.setGeometry(*self.image_positions["mouse"])
        self.talking_label.setGeometry(*self.image_positions["talking"])

        # Estados compartidos
        self.state = {
            "keyboard": False,
            "mouse_click": False,
            "mouse_move": False,
            "talking": False
        }
        self.last_mouse_move = 0
        self.last_mouse_click = 0  # Para rastrear el tiempo del último clic
        self.volume_level = 0.0
        self.threshold = 3.5  # Ajustado para micrófono

        # Cargar imágenes
        self.images = {}
        for key, path in [
            ("base", "cat_idle.png"),
            ("typing", "cat_typing_hands.png"),
            ("mouse", "cat_mouse_hands.png"),
            ("talking", "cat_talking_mouth.png")
        ]:
            try:
                self.images[key] = QPixmap(path)
                if self.images[key].isNull():
                    # print(f"⚠ Imagen {path} no encontrada o inválida")
                    pass
            except Exception as e:
                # print(f"Error cargando {path}: {e}")
                self.images[key] = QPixmap()

        # Timer para refrescar imágenes (60 fps)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_image)
        self.timer.start(1000 // 60)

        # Variables para arrastrar la ventana
        self.dragging = False
        self.drag_position = None

    def update_image(self):
        current_time = time.time()
        if current_time - self.last_mouse_move > 0.2:
            self.state["mouse_move"] = False
        if current_time - self.last_mouse_click > 0.01:  # Resetear clic después de 0.5s
            self.state["mouse_click"] = False

        # Mostrar siempre la imagen base
        if not self.images["base"].isNull():
            self.base_label.setPixmap(self.images["base"].scaled(self.base_label.size(), Qt.KeepAspectRatio))
        # else:
        #     print("⚠ Imagen base no encontrada")

        # Mostrar imágenes de acción según el estado (priorizar mouse_click)
        if (self.state["mouse_click"] or self.state["mouse_move"]) and not self.images["mouse"].isNull():
            self.mouse_label.setPixmap(self.images["mouse"].scaled(self.mouse_label.size(), Qt.KeepAspectRatio))
        else:
            self.mouse_label.clear()

        if self.state["keyboard"] and not self.images["typing"].isNull():
            self.typing_label.setPixmap(self.images["typing"].scaled(self.typing_label.size(), Qt.KeepAspectRatio))
        else:
            self.typing_label.clear()

        if self.state["talking"] and not self.images["talking"].isNull():
            self.talking_label.setPixmap(self.images["talking"].scaled(self.talking_label.size(), Qt.KeepAspectRatio))
        else:
            self.talking_label.clear()

        # # Depuración
        # print(f"Estado actual: keyboard={self.state['keyboard']}, "
        #       f"mouse_click={self.state['mouse_click']}, "
        #       f"mouse_move={self.state['mouse_move']}, "
        #       f"talking={self.state['talking']}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        event.accept()

def start_keyboard_listener(app):
    def on_key(event):
        app.state["keyboard"] = event.event_type == "down"
        # print(f"Keyboard: {event.event_type}, State: {app.state['keyboard']}")
    try:
        keyboard.hook(on_key)
    except Exception as e:
        # print(f"Error en keyboard listener: {e}")
        pass

def start_mouse_listener(app):
    def on_mouse_event(event):
        if isinstance(event, mouse.ButtonEvent):
            app.state["mouse_click"] = event.event_type == "down"
            if event.event_type == "down":
                app.last_mouse_click = time.time()  # Actualizar tiempo del clic
            # print(f"Mouse click: {event.event_type}, State: {app.state['mouse_click']}")
        elif isinstance(event, mouse.MoveEvent):
            app.state["mouse_move"] = True
            app.last_mouse_move = time.time()
            # print(f"Mouse move detected, State: {app.state['mouse_move']}")
    try:
        mouse.hook(on_mouse_event)
    except Exception as e:
        # print(f"Error en mouse listener: {e}")
        pass

def start_mic_listener(app):
    try:
        def audio_callback(indata, frames, time, status):
            if status:
                # print(f"Error en audio: {status}")
                pass
            volume_norm = np.linalg.norm(indata) * 10
            app.volume_level = volume_norm
            app.state["talking"] = volume_norm > app.threshold
            # print(f"Volume: {volume_norm:.2f}, Talking: {app.state['talking']}")
        with sd.InputStream(callback=audio_callback):
            sd.sleep(1000000)
    except Exception as e:
        # print(f"Error iniciando micrófono: {e}")
        pass

if __name__ == "__main__":
    app_qt = QApplication(sys.argv)
    window = MadTuber()
    window.show()

    threading.Thread(target=start_keyboard_listener, args=(window,), daemon=True).start()
    threading.Thread(target=start_mouse_listener, args=(window,), daemon=True).start()
    threading.Thread(target=start_mic_listener, args=(window,), daemon=True).start()

    sys.exit(app_qt.exec_())