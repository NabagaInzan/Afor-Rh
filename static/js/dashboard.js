// Gestionnaire d'erreur global pour les requêtes AJAX
$(document).ajaxError(function(event, jqXHR, settings, error) {
    if (jqXHR.status === 401) {
        window.location.href = '/';
    }
});

// Variables globales
let employeesTable;
let selectedEmployees = new Set();
let selectedExpiredEmployees = [];
let postes = [];
let currentOperatorId;
let currentEmployeeId = null; // Remettre la variable globale

// Fonction pour formater le nom
function formatName(name) {
    if (!name) return '';
    return name.toUpperCase();
}

// Fonction pour formater le prénom
function formatFirstName(name) {
    if (!name) return '';
    return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
}

// Fonction pour réinitialiser les statistiques
function resetStats() {
    $('#totalEmployees').text('--');
    $('#availableEmployees').html('--');
    $('#maleEmployees').text('--');
    $('#femaleEmployees').text('--');
    $('#youngEmployees').text('--');
}

// Fonction pour charger les statistiques
function loadStats() {
    $.get('/api/stats')
        .done(function(data) {
            // Mise à jour des statistiques
            $('#totalEmployees').text(data.total || 0);
            $('#maleEmployees').text(data.male || 0);
            $('#femaleEmployees').text(data.female || 0);
            $('#availableEmployees').text(data.available || 0);
            $('#unavailableEmployees').text(data.unavailable || 0);
            $('#youngEmployees').text(data.young_employees || 0);

            // Animation des compteurs
            $('.counter-value').each(function () {
                $(this).prop('Counter', 0).animate({
                    Counter: $(this).text()
                }, {
                    duration: 1000,
                    easing: 'swing',
                    step: function (now) {
                        $(this).text(Math.ceil(now));
                    }
                });
            });
        })
        .fail(function(xhr) {
            console.error('Erreur lors de la récupération des statistiques:', xhr.responseText);
            showAlert('Erreur lors de la récupération des statistiques', 'danger');
            // En cas d'erreur, mettre des tirets
            $('#totalEmployees').text('--');
            $('#maleEmployees').text('--');
            $('#femaleEmployees').text('--');
            $('#availableEmployees').text('--');
            $('#unavailableEmployees').text('--');
            $('#youngEmployees').text('--');
        });
}

// Fonction pour charger les employés
function loadEmployees() {
    $.get('/api/employees', function(response) {
        if (!response.success || !response.employees) {
            console.error("Réponse invalide:", response);
            showAlert("Erreur lors du chargement des employés", "danger");
            return;
        }

        // Initialiser DataTable si ce n'est pas déjà fait
        let table = $('#employeesTable').DataTable();
        if (table) {
            table.clear().destroy();
        }

        table = $('#employeesTable').DataTable({
            language: {
                url: 'https://cdn.datatables.net/plug-ins/1.13.7/i18n/fr-FR.json'
            },
            responsive: true,
            data: response.employees,
            columns: [
                { 
                    data: null,
                    render: function(data) {
                        return data.region_nom || '-';
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        return data.departement_nom || '-';
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        return data.sous_prefecture_nom || '-';
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        return data.last_name || '-';
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        return data.first_name || '-';
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        return data.gender || '-';
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        if (!data.birth_date) return '-';
                        const birthDate = new Date(data.birth_date);
                        const age = calculateAge(birthDate);
                        return age ? age + ' ans' : '-';
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        return data.poste || '-';
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        if (!data.contract || !data.contract.status) return '-';
                        const status = data.contract.status;
                        const statusClass = status === 'Expiré' ? 'text-danger' : 'text-success';
                        return `<span class="${statusClass}">${status}</span>`;
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        if (!data.contract || !data.contract.start_date || !data.contract.end_date) {
                            return data.contract_duration_months ? data.contract_duration_months + ' mois' : '-';
                        }
                        const startDate = new Date(data.contract.start_date);
                        const endDate = new Date(data.contract.end_date);
                        const diffTime = Math.abs(endDate - startDate);
                        const diffMonths = Math.ceil(diffTime / (1000 * 60 * 60 * 24 * 30.44));
                        return diffMonths + ' mois';
                    }
                },
                {
                    data: null,
                    render: function(data) {
                        let buttons = `
                            <div class="btn-group">
                                <button class="btn btn-sm btn-primary edit-employee" data-id="${data.id}" title="Modifier">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-info view-contracts" data-id="${data.id}" data-first-name="${data.first_name}" data-last-name="${data.last_name}" title="Voir les détails">
                                    <i class="fas fa-eye"></i>
                                </button>`;
                        
                        // Ajouter le bouton de reconduction uniquement si le contrat est expiré
                        if (data.contract && data.contract.status === 'Expiré') {
                            buttons += `
                                <button class="btn btn-sm btn-warning btn-renew" data-id="${data.id}" data-first-name="${data.first_name}" data-last-name="${data.last_name}" title="Reconduire le contrat">
                                    <i class="fas fa-sync-alt"></i>
                                </button>`;
                        }
                        
                        buttons += `</div>`;
                        return buttons;
                    }
                }
            ],
            order: [[3, 'asc']]  // Tri par nom de famille
        });

        // Mettre à jour les statistiques après le chargement
        loadStats();
    })
    .fail(function(xhr) {
        console.error("Erreur lors du chargement des employés:", xhr.responseText);
        showAlert("Erreur lors du chargement des employés", "danger");
    });
}

// Fonction pour charger les postes
function loadPostes() {
    return $.get('/api/postes', function(response) {
        try {
            if (response.success && Array.isArray(response.data)) {
                postes = response.data;
                // Remplir le champ de sélection des postes
                const posteSelect = $('#poste');
                posteSelect.empty().append('<option value="">Sélectionner un poste</option>');
                postes.forEach(poste => {
                    posteSelect.append(`<option value="${poste.id}">${poste.titre}</option>`);
                });
            } else {
                console.error("Format de réponse postes invalide:", response);
                postes = [];
            }
        } catch (error) {
            console.error("Erreur lors du traitement des postes:", error);
            postes = [];
        }
    }).fail(function(error) {
        console.error("Erreur lors du chargement des postes:", error);
        postes = [];
    });
}

// Fonction pour obtenir le titre du poste
function getPosteNom(posteId) {
    if (!posteId || !postes) return '-';
    const poste = postes.find(p => p.id === posteId);
    return poste ? poste.titre : '-';
}

// Fonction pour calculer l'âge
function calculateAge(birthDate) {
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    return age;
}

// Fonction pour formater la durée en texte
function formatDurationText(months) {
    months = parseInt(months);
    if (months <= 0) return '0 mois';
    if (months === 1) return '1 mois';
    if (months < 12) return months + ' mois';
    
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;
    
    let text = years === 1 ? '1 an' : years + ' ans';
    if (remainingMonths > 0) {
        text += ' ' + (remainingMonths === 1 ? '1 mois' : remainingMonths + ' mois');
    }
    return text;
}

