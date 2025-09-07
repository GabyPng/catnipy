import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel
from PyQt5.QtGui import QPixmap, QPainter, QCursor, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect

# Obtener la ruta del directorio donde se encuentra el script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Rutas de imágenes (ahora con rutas absolutas)
SETTINGS_BG = os.path.join(script_dir, "assets/gui/catnipy_gui__settings.png")
SETTINGS_EXIT = os.path.join(script_dir, "assets/gui/catnipy_gui__settings_exit.png")
SETTINGS_SELECTOR = os.path.join(script_dir, "assets/gui/catnipy_gui__settings_selector.png")

"""
Constantes técnicas para la interfaz de configuración:
    - SETTINGS_BG: Imagen de fondo para la ventana de configuración
    - SETTINGS_EXIT: Botón para guardar y salir de la configuración
    - SETTINGS_SELECTOR: Control deslizante para ajustar parámetros
    
La interfaz utiliza imágenes personalizadas en lugar de widgets estándar 
para mantener una estética coherente con el personaje principal.
"""

# Configuración por defecto
DEFAULT_CONFIG = {
    "volumen_umbral": 0.005,  # Sensibilidad del micrófono
    "mouse_sensibilidad": 0.1  # Sensibilidad del movimiento del mouse
}

"""
Parámetros de configuración por defecto:
    - volumen_umbral: Umbral RMS para detección de audio (0.005)
      * Valores más bajos aumentan sensibilidad (detecta sonidos más suaves)
      * Rango efectivo: 0.001 - 0.02
      
    - mouse_sensibilidad: Intervalo mínimo entre actualizaciones de mouse (0.1s)
      * Valores más bajos = animación más fluida pero más uso de CPU
      * Valores más altos = animación menos reactiva pero menor uso de CPU
      * Rango efectivo: 0.05 - 0.5 segundos
"""

# Archivo de configuración
CONFIG_FILE = os.path.join(script_dir, "config.json")

