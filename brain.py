
import sounddevice as sd
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, Qt
import numpy as np
import sys

impath = "./assets/motions/cat_idle.png"

# Parámetros para la captura de audio
samplerate = 44100  # Frecuencia de muestreo (Hz)
chunk_size = 1024   # Tamaño del bloque de datos

# Umbral de volumen para detectar sonido
volumen_umbral = 0.1  # Ajusta este valor según tu micrófono y entorno

class CatNipy(QWidget):
    def __init__(self):
        super().__init__()
        self.dragging = False
        self.drag_position = None
        self.init_ui()
        self.init_audio()

    def init_ui(self):
        self.setWindowTitle("CatNipy")
        self.setGeometry(1620, 750, 20, 20)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)  # Ventana sin bordes y siempre encima
        self.setAttribute(Qt.WA_TranslucentBackground)  # Fondo transparente
        
        # Crear label para mostrar las imágenes
        self.label = QLabel(self)
        
        # Crear un segundo label para la superposición (boca hablando)
        self.overlay_label = QLabel(self)
        
        # Cargar imágenes
        self.idle_pixmap = QPixmap(impath)
        self.overlay_pixmap = QPixmap("./assets/motions/cat_onlytalking.png")  # Nueva imagen de superposición
        
        # Verificar que las imágenes se cargaron correctamente
        if self.idle_pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen {impath}")
        if self.overlay_pixmap.isNull():
            print("Error: No se pudo cargar la imagen cat_onlytalking.png")
        
        # Establecer imagen base inicial
        self.label.setPixmap(self.idle_pixmap)
        self.label.resize(self.idle_pixmap.size())
        
        # Configurar el label de superposición
        self.overlay_label.resize(self.overlay_pixmap.size())
        self.overlay_label.setPixmap(self.overlay_pixmap)
        self.overlay_label.hide()  # Inicialmente oculto
        
        # Posicionar la superposición (ajusta estos valores según tu imagen)
        self.overlay_label.move(0, 0)  # Cambia estos valores para posicionar la boca correctamente
        
        # Ajustar el tamaño de la ventana al tamaño de la imagen base
        self.resize(self.idle_pixmap.size())


        # Conectar doble clic para cerrar
        self.label.mouseDoubleClickEvent = self.close_app
        
    def mousePressEvent(self, event):
        """
        Clic
        Se ejecuta cuando se presiona un botón del mouse sobre la ventana.
        Prepara el sistema de arrastre capturando la posición inicial del clic.
        """
        if event.button() == Qt.LeftButton:
            self.dragging = True  # Activar modo arrastre
            # Calcular la diferencia entre la posición del cursor y la esquina superior izquierda de la ventana
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()  # Confirmar que el evento fue procesado
            
    def mouseMoveEvent(self, event):
        """
        Mover
        Se ejecuta mientras se mueve el mouse con un botón presionado.
        Mueve la ventana siguiendo el cursor del mouse manteniendo la posición relativa inicial.
        """
        if event.buttons() == Qt.LeftButton and self.dragging:
            # Mover la ventana: nueva posición del cursor - offset inicial
            self.move(event.globalPos() - self.drag_position)
            event.accept()  # Confirmar que el evento fue procesado
            
    def mouseReleaseEvent(self, event):
        """
        Soltar
        Se ejecuta cuando se suelta un botón del mouse.
        Termina el modo de arrastre y detiene el movimiento de la ventana.
        """
        if event.button() == Qt.LeftButton:
            self.dragging = False  # Desactivar modo arrastre
            event.accept()  # Confirmar que el evento fue procesado
            
    def mouseDoubleClickEvent(self, event):
        """
        Doble clic
        Se ejecuta cuando se hace doble clic sobre la ventana.
        Cierra la aplicación completamente.
        """
        if event.button() == Qt.LeftButton:
            self.close_app(event)  # Llamar función para cerrar la aplicación
        
    def init_audio(self):
        # Inicializar stream de audio
        self.stream = sd.InputStream(
            samplerate=samplerate, 
            blocksize=chunk_size, 
            callback=self.audio_callback
        )
        self.stream.start()
        
    def audio_callback(self, indata, frames, time, status):
        # Calcula la media cuadrática (RMS) del bloque de audio
        volumen = np.sqrt(np.mean(indata**2))
        
        # Compara el volumen con el umbral
        if volumen > volumen_umbral:
            print(f"Volumen: {volumen:.4f}")
            self.show_sound()  # Mostrar imagen de gato hablando
        else:
            self.show_idle()   # Mostrar imagen de gato idle
            
    def show_idle(self):
        # Mantener la imagen base y ocultar la superposición
        self.overlay_label.hide()
        
    def show_sound(self):
        # Mantener la imagen base y mostrar la superposición
        self.overlay_label.show()
        
    def close_app(self, event):
        self.stream.stop()
        self.stream.close()
        QApplication.quit()
        
    def closeEvent(self, event):
        # Asegurar que el stream se cierre al cerrar la ventana
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    print("Escuchando...")
    
    cat = CatNipy()
    cat.show()
    
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        pass