// Initialisation au chargement de la page
$(document).ready(function() {
    // Log pour vérifier que le code s'exécute
    console.log('Script chargé et prêt');
    
    $(document).on('click', '.renew-contract', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('Bouton de reconduction cliqué');
        
        const employeeId = $(this).data('id');
        console.log('ID employé:', employeeId);
        
        // Vérifier si le modal existe
        const modalElement = document.getElementById('renewContractModal');
        console.log('Modal element:', modalElement);
        
        try {
            const bsModal = new bootstrap.Modal(modalElement);
            bsModal.show();
        } catch (error) {
            console.error('Erreur lors de l\'ouverture du modal:', error);
        }
    });
    
    // Récupérer l'ID de l'opérateur depuis le data attribute
    currentOperatorId = $('#employeesTable').data('operator-id');
    console.log('ID de l\'opérateur:', currentOperatorId);

    // Charger les données nécessaires
    loadPostes().then(function() {
        // Une fois les postes chargés, charger les employés
        loadEmployees();
    });
    
    // Rafraîchissement automatique toutes les 30 secondes
    setInterval(function() {
        loadPostes().then(loadEmployees);
    }, 30000);
});

// Fonction pour exporter les données vers Excel
function exportToExcel() {
    const table = $('#employeesTable').DataTable();
    const data = table.rows().data().toArray();
    
    if (!data || data.length === 0) {
        showAlert('Aucune donnée à exporter', 'warning');
        return;
    }

    const exportData = data.map(row => ({
        'Région': row.region_nom || '-',
        'Département': row.departement_nom || '-',
        'Sous-préfecture': row.sous_prefecture_nom || '-',
        'Nom': row.last_name || '-',
        'Prénom': row.first_name || '-',
        'Genre': row.gender || '-',
        'Âge': row.birth_date ? calculateAge(new Date(row.birth_date)) + ' ans' : '-',
        'Poste': row.poste || '-',
        'Statut Contrat': row.contract ? row.contract.status : '-',
        'Durée Contrat': row.contract_duration_months ? row.contract_duration_months + ' mois' : '-'
    }));

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Employés");

    // Ajuster la largeur des colonnes
    const wscols = [
        {wch: 20}, // Région
        {wch: 20}, // Département
        {wch: 20}, // Sous-préfecture
        {wch: 20}, // Nom
        {wch: 20}, // Prénom
        {wch: 10}, // Genre
        {wch: 10}, // Âge
        {wch: 25}, // Poste
        {wch: 15}, // Statut Contrat
        {wch: 15}  // Durée Contrat
    ];
    worksheet['!cols'] = wscols;

    const now = new Date();
    const dateStr = now.toLocaleDateString('fr-FR').replace(/\//g, '-');
    const timeStr = now.toLocaleTimeString('fr-FR').replace(/:/g, '-');
    const fileName = `Liste_Employés_${dateStr}_${timeStr}.xlsx`;

    XLSX.writeFile(workbook, fileName);
}

// Fonction pour exporter les données vers PDF
function exportToPDF() {
    try {
        // Récupérer les données de la table
        const table = $('#employeesTable').DataTable();
        const data = table.rows().data().toArray();

        if (!data || data.length === 0) {
            showAlert('Aucune donnée à exporter', 'warning');
            return;
        }

        // Créer les données pour le tableau PDF
        const tableBody = [
            // En-tête
            [
                { text: 'Région', style: 'tableHeader' },
                { text: 'Département', style: 'tableHeader' },
                { text: 'Sous-préfecture', style: 'tableHeader' },
                { text: 'Nom', style: 'tableHeader' },
                { text: 'Prénom', style: 'tableHeader' },
                { text: 'Genre', style: 'tableHeader' },
                { text: 'Âge', style: 'tableHeader' },
                { text: 'Poste', style: 'tableHeader' },
                { text: 'Statut', style: 'tableHeader' },
                { text: 'Durée', style: 'tableHeader' }
            ]
        ];

        // Ajouter les données
        data.forEach(row => {
            tableBody.push([
                row.region_nom || '-',
                row.departement_nom || '-',
                row.sous_prefecture_nom || '-',
                row.last_name || '-',
                row.first_name || '-',
                row.gender || '-',
                row.birth_date ? calculateAge(new Date(row.birth_date)) + ' ans' : '-',
                row.poste || '-',
                row.contract ? row.contract.status : '-',
                row.contract_duration_months ? row.contract_duration_months + ' mois' : '-'
            ]);
        });

        // Configuration du document PDF
        const docDefinition = {
            pageOrientation: 'landscape',
            pageSize: 'A4',
            pageMargins: [20, 40, 20, 40],
            header: {
                text: 'Liste des Employés PRESFOR',
                alignment: 'center',
                margin: [0, 20, 0, 20],
                fontSize: 16,
                bold: true
            },
            footer: function(currentPage, pageCount) {
                return {
                    text: `Page ${currentPage} sur ${pageCount}`,
                    alignment: 'center',
                    margin: [0, 10, 0, 0]
                };
            },
            content: [
                {
                    text: new Date().toLocaleDateString('fr-FR', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    }),
                    alignment: 'right',
                    margin: [0, 0, 0, 10]
                },
                {
                    table: {
                        headerRows: 1,
                        widths: Array(10).fill('auto'),
                        body: tableBody
                    }
                }
            ],
            styles: {
                tableHeader: {
                    bold: true,
                    fontSize: 10,
                    fillColor: '#059669',
                    color: 'white',
                    alignment: 'center',
                    margin: [2, 4, 2, 4]
                }
            },
            defaultStyle: {
                fontSize: 9,
                alignment: 'left'
            }
        };

        // Générer et télécharger le PDF
        try {
            const now = new Date();
            const dateStr = now.toLocaleDateString('fr-FR').replace(/\//g, '-');
            const timeStr = now.toLocaleTimeString('fr-FR').replace(/:/g, '-');
            const fileName = `Liste_Employés_PRESFOR_${dateStr}_${timeStr}.pdf`;

            pdfMake.createPdf(docDefinition).download(fileName);
        } catch (error) {
            console.error('Erreur lors de la création du PDF:', error);
            showAlert('Erreur lors de la création du PDF', 'danger');
        }
    } catch (error) {
        console.error('Erreur lors de l\'exportation PDF:', error);
        showAlert('Erreur lors de l\'exportation PDF', 'danger');
    }
}

// Gestionnaire d'événement pour l'export PDF
$('#exportPDF').off('click').on('click', function() {
    exportToPDF();
});

// Fonction pour charger le nom de l'opérateur
function loadOperatorName() {
    $.ajax({
        url: '/api/current-operator',
        method: 'GET',
        success: function(response) {
            if (response.success && response.operator) {
                $('#operatorName').text(response.operator.name);
                // Stocker l'ID de l'opérateur pour une utilisation ultérieure
                window.currentOperatorId = response.operator.id;
            } else {
                console.error('Erreur:', response.message);
                $('#operatorName').text('Utilisateur');
            }
        },
        error: function(xhr) {
            console.error('Erreur lors du chargement du nom de l\'opérateur:', xhr);
            $('#operatorName').text('Utilisateur');
        }
    });
}

// Initialisation au chargement de la page
$(document).ready(function() {
    // Charger le nom de l'opérateur
    loadOperatorName();
    
    // Mettre à jour l'heure toutes les secondes
    setInterval(updateTime, 1000);
    updateTime();
    
});

// Fonction pour mettre à jour l'heure
function updateTime() {
    const now = new Date();
    const options = { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit',
        hour12: false 
    };
    $('#currentTime').text(now.toLocaleTimeString('fr-FR', options));
}

// Fonction pour charger le nom de l'opérateur
function loadOperatorName() {
    $.ajax({
        url: '/api/current-operator',
        method: 'GET',
        success: function(response) {
            if (response.success && response.operator) {
                $('#operatorName').text(response.operator.name);
                // Stocker l'ID de l'opérateur pour une utilisation ultérieure
                window.currentOperatorId = response.operator.id;
            } else {
                console.error('Erreur:', response.message);
                $('#operatorName').text('Utilisateur');
            }
        },
        error: function(xhr) {
            console.error('Erreur lors du chargement du nom de l\'opérateur:', xhr);
            $('#operatorName').text('Utilisateur');
        }
    });
}

// Gestionnaire pour le bouton d'édition
$(document).on('click', '.edit-employee', function(e) {
    e.preventDefault();
    const employeeId = $(this).data('id');
    if (employeeId) {
        currentEmployeeId = employeeId; // Définir l'ID
        console.log('Mode édition - ID:', currentEmployeeId);
        
        // Charger les données de l'employé
        $.ajax({
            url: `/api/employees/${employeeId}`,
            method: 'GET',
            success: function(response) {
                if (response && response.employee) {
                    const employee = response.employee;
                    
                    // Remplir le formulaire
                    $('#firstName').val(employee.first_name || '');
                    $('#lastName').val(employee.last_name || '');
                    $('#gender').val(employee.gender || '');
                    $('#birthDate').val(employee.birth_date ? employee.birth_date.split('T')[0] : '');
                    $('#region').val(employee.region_id || '');
                    $('#departement').val(employee.departement_id || '');
                    $('#sousprefecture').val(employee.sous_prefecture_id || '');
                    $('#additionalInfo').val(employee.additional_info || '');
                    $('#contractDuration').val(employee.contract_duration || 3);
                    $('#poste').val(employee.poste_id || null);  // Changé de position à poste
                    $('#contact').val(employee.contact || '');
                    $('#contractStartDate').val(employee.contract_start_date || '');
                    
                    // Nouveaux champs
                    $('#ecole').val(employee.ecole_id || '');
                    $('#diplome').val(employee.diplome_id || '');
                    $('#categorie').val(employee.categorie || '');
                    $('#contract_type').val(employee.contract_type || 'CDD');
                    
                    // Mettre à jour le titre du modal
                    $('#addEmployeeModal .modal-title').html('<i class="fas fa-user-edit me-2"></i>Modifier un Employé');
                    $('#addEmployeeModal').modal('show');
                    
                    console.log('Formulaire rempli pour édition - ID:', currentEmployeeId);
                } else {
                    showAlert('Erreur: données de l\'employé non trouvées', 'danger');
                    currentEmployeeId = null;
                }
            },
            error: function(xhr) {
                showAlert('Erreur lors du chargement des données', 'danger');
                currentEmployeeId = null;
            }
        });
    }
});

function submitEmployeeForm(event) {
    event.preventDefault();
    const formData = {
        first_name: $('#firstName').val(),
        last_name: $('#lastName').val(),
        gender: $('#gender').val(),
        birth_date: $('#birthDate').val(),
        region_id: $('#region').val() || null,
        departement_id: $('#departement').val() || null,
        sous_prefecture_id: $('#sousprefecture').val() || null,
        additional_info: $('#additionalInfo').val() || null,
        contact: $('#contact').val(),
        contract_duration: parseInt($('#contractDuration').val()) || 3,
        contract_start_date: $('#contractStartDate').val(),
        
        // Ensure these fields are properly formatted
        ecole_id: $('#ecole').val() || null,
        diplome_id: $('#diplome').val() || null,
        poste_id: $('#poste').val() || null,  // Assurez-vous que c'est null si aucune valeur n'est sélectionnée
        poste: $('#poste option:selected').text() || null,  // Ajout du texte du poste sélectionné
        categorie: $('#categorie').val(),
        contract_type: $('#contract_type').val() || 'CDD',
        operator_id: window.currentOperatorId,
        availability: $('input[name="availability"]:checked').val() || 'Au siège'  // Mise à jour du sélecteur
    };

    console.log('Données du formulaire à envoyer:', formData);

    const url = currentEmployeeId ? 
        `/api/employees/${currentEmployeeId}` : 
        '/api/employees';
    
    const method = currentEmployeeId ? 'PUT' : 'POST';

    // Envoyer la requête
    $.ajax({
        url: url,
        method: method,
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            if (response.success) {
                showAlert(
                    currentEmployeeId ? 
                    "Employé modifié avec succès" : 
                    "Employé créé avec succès", 
                    "success"
                );
                
                // Fermer le modal en utilisant Bootstrap
                $('#addEmployeeModal').modal('hide');
                
                // Réinitialiser le formulaire
                $('#employeeForm')[0].reset();
                
                // Rafraîchir la liste des employés
                loadEmployees();
                
                // Réinitialiser l'ID courant
                currentEmployeeId = null;
            } else {
                showAlert(response.error || "Une erreur est survenue", "danger");
            }
        },
        error: function(xhr) {
            console.error('Erreur:', xhr.responseJSON);
            showAlert(xhr.responseJSON?.error || "Erreur lors de l'opération", "danger");
       }
    });
}

