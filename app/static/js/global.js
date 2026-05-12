document.addEventListener('DOMContentLoaded', () => {

    // 1. Loader Removal - Immediate & Robust
    const hideLoader = () => {
        const loader = document.getElementById('global-loader');
        if (loader) loader.classList.add('hidden');
    };
    setTimeout(hideLoader, 500);
    // Fallback: Si por algo no se oculta, ocultarlo a los 3 segundos
    setTimeout(hideLoader, 3000);

    // 2. Magnetic Button Logic
    const magneticButtons = document.querySelectorAll('.magnetic-btn');
    magneticButtons.forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const rect = btn.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            btn.style.transform = `translate(${x * 0.2}px, ${y * 0.2}px)`;
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.transform = 'translate(0, 0)';
        });
    });

    // 3. Magic Line Logic
    const sidebar = document.querySelector('.sidebar-nav');
    const magicLine = document.querySelector('.magic-line');
    const activeLink = document.querySelector('.sidebar-nav a.active');

    if (magicLine && activeLink) {
        magicLine.style.transform = `translateY(${activeLink.offsetTop}px)`;
    }

    // 4. Theme Toggler
    const themeBtns = document.querySelectorAll('.theme-icon-btn');

    if (themeBtns.length > 0) {
        const currentTheme = localStorage.getItem('theme') || 'light';

        themeBtns.forEach(btn => {
            const icon = btn.querySelector('i');
            if (icon) icon.className = currentTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';

            btn.addEventListener('click', () => {
                const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
                const newTheme = isDark ? 'light' : 'dark';

                if (newTheme === 'dark') {
                    document.documentElement.setAttribute('data-theme', 'dark');
                    localStorage.setItem('theme', 'dark');
                    initParticlesGlobal('#ffffff'); // Re-inicializar con blanco
                } else {
                    document.documentElement.removeAttribute('data-theme');
                    localStorage.setItem('theme', 'light');
                    initParticlesGlobal('#39A900'); // Usar Verde SENA en modo claro para que se vea mejor
                }

                // Update all icons
                themeBtns.forEach(b => {
                    const i = b.querySelector('i');
                    if (i) i.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
                });
            });
        });
    }

    // 5. Vanilla Tilt Initialization
    try {
        if (typeof VanillaTilt !== 'undefined') {
            VanillaTilt.init(document.querySelectorAll(".card, .stat-card"), {
                max: 5,
                speed: 400,
                glare: true,
                "max-glare": 0.15,
            });

            VanillaTilt.init(document.querySelectorAll(".glass-card, .carnet-card"), {
                max: 3,
                speed: 400,
                glare: true,
                "max-glare": 0.2,
            });
        }
    } catch (e) { console.warn("Tilt.js fail", e); }

    // 6. Particles.js Initialization
    initParticlesGlobal(localStorage.getItem('theme') === 'dark' ? '#ffffff' : '#39A900');

    // 7. Cinematic Reveal Logic
    const observerOptions = { root: null, rootMargin: '0px 0px -50px 0px', threshold: 0.05 };

    const revealElement = (el, delay = 0) => {
        setTimeout(() => {
            const anim = el.dataset.animation || 'fade-in-up';
            el.classList.add('revealed');
            el.classList.add(anim);
        }, delay);
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = entry.target;
                const staggeredItems = target.querySelectorAll('.stagger-item');
                if (staggeredItems.length > 0) {
                    staggeredItems.forEach((item, index) => revealElement(item, index * 100));
                }
                revealElement(target);
                observer.unobserve(target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.animate-on-scroll, .stagger-item, .dust-reveal').forEach(el => observer.observe(el));

    // Emergency Reveal
    setTimeout(() => {
        document.querySelectorAll('.animate-on-scroll, .stagger-item').forEach(el => {
            if (!el.classList.contains('revealed')) revealElement(el);
        });
    }, 2000);

    // 8. Global AJAX Forms
    document.body.addEventListener('submit', async (e) => {
        const form = e.target;
        if (form.hasAttribute('data-no-ajax')) return;
        e.preventDefault();
        
        const formData = new FormData(form);
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnContent = submitBtn ? submitBtn.innerHTML : '';

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
        }

        try {
            const response = await fetch(form.action, {
                method: form.method || 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });

            if (response.redirected) {
                window.location.href = response.url;
                return;
            }

            const data = await response.json();
            if (data.status === 'success' || data.success) {
                showToast("Éxito", data.message || "Operación completada", "success");
                if (data.redirect) setTimeout(() => window.location.href = data.redirect, 1000);
                else if (data.reload) setTimeout(() => window.location.reload(), 1000);
            } else {
                showToast("Atención", data.message || "Error en la operación", "danger");
                if (data.bloqueado_segundos && typeof startLockoutTimer === 'function') {
                    startLockoutTimer(parseInt(data.bloqueado_segundos));
                }
            }
        } catch (error) {
            console.error("AJAX Error:", error);
            showToast("Error", "Error de conexión o datos inválidos.", "danger");
        } finally {
            if (submitBtn && !form.dataset.stayDisabled) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnContent;
            }
        }
    });

    // 9. Initial Flash Messages
    const flashContainer = document.getElementById('flex-messages-data');
    if (flashContainer) {
        try {
            const messages = JSON.parse(flashContainer.dataset.messages);
            messages.forEach(([category, message]) => {
                showToast("Aviso del Sistema", message, category);
            });
        } catch (e) { console.error("Flash parse error", e); }
    }

    // 10. Sidebar Toggle Logic (Mobile)
    const menuToggle = document.getElementById('menu-toggle');
    const sidebarClose = document.getElementById('sidebar-close');
    const sidebarMain = document.getElementById('sidebar-main');
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    const toggleSidebar = (show) => {
        if (sidebarMain) sidebarMain.classList.toggle('active', show);
        if (sidebarOverlay) sidebarOverlay.classList.toggle('active', show);
        document.body.style.overflow = show ? 'hidden' : '';
    };

    if (menuToggle) menuToggle.addEventListener('click', () => toggleSidebar(true));
    if (sidebarClose) sidebarClose.addEventListener('click', () => toggleSidebar(false));
    if (sidebarOverlay) sidebarOverlay.addEventListener('click', () => toggleSidebar(false));

    // Cerrar automáticamente si se redimensiona a escritorio
    window.addEventListener('resize', () => {
        if (window.innerWidth > 1024) toggleSidebar(false);
    });
});

