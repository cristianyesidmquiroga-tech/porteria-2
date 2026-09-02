// Extraido de register.html: la CSP ya no admite scripts inline.

// El registro público ahora es exclusivamente para Aprendices
// Las funciones de toggle quedan inactivas para el usuario final
    // Muestra el formato esperado según el tipo elegido, para que la persona
    // lo corrija antes de enviar y no después de un error del servidor.
    (function () {
        const selector = document.getElementById('tipo_documento');
        const pista = document.getElementById('formato-doc-registro');
        if (!selector || !pista) return;
        const actualizar = () => {
            const opcion = selector.options[selector.selectedIndex];
            pista.textContent = opcion ? opcion.dataset.formato || '' : '';
        };
        selector.addEventListener('change', actualizar);
        actualizar();
    })();
