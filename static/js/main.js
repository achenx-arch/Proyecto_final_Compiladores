/**
 * CompilerStudio — Main JavaScript
 * Maneja: editor, análisis AJAX, renderizado de resultados, exportaciones
 */

'use strict';

// ════════════════════════════════════════════════════════
// ESTADO GLOBAL
// ════════════════════════════════════════════════════════
const State = {
    tokens:      [],
    symbols:     [],
    lexErrors:   [],
    synErrors:   [],
    derivations: [],
    stats:       {},
    dotSource:   '',
    treePngB64:  null,
    first:       {},
    follow:      {},
    ll1Table:    {},
    grammar:     {},
};

// ════════════════════════════════════════════════════════
// MERMAID INIT
// ════════════════════════════════════════════════════════
mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    themeVariables: {
        darkMode: true,
        background: '#1c2128',
        primaryColor: '#1e3a5f',
        primaryTextColor: '#e6edf3',
        lineColor: '#8b949e',
        secondaryColor: '#2d6a4f',
        tertiaryColor: '#21262d',
    },
    flowchart: { curve: 'basis', htmlLabels: true },
    stateDiagram: { htmlLabels: false },
});

// ════════════════════════════════════════════════════════
// CÓDIGO DE EJEMPLO
// ════════════════════════════════════════════════════════
const EXAMPLE_CODE = `# Programa de ejemplo — Analizador Python
# Variables básicas
edad = 20
nombre = "Juan"
precio = 15.99

# Condicional
if edad >= 18:
    print(nombre)

# Bucle while
contador = 0
while contador < 5:
    contador = contador + 1

# Definición de función
def calcular(x, y):
    resultado = x + y
    return resultado

# Llamada con errores léxicos intencionales para demo
# valor = @precio + 10   ← descomenta para ver error léxico
`;

// ════════════════════════════════════════════════════════
// DOM READY
// ════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    initEditor();
    initSidebar();
    initButtons();
    // NO renderizar Mermaid aquí: las secciones de diagramas están ocultas
    // (display:none) al cargar y Mermaid fallaría al medir el texto.
    // El render se dispara al mostrar cada sección (ver showSection()).
});

// ════════════════════════════════════════════════════════
// EDITOR DE CÓDIGO
// ════════════════════════════════════════════════════════
function initEditor() {
    const editor      = document.getElementById('codeEditor');
    const lineNumbers = document.getElementById('lineNumbers');
    const charCount   = document.getElementById('charCount');
    const lineCount   = document.getElementById('lineCount');

    if (!editor) return;

    // Actualizar numeración de líneas y contadores
    function updateEditor() {
        const lines = editor.value.split('\n');
        const nums  = lines.map((_, i) => i + 1).join('\n');
        lineNumbers.textContent = nums;
        charCount.textContent   = editor.value.length;
        lineCount.textContent   = lines.length;
        // Sincronizar scroll
        lineNumbers.scrollTop = editor.scrollTop;
    }

    editor.addEventListener('input',  updateEditor);
    editor.addEventListener('scroll', () => {
        lineNumbers.scrollTop = editor.scrollTop;
    });

    // Tab key → insertar 4 espacios
    editor.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = editor.selectionStart;
            const end   = editor.selectionEnd;
            editor.value = editor.value.substring(0, start) + '    ' +
                           editor.value.substring(end);
            editor.selectionStart = editor.selectionEnd = start + 4;
            updateEditor();
        }
    });

    updateEditor();
}

// ════════════════════════════════════════════════════════
// SIDEBAR NAVIGATION
// ════════════════════════════════════════════════════════
function initSidebar() {
    const toggle   = document.getElementById('sidebarToggle');
    const sidebar  = document.getElementById('sidebar');
    const sections = document.querySelectorAll('.content-section');
    const links    = document.querySelectorAll('.sidebar-link');
    const title    = document.getElementById('currentSection');

    const sectionTitles = {
        'editor':     'Editor de Código',
        'tokens':     'Tabla de Tokens',
        'symbols':    'Tabla de Símbolos',
        'syntax':     'Árbol Sintáctico',
        'firstfollow':'PRIMEROS y SIGUIENTES',
        'll1':        'Tabla LL(1)',
        'derivation': 'Derivación Paso a Paso',
        'regex':      'Expresiones Regulares',
        'bnf':        'Notación BNF',
        'automata':   'Autómatas AFD',
        'conway':     'Diagramas de Conway',
        'errors':     'Reporte de Errores',
        'dashboard':  'Dashboard',
    };

    // Cambiar sección
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const sec = link.dataset.section;
            showSection(sec);
            links.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            if (title && sectionTitles[sec]) title.textContent = sectionTitles[sec];

            // En móvil cerrar sidebar
            if (window.innerWidth < 768) {
                sidebar.classList.add('collapsed');
            }
        });
    });

    // Toggle sidebar
    if (toggle) {
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    }
}