// Gestionnaire pour le formulaire
$('#addEmployeeForm').on('submit', function(e) {
    submitEmployeeForm(e);
});

// Gestionnaire pour la fermeture du modal
$('#addEmployeeModal').on('hidden.bs.modal', function() {
    $('#addEmployeeForm')[0].reset();
    $('#addEmployeeModal .modal-title').html('<i class="fas fa-user-plus me-2"></i>Ajouter un Employé');
    currentEmployeeId = null;
});

// Gestionnaire pour le bouton d'ajout
$('#addEmployeeBtn').on('click', function() {
    currentEmployeeId = null; // S'assurer que nous sommes en mode création
    $('#addEmployeeForm')[0].reset();
    $('#addEmployeeModal .modal-title').html('<i class="fas fa-user-plus me-2"></i>Ajouter un Employé');
    $('#addEmployeeModal').modal('show');
});

// Fonction pour formater une date
function formatDate(dateStr) {
    if (!dateString) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR');
}

// Fonction pour afficher le modal de changement de mot de passe
function showChangePasswordModal() {
    // Réinitialiser le formulaire
    document.getElementById('changePasswordForm').reset();
    // Afficher le modal
    new bootstrap.Modal(document.getElementById('changePasswordModal')).show();
}

// Fonction pour changer le mot de passe
function changePassword() {
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (newPassword !== confirmPassword) {
        showAlert('danger', 'Les nouveaux mots de passe ne correspondent pas');
        return;
    }

    fetch('/api/change-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Mot de passe modifié avec succès');
            bootstrap.Modal.getInstance(document.getElementById('changePasswordModal')).hide();
        } else {
            showAlert('danger', data.error || 'Erreur lors de la modification du mot de passe');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'Erreur lors de la modification du mot de passe');
    });
}

// Fonction pour gérer le changement de thème
function toggleTheme() {
    const root = document.documentElement;
    const isDark = root.getAttribute('data-theme') === 'dark';
    
    if (isDark) {
        root.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
    } else {
        root.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
    }
    
    // Mettre à jour l'apparence des éléments spécifiques
    updateThemeSpecificElements(!isDark);
}

