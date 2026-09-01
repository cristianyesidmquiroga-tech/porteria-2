// Verificacion de acceso. Externo por la CSP sin unsafe-inline.
    document.addEventListener('DOMContentLoaded', function() {
        const formEntrada = document.getElementById('form-entrada');
        if (formEntrada) {
            formEntrada.addEventListener('submit', function() {
                const checked = document.querySelectorAll('.equipo-checkbox:checked');
                const container = document.getElementById('equipos-entrada');
                container.innerHTML = '';
                checked.forEach(cb => {
                    container.innerHTML += `<input type="hidden" name="equipos_ids" value="${cb.value}">`;
                });
            });
        }

        const formSalida = document.getElementById('form-salida');
        if (formSalida) {
            formSalida.addEventListener('submit', function() {
                const checked = document.querySelectorAll('.equipo-checkbox:checked');
                const container = document.getElementById('equipos-salida');
                container.innerHTML = '';
                checked.forEach(cb => {
                    container.innerHTML += `<input type="hidden" name="equipos_ids" value="${cb.value}">`;
                });
            });
        }
    });

// El boton "Volver al Escaner" antes llevaba onclick inline.
document.addEventListener('DOMContentLoaded', () => {
    const volver = document.getElementById('btn-volver-atras');
    if (volver) volver.addEventListener('click', () => window.history.back());
});