function showSection(name) {
    document.querySelectorAll('.content-section').forEach(s => {
        s.style.display = 'none';
    });
    const sec = document.getElementById(`sec-${name}`);
    if (sec) {
        sec.style.display = 'block';
        // Renderizar Mermaid solo cuando la sección ya es visible (ancho > 0)
        if (name === 'automata' || name === 'conway') {
            renderMermaidDiagrams(sec);
        }
    }
}

// ════════════════════════════════════════════════════════
// BOTONES
// ════════════════════════════════════════════════════════
function initButtons() {
    // Analizar
    ['btnAnalyze', 'btnAnalyze2'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.addEventListener('click', runAnalysis);
    });

    // Limpiar
    ['btnClear', 'btnClear2'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.addEventListener('click', clearEditor);
    });

    // Cargar ejemplo
    const exBtn = document.getElementById('btnLoadExample');
    if (exBtn) exBtn.addEventListener('click', loadExample);

    // Exportaciones
    document.getElementById('btnExportTokens')?.addEventListener('click', exportTokens);
    document.getElementById('btnExportSymbols')?.addEventListener('click', exportSymbols);
    document.getElementById('btnExportTokensD')?.addEventListener('click', exportTokens);
    document.getElementById('btnExportSymbolsD')?.addEventListener('click', exportSymbols);
    document.getElementById('btnExportReportD')?.addEventListener('click', exportReport);
    document.getElementById('btnExportTreeD')?.addEventListener('click', downloadTree);
    document.getElementById('btnDownloadTree')?.addEventListener('click', downloadTree);

    // Copiar DOT
    document.getElementById('btnCopyDot')?.addEventListener('click', () => {
        navigator.clipboard.writeText(State.dotSource || '');
        Swal.fire({ toast: true, position: 'top-end', icon: 'success',
                    title: '¡Copiado!', showConfirmButton: false, timer: 1500 });
    });

    // Filtro de tokens
    const filter    = document.getElementById('tokenFilter');
    const catFilter = document.getElementById('tokenCatFilter');
    if (filter)    filter.addEventListener('input',    filterTokens);
    if (catFilter) catFilter.addEventListener('change', filterTokens);
}

// ════════════════════════════════════════════════════════
// ANÁLISIS PRINCIPAL
// ════════════════════════════════════════════════════════
async function runAnalysis() {
    const editor = document.getElementById('codeEditor');
    const code   = editor?.value || '';

    if (!code.trim()) {
        Swal.fire({
            icon: 'warning', title: 'Editor vacío',
            text: 'Escribe o pega código Python antes de analizar.',
            background: '#1c2128', color: '#e6edf3',
            confirmButtonColor: '#58a6ff',
        });
        return;
    }

    // Mostrar overlay
    showLoading(true);
    setEditorStatus('Analizando...', 'warning');

    try {
        const response = await fetch('/analyze', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ code }),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        if (data.error) throw new Error(data.error);

        // Guardar en estado
        State.tokens      = data.tokens      || [];
        State.symbols     = data.symbol_table|| [];
        State.lexErrors   = data.lex_errors  || [];
        State.synErrors   = data.syn_errors  || [];
        State.derivations = data.derivations || [];
        State.stats       = data.stats       || {};
        State.dotSource   = data.dot_source  || '';
        State.treePngB64  = data.tree_png_b64|| null;
        State.first       = data.first       || {};
        State.follow      = data.follow      || {};
        State.ll1Table    = data.ll1_table   || {};
        State.grammar     = data.grammar     || {};

        // Renderizar todas las secciones
        renderTokens();
        renderSymbols();
        renderSyntaxTree();
        renderFirstFollow();
        renderLL1Table();
        renderDerivations();
        renderErrors();
        renderDashboard();

        // Estado
        const hasErrors = State.lexErrors.length + State.synErrors.length;
        if (hasErrors > 0) {
            setEditorStatus(`${hasErrors} error(es)`, 'danger');
        } else if (data.syn_success) {
            setEditorStatus('OK — Sin errores', 'success');
        } else {
            setEditorStatus('Análisis completado', 'secondary');
        }

        // Notificación
        const totalErrors = State.lexErrors.length + State.synErrors.length;
        Swal.fire({
            toast: true, position: 'top-end', icon: totalErrors ? 'warning' : 'success',
            title: totalErrors
                ? `Análisis completado con ${totalErrors} error(es)`
                : '¡Análisis completado sin errores!',
            showConfirmButton: false, timer: 2500,
            background: '#1c2128', color: '#e6edf3',
        });

        // Ir a sección tokens
        showSection('tokens');
        document.querySelectorAll('.sidebar-link').forEach(l => l.classList.remove('active'));
        document.querySelector('[data-section="tokens"]')?.classList.add('active');

    } catch (err) {
        setEditorStatus('Error', 'danger');
        Swal.fire({
            icon: 'error', title: 'Error en el análisis',
            text: err.message || 'Error desconocido',
            background: '#1c2128', color: '#e6edf3',
            confirmButtonColor: '#f85149',
        });
    } finally {
        showLoading(false);
    }
}