// Fonction pour mettre à jour les éléments spécifiques au thème
function updateThemeSpecificElements(isDark) {
    const navbar = document.querySelector('.navbar');
    if (isDark) {
        navbar.classList.remove('navbar-light', 'bg-light');
        navbar.classList.add('navbar-dark', 'bg-dark');
    } else {
        navbar.classList.remove('navbar-dark', 'bg-dark');
        navbar.classList.add('navbar-light', 'bg-light');
    }
}

// Initialisation du thème au chargement
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme');
    const root = document.documentElement;
    
    if (savedTheme === 'dark') {
        root.setAttribute('data-theme', 'dark');
        updateThemeSpecificElements(true);
    }
    
    // Gestionnaire pour le switch de thème
    document.querySelector('.theme-switch input[type="checkbox"]').addEventListener('change', toggleTheme);
});

// Gestionnaire pour le bouton de reconduction
$(document).on('click', '.btn-renew', function(e) {
    e.preventDefault();
    e.stopPropagation();
    const employeeId = $(this).data('id');
    const firstName = $(this).data('first-name');
    const lastName = $(this).data('last-name');
    console.log('Clic sur le bouton de reconduction:', employeeId, firstName, lastName);
    openRenewModal(employeeId, firstName, lastName);
});

// Fonction pour ouvrir le modal de reconduction
function openRenewModal(employeeId, firstName, lastName) {
    console.log('Ouverture du modal de reconduction pour:', employeeId, firstName, lastName);
    
    // Réinitialiser le formulaire
    $('#renewContractForm')[0].reset();
    
    // Remplir les champs d'identification
    $('#renewEmployeeId').val(employeeId);
    $('#renewFirstName').val(firstName);
    $('#renewLastName').val(lastName);
    
    // Définir la date de début par défaut à aujourd'hui
    const today = new Date().toISOString().split('T')[0];
    $('#renewStartDate').val(today);
    
    // Définir une durée par défaut de 3 mois
    $('#renewDuration').val(3);
    
    // Calculer la date de fin initiale
    calculateRenewEndDate();
    
    // Charger les données de l'employé actuel
    $.get(`/api/employees/${employeeId}`, function(response) {
        if (response.success && response.employee) {
            const employee = response.employee;
            
            // Définir la situation géographique
            if (employee.location === 'Au siège') {
                $('#renewAuSiege').prop('checked', true);
                $('#renewLocationFields select').prop('disabled', true);
            } else {
                $('#renewALInterieur').prop('checked', true);
                $('#renewLocationFields select').prop('disabled', false);
                
                // Charger les régions
                $.get('/api/regions', function(data) {
                    if (data.success && data.data) {
                        const regionSelect = $('#renewRegion');
                        regionSelect.empty().append('<option value="">Sélectionner une région</option>');
                        data.data.forEach(region => {
                            regionSelect.append(`<option value="${region.id}">${region.name}</option>`);
                        });
                        
                        // Pré-remplir la région si elle existe
                        if (employee.region_id) {
                            regionSelect.val(employee.region_id);
                            
                            // Charger les départements de cette région
                            $.get(`/api/departements/${employee.region_id}`, function(deptData) {
                                if (deptData.success && deptData.data) {
                                    const departementSelect = $('#renewDepartement');
                                    departementSelect.empty().append('<option value="">Sélectionner un département</option>');
                                    deptData.data.forEach(dept => {
                                        departementSelect.append(`<option value="${dept.id}">${dept.name}</option>`);
                                    });
                                    departementSelect.prop('disabled', false);
                                    
                                    // Pré-remplir le département si il existe
                                    if (employee.departement_id) {
                                        departementSelect.val(employee.departement_id);
                                        
                                        // Charger les sous-préfectures de ce département
                                        $.get(`/api/sousprefectures/${employee.departement_id}`, function(spData) {
                                            if (spData.success && spData.data) {
                                                const spSelect = $('#renewSousprefecture');
                                                spSelect.empty().append('<option value="">Sélectionner une sous-préfecture</option>');
                                                spData.data.forEach(sp => {
                                                    spSelect.append(`<option value="${sp.id}">${sp.name}</option>`);
                                                });
                                                spSelect.prop('disabled', false);
                                                
                                                // Pré-remplir la sous-préfecture si elle existe
                                                if (employee.sous_prefecture_id) {
                                                    spSelect.val(employee.sous_prefecture_id);
                                                }
                                            }
                                        });
                                    }
                                }
                            });
                        }
                    }
                });
            }
            
            // Pré-remplir les autres champs si disponibles
            if (employee.poste_id) $('#renewPosition').val(employee.poste_id);
            if (employee.categorie) $('#renewCategorie').val(employee.categorie);
            if (employee.diplome_id) $('#renewDiplome').val(employee.diplome_id);
            if (employee.ecole_id) $('#renewEcole').val(employee.ecole_id);
        }
    });
    
    // Afficher le modal
    $('#renewContractModal').modal('show');
}

// Gestionnaire pour le changement de durée ou date de début dans le modal de reconduction
function calculateRenewEndDate() {
    const startDate = $('#renewStartDate').val();
    const duration = parseInt($('#renewDuration').val()) || 0;
    
    if (startDate && duration > 0) {
        const endDate = new Date(startDate);
        endDate.setMonth(endDate.getMonth() + duration);
        $('#renewEndDate').val(endDate.toISOString().split('T')[0]);
    } else {
        $('#renewEndDate').val('');
    }
}

// Attacher les gestionnaires d'événements pour le calcul de la date de fin
$('#renewStartDate, #renewDuration').on('change input', calculateRenewEndDate);

// Gestionnaire pour la soumission du formulaire de reconduction
$('#renewContractForm').on('submit', function(e) {
    e.preventDefault();
    
    // Récupérer toutes les valeurs du formulaire
    const formData = {
        employee_ids: [$('#renewEmployeeId').val()],
        start_date: $('#renewStartDate').val(),
        duration: $('#renewDuration').val(),
        location: $('input[name="renewLocation"]:checked').val(),
        region_id: $('#renewRegion').val() || null,
        departement_id: $('#renewDepartement').val() || null,
        sous_prefecture_id: $('#renewSousprefecture').val() || null,
        poste_id: $('#renewPosition').val(),
        poste: $('#renewPosition option:selected').text() || null,  // Ajout du texte du poste sélectionné
        categorie_id: $('#renewCategorie').val(),
        diplome_id: $('#renewDiplome').val(),
        ecole_id: $('#renewEcole').val()
    };

    // Log des données avant envoi
    console.log('Données envoyées:', formData);
  
    // Vérification des champs requis (sans les champs de localisation)
    const requiredFields = ['employee_ids', 'start_date', 'duration', 'poste_id', 'categorie_id', 'diplome_id', 'ecole_id'];
    const missingFields = requiredFields.filter(field => !formData[field] || 
        (Array.isArray(formData[field]) && formData[field].length === 0) || 
        (Array.isArray(formData[field]) && formData[field][0] === '') ||
        formData[field] === '');
    
    if (missingFields.length > 0) {
        showAlert(`Les champs suivants sont requis : ${missingFields.join(', ')}`, 'danger');
        return;
    }

   // Envoyer les données au serveur
    $.ajax({
        url: '/api/employees/renew',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            if (response.success) {
                $('#renewContractModal').modal('hide');
                showAlert('Le contrat a été renouvelé avec succès', 'success');
                loadEmployees();
            } else {
                showAlert(response.error || 'Une erreur est survenue lors du renouvellement du contrat', 'danger');
            }
        },
        error: function(xhr) {
            const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : 'Erreur lors du renouvellement du contrat';
            showAlert(errorMsg, 'danger');
            console.error('Erreur:', xhr);
        }
    });
});

