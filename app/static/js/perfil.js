// Perfil del usuario. Externo porque la CSP ya no admite scripts inline;
// el nombre del archivo del carnet y el token CSRF llegan por data-*.
const CFG = document.currentScript.dataset;

    function toggleSection(sectionId) {
        const sections = ['update-info-section', 'devices-section', 'add-device-section'];
        const placeholder = document.getElementById('profile-placeholder');

        // Determinar si ya está abierto / Check if already open
        const target = document.getElementById(sectionId);
        const alreadyOpen = target.style.display === 'block';

        // Ocultar todos / Hide all
        sections.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });

        if (!alreadyOpen) {
            target.style.display = 'block';
            if (placeholder) placeholder.style.display = 'none';
        } else {
            if (placeholder) placeholder.style.display = 'block';
        }
    }

    // === DESCARGAR CARNET COMO IMAGEN ===
    async function descargarCarnet() {
        const btn = document.getElementById('btn-descargar-carnet');
        const carnet = document.getElementById('carnet-capture');
        
        if (!carnet) return;

        // Estado de carga
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generando...';
        btn.disabled = true;
        btn.style.opacity = '0.7';

        try {
            // Esperar a que la tipografia este cargada antes de capturar. Sin
            // esto html2canvas mide el texto con la fuente de reserva y luego
            // lo dibuja con la definitiva: los espacios se pierden y el pie
            // sale como "RegionalSantander" en vez de "Regional Santander".
            if (document.fonts && document.fonts.ready) {
                await document.fonts.ready;
            }

            const canvas = await html2canvas(carnet, {
                scale: 2,
                useCORS: true,
                allowTaint: true,
                // Fondo blanco explicito: el carnet se imprime y el codigo de
                // barras necesita blanco puro detras para que el lector lo lea.
                backgroundColor: '#ffffff',
                logging: false,
                onclone: function (documentoClonado) {
                    // html2canvas dibuja cada palabra por separado y calcula el
                    // avance del espacio con la metrica de la fuente. Con pesos
                    // y cursivas sintetizados ese avance sale en cero y las
                    // palabras quedan pegadas. Fijar el espaciado a mano obliga
                    // a que el hueco exista, sin alterar como se ve en pantalla.
                    const copia = documentoClonado.getElementById('carnet-capture');
                    if (!copia) { return; }
                    copia.style.wordSpacing = '0.08em';
                    copia.querySelectorAll('*').forEach(function (elemento) {
                        elemento.style.wordSpacing = '0.08em';
                    });
                }
            });

            // Crear enlace de descarga
            const link = document.createElement('a');
            link.download = CFG.nombreArchivoCarnet;
            link.href = canvas.toDataURL('image/png');
            link.click();

            // Feedback visual
            btn.innerHTML = '<i class="fas fa-check"></i> ¡Descargado!';
            btn.style.background = 'linear-gradient(135deg, #2ecc71, #27ae60)';
            
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.background = '';
            }, 2500);
        } catch (err) {
            console.error('Error al generar la imagen del carnet:', err);
            btn.innerHTML = '<i class="fas fa-exclamation-circle"></i> Error';
            btn.style.background = 'linear-gradient(135deg, #e74c3c, #c0392b)';
            
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.background = '';
            }, 2500);
        }
    }

    const botonDescarga = document.getElementById('btn-descargar-carnet');
    if (botonDescarga) botonDescarga.addEventListener('click', descargarCarnet);

    // Premium Confirmation Integration
    // Muestra el formato esperado del documento segun el tipo elegido, para
    // que la persona lo corrija antes de enviar y no tras un error.
    const selectorTipo = document.getElementById('tipo_documento');
    const pistaFormato = document.getElementById('formato-documento');
    if (selectorTipo && pistaFormato) {
        const actualizarPista = () => {
            const opcion = selectorTipo.options[selectorTipo.selectedIndex];
            pistaFormato.textContent = opcion ? opcion.dataset.formato || '' : '';
        };
        selectorTipo.addEventListener('change', actualizarPista);
        actualizarPista();
    }

    document.querySelectorAll('.delete-device-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const url = btn.dataset.url;
            const name = btn.dataset.name;
            
            const confirmed = await window.customConfirm(
                "¿Eliminar Equipo?",
                `¿Estás seguro de que deseas eliminar el equipo "${name}"? Esta acción desvinculará el dispositivo de tu cuenta.`,
                "Si, Eliminar"
            );

            if (!confirmed) return;

            // El borrado ahora exige POST con token CSRF; una navegación GET
            // permitía borrar el equipo desde cualquier sitio externo.
            try {
                const respuesta = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': CFG.csrf
                    }
                });
                const datos = await respuesta.json();
                if (datos.status === 'success') {
                    showToast("Éxito", datos.message, "success");
                    setTimeout(() => window.location.reload(), 800);
                } else {
                    showToast("Atención", datos.message || "No se pudo eliminar.", "danger");
                }
            } catch (error) {
                showToast("Error", "Error de conexión.", "danger");
            }
        });
    });

// Botones de las secciones desplegables (antes onclick inline).
document.querySelectorAll('[data-seccion]').forEach(b =>
    b.addEventListener('click', () => toggleSection(b.dataset.seccion)));