// ════════════════════════════════════════════════════════
// RENDERIZAR TOKENS
// ════════════════════════════════════════════════════════
function renderTokens() {
    const tbody = document.getElementById('tokensBody');
    if (!tbody) return;

    if (!State.tokens.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-muted text-center py-3">Sin tokens</td></tr>';
        return;
    }

    tbody.innerHTML = State.tokens.map(t => `
        <tr class="fade-in-up">
            <td class="text-muted">${t.numero}</td>
            <td>${t.linea}</td>
            <td>${t.columna}</td>
            <td><code style="color:#7ee787">${escHtml(t.lexema)}</code></td>
            <td><code style="color:#79c0ff">${escHtml(t.token)}</code></td>
            <td><span class="badge ${catBadge(t.categoria)}">${t.categoria}</span></td>
        </tr>`
    ).join('');
}

function filterTokens() {
    const text   = (document.getElementById('tokenFilter')?.value || '').toLowerCase();
    const cat    = (document.getElementById('tokenCatFilter')?.value || '');
    const tbody  = document.getElementById('tokensBody');
    if (!tbody) return;

    const filtered = State.tokens.filter(t => {
        const matchText = !text ||
            t.lexema.toLowerCase().includes(text) ||
            t.token.toLowerCase().includes(text);
        const matchCat  = !cat || t.categoria === cat;
        return matchText && matchCat;
    });

    if (!filtered.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-muted text-center py-3">Sin resultados</td></tr>';
        return;
    }

    tbody.innerHTML = filtered.map(t => `
        <tr>
            <td class="text-muted">${t.numero}</td>
            <td>${t.linea}</td>
            <td>${t.columna}</td>
            <td><code style="color:#7ee787">${escHtml(t.lexema)}</code></td>
            <td><code style="color:#79c0ff">${escHtml(t.token)}</code></td>
            <td><span class="badge ${catBadge(t.categoria)}">${t.categoria}</span></td>
        </tr>`
    ).join('');
}

function catBadge(cat) {
    const map = {
        'PALABRA_RESERVADA': 'badge-keyword',
        'IDENTIFICADOR':     'badge-identifier',
        'ENTERO':            'badge-number',
        'DECIMAL':           'badge-number',
        'CADENA':            'badge-string',
        'OPERADOR':          'badge-operator',
        'DELIMITADOR':       'badge-delimiter',
        'ERROR':             'badge-error',
    };
    return map[cat] || 'bg-secondary';
}

// ════════════════════════════════════════════════════════
// RENDERIZAR TABLA DE SÍMBOLOS
// ════════════════════════════════════════════════════════
function renderSymbols() {
    const tbody = document.getElementById('symbolsBody');
    if (!tbody) return;

    if (!State.symbols.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-muted text-center py-3">Sin símbolos</td></tr>';
        return;
    }

    const typeColors = {
        'funcion':          '#58a6ff',
        'clase':            '#bc8cff',
        'modulo':           '#ffa657',
        'variable':         '#7ee787',
        'variable_control': '#e3b341',
    };

    tbody.innerHTML = State.symbols.map(s => {
        const color = typeColors[s.tipo] || '#8b949e';
        return `<tr class="fade-in-up">
            <td><code style="color:#7ee787">${escHtml(s.nombre)}</code></td>
            <td><span style="color:${color};font-size:0.78rem">${s.tipo}</span></td>
            <td>${s.linea}</td>
            <td class="text-muted">${s.referencias}</td>
        </tr>`;
    }).join('');
}

