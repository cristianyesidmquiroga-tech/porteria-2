// Gestion de usuarios. Fuera de la plantilla porque la CSP prohibe
// scripts inline; las rutas y el token CSRF llegan por data-* .
const CFG = document.currentScript.dataset;

    function toggleCargoFields(cargo, prefix) {
        const fields = document.getElementById(`${prefix}-aprendiz-fields`);
        if (cargo === 'Aprendiz') {
            fields.style.display = 'grid';
        } else {
            fields.style.display = 'none';
        }
    }

    function updateFileName(input) {
        const fileNameDisplay = document.getElementById('file-name-display');
        if (input.files && input.files.length > 0) {
            fileNameDisplay.textContent = input.files[0].name;
        } else {
            fileNameDisplay.textContent = 'Seleccionar archivo';
        }
    }

    // Modal helpers
    function openModal(id) {
        document.getElementById(id).classList.add('active');
    }
    function closeModal(id) {
        document.getElementById(id).classList.remove('active');
    }

    // Función auxiliar para notificaciones (usando showToast de base.html)
    function showNotification(message, type) {
        const title = type === 'success' ? 'Éxito' : 'Error';
        showToast(title, message, type === 'success' ? 'success' : 'danger');
    }

    // --- FLUJO DE AUDITORÍA ---
    let pendingAuditAction = null;

    function openAuditModal(onConfirm) {
        document.getElementById('audit-autorizado').value = '';
        document.getElementById('audit-motivo').value = '';
        pendingAuditAction = onConfirm;
        openModal('modal-audit');
    }

    document.getElementById('audit-submit-btn').onclick = function() {
        const autorizado = document.getElementById('audit-autorizado').value;
        const motivo = document.getElementById('audit-motivo').value;

        if (!autorizado || !motivo) {
            showNotification('Todos los campos de auditoría son obligatorios.', 'error');
            return;
        }

        if (pendingAuditAction) {
            pendingAuditAction({ autorizado_por: autorizado, motivo: motivo });
            closeModal('modal-audit');
            pendingAuditAction = null;
        }
    };

    // Crear Usuario
    async function createUser(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        data.verificado = true; 
        
        try {
            const response = await fetch(CFG.urlCrear, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CFG.csrf
                },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            
            if(response.ok) {
                showNotification(result.message, 'success');
                closeModal('modal-add-user');
                setTimeout(() => window.location.reload(), 1500);
            } else {
                showNotification(result.message, 'error');
            }
        } catch(e) {
            showNotification('Error de conexión', 'error');
        }
    }

    // Preparar y Abrir Editar
    function openEditModal(id) {
        const targetBtn = event.target.closest('.action-btn-edit');
        document.getElementById('edit-id').value = id;
        document.getElementById('edit-nombre').value = targetBtn.dataset.nombre;
        document.getElementById('edit-documento').value = targetBtn.dataset.documento;
        document.getElementById('edit-correo').value = targetBtn.dataset.correo;
        document.getElementById('edit-cargo').value = targetBtn.dataset.cargo;
        document.getElementById('edit-rol').value = targetBtn.dataset.rol;
        document.getElementById('edit-verificado').value = targetBtn.dataset.verificado;
        document.getElementById('edit-password').value = '';
        
        toggleCargoFields(targetBtn.dataset.cargo, 'edit');
        if(targetBtn.dataset.cargo === 'Aprendiz') {
            document.getElementById('edit-ficha').value = targetBtn.dataset.ficha;
            document.getElementById('edit-programa').value = targetBtn.dataset.programa;
            document.getElementById('edit-horario').value = targetBtn.dataset.horario;
        }

        const bloqueoGroup = document.getElementById('edit-bloqueo-group');
        if(targetBtn.dataset.bloqueado === 'true') {
            bloqueoGroup.style.display = 'block';
            document.getElementById('edit-bloqueo').value = '';
        } else {
            bloqueoGroup.style.display = 'none';
        }

        openModal('modal-edit-user');
    }

    // Actualizar Usuario (Con Auditoría)
    async function updateUser(event) {
        event.preventDefault();
        const form = event.target;
        const id = document.getElementById('edit-id').value;
        const formData = new FormData(form);
        const userData = Object.fromEntries(formData.entries());
        userData.verificado = userData.verificado === 'true';

        openAuditModal(async (auditData) => {
            const finalData = { ...userData, ...auditData };
            try {
                const response = await fetch(`/usuarios/api/admin/editar_usuario/${id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': CFG.csrf
                    },
                    body: JSON.stringify(finalData)
                });
                const result = await response.json();
                
                if(response.ok) {
                    showNotification(result.message, 'success');
                    closeModal('modal-edit-user');
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    showNotification(result.message, 'error');
                }
            } catch(e) {
                showNotification('Error de conexión', 'error');
            }
        });
    }

    // Eliminar Usuario (Con Auditoría)
    async function deleteUser(id, nombre) {
        const confirmed = await window.customConfirm(
            'Confirmar Eliminación',
            `¿Estás seguro de que deseas eliminar permanentemente el perfil de ${nombre}?`
        );

        if (confirmed) {
            openAuditModal(async (auditData) => {
                try {
                    const response = await fetch(`/usuarios/api/admin/eliminar_usuario/${id}`, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': CFG.csrf
                        },
                        body: JSON.stringify(auditData)
                    });
                    const result = await response.json();
                    
                    if(response.ok) {
                        showNotification(result.message, 'success');
                        const row = document.getElementById(`user-row-${id}`);
                        if(row) row.remove();
                    } else {
                        showNotification(result.message, 'error');
                    }
                } catch(e) {
                    showNotification('Error de conexión', 'error');
                }
            });
        }
    }

    async function importExcel(event) {
        event.preventDefault();
        const form = event.target;
        const btn = document.getElementById('btn-submit-import');
        const resultsDiv = document.getElementById('import-results');
        const statsP = document.getElementById('import-stats');
        const errorsUl = document.getElementById('import-errors');
        
        const formData = new FormData(form);
        
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
        
        try {
            const response = await fetch(CFG.urlImportar, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': CFG.csrf
                },
                body: formData
            });
            const result = await response.json();
            
            if(response.ok) {
                showNotification(result.message, 'success');
                resultsDiv.style.display = 'block';
                statsP.innerText = result.message;
                errorsUl.innerHTML = '';
                
                if (result.detalles.errores.length > 0) {
                    result.detalles.errores.forEach(err => {
                        const li = document.createElement('li');
                        li.innerText = err;
                        errorsUl.appendChild(li);
                    });
                }
                
                setTimeout(() => window.location.reload(), 3000);
            } else {
                showNotification(result.message, 'error');
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-upload"></i> Subir e Importar';
            }
        } catch(e) {
            showNotification('Error de conexión', 'error');
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-upload"></i> Subir e Importar';
        }
    }

// Enganche de los manejadores que antes eran atributos inline.
document.addEventListener('DOMContentLoaded', () => {
    // Botones que abren o cierran un modal: el id del modal va en el data-*.
    document.querySelectorAll('[data-abrir-modal]').forEach(b =>
        b.addEventListener('click', () => openModal(b.dataset.abrirModal)));
    document.querySelectorAll('[data-cerrar-modal]').forEach(b =>
        b.addEventListener('click', () => closeModal(b.dataset.cerrarModal)));

    // Filas de la tabla: editar y eliminar.
    document.querySelectorAll('[data-accion="editar-usuario"]').forEach(b =>
        b.addEventListener('click', () => openEditModal(b.dataset.id)));
    document.querySelectorAll('[data-accion="eliminar-usuario"]').forEach(b =>
        b.addEventListener('click', () => deleteUser(b.dataset.uid, b.dataset.uname)));

    // Formularios.
    const enganchar = (id, fn) => {
        const f = document.getElementById(id);
        if (f) f.addEventListener('submit', fn);
    };
    enganchar('form-add-user', createUser);
    enganchar('form-edit-user', updateUser);
    enganchar('form-import-excel', importExcel);

    // Los campos de aprendiz aparecen segun el cargo elegido.
    document.querySelectorAll('[data-cargo-prefijo]').forEach(sel =>
        sel.addEventListener('change', () => toggleCargoFields(sel.value, sel.dataset.cargoPrefijo)));

    // Selector de archivo Excel: el boton visible delega en el input oculto.
    const inputExcel = document.getElementById('excel-file-input');
    const botonExcel = document.getElementById('btn-elegir-excel');
    if (inputExcel) inputExcel.addEventListener('change', () => updateFileName(inputExcel));
    if (botonExcel && inputExcel) botonExcel.addEventListener('click', () => inputExcel.click());
});
