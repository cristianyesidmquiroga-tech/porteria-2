// Tema guardado y marca de "JS listo". Debe correr antes de pintar: si se
// aplazara, la pagina parpadearia en claro antes de pasar a oscuro.
(function () {
    const temaGuardado = localStorage.getItem('theme') || 'light';
    if (temaGuardado === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
    document.documentElement.classList.add('js-ready');
})();