// ════════════════════════════════════════════════════════
// RENDERIZAR ÁRBOL SINTÁCTICO
// ════════════════════════════════════════════════════════
async function renderSyntaxTree() {
    const container = document.getElementById('treeSvgContainer');
    const dotPre    = document.getElementById('dotSource');
    if (!container) return;

    if (dotPre) dotPre.textContent = State.dotSource || '// Sin DOT source';

    if (State.treePngB64) {
        // Mostrar PNG generado por Graphviz
        container.innerHTML = `
            <img src="data:image/png;base64,${State.treePngB64}"
                 class="img-fluid" alt="Árbol Sintáctico"
                 style="max-height:600px; border-radius:8px">`;
        return;
    }

    if (State.dotSource && typeof Viz !== 'undefined') {
        // Renderizar con Viz.js (Graphviz en el browser)
        try {
            container.innerHTML = '<div class="text-muted py-3">Renderizando árbol...</div>';
            const viz = await Viz.instance();
            const svg = await viz.renderString(State.dotSource, { format: 'svg' });
            container.innerHTML = svg;
            // Ajustar SVG
            const svgEl = container.querySelector('svg');
            if (svgEl) {
                svgEl.style.maxWidth  = '100%';
                svgEl.style.height    = 'auto';
            }
        } catch (e) {
            container.innerHTML = `<div class="text-danger py-3">
                <i class="fa-solid fa-triangle-exclamation me-2"></i>
                Error al renderizar árbol: ${e.message}
            </div>`;
        }
    } else if (State.dotSource) {
        container.innerHTML = `<div class="text-muted py-3">
            <i class="fa-solid fa-info-circle me-2"></i>
            Viz.js no disponible — ver código DOT abajo
        </div>`;
    } else {
        container.innerHTML = `<div class="text-muted py-3">
            <i class="fa-solid fa-tree fa-2x mb-2 d-block opacity-25"></i>
            Sin árbol generado
        </div>`;
    }
}

// ════════════════════════════════════════════════════════
// RENDERIZAR FIRST / FOLLOW + GRAMÁTICA
// ════════════════════════════════════════════════════════
function renderFirstFollow() {
    // PRIMEROS (FIRST)
    const firstBody = document.getElementById('firstBody');
    if (firstBody) {
        firstBody.innerHTML = Object.entries(State.first)
            .map(([nt, syms]) => `
                <tr>
                    <td><code style="color:#58a6ff">${escHtml(nt)}</code></td>
                    <td>${syms.map(s => `<span class="badge badge-operator me-1">${escHtml(s)}</span>`).join('')}</td>
                </tr>`
            ).join('') || '<tr><td colspan="2" class="text-muted text-center">Sin datos</td></tr>';
    }

    // SIGUIENTES (FOLLOW)
    const followBody = document.getElementById('followBody');
    if (followBody) {
        followBody.innerHTML = Object.entries(State.follow)
            .map(([nt, syms]) => `
                <tr>
                    <td><code style="color:#58a6ff">${escHtml(nt)}</code></td>
                    <td>${syms.map(s => `<span class="badge badge-number me-1">${escHtml(s)}</span>`).join('')}</td>
                </tr>`
            ).join('') || '<tr><td colspan="2" class="text-muted text-center">Sin datos</td></tr>';
    }

    // Gramática
    const gramDiv = document.getElementById('grammarDisplay');
    if (gramDiv) {
        gramDiv.innerHTML = Object.entries(State.grammar).map(([nt, prods]) => {
            const rules = prods.map((p, i) => {
                const arrow = i === 0 ? '::=' : '  |';
                const syms  = p.split(' ').map(s => {
                    if (s === 'ε') return `<span class="grammar-eps">ε</span>`;
                    if (s === s.toUpperCase() && !s.includes('_'))
                        return `<span class="grammar-term">${escHtml(s)}</span>`;
                    if (/^[A-Z_]+$/.test(s))
                        return `<span class="grammar-nt">${escHtml(s)}</span>`;
                    return `<span class="grammar-prod">${escHtml(s)}</span>`;
                }).join(' ');
                return `<div class="grammar-rule"><span class="grammar-nt">${nt}</span><span class="grammar-arrow">${arrow}</span><span class="grammar-prod">${syms}</span></div>`;
            }).join('');
            return rules;
        }).join('');
    }
}

