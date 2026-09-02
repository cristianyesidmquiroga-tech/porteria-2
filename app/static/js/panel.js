// Panel de porteria: filtro de ficha, pestanas y grafica. Vive aqui y no
// en la plantilla porque la CSP ya no admite scripts inline. Los datos de
// la grafica siguen leyendose del elemento #chart-data-source.

            document.addEventListener('DOMContentLoaded', function() {
                const cargoFilter = document.getElementById('cargoFilter');
                const fichaContainer = document.getElementById('fichaFilterContainer');
                
                function toggleFichaFilter() {
                    const val = cargoFilter.value.toLowerCase();
                    // Mostrar si el cargo es Aprendiz
                    if (val === 'aprendiz') {
                        fichaContainer.style.display = 'block';
                    } else {
                        fichaContainer.style.display = 'none';
                        // Limpiar el valor si se oculta para no enviar filtros fantasmas
                        document.getElementById('ficha').value = '';
                    }
                }
                
                cargoFilter.addEventListener('change', toggleFichaFilter);
                // Run on load to set initial state
                toggleFichaFilter();
            });
        
    function switchTab(viewName) {
        document.querySelectorAll('.tab-btn').forEach(function (btn) {
            btn.classList.remove('active');
        });
        document.getElementById('btn-tab-' + viewName).classList.add('active');
        document.getElementById('view-dashboard').style.display = 'none';
        document.getElementById('view-history').style.display = 'none';
        document.getElementById('view-' + viewName).style.display = 'block';
    }

    document.addEventListener('DOMContentLoaded', function () {
        // Switch to history tab on load if there are active filters or specific tab requested
        var urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('cargo') || urlParams.get('ficha') || urlParams.get('tab') === 'history' || window.location.href.includes('cargo=')) {
            switchTab('history');
        }

        // Read chart data from hidden element
        var src = document.getElementById('chart-data-source');
        var labels = JSON.parse(src.getAttribute('data-labels'));
        var aprendices = JSON.parse(src.getAttribute('data-aprendices'));
        var instructores = JSON.parse(src.getAttribute('data-instructores'));
        var trabajadores = JSON.parse(src.getAttribute('data-trabajadores'));

        // Initialize chart only if canvas exists
        var chartCanvas = document.getElementById('entriesChart');
        if (chartCanvas) {
            var ctx = chartCanvas.getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Aprendices',
                            data: aprendices,
                            backgroundColor: 'rgba(57, 169, 0, 0.1)',
                            borderColor: '#39A900',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: '#fff',
                            pointBorderColor: '#39A900',
                            pointBorderWidth: 2,
                            pointRadius: 4
                        },
                        {
                            label: 'Instructores',
                            data: instructores,
                            backgroundColor: 'rgba(54, 162, 235, 0.1)',
                            borderColor: '#36A2EB',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: '#fff',
                            pointBorderColor: '#36A2EB',
                            pointBorderWidth: 2,
                            pointRadius: 4
                        },
                        {
                            label: 'Trabajadores',
                            data: trabajadores,
                            backgroundColor: 'rgba(255, 159, 64, 0.1)',
                            borderColor: '#FF9F40',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: '#fff',
                            pointBorderColor: '#FF9F40',
                            pointBorderWidth: 2,
                            pointRadius: 4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { stepSize: 1, color: '#999' },
                            grid: { color: '#F0F0F0' }
                        },
                        x: {
                            ticks: { color: '#999' },
                            grid: { display: false }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: { boxWidth: 12, usePointStyle: true }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            padding: 10,
                            cornerRadius: 8
                        }
                    },
                    interaction: {
                        mode: 'index',
                        intersect: false
                    }
                }
            });
        }
    });

// Pestanas del panel (antes onclick inline).
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-pestana]').forEach(b =>
        b.addEventListener('click', () => switchTab(b.dataset.pestana)));
});
