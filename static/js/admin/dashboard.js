// Fonction pour charger les statistiques générales
function loadDashboardStats() {
    fetch('/api/admin/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('operatorsCount').textContent = data.stats.operators;
                document.getElementById('employeesCount').textContent = data.stats.employees;
                document.getElementById('projectsCount').textContent = data.stats.projects;
                document.getElementById('schoolsCount').textContent = data.stats.schools;
            }
        })
        .catch(error => console.error('Erreur lors du chargement des statistiques:', error));
}

// Fonction pour afficher les messages d'erreur/succès
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('.container-fluid').insertBefore(alertDiv, document.querySelector('.container-fluid').firstChild);
    
    setTimeout(() => alertDiv.remove(), 3000);
}

// Charger les données initiales
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardStats();
});