// ════════════════════════════════════════════════════════
// RENDERIZAR TABLA LL(1)
// ════════════════════════════════════════════════════════
function renderLL1Table() {
    const container = document.getElementById('ll1TableContainer');
    if (!container) return;

    if (!Object.keys(State.ll1Table).length) {
        container.innerHTML = '<p class="text-muted text-center py-5">Sin datos</p>';
        return;
    }

    // Recopilar todos los terminales
    const terminals = new Set();
    Object.values(State.ll1Table).forEach(row => {
        Object.keys(row).forEach(t => terminals.add(t));
    });
    const termArr = Array.from(terminals).sort();
    const ntArr   = Object.keys(State.ll1Table).sort();

    let html = `<table class="table table-sm ll1-table">
        <thead><tr>
            <th class="ll1-nt-header">No-Terminal \\ Terminal</th>
            ${termArr.map(t => `<th>${escHtml(t)}</th>`).join('')}
        </tr></thead>
        <tbody>
            ${ntArr.map(nt => `
                <tr>
                    <td class="nt-col">${escHtml(nt)}</td>
                    ${termArr.map(t => {
                        const prod = State.ll1Table[nt]?.[t] || '';
                        return `<td class="${prod ? 'has-prod' : ''}" title="${escHtml(prod)}">${escHtml(prod) || ''}</td>`;
                    }).join('')}
                </tr>`
            ).join('')}
        </tbody>
    </table>`;

    container.innerHTML = html;
}

// ════════════════════════════════════════════════════════
// RENDERIZAR DERIVACIÓN
// ════════════════════════════════════════════════════════
function renderDerivations() {
    const tbody = document.getElementById('derivationBody');
    if (!tbody) return;

    if (!State.derivations.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-muted text-center py-3">Sin derivaciones</td></tr>';
        return;
    }

    tbody.innerHTML = State.derivations.map((d, i) => {
        let rowClass = '';
        if (d.produccion === 'ACEPTAR') rowClass = 'row-accept';
        else if (d.produccion?.startsWith('Error')) rowClass = 'row-error';
        else if (d.produccion?.startsWith('Emparejar')) rowClass = 'row-match';

        return `<tr class="${rowClass}">
            <td class="text-muted">${i + 1}</td>
            <td><code style="font-size:0.75rem;color:#79c0ff">${escHtml(d.pila || '')}</code></td>
            <td><code style="font-size:0.75rem;color:#7ee787">${escHtml(d.entrada || '')}</code></td>
            <td><small>${escHtml(d.produccion || '')}</small></td>
        </tr>`;
    }).join('');
}

// ════════════════════════════════════════════════════════
// RENDERIZAR ERRORES
// ════════════════════════════════════════════════════════
function renderErrors() {
    const lexDiv    = document.getElementById('lexErrors');
    const synDiv    = document.getElementById('synErrors');
    const lexCount  = document.getElementById('lexErrCount');
    const synCount  = document.getElementById('synErrCount');

    if (lexCount) lexCount.textContent = State.lexErrors.length;
    if (synCount) synCount.textContent = State.synErrors.length;

    if (lexDiv) {
        if (!State.lexErrors.length) {
            lexDiv.innerHTML = '<p class="text-muted"><i class="fa-solid fa-check-circle text-success me-2"></i>Sin errores léxicos</p>';
        } else {
            lexDiv.innerHTML = State.lexErrors.map(e => `
                <div class="error-card">
                    <div class="d-flex justify-content-between">
                        <strong class="text-danger"><i class="fa-solid fa-xmark me-2"></i>${escHtml(e.tipo)}</strong>
                        <span class="text-muted small">Línea ${e.linea} Col ${e.columna}</span>
                    </div>
                    <div class="mt-1">${escHtml(e.descripcion)}</div>
                    <div class="mt-1 text-muted small">Símbolo: <code>${escHtml(e.simbolo)}</code></div>
                </div>`
            ).join('');
        }
    }

    if (synDiv) {
        if (!State.synErrors.length) {
            synDiv.innerHTML = '<p class="text-muted"><i class="fa-solid fa-check-circle text-success me-2"></i>Sin errores sintácticos</p>';
        } else {
            synDiv.innerHTML = State.synErrors.map(e => `
                <div class="syn-error-card">
                    <div class="d-flex justify-content-between">
                        <strong class="text-warning"><i class="fa-solid fa-triangle-exclamation me-2"></i>${escHtml(e.tipo)}</strong>
                        <span class="text-muted small">Línea ${e.linea || '-'}</span>
                    </div>
                    <div class="mt-1">${escHtml(e.descripcion)}</div>
                    ${e.lexema ? `<div class="mt-1 text-muted small">Token: <code>${escHtml(e.lexema)}</code></div>` : ''}
                </div>`
            ).join('');
        }
    }
}

