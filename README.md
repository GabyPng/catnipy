# CatNipy | Mascota Virtual

<img width="500" height="500" alt="cat_idle" src="https://github.com/user-attachments/assets/50385f68-33d8-4353-b5b5-b99f11282e08" />
<br>

Trabajo en conjunto con [Madnux](https://github.com/mad2ux)

<br>

## Descripción detallada

CatNipy es una aplicación de escritorio que muestra una mascota virtual (un gato) que hasta ahora reacciona al sonido del micrófono. La aplicación utiliza PyQt5 para la interfaz gráfica y sounddevice para la captura de audio en tiempo real.

---
<br>

## Documentación técnica

### Inspiración
https://medium.com/analytics-vidhya/create-your-own-desktop-pet-with-python-5b369be18868

### Sounddevice
https://python-sounddevice.readthedocs.io/en/0.5.1/installation.html

<br>

## Instalación y Ejecución

### **Dependencias**
```bash
pip install sounddevice numpy PyQt5
```

### **Ejecución**
```bash
python brain.py
```

### **Controles**
- **Clic + Arrastrar**: Mover mascota
- **Doble clic**: Cerrar aplicación
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
---
<br>



## Arquitectura del Sistema

### Componentes Principales

#### 1. **Clase Principal: `CatNipy(QWidget)`**
- **Herencia**: Extiende `QWidget` de PyQt5
- Gestiona la interfaz gráfica y coordinar todos los componentes
- Compositor (combina UI, audio y eventos)

#### 2. **Sistema de Interfaz Gráfica**
```python
self.label = QLabel(self)           # Imagen base del gato
self.overlay_label = QLabel(self)   # Superposición para animaciones
```

#### 3. **Sistema de Audio**
```python
self.stream = sd.InputStream(...)   # Stream de captura de audio
```

<br>



## Componentes Técnicos Detallados

### **Configuración de Ventana**

#### `setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)`
- **FramelessWindowHint**: Elimina decoraciones de ventana (barra de título, bordes)
- **WindowStaysOnTopHint**: Mantiene la ventana siempre visible sobre otras aplicaciones
- **Operador |**: Combina múltiples flags usando OR bitwise

#### `setAttribute(Qt.WA_TranslucentBackground)`
- **Función**: Hace el fondo de la ventana completamente transparente
- **Resultado**: Solo las imágenes PNG son visibles, el resto es transparente

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

## Notas Técnicas

- **Thread Model**: Audio callback en thread separado, GUI en main thread
- **Cross-platform**: Compatible con Windows ?, Linux, macOS ???
- **Dependencies**: PyQt5, sounddevice, numpy
- **Python Version**: 3.6+
# catnipy
