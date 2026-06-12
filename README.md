# Analizador Léxico y Sintáctico para Python

Aplicación web que simula las fases iniciales de un compilador —**análisis léxico** y
**análisis sintáctico LL(1)**— sobre un subconjunto del lenguaje Python.
Proyecto del curso de **Compiladores**, Universidad Mariano Gálvez (2026).

🔗 **Demo en producción:** https://proyecto-final-compiladores.onrender.com

---

## 📋 Descripción

El sistema recibe un bloque de código Python, lo procesa en dos fases y muestra de forma
visual todos los productos de cada fase: tokens, tabla de símbolos, árbol sintáctico,
conjuntos PRIMEROS/SIGUIENTES, tabla predictiva LL(1), derivación paso a paso y control de
errores léxicos y sintácticos. Incluye además la documentación teórica del lenguaje
(expresiones regulares, autómatas AFD, máquina discriminadora, notación BNF y diagramas
de Conway).

---

## ✨ Funcionalidades

### Análisis Léxico
- Reconocimiento de **tokens** con número, línea, columna, lexema, token y categoría.
- **Tabla de símbolos** con tipo (variable, función, clase, módulo) y referencias.
- **Control de errores léxicos**: símbolo, tipo, línea y columna.
- Conteo de líneas, tokens e identificadores.

### Análisis Sintáctico
- **Parser predictivo LL(1)** con tabla construida automáticamente (sin conflictos).
- **Árbol sintáctico** generado según el código (Graphviz / viz.js).
- Conjuntos **PRIMEROS y SIGUIENTES** calculados a partir de la gramática.
- **Tabla predictiva LL(1)** y **derivación paso a paso** (traza de la pila).
- **Control de errores sintácticos** con recuperación en modo pánico.

### Material teórico (documentación del lenguaje)
- Expresiones regulares de cada categoría léxica.
- Autómatas finitos deterministas (AFD) y máquina discriminadora.
- Gramática formal en notación BNF.
- Diagramas de Conway (sintaxis).

### Extras
- Exportación a **PDF** (tokens, tabla de símbolos, reporte completo).
- Descarga del árbol sintáctico.
- Dashboard con estadísticas y desglose por categoría.

---

## 🛠️ Tecnologías

**Backend:** Python 3.12, Flask 3, Gunicorn (producción), Graphviz, ReportLab
**Frontend:** Bootstrap 5, Font Awesome 6, Mermaid.js, viz.js, SweetAlert2

---

## 📂 Estructura del proyecto

```
ProyectoCompilador/
├── app.py                  # Servidor Flask y rutas (/, /analyze, /export/*, /healthz)
├── requirements.txt        # Dependencias de Python
├── Procfile                # Comando de arranque en producción (gunicorn)
├── render.yaml             # Configuración automática para Render
├── runtime.txt             # Versión de Python
├── lexer/
│   └── lexer.py            # Analizador léxico (tokens, símbolos, errores)
├── parser/
│   └── parser.py           # Parser LL(1) + gramática
├── utils/
│   ├── first_follow.py     # Cálculo de conjuntos PRIMEROS y SIGUIENTES
│   ├── ll1.py              # Construcción de la tabla predictiva LL(1)
│   └── tree_generator.py   # Generación del árbol sintáctico (Graphviz)
├── templates/
│   ├── base.html           # Layout base y menú lateral
│   └── index.html          # Página principal (todas las secciones)
└── static/
    ├── css/style.css       # Tema oscuro tipo IDE
    └── js/main.js          # Lógica del frontend (AJAX, render, exportación)
```

Cada carpeta es un **módulo por responsabilidad** que corresponde a una fase del compilador:
el texto fluye `lexer → parser → utils → árbol`.

---

## 🔤 Categorías léxicas reconocidas

| Categoría | Ejemplo | Expresión regular |
|-----------|---------|-------------------|
| Palabra reservada | `if`, `while`, `def` | `[a-zA-Z_][a-zA-Z0-9_]*` + tabla de keywords |
| Identificador | `nombre`, `x` | `[a-zA-Z_][a-zA-Z0-9_]*` |
| Entero | `42` | `\d+` |
| Decimal | `3.14` | `\d+\.\d+` |
| Cadena | `"hola"` | `"[^"\n]*"` y `'[^'\n]*'` |
| Operador | `+ - * / == <= **` | `==\|!=\|<=\|>=\|\*\*\|//\|->` y `[+\-*/=%<>!&\|^~]` |
| Delimitador | `( ) { } [ ] : , .` | `[(){}\[\]:,.]` |

