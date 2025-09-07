import sounddevice as sd
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject
import numpy as np
import sys
import os
import time
import json
from pynput import keyboard, mouse
from settings import open_settings, CONFIG_FILE, DEFAULT_CONFIG

# Rutas de imágenes
CAT_IDLE = "./assets/motions/cat_idle.png"
CAT_KEYBOARD_IDLE = "./assets/motions/cat_keyboard_idle.png"
CAT_MOUSE_IDLE = "./assets/motions/cat_mouse_idle.png"
CAT_TYPING_HANDUP = "./assets/motions/cat_typing_handup.png"
CAT_TYPING_HANDDOWN = "./assets/motions/cat_typing_handdown.png"
CAT_MOUSE_MOVE = "./assets/motions/cat_mouse_move.png"
CAT_TALKING = "./assets/motions/cat_onlytalking__nomic.png"

# Verificar que los archivos existen
def check_file_exists(filepath):
    if os.path.exists(filepath):
        print(f"Archivo encontrado: {filepath}")
        return True
    else:
        print(f"ADVERTENCIA: Archivo no encontrado: {filepath}")
        return False

# Verificar todas las imágenes
print("Verificando archivos de imágenes...")
check_file_exists(CAT_IDLE)
check_file_exists(CAT_KEYBOARD_IDLE)
check_file_exists(CAT_MOUSE_IDLE)
check_file_exists(CAT_TYPING_HANDUP)
check_file_exists(CAT_TYPING_HANDDOWN)
check_file_exists(CAT_MOUSE_MOVE)
check_file_exists(CAT_TALKING)

# Parámetros para la captura de audio
samplerate = 44100  # Frecuencia de muestreo (Hz)
chunk_size = 1024   # Tamaño del bloque de datos

"""
Configuración técnica del sistema de audio:
    samplerate (int): Frecuencia de muestreo en Hz (44.1 KHz, calidad CD)
    chunk_size (int): Tamaño del buffer de audio por bloque
                      Valor óptimo para equilibrar latencia y rendimiento
                      - Valores bajos: menor latencia pero más carga de CPU
                      - Valores altos: mayor latencia pero menos procesamiento

El sistema utiliza sounddevice para procesar audio en tiempo real
y detectar cuando el usuario está hablando mediante análisis RMS.
"""

# Cargar configuración o usar valores por defecto
def cargar_configuracion():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config
        else:
            # Si no existe el archivo, usar valores por defecto
            return DEFAULT_CONFIG.copy()
    except Exception as e:
        print(f"Error al cargar la configuración: {e}")
        return DEFAULT_CONFIG.copy()

# Obtener configuración
config = cargar_configuracion()
volumen_umbral = config.get("volumen_umbral", 0.005)  # Valor más bajo = más sensible
mouse_sensibilidad = config.get("mouse_sensibilidad", 0.1)  # Sensibilidad del mouse

