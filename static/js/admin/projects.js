// Fonction pour charger et afficher les projets
function loadProjects() {
    fetch('/api/admin/projects')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayProjects(data.projects);
            } else {
                console.error('Erreur lors du chargement des projets:', data.error);
            }
        })
        .catch(error => {
            console.error('Erreur lors du chargement des projets:', error);
        });
}

// Fonction pour afficher les projets dans un tableau
function displayProjects(projects) {
    const tableBody = document.querySelector('#projectsTable tbody');
    tableBody.innerHTML = '';

    projects.forEach(project => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${project.name}</td>
            <td>${project.description || '-'}</td>
            <td>${project.region || '-'}</td>
            <td>${project.start_date || '-'}</td>
            <td>${project.end_date || '-'}</td>
            <td>${project.status || '-'}</td>
            <td>${project.budget ? formatCurrency(project.budget) : '-'}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editProject(${project.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteProject(${project.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

// Fonction pour formater la monnaie
function formatCurrency(amount) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'XOF'
    }).format(amount);
}

// Charger les projets au chargement de la page
document.addEventListener('DOMContentLoaded', loadProjects);
