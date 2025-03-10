// Gestion des statistiques et graphiques
document.addEventListener('DOMContentLoaded', function() {
    let charts = {};
    const colors = [
        'rgba(255, 99, 132, 0.8)',
        'rgba(54, 162, 235, 0.8)',
        'rgba(255, 206, 86, 0.8)',
        'rgba(75, 192, 192, 0.8)',
        'rgba(153, 102, 255, 0.8)',
        'rgba(255, 159, 64, 0.8)'
    ];

    // Configuration commune pour les graphiques
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'right',
                labels: {
                    font: {
                        size: 12
                    }
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        let label = context.label || '';
                        let value = context.raw || 0;
                        let total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                        let percentage = ((value * 100) / total).toFixed(1);
                        return `${label}: ${value} (${percentage}%)`;
                    }
                }
            }
        }
    };

    // Fonction pour charger les statistiques générales
    function loadGeneralStats() {
        fetch('/api/admin/stats/general')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const stats = data.stats;
                    document.getElementById('totalEmployees').textContent = stats.total_employees;
                    document.getElementById('averageAge').textContent = `${stats.average_age} ans`;
                    document.getElementById('genderRatio').textContent = `${stats.male_ratio}% H`;
                    document.getElementById('averageTenure').textContent = `${stats.average_tenure} ans`;
                }
            })
            .catch(error => console.error('Erreur:', error));
    }

    // Fonction pour charger les données géographiques
    function loadGeoData(type = 'region') {
        fetch(`/api/admin/stats/geo/${type}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateGeoChart(data.stats, type);
                }
            })
            .catch(error => console.error('Erreur:', error));
    }

    // Fonction pour mettre à jour le graphique géographique
    function updateGeoChart(data, type) {
        const ctx = document.getElementById('geoDistChart').getContext('2d');
        const title = type === 'region' ? 'Régions' : 
                     type === 'departement' ? 'Départements' : 
                     'Sous-préfectures';
        
        if (charts.geo) {
            charts.geo.destroy();
        }

        charts.geo = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(item => item.name),
                datasets: [{
                    data: data.map(item => item.count),
                    backgroundColor: colors
                }]
            },
            options: {
                ...commonOptions,
                plugins: {
                    ...commonOptions.plugins,
                    title: {
                        display: true,
                        text: `Distribution par ${title}`,
                        font: {
                            size: 16
                        }
                    }
                }
            }
        });
    }

    // Fonction pour charger les données de poste
    function loadPositionData() {
        fetch('/api/admin/stats/positions')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const ctx = document.getElementById('positionChart').getContext('2d');
                    if (charts.position) {
                        charts.position.destroy();
                    }
                    charts.position = new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: data.stats.map(item => item.position),
                            datasets: [{
                                data: data.stats.map(item => item.count),
                                backgroundColor: colors
                            }]
                        },
                        options: commonOptions
                    });
                }
            })
            .catch(error => console.error('Erreur:', error));
    }

    // Fonction pour charger les données de catégorie
    function loadCategoryData() {
        fetch('/api/admin/stats/categories')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const ctx = document.getElementById('categoryChart').getContext('2d');
                    if (charts.category) {
                        charts.category.destroy();
                    }
                    charts.category = new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: data.stats.map(item => item.category),
                            datasets: [{
                                data: data.stats.map(item => item.count),
                                backgroundColor: colors
                            }]
                        },
                        options: commonOptions
                    });
                }
            })
            .catch(error => console.error('Erreur:', error));
    }

    // Fonction pour charger les données de diplôme
    function loadDiplomaData() {
        fetch('/api/admin/stats/diplomas')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const ctx = document.getElementById('diplomaChart').getContext('2d');
                    if (charts.diploma) {
                        charts.diploma.destroy();
                    }
                    charts.diploma = new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: data.stats.map(item => item.diploma),
                            datasets: [{
                                data: data.stats.map(item => item.count),
                                backgroundColor: colors
                            }]
                        },
                        options: commonOptions
                    });
                }
            })
            .catch(error => console.error('Erreur:', error));
    }

    // Fonction pour charger les données de genre
    function loadGenderData() {
        fetch('/api/admin/stats/gender')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const ctx = document.getElementById('genderChart').getContext('2d');
                    if (charts.gender) {
                        charts.gender.destroy();
                    }
                    charts.gender = new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: data.stats.map(item => item.gender),
                            datasets: [{
                                data: data.stats.map(item => item.count),
                                backgroundColor: colors.slice(0, 2)
                            }]
                        },
                        options: {
                            ...commonOptions,
                            plugins: {
                                ...commonOptions.plugins,
                                legend: {
                                    position: 'right'
                                }
                            }
                        }
                    });
                }
            })
            .catch(error => console.error('Erreur:', error));
    }

    // Fonction pour charger les données d'âge
    function loadAgeData() {
        fetch('/api/admin/stats/age')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const ctx = document.getElementById('ageChart').getContext('2d');
                    if (charts.age) {
                        charts.age.destroy();
                    }
                    charts.age = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: data.stats.map(item => item.range),
                            datasets: [{
                                label: 'Nombre d\'employés',
                                data: data.stats.map(item => item.count),
                                backgroundColor: colors[0]
                            }]
                        },
                        options: {
                            ...commonOptions,
                            plugins: {
                                ...commonOptions.plugins,
                                legend: {
                                    display: false
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: {
                                        stepSize: 1
                                    }
                                }
                            }
                        }
                    });
                }
            })
            .catch(error => console.error('Erreur:', error));
    }

    // Gestion des boutons de filtrage géographique
    document.querySelectorAll('[data-chart]').forEach(button => {
        button.addEventListener('click', function() {
            const type = this.dataset.chart;
            document.querySelectorAll('[data-chart]').forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            loadGeoData(type);
        });
    });

    // Export en PNG
    document.getElementById('exportPNG').addEventListener('click', function() {
        const zip = new JSZip();
        const promises = [];

        Object.entries(charts).forEach(([name, chart]) => {
            const promise = new Promise(resolve => {
                const canvas = chart.canvas;
                canvas.toBlob(blob => {
                    zip.file(`${name}_chart.png`, blob);
                    resolve();
                });
            });
            promises.push(promise);
        });

        Promise.all(promises).then(() => {
            zip.generateAsync({type: 'blob'}).then(content => {
                const link = document.createElement('a');
                link.href = URL.createObjectURL(content);
                link.download = 'statistiques_charts.zip';
                link.click();
            });
        });
    });

    // Export en PowerPoint (via API pptx.js)
    document.getElementById('exportPPT').addEventListener('click', function() {
        const pptx = new PptxGenJS();
        
        Object.entries(charts).forEach(([name, chart]) => {
            const slide = pptx.addSlide();
            const dataUrl = chart.canvas.toDataURL();
            
            slide.addImage({
                data: dataUrl,
                x: 1,
                y: 1,
                w: 8,
                h: 5
            });
            
            slide.addText(name.charAt(0).toUpperCase() + name.slice(1) + ' Statistics', {
                x: 1,
                y: 0,
                fontSize: 18,
                bold: true
            });
        });

        pptx.writeFile('statistiques_presentation.pptx');
    });

    // Charger les données initiales quand on active l'onglet statistiques
    document.querySelector('a[href="#stats"]').addEventListener('shown.bs.tab', function() {
        loadGeneralStats();
        loadGeoData();
        loadPositionData();
        loadCategoryData();
        loadDiplomaData();
        loadGenderData();
        loadAgeData();
    });
});
