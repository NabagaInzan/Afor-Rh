// Fonction pour charger et afficher les écoles
function loadSchools() {
    fetch('/api/admin/schools')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displaySchools(data.schools);
            } else {
                console.error('Erreur lors du chargement des écoles:', data.error);
            }
        })
        .catch(error => {
            console.error('Erreur lors du chargement des écoles:', error);
        });
}

// Fonction pour afficher les écoles dans un tableau
function displaySchools(schools) {
    const tableBody = document.querySelector('#schoolsTable tbody');
    tableBody.innerHTML = '';

    schools.forEach(school => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${school.name}</td>
            <td>${school.address || '-'}</td>
            <td>${school.contact || '-'}</td>
            <td>${school.email || '-'}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editSchool(${school.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteSchool(${school.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

// Charger les écoles au chargement de la page
document.addEventListener('DOMContentLoaded', loadSchools);
