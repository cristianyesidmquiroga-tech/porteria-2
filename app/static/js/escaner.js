// Escaner de porteria. Vive fuera de la plantilla porque la CSP ya no
// permite scripts inline; los dos valores que dependen del servidor
// (avatar de reserva y token CSRF) llegan por data-* en la etiqueta script.
const CONFIG_ESCANER = document.currentScript.dataset;
const AVATAR_GENERICO = CONFIG_ESCANER.avatarGenerico;
const CSRF_TOKEN = CONFIG_ESCANER.csrf;

    let html5QrCode;
    const scannerId = "reader";

    let currentCameraId = null;
    let availableCameras = [];

    // Recuadro de enfoque ancho y bajo. El anterior era cuadrado porque se
    // leian QR; un codigo de barras es una franja horizontal, y con recuadro
    // cuadrado el celador tiene que alejar el telefono hasta que las barras
    // quedan demasiado finas para el sensor.
    function recuadroBarras(anchoVista, altoVista) {
        const ancho = Math.floor(anchoVista * 0.9);
        const alto = Math.max(80, Math.floor(altoVista * 0.35));
        return { width: ancho, height: Math.min(alto, altoVista) };
    }

    async function startCamera() {
        const overlay = document.getElementById('camera-overlay');
        const diagMsg = document.getElementById('diag-msg');
        const powerBtn = document.querySelector('.btn-power-camera');
        
        if(location.protocol !== 'https:' && location.hostname !== 'localhost' && !location.hostname.startsWith('127.')) {
            diagMsg.innerHTML = "❌ <strong>Error de Seguridad:</strong> El navegador bloquea la cámara en conexiones HTTP externas.<br><br>Usa 'localhost' o activa HTTPS.";
            diagMsg.style.color = "#FF4B2B";
            powerBtn.style.display = 'none';
            return;
        }

        // Se limita el lector a CODE_128, que es la simbologia que emite el
        // carnet y los pases. Sin esta lista intenta todos los formatos en
        // cada fotograma y tarda mas en enganchar.
        if (!html5QrCode) {
            html5QrCode = new Html5Qrcode(scannerId, {
                formatsToSupport: [Html5QrcodeSupportedFormats.CODE_128],
                verbose: false
            });
        }
        
        try {
            availableCameras = await Html5Qrcode.getCameras();
            if (availableCameras && availableCameras.length > 0) {
                const backCamera = availableCameras.find(cam => cam.label.toLowerCase().includes('back') || cam.label.toLowerCase().includes('trasera'));
                currentCameraId = backCamera ? backCamera.id : availableCameras[0].id;

                const config = { fps: 20, qrbox: recuadroBarras };

                await html5QrCode.start(currentCameraId, config, onScanSuccess);
                
                overlay.classList.add('hidden');
                document.getElementById('laser').style.display = 'block';
                
                if (availableCameras.length > 1) {
                    document.getElementById('switch-cam-btn').style.display = 'inline-block';
                }

                showToast("Cámara Iniciada", "Puedes comenzar a escanear.", "success");
            } else {
                throw new Error("No se detectaron cámaras.");
            }
        } catch(err) {
            console.error("Camera fail:", err);
            diagMsg.innerHTML = "❌ <strong>Cámara no detectada:</strong> No pudimos conectar con ningún sensor de video.<br><br>1. Verifica los permisos.<br>2. Asegúrate de que ninguna otra app use la cámara.<br>3. Recarga (F5).";
            diagMsg.style.color = "#FF4B2B";
        }
    }

    async function switchCamera() {
        if (availableCameras.length < 2) return;
        
        const currentIndex = availableCameras.findIndex(cam => cam.id === currentCameraId);
        const nextIndex = (currentIndex + 1) % availableCameras.length;
        currentCameraId = availableCameras[nextIndex].id;

        showToast("Cambiando", "Conectando al siguiente sensor...", "info");
        
        try {
            await html5QrCode.stop();
            const config = { fps: 20, qrbox: recuadroBarras };
            await html5QrCode.start(currentCameraId, config, onScanSuccess);
            document.getElementById('laser').style.display = 'block';
        } catch (e) {
            showToast("Error", "No se pudo cambiar de cámara", "danger");
        }
    }

    async function onScanSuccess(decodedText) {
        document.getElementById('success-flash').classList.remove('hidden');
        document.getElementById('laser').style.display = 'none';
        
        try { await html5QrCode.stop(); } catch(e) {}
        
        setTimeout(() => {
            document.getElementById('success-flash').classList.add('hidden');
            processValidation(decodedText);
        }, 1000);
    }

    function toggleManual() {
        const form = document.getElementById('manual-form');
        form.style.display = form.style.display === 'none' ? 'block' : 'none';
        if(form.style.display === 'block') {
            document.getElementById('manualDoc').focus();
        }
    }

    function handleManualSubmit() {
        const val = document.getElementById('manualDoc').value;
        if(val) processValidation(val);
    }

    async function processValidation(doc) {
        showToast("Escaneando", "Analizando identidad de... " + doc, "info");
        
        try {
            const res = await fetch(`/porteria/api/verify/${encodeURIComponent(doc)}`);
            const data = await res.json();
            
            if(!data.found) {
                showToast("No Encontrado", "El documento o código no coincide con ningún perfil registrado.", "danger");
                resetUI();
                return;
            }

            document.querySelector('.scanner-view-container').style.display = 'none';
            document.getElementById('manual-trigger-group').style.display = 'none';
            const resUI = document.getElementById('scanner-result-ui');
            resUI.style.display = 'block';

            document.getElementById('res-nombre').textContent = data.nombre;
            document.getElementById('res-cargo').textContent = data.cargo || data.tipo;
            
            if (data.tipo === 'Vehiculo') {
                document.getElementById('res-photo').src = data.foto || AVATAR_GENERICO;
            } else {
                // El servidor siempre manda una URL valida (foto real o avatar
                // del cargo), asi que no hace falta construir ninguna de reserva
                // ni consultar un servicio externo.
                document.getElementById('res-photo').src = data.foto || AVATAR_GENERICO;
            }
            
            const pill = document.getElementById('res-status-pill');
            pill.textContent = "ESTADO ACTUAL: " + (data.status === 'Entrada' ? 'EN SEDE' : 'AFUERA');
            pill.className = "status-pill " + (data.status === 'Entrada' ? "status-entrada" : "status-afuera");

            // Warnings block
            const warnBox = document.getElementById('res-warnings');
            warnBox.innerHTML = '';
            warnBox.style.display = 'none';

            // Visitor duration logic
            if (data.tipo === 'Visitante' && data.status === 'Entrada') {
                warnBox.style.display = 'block';
                const timeColor = data.tiempo_excedido ? '#C62828' : '#2E7D32';
                const bg = data.tiempo_excedido ? '#FFEBEE' : '#E8F5E9';
                const border = data.tiempo_excedido ? '#FFCDD2' : '#C8E6C9';
                let visitorWarn = `
                    <div style="background: ${bg}; border: 1px solid ${border}; padding: 12px; border-radius: 10px; display: flex; align-items: center; justify-content: space-between; font-size: 0.85rem; margin-bottom: 10px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <i class="fas fa-clock" style="color: ${timeColor}; font-size: 1.2rem;"></i>
                            <div>
                                <strong style="color: #2c3e50;">Permanencia:</strong> <span style="font-weight: 700; color: ${timeColor};">${esc(data.tiempo_transcurrido || 'Menos de 1 min')}</span>
                            </div>
                        </div>
                `;
                if (data.tiempo_excedido) {
                    visitorWarn += `<span style="background: #C62828; color: white; padding: 2px 8px; border-radius: 10px; font-weight: 700; font-size: 0.7rem; animation: pulse 1.5s infinite;">⚠️ TIEMPO EXCEDIDO</span>`;
                }
                visitorWarn += `</div>`;
                warnBox.innerHTML += visitorWarn;
            }

            // Aviso de foto sin verificar: el celador no debe apoyarse en una
            // foto que nadie ha comprobado que corresponda a esa persona.
            if (data.tipo === 'Usuario' && data.foto_aprobada === false) {
                warnBox.style.display = 'block';
                warnBox.innerHTML += `
                    <div style="background: #FFF3E0; border: 1px solid #FFE0B2; color: #E65100; padding: 12px; border-radius: 10px; font-size: 0.85rem; display: flex; align-items: flex-start; gap: 8px; margin-bottom: 10px; line-height: 1.4; text-align: left;">
                        <i class="fas fa-user-clock" style="margin-top: 2px;"></i>
                        <div>
                            <strong>Foto sin verificar:</strong> esta foto todavía no fue
                            aprobada por un administrador. Pide el documento físico para
                            confirmar la identidad.
                        </div>
                    </div>
                `;
            }

            // Flow discrepancy alert
            if (data.status !== 'Entrada') {
                warnBox.style.display = 'block';
                warnBox.innerHTML += `
                    <div style="background: #FFF3E0; border: 1px solid #FFE0B2; color: #E65100; padding: 12px; border-radius: 10px; font-size: 0.85rem; display: flex; align-items: flex-start; gap: 8px; margin-bottom: 10px; line-height: 1.4; text-align: left;">
                        <i class="fas fa-exclamation-triangle" style="margin-top: 2px;"></i>
                        <div>
                            <strong>Alerta de Flujo:</strong> Figura como **AFUERA**. Si registra una **SALIDA** forzada sin ingreso previo, se creará un log de auditoría por flujo irregular.
                        </div>
                    </div>
                `;
            }

            // Setup Quick Incident box
            const incBox = document.getElementById('res-incident-box');
            if (incBox) {
                incBox.style.display = 'block';
                document.getElementById('inc-entidad-id').value = data.id;
                document.getElementById('inc-tipo-entidad').value = data.tipo;
            }

            let equiposHtml = '';
            if (data.equipos && data.equipos.length > 0) {
                equiposHtml = `
                    <div style="margin-top: 15px; text-align: left;">
                        <p style="font-size: 0.85rem; font-weight: 700; color: var(--secondary-text); margin-bottom: 10px;">
                            <i class="fas fa-laptop"></i> Equipos Registrados:
                        </p>
                `;
                data.equipos.forEach(eq => {
                    const checked = eq.estado === 'Adentro' ? 'checked' : '';
                    const badgeBg = eq.estado === 'Adentro' ? '#E8F5E9' : '#FFF3E0';
                    const badgeColor = eq.estado === 'Adentro' ? '#2E7D32' : '#E65100';
                    const serialHtml = eq.serial ? `<span style="font-size: 0.7rem; color: var(--text-muted); background: rgba(0,0,0,0.05); padding: 2px 8px; border-radius: 4px;">${esc(eq.serial)}</span>` : '';
                    const icon = eq.tipo === 'Tablet' ? '📱' : (eq.tipo === 'Computador' || eq.tipo === 'Portátil' ? '💻' : '📦');
                    
                    equiposHtml += `
                    <label style="display: flex; justify-content: space-between; align-items: center; background: var(--white); padding: 10px 14px; border: 1px solid var(--glass-border); border-radius: 10px; margin-bottom: 6px; cursor: pointer; transition: all 0.3s;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <input type="checkbox" name="equipos_ids" value="${esc(eq.id)}" class="equipo-checkbox-ajax" ${checked} style="width: 18px; height: 18px; accent-color: #39A900;">
                            <span style="font-size: 0.9rem; font-weight: 600; color: var(--text-main);">
                                ${icon} ${esc(eq.nombre)} <small style="opacity: 0.6;">(${esc(eq.tipo)})</small>
                            </span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            ${serialHtml}
                            <span style="font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; font-weight: 700; background: ${badgeBg}; color: ${badgeColor};">
                                ${esc(eq.estado)}
                            </span>
                        </div>
                    </label>`;
                });
                equiposHtml += `
                        <p style="font-size: 0.75rem; color: var(--text-muted); margin-top: 8px; text-align: center;">
                            <i class="fas fa-info-circle"></i> Marca los equipos que el usuario trae consigo.
                        </p>
                    </div>`;
            }

            let detailsHtml = '';
            if (data.tipo === 'Vehiculo') {
                detailsHtml = `
                    <div style="display:flex; justify-content:space-around;">
                        <p><strong>Placa:</strong><br>${esc(data.documento)}</p>
                        <p><strong>Clase/Tipo:</strong><br>${esc(data.cargo)}</p>
                        <p><strong>Rol:</strong><br>${esc(data.rol)}</p>
                    </div>
                `;
            } else if (data.tipo === 'ObjetoExterno') {
                detailsHtml = `
                    <div style="display:flex; justify-content:space-around;">
                        <p><strong>Serial:</strong><br>${esc(data.documento)}</p>
                        <p><strong>Propietario:</strong><br>${esc(data.cargo)}</p>
                        <p><strong>Rol:</strong><br>${esc(data.rol)}</p>
                    </div>
                `;
            } else {
                detailsHtml = `
                    <div style="display:flex; justify-content:space-around;">
                        <p><strong>Cédula:</strong><br>${esc(data.documento)}</p>
                        <p><strong>Rol:</strong><br>${esc(data.rol)}</p>
                    </div>
                `;
            }

            document.getElementById('res-details').innerHTML = detailsHtml + equiposHtml;

            const bEntrada = document.getElementById('btn-entrada');
            const bSalida = document.getElementById('btn-salida');
            bEntrada.onclick = () => registerMove(data.id, 'Entrada', data.tipo);
            bSalida.onclick = () => registerMove(data.id, 'Salida', data.tipo);
            bEntrada.disabled = (data.status === 'Entrada');
            bSalida.disabled = (data.status === 'Salida');

        } catch(e) {
            console.error(e);
            showToast("Fallo Crítico", "No se pudo conectar con el servidor de validación.", "danger");
            resetUI();
        }
    }

    // Los datos vienen de la base y los escribe personal de porteria o los
    // propios usuarios (nombre de equipo, propietario de un objeto). Sin
    // escapar, un valor como <img onerror=...> se ejecutaria en la sesion del
    // celador al escanear. Todo dato dinamico pasa por aqui.

    function esc(valor) {
        if (valor === null || valor === undefined) return '';
        return String(valor)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    async function registerMove(id, type, entityType) {
        const url = entityType === 'Usuario' 
            ? `/porteria/register_movement/${id}/${type}`
            : `/porteria/register_movement_entidad/${entityType}/${id}/${type}`;
        
        const formData = new FormData();
        if (entityType === 'Usuario') {
            document.querySelectorAll('.equipo-checkbox-ajax:checked').forEach(cb => {
                formData.append('equipos_ids', cb.value);
            });
        }
        
        try {
            const res = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: { 
                    'X-Requested-With': 'XMLHttpRequest', 
                    'X-CSRF-Token': CSRF_TOKEN 
                }
            });
            const data = await res.json();
            if(data.status === 'success') {
                showToast("Éxito", data.message, "success");
                resetUI();
            }
        } catch(e) {
            showToast("Error de Registro", "Hubo un error al guardar el movimiento.", "danger");
        }
    }

    function resetUI() {
        document.getElementById('scanner-result-ui').style.display = 'none';
        document.querySelector('.scanner-view-container').style.display = 'block';
        document.getElementById('manual-trigger-group').style.display = 'block';
        document.getElementById('camera-overlay').classList.remove('hidden');
        document.getElementById('laser').style.display = 'none';
        document.getElementById('manual-form').style.display = 'none';
        document.getElementById('manualDoc').value = '';
        if (document.getElementById('res-incident-form')) {
            document.getElementById('res-incident-form').reset();
        }
    }

// Enganche de los botones que antes llevaban onclick inline.
document.addEventListener('DOMContentLoaded', () => {
    const acciones = {
        'btn-iniciar-camara': startCamera,
        'switch-cam-btn': switchCamera,
        'btn-manual-toggle': toggleManual,
        'btn-manual-enviar': handleManualSubmit,
        'btn-volver-escaner': resetUI,
    };
    for (const [id, fn] of Object.entries(acciones)) {
        const el = document.getElementById(id);
        if (el) el.addEventListener('click', fn);
    }

    // El respaldo de la foto se resuelve aqui porque la ruta la conoce el JS.
    const foto = document.getElementById('res-photo');
    if (foto) {
        foto.dataset.respaldo = AVATAR_GENERICO;
        if (window.engancharRespaldoImagenes) engancharRespaldoImagenes();
    }
});