// S'assurer que le code s'exécute une fois que le DOM est chargé
$(document).ready(function() {
    $('#submitRenewContract').on('click', function(e) {
        e.preventDefault();
        console.log('Bouton de renouvellement cliqué');
        
        const location = $('input[name="renewLocation"]:checked').val() || 'siege';
        
        const formData = {
            employee_ids: [$('#renewEmployeeId').val()],
            start_date: $('#renewStartDate').val(),
            duration: parseInt($('#renewDuration').val()),
            poste_id: $('#renewPosition').val(),
            poste: $('#renewPosition option:selected').text() || null,  // Ajout du texte du poste sélectionné
            categorie: String($('#renewCategorie').val()),
            diplome_id: $('#renewDiplome').val(),
            ecole_id: $('#renewEcole').val(),
            location: location,
            // Ne pas envoyer les champs de localisation si on est au siège
            ...(location === 'interieur' ? {
                region_id: $('#renewRegion').val() || null,
                departement_id: $('#renewDepartement').val() || null,
                sous_prefecture_id: $('#renewSousprefecture').val() || null
            } : {
                region_id: null,
                departement_id: null,
                sous_prefecture_id: null
            })
        };

        console.log('Données du formulaire à envoyer:', formData);

        // Vérification des champs requis de base
        const requiredFields = ['employee_ids', 'start_date', 'duration', 'poste_id', 'categorie', 'diplome_id', 'ecole_id'];
        const missingFields = requiredFields.filter(field => {
            const value = formData[field];
            return !value || 
                (Array.isArray(value) && value.length === 0) || 
                (Array.isArray(value) && value[0] === '') ||
                value === '';
        });

        if (missingFields.length > 0) {
            showAlert(`Veuillez remplir les champs obligatoires suivants : ${missingFields.join(', ')}`, 'danger');
            return;
        }

        // Envoyer la requête AJAX
        $.ajax({
            url: '/api/employees/renew',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                console.log('Réponse reçue:', response);
                if (response.success) {
                    // Fermer le modal en utilisant l'API Bootstrap
                    const modal = bootstrap.Modal.getInstance(document.getElementById('renewContractModal'));
                    if (modal) {
                        modal.hide();
                    }
                    
                    showAlert('Le contrat a été renouvelé avec succès', 'success');
                    
                    // Réinitialiser le formulaire
                    $('#renewContractForm')[0].reset();
                    
                    // Rafraîchir la liste des employés
                    loadEmployees();
                } else {
                    showAlert(response.error || 'Une erreur est survenue lors du renouvellement du contrat', 'danger');
                }
            },
            error: function(xhr) {
                console.error('Erreur AJAX:', xhr);
                const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : 'Erreur lors du renouvellement du contrat';
                showAlert(errorMsg, 'danger');
            }
        });
    });

    // Gestionnaire pour le changement de localisation
    $('input[name="renewLocation"]').on('change', function() {
        const isInterieur = $(this).val() === 'interieur';
        $('#renewLocationFields select').prop('disabled', !isInterieur);
        if (!isInterieur) {
            $('#renewRegion, #renewDepartement, #renewSousprefecture').val('');
        }
    });


    // Ajouter un gestionnaire pour calculer automatiquement la date de fin
    $('#renewStartDate, #renewDuration').on('change', function() {
        const startDate = $('#renewStartDate').val();
        const duration = $('#renewDuration').val();
        
        if (startDate && duration) {
            const endDate = new Date(startDate);
            endDate.setMonth(endDate.getMonth() + parseInt(duration));
            $('#renewEndDate').val(endDate.toISOString().split('T')[0]);
        }
    });
});

// Charger les données au moment de l'ouverture du modal de reconduction
$('#renewContractModal').on('show.bs.modal', function() {
    console.log('Ouverture du modal de reconduction');
    
    // Activer/désactiver les champs de localisation selon la situation géographique
    $('input[name="renewLocation"]').on('change', function() {
        const isInterieur = $(this).val() === 'interieur';
        $('#renewLocationFields select').prop('disabled', !isInterieur);
        if (!isInterieur) {
            $('#renewRegion, #renewDepartement, #renewSousprefecture').val('');
        }
    });

    // Charger les régions
    $.get('/api/regions', function(data) {
        console.log('Régions reçues:', data);
        const select = $('#renewRegion');
        select.empty().append('<option value="">Sélectionner une région</option>');
        if (data.success && data.data) {
            data.data.forEach(region => {
                select.append(`<option value="${region.id}">${region.name}</option>`);
            });
        }
    }).fail(function(err) {
        console.error('Erreur lors du chargement des régions:', err);
    });

    // Gestionnaire pour le changement de région
    $('#renewRegion').off('change').on('change', function() {
        const regionId = $(this).val();
        const departementSelect = $('#renewDepartement');
        const sousprefectureSelect = $('#renewSousprefecture');
        
        departementSelect.empty().append('<option value="">Sélectionner un département</option>');
        sousprefectureSelect.empty().append('<option value="">Sélectionner une sous-préfecture</option>');
        
        if (regionId) {
            // Charger les départements
            $.get(`/api/departements/${regionId}`, function(data) {
                console.log('Départements reçus:', data);
                if (data.success && data.data) {
                    data.data.forEach(dept => {
                        departementSelect.append(`<option value="${dept.id}">${dept.name}</option>`);
                    });
                    departementSelect.prop('disabled', false);
                }
            }).fail(function(err) {
                console.error('Erreur lors du chargement des départements:', err);
            });
        } else {
            departementSelect.prop('disabled', true);
            sousprefectureSelect.prop('disabled', true);
        }
    });

    // Gestionnaire pour le changement de département
    $('#renewDepartement').off('change').on('change', function() {
        const departementId = $(this).val();
        const sousprefectureSelect = $('#renewSousprefecture');
        
        sousprefectureSelect.empty().append('<option value="">Sélectionner une sous-préfecture</option>');
        
        if (departementId) {
            // Charger les sous-préfectures
            $.get(`/api/sousprefectures/${departementId}`, function(data) {
                console.log('Sous-préfectures reçues:', data);
                if (data.success && data.data) {
                    data.data.forEach(sp => {
                        sousprefectureSelect.append(`<option value="${sp.id}">${sp.name}</option>`);
                    });
                    sousprefectureSelect.prop('disabled', false);
                }
            }).fail(function(err) {
                console.error('Erreur lors du chargement des sous-préfectures:', err);
            });
        } else {
            sousprefectureSelect.prop('disabled', true);
        }
    });

    // Charger les postes
    $.get('/api/postes', function(data) {
        console.log('Postes reçus:', data);
        const select = $('#renewPosition');
        select.empty().append('<option value="">Sélectionner un poste</option>');
        if (data.success && data.data) {
            data.data.forEach(poste => {
                select.append(`<option value="${poste.id}">${poste.titre}</option>`);
            });
        }
    }).fail(function(err) {
        console.error('Erreur lors du chargement des postes:', err);
    });

    // Charger les catégories
    $.get('/api/categories', function(data) {
        console.log('Catégories reçues:', data);
        const select = $('#renewCategorie');
        select.empty().append('<option value="">Sélectionner une catégorie</option>');
        if (data.success && data.data) {
            data.data.forEach(cat => {
                select.append(`<option value="${cat.id}">${cat.name}</option>`);
            });
        }
    }).fail(function(err) {
        console.error('Erreur lors du chargement des catégories:', err);
    });

    // Charger les diplômes
    $.get('/api/diplomes', function(data) {
        console.log('Diplômes reçus:', data);
        const select = $('#renewDiplome');
        select.empty().append('<option value="">Sélectionner un diplôme</option>');
        if (data.success && data.data) {
            data.data.forEach(diplome => {
                select.append(`<option value="${diplome.id}">${diplome.name}</option>`);
            });
        }
    }).fail(function(err) {
        console.error('Erreur lors du chargement des diplômes:', err);
    });

    // Charger les écoles
    $.get('/api/ecoles', function(data) {
        console.log('Écoles reçues:', data);
        const select = $('#renewEcole');
        select.empty().append('<option value="">Sélectionner une école</option>');
        if (data.success && data.data) {
            data.data.forEach(ecole => {
                select.append(`<option value="${ecole.id}">${ecole.name}</option>`);
            });
        }
    }).fail(function(err) {
        console.error('Erreur lors du chargement des écoles:', err);
    });
});

