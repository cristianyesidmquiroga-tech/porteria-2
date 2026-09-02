// Hilo de mensajes. Externo por la CSP; la ruta de envio y el token
// CSRF llegan por data-*.
const CFG = document.currentScript.dataset;

    // El hilo arranca abajo, en lo más reciente.
    const hilo = document.getElementById('hilo');
    if (hilo) hilo.scrollTop = hilo.scrollHeight;

    const btnAdmin = document.getElementById('btn-admin-enviar');
    if (btnAdmin) {
        btnAdmin.addEventListener('click', async () => {
            const campo = document.getElementById('texto-admin');
            const texto = campo.value.trim();
            if (!texto) {
                showToast('Falta el mensaje', 'Escribe algo antes de enviar.', 'warning');
                campo.focus();
                return;
            }
            btnAdmin.disabled = true;
            try {
                const respuesta = await fetch(CFG.urlEnviar, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CFG.csrf },
                    body: JSON.stringify({ texto: texto })
                });
                const datos = await respuesta.json();
                if (datos.status === 'success') {
                    showToast('Enviado', datos.message, 'success');
                    setTimeout(() => window.location.reload(), 700);
                } else {
                    showToast('Atención', datos.message, 'danger');
                    btnAdmin.disabled = false;
                }
            } catch (error) {
                showToast('Error', 'No se pudo enviar el mensaje.', 'danger');
                btnAdmin.disabled = false;
            }
        });
    }
