// Extraido de analytics_rol.html: la CSP ya no admite scripts inline.

    document.addEventListener("DOMContentLoaded", function () {
        var src = document.getElementById("chart-data-source");
        var hoyLabels = JSON.parse(src.getAttribute("data-hoy-labels"));
        var hoyData = JSON.parse(src.getAttribute("data-hoy-data"));
        var semanaLabels = JSON.parse(src.getAttribute("data-semana-labels"));
        var semanaData = JSON.parse(src.getAttribute("data-semana-data"));
        var programCharts = JSON.parse(src.getAttribute("data-programs"));

        var bg = [
            "rgba(57, 169, 0, 0.85)",
            "rgba(54, 162, 235, 0.85)",
            "rgba(255, 206, 86, 0.85)",
            "rgba(255, 99, 132, 0.85)",
            "rgba(153, 102, 255, 0.85)",
            "rgba(255, 159, 64, 0.85)",
            "rgba(0, 150, 136, 0.85)",
            "rgba(233, 30, 99, 0.85)",
            "rgba(63, 81, 181, 0.85)",
            "rgba(121, 85, 72, 0.85)",
            "rgba(96, 125, 139, 0.85)"
        ];

        var opts = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "right",
                    labels: { boxWidth: 12, padding: 15, font: { size: 11, family: "'Outfit', sans-serif" } }
                },
                tooltip: { 
                    backgroundColor: "rgba(0,0,0,0.85)", padding: 12, cornerRadius: 8,
                    bodyFont: { size: 14 }, titleFont: { size: 13 }
                }
            },
            cutout: "60%",
            animation: { animateScale: true, animateRotate: true, duration: 1500, easing: 'easeOutQuart' },
            hover: { mode: 'nearest', intersect: true }
        };

        var polarOpts = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "right",
                    labels: { boxWidth: 12, padding: 15, font: { size: 11, family: "'Outfit', sans-serif" } }
                },
                tooltip: { 
                    backgroundColor: "rgba(0,0,0,0.85)", padding: 12, cornerRadius: 8,
                    bodyFont: { size: 14 }, titleFont: { size: 13 }
                }
            },
            animation: { animateScale: true, animateRotate: true, duration: 2000, easing: 'easeOutQuart' }
        };

        if (hoyData.length > 0) {
            new Chart(document.getElementById("hoyChart").getContext("2d"), {
                type: "doughnut",
                data: {
                    labels: hoyLabels,
                    datasets: [{ data: hoyData, backgroundColor: bg, borderWidth: 2, hoverOffset: 25, borderColor: "#ffffff" }]
                },
                options: opts
            });
        }

        if (semanaData.length > 0) {
            new Chart(document.getElementById("semanaChart").getContext("2d"), {
                type: "polarArea",
                data: {
                    labels: semanaLabels,
                    datasets: [{ data: semanaData, backgroundColor: bg.map(c => c.replace('0.85', '0.6')), borderColor: bg, borderWidth: 2 }]
                },
                options: polarOpts
            });
        }

        programCharts.forEach(function (p, index) {
            if (p.seven_data && p.seven_data.length > 0) {
                var el = document.getElementById("progChart_" + (index + 1));
                if (el) {
                    new Chart(el.getContext("2d"), {
                        type: "doughnut",
                        data: {
                            labels: p.seven_labels,
                            datasets: [{ data: p.seven_data, backgroundColor: bg, borderWidth: 2, hoverOffset: 10, borderColor: "#ffffff" }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 11, family: "'Montserrat', sans-serif" } } }
                            },
                            cutout: "50%"
                        }
                    });
                }
            }
        });
    });
