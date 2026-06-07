"""
Aplicación Web: Analizador Léxico y Sintáctico para Python
Backend: Flask 3.x
Autor: ProyectoCompilador UMG

Rutas:
    GET  /                  → Página principal (editor + resultados)
    POST /analyze           → Ejecutar análisis léxico + sintáctico
    GET  /export/tokens     → Exportar tokens a PDF
    GET  /export/symbols    → Exportar tabla de símbolos a PDF
    GET  /export/report     → Exportar reporte completo a PDF
    GET  /tree/download     → Descargar árbol sintáctico PNG
"""

import os
import sys
import json
import time
import base64
import io

from flask import (
    Flask, render_template, request, jsonify,
    send_file, session
)

# ── Agregar raíz al path para imports relativos ──
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer.lexer        import PythonLexer
from parser.parser      import LL1Parser
from utils.tree_generator import TreeGenerator

# ─────────────────────────────────────────────────────────────────────────────
# Configuración de la aplicación
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'compilador-umg-2024-secret'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB máximo

# Directorio para reportes y árboles generados
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
STATIC_IMG  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'img')
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(STATIC_IMG,  exist_ok=True)

# Instancias de analizadores (reutilizables)
lexer          = PythonLexer()
parser         = LL1Parser()
tree_generator = TreeGenerator(output_dir=STATIC_IMG)


# ─────────────────────────────────────────────────────────────────────────────
# Ruta Principal
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    """Sirve la página principal de la aplicación."""
    return render_template('index.html')


