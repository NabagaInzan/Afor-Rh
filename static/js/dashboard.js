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
let currentEmployeeId = null;
let postes = [];
let currentOperatorId;

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
            if (Array.isArray(response)) {
                postes = response;
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
    
    // ... le reste du code existant ...
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

// Fonction pour afficher les détails d'un employé
function showEmployeeDetails(employeeId) {
    $.ajax({
        url: `/api/employees/${employeeId}`,
        method: 'GET',
        success: function(response) {
            console.log('Données reçues:', response); // Pour le débogage
            
            // Remplir le formulaire avec les données
            $('#firstName').val(response.first_name || '');
            $('#lastName').val(response.last_name || '');
            $('#poste').val(response.poste_id || '');
            $('#gender').val(response.gender || '');
            $('#birthDate').val(response.birth_date || '');
            $('#region').val(response.region_id || '');
            $('#departement').val(response.departement_id || '');
            $('#sousprefecture').val(response.sous_prefecture_id || '');
            $('#additionalInfo').val(response.additional_info || '');
            $('#contractDuration').val(response.contract_duration_months || '');
            $('#position').val(response.position || '');
            $('#contact').val(response.contact || '');
            
            // Stocker l'ID pour la mise à jour
            currentEmployeeId = employeeId;
            
            // Mettre à jour le titre du modal
            $('#addEmployeeModal .modal-title').html('<i class="fas fa-user-edit me-2"></i>Modifier un Employé');
            
            // Afficher le modal
            $('#addEmployeeModal').modal('show');
        },
        error: function(xhr) {
            console.error('Erreur lors du chargement:', xhr.responseJSON);
            showAlert('Erreur lors du chargement des données', 'danger');
        }
    });
}

// Gestionnaire pour le formulaire d'ajout/modification
$('#addEmployeeForm').on('submit', function(e) {
    e.preventDefault();
    
    const formData = {
        first_name: $('#firstName').val(),
        last_name: $('#lastName').val(),
        poste_id: $('#poste').val(),
        gender: $('#gender').val(),
        birth_date: $('#birthDate').val(),
        region_id: $('#region').val(),
        departement_id: $('#departement').val(),
        sous_prefecture_id: $('#sousprefecture').val(),
        additional_info: $('#additionalInfo').val(),
        contract_duration_months: parseInt($('#contractDuration').val()) || 0,
        position: $('#position').val(),
        contact: $('#contact').val()
    };

    const url = currentEmployeeId ? 
        `/api/employees/${currentEmployeeId}` : 
        '/api/employees';

    $.ajax({
        url: url,
        method: currentEmployeeId ? 'PUT' : 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            $('#addEmployeeModal').modal('hide');
            loadEmployees(); // Recharger la table
            showAlert('Employé ' + (currentEmployeeId ? 'modifié' : 'ajouté') + ' avec succès!', 'success');
            currentEmployeeId = null; // Réinitialiser l'ID
        },
        error: function(xhr) {
            showAlert('Erreur lors de l\'opération: ' + (xhr.responseJSON?.error || 'Une erreur est survenue'), 'danger');
        }
    });
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
    console.log('Ouverture du modal de reconduction pour:', employeeId);
    
    // Réinitialiser le formulaire
    $('#renewContractForm')[0].reset();
    
    // Définir les valeurs de base
    $('#renewEmployeeId').val(employeeId);
    $('#renewFirstName').val(firstName);
    $('#renewLastName').val(lastName);
    
    // Désactiver les champs de localisation par défaut
    $('#renewRegion, #renewDepartement, #renewSousprefecture').prop('disabled', true);
    
    // Définir la date de début par défaut à aujourd'hui
    const today = new Date().toISOString().split('T')[0];
    $('#renewStartDate').val(today);
    
    // Déclencher le calcul de la date de fin
    $('#renewDuration').trigger('change');
    
    try {
        const modalElement = document.getElementById('renewContractModal');
        if (!modalElement) {
            console.error('Modal element not found');
            showAlert('Erreur: Modal non trouvé', 'danger');
            return;
        }
        
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    } catch (error) {
        console.error('Erreur lors de l\'ouverture du modal:', error);
        showAlert('Erreur lors de l\'ouverture du modal de reconduction', 'danger');
    }
}

// Fonction pour calculer la date de fin du contrat dans le modal de reconduction
function calculateRenewEndDate() {
    const startDate = $('#renewStartDate').val();
    const duration = parseInt($('#renewDuration').val());
    
    if (startDate && !isNaN(duration)) {
        const endDate = new Date(startDate);
        endDate.setMonth(endDate.getMonth() + duration);
        $('#renewEndDate').val(endDate.toISOString().split('T')[0]);
    }
}

// Gestionnaire pour les changements de date de début et durée dans le modal de reconduction
$('#renewStartDate, #renewDuration').on('change input', calculateRenewEndDate);

// Gestionnaire pour la soumission du formulaire de reconduction
$('#submitRenewContract').on('click', function(e) {
    e.preventDefault();
    submitRenewContract();
});

// Fonction pour soumettre le formulaire de reconduction
function submitRenewContract() {
    const formData = {
        employee_ids: [$('#renewEmployeeId').val()],
        start_date: $('#renewStartDate').val(),
        duration: $('#renewDuration').val(),
        position: $('#renewPosition').val(),
        categorie: $('#renewCategorie').val(),
        diplome: $('#renewDiplome').val(),
        ecole: $('#renewEcole').val(),
        location: $('input[name="renewLocation"]:checked').val(),
        region: $('#renewRegion').val(),
        departement: $('#renewDepartement').val(),
        sousprefecture: $('#renewSousprefecture').val()
    };

    // Validation des champs requis
    if (!formData.start_date || !formData.duration || !formData.position || 
        !formData.categorie || !formData.diplome || !formData.ecole) {
        showAlert('Veuillez remplir tous les champs obligatoires', 'warning');
        return;
    }

    // Si "À l'intérieur" est sélectionné, vérifier les champs de localisation
    if (formData.location === 'interieur' && 
        (!formData.region || !formData.departement || !formData.sousprefecture)) {
        showAlert('Veuillez sélectionner la localisation complète', 'warning');
        return;
    }

    $.ajax({
        url: '/api/employees/renew',
        method: 'POST',
        data: JSON.stringify(formData),
        contentType: 'application/json',
        success: function(response) {
            if (response.success) {
                $('#renewContractModal').modal('hide');
                showAlert('Le contrat a été renouvelé avec succès', 'success');
                loadEmployees();
            } else {
                showAlert(response.error || 'Erreur lors du renouvellement du contrat', 'danger');
            }
        },
        error: function(xhr) {
            console.error('Erreur lors du renouvellement du contrat:', xhr.responseJSON);
            showAlert(xhr.responseJSON?.error || 'Erreur lors du renouvellement du contrat', 'danger');
        }
    });
}

// Charger les données au moment de l'ouverture du modal de reconduction
$('#renewContractModal').on('show.bs.modal', function() {
    // Charger les postes
    $.get('/api/postes', function(data) {
        const select = $('#renewPosition');
        select.empty().append('<option value="">Sélectionner un poste</option>');
        data.forEach(poste => {
            select.append(`<option value="${poste.id}">${poste.nom}</option>`);
        });
    });

    // Charger les catégories
    $.get('/api/categories', function(data) {
        const select = $('#renewCategorie');
        select.empty().append('<option value="">Sélectionner une catégorie</option>');
        data.forEach(cat => {
            select.append(`<option value="${cat.id}">${cat.nom}</option>`);
        });
    });

    // Charger les diplômes
    $.get('/api/diplomes', function(data) {
        const select = $('#renewDiplome');
        select.empty().append('<option value="">Sélectionner un diplôme</option>');
        data.forEach(diplome => {
            select.append(`<option value="${diplome.id}">${diplome.nom}</option>`);
        });
    });

    // Charger les écoles
    $.get('/api/ecoles', function(data) {
        const select = $('#renewEcole');
        select.empty().append('<option value="">Sélectionner une école</option>');
        data.forEach(ecole => {
            select.append(`<option value="${ecole.id}">${ecole.nom}</option>`);
        });
    });

    // Charger les régions
    $.get('/api/regions', function(data) {
        const select = $('#renewRegion');
        select.empty().append('<option value="">Sélectionner une région</option>');
        data.forEach(region => {
            select.append(`<option value="${region.id}">${region.nom}</option>`);
        });
    });
});

// Gestionnaire pour le changement de situation géographique dans le modal de reconduction
$('input[name="renewLocation"]').on('change', function() {
    const isInterieur = $(this).val() === 'interieur';
    $('#renewRegion, #renewDepartement, #renewSousprefecture').prop('disabled', !isInterieur);
    if (!isInterieur) {
        $('#renewRegion, #renewDepartement, #renewSousprefecture').val('');
    }
});

// Gestionnaire pour le changement de région dans le modal de reconduction
$('#renewRegion').on('change', function() {
    const regionId = $(this).val();
    if (regionId) {
        $.get(`/api/departements/${regionId}`, function(data) {
            const select = $('#renewDepartement');
            select.empty().append('<option value="">Sélectionner un département</option>');
            data.forEach(dept => {
                select.append(`<option value="${dept.id}">${dept.nom}</option>`);
            });
            select.prop('disabled', false);
        });
    }
});

// Gestionnaire pour le changement de département dans le modal de reconduction
$('#renewDepartement').on('change', function() {
    const deptId = $(this).val();
    if (deptId) {
        $.get(`/api/sous-prefectures/${deptId}`, function(data) {
            const select = $('#renewSousprefecture');
            select.empty().append('<option value="">Sélectionner une sous-préfecture</option>');
            data.forEach(sp => {
                select.append(`<option value="${sp.id}">${sp.nom}</option>`);
            });
            select.prop('disabled', false);
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

// Gestionnaire pour le bouton d'édition
$(document).on('click', '.edit-employee', function(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const employeeId = $(this).data('id');
    console.log('Edition employé:', employeeId);
    
    // Réinitialiser le formulaire
    $('#addEmployeeForm')[0].reset();
    
    // Mettre à jour le titre du modal
    $('#addEmployeeModal .modal-title').html('<i class="fas fa-user-edit me-2"></i>Modifier un Employé');
    
    // Charger les données de l'employé
    $.ajax({
        url: `/api/employees/${employeeId}`,
        method: 'GET',
        beforeSend: function() {
            $('.loader').addClass('loading');
        },
        success: function(response) {
            console.log('Réponse reçue:', response);
            
            if (response.success && response.employee) {
                const employee = response.employee;
                console.log('Données employé:', employee);
                
                // Remplir le formulaire avec les données de l'employé
                $('<input>').attr({
                    type: 'hidden',
                    id: 'employeeId',
                    name: 'id',
                    value: employee.id
                }).appendTo('#addEmployeeForm');
                
                $('#lastName').val(employee.last_name || '');
                $('#firstName').val(employee.first_name || '');
                $('#birthDate').val(employee.birth_date ? employee.birth_date.split('T')[0] : '');
                $('#gender').val(employee.gender || '');
                $('#contact').val(employee.contact || '');
                
                // Gérer la situation géographique
                if (employee.region_id) {
                    $('#aLInterieur').prop('checked', true).trigger('change');
                    $('#locationFields select').prop('disabled', false);
                    
                    // Charger et sélectionner la région
                    $.get('/api/regions', function(data) {
                        if (data.success) {
                            const regionSelect = $('#region');
                            regionSelect.empty().append('<option value="">Sélectionner une région</option>');
                            data.regions.forEach(function(region) {
                                regionSelect.append(`<option value="${region.id}">${region.nom}</option>`);
                            });
                            regionSelect.val(employee.region_id).trigger('change');
                            
                            // Charger et sélectionner le département
                            $.get(`/api/departements/${employee.region_id}`, function(data) {
                                if (data.success) {
                                    const departementSelect = $('#departement');
                                    departementSelect.empty().append('<option value="">Sélectionner un département</option>');
                                    data.departements.forEach(function(departement) {
                                        departementSelect.append(`<option value="${departement.id}">${departement.nom}</option>`);
                                    });
                                    departementSelect.val(employee.departement_id).trigger('change');
                                    
                                    // Charger et sélectionner la sous-préfecture
                                    if (employee.departement_id) {
                                        $.get(`/api/sous-prefectures/${employee.departement_id}`, function(data) {
                                            if (data.success) {
                                                const spSelect = $('#sousprefecture');
                                                spSelect.empty().append('<option value="">Sélectionner une sous-préfecture</option>');
                                                data.sous_prefectures.forEach(function(sp) {
                                                    spSelect.append(`<option value="${sp.id}">${sp.nom}</option>`);
                                                });
                                                spSelect.val(employee.sous_prefecture_id);
                                            }
                                        });
                                    }
                                }
                            });
                        }
                    });
                } else {
                    $('#auSiege').prop('checked', true).trigger('change');
                }
                
                // Remplir les données du contrat
                if (employee.contract_start_date) {
                    $('#contractStartDate').val(employee.contract_start_date.split('T')[0]);
                }
                $('#contractDuration').val(employee.contract_duration_months || '3');
                
                // Sélectionner le poste
                if (employee.poste_id) {
                    $('#poste').val(employee.poste_id);
                }
                
                // Afficher le modal
                try {
                    addEmployeeModal.show();
                } catch (error) {
                    console.error('Erreur lors de l\'affichage du modal:', error);
                    // Fallback si l'instance du modal n'est pas disponible
                    $('#addEmployeeModal').modal('show');
                }
            } else {
                console.error('Erreur:', response.message);
                showAlert("Erreur lors du chargement des données de l'employé", "danger");
            }
        },
        error: function(xhr) {
            console.error('Erreur AJAX:', xhr);
            showAlert("Erreur lors du chargement des données de l'employé", "danger");
        },
        complete: function() {
            $('.loader').removeClass('loading');
        }
    });
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

// Gestionnaire pour l'export Excel des contrats
$('#exportContractsExcel').on('click', function() {
    const employeeId = $('#viewContractsModal').data('employee-id');
    const employeeName = $('#viewContractsModal .modal-title').text().split('-')[1].trim();
    
    // Récupérer les données du tableau
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
    XLSX.utils.book_append_sheet(wb, ws, 'Contrats');
    
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
        }
    };
    
    // Générer le PDF
    pdfMake.createPdf(docDefinition).download(`Contrats_${employeeName}.pdf`);
});