// Gestionnaire pour le changement de situation géographique
$('input[name="renewLocation"]').on('change', function() {
    const isInterieur = $(this).val() === 'interieur';
    const locationFields = $('#renewRegion, #renewDepartement, #renewSousprefecture');
    
    locationFields.prop('disabled', !isInterieur);
    
    if (isInterieur) {
        // Charger les régions si "À l'intérieur" est sélectionné
        $.get('/api/regions', function(data) {
            console.log('Régions reçues:', data);
            const select = $('#renewRegion');
            select.empty().append('<option value="">Sélectionner une région</option>');
            if (data.success && data.data) {
                data.data.forEach(region => {
                    select.append(`<option value="${region.id}">${region.name}</option>`);
                });
                select.prop('disabled', false);
            }
        }).fail(function(err) {
            console.error('Erreur lors du chargement des régions:', err);
        });
    } else {
        // Réinitialiser les champs si "Au siège" est sélectionné
        locationFields.val('');
    }
});

// Gestionnaire pour le changement de région
$('#renewRegion').on('change', function() {
    const regionId = $(this).val();
    if (regionId) {
        $.get(`/api/departements/${regionId}`, function(data) {
            console.log('Départements reçus:', data);
            const select = $('#renewDepartement');
            select.empty().append('<option value="">Sélectionner un département</option>');
            if (data.success && data.data) {
                data.data.forEach(dept => {
                    select.append(`<option value="${dept.id}">${dept.name}</option>`);
                });
                select.prop('disabled', false);
            }
        }).fail(function(err) {
            console.error('Erreur lors du chargement des départements:', err);
        });
    }
});

// Gestionnaire pour le changement de département
$('#renewDepartement').on('change', function() {
    const deptId = $(this).val();
    if (deptId) {
        $.get(`/api/sousprefectures/${deptId}`, function(data) {
            console.log('Sous-préfectures reçues:', data);
            const select = $('#renewSousprefecture');
            select.empty().append('<option value="">Sélectionner une sous-préfecture</option>');
            if (data.success && data.data) {
                data.data.forEach(sp => {
                    select.append(`<option value="${sp.id}">${sp.name}</option>`);
                });
                select.prop('disabled', false);
            }
        }).fail(function(err) {
            console.error('Erreur lors du chargement des sous-préfectures:', err);
        });
    }
});

// Initialisation des modals Bootstrap au chargement de la page
let addEmployeeModal;

$(document).ready(function() {
    // Initialiser le modal une seule fois
    addEmployeeModal = new bootstrap.Modal(document.getElementById('addEmployeeModal'), {
        backdrop: 'static',
        keyboard: false
    });
});

// Fonction pour réinitialiser le formulaire
function resetEmployeeForm() {
    $('#addEmployeeForm')[0].reset();
    currentEmployeeId = null;
    $('#addEmployeeModal .modal-title').html('<i class="fas fa-user-plus me-2"></i>Ajouter un Employé');
}

// Gestionnaire pour le bouton d'ajout d'employé
$('#addEmployeeBtn').on('click', function() {
    resetEmployeeForm();
    $('#addEmployeeModal').modal('show');
});

// Gestionnaire pour la fermeture du modal
$('#addEmployeeModal').on('hidden.bs.modal', function() {
    resetEmployeeForm();
});

// Gestionnaire pour les boutons radio de localisation
$('input[name="location"]').on('change', function() {
    const isInterieur = $('#aLInterieur').is(':checked');
    $('#locationFields select').prop('disabled', !isInterieur);
    if (!isInterieur) {
        $('#locationFields select').val('');
    }
});

// Gestionnaire pour le bouton de visualisation des contrats
$(document).on('click', '.view-contracts', function(e) {
    e.preventDefault();
    const employeeId = $(this).data('id');
    const firstName = $(this).data('first-name');
    const lastName = $(this).data('last-name');
    
    // Mettre à jour le titre du modal avec le nom de l'employé
    $('#viewContractsModal .modal-title').html(`
        <i class="fas fa-history me-2"></i>Historique des Contrats - ${firstName} ${lastName}
    `);
    
    // Stocker l'ID de l'employé dans le modal pour l'export
    $('#viewContractsModal').data('employee-id', employeeId);
    
    // Charger l'historique des contrats
    $.ajax({
        url: `/api/employees/${employeeId}/contracts`,
        method: 'GET',
        beforeSend: function() {
            $('.loader').addClass('loading');
            $('#contractsTableBody').html('<tr><td colspan="5" class="text-center">Chargement...</td></tr>');
        },
        success: function(response) {
            if (response.success && response.contracts) {
                let html = '';
                response.contracts.forEach(function(contract) {
                    const startDate = contract.start_date ? new Date(contract.start_date).toLocaleDateString() : '-';
                    const endDate = contract.end_date ? new Date(contract.end_date).toLocaleDateString() : '-';
                    const duration = contract.duration_months ? `${contract.duration_months} mois` : '-';
                    const statusClass = contract.status === 'Expiré' ? 'text-danger' : 'text-success';
                    
                    html += `
                        <tr>
                            <td>${startDate}</td>
                            <td>${endDate}</td>
                            <td>${duration}</td>
                            <td>${contract.position || '-'}</td>
                            <td><span class="${statusClass}">${contract.status || '-'}</span></td>
                        </tr>
                    `;
                });
                $('#contractsTableBody').html(html || '<tr><td colspan="5" class="text-center">Aucun contrat trouvé</td></tr>');
            } else {
                $('#contractsTableBody').html('<tr><td colspan="5" class="text-center">Aucun contrat trouvé</td></tr>');
            }
        },
        error: function(xhr) {
            console.error('Erreur:', xhr);
            $('#contractsTableBody').html('<tr><td colspan="5" class="text-center text-danger">Erreur lors du chargement des contrats</td></tr>');
            showAlert("Erreur lors du chargement des contrats", "danger");
        },
        complete: function() {
            $('.loader').removeClass('loading');
        }
    });
    
    // Ouvrir le modal
    const modal = new bootstrap.Modal(document.getElementById('viewContractsModal'));
    modal.show();
});