# ─────────────────────────────────────────────────────────────────────────────
# Ruta de Análisis (AJAX)
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Ejecuta el análisis léxico y sintáctico sobre el código recibido.

    Body JSON:
        { "code": "código Python..." }

    Returns:
        JSON con tokens, tabla de símbolos, errores, árbol y más.
    """
    data = request.get_json(silent=True)
    if not data or 'code' not in data:
        return jsonify({'error': 'No se recibió código'}), 400

    code = data['code']
    if not code.strip():
        return jsonify({'error': 'El código está vacío'}), 400

    start_total = time.time()

    # ── Fase 1: Análisis Léxico ──
    lex_result = lexer.tokenize(code)

    # ── Fase 2: Análisis Sintáctico (solo si no hay errores graves) ──
    syn_result = {}
    tree_data  = {}

    try:
        # Solo parsear si hay tokens válidos
        valid_tokens = [
            t for t in lex_result['tokens']
            if t['categoria'] not in ('ERROR',)
        ]
        syn_result = parser.parse(valid_tokens)

        # ── Generar árbol sintáctico ──
        if syn_result.get('tree'):
            tree_data = tree_generator.generate(
                syn_result['tree'],
                filename='syntax_tree'
            )
    except Exception as e:
        syn_result = {
            'success':     False,
            'errors':      [{'tipo': 'Error interno', 'descripcion': str(e), 'linea': 0}],
            'derivations': [],
            'first':       {},
            'follow':      {},
            'll1_table':   {},
            'grammar':     {},
        }

    elapsed_total = round((time.time() - start_total) * 1000, 2)

    # ── Guardar en sesión para exportaciones ──
    session['last_lex'] = lex_result
    session['last_syn'] = {
        'success':     syn_result.get('success', False),
        'errors':      syn_result.get('errors', []),
        'grammar':     syn_result.get('grammar', {}),
    }
    session['last_code'] = code[:500]  # Guardar fragmento

    response = {
        # Análisis léxico
        'tokens':       lex_result['tokens'],
        'symbol_table': lex_result['symbol_table'],
        'lex_errors':   lex_result['errors'],
        'stats':        {
            **lex_result['stats'],
            'tiempo_total_ms': elapsed_total,
        },

        # Análisis sintáctico
        'syn_success':  syn_result.get('success', False),
        'syn_errors':   syn_result.get('errors', []),
        'derivations':  syn_result.get('derivations', []),
        'first':        syn_result.get('first', {}),
        'follow':       syn_result.get('follow', {}),
        'll1_table':    syn_result.get('ll1_table', {}),
        'grammar':      syn_result.get('grammar', {}),

        # Árbol sintáctico
        'tree':         syn_result.get('tree', {}),
        'dot_source':   tree_data.get('dot_source', ''),
        'tree_png_b64': tree_data.get('png_base64', None),
    }

    return jsonify(response)


# ─────────────────────────────────────────────────────────────────────────────
# Exportación a PDF
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/export/tokens', methods=['POST'])
def export_tokens():
    """Exporta la tabla de tokens a PDF."""
    data = request.get_json(silent=True) or {}
    tokens = data.get('tokens', [])
    return _generate_pdf_tokens(tokens)


@app.route('/export/symbols', methods=['POST'])
def export_symbols():
    """Exporta la tabla de símbolos a PDF."""
    data = request.get_json(silent=True) or {}
    symbols = data.get('symbols', [])
    return _generate_pdf_symbols(symbols)


@app.route('/export/report', methods=['POST'])
def export_report():
    """Exporta el reporte completo a PDF."""
    data = request.get_json(silent=True) or {}
    return _generate_pdf_report(data)


# ─────────────────────────────────────────────────────────────────────────────
# Descarga de árbol PNG
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/tree/download')
def download_tree():
    """Descarga el árbol sintáctico generado como PNG."""
    tree_path = os.path.join(STATIC_IMG, 'syntax_tree.png')
    if os.path.exists(tree_path):
        return send_file(tree_path, as_attachment=True, download_name='arbol_sintactico.png')
    return jsonify({'error': 'Árbol no generado aún'}), 404


# ─────────────────────────────────────────────────────────────────────────────
# Helpers PDF con ReportLab
# ─────────────────────────────────────────────────────────────────────────────
def _generate_pdf_tokens(tokens: list):
    """Genera PDF con la tabla de tokens."""
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                                topMargin=1.5*cm, bottomMargin=1.5*cm)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('title', parent=styles['Title'],
                                     textColor=colors.HexColor('#1e3a5f'),
                                     fontSize=16)
        elements = []
        elements.append(Paragraph('Analizador Léxico — Tabla de Tokens', title_style))
        elements.append(Spacer(1, 0.5*cm))

        # Encabezados
        header = ['#', 'Línea', 'Columna', 'Lexema', 'Token', 'Categoría']
        table_data = [header]
        for t in tokens:
            table_data.append([
                str(t.get('numero', '')),
                str(t.get('linea', '')),
                str(t.get('columna', '')),
                t.get('lexema', ''),
                t.get('token', ''),
                t.get('categoria', ''),
            ])

        tbl = Table(table_data, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND',  (0, 0), (-1, 0),  colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR',   (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',    (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',    (0, 0), (-1, 0),  10),
            ('ALIGN',       (0, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.HexColor('#f8f9fa'), colors.white]),
            ('GRID',        (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('FONTSIZE',    (0, 1), (-1, -1), 9),
        ]))
        elements.append(tbl)
        doc.build(elements)
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf',
                         as_attachment=True, download_name='tokens.pdf')
    except Exception as e:
        return jsonify({'error': f'Error generando PDF: {e}'}), 500


def _generate_pdf_symbols(symbols: list):
    """Genera PDF con la tabla de símbolos."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                topMargin=1.5*cm, bottomMargin=1.5*cm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('title', parent=styles['Title'],
                                     textColor=colors.HexColor('#2d6a4f'),
                                     fontSize=16)
        elements = []
        elements.append(Paragraph('Tabla de Símbolos', title_style))
        elements.append(Spacer(1, 0.5*cm))

        header = ['Nombre', 'Tipo', 'Línea Declaración', 'Referencias']
        table_data = [header]
        for s in symbols:
            table_data.append([
                s.get('nombre', ''),
                s.get('tipo', ''),
                str(s.get('linea', '')),
                s.get('referencias', ''),
            ])

        tbl = Table(table_data, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND',  (0, 0), (-1, 0),  colors.HexColor('#2d6a4f')),
            ('TEXTCOLOR',   (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',    (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('ALIGN',       (0, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.HexColor('#f8f9fa'), colors.white]),
            ('GRID',        (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('FONTSIZE',    (0, 1), (-1, -1), 9),
        ]))
        elements.append(tbl)
        doc.build(elements)
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf',
                         as_attachment=True, download_name='tabla_simbolos.pdf')
    except Exception as e:
        return jsonify({'error': f'Error generando PDF: {e}'}), 500


def _generate_pdf_report(data: dict):
    """Genera reporte completo en PDF."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph,
            Spacer, HRFlowable, PageBreak
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()

        heading = ParagraphStyle('heading', parent=styles['Heading1'],
                                 textColor=colors.HexColor('#1e3a5f'))
        subheading = ParagraphStyle('subh', parent=styles['Heading2'],
                                    textColor=colors.HexColor('#2d6a4f'))
        normal = styles['Normal']

        elements = []

        # Portada
        elements.append(Spacer(1, 2*cm))
        elements.append(Paragraph(
            'Reporte de Análisis Léxico y Sintáctico',
            ParagraphStyle('cover', parent=styles['Title'],
                           textColor=colors.HexColor('#1e3a5f'), fontSize=20)
        ))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph('Universidad Mariano Gálvez — Compiladores', normal))
        elements.append(HRFlowable(width='100%', color=colors.HexColor('#1e3a5f')))
        elements.append(Spacer(1, 1*cm))

        # Estadísticas
        stats = data.get('stats', {})
        if stats:
            elements.append(Paragraph('Estadísticas del Análisis', heading))
            stats_data = [
                ['Métrica', 'Valor'],
                ['Líneas analizadas',    str(stats.get('lineas', 0))],
                ['Total de tokens',      str(stats.get('total_tokens', 0))],
                ['Identificadores',      str(stats.get('identificadores', 0))],
                ['Errores léxicos',      str(stats.get('errores', 0))],
                ['Tiempo de análisis',   f"{stats.get('tiempo_total_ms', 0)} ms"],
            ]
            tbl = Table(stats_data)
            tbl.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a5f')),
                ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
                ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID',       (0,0), (-1,-1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0,1), (-1,-1),
                 [colors.HexColor('#f8f9fa'), colors.white]),
            ]))
            elements.append(tbl)
            elements.append(Spacer(1, 1*cm))

        # Tokens
        tokens = data.get('tokens', [])
        if tokens:
            elements.append(PageBreak())
            elements.append(Paragraph('Tabla de Tokens', heading))
            token_data = [['#', 'Línea', 'Lexema', 'Token', 'Categoría']]
            for t in tokens[:100]:  # Max 100 para PDF
                token_data.append([
                    str(t.get('numero','')), str(t.get('linea','')),
                    t.get('lexema',''), t.get('token',''), t.get('categoria','')
                ])
            tbl = Table(token_data, repeatRows=1)
            tbl.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a5f')),
                ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
                ('GRID',       (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE',   (0,0), (-1,-1), 8),
                ('ROWBACKGROUNDS', (0,1), (-1,-1),
                 [colors.HexColor('#f8f9fa'), colors.white]),
            ]))
            elements.append(tbl)

        doc.build(elements)
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf',
                         as_attachment=True, download_name='reporte_completo.pdf')
    except Exception as e:
        return jsonify({'error': f'Error generando reporte: {e}'}), 500


# ─────────────────────────────────────────────────────────────────────────────
# Punto de entrada
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 60)
    print("  Analizador Léxico y Sintáctico para Python")
    print("  Universidad Mariano Gálvez — Compiladores")
    print("  http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
