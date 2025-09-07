# CATNIPY

<img width="500" height="500" alt="cat_idle" src="https://github.com/user-attachments/assets/50385f68-33d8-4353-b5b5-b99f11282e08" />

Transforming Interaction into Engaging Digital Experiences

[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-blue)](https://github.com/GabyPng/catnipy)
[![Python](https://img.shields.io/badge/python-3.6+-blue)](https://www.python.org/downloads/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15-blue)](https://pypi.org/project/PyQt5/)

Built with the tools and technologies:

[![PyQt5](https://img.shields.io/badge/-PyQt5-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)
[![NumPy](https://img.shields.io/badge/-NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
[![Pynput](https://img.shields.io/badge/-Pynput-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://pynput.readthedocs.io/)
[![Python](https://img.shields.io/badge/-Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GitHub Actions](https://img.shields.io/badge/-GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)](https://github.com/features/actions)

## Table of Contents

* [Descripción detallada](#descripción-detallada)
* [Documentación técnica](#documentación-técnica)
  * [Inspiración](#inspiración)
  * [Sounddevice](#sounddevice)
  * [Pynput](#pynput)
* [Instalación y Ejecución](#instalación-y-ejecución)
  * [Dependencias](#dependencias)
  * [Ejecución](#ejecución)
  * [Controles](#controles)
* [Configuración Avanzada](#configuración-avanzada)
* [Arquitectura del Sistema](#arquitectura-del-sistema)
* [Exportación a Ejecutable](#exportación-a-ejecutable)

CatNipy es una aplicación de escritorio que muestra una mascota virtual (un gato) que reacciona al sonido del micrófono, movimientos del teclado y del mouse. La aplicación utiliza PyQt5 para la interfaz gráfica, sounddevice para la captura de audio en tiempo real y pynput para capturar eventos globales del sistema.

Trabajo en conjunto con [Madnux](https://github.com/mad2ux)

---
<br>

## Documentación técnica

### Inspiración
https://medium.com/analytics-vidhya/create-your-own-desktop-pet-with-python-5b369be18868

### Sounddevice
https://python-sounddevice.readthedocs.io/en/0.5.1/installation.html

### Pynput
https://pynput.readthedocs.io/en/latest/

<br>

## Instalación y Ejecución

### **Dependencias**
```bash
pip install sounddevice numpy PyQt5 pynput
```

### **Ejecución**
```bash
python brain.py
```

### **Controles**
- **Clic + Arrastrar**: Mover mascota
- **Doble clic**: Cerrar aplicación
- **Teclas**: Activa animación de teclado
- **Mouse**: Activa animación de mouse
- **Audio**: Detección automática

---
<br>

## Configuración Avanzada

### **Ajustar Sensibilidad Audio**
```python
volumen_umbral = 0.001  # Reducir => más sensible
```

### **Cambiar Posición Inicial**
```python
self.setGeometry(x, y, 20, 20)  # Modificar x, y
```

### **Ajustar Posición Overlay**
```python
self.overlay_label.move(x_offset, y_offset)
```

### **Ajustar Sensibilidad de Movimiento del Mouse**
```python
# Limitar la frecuencia de actualización para movimientos del mouse
if current_time - self.last_mouse_move_time > 0.1:  # Modificar este valor (segundos)
    # Cuanto mayor sea el valor, menos sensible será a los movimientos del mouse
```

---
<br>

## Arquitectura del Sistema

### Componentes Principales

#### 1. **Clase Principal: `CatNipy(QWidget)`**
- **Herencia**: Extiende `QWidget` de PyQt5
- Gestiona la interfaz gráfica y coordina todos los componentes
- Compositor (combina UI, audio y eventos)

#### 2. **Sistema de Interfaz Gráfica por Capas**
```python
self.base_label = QLabel(self)          # Imagen base del gato
self.keyboard_label = QLabel(self)      # Capa para animaciones de teclado
self.mouse_label = QLabel(self)         # Capa para animaciones de mouse
self.overlay_label = QLabel(self)       # Capa para animaciones de boca (cuanto está hablando)
```

#### 3. **Sistema de Audio**
```python
self.stream = sd.InputStream(...)   # Stream de captura de audio
```

#### 4. **Sistema de Eventos Globales**
```python
# Monitoreo de teclado global
self.keyboard_listener = keyboard.Listener(...)

# Monitoreo de mouse global
self.mouse_listener = mouse.Listener(...)
```

#### 5. **Sistema de Comunicación Entre Hilos**
```python
# Clase para manejar señales entre hilos
class GlobalEventSignals(QObject):
    keyPressSignal = pyqtSignal()
    keyReleaseSignal = pyqtSignal()
    # ... otras señales
```

<br>

## Componentes Técnicos

### **Configuración de Ventana**

#### `setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)`
- **FramelessWindowHint**: Elimina decoraciones de ventana (barra de título, bordes)
- **WindowStaysOnTopHint**: Mantiene la ventana siempre visible sobre otras aplicaciones

### **Comunicación Entre Hilos**

PyQt5 requiere que todas las actualizaciones de UI se realicen desde el hilo principal. Para manejar eventos provenientes de hilos secundarios (como los monitores globales de pynput), usamos el sistema de señales y slots de Qt:

```python
# Emisión de señal desde un hilo secundario
self.signals.keyPressSignal.emit()

# Conexión en el hilo principal
self.signals.keyPressSignal.connect(lambda: self.update_keyboard_state("typing_handdown"))
```

### **Sistema de Monitoreo Global**

El uso de `pynput` permite detectar eventos de teclado y mouse incluso cuando la aplicación no tiene el foco:

```python
# Inicializar monitor de teclado global
self.keyboard_listener = keyboard.Listener(
    on_press=self.on_global_key_press,
    on_release=self.on_global_key_release)
```

### **Limitación de Frecuencia de Eventos**

Para evitar sobrecargar la CPU con demasiados eventos, especialmente para el movimiento del mouse:

```python
# Limitación de la frecuencia de actualización
current_time = time.time()
if current_time - self.last_mouse_move_time > 0.1:  # ~10 actualizaciones/segundo
    self.last_mouse_move_time = current_time
    # Procesar evento...
```
- **Operador |**: Combina múltiples flags usando OR bitwise

#### `setAttribute(Qt.WA_TranslucentBackground)`
- **Función**: Hace el fondo de la ventana completamente transparente

#### `setGeometry(x, y, width, height)`
- **Parámetros**: Posición inicial (x,y) y tamaño inicial (width,height)
- **Nota**: El tamaño se reajusta automáticamente con `resize()`

---
<br>

### **Sistema de Imágenes en Capas**

#### Arquitectura de Capas
```
┌─────────────────────────┐
│   overlay_label         │ ← Capa superior (boca hablando)
│   (cat_onlytalking.png) │
├─────────────────────────┤
│   label                 │ ← Capa base (gato idle)
│   (cat_idle.png)        │
└─────────────────────────┘
```

#### `QPixmap`
- Contenedor optimizado para imágenes en memoria
- Sirve para la aceleración por hardware, soporte transparencia Alpha
- Cargado una vez, reutilizado múltiples veces

#### Sistema de Superposición
```python
self.overlay_label.show()  # Mostrar capa superior
self.overlay_label.hide()  # Ocultar capa superior
```
- No hay intercambio de imágenes, solo visibilidad
- Más eficiente que cargar/descargar imágenes

---
<br>


### **Sistema de Detección de Audio**

#### `sounddevice.InputStream`
```python
sd.InputStream(
    samplerate=44100,      # Frecuencia de muestreo (Hz)
    blocksize=1024,        # Tamaño del buffer (samples)
    callback=self.audio_callback
)
```

#### Parámetros Técnicos
- **samplerate (44100 Hz)**: Estándar de audio CD, captura hasta 22kHz
- **blocksize (1024)**: Buffer de ~23ms a 44.1kHz (balance latencia/procesamiento)
- **callback**: Función ejecutada asíncronamente por cada bloque de audio

#### Algoritmo de Detección
```python
volumen = np.sqrt(np.mean(indata**2))  # RMS (Root Mean Square)
```
- **indata**: Array NumPy con samples de audio
- **indata**2**: Elevar al cuadrado (eliminar valores negativos)
- **np.mean()**: Promedio de la energía
- **np.sqrt()**: Raíz cuadrada = valor RMS
- **Resultado**: Valor entre 0.0 (silencio) y 1.0+ (sonido fuerte)

#### Umbral de Detección
```python
volumen_umbral = 0.001  # Sensibilidad ajustable
```
- Filtro de ruido de fondo
- Permite calibrar según micrófono/ambiente

---
<br>

### **Sistema de Eventos del Mouse**

#### Patrón Observer
Cada evento del mouse se maneja mediante el patrón Observer de PyQt5:

#### `mousePressEvent(event)`
```python
self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
```
- **event.globalPos()**: Posición absoluta del cursor en pantalla
- **frameGeometry().topLeft()**: Esquina superior izquierda de la ventana
- **Cálculo**: Offset relativo para mantener posición durante arrastre

#### `mouseMoveEvent(event)`
```python
self.move(event.globalPos() - self.drag_position)
```
- Nueva posición = Cursor actual - Offset inicial
- Movimiento suave sin saltos al cursor

#### Control de Estados
```python
self.dragging = False  # Flag de estado
```
- Evitar movimiento accidental
- **Thread-safe**: Acceso controlado al estado de arrastre

---
<br>


## Flujo de Datos

### **Flujo de Audio**
```
Micrófono → sounddevice → Buffer (1024 samples) → 
Callback función → Cálculo RMS → Comparación umbral → 
Mostrar/Ocultar overlay
```

### **Flujo de Eventos UI**
```
Mouse Event → PyQt5 Event System → Event Handler → 
Update GUI State → Repaint Window
```

---
<br>


## Gestión de Recursos

### **Audio Stream**
```python
def closeEvent(self, event):
    if hasattr(self, 'stream'):
        self.stream.stop()
        self.stream.close()
```
- **Importante**: Liberar recursos de audio al cerrar
- **Previene**: Memory leaks y bloqueo de dispositivos de audio

### **Gestión de Memoria**
- **QPixmap**: Cargado una vez, reutilizado
- **Event Handlers**: Garbage collected automáticamente por PyQt5
- **Audio Buffer**: Gestionado internamente por sounddevice

---
<br>

## Consideraciones de Rendimiento

### **Audio Processing**
- **Frecuencia**: ~43 callbacks por segundo (1024/44100)
- **CPU**: Mínimo (solo cálculo RMS)
- **Latencia**: ~23ms (tiempo real perceptible)

### **GUI Updates**
- **Frecuencia**: Variable (según detección de audio)
- **Operación**: Show/Hide (no redibujado completo)
- **GPU**: Aceleración hardware para transparencias

<br>

## Estructura de Archivos

```
catnipy/
├── brain.py                        # Aplicación principal
├── requirements.txt                 # Dependencias Python
├── README.md                       # Documentación técnica
└── assets/
    └── motions/
        ├── cat_idle.png            # Imagen base del gato
        └── cat_onlytalking.png     # Superposición boca hablando
```

---

## Exportación a Ejecutable

### Método rápido (recomendado)
Usa el script multiplataforma incluido:
```bash
python create_executable.py
```
o
```bash
./create_executable.py  # En Linux/macOS
```

### Método manual

#### Instalación de PyInstaller
```bash
pip install pyinstaller
```

#### Para Linux
```bash
pyinstaller --onefile --noconsole --name catnipy --add-data "assets:assets" brain.py
```

#### Para Windows
```bash
pyinstaller --onefile --noconsole --name catnipy --add-data "assets;assets" brain.py
```

> **Nota importante**: Observa la diferencia en el separador de `--add-data`: en Linux se usa `:` (dos puntos) mientras que en Windows se usa `;` (punto y coma).

### Ubicación del ejecutable
El archivo ejecutable se creará en la carpeta `dist/` dentro del directorio de tu proyecto.

### Compatibilidad entre plataformas
Si estás desarrollando en una plataforma para generar un ejecutable para otra:
1. Usa el script `create_executable.py` incluido (multiplataforma)
2. O genera el ejecutable directamente en la plataforma de destino

### Resolución de problemas comunes
- **Archivos no encontrados**: Asegúrate de que la estructura de `assets/` se mantiene
- **Problemas de acceso al micrófono**: En Windows puede requerir permisos de administrador
- **Antivirus**: Algunos antivirus pueden bloquear el ejecutable; añádelo a excepciones

## Notas Técnicas

- **Thread Model**: Audio callback en thread separado, GUI en main thread
- **Cross-platform**: Compatible con Windows ✅, Linux ✅, macOS ⚠️ (no probado)
- **Dependencies**: PyQt5, sounddevice, numpy, pynput
- **Python Version**: 3.6+
# catnipy
