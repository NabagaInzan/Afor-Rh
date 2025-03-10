// Gestion des opérateurs
document.addEventListener('DOMContentLoaded', function() {
    const operatorForm = document.getElementById('operatorForm');
    const operatorTable = document.getElementById('operatorsTable').getElementsByTagName('tbody')[0];
    
    // Charger les opérateurs
    function loadOperators() {
        fetch('/api/admin/operators')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    operatorTable.innerHTML = '';
                    data.operators.forEach(operator => {
                        const row = operatorTable.insertRow();
                        row.innerHTML = `
                            <td>${operator.name}</td>
                            <td>${operator.contact1}</td>
                            <td>${operator.email1 || '-'}</td>
                            <td>${operator.acteur_type || '-'}</td>
                            <td>${operator.project || '-'}</td>
                            <td>
                                <button class="btn btn-sm btn-primary me-1" onclick="editOperator('${operator.id}')">
                                    <i class="bx bx-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-danger" onclick="deleteOperator('${operator.id}')">
                                    <i class="bx bx-trash"></i>
                                </button>
                            </td>
                        `;
                    });
                }
            })
            .catch(error => console.error('Erreur lors du chargement des opérateurs:', error));
    }

    // Charger les types d'acteurs
    function loadActorTypes() {
        fetch('/api/admin/actor-types')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const select = document.getElementById('operatorType');
                    select.innerHTML = '<option value="">Sélectionnez un type</option>';
                    data.types.forEach(type => {
                        const option = document.createElement('option');
                        option.value = type.id;
                        option.textContent = type.nom;
                        select.appendChild(option);
                    });
                }
            })
            .catch(error => console.error('Erreur lors du chargement des types d\'acteurs:', error));
    }

    // Charger les projets
    function loadProjects() {
        fetch('/api/admin/projects')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const select = document.getElementById('operatorProject');
                    select.innerHTML = '<option value="">Sélectionnez un projet</option>';
                    data.projects.forEach(project => {
                        const option = document.createElement('option');
                        option.value = project.id;
                        option.textContent = project.nom;
                        select.appendChild(option);
                    });
                }
            })
            .catch(error => console.error('Erreur lors du chargement des projets:', error));
    }

    // Sauvegarder un opérateur
    document.getElementById('saveOperator').addEventListener('click', function() {
        if (!operatorForm.checkValidity()) {
            operatorForm.reportValidity();
            return;
        }

        const operatorData = {
            name: document.getElementById('operatorName').value,
            contact1: document.getElementById('operatorContact').value,
            email1: document.getElementById('operatorEmail').value,
            password: document.getElementById('operatorPassword').value,
            acteur_type_id: document.getElementById('operatorType').value,
            project_id: document.getElementById('operatorProject').value
        };

        const operatorId = document.getElementById('operatorId').value;
        const url = operatorId ? `/api/admin/operators/${operatorId}` : '/api/admin/operators';
        const method = operatorId ? 'PUT' : 'POST';

        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(operatorData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Opérateur sauvegardé avec succès');
                loadOperators();
                bootstrap.Modal.getInstance(document.getElementById('addOperatorModal')).hide();
            } else {
                showAlert(data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showAlert('Une erreur est survenue', 'danger');
        });
    });

    // Supprimer un opérateur
    window.deleteOperator = function(operatorId) {
        if (confirm('Êtes-vous sûr de vouloir supprimer cet opérateur ?')) {
            fetch(`/api/admin/operators/${operatorId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Opérateur supprimé avec succès');
                    loadOperators();
                } else {
                    showAlert(data.error, 'danger');
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                showAlert('Une erreur est survenue', 'danger');
            });
        }
    };

    // Éditer un opérateur
    window.editOperator = function(operatorId) {
        fetch(`/api/admin/operators/${operatorId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const operator = data.operator;
                    document.getElementById('operatorId').value = operator.id;
                    document.getElementById('operatorName').value = operator.name;
                    document.getElementById('operatorContact').value = operator.contact1;
                    document.getElementById('operatorEmail').value = operator.email1 || '';
                    document.getElementById('operatorType').value = operator.acteur_type_id || '';
                    document.getElementById('operatorProject').value = operator.project_id || '';
                    document.getElementById('operatorPassword').value = '';
                    
                    const modal = new bootstrap.Modal(document.getElementById('addOperatorModal'));
                    modal.show();
                }
            })
            .catch(error => console.error('Erreur:', error));
    };

    // Initialisation
    loadOperators();
    loadActorTypes();
    loadProjects();

    // Réinitialiser le formulaire à l'ouverture du modal
    document.getElementById('addOperatorModal').addEventListener('show.bs.modal', function() {
        operatorForm.reset();
        document.getElementById('operatorId').value = '';
    });
});
