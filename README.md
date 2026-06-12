# Analizador Lexico y Sintactico para Python

Aplicacion web universitaria que simula las fases de un compilador.
Universidad Mariano Galvez — Compiladores 2026

## Tecnologias

**Backend:** Python 3.10+, Flask 3.x, Graphviz  
**Frontend:** Bootstrap 5, Font Awesome 6, Mermaid.js, Viz.js, SweetAlert2

## Instalacion

```bash
# 1. Clonar / descomprimir el proyecto
cd ProyectoCompilador

# 2. Instalar dependencias Python
pip install -r requirements.txt

# 3. (Opcional) Instalar Graphviz del sistema para PNG del arbol
#    Windows: https://graphviz.org/download/
#    Linux:   sudo apt install graphviz
#    macOS:   brew install graphviz

# 4. Ejecutar
python app.py
```

Abrir en el navegador: http://localhost:5000

> El árbol sintáctico se renderiza en el navegador con viz.js, por lo que
> instalar Graphviz del sistema es **opcional** (solo se usa para exportar el PNG).

### Variables de entorno (opcionales)

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `FLASK_DEBUG` | `0` | `1` activa el modo debug de Flask |
| `SECRET_KEY` | dev key | Clave de sesión para producción |
| `PORT` | `5000` | Puerto del servidor |

## Modulos

| Modulo | Descripcion |
|--------|-------------|
| Modulo 1 | Editor de codigo estilo VS Code con numeracion de lineas |
| Modulo 2 | Analizador Lexico — tokens, tabla de simbolos, errores |
| Modulo 3 | Analizador Sintactico LL(1) — arbol, FIRST/FOLLOW, derivacion |
| Modulo 4 | Automatas AFD (Identificador, Entero, Decimal, Cadena) |
| Modulo 5 | Maquina Discriminadora |
| Modulo 6 | Diagramas de Conway |
| Dashboard | Estadisticas, exportacion PDF |

## Estructura

```
ProyectoCompilador/
├── app.py              # Flask backend y rutas
├── requirements.txt
├── lexer/
│   └── lexer.py        # Analizador lexico
├── parser/
│   └── parser.py       # Parser LL(1)
├── utils/
│   ├── first_follow.py # Conjuntos FIRST y FOLLOW
│   ├── ll1.py          # Tabla predictiva LL(1)
│   └── tree_generator.py # Arbol con Graphviz
├── templates/
│   ├── base.html       # Layout base
│   └── index.html      # Pagina principal
├── static/
│   ├── css/style.css   # Tema oscuro IDE
│   └── js/main.js      # Logica frontend
└── reports/            # PDFs exportados
```

## Gramatica LL(1)

```
PROGRAMA              -> LISTA_SENTENCIAS
LISTA_SENTENCIAS      -> SENTENCIA LISTA_SENTENCIAS_REST
LISTA_SENTENCIAS_REST -> SENTENCIA LISTA_SENTENCIAS_REST | e
SENTENCIA             -> ID SENTENCIA_ID | if EXPRESION :
                       | while EXPRESION : | for ID in EXPRESION :
                       | def ID ( PARAMS ) : | return EXPRESION
SENTENCIA_ID          -> = EXPRESION | ( ARGS )
EXPRESION             -> TERMINO EXPRESION_REST
EXPRESION_REST        -> OP TERMINO EXPRESION_REST | e
TERMINO               -> ID | NUM | DECIMAL | CADENA | ( EXPRESION )
```

## Uso

1. Escribe codigo Python en el editor
2. Presiona **Analizar**
3. Navega por las secciones del menu lateral
4. Exporta resultados como PDF desde el Dashboard
