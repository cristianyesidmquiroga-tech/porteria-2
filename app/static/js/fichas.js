// Extraido de fichas.html: la CSP ya no admite scripts inline.

    (function () {
        const modal = document.getElementById('modal-editar-ficha');
        const formulario = document.getElementById('form-editar-ficha');
        let ultimoBoton = null;

        function abrir(boton) {
            ultimoBoton = boton;
            formulario.action = '/usuarios/admin/fichas/' + boton.dataset.id + '/editar';
            document.getElementById('editar-numero').value = boton.dataset.numero;
            document.getElementById('editar-programa').value = boton.dataset.programa;
            document.getElementById('editar-fecha').value = boton.dataset.fecha;
            modal.style.display = 'flex';
            modal.setAttribute('aria-hidden', 'false');
            // El foco entra al diálogo y vuelve al botón al cerrar: sin esto,
            // quien navega con teclado sigue "detrás" del modal.
            document.getElementById('editar-numero').focus();
        }

        function cerrar() {
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
            if (ultimoBoton) ultimoBoton.focus();
        }

        document.querySelectorAll('.btn-editar-ficha').forEach(function (boton) {
            boton.addEventListener('click', function () { abrir(boton); });
        });
        document.getElementById('cancelar-editar-ficha').addEventListener('click', cerrar);
        modal.addEventListener('click', function (evento) {
            if (evento.target === modal) cerrar();
        });
        document.addEventListener('keydown', function (evento) {
            if (evento.key === 'Escape' && modal.style.display === 'flex') cerrar();
        });

        // Atrapa el tabulador dentro del diálogo mientras está abierto.
        modal.addEventListener('keydown', function (evento) {
            if (evento.key !== 'Tab') return;
            const focosables = modal.querySelectorAll('input, button');
            const primero = focosables[0];
            const ultimo = focosables[focosables.length - 1];
            if (evento.shiftKey && document.activeElement === primero) {
                evento.preventDefault();
                ultimo.focus();
            } else if (!evento.shiftKey && document.activeElement === ultimo) {
                evento.preventDefault();
                primero.focus();
            }
        });
    })();