// ════════════════════════════════════════════════════════
// RENDERIZAR DASHBOARD
// ════════════════════════════════════════════════════════
function renderDashboard() {
    const s = State.stats;
    setKpi('kpiLines',       s.lineas         || 0);
    setKpi('kpiTokens',      s.total_tokens   || 0);
    setKpi('kpiIdentifiers', s.identificadores|| 0);
    setKpi('kpiErrors',      (State.lexErrors.length + State.synErrors.length));

    // Desglose por categoría
    const catDiv = document.getElementById('categoryBreakdown');
    if (catDiv) {
        const cats = {};
        State.tokens.forEach(t => {
            cats[t.categoria] = (cats[t.categoria] || 0) + 1;
        });
        const total = State.tokens.length || 1;
        const colors = {
            'PALABRA_RESERVADA': '#f85149',
            'IDENTIFICADOR':     '#58a6ff',
            'ENTERO':            '#ffa657',
            'DECIMAL':           '#ffa657',
            'CADENA':            '#3fb950',
            'OPERADOR':          '#bc8cff',
            'DELIMITADOR':       '#8b949e',
        };

        catDiv.innerHTML = Object.entries(cats)
            .sort((a, b) => b[1] - a[1])
            .map(([cat, count]) => {
                const pct   = Math.round((count / total) * 100);
                const color = colors[cat] || '#8b949e';
                return `<div class="cat-bar-item">
                    <div class="cat-bar-label">
                        <span>${cat}</span>
                        <span>${count} (${pct}%)</span>
                    </div>
                    <div class="cat-bar-track">
                        <div class="cat-bar-fill" style="width:${pct}%;background:${color}"></div>
                    </div>
                </div>`;
            }).join('');
    }

    // Métricas de tiempo
    const timeDiv = document.getElementById('timeMetrics');
    if (timeDiv) {
        timeDiv.innerHTML = `
            <div class="d-flex justify-content-between py-2 border-bottom" style="border-color:#30363d!important">
                <span class="text-muted">Tiempo de análisis</span>
                <strong>${s.tiempo_total_ms || 0} ms</strong>
            </div>
            <div class="d-flex justify-content-between py-2 border-bottom" style="border-color:#30363d!important">
                <span class="text-muted">Tokens por línea</span>
                <strong>${s.lineas ? Math.round((s.total_tokens||0) / s.lineas * 10)/10 : 0}</strong>
            </div>
            <div class="d-flex justify-content-between py-2">
                <span class="text-muted">Tasa de éxito léxico</span>
                <strong>${s.total_tokens
                    ? Math.round(((s.total_tokens - (State.lexErrors.length||0)) / s.total_tokens) * 100)
                    : 100}%</strong>
            </div>`;
    }
}

function setKpi(id, value) {
    const el = document.getElementById(id);
    if (!el) return;
    // Animación contadora
    const start = parseInt(el.textContent) || 0;
    const end   = parseInt(value) || 0;
    const steps = 20;
    const step  = (end - start) / steps;
    let current = start;
    let count   = 0;
    const interval = setInterval(() => {
        current += step;
        count++;
        el.textContent = Math.round(current);
        if (count >= steps) { el.textContent = end; clearInterval(interval); }
    }, 20);
}