function showContractsHistory(employeeId, firstName, lastName) {
    console.log(`Récupération des contrats pour l'employé ${employeeId}`);
    $.ajax({
        url: `/api/employees/${employeeId}/contracts`,
        method: 'GET',
        success: function(response) {
            console.log('Réponse reçue:', response); // Pour déboguer
            if (response.success && response.contracts && response.contracts.length > 0) {
                let html = '';
                response.contracts.forEach(contract => {
                    // Déboguer les données de chaque contrat
                    console.log('Données du contrat:', contract);
                    
                    const startDate = contract.start_date || '-';
                    const endDate = contract.end_date || '-';
                    const duration = contract.duration || '-';
                    const statusClass = contract.status === 'Expiré' ? 'text-danger' : 'text-success';
                    
                    // Utiliser le titre du poste depuis la bonne propriété
                    const poste = contract.poste || 'Non spécifié';
                    
                    html += `
                        <tr>
                            <td>${startDate}</td>
                            <td>${endDate}</td>
                            <td>${duration}</td>
                            <td>${poste}</td>
                            <td><span class="${statusClass}">${contract.status || '-'}</span></td>
                        </tr>
                    `;
                });
                $('#contractsTableBody').html(html);
            } else {
                $('#contractsTableBody').html('<tr><td colspan="5" class="text-center">Aucun contrat trouvé</td></tr>');
            }
        },
        error: function(xhr) {
            console.error('Erreur:', xhr);
            $('#contractsTableBody').html('<tr><td colspan="5" class="text-center text-danger">Erreur lors du chargement des contrats</td></tr>');
            showAlert("Erreur lors du chargement des contrats", "danger");
        }
    });
    
    // Ouvrir le modal
    const modal = new bootstrap.Modal(document.getElementById('viewContractsModal'));
    modal.show();
}

// Gestionnaire pour l'export Excel des contrats
$('#exportContractsExcel').on('click', function() {
    const employeeId = $('#viewContractsModal').data('employee-id');
    const employeeName = $('#viewContractsModal .modal-title').text().split('-')[1].trim();
    
    // Récupérer les données de la table
    const data = [];
    $('#contractsTableBody tr').each(function() {
        const row = [];
        $(this).find('td').each(function() {
            row.push($(this).text().trim());
        });
        data.push(row);
    });
    
    // Créer le workbook
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet([
        ['Date de début', 'Date de fin', 'Durée', 'Poste', 'Statut'],
        ...data
    ]);
    
    // Ajouter la feuille au workbook
    XLSX.utils.book_append_sheet(wb, ws, "Contrats");
    
    // Générer le fichier Excel
    XLSX.writeFile(wb, `Contrats_${employeeName}.xlsx`);
});

// Gestionnaire pour l'export PDF des contrats
$('#exportContractsPDF').on('click', function() {
    const employeeName = $('#viewContractsModal .modal-title').text().split('-')[1].trim();
    
    // Récupérer les données du tableau
    const tableBody = [];
    $('#contractsTableBody tr').each(function() {
        const row = [];
        $(this).find('td').each(function() {
            row.push($(this).text().trim());
        });
        tableBody.push(row);
    });
    
    // Définir le document
    const docDefinition = {
        content: [
            { text: `Historique des Contrats - ${employeeName}`, style: 'header' },
            {
                table: {
                    headerRows: 1,
                    body: [
                        ['Date de début', 'Date de fin', 'Durée', 'Poste', 'Statut'],
                        ...tableBody
                    ]
                }
            }
        ],
        styles: {
            header: {
                fontSize: 18,
                bold: true,
                margin: [0, 0, 0, 10]
            }
        },
        defaultStyle: {
            fontSize: 9,
            alignment: 'left'
        }
    };
    
    // Générer le PDF
    pdfMake.createPdf(docDefinition).download(`Contrats_${employeeName}.pdf`);
});

// Fonction pour calculer la date de fin
function calculateEndDate(startDate, durationMonths) {
    const date = startDate ? new Date(startDate) : new Date();
    date.setMonth(date.getMonth() + parseInt(durationMonths));
    return date.toISOString().split('T')[0];
}

// Gestionnaire pour la durée du contrat et la date de début
function handleContractDurationChange() {
    const duration = document.getElementById('contractDuration').value;
    const startDate = document.getElementById('contractStartDate').value;
    const endDateInput = document.getElementById('contractEndDate');
    
    if (duration) {
        // Mettre à jour le texte de la durée
        document.querySelector('.contract-duration-text').textContent = formatDurationText(duration);
        
        const endDate = calculateEndDate(startDate, duration);
        endDateInput.value = endDate;
        
        // Vérifier si la date de fin est dans le futur
        const today = new Date();
        const endDateObj = new Date(endDate);
        const warningSection = document.querySelector('.contract-expiration-section');
        
        if (endDateObj < today) {
            warningSection.style.display = 'block';
        } else {
            warningSection.style.display = 'none';
        }
    }
}

// Ajouter les écouteurs d'événements
document.addEventListener('DOMContentLoaded', function() {
    const durationInput = document.getElementById('contractDuration');
    const startDateInput = document.getElementById('contractStartDate');
    
    if (durationInput) {
        durationInput.addEventListener('change', handleContractDurationChange);
        durationInput.addEventListener('input', handleContractDurationChange);
        
        // Mettre à jour le texte de la durée
        durationInput.addEventListener('input', function() {
            const months = this.value;
            const text = formatDurationText(months);
            document.querySelector('.contract-duration-text').textContent = text;
        });
    }
    
    if (startDateInput) {
        startDateInput.addEventListener('change', handleContractDurationChange);
        
        // Définir la date du jour par défaut
        if (!startDateInput.value) {
            startDateInput.value = new Date().toISOString().split('T')[0];
            handleContractDurationChange();
        }
    }
});