class CatNipy(QWidget):
    """
    Clase principal que implementa el personaje virtual interactivo.
    
    Arquitectura técnica:
        - Hereda de QWidget para crear una ventana personalizada sin bordes
        - Utiliza un sistema de capas (QLabels) para componer animaciones modulares
        - Implementa monitores globales de teclado/ratón/audio para detectar actividad
        - Gestiona estados múltiples con transiciones visuales
    
    Componentes principales:
        - Sistema de UI: Ventana transparente con múltiples capas visuales
        - Sistema de audio: Monitoreo en tiempo real del micrófono
        - Sistema de eventos: Captura global de teclado y mouse
        - Sistema de estados: Gestión de animaciones y comportamientos
    """
    def __init__(self):
        super().__init__()
        self.dragging = False
        self.drag_position = None
        self.is_talking = False  # Inicializar is_talking para evitar errores
        self.last_mouse_move_time = 0  # Para limitar frecuencia de eventos de mouse
        
        # Inicializar señales para eventos globales
        self.signals = GlobalEventSignals()
        self.setup_signals()
        
        self.init_ui()
        self.init_audio()

    def init_ui(self):
        """
        Inicializa la interfaz de usuario del personaje.
        
        Componentes técnicos:
            - Ventana sin bordes (FramelessWindowHint)
            - Fondo transparente (TranslucentBackground)
            - Sistema de capas para composición de animaciones:
                * base_label: Imagen de fondo del personaje
                * keyboard_label: Capa de animación de teclado
                * mouse_label: Capa de animación de ratón
                * overlay_label: Capa de animación de boca/habla
            
            - Posicionamiento preciso de cada capa para alineación visual
            - Botón de configuración oculto con estilo CSS personalizado
            - Sistema de delegación de eventos para manejar interacciones en todas las capas
        """
        self.setWindowTitle("CatNipy")
        self.setGeometry(1620, 750, 20, 20)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)  # Ventana sin bordes y siempre encima
        self.setAttribute(Qt.WA_TranslucentBackground)  # Fondo transparente
        self.setFocusPolicy(Qt.StrongFocus)  # Permitir que la ventana reciba eventos de teclado
        
        # Usar un layout para organizar las etiquetas superpuestas
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        # Crear labels para mostrar las diferentes capas del personaje
        self.base_label = QLabel(self)          # Imagen base (gato)
        self.keyboard_label = QLabel(self)      # Acción de teclado
        self.mouse_label = QLabel(self)         # Acción de mouse
        self.overlay_label = QLabel(self)       # Boca (hablando)
        
        # Hacer transparente el fondo de las etiquetas
        self.base_label.setAttribute(Qt.WA_TranslucentBackground)
        self.keyboard_label.setAttribute(Qt.WA_TranslucentBackground)
        self.mouse_label.setAttribute(Qt.WA_TranslucentBackground)
        self.overlay_label.setAttribute(Qt.WA_TranslucentBackground)
        
        # Inicializar los monitores globales de eventos de teclado y mouse
        self.init_global_monitors()
        
        # Botón de configuración (inicialmente oculto, se muestra al hacer clic derecho)
        self.settings_button = QPushButton("⚙", self)
        self.settings_button.setFixedSize(30, 30)
        self.settings_button.setStyleSheet("""
            QPushButton { 
                background-color: rgba(0, 0, 0, 150); 
                color: white; 
                border-radius: 15px; 
                font-size: 16px; 
            }
            QPushButton:hover { 
                background-color: rgba(30, 30, 30, 200); 
            }
        """)
        self.settings_button.move(5, 5)  # Posición en la esquina superior izquierda
        self.settings_button.clicked.connect(self.open_settings_window)
        self.settings_button.hide()  # Inicialmente oculto
        
        
        # Cargar todas las imágenes
        print("Cargando imágenes...")
        self.idle_pixmap = QPixmap(CAT_IDLE)
        self.keyboard_idle_pixmap = QPixmap(CAT_KEYBOARD_IDLE)
        self.mouse_idle_pixmap = QPixmap(CAT_MOUSE_IDLE)
        self.typing_handup_pixmap = QPixmap(CAT_TYPING_HANDUP)
        self.typing_handdown_pixmap = QPixmap(CAT_TYPING_HANDDOWN)
        self.mouse_move_pixmap = QPixmap(CAT_MOUSE_MOVE)
        self.overlay_pixmap = QPixmap(CAT_TALKING)
        
        # Verificar que las imágenes se cargaron correctamente
        if self.idle_pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen {CAT_IDLE}")
        else:
            print(f"Imagen cargada con éxito: {CAT_IDLE}")
            
        if self.keyboard_idle_pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen {CAT_KEYBOARD_IDLE}")
        else:
            print(f"Imagen cargada con éxito: {CAT_KEYBOARD_IDLE}")
            
        if self.mouse_idle_pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen {CAT_MOUSE_IDLE}")
        else:
            print(f"Imagen cargada con éxito: {CAT_MOUSE_IDLE}")
            
        if self.typing_handup_pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen {CAT_TYPING_HANDUP}")
        else:
            print(f"Imagen cargada con éxito: {CAT_TYPING_HANDUP}")
            
        if self.typing_handdown_pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen {CAT_TYPING_HANDDOWN}")
        else:
            print(f"Imagen cargada con éxito: {CAT_TYPING_HANDDOWN}")
            
        if self.mouse_move_pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen {CAT_MOUSE_MOVE}")
        else:
            print(f"Imagen cargada con éxito: {CAT_MOUSE_MOVE}")
            
        if self.overlay_pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen {CAT_TALKING}")
        else:
            print(f"Imagen cargada con éxito: {CAT_TALKING}")
        
        # Configurar la imagen base inicial (gato idle)
        self.base_label.setPixmap(self.idle_pixmap)
        self.base_label.resize(self.idle_pixmap.size())
        
        # Configurar las capas de acción (inicialmente vacías)
        self.keyboard_label.resize(self.idle_pixmap.size())
        self.keyboard_label.setPixmap(QPixmap())  # Pixmap vacío
        
        self.mouse_label.resize(self.idle_pixmap.size())
        self.mouse_label.setPixmap(QPixmap())  # Pixmap vacío
        
        # Configurar la capa de superposición (boca)
        self.overlay_label.resize(self.overlay_pixmap.size())
        self.overlay_label.setPixmap(self.overlay_pixmap)
        self.overlay_label.hide()  # Inicialmente oculto
        
        # Posicionar las etiquetas una encima de otra
        self.base_label.move(0, 0)
        self.keyboard_label.move(0, 0)
        self.mouse_label.move(0, 0)
        self.overlay_label.move(0, 0)
        
        # Ajustar el tamaño de la ventana al tamaño de la imagen base
        self.resize(self.idle_pixmap.size())
        
        # Indicadores de estado
        self.estado_actual = "idle"  # Estado inicial
        self.is_typing = False
        self.is_moving_mouse = False

        # Configurar eventos para todos los labels
        for label in [self.base_label, self.keyboard_label, self.mouse_label, self.overlay_label]:
            label.mousePressEvent = self.label_mouse_press
            label.mouseMoveEvent = self.label_mouse_move
            label.mouseReleaseEvent = self.label_mouse_release
            label.mouseDoubleClickEvent = self.label_mouse_double_click
        
    # Métodos de eventos para labels
    def label_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            # Delegar al método del widget principal
            self.mousePressEvent(event)
        elif event.button() == Qt.RightButton:
            # Delegar al método del widget principal para el clic derecho
            self.mousePressEvent(event)
            
    def label_mouse_move(self, event):
        # Delegar el movimiento al widget principal
        self.mouseMoveEvent(event)
            
    def label_mouse_release(self, event):
        if event.button() == Qt.LeftButton:
            # Delegar al método del widget principal
            self.mouseReleaseEvent(event)
            
    def label_mouse_double_click(self, event):
        if event.button() == Qt.LeftButton:
            self.close_app(event)
            
    # Métodos de eventos para el widget principal
    def mousePressEvent(self, event):
        """
        Clic
        Se ejecuta cuando se presiona un botón del mouse sobre la ventana.
        """
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.update_mouse_state("mouse_move")
            event.accept()
        elif event.button() == Qt.RightButton:
            # Abrir configuración directamente con clic derecho
            print("Clic derecho detectado - abriendo configuración")
            self.open_settings_window()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """
        Mover
        Se ejecuta mientras se mueve el mouse con un botón presionado.
        """
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        """
        Soltar
        Se ejecuta cuando se suelta un botón del mouse.
        """
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.update_mouse_state("mouse_idle")
            event.accept()
            
    def mouseDoubleClickEvent(self, event):
        """
        Doble clic
        Se ejecuta cuando se hace doble clic sobre la ventana.
        """
        if event.button() == Qt.LeftButton:
            self.close_app(event)
    
    def keyPressEvent(self, event):
        """
        Se ejecuta cuando se presiona cualquier tecla mientras la ventana tiene foco.
        """
        self.update_keyboard_state("typing_handdown")
        event.accept()
        
    def keyReleaseEvent(self, event):
        """
        Se ejecuta cuando se suelta cualquier tecla.
        """
        self.update_keyboard_state("typing_handup")
        
        # Volver al estado keyboard_idle después de un breve momento
        QTimer.singleShot(500, lambda: self.update_keyboard_state("keyboard_idle"))
        event.accept()
    
    def update_keyboard_state(self, estado):
        """
        Actualiza el estado del teclado independientemente del estado del mouse.
        
        Parámetros técnicos:
            estado (str): Determina el estado visual y comportamiento del teclado
                - "keyboard_idle": Muestra imagen estática de teclado en reposo
                - "typing_handdown": Animación de presionar tecla
                - "typing_handup": Animación de soltar tecla
                - "idle": Oculta completamente la capa del teclado
        
        Implementación:
            1. Actualiza el QLabel correspondiente con la imagen apropiada
            2. Establece el flag is_typing para seguimiento interno
            3. Preserva el estado de habla si está activo
            
        Este método utiliza un sistema de capas independientes que permite
        combinar diferentes estados de teclado, mouse y habla simultáneamente.
        """
        print(f"Cambiando estado de teclado a: {estado}")
        
        # Actualizar estado de teclado
        if estado == "keyboard_idle":
            self.keyboard_label.setPixmap(self.keyboard_idle_pixmap)
            self.is_typing = True
            
        elif estado == "typing_handdown":
            self.keyboard_label.setPixmap(self.typing_handdown_pixmap)
            self.is_typing = True
            
        elif estado == "typing_handup":
            self.keyboard_label.setPixmap(self.typing_handup_pixmap)
            self.is_typing = True
            
        elif estado == "idle":
            self.keyboard_label.setPixmap(QPixmap())  # Ocultar teclado
            self.is_typing = False
            
        # Mantener el estado del habla si está activo
        if self.is_talking:
            self.overlay_label.show()
            
    def update_mouse_state(self, estado):
        """
        Actualiza el estado del mouse independientemente del estado del teclado.
        Estados: "mouse_idle", "mouse_move"
        
        Parámetros técnicos:
            estado (str): Determina el estado visual y comportamiento del mouse
                - "mouse_idle": Muestra imagen estática del mouse en reposo
                - "mouse_move": Muestra imagen de mouse en movimiento
                - "idle": Oculta completamente la capa del mouse
        
        Funcionamiento:
            1. Actualiza el QLabel correspondiente con la imagen apropiada
            2. Establece el flag is_moving_mouse para seguimiento interno
            3. Conserva el estado de habla si está activo
        """
        print(f"Cambiando estado de mouse a: {estado}")
        
        # Actualizar estado de mouse
        if estado == "mouse_idle":
            self.mouse_label.setPixmap(self.mouse_idle_pixmap)
            self.is_moving_mouse = True
            
        elif estado == "mouse_move":
            self.mouse_label.setPixmap(self.mouse_move_pixmap)
            self.is_moving_mouse = True
            
        elif estado == "idle":
            self.mouse_label.setPixmap(QPixmap())  # Ocultar mouse usando un pixmap vacío
            self.is_moving_mouse = False
            
        # Mantener el estado del habla si está activo
        if self.is_talking:
            self.overlay_label.show()
            
    def cambiar_estado(self, nuevo_estado):
        """
        Cambia el estado general del gato.
        Este método es mantenido por compatibilidad, pero se prefiere usar
        update_keyboard_state y update_mouse_state por separado.
        
        Parámetros técnicos:
            nuevo_estado (str): Estado general deseado del personaje
                - "idle": Estado neutral, sin interacciones
                - "keyboard_idle": Teclado en reposo
                - "mouse_idle": Mouse en reposo
                - "typing_handdown"/"typing_handup": Animaciones de escritura
                - "mouse_move": Animación de movimiento del mouse
                
        Funcionamiento:
            1. Actualiza el estado interno del personaje
            2. Delega a métodos específicos para actualizar cada capa visual
            3. Preserva estados de superposición (como hablar)
        """
        print(f"Cambiando estado general: {self.estado_actual} -> {nuevo_estado}")
        
        self.estado_actual = nuevo_estado
        
        if nuevo_estado == "idle":
            self.update_keyboard_state("idle")
            self.update_mouse_state("idle")
            
        elif nuevo_estado == "keyboard_idle":
            self.update_keyboard_state("keyboard_idle")
            
        elif nuevo_estado == "mouse_idle":
            self.update_mouse_state("mouse_idle")
            
        elif nuevo_estado == "typing_handdown":
            self.update_keyboard_state("typing_handdown")
            
        elif nuevo_estado == "typing_handup":
            self.update_keyboard_state("typing_handup")
            
        elif nuevo_estado == "mouse_move":
            self.update_mouse_state("mouse_move")
            
        # Si hay un overlay visible (hablando), mantenerlo
        if hasattr(self, 'is_talking') and self.is_talking:
            self.overlay_label.show()

    def init_audio(self):
        """
        Inicializa el sistema de captura y procesamiento de audio.
        
        Detalles técnicos:
            - Utiliza sounddevice (sd) para captura de audio en tiempo real
            - Configura un stream de entrada con callback asíncrono
            - Implementa manejo de errores con intento alternativo de configuración
            - Parámetros optimizados:
                * samplerate: 44100Hz (calidad CD)
                * blocksize: 1024 muestras (equilibrio entre latencia y rendimiento)
            
            El callback procesa cada bloque de audio para detectar actividad
            vocal mediante análisis RMS (Root Mean Square) comparado con un
            umbral configurable por el usuario.
        """
        # Inicializar stream de audio
        try:
            self.stream = sd.InputStream(
                samplerate=samplerate, 
                blocksize=chunk_size, 
                callback=self.audio_callback
            )
            self.stream.start()
            print("Sistema de audio iniciado correctamente")
        except Exception as e:
            print(f"Error al iniciar el sistema de audio: {e}")
            # Intento alternativo con parámetros diferentes
            try:
                print("Intentando configuración alternativa...")
                self.stream = sd.InputStream(
                    channels=1,
                    samplerate=samplerate, 
                    blocksize=chunk_size, 
                    callback=self.audio_callback
                )
                self.stream.start()
                print("Sistema de audio iniciado con configuración alternativa")
            except Exception as e2:
                print(f"Error en el segundo intento: {e2}")
                print("No se pudo iniciar el sistema de audio")
        
    def audio_callback(self, indata, frames, time, status):
        """
        Callback para procesar cada bloque de audio capturado.
        
        Parámetros técnicos:
            indata (numpy.ndarray): Buffer de audio del micrófono
            frames (int): Número de frames en este bloque
            time (CData): Información de tiempo de la captura
            status (CallbackFlags): Flags de estado/error
        
        Algoritmo:
            1. Calcula el valor RMS (Root Mean Square) del bloque de audio
               RMS = sqrt(mean(x²)) donde x son las muestras de audio
            2. Compara con el umbral configurable (volumen_umbral)
            3. Actualiza la UI en el hilo principal mediante QTimer.singleShot
               para evitar problemas de threading
        
        El uso de numpy permite cálculos vectorizados eficientes para
        el análisis de audio en tiempo real.
        """
        # Calcula la media cuadrática (RMS) del bloque de audio
        volumen = np.sqrt(np.mean(indata**2))
        
        # Compara el volumen con el umbral configurable
        if volumen > volumen_umbral:
            print(f"Volumen detectado: {volumen:.4f}")
            # Usar QTimer.singleShot para ejecutar show_sound en el hilo principal de Qt
            QTimer.singleShot(0, self.show_sound)
        else:
            # Usar QTimer.singleShot para ejecutar show_idle en el hilo principal de Qt
            QTimer.singleShot(0, self.show_idle)
            
    def show_idle(self):
        # Mantener la imagen base y ocultar la superposición
        self.overlay_label.hide()
        self.is_talking = False
        
    def show_sound(self):
        # Mantener la imagen base y mostrar la superposición
        self.overlay_label.show()
        self.is_talking = True
        print("Hablando detectado - overlay visible")
        
    def setup_signals(self):
        """
        Configura las conexiones de señales para eventos globales
        
        Arquitectura de señales:
            Implementa un patrón de comunicación entre hilos usando Qt Signals.
            Las señales son emitidas por los listeners globales (en hilos separados)
            y conectadas a slots en el hilo principal de la UI para:
            
            1. Garantizar thread-safety en la actualización de la UI
            2. Desacoplar la captura de eventos de su procesamiento
            3. Mantener responsabilidad única en cada componente
            
            Conexiones:
            - keyPressSignal → update_keyboard_state("typing_handdown")
            - keyReleaseSignal → handle_key_release() con temporizador
            - mouseClickPressSignal → update_mouse_state("mouse_move")
            - mouseClickReleaseSignal → update_mouse_state("mouse_idle")
            - mouseMoveSignal → handle_mouse_move() con temporizador
        """
        # Conectar señales a manejadores en el hilo principal
        self.signals.keyPressSignal.connect(lambda: self.update_keyboard_state("typing_handdown"))
        self.signals.keyReleaseSignal.connect(lambda: self.handle_key_release())
        self.signals.mouseClickPressSignal.connect(lambda: self.update_mouse_state("mouse_move"))
        self.signals.mouseClickReleaseSignal.connect(lambda: self.update_mouse_state("mouse_idle"))
        self.signals.mouseMoveSignal.connect(lambda: self.handle_mouse_move())
        
    def handle_key_release(self):
        """Manejador para la señal de liberación de tecla"""
        self.update_keyboard_state("typing_handup")
        # Volver al estado keyboard_idle después de un breve momento
        QTimer.singleShot(500, lambda: self.update_keyboard_state("keyboard_idle"))
        
    def handle_mouse_move(self):
        """Manejador para la señal de movimiento del mouse"""
        # Solo actualizar si no estamos arrastrando
        if not self.dragging:
            self.update_mouse_state("mouse_move")
            # Volver al estado mouse_idle después de un breve momento
            QTimer.singleShot(300, lambda: self.update_mouse_state("mouse_idle"))
    
    def open_settings_window(self):
        """
        Abre la ventana de configuración
        
        Implementación técnica:
            1. Reutiliza una instancia existente si ya se creó anteriormente
            2. Crea una nueva instancia de SettingsWindow desde el módulo settings
            3. Programa una recarga de configuración asíncrona mediante QTimer
            
            La recarga asíncrona permite que los cambios en la configuración
            se apliquen correctamente después de cerrar la ventana de configuración,
            evitando condiciones de carrera entre el guardado y la recarga.
        """
        print("Abriendo ventana de configuración...")
        # Guardar una referencia para evitar que se destruya
        if hasattr(self, 'settings_window') and self.settings_window:
            # Si ya existe una ventana, mostrarla de nuevo
            self.settings_window.show()
            self.settings_window.activateWindow()
            self.settings_window.raise_()
        else:
            # Crear una nueva ventana
            self.settings_window = open_settings()
        
        # Programar una recarga de la configuración después de cerrar la ventana
        QTimer.singleShot(500, self.reload_config)
        
    def close_app(self, event):
        self.stream.stop()
        self.stream.close()
        QApplication.quit()
        
    def closeEvent(self, event):
        # Asegurar que el stream se cierre al cerrar la ventana
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        # Detener los monitores globales
        if hasattr(self, 'keyboard_listener') and self.keyboard_listener.running:
            self.keyboard_listener.stop()
        if hasattr(self, 'mouse_listener') and self.mouse_listener.running:
            self.mouse_listener.stop()
            
        event.accept()
        
    def activateWindow(self):
        # Sobrescribir método para asegurar que la ventana permanece encima
        super().activateWindow()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.raise_()
        
    def reload_config(self):
        """
        Recarga la configuración desde el archivo
        
        Detalles técnicos:
            1. Actualiza variables globales para parámetros configurables:
               - volumen_umbral: Sensibilidad de detección de audio
               - mouse_sensibilidad: Frecuencia de respuesta a movimientos
               
            2. Reinicia el temporizador del mouse para aplicar nueva sensibilidad
            
            Utiliza palabra clave 'global' para modificar variables de ámbito global
            definidas fuera de esta clase. Esto permite que los callbacks de audio
            y mouse accedan a los valores actualizados.
        """
        global volumen_umbral, mouse_sensibilidad
        config = cargar_configuracion()
        volumen_umbral = config.get("volumen_umbral", 0.005)
        mouse_sensibilidad = config.get("mouse_sensibilidad", 0.1)
        self.last_mouse_move_time = time.time() - mouse_sensibilidad  # Actualizar tiempo del mouse
        print(f"Configuración actualizada: volumen_umbral={volumen_umbral}, mouse_sensibilidad={mouse_sensibilidad}")
        
    def showEvent(self, event):
        # Se llama cuando la ventana se muestra
        super().showEvent(event)
        self.activateWindow()  # Asegurar que está activa al mostrarse
    
    def init_global_monitors(self):
        """
        Inicializa monitores globales para eventos de teclado y mouse.
        
        Arquitectura técnica:
            Utiliza la biblioteca 'pynput' para monitorear eventos de entrada
            globales a nivel del sistema operativo. Esto permite detectar
            actividad incluso cuando la aplicación no tiene el foco.
            
            Componentes:
            1. keyboard.Listener: Captura eventos de teclado globales
               - on_press: Llamado cuando se presiona cualquier tecla
               - on_release: Llamado cuando se suelta cualquier tecla
               
            2. mouse.Listener: Captura eventos de mouse globales
               - on_move: Llamado cuando se mueve el cursor
               - on_click: Llamado cuando se hace clic con cualquier botón
            
            Los callbacks emiten señales Qt para procesamiento thread-safe
            en el hilo principal de la UI.
        """
        # Inicializar monitor de teclado global
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_global_key_press,
            on_release=self.on_global_key_release)
        self.keyboard_listener.start()
        
        # Inicializar monitor de mouse global
        self.mouse_listener = mouse.Listener(
            on_move=self.on_global_mouse_move,
            on_click=self.on_global_mouse_click)
        self.mouse_listener.start()
        
        print("Monitores globales de teclado y mouse iniciados")
    
    def on_global_key_press(self, key):
        """Manejador para eventos globales de tecla presionada"""
        # Emitir señal para manejar en el hilo principal
        self.signals.keyPressSignal.emit()
        return True  # Permitir que el evento se propague
    
    def on_global_key_release(self, key):
        """Manejador para eventos globales de tecla liberada"""
        # Emitir señal para manejar en el hilo principal
        self.signals.keyReleaseSignal.emit()
        return True  # Permitir que el evento se propague
    
    def on_global_mouse_move(self, x, y):
        """
        Manejador para eventos globales de movimiento del mouse
        
        Parámetros técnicos:
            x, y (int): Coordenadas absolutas del cursor en la pantalla
            
        Algoritmo de limitación de frecuencia:
            Implementa un mecanismo de throttling (limitación de frecuencia)
            para reducir la cantidad de actualizaciones de la UI:
            
            1. Registra timestamp del movimiento actual
            2. Compara con el timestamp del último movimiento procesado
            3. Solo procesa si ha pasado suficiente tiempo (configurable)
            
            Este enfoque reduce significativamente la carga de CPU y
            proporciona animaciones más suaves con múltiples movimientos.
            
        Nota: No se procesan movimientos durante arrastre del personaje.
        """
        # Solo actualizar el estado si no estamos arrastrando
        if self.dragging:
            return True  # No hacer nada especial durante el arrastre de la ventana
        
        # Limitar la frecuencia de actualización para movimientos del mouse
        current_time = time.time()
        if current_time - self.last_mouse_move_time > mouse_sensibilidad:  # Usar sensibilidad configurable
            self.last_mouse_move_time = current_time
            # Emitir señal para manejar en el hilo principal
            self.signals.mouseMoveSignal.emit()
        
        return True  # Permitir que el evento se propague
    
    def on_global_mouse_click(self, x, y, button, pressed):
        """Manejador para eventos globales de clic del mouse"""
        if pressed:
            # Emitir señal para manejar en el hilo principal
            self.signals.mouseClickPressSignal.emit()
        else:
            # Emitir señal para manejar en el hilo principal
            self.signals.mouseClickReleaseSignal.emit()
        return True  # Permitir que el evento se propague

# Clase para manejar señales entre hilos
class GlobalEventSignals(QObject):
    """Clase para enviar señales de eventos globales al hilo principal de Qt"""
    keyPressSignal = pyqtSignal()
    keyReleaseSignal = pyqtSignal()
    mouseClickPressSignal = pyqtSignal()
    mouseClickReleaseSignal = pyqtSignal()
    mouseMoveSignal = pyqtSignal()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    print("Escuchando...")
    
    cat = CatNipy()
    cat.show()
    cat.activateWindow()  # Asegurar que está activa y encima
    
    # Aplicar ambos estados simultáneamente para probar
    QTimer.singleShot(1000, lambda: cat.update_keyboard_state("keyboard_idle"))
    QTimer.singleShot(1000, lambda: cat.update_mouse_state("mouse_idle"))
    
    # Programar una actualización periódica de la configuración
    config_timer = QTimer()
    config_timer.timeout.connect(cat.reload_config)
    config_timer.start(5000)  # Verificar cada 5 segundos por cambios en la configuración
    
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        pass