// ════════════════════════════════════════════════════════
// MERMAID DIAGRAMS
// ════════════════════════════════════════════════════════
async function renderMermaidDiagrams(root = document) {
    const nodes = root.querySelectorAll('.mermaid');
    const pending = [];

    nodes.forEach(node => {
        // Respaldar el código fuente original la primera vez que se ve el nodo
        if (!node.dataset.mmdSrc) {
            node.dataset.mmdSrc = node.textContent.trim();
        }
        // Si ya tiene un SVG válido (no de error), no hay que volver a renderizar
        const yaRenderizado = node.dataset.processed === 'true' &&
                              node.querySelector('svg') &&
                              !node.textContent.includes('Syntax error');
        if (yaRenderizado) return;

        // (Re)preparar el nodo: restaurar la fuente y limpiar el estado previo
        node.removeAttribute('data-processed');
        node.innerHTML = node.dataset.mmdSrc;
        pending.push(node);
    });

    if (!pending.length) return;

    try {
        await mermaid.run({ nodes: pending });
    } catch (e) {
        console.warn('Mermaid render error:', e);
    }
}

// ════════════════════════════════════════════════════════
// EXPORTACIONES
// ════════════════════════════════════════════════════════
async function exportTokens() {
    if (!State.tokens.length) {
        return alertNoData('No hay tokens para exportar');
    }
    await postAndDownload('/export/tokens', { tokens: State.tokens }, 'tokens.pdf');
}

async function exportSymbols() {
    if (!State.symbols.length) {
        return alertNoData('No hay tabla de símbolos para exportar');
    }
    await postAndDownload('/export/symbols', { symbols: State.symbols }, 'tabla_simbolos.pdf');
}

async function exportReport() {
    if (!State.tokens.length) {
        return alertNoData('Ejecuta el análisis primero');
    }
    await postAndDownload('/export/report', {
        tokens:  State.tokens,
        symbols: State.symbols,
        stats:   State.stats,
        errors:  State.lexErrors,
    }, 'reporte_completo.pdf');
}

async function downloadTree() {
    if (!State.treePngB64 && !State.dotSource) {
        return alertNoData('No hay árbol generado');
    }
    if (State.treePngB64) {
        // Descargar desde endpoint
        window.location.href = '/tree/download';
    } else if (State.dotSource) {
        // Descargar DOT como texto
        const blob = new Blob([State.dotSource], { type: 'text/plain' });
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = 'arbol_sintactico.dot';
        a.click();
        URL.revokeObjectURL(url);
    }
}

async function postAndDownload(url, data, filename) {
    try {
        showLoading(true);
        const response = await fetch(url, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(data),
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const blob  = await response.blob();
        const bUrl  = URL.createObjectURL(blob);
        const a     = document.createElement('a');
        a.href      = bUrl;
        a.download  = filename;
        a.click();
        URL.revokeObjectURL(bUrl);
    } catch (e) {
        Swal.fire({
            icon: 'error', title: 'Error al exportar',
            text: e.message,
            background: '#1c2128', color: '#e6edf3',
        });
    } finally {
        showLoading(false);
    }
}

// ════════════════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════════════════
function clearEditor() {
    const editor = document.getElementById('codeEditor');
    if (editor) {
        editor.value = '';
        editor.dispatchEvent(new Event('input'));
    }
    setEditorStatus('Listo', 'secondary');
}

function loadExample() {
    const editor = document.getElementById('codeEditor');
    if (editor) {
        editor.value = EXAMPLE_CODE;
        editor.dispatchEvent(new Event('input'));
    }
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.toggle('d-none', !show);
    }
    const btns = ['btnAnalyze', 'btnAnalyze2'];
    btns.forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.disabled = show;
            btn.innerHTML = show
                ? '<span class="spinner-border spinner-border-sm me-1"></span>Analizando...'
                : '<i class="fa-solid fa-play me-1"></i>Analizar';
        }
    });
}

function setEditorStatus(text, type) {
    const badge = document.getElementById('editorStatus');
    if (!badge) return;
    badge.className = `badge bg-${type}`;
    badge.innerHTML = `<i class="fa-solid fa-circle me-1" style="font-size:0.5rem"></i>${text}`;
}

function alertNoData(msg) {
    Swal.fire({
        toast: true, position: 'top-end', icon: 'info',
        title: msg, showConfirmButton: false, timer: 2000,
        background: '#1c2128', color: '#e6edf3',
    });
}

function escHtml(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