class SettingsWindow(QWidget):
    """
    Ventana de configuración para CatNipy.
    
    Arquitectura técnica:
        - Hereda de QWidget para crear una ventana personalizada
        - Implementa interfaz gráfica con imágenes personalizadas
        - Utiliza QPainter para renderizado personalizado
        - Controles deslizantes interactivos para ajustar parámetros
        - Persistencia de configuración mediante archivos JSON
    
    Componentes principales:
        - Controles deslizantes para volumen y sensibilidad del mouse
        - Sistema de arrastre personalizado para controles y ventana
        - Guardado automático de configuración al cerrar
        - Visualización numérica de los valores actuales
    """
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
        """
        Inicializa la interfaz de usuario de la ventana de configuración
        
        Detalles técnicos:
            1. Configuración de ventana:
               - FramelessWindowHint: Elimina bordes estándar del sistema
               - WindowStaysOnTopHint: Mantiene ventana siempre visible
               - TranslucentBackground: Permite transparencia y formas personalizadas
               
            2. Carga de recursos gráficos:
               - Imágenes para fondo, botón de salida y selectores
               - Verificación de carga correcta y mensajes de diagnóstico
               
            3. Configuración de controles:
               - Botón de salida con estilo CSS personalizado
               - Posicionamiento preciso de barras de configuración
               - Cálculo inicial de posiciones de selectores basado en valores actuales
               
            4. Sistema de interacción:
               - Variables para seguimiento de arrastre de controles
               - Centrado automático en pantalla
        """
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
        
        # Posicionar el botón en la parte inferior central, pero un poco más arriba
        self.exit_button.setGeometry(
            (self.width() - exit_width) // 2,  # Centrado horizontalmente
            self.height() - exit_height - 20,  # 30 píxeles más arriba 
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
        self.mic_bar_y = 125
        self.mouse_bar_y = 200  # Posición más alta para el selector de mouse
        
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
        """
        Carga la configuración desde un archivo o usa los valores predeterminados
        
        Implementación técnica:
            1. Intenta abrir y leer el archivo JSON de configuración
            2. Verifica que todas las claves necesarias estén presentes
            3. Aplica valores predeterminados para claves faltantes
            4. Manejo de excepciones para fallas de archivo o formato
            
        Retorna:
            dict: Diccionario con la configuración completa y válida
        """
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
        """
        Convierte un valor en una posición X para el selector
        
        Algoritmo de conversión:
            1. Calcula la proporción normalizada del valor en su rango:
               ratio = (value - min_value) / (max_value - min_value)
            2. Interpola linealmente esta proporción al rango de pixeles de la barra:
               position = bar_x + ratio * bar_width
            
        Parámetros:
            value (float): Valor actual del parámetro
            min_value (float): Valor mínimo del rango
            max_value (float): Valor máximo del rango
            
        Retorna:
            int: Posición X en píxeles para el selector
        """
        ratio = (value - min_value) / (max_value - min_value)
        return int(self.bar_x + ratio * self.bar_width)
    
    def position_to_value(self, position, min_value, max_value):
        """
        Convierte una posición X en un valor
        
        Algoritmo de conversión:
            1. Calcula la proporción normalizada de la posición en la barra:
               ratio = (position - bar_x) / bar_width
            2. Limita el ratio al rango [0,1] para evitar valores fuera de rango
            3. Interpola linealmente esta proporción al rango de valores:
               value = min_value + ratio * (max_value - min_value)
            
        Parámetros:
            position (int): Posición X en píxeles
            min_value (float): Valor mínimo del rango
            max_value (float): Valor máximo del rango
            
        Retorna:
            float: Valor calculado según la posición
        """
        ratio = max(0, min(1, (position - self.bar_x) / self.bar_width))
        return min_value + ratio * (max_value - min_value)
    
    def paintEvent(self, event):
        """
        Dibuja el fondo y los elementos de la interfaz
        
        Detalles técnicos de renderizado:
            Utiliza QPainter para dibujar los elementos visuales en cada frame:
            
            1. Fondo: Imagen completa como base visual
            
            2. Selectores: Controles deslizantes posicionados según valores actuales
               - Centrados vertical y horizontalmente en su posición calculada
               - Posicionamiento preciso mediante cálculo de offsets
            
            3. Valores numéricos: Representación textual de los valores actuales
               - Formateo específico para cada tipo de valor (3 y 1 decimales)
               - Posicionados a la derecha de cada barra
            
            4. Etiquetas: Textos descriptivos para cada parámetro
               - Posicionados a la izquierda de cada barra
               
        Este método es llamado automáticamente por Qt cuando:
        - La ventana es mostrada por primera vez
        - La ventana es redimensionada
        - Se llama explícitamente a self.update() o self.repaint()
        """
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
        """
        Maneja el evento de presionar el mouse
        
        Detalles técnicos:
            Implementa un sistema de detección y manejo de interacciones
            que determina qué elemento está siendo interactuado:
            
            1. Detección de área de interacción:
               - Crea rectángulos virtuales (QRect) alrededor de cada selector
               - Verifica si la posición del clic está dentro de estos rectángulos
               
            2. Modos de interacción:
               - 'mic': Arrastrando el selector de micrófono
               - 'mouse': Arrastrando el selector de sensibilidad del mouse
               - 'window': Arrastrando la ventana completa
               
            3. Interacción directa con barras:
               - Permite clic directo en cualquier punto de la barra
               - Mueve inmediatamente el selector a esa posición
               - Actualiza el valor correspondiente
               
            El offset de arrastre permite mantener la posición relativa
            del cursor dentro del selector durante todo el arrastre.
        """
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
        """
        Maneja el evento de mover el mouse
        
        Implementación técnica:
            Procesa el movimiento según el modo de interacción activo:
            
            1. Modo 'mic': Actualización del selector de micrófono
               - Calcula nueva posición basada en movimiento + offset
               - Restringe posición al rango válido de la barra (clamp)
               - Actualiza valor de configuración correspondiente
               
            2. Modo 'mouse': Actualización del selector de sensibilidad
               - Similar al selector de micrófono, pero para el otro parámetro
               
            3. Modo 'window': Arrastre de ventana completa
               - Utiliza posición global del cursor y offset inicial
               - Implementa movimiento suave de la ventana sin bordes
               
            Cada modo mantiene su propio estado (self.dragging) y
            se actualiza la UI llamando a self.update() cuando es necesario.
        """
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
    """
    Abre la ventana de configuración
    
    Implementación técnica:
        1. Obtiene o crea una instancia de QApplication:
           - Reutiliza la instancia existente si está disponible
           - Crea una nueva instancia si es necesario
           
        2. Inicializa la ventana de configuración (SettingsWindow)
        
        3. Garantiza visibilidad y foco:
           - show(): Hace visible la ventana
           - activateWindow(): Da foco y activa la ventana
           - raise_(): Trae la ventana al frente
           
        4. No ejecuta un nuevo ciclo de eventos (app.exec_()):
           - Asume que ya hay un ciclo de eventos en ejecución
           - Permite que la ventana sea modal sin bloquear la aplicación principal
           
    Retorna:
        SettingsWindow: Referencia a la ventana creada para que el
                        llamador pueda mantener un seguimiento
    """
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