---

## 📐 Gramática LL(1)

```
PROGRAMA              -> LISTA_SENTENCIAS
LISTA_SENTENCIAS      -> SENTENCIA LISTA_SENTENCIAS_REST
LISTA_SENTENCIAS_REST -> SENTENCIA LISTA_SENTENCIAS_REST | e
SENTENCIA             -> ID SENTENCIA_ID | if EXPRESION :
                       | while EXPRESION : | for ID in EXPRESION :
                       | def ID ( PARAMS ) : | return EXPRESION
SENTENCIA_ID          -> = EXPRESION | ( ARGS )
ARGS                  -> EXPRESION ARGS_REST | e
ARGS_REST             -> , EXPRESION ARGS_REST | e
PARAMS                -> ID PARAMS_REST | e
PARAMS_REST           -> , ID PARAMS_REST | e
EXPRESION             -> TERMINO EXPRESION_REST
EXPRESION_REST        -> OPERADOR TERMINO EXPRESION_REST | e
TERMINO               -> ID | ENTERO | DECIMAL | CADENA | ( EXPRESION )
```

La gramática está **factorizada por la izquierda** para evitar conflictos LL(1)
(verificado: la tabla predictiva no tiene celdas en conflicto).

---

## ▶️ Ejecución local

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar
python app.py
```

Abrir en el navegador: http://localhost:5000

> No es obligatorio instalar Graphviz del sistema: el árbol se dibuja en el navegador
> con viz.js. Graphviz solo se usa para exportar el árbol como PNG.

### Variables de entorno (opcionales)

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `FLASK_DEBUG` | `0` | `1` activa el modo debug |
| `SECRET_KEY` | clave de desarrollo | Clave de sesión para producción |
| `PORT` | `5000` | Puerto del servidor |

---

## ☁️ Despliegue en producción (Render)

El proyecto está listo para Render con `render.yaml`, `Procfile` y `gunicorn`:

1. Subir el código a GitHub.
2. En [render.com](https://render.com) → **New + → Web Service** → conectar el repositorio.
3. Render detecta `render.yaml` y configura todo (build: `pip install -r requirements.txt`,
   start: `gunicorn app:app --bind 0.0.0.0:$PORT`).
4. Render genera el link público y una `SECRET_KEY` segura automáticamente.

El plan gratuito "duerme" el servicio tras 15 min de inactividad. Para mantenerlo siempre
despierto se usa un monitor gratuito (UptimeRobot) que hace ping cada 5 min al endpoint
ligero `/healthz`.

---

## 🔄 ¿Qué cambia al cambiar de ejercicio?

Concepto clave de compiladores: algunas secciones describen el **lenguaje/gramática**
(son fijas) y otras describen el **código de entrada** (cambian).

**Fijas (propiedad del lenguaje/gramática):** Expresiones Regulares, Autómatas AFD,
Máquina Discriminadora, Notación BNF, Diagramas de Conway, conjuntos PRIMEROS/SIGUIENTES
y Tabla LL(1). No dependen del código; son las mismas para cualquier entrada.

**Dinámicas (dependen del código analizado):** Tabla de Tokens, Tabla de Símbolos,
Árbol Sintáctico, Derivación paso a paso, Errores y Dashboard.

---

## ⚠️ Limitaciones conocidas

- Las llamadas a función son válidas como sentencia (`suma(5, 10)`), no como valor a la
  derecha de una asignación (`r = suma(5, 10)`).
- No se modela la indentación/bloques anidados de Python: las sentencias se analizan como
  una lista plana (alcance de "subconjunto simplificado").
- Los decimales requieren dígitos a ambos lados del punto (`3.14`, no `.5` ni `3.`).

---

## 👤 Autor

Proyecto de Compiladores — Universidad Mariano Gálvez, 2026.
