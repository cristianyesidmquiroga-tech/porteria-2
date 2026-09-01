// Pases de acceso. Fuera de la plantilla: la CSP ya no admite inline.
    function switchPaseTab(view) {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.getElementById('btn-tab-' + view).classList.add('active');
        document.getElementById('view-visitantes').style.display = (view === 'visitantes' ? 'block' : 'none');
        document.getElementById('view-vehiculos').style.display = (view === 'vehiculos' ? 'block' : 'none');
        document.getElementById('view-objetos').style.display = (view === 'objetos' ? 'block' : 'none');
    }

    const modalBarras = document.getElementById('modal-barras');
    const cajaBarras = document.getElementById('caja-barras');
    let ultimoBotonBarras = null;

    function abrirBarras(boton) {
        const origen = document.getElementById(boton.dataset.objetivo);
        if (!origen) return;
        ultimoBotonBarras = boton;
        document.getElementById('titulo-barras').textContent = boton.dataset.titulo || 'Pase de acceso';
        cajaBarras.innerHTML = origen.innerHTML;
        // El SVG llega sin ancho fijo: aquí se estira a todo lo que dé el
        // modal, porque cuanto más ancho es el código más fácil de escanear.
        const svg = cajaBarras.querySelector('svg');
        if (svg) { svg.style.width = '100%'; svg.style.height = '120px'; }
        modalBarras.style.display = 'flex';
        modalBarras.setAttribute('aria-hidden', 'false');
        document.getElementById('cerrar-barras').focus();
    }

    function cerrarBarras() {
        modalBarras.style.display = 'none';
        modalBarras.setAttribute('aria-hidden', 'true');
        cajaBarras.innerHTML = '';
        if (ultimoBotonBarras) ultimoBotonBarras.focus();
    }

    document.querySelectorAll('.boton-ver-barras').forEach(function (boton) {
        boton.addEventListener('click', function () { abrirBarras(boton); });
    });
    document.getElementById('cerrar-barras').addEventListener('click', cerrarBarras);
    document.getElementById('imprimir-barras').addEventListener('click', function () { window.print(); });
    modalBarras.addEventListener('click', function (e) { if (e.target === modalBarras) cerrarBarras(); });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && modalBarras.style.display === 'flex') cerrarBarras();
    });

// Pestanas: el nombre de la vista viaja en data-pestana.
document.querySelectorAll('[data-pestana]').forEach(b =>
    b.addEventListener('click', () => switchPaseTab(b.dataset.pestana)));
