// El token CSRF llega por data-* porque la CSP prohibe scripts inline.
const CSRF = document.currentScript.dataset.csrf;

    async function revisar(id, decision, motivo) {
        const respuesta = await fetch(`/usuarios/api/admin/fotos/${id}/revisar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
            body: JSON.stringify({ decision: decision, motivo: motivo || '' })
        });
        const datos = await respuesta.json();
        if (datos.status === 'success') {
            showToast('Listo', datos.message, 'success');
            // El contador del filtro y el del menú lateral deben reflejar de
            // inmediato lo que queda por revisar.
            const contador = document.getElementById('contador-pendientes');
            if (contador) contador.textContent = datos.pendientes ? `(${datos.pendientes})` : '';
            const insignia = document.querySelector('.sidebar-nav a[href*="admin/fotos"] span:last-child');
            if (insignia && insignia.getAttribute('aria-label')) {
                if (datos.pendientes) { insignia.textContent = datos.pendientes; }
                else { insignia.remove(); }
            }
            const tarjeta = document.getElementById('tarjeta-' + id);
            if (tarjeta) {
                tarjeta.style.transition = 'opacity .3s';
                tarjeta.style.opacity = '0';
                setTimeout(() => tarjeta.remove(), 320);
            }
        } else {
            showToast('Atención', datos.message || 'No se pudo registrar', 'danger');
        }
    }

    document.querySelectorAll('.btn-aprobar').forEach(btn => {
        btn.addEventListener('click', async () => {
            btn.disabled = true;
            await revisar(btn.dataset.id, 'aprobar');
        });
    });

    const modal = document.getElementById('modal-rechazo');
    const campoMotivo = document.getElementById('motivo-rechazo');
    let idEnRevision = null;

    document.querySelectorAll('.btn-rechazar').forEach(btn => {
        btn.addEventListener('click', () => {
            idEnRevision = btn.dataset.id;
            document.getElementById('rechazo-persona').textContent =
                'Se le avisará por correo a ' + btn.dataset.nombre + '.';
            campoMotivo.value = '';
            document.getElementById('motivos-frecuentes').value = '';
            modal.style.display = 'flex';
            campoMotivo.focus();
        });
    });

    document.getElementById('motivos-frecuentes').addEventListener('change', (e) => {
        if (e.target.value) campoMotivo.value = e.target.value;
    });

    document.getElementById('rechazo-cancelar').addEventListener('click', () => {
        modal.style.display = 'none';
        idEnRevision = null;
    });

    document.getElementById('rechazo-confirmar').addEventListener('click', async () => {
        const motivo = campoMotivo.value.trim();
        if (!motivo) {
            showToast('Falta el motivo', 'Sin motivo la persona no sabrá qué corregir.', 'warning');
            campoMotivo.focus();
            return;
        }
        modal.style.display = 'none';
        await revisar(idEnRevision, 'rechazar', motivo);
        idEnRevision = null;
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            modal.style.display = 'none';
            idEnRevision = null;
        }
    });
