# 🎬 Agentic Cinema — Design Specifications & Frontend Guidelines

Bienvenido a la carpeta de especificaciones de diseño (`design/`) de **Agentic Cinema**. 

Este documento tiene como objetivo guiar a cualquier desarrollador frontend, diseñador o agente de desarrollo que trabaje en el proyecto, explicando la estructura de los recursos visuales, la interpretación de las plantillas y las reglas de implementación técnica para la interfaz de usuario y los componentes animados.

---

## 📁 1. Estructura de Directorios

La carpeta `design/` dentro de la raíz del proyecto (`agentic.cinema/`) está organizada de la siguiente manera:

```text
agentic.cinema/
└── design/
    ├── icon_references/
    │   ├── agenti_cinema_icons_animation.mp4  # Referencia en video de las animaciones
    │   └── agentic_cinema_icons.jpg           # Collage/plantilla estática de iconos
    ├── ui_references/
    │   ├── agenti_cinema_chat.jpg             # Maqueta visual de la interfaz de Chat / Agente
    │   └── agentic_cinema_library.jpg         # Maqueta visual de la Biblioteca / Catálogo
    └── README.md                              # Esta guía técnica de diseño e implementación
```

---

## 🖥️ 2. Referencias de Interfaz de Usuario (`ui_references/`)

Las imágenes en esta carpeta definen la **apariencia global, arquitectura visual y experiencia de usuario (UX/UI)** del sistema. Deben utilizarse como la fuente de verdad (*ground truth*) para estructurar el layout y los estilos:

### 💬 `agenti_cinema_chat.jpg` (Módulo de Chat & Colaboración con Agentes)
* **Propósito:** Define la pantalla de interacción conversacional en tiempo real con los agentes cinematográficos (guionistas, directores, asistentes de escena).
* **Puntos clave a implementar:**
  * Disposición de mensajes estilo asistente/usuario con soporte para bloques de código, previsualizaciones y prompts enriquecidos.
  * Barra de entrada (*input box*) con botones de acción rápida, controles de contexto y selección de modo/agente.
  * Paneles laterales colapsables para parámetros de contexto, memoria del agente o historial de conversaciones.

### 📚 `agentic_cinema_library.jpg` (Módulo de Biblioteca & Gestión de Proyectos)
* **Propósito:** Define la vista de catálogo y administración de recursos generados (películas, tomas, escenas, storyboards, personajes y assets).
* **Puntos clave a implementar:**
  * Cuadrícula de tarjetas (*cards*) con vista previa de miniaturas, metadatos (duración, etiquetas, estado de render) y menú de opciones rápidas.
  * Sistema de filtrado superior (búsqueda por texto, categorías de género, fecha de creación o estado de producción).
  * Consistencia de espaciado y márgenes según la estética general.

### 🎨 Estética y Lenguaje Visual General
* **Tema Oscuro Cinemático (*Dark Mode*):** Fondos en tonalidades oscuras profundas (`#0B0D13`, `#12151E` o similar) para maximizar el contraste de contenido audiovisual.
* **Acentos Lumínicos:** Destellos sutiles en bordes, acentos en tonos dorados/ámbar cálidos o azules de proyector para elementos interactivos y estados activos.
* **Acabados Modernos:** Uso de bordes sutiles semi-transparentes y paneles con desenfoque de fondo (*backdrop-filter / glassmorphism*).

---

## 🎭 3. Referencias e Implementación de Iconos (`icon_references/`)

Los archivos de esta carpeta contienen el diseño y el comportamiento esperado para la iconografía personalizada del proyecto.

### 🖼️ `agentic_cinema_icons.jpg` (Plantilla Estática)
* Muestra el collage con la totalidad de los iconos diseñados para el sistema.
* Define la **forma base, proporciones, estilo de trazo (*stroke*) y estado de reposo (*idle state*)**.

### 🎥 `agenti_cinema_icons_animation.mp4` (Referencia de Movimiento)
* Demuestra cómo debe ser el **movimiento, rotación, trayectoria y micro-interacción** de cada elemento móvil de los iconos.
* Sirve como guía de ritmo (*timing/easing*) para reproducir mediante código frontend.

