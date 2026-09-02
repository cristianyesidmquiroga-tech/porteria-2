/**
 * Recorrido guiado de primer ingreso.
 *
 * Escrito a mano en lugar de usar una libreria de tours (driver.js, intro.js):
 * la CSP del sitio restringe los origenes de scripts y no queremos sumar otra
 * dependencia de CDN por una superposicion y un globo de texto.
 *
 * Se lanza solo en "Mi Perfil" la primera vez que la persona entra
 * (tutorial_visto en falso), o cuando llega con ?tutorial=1 desde la version
 * en texto. Al terminar o saltar, avisa al servidor para no repetirse.
 */
(function () {
    'use strict';

    // El propio <script> lleva la configuracion en data-*: asi la plantilla
    // no necesita un bloque JSON aparte y el archivo queda cacheable.
    var script = document.currentScript;
    if (!script) { return; }

    var config = {
        visto: script.dataset.tutorialVisto === 'true',
        enPerfil: script.dataset.enPerfil === 'true',
        urlCompletar: script.dataset.urlCompletar,
        urlTexto: script.dataset.urlTexto,
        csrf: script.dataset.csrf
    };

    // Reducir movimiento: sin desplazamiento suave ni transiciones.
    var reducirMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ------------------------------------------------------------------ */
    /* Pasos del recorrido. Si un selector no existe o esta oculto en la  */
    /* pagina (ej. sidebar plegado en movil, botones de equipos que un    */
    /* celador no tiene), el paso se salta sin romper el recorrido.       */
    /* ------------------------------------------------------------------ */
    var PASOS = [
        {
            selector: null, // paso de bienvenida, centrado, sin resaltar nada
            titulo: '¡Bienvenido al sistema de acceso del SENA!',
            texto: 'Este recorrido te muestra en un minuto lo que necesitas ' +
                   'hacer para activar tu carnet digital y poder entrar al ' +
                   'centro con tu código de barras. Puedes avanzar con el botón ' +
                   '"Continuar" o con la tecla Enter, y salir cuando quieras ' +
                   'con "Saltar" o la tecla Escape.'
        },
        {
            selector: '.profile-quick-actions .gradient-blue',
            titulo: '1. Completa tu información',
            texto: 'Con este botón abres el formulario de tus datos: tipo y ' +
                   'número de documento, tipo de sangre, y si eres aprendiz ' +
                   'también tu programa y tu ficha. Sin estos datos el carnet ' +
                   'no se puede activar.'
        },
        {
            selector: '.profile-quick-actions .gradient-blue',
            titulo: '2. Sube tu foto',
            texto: 'En ese mismo formulario subes tu foto de perfil. Debe ' +
                   'salir solo tu rostro, despejado (sin gorra ni ' +
                   'mascarilla; gafas sí se permiten), con buena luz, de ' +
                   'frente y de cerca. En portería el celador la compara ' +
                   'contigo para dejarte entrar.'
        },
        {
            selector: '.carnet-oficial',
            titulo: '3. Tu carnet digital',
            texto: 'Este es tu carnet institucional. Se completa solo a ' +
                   'medida que llenas tus datos. Tu foto la revisa un asesor: ' +
                   'hasta que la apruebe, el carnet y el código de barras ' +
                   'permanecen bloqueados.'
        },
        {
            selector: '.carnet-of-barras',
            titulo: '4. Tu código de barras de acceso',
            texto: 'Aquí aparecerá tu código de barras cuando tu perfil esté ' +
                   'completo y tu foto aprobada. Es el que presentas al ' +
                   'escáner de portería para entrar y salir del centro.'
        },
        {
            selector: '#btn-add-equipo',
            titulo: '5. Registra tus equipos',
            texto: 'Si vas a entrar con portátil o tablet, regístralo aquí ' +
                   'antes de traerlo: nombre, tipo y número de serial. El ' +
                   'celador marca cuáles traes al entrar y al salir.'
        },
        {
            selector: 'a[href*="/usuarios/ayuda"]',
            titulo: '6. Centro de Ayuda',
            texto: 'Si algo falla (te rechazan la foto, el código de barras no aparece, tu ' +
                   'ficha está mal), aquí están las respuestas a las dudas ' +
                   'más comunes.'
        },
        {
            selector: 'a[href*="/usuarios/mensajes"]',
            titulo: '7. Mensajes con un asesor',
            texto: 'Y si la respuesta no está en el Centro de Ayuda, por ' +
                   'aquí hablas directamente con un asesor sin tener que ' +
                   'buscar a nadie en portería.'
        },
        {
            selector: null,
            titulo: '¡Listo!',
            texto: 'Eso es todo. Recuerda el orden: completa tus datos, sube ' +
                   'tu foto, espera la aprobación y usa tu código de barras en portería. ' +
                   'Mientras tu perfil esté incompleto verás un botón para ' +
                   'releer este tutorial con ejemplos, en el aviso rojo de ' +
                   'arriba.'
        }
    ];

    /* ------------------------------------------------------------------ */
    /* Estilos del recorrido, inyectados desde aqui para que el tutorial   */
    /* sea un solo archivo autocontenido.                                  */
    /* ------------------------------------------------------------------ */
    var CSS = '' +
        '.tut-resaltado{position:absolute;z-index:10000;border-radius:12px;' +
        // La "oscuridad" alrededor es la sombra gigante de este recuadro:
        // un solo elemento resalta el objetivo y atenua todo lo demas.
        'box-shadow:0 0 0 9999px rgba(0,0,0,.62);pointer-events:none;' +
        'border:2px solid #39A900;}' +
        '.tut-resaltado.tut-anim{transition:top .25s ease,left .25s ease,' +
        'width .25s ease,height .25s ease;}' +
        '.tut-globo{position:absolute;z-index:10001;max-width:340px;' +
        'width:calc(100vw - 32px);background:#fff;color:#1c2733;' +
        'border-radius:14px;padding:1.1rem 1.25rem;' +
        'box-shadow:0 12px 40px rgba(0,0,0,.35);font-family:inherit;}' +
        '@media (prefers-color-scheme:dark){}' + /* el tema lo maneja data-theme */
        '[data-theme="dark"] .tut-globo{background:#1e2a36;color:#eef3f7;}' +
        '.tut-globo h2{margin:0 0 .5rem 0;font-size:1.02rem;color:#39A900;}' +
        '.tut-globo p{margin:0 0 1rem 0;font-size:.9rem;line-height:1.55;}' +
        '.tut-progreso{font-size:.75rem;opacity:.7;margin-bottom:.35rem;}' +
        '.tut-acciones{display:flex;gap:.5rem;justify-content:flex-end;flex-wrap:wrap;}' +
        '.tut-btn{border:none;border-radius:8px;padding:.5rem .9rem;' +
        'font-size:.85rem;font-weight:600;cursor:pointer;font-family:inherit;}' +
        '.tut-btn-primario{background:#39A900;color:#fff;}' +
        '.tut-btn-secundario{background:transparent;color:inherit;' +
        'border:1px solid rgba(128,128,128,.45);}' +
        '.tut-btn:hover{filter:brightness(1.08);}' +
        '.tut-btn:active{transform:translateY(1px);}' +
        '.tut-btn:disabled{opacity:.45;cursor:not-allowed;}' +
        // Foco visible por teclado en TODOS los botones del globo.
        '.tut-btn:focus-visible{outline:3px solid #39A900;outline-offset:2px;}' +
        '.tut-globo a{color:#39A900;font-weight:600;}' +
        '.tut-globo a:focus-visible{outline:3px solid #39A900;outline-offset:2px;}' +
        '@media (prefers-reduced-motion:reduce){.tut-resaltado.tut-anim{transition:none;}}';

    var estado = {
        activo: false,
        indice: 0,
        pasos: [],
        resaltado: null,
        globo: null,
        vivo: null,          // region aria-live que anuncia cada paso
        focoPrevio: null     // a donde devolver el foco al salir
    };

    function elementoUtilizable(selector) {
        if (!selector) { return true; } // pasos sin objetivo siempre valen
        var el = document.querySelector(selector);
        if (!el) { return false; }
        var caja = el.getBoundingClientRect();
        // Sin tamano (display:none) no hay nada que resaltar. Y si esta fuera
        // del viewport en horizontal (el sidebar plegado en movil vive en
        // x negativa), tampoco: el scroll vertical no puede traerlo a la vista.
        return caja.width > 0 && caja.height > 0 &&
               caja.right > 0 && caja.left < window.innerWidth;
    }

    function marcarComoVisto() {
        // sendBeacon no permite cabeceras, asi que se usa fetch con keepalive:
        // el aviso llega aunque la persona cierre la pestana justo despues.
        try {
            fetch(config.urlCompletar, {
                method: 'POST',
                keepalive: true,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': config.csrf
                }
            }).catch(function () { /* sin red no pasa nada: reaparecera */ });
        } catch (e) { /* idem */ }
    }

    function crearInterfaz() {
        var estilo = document.createElement('style');
        estilo.id = 'tut-estilos';
        estilo.textContent = CSS;
        document.head.appendChild(estilo);

        estado.resaltado = document.createElement('div');
        estado.resaltado.className = 'tut-resaltado' + (reducirMovimiento ? '' : ' tut-anim');
        estado.resaltado.setAttribute('aria-hidden', 'true');

        estado.globo = document.createElement('div');
        estado.globo.className = 'tut-globo';
        estado.globo.setAttribute('role', 'dialog');
        estado.globo.setAttribute('aria-modal', 'true');
        estado.globo.setAttribute('aria-labelledby', 'tut-titulo');
        estado.globo.setAttribute('aria-describedby', 'tut-texto');

        // Region separada del globo: anuncia el contenido de cada paso a los
        // lectores de pantalla sin depender de a donde se mueva el foco.
        estado.vivo = document.createElement('div');
        estado.vivo.setAttribute('aria-live', 'polite');
        estado.vivo.style.cssText = 'position:absolute;width:1px;height:1px;' +
            'overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;';

        document.body.appendChild(estado.resaltado);
        document.body.appendChild(estado.globo);
        document.body.appendChild(estado.vivo);

        document.addEventListener('keydown', alTeclear, true);
    }

    function destruirInterfaz() {
        document.removeEventListener('keydown', alTeclear, true);
        ['tut-estilos'].forEach(function (id) {
            var el = document.getElementById(id);
            if (el) { el.remove(); }
        });
        [estado.resaltado, estado.globo, estado.vivo].forEach(function (el) {
            if (el) { el.remove(); }
        });
        estado.resaltado = estado.globo = estado.vivo = null;
    }

    function terminar(motivo) {
        if (!estado.activo) { return; }
        estado.activo = false;
        destruirInterfaz();
        marcarComoVisto();
        // Devolver el foco a donde estaba antes de abrir el recorrido.
        if (estado.focoPrevio && document.contains(estado.focoPrevio)) {
            estado.focoPrevio.focus();
        }
    }

    function alTeclear(evento) {
        if (!estado.activo) { return; }
        if (evento.key === 'Escape') {
            evento.preventDefault();
            terminar('salto');
            return;
        }
        // Enter activa el control con foco (o avanza si el foco quedo fuera).
        // Se gestiona a mano y con preventDefault en vez de confiar en la
        // activacion nativa del navegador, para que no dispare dos veces.
        if (evento.key === 'Enter') {
            evento.preventDefault();
            var conFoco = document.activeElement;
            if (estado.globo.contains(conFoco) &&
                    (conFoco.tagName === 'BUTTON' || conFoco.tagName === 'A')) {
                conFoco.click();
            } else {
                var continuar = estado.globo.querySelector('#tut-continuar');
                if (continuar) { continuar.click(); }
            }
            return;
        }
        // Trampa de foco: Tab circula solo entre los controles del globo.
        if (evento.key === 'Tab') {
            var focables = estado.globo.querySelectorAll('button, a[href]');
            if (!focables.length) { return; }
            var primero = focables[0];
            var ultimo = focables[focables.length - 1];
            if (evento.shiftKey && document.activeElement === primero) {
                evento.preventDefault();
                ultimo.focus();
            } else if (!evento.shiftKey && document.activeElement === ultimo) {
                evento.preventDefault();
                primero.focus();
            } else if (!estado.globo.contains(document.activeElement)) {
                // El foco se escapo del dialogo (ej. clic fuera): traerlo.
                evento.preventDefault();
                primero.focus();
            }
        }
    }

    function posicionarSobre(paso) {
        var margen = 8;
        if (!paso.selector) {
            // Paso sin objetivo: sin recuadro (la sombra oscurece todo), y
            // el globo centrado en pantalla.
            estado.resaltado.style.border = 'none';
            estado.resaltado.style.top = (window.scrollY + window.innerHeight / 2) + 'px';
            estado.resaltado.style.left = (window.scrollX + window.innerWidth / 2) + 'px';
            estado.resaltado.style.width = '0px';
            estado.resaltado.style.height = '0px';
            estado.globo.style.top = (window.scrollY + window.innerHeight / 2) + 'px';
            estado.globo.style.left = '50%';
            estado.globo.style.transform = 'translate(-50%,-50%)';
            return;
        }
        var el = document.querySelector(paso.selector);
        el.scrollIntoView({
            behavior: reducirMovimiento ? 'auto' : 'smooth',
            block: 'center'
        });
        var caja = el.getBoundingClientRect();
        var top = caja.top + window.scrollY;
        var left = caja.left + window.scrollX;
        estado.resaltado.style.border = '';
        estado.resaltado.style.top = (top - margen) + 'px';
        estado.resaltado.style.left = (left - margen) + 'px';
        estado.resaltado.style.width = (caja.width + margen * 2) + 'px';
        estado.resaltado.style.height = (caja.height + margen * 2) + 'px';

        // Globo debajo del objetivo si cabe; si no, encima.
        estado.globo.style.transform = 'none';
        var altoGlobo = estado.globo.offsetHeight || 180;
        var debajo = caja.bottom + margen * 2 + altoGlobo < window.innerHeight;
        estado.globo.style.top = debajo
            ? (top + caja.height + margen * 2) + 'px'
            : Math.max(window.scrollY + 8, top - altoGlobo - margen * 2) + 'px';
        estado.globo.style.left = Math.max(16,
            Math.min(left, window.scrollX + window.innerWidth - 360)) + 'px';
    }

    function pintarPaso() {
        var paso = estado.pasos[estado.indice];
        var total = estado.pasos.length;
        var esUltimo = estado.indice === total - 1;

        estado.globo.innerHTML =
            '<div class="tut-progreso">Paso ' + (estado.indice + 1) + ' de ' + total + '</div>' +
            '<h2 id="tut-titulo"></h2>' +
            '<p id="tut-texto"></p>' +
            (esUltimo && config.urlTexto
                ? '<p style="font-size:.82rem;margin-top:-.4rem;">También puedes ' +
                  '<a href="' + config.urlTexto + '" id="tut-enlace-texto">leer el ' +
                  'tutorial completo con ejemplos</a>.</p>'
                : '') +
            '<div class="tut-acciones">' +
            '<button type="button" class="tut-btn tut-btn-secundario" id="tut-saltar">Saltar</button>' +
            '<button type="button" class="tut-btn tut-btn-secundario" id="tut-anterior"' +
            (estado.indice === 0 ? ' disabled' : '') + '>Anterior</button>' +
            '<button type="button" class="tut-btn tut-btn-primario" id="tut-continuar">' +
            (esUltimo ? 'Finalizar' : 'Continuar') + '</button>' +
            '</div>';

        // textContent y no innerHTML para los textos: nada interpretable.
        estado.globo.querySelector('#tut-titulo').textContent = paso.titulo;
        estado.globo.querySelector('#tut-texto').textContent = paso.texto;
        estado.vivo.textContent = 'Paso ' + (estado.indice + 1) + ' de ' + total +
            '. ' + paso.titulo + '. ' + paso.texto;

        estado.globo.querySelector('#tut-saltar')
            .addEventListener('click', function () { terminar('salto'); });
        estado.globo.querySelector('#tut-anterior')
            .addEventListener('click', function () { mover(-1); });
        estado.globo.querySelector('#tut-continuar')
            .addEventListener('click', function () {
                if (esUltimo) { terminar('fin'); } else { mover(1); }
            });

        posicionarSobre(paso);
        // El foco entra al boton principal: Enter avanza de inmediato.
        estado.globo.querySelector('#tut-continuar').focus();
    }

    function mover(delta) {
        estado.indice = Math.min(Math.max(estado.indice + delta, 0),
                                 estado.pasos.length - 1);
        pintarPaso();
    }

    function iniciar() {
        if (estado.activo) { return; }
        // Filtrar aqui (y no al definir PASOS) porque la visibilidad de un
        // elemento puede cambiar entre cargas: sidebar plegado, sin permiso
        // de equipos, etc.
        estado.pasos = PASOS.filter(function (p) { return elementoUtilizable(p.selector); });
        if (!estado.pasos.length) { return; }
        estado.activo = true;
        estado.indice = 0;
        estado.focoPrevio = document.activeElement;
        crearInterfaz();
        pintarPaso();
    }

    // Reaccionar a cambios de tamano reposicionando el paso actual.
    window.addEventListener('resize', function () {
        if (estado.activo) { posicionarSobre(estado.pasos[estado.indice]); }
    });

    function alCargar() {
        var forzado = new URLSearchParams(window.location.search).get('tutorial') === '1';
        if (config.enPerfil && (forzado || !config.visto)) {
            // Pequena espera: las animaciones de entrada de la pagina mueven
            // los elementos y el recuadro quedaria descolocado si se mide antes.
            setTimeout(iniciar, reducirMovimiento ? 0 : 450);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', alCargar);
    } else {
        alCargar();
    }
})();