// Helper Functions
function initParticlesGlobal(color) {
    try {
        if (typeof particlesJS !== 'undefined' && document.getElementById('particles-js')) {
            particlesJS("particles-js", {
                "particles": {
                    "number": { "value": 60, "density": { "enable": true, "value_area": 800 } },
                    "color": { "value": color },
                    "shape": { "type": "circle" },
                    "opacity": { "value": 0.5, "random": true }, // Aumentada opacidad
                    "size": { "value": 3, "random": true },
                    "line_linked": { "enable": true, "distance": 150, "color": color, "opacity": 0.3, "width": 1 }, // Aumentada opacidad
                    "move": { "enable": true, "speed": 1.5, "direction": "none", "random": true, "out_mode": "out" }
                },
                "interactivity": {
                    "detect_on": "window",
                    "events": {
                        "onhover": { "enable": true, "mode": "grab" },
                        "onclick": { "enable": true, "mode": "push" }
                    },
                    "modes": {
                        "grab": { "distance": 200, "line_linked": { "opacity": 0.5 } },
                        "push": { "particles_nb": 4 }
                    }
                },
                "retina_detect": true
            });
        }
    } catch (e) { console.warn("Particles.js fail", e); }
}

function showToast(title, message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const typeMap = { 'danger': 'danger', 'error': 'danger', 'success': 'success', 'warning': 'warning', 'info': 'info' };
    const toastType = typeMap[type] || 'info';
    const iconMap = { 'success': 'fa-check-circle', 'danger': 'fa-exclamation-circle', 'warning': 'fa-align-left', 'info': 'fa-info-circle' };

    const toast = document.createElement('div');
    toast.className = `toast toast-${toastType}`;
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas ${iconMap[toastType]}"></i>
        </div>
        <div class="toast-content">
            <span class="toast-title">${title}</span>
            <p class="toast-message">${message}</p>
        </div>
        <div class="toast-progress">
            <div class="toast-progress-bar"></div>
        </div>
    `;

    container.appendChild(toast);
    void toast.offsetWidth;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}

function globalCheckFileSize(input) {
    const maxSizeMB = 10;
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    let errorDiv = input.parentNode.querySelector('.file-size-error');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'file-size-error';
        errorDiv.style.cssText = 'color: #e74c3c; font-size: 0.8rem; margin-top: 5px; font-weight: 600; display: none;';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ¡Archivo demasiado pesado! Máximo ${maxSizeMB}MB.`;
        input.parentNode.appendChild(errorDiv);
    }
    if (input.files && input.files[0]) {
        if (input.files[0].size > maxSizeBytes) {
            errorDiv.style.display = 'block';
            input.value = ""; 
            input.classList.add('input-error');
        } else {
            errorDiv.style.display = 'none';
            input.classList.remove('input-error');
        }
    }
}

// 10. Global Premium Confirmation Logic
window.customConfirm = function(title, message, confirmText = 'Si, Eliminar') {
    return new Promise((resolve) => {
        const modal = document.getElementById('global-confirm-modal');
        const titleEl = document.getElementById('confirm-modal-title');
        const messageEl = document.getElementById('confirm-modal-message');
        const okBtn = document.getElementById('confirm-modal-ok');
        const cancelBtn = document.getElementById('confirm-modal-cancel');

        if (!modal) {
            console.error("Modal no encontrado.");
            resolve(confirm(message)); // Fallback
            return;
        }

        titleEl.textContent = title;
        messageEl.textContent = message;
        okBtn.innerHTML = `<i class="fas fa-trash-alt"></i> ${confirmText}`;

        modal.style.display = 'flex';
        modal.classList.add('active');

        // Cerrar si se presiona Escape
        const escHandler = (e) => {
            if (e.key === 'Escape') cancelHandler();
        };
        window.addEventListener('keydown', escHandler);

        const cancelHandler = () => {
            window.removeEventListener('keydown', escHandler);
            modal.style.display = 'none';
            modal.classList.remove('active');
            resolve(false);
        };

        const okHandler = () => {
            window.removeEventListener('keydown', escHandler);
            modal.style.display = 'none';
            modal.classList.remove('active');
            resolve(true);
        };

        okBtn.onclick = okHandler;
        cancelBtn.onclick = cancelHandler;
    });
};