---

## ⚙️ 4. Reglas Estrictas de Implementación para Desarrolladores

Para garantizar el mejor rendimiento, accesibilidad y fidelidad de diseño, todos los desarrolladores deben seguir estas directrices:

### 1. Construcción Modular Individual (SVG + CSS/JS)
> ⚠️ **NO incrustar videos ni GIFs directamente en la interfaz.**
* Cada icono mostrado en `agentic_cinema_icons.jpg` debe codificarse como un **componente SVG independiente y reutilizable** (en React, Vue, Web Components o HTML semántico).
* Los elementos internos del SVG que tengan animación deben contar con sus respectivas clases (`.icon-reel`, `.icon-lens`, etc.) para ser manipulados por CSS o JavaScript.

### 2. Comportamiento de Animación: Interactiva y Sin Bucle (*No Infinite Loop*)
* 🛑 **Prohibido el bucle infinito:** Ningún icono debe animarse de forma continua o permanente cuando el usuario no está interactuando con él. Esto evita distracciones visuales y sobrecarga del hilo principal del navegador.
* 🖱️ **Disparo en Hover / Foco (1 solo ciclo):** La animación se activa cuando el usuario pasa el cursor por encima (`:hover`) o enfoca el elemento mediante navegación por teclado (`:focus-visible`).
* 🔄 **Ejecución Única y Retorno Suave:** La animación debe correr exactamente **una vez (1 ciclo)** y finalizar suavemente en su estado natural o regresar gradualmente a su posición de reposo al retirar el cursor (`mouseleave`).

---

## 💻 5. Ejemplo Técnico de Referencia (CSS & SVG)

A continuación se presenta el patrón estándar recomendado para cualquier icono animado del proyecto:

```html
<!-- Ejemplo: Componente de Carrete de Cine -->
<button class="cinema-btn" aria-label="Abrir Biblioteca">
  <svg class="cinema-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
    <!-- Base fija del icono -->
    <path class="icon-base" d="M4 6h16M4 18h16" stroke-width="2" stroke-linecap="round"/>
    <!-- Elemento interactivo con animación -->
    <circle class="icon-reel-spin" cx="12" cy="12" r="5" stroke-width="2"/>
  </svg>
  <span>Proyectos</span>
</button>
```

```css
/* Estado Base en Reposo */
.cinema-icon {
  width: 24px;
  height: 24px;
  stroke: #94a3b8; /* Color neutro de reposo */
  transition: stroke 0.3s ease;
}

/* Disparo de animación en Hover (1 solo ciclo, NO loop) */
.cinema-btn:hover .cinema-icon {
  stroke: #f59e0b; /* Acento dorado cinemático */
}

.cinema-btn:hover .icon-reel-spin {
  animation: singleSpin 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

/* Definición de la animación de 1 ciclo */
@keyframes singleSpin {
  0% {
    transform: rotate(0deg);
    transform-origin: center;
  }
  100% {
    transform: rotate(180deg);
    transform-origin: center;
  }
}

/* Accesibilidad: Respetar si el usuario tiene desactivadas las animaciones */
@media (prefers-reduced-motion: reduce) {
  .cinema-btn:hover .icon-reel-spin {
    animation: none;
  }
}
```

---

## 📋 6. Checklist de Integración

Antes de enviar un Pull Request o dar por completada una pantalla/componente, verifica lo siguiente:

- [ ] La estructura y colores de la vista coinciden con `agenti_cinema_chat.jpg` o `agentic_cinema_library.jpg`.
- [ ] Los iconos están creados como componentes SVG individuales basados en `agentic_cinema_icons.jpg`.
- [ ] La coreografía de movimiento refleja lo visto en `agenti_cinema_icons_animation.mp4`.
- [ ] Las animaciones se ejecutan solo al interactuar (hover/foco) y **no se quedan en bucle infinito**.
- [ ] Se incluye soporte para modo de movimiento reducido (`prefers-reduced-motion`).