// Fonction pour afficher les détails de l'employé
function showEmployeeDetails(employee) {
    currentEmployeeId = employee.id;
    const modal = document.getElementById('employeeModal');
    
    // Remplir les champs du formulaire avec les données de l'employé
    document.getElementById('first_name').value = employee.first_name || '';
    document.getElementById('last_name').value = employee.last_name || '';
    document.getElementById('gender').value = employee.gender || '';
    document.getElementById('birth_date').value = employee.birth_date || '';
    document.getElementById('contact').value = employee.contact || '';
    document.getElementById('additional_info').value = employee.additional_info || '';
    document.getElementById('poste').value = employee.poste_id || '';  // Changé de position à poste
    document.getElementById('contractDuration').value = employee.contract_duration || '3';
    
    // Nouveaux champs
    const ecoleSelect = document.getElementById('ecole');
    const diplomeSelect = document.getElementById('diplome');
    const categorieSelect = document.getElementById('categorie');
    const posteTypeSelect = document.getElementById('poste_type');
    
    // Réinitialiser l'affichage des champs "autre"
    document.getElementById('autreEcoleDiv').style.display = 'none';
    document.getElementById('autreDiplomeDiv').style.display = 'none';
    document.getElementById('autreCategorieDiv').style.display = 'none';
    
    // Gérer les cas "autre" pour chaque select
    if (employee.ecole_id) {
        if (Array.from(ecoleSelect.options).some(opt => opt.value === employee.ecole_id)) {
            ecoleSelect.value = employee.ecole_id;
        } else {
            ecoleSelect.value = 'autre';
            document.getElementById('autreEcole').value = employee.ecole_id;
            document.getElementById('autreEcoleDiv').style.display = 'block';
        }
    } else {
        ecoleSelect.value = '';
    }
    
    if (employee.diplome_id) {
        if (Array.from(diplomeSelect.options).some(opt => opt.value === employee.diplome_id)) {
            diplomeSelect.value = employee.diplome_id;
        } else {
            diplomeSelect.value = 'autre';
            document.getElementById('autreDiplome').value = employee.diplome_id;
            document.getElementById('autreDiplomeDiv').style.display = 'block';
        }
    } else {
        diplomeSelect.value = '';
    }
    
    if (employee.categorie) {
        if (Array.from(categorieSelect.options).some(opt => opt.value === employee.categorie)) {
            categorieSelect.value = employee.categorie;
        } else {
            categorieSelect.value = 'autre';
            document.getElementById('autreCategorie').value = employee.categorie;
            document.getElementById('autreCategorieDiv').style.display = 'block';
        }
    } else {
        categorieSelect.value = '';
    }
    
    if (employee.poste_id) {
        posteTypeSelect.value = employee.poste_id;
    } else {
        posteTypeSelect.value = '';
    }
    
    // Utiliser la date de début existante du contrat ou la date du jour
    const today = new Date();
    const startDate = employee.contract_start_date || today;
    document.getElementById('contractStartDate').value = startDate;
    
    // Calculer et afficher la date de fin
    handleContractDurationChange();
    
    // Mise à jour des autres champs...
    updateRegions(employee.region_id);
    if (employee.region_id) {
        updateDepartements(employee.region_id, employee.departement_id);
    }
    if (employee.departement_id) {
        updateSousPrefectures(employee.departement_id, employee.sous_prefecture_id);
    }
    
    // Afficher le modal
    document.getElementById('modalTitle').textContent = 'Modifier un employé';
    modal.style.display = 'block';
}

// Fonction pour charger les employés
function loadEmployees() {
    $.get('/api/employees', function(response) {
        if (!response.success || !response.employees) {
            console.error("Réponse invalide:", response);
            showAlert("Erreur lors du chargement des employés", "danger");
            return;
        }

        // Initialiser DataTable si ce n'est pas déjà fait
        let table = $('#employeesTable').DataTable();
        if (table) {
            table.clear().destroy();
        }

        table = $('#employeesTable').DataTable({
            language: {
                url: 'https://cdn.datatables.net/plug-ins/1.13.7/i18n/fr-FR.json'
            },
            responsive: true,
            data: response.employees,
            columns: [
                { 
                    data: null,
                    render: function(data) {
                        return data.region_nom || '-';
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        return data.departement_nom || '-';
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        return data.sous_prefecture_nom || '-';
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        return data.last_name || '-';
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        return data.first_name || '-';
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        return data.gender || '-';
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        if (!data.birth_date) return '-';
                        const birthDate = new Date(data.birth_date);
                        const age = calculateAge(birthDate);
                        return age ? age + ' ans' : '-';
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        return data.poste || '-';
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        if (!data.contract || !data.contract.status) return '-';
                        const status = data.contract.status;
                        const statusClass = status === 'Expiré' ? 'text-danger' : 'text-success';
                        return `<span class="${statusClass}">${status}</span>`;
                    }
                },
                { 
                    data: null,
                    render: function(data) {
                        if (!data.contract || !data.contract.start_date || !data.contract.end_date) {
                            return data.contract_duration_months ? data.contract_duration_months + ' mois' : '-';
                        }
                        const startDate = new Date(data.contract.start_date);
                        const endDate = new Date(data.contract.end_date);
                        const diffTime = Math.abs(endDate - startDate);
                        const diffMonths = Math.ceil(diffTime / (1000 * 60 * 60 * 24 * 30.44));
                        return diffMonths + ' mois';
                    }
                },
                {
                    data: null,
                    render: function(data) {
                        let buttons = `
                            <div class="btn-group">
                                <button class="btn btn-sm btn-primary edit-employee" data-id="${data.id}" title="Modifier">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-info view-contracts" data-id="${data.id}" data-first-name="${data.first_name}" data-last-name="${data.last_name}" title="Voir les détails">
                                    <i class="fas fa-eye"></i>
                                </button>`;
                        
                        // Ajouter le bouton de reconduction uniquement si le contrat est expiré
                        if (data.contract && data.contract.status === 'Expiré') {
                            buttons += `
                                <button class="btn btn-sm btn-warning btn-renew" data-id="${data.id}" data-first-name="${data.first_name}" data-last-name="${data.last_name}" title="Reconduire le contrat">
                                    <i class="fas fa-sync-alt"></i>
                                </button>`;
                        }
                        
                        buttons += `</div>`;
                        return buttons;
                    }
                }
            ],
            order: [[3, 'asc']]  // Tri par nom de famille
        });

        // Mettre à jour les statistiques après le chargement
        loadStats();
    })
    .fail(function(xhr) {
        console.error("Erreur lors du chargement des employés:", xhr.responseText);
        showAlert("Erreur lors du chargement des employés", "danger");
    });
}

function showContractsHistory(employeeId, firstName, lastName) {
    console.log(`Récupération des contrats pour l'employé ${employeeId}`);
    $.ajax({
        url: `/api/employees/${employeeId}/contracts`,
        method: 'GET',
        success: function(response) {
            console.log('Réponse reçue:', response); // Pour déboguer
            if (response.success && response.contracts && response.contracts.length > 0) {
                let html = '';
                response.contracts.forEach(contract => {
                    console.log('Données du contrat:', contract);
                    
                    const startDate = contract.start_date || '-';
                    const endDate = contract.end_date || '-';
                    const duration = contract.duration || '-';
                    
                    // Définir la classe CSS en fonction du statut
                    let statusClass;
                    switch(contract.status) {
                        case 'Expiré':
                            statusClass = 'text-danger';
                            break;
                        case 'En cours':
                            statusClass = 'text-success';
                            break;
                        case 'À venir':
                            statusClass = 'text-primary';
                            break;
                        default:
                            statusClass = 'text-secondary';
                    }
                    
                    // Utiliser le titre du poste depuis la bonne propriété
                    const poste = contract.poste || 'Non spécifié';
                    
                    html += `
                        <tr>
                            <td>${startDate}</td>
                            <td>${endDate}</td>
                            <td>${duration}</td>
                            <td>${poste}</td>
                            <td><span class="${statusClass}">${contract.status || '-'}</span></td>
                        </tr>
                    `;
                });
                $('#contractsTableBody').html(html);
            } else {
                $('#contractsTableBody').html('<tr><td colspan="5" class="text-center">Aucun contrat trouvé</td></tr>');
            }
        },
        error: function(xhr) {
            console.error('Erreur:', xhr);
            $('#contractsTableBody').html('<tr><td colspan="5" class="text-center text-danger">Erreur lors du chargement des contrats</td></tr>');
            showAlert("Erreur lors du chargement des contrats", "danger");
        }
    });
    
    // Ouvrir le modal
    const modal = new bootstrap.Modal(document.getElementById('viewContractsModal'));
    modal.show();
}
