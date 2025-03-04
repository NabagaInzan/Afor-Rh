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

// Fonction pour initialiser la table
function initializeEmployeesTable() {
    employeesTable = $('#employeesTable').DataTable({
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/fr-FR.json'
        },
        select: {
            style: 'multi',
            selector: 'td:first-child'
        },
        order: [[1, 'asc']],
        columnDefs: [
            {
                targets: 0,
                orderable: false,
                className: 'select-checkbox'
            }
        ],
        ajax: {
            url: '/api/employees',
            dataSrc: ''
        },
        columns: [
            {
                data: null,
                defaultContent: '',
                orderable: false,
                className: 'select-checkbox',
                width: '30px'
            },
            { data: 'last_name' },
            { data: 'first_name' },
            { data: 'age' },
            { data: 'position' },
            { data: 'contact' },
            { 
                data: 'contract.status',
                render: function(data, type, row) {
                    if (type === 'display') {
                        const statusClass = data === 'Expiré' ? 'text-danger' : 'text-success';
                        return `<span class="${statusClass}">${data}</span>`;
                    }
                    return data;
                }
            },
            { 
                data: 'contract.duration',
                render: function(data, type, row) {
                    if (!data) {
                        return row.contract_duration || 'Non spécifié';
                    }
                    const months = parseInt(data);
                    if (isNaN(months)) return 'Non spécifié';
                    
                    const years = Math.floor(months / 12);
                    const remainingMonths = months % 12;
                    
                    if (years > 0) {
                        if (remainingMonths > 0) {
                            return `${years} an${years > 1 ? 's' : ''} et ${remainingMonths} mois`;
                        }
                        return `${years} an${years > 1 ? 's' : ''}`;
                    }
                    return `${months} mois`;
                }
            },
            { 
                data: 'availability',
                render: function(data) {
                    const badgeClass = data === 'Au siège' ? 'text-dark' : 'text-dark';
                    return `<span class="${badgeClass}">${data}</span>`;
                }
            },
            {
                data: null,
                orderable: false,
                render: function(data, type, row) {
                    return `
                        <div class="btn-group">
                            <button class="btn btn-sm btn-info view-btn" data-id="${row.id}">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-primary edit-btn" data-id="${row.id}">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-danger delete-btn" data-id="${row.id}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    `;
                }
            }
        ]
    });

    // Gestion de la sélection des lignes
    employeesTable.on('select deselect', function() {
        const selectedRows = employeesTable.rows({ selected: true }).data().toArray();
        const expiredContracts = selectedRows.filter(row => 
            row.contract && row.contract.status === 'Expiré'
        );
        
        // Afficher/masquer les boutons d'action
        $('#renewContractBtn').toggleClass('d-none', expiredContracts.length === 0);
        $('#deleteSelectedBtn').toggleClass('d-none', selectedRows.length === 0);
        
        // Mise à jour du compteur
        const count = selectedRows.length;
        $('#selectionCounter').text(count > 0 ? 
            `${count} employé${count > 1 ? 's' : ''} sélectionné${count > 1 ? 's' : ''}` : ''
        );
    });

    // Gestionnaire pour le bouton de reconduction
    $('#renewContractBtn').on('click', function() {
        const selectedRows = employeesTable.rows({ selected: true }).data().toArray();
        const expiredContracts = selectedRows.filter(row => 
            row.contract && row.contract.status === 'Expiré'
        );
        
        if (expiredContracts.length > 0) {
            const firstEmployee = expiredContracts[0];
            
            // Pré-remplir le formulaire
            $('#renewPoste').val(firstEmployee.position || '');
            $('#renewSituation').val(firstEmployee.availability || '');
            $('#startDate').val(new Date().toISOString().split('T')[0]);
            
            // Stocker les IDs
            $('#renewContractModal')
                .data('selectedIds', expiredContracts.map(row => row.id))
                .modal('show');
        }
    });

    // Gestionnaire de confirmation de reconduction
    $('#confirmRenewBtn').on('click', function() {
        const selectedIds = $('#renewContractModal').data('selectedIds');
        const newDuration = $('#newDuration').val();
        const startDate = $('#startDate').val();
        const poste = $('#renewPoste').val();
        const situation = $('#renewSituation').val();

        if (!newDuration || !startDate || !poste || !situation || !selectedIds?.length) {
            showAlert('Veuillez remplir tous les champs', 'danger');
            return;
        }

        const endDate = new Date(startDate);
        endDate.setMonth(endDate.getMonth() + parseInt(newDuration));

        $.ajax({
            url: '/api/contracts/renew',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                employee_ids: selectedIds,
                start_date: startDate,
                end_date: endDate.toISOString().split('T')[0],
                duration: parseInt(newDuration),
                position: poste,
                availability: situation
            }),
            success: function(response) {
                $('#renewContractModal').modal('hide');
                showAlert('Les contrats ont été reconduits avec succès', 'success');
                employeesTable.ajax.reload();
            },
            error: function(xhr) {
                showAlert('Erreur lors de la reconduction des contrats', 'danger');
                console.error('Erreur:', xhr.responseJSON);
            }
        });
    });
}

// Fonction pour initialiser les gestionnaires de reconduction de contrat
function initializeRenewContractHandlers() {
    // Convertir la durée en années et mois
    $('#renewDuration').on('input', function() {
        const months = parseInt($(this).val()) || 0;
        const years = Math.floor(months / 12);
        const remainingMonths = months % 12;
        let durationText = '';

        if (months === 0) {
            durationText = 'Veuillez entrer une durée';
        } else {
            if (years > 0) {
                durationText += years + ' an' + (years > 1 ? 's' : '');
            }
            if (remainingMonths > 0) {
                if (years > 0) durationText += ' et ';
                durationText += remainingMonths + ' mois';
            }
        }

        $('#durationInYears').text(durationText);

        // Calculer les dates si une durée valide est entrée
        if (months > 0) {
            const startDate = new Date();
            const endDate = new Date();
            endDate.setMonth(endDate.getMonth() + months);
            
            // Stocker les dates calculées dans des champs cachés
            $('#renewStartDate').val(startDate.toISOString().split('T')[0]);
            $('#renewEndDate').val(endDate.toISOString().split('T')[0]);
        }
    });

    // Validation du formulaire avant soumission
    $('#renewContractForm').on('submit', function(e) {
        e.preventDefault();
        
        // Vérifier si le formulaire est valide
        if (!this.checkValidity()) {
            e.stopPropagation();
            $(this).addClass('was-validated');
            return;
        }

        // Vérifier la durée
        const duration = parseInt($('#renewDuration').val());
        if (duration <= 0) {
            showToast('La durée du contrat doit être supérieure à 0', 'error');
            return;
        }

        // Préparer les données du formulaire
        const formData = {
            employee_id: $('#renewEmployeeId').val() || '',
            first_name: $('#renewFirstName').val() || '',
            last_name: $('#renewLastName').val() || '',
            contact: $('#renewContact').val() || '',
            gender: $('#renewGender').val() || '',
            position: $('#renewPosition').val() || '',
            address: $('#renewAddress').val() || '',
            birth_date: $('#renewBirthDate').val() || '',
            location: $('#renewLocation').val() || '',
            region: $('#renewRegion').val() || '',
            departement: $('#renewDepartement').val() || '',
            sousprefecture: $('#renewSousprefecture').val() || '',
            duration: duration || 0,
            start_date: $('#renewStartDate').val() || '',
            end_date: $('#renewEndDate').val() || '',
            additional_info: $('#renewAdditionalInfo').val() || ''
        };

        // Envoyer la requête
        $.ajax({
            url: '/api/contracts/renew',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                $('#renewContractModal').modal('hide');
                employeesTable.ajax.reload();
                showToast('Contrat reconduit avec succès', 'success');
            },
            error: function(xhr) {
                const error = xhr.responseJSON?.error || 'Erreur lors de la reconduction du contrat';
                showToast(error, 'error');
            }
        });
    });
    
    // Gestionnaire pour le bouton de confirmation de reconduction
    $('#confirmRenewBtn').on('click', function() {
        const form = $('#renewContractForm')[0];
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return;
        }

        const data = {
            employee_ids: selectedExpiredEmployees.map(e => e.id),
            type: $('#renewType').val(),
            duration: $('#renewDuration').val()
        };

        $.ajax({
            url: '/api/employees/renew',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                if (response.success) {
                    $('#renewContractModal').modal('hide');
                    showToast(response.message, 'success');
                    selectedExpiredEmployees = [];
                    employeesTable.ajax.reload();
                } else {
                    showToast('Erreur: ' + (response.error || 'Erreur inconnue'), 'error');
                }
            },
            error: function(xhr) {
                showToast('Erreur: ' + (xhr.responseJSON?.error || 'Erreur de connexion'), 'error');
            }
        });
    });

    // Réinitialiser le formulaire quand le modal est fermé
    $('#renewContractModal').on('hidden.bs.modal', function() {
        $('#renewContractForm')[0].reset();
        $('#renewContractForm').removeClass('was-validated');
        $('.is-invalid').removeClass('is-invalid');
        $('.invalid-feedback').remove();
        $('#renewDuration').val('');
        $('#durationInYears').text('');
    });
}

// Fonctions d'export
function exportToExcel(data) {
    const worksheet = XLSX.utils.json_to_sheet(data.map(row => ({
        'Nom': row.last_name,
        'Prénom': row.first_name,
        'Âge': row.age,
        'Poste': row.position,
        'Contact': row.contact,
        'Statut Contrat': row.contract.status,
        'Durée Contrat': row.contract.duration + ' mois',
        'Situation Géographique': row.availability
    })));

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Employés");
    
    // Ajuster la largeur des colonnes
    const wscols = [
        {wch: 20}, // Nom
        {wch: 20}, // Prénom
        {wch: 10}, // Âge
        {wch: 25}, // Poste
        {wch: 15}, // Contact
        {wch: 15}, // Statut Contrat
        {wch: 15}, // Durée Contrat
        {wch: 20}  // Situation Géographique
    ];
    worksheet['!cols'] = wscols;

    XLSX.writeFile(workbook, "Liste_Employés_PRESFOR.xlsx");
}

function exportToPDF(data) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    
    // Ajouter un arrière-plan stylisé
    doc.setFillColor(240, 240, 240);
    doc.rect(0, 0, doc.internal.pageSize.width, doc.internal.pageSize.height, 'F');
    
    // Ajouter le logo et le titre
    doc.setFontSize(22);
    doc.setTextColor(5, 150, 105); // Couleur verte PRESFOR
    doc.text("PRESFOR - Liste des Employés", 105, 20, { align: 'center' });
    
    // Ajouter la date
    doc.setFontSize(10);
    doc.setTextColor(100, 100, 100);
    doc.text("Date d'export: " + new Date().toLocaleDateString(), 105, 30, { align: 'center' });
    
    // Configuration de la table
    const columns = [
        {header: 'Nom', dataKey: 'nom'},
        {header: 'Prénom', dataKey: 'prenom'},
        {header: 'Âge', dataKey: 'age'},
        {header: 'Poste', dataKey: 'poste'},
        {header: 'Contact', dataKey: 'contact'},
        {header: 'Statut Contrat', dataKey: 'statut'},
        {header: 'Durée Contrat', dataKey: 'duree'},
        {header: 'Situation Géo.', dataKey: 'situation'}
    ];
    
    const rows = data.map(row => ({
        nom: row.last_name,
        prenom: row.first_name,
        age: row.age,
        poste: row.position,
        contact: row.contact,
        statut: row.contract.status,
        duree: row.contract.duration + ' mois',
        situation: row.availability
    }));

    // Style de la table
    doc.autoTable({
        startY: 40,
        head: [['Date de début', 'Date de fin', 'Durée', 'Poste', 'Statut']],
        body: rows,
        theme: 'striped',
        headStyles: {
            fillColor: [5, 150, 105],
            textColor: [255, 255, 255],
            fontSize: 10,
            fontStyle: 'bold',
            halign: 'center'
        },
        alternateRowStyles: {
            fillColor: [245, 245, 245]
        },
        columnStyles: {
            0: {fontStyle: 'bold'}, // Nom en gras
            1: {fontStyle: 'bold'}, // Prénom en gras
        },
        margin: {top: 40},
        didDrawPage: function(data) {
            // Ajouter un pied de page
            doc.setFontSize(8);
            doc.setTextColor(100, 100, 100);
            doc.text('Page ' + doc.internal.getCurrentPageInfo().pageNumber, doc.internal.pageSize.width / 2, doc.internal.pageSize.height - 10, {
                align: 'center'
            });
        }
    });
    
    // Sauvegarder le PDF
    doc.save("Liste_Employés_PRESFOR.pdf");
}

// Export de la liste des employés
$('#exportExcel').click(function() {
    const data = employeesTable.rows().data().toArray();
    exportToExcel(data);
});

$('#exportPDF').click(function() {
    const data = employeesTable.rows().data().toArray();
    exportToPDF(data);
});

// Export de l'historique des contrats
let currentContractsData = null;

function updateCurrentContractsData(data) {
    currentContractsData = data;
}

// Fonction pour exporter l'historique des contrats vers Excel
function exportContractsToExcel(data) {
    const contractsData = data.contracts.map(contract => {
        const duration = calculateContractDuration(contract.start_date, contract.end_date);
        return {
            'Date de début': formatDate(contract.start_date),
            'Date de fin': formatDate(contract.end_date),
            'Durée': formatDuration(duration),
            'Poste': contract.position || 'Non spécifié',
            'Statut': contract.status
        };
    });

    const ws = XLSX.utils.json_to_sheet(contractsData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Historique Contrats");
    
    // Sauvegarder le fichier
    XLSX.writeFile(wb, `Historique_Contrats_${data.employee.last_name}_${data.employee.first_name}.xlsx`);
}

// Fonction pour exporter l'historique des contrats vers PDF
function exportContractsToPDF(data) {
    const doc = new jspdf.jsPDF();
    
    // En-tête
    doc.setFontSize(16);
    doc.text(`Historique des contrats - ${data.employee.last_name} ${data.employee.first_name}`, 14, 20);
    
    // Tableau des contrats
    const contractsData = data.contracts.map(contract => {
        const duration = calculateContractDuration(contract.start_date, contract.end_date);
        return [
            formatDate(contract.start_date),
            formatDate(contract.end_date),
            formatDuration(duration),
            contract.position || 'Non spécifié',
            contract.status
        ];
    });

    doc.autoTable({
        startY: 30,
        head: [['Date de début', 'Date de fin', 'Durée', 'Poste', 'Statut']],
        body: contractsData,
        theme: 'striped',
        headStyles: {
            fillColor: [5, 150, 105],
            textColor: [255, 255, 255],
            fontSize: 10,
            fontStyle: 'bold',
            halign: 'center'
        },
        alternateRowStyles: {
            fillColor: [245, 245, 245]
        },
        columnStyles: {
            0: {fontStyle: 'bold'}, // Nom en gras
            1: {fontStyle: 'bold'}, // Prénom en gras
        },
        margin: {top: 40},
        didDrawPage: function(data) {
            // Ajouter un pied de page
            doc.setFontSize(8);
            doc.setTextColor(100, 100, 100);
            doc.text('Page ' + doc.internal.getCurrentPageInfo().pageNumber, doc.internal.pageSize.width / 2, doc.internal.pageSize.height - 10, {
                align: 'center'
            });
        }
    });
    
    // Sauvegarder le PDF
    doc.save(`Historique_Contrats_${data.employee.last_name}_${data.employee.first_name}.pdf`);
}

$('#exportContractsExcel').click(function() {
    if (!currentContractsData) return;
    
    exportContractsToExcel(currentContractsData);
});

$('#exportContractsPDF').click(function() {
    if (!currentContractsData) return;
    
    exportContractsToPDF(currentContractsData);
});

$('#printContracts').click(function() {
    if (!currentContractsData) return;
    
    const printWindow = window.open('', '_blank');
    const contractsTable = $('#viewContractsModal .table').clone();
    
    printWindow.document.write(`
        <html>
            <head>
                <title>Historique des Contrats</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    @media print {
                        .table { width: 100%; }
                        th { background-color: #f8f9fa !important; }
                    }
                </style>
            </head>
            <body>
                <div class="container mt-4">
                    <h2>Historique des Contrats</h2>
                    <h4>${currentContractsData.employee.first_name} ${currentContractsData.employee.last_name}</h4>
                    <p>Date: ${new Date().toLocaleDateString()}</p>
                    ${contractsTable.prop('outerHTML')}
                </div>
            </body>
        </html>
    `);
    
    printWindow.document.close();
    printWindow.print();
});

// Mise à jour du gestionnaire de visualisation des contrats
$('#employeesTable').on('click', '.view-btn', function(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const employeeId = $(this).data('id');
    
    $.ajax({
        url: `/api/employees/${employeeId}/contracts`,
        method: 'GET',
        success: function(response) {
            // Stocker les données pour l'export
            updateCurrentContractsData(response);
            
            // Construire le contenu du modal
            let modalContent = `
                <h5>Historique des contrats de ${response.employee.first_name} ${response.employee.last_name}</h5>
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th>Début</th>
                                <th>Fin</th>
                                <th>Statut</th>
                                <th>Poste</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            response.contracts.forEach(contract => {
                const statusClass = contract.status === 'En cours' ? 'text-success' : 
                                  contract.status === 'Expiré' ? 'text-danger' : 'text-muted';
                                  
                modalContent += `
                    <tr>
                        <td>${contract.type || ''}</td>
                        <td>${contract.start_date || ''}</td>
                        <td>${contract.end_date || ''}</td>
                        <td><span class="${statusClass}">${contract.status || ''}</span></td>
                        <td>${contract.position || ''}</td>
                    </tr>
                `;
            });
            
            modalContent += `
                        </tbody>
                    </table>
                </div>
            `;
            
            // Mettre à jour et afficher le modal
            $('#viewContractsModal .modal-body').html(modalContent);
            $('#viewContractsModal').modal('show');
        },
        error: function(xhr) {
            console.error('Erreur lors du chargement des contrats:', xhr.responseJSON);
            showAlert('Erreur lors du chargement de l\'historique des contrats', 'danger');
        }
    });
});

// Fonction pour ouvrir le modal de reconduction de contrat
function renewContract(employeeId) {
    // Récupérer les données de l'employé
    const employee = employeesTable.data().toArray().find(emp => emp.id === employeeId);
    if (!employee) return;

    // Remplir le formulaire avec les données de l'employé
    $('#renewEmployeeId').val(employee.id);
    $('#renewFirstName').val(employee.first_name);
    $('#renewLastName').val(employee.last_name);
    $('#renewContact').val(employee.contact);
    $('#renewGender').val(employee.gender);
    $('#renewPosition').val(employee.position);
    $('#renewAddress').val(employee.address);
    $('#renewBirthDate').val(employee.birth_date);
    $('#renewAvailability').val(employee.availability);
    $('#renewAdditionalInfo').val(employee.additional_info);

    // Réinitialiser la durée
    $('#renewDuration').val('').trigger('input');

    // Ouvrir le modal
    $('#renewContractModal').modal('show');
}

// Fonction pour calculer l'âge
function calculateAge(birthDate) {
    if (!birthDate) return '';
    
    const today = new Date();
    const birth = new Date(birthDate);
    
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--;
    }
    
    return age;
}

// Fonction pour calculer la durée entre deux dates en mois
function calculateContractDuration(startDate, endDate) {
    if (!startDate || !endDate) return 'Non spécifié';
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    const yearsDiff = end.getFullYear() - start.getFullYear();
    const monthsDiff = end.getMonth() - start.getMonth();
    
    const totalMonths = (yearsDiff * 12) + monthsDiff;
    
    if (totalMonths < 0) return 'Non spécifié';
    return totalMonths;
}

// Fonction pour formater la durée en texte
function formatDuration(months) {
    if (!months || months === 'Non spécifié') return 'Non spécifié';
    
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;
    
    if (years > 0) {
        if (remainingMonths > 0) {
            return `${years} an${years > 1 ? 's' : ''} et ${remainingMonths} mois`;
        }
        return `${years} an${years > 1 ? 's' : ''}`;
    }
    return `${months} mois`;
}

// Fonction pour convertir les mois en années et mois
function convertMonthsToYearsAndMonths(totalMonths) {
    const years = Math.floor(totalMonths / 12);
    const months = totalMonths % 12;
    let durationText = '';
    
    if (years > 0) {
        durationText += `${years} an${years > 1 ? 's' : ''}`;
    }
    if (months > 0) {
        if (durationText) durationText += ' et ';
        durationText += `${months} mois`;
    }
    if (!durationText) {
        durationText = `${totalMonths} mois`;
    }
    return durationText;
}

function calculateContractEndDate(startDate, duration) {
    if (!startDate || !duration) return '-';
    
    // Convertir la durée en nombre de mois
    let months = 0;
    if (typeof duration === 'string') {
        // Si la durée est "6 mois", "1 an", "18 mois", etc.
        const match = duration.match(/(\d+)\s*(mois|an|ans)/i);
        if (match) {
            const number = parseInt(match[1]);
            const unit = match[2].toLowerCase();
            months = unit.startsWith('an') ? number * 12 : number;
        } else {
            // Si c'est juste un nombre, on considère que ce sont des mois
            months = parseInt(duration) || 12; // Par défaut 12 mois si non valide
        }
    } else {
        months = parseInt(duration) || 12;
    }

    // Calculer la date de fin
    const endDate = new Date(startDate);
    endDate.setMonth(endDate.getMonth() + months);
    
    // Formater la date en français
    return endDate.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Fonction pour supprimer un employé individuel
function deleteEmployee(employeeId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cet employé ?')) {
        $.ajax({
            url: `/api/employees/${employeeId}`,
            method: 'DELETE',
            success: function(response) {
                if (response.success) {
                    showToast('Employé supprimé avec succès', 'success');
                    employeesTable.ajax.reload();
                } else {
                    showToast(response.error || 'Erreur lors de la suppression', 'error');
                }
            },
            error: function(xhr) {
                showToast('Erreur lors de la suppression de l\'employé', 'error');
            }
        });
    }
}

// Fonction pour vérifier l'expiration du contrat
function checkContractExpiration() {
    const startDateInput = $('#contractStartDate');
    const durationInput = $('#contractDuration');
    const expirationSection = $('.contract-expiration-section');
    const contractExpiredCheckbox = $('#contractExpired');
    
    const startDate = startDateInput.val() ? new Date(startDateInput.val()) : new Date();
    const durationMonths = parseInt(durationInput.val()) || 0;
    
    // Calculer la date de fin
    const endDate = new Date(startDate);
    endDate.setMonth(endDate.getMonth() + durationMonths);
    
    // Vérifier si le contrat est expiré
    const now = new Date();
    if (endDate < now) {
        expirationSection.slideDown();
    } else {
        expirationSection.slideUp();
        // Réinitialiser la case à cocher si le contrat n'est pas expiré
        contractExpiredCheckbox.prop('checked', false);
    }
}

// Fonction pour calculer la date de fin du contrat
function calculateContractEndDate() {
    const startDateInput = $('#contractStartDate');
    const durationInput = $('#contractDuration');
    const endDateInput = $('#contractEndDate');
    
    const startDate = startDateInput.val() ? new Date(startDateInput.val()) : new Date();
    const durationMonths = parseInt(durationInput.val()) || 0;
    
    if (durationMonths > 0) {
        // Calculer la date de fin
        const endDate = new Date(startDate);
        endDate.setMonth(endDate.getMonth() + durationMonths);
        
        // Formater la date en YYYY-MM-DD pour l'input date
        const endDateStr = endDate.toISOString().split('T')[0];
        endDateInput.val(endDateStr);
        
        // Vérifier si le contrat est expiré
        checkContractExpiration();
    }
}

// Écouteurs d'événements pour le calcul automatique
$('#contractStartDate, #contractDuration').on('change', calculateContractEndDate);

// Calculer la date de fin initiale au chargement du modal
$('#addEmployeeModal').on('shown.bs.modal', function() {
    // Si la date de début n'est pas définie, utiliser la date actuelle
    if (!$('#contractStartDate').val()) {
        const today = new Date().toISOString().split('T')[0];
        $('#contractStartDate').val(today);
    }
    calculateContractEndDate();
});

$(document).ready(function() {
    // Initialisation de DataTables
    employeesTable = $('#employeesTable').DataTable({
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/fr-FR.json'
        },
        select: {
            style: 'multi',
            selector: 'td:first-child'
        },
        order: [[1, 'asc']],
        columnDefs: [
            {
                targets: 0,
                orderable: false,
                className: 'select-checkbox'
            }
        ],
        ajax: {
            url: '/api/employees',
            dataSrc: ''
        },
        columns: [
            {
                data: null,
                defaultContent: '',
                orderable: false,
                className: 'select-checkbox',
                width: '30px'
            },
            { data: 'last_name' },
            { data: 'first_name' },
            { data: 'age' },
            { data: 'position' },
            { data: 'contact' },
            { 
                data: 'contract.status',
                render: function(data, type, row) {
                    if (type === 'display') {
                        const statusClass = data === 'Expiré' ? 'text-danger' : 'text-success';
                        return `<span class="${statusClass}">${data}</span>`;
                    }
                    return data;
                }
            },
            { 
                data: 'contract.duration',
                render: function(data, type, row) {
                    if (!data) {
                        return row.contract_duration || 'Non spécifié';
                    }
                    const months = parseInt(data);
                    if (isNaN(months)) return 'Non spécifié';
                    
                    const years = Math.floor(months / 12);
                    const remainingMonths = months % 12;
                    
                    if (years > 0) {
                        if (remainingMonths > 0) {
                            return `${years} an${years > 1 ? 's' : ''} et ${remainingMonths} mois`;
                        }
                        return `${years} an${years > 1 ? 's' : ''}`;
                    }
                    return `${months} mois`;
                }
            },
            { 
                data: 'availability',
                render: function(data) {
                    const badgeClass = data === 'Au siège' ? 'text-dark' : 'text-dark';
                    return `<span class="${badgeClass}">${data}</span>`;
                }
            },
            {
                data: null,
                orderable: false,
                render: function(data, type, row) {
                    return `
                        <div class="btn-group">
                            <button class="btn btn-sm btn-info view-btn" data-id="${row.id}">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-primary edit-btn" data-id="${row.id}">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-danger delete-btn" data-id="${row.id}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    `;
                }
            }
        ]
    });

    // Gestion de la sélection des lignes
    employeesTable.on('select deselect', function() {
        const selectedRows = employeesTable.rows({ selected: true }).data().toArray();
        const expiredContracts = selectedRows.filter(row => 
            row.contract && row.contract.status === 'Expiré'
        );
        
        // Afficher/masquer les boutons d'action
        $('#renewContractBtn').toggleClass('d-none', expiredContracts.length === 0);
        $('#deleteSelectedBtn').toggleClass('d-none', selectedRows.length === 0);
        
        // Mise à jour du compteur
        const count = selectedRows.length;
        $('#selectionCounter').text(count > 0 ? 
            `${count} employé${count > 1 ? 's' : ''} sélectionné${count > 1 ? 's' : ''}` : ''
        );
    });

    // Gestionnaire pour le bouton d'édition
    $('#employeesTable').on('click', '.edit-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const employeeId = $(this).data('id');
        
        $.ajax({
            url: `/api/employees/${employeeId}`,
            method: 'GET',
            success: function(response) {
                // Remplir le formulaire avec les données
                $('#lastName').val(response.last_name || '');
                $('#firstName').val(response.first_name || '');
                $('#position').val(response.position || '');
                $('#contact').val(response.contact || '');
                $('#gender').val(response.gender || '');
                $('#birthDate').val(response.birth_date || '');
                $('#location').val(response.location || '');
                $('#region').val(response.region || '');
                $('#departement').val(response.departement || '');
                $('#sousprefecture').val(response.sousprefecture || '');
                $('#additionalInfo').val(response.additional_info || '');
                $('#contractDuration').val(response.contract_duration || ''); // Ajout de la durée du contrat
                
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
    });

    // Gestionnaire pour le formulaire d'ajout/modification
    $('#addEmployeeForm').on('submit', function(e) {
        e.preventDefault();
        
        const startDate = $('#contractStartDate').val() || new Date().toISOString().split('T')[0];
        const isExpired = $('#contractExpired').is(':checked');
        
        const formData = {
            first_name: $('#firstName').val(),
            last_name: $('#lastName').val(),
            position: $('#poste').val() === 'autre' ? $('#autrePoste').val() : $('#poste').val(),
            contact: $('#contact').val(),
            gender: $('#gender').val(),
            birth_date: $('#birthDate').val(),
            location: $('input[name="location"]:checked').val(),
            region: $('#region').val(),
            departement: $('#departement').val(),
            sousprefecture: $('#sousprefecture').val(),
            additional_info: $('#additionalInfo').val(),
            contract_duration: $('#contractDuration').val(),
            contract_start_date: startDate,
            additional_terms: $('#additionalTerms').val(),
            contract_expired: isExpired
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
                employeesTable.ajax.reload();
                showAlert('Employé ' + (currentEmployeeId ? 'modifié' : 'ajouté') + ' avec succès!', 'success');
            },
            error: function(xhr) {
                showAlert('Erreur lors de l\'opération: ' + xhr.responseText, 'danger');
            }
        });
    });

    // Gestionnaire pour le bouton de suppression
    $('#employeesTable').on('click', '.delete-btn', function(e) {
        e.preventDefault();
        const employeeId = $(this).data('id');
        
        if (confirm('Êtes-vous sûr de vouloir supprimer cet employé ?')) {
            $.ajax({
                url: `/api/employees/${employeeId}`,
                method: 'DELETE',
                success: function(response) {
                    showAlert(response.message || 'Employé supprimé avec succès', 'success');
                    employeesTable.ajax.reload();
                },
                error: function(xhr) {
                    showAlert(xhr.responseJSON?.error || 'Erreur lors de la suppression', 'danger');
                    console.error('Erreur:', xhr.responseJSON);
                }
            });
        }
    });

    // Gestionnaire pour le bouton de reconduction
    $('#renewContractBtn').on('click', function() {
        const selectedRows = employeesTable.rows({ selected: true }).data().toArray();
        const expiredContracts = selectedRows.filter(row => 
            row.contract && row.contract.status === 'Expiré'
        );
        
        if (expiredContracts.length > 0) {
            const firstEmployee = expiredContracts[0];
            
            // Pré-remplir le formulaire
            $('#renewPoste').val(firstEmployee.position || '');
            $('#renewSituation').val(firstEmployee.availability || '');
            $('#startDate').val(new Date().toISOString().split('T')[0]);
            
            // Stocker les IDs
            $('#renewContractModal')
                .data('selectedIds', expiredContracts.map(row => row.id))
                .modal('show');
        }
    });

    // Gestionnaire de confirmation de reconduction
    $('#confirmRenewBtn').on('click', function() {
        const selectedIds = $('#renewContractModal').data('selectedIds');
        const newDuration = $('#newDuration').val();
        const startDate = $('#startDate').val();
        const poste = $('#renewPoste').val();
        const situation = $('#renewSituation').val();

        if (!newDuration || !startDate || !poste || !situation || !selectedIds?.length) {
            showAlert('Veuillez remplir tous les champs', 'danger');
            return;
        }

        const endDate = new Date(startDate);
        endDate.setMonth(endDate.getMonth() + parseInt(newDuration));

        $.ajax({
            url: '/api/contracts/renew',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                employee_ids: selectedIds,
                start_date: startDate,
                end_date: endDate.toISOString().split('T')[0],
                duration: parseInt(newDuration),
                position: poste,
                availability: situation
            }),
            success: function(response) {
                $('#renewContractModal').modal('hide');
                showAlert('Les contrats ont été reconduits avec succès', 'success');
                employeesTable.ajax.reload();
                
                // Désélectionner toutes les lignes après la reconduction
                employeesTable.rows().deselect();
            },
            error: function(xhr) {
                showAlert('Erreur lors de la reconduction des contrats', 'danger');
                console.error('Erreur:', xhr.responseJSON);
            }
        });
    });

    // Gestionnaire pour le bouton de visualisation des contrats
    $('#employeesTable').on('click', '.view-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const employeeId = $(this).data('id');
        
        $.ajax({
            url: `/api/employees/${employeeId}/contracts`,
            method: 'GET',
            success: function(response) {
                // Construire le contenu du modal
                let modalContent = `
                    <h5>Historique des contrats de ${response.employee.first_name} ${response.employee.last_name}</h5>
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Type</th>
                                    <th>Début</th>
                                    <th>Fin</th>
                                    <th>Statut</th>
                                    <th>Poste</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                response.contracts.forEach(contract => {
                    const statusClass = contract.status === 'En cours' ? 'text-success' : 
                                      contract.status === 'Expiré' ? 'text-danger' : 'text-muted';
                                      
                    modalContent += `
                        <tr>
                            <td>${contract.type || ''}</td>
                            <td>${contract.start_date || ''}</td>
                            <td>${contract.end_date || ''}</td>
                            <td><span class="${statusClass}">${contract.status || ''}</span></td>
                            <td>${contract.position || ''}</td>
                        </tr>
                    `;
                });
                
                modalContent += `
                            </tbody>
                        </table>
                    </div>
                `;
                
                // Mettre à jour et afficher le modal
                $('#viewContractsModal .modal-body').html(modalContent);
                $('#viewContractsModal').modal('show');
            },
            error: function(xhr) {
                console.error('Erreur lors du chargement des contrats:', xhr.responseJSON);
                showAlert('Erreur lors du chargement de l\'historique des contrats', 'danger');
            }
        });
    });

    // Réinitialisation du formulaire lors de la fermeture du modal
    $('#addEmployeeModal').on('hidden.bs.modal', function() {
        $('#addEmployeeForm')[0].reset();
        currentEmployeeId = null;
        $('.modal-title').html('<i class="fas fa-user-plus me-2"></i>Ajouter un Employé');
    });

    // Initialisation des autres fonctionnalités
    initializeRenewContractHandlers();
    loadStats();
    
    // Actualisation automatique des statistiques
    setInterval(loadStats, 30000);

    // Ajouter les gestionnaires d'événements pour la vérification de l'expiration
    $('#contractStartDate, #contractDuration').on('change', checkContractExpiration);
    
    // Vérifier l'expiration lors de l'ouverture du modal
    $('#addEmployeeModal').on('shown.bs.modal', checkContractExpiration);

    // Fonction pour mettre à jour l'heure
    function updateTime() {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        $('#currentTime').text(`${hours}:${minutes}:${seconds}`);
    }

    // Mettre à jour l'heure toutes les secondes
    setInterval(updateTime, 1000);

    // Mettre à jour l'heure immédiatement au chargement
    updateTime();
});

// Fonction pour afficher les détails d'un employé
function showEmployeeDetails(employeeId) {
    $.get(`/api/employees/${employeeId}/contracts`)
        .done(function(response) {
            // Mettre à jour le titre du modal
            $('#employeeDetailsModalLabel').text(`Historique des contrats de ${response.employee.first_name} ${response.employee.last_name}`);
            
            // Construire le tableau des contrats
            let contractsHtml = `
                <div class="table-responsive">
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th>Début</th>
                                <th>Fin</th>
                                <th>Statut</th>
                                <th>Poste</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            response.contracts.forEach(contract => {
                const statusClass = contract.status === 'En cours' ? 'badge bg-success' : 'badge bg-danger';
                contractsHtml += `
                    <tr>
                        <td>${contract.type || ''}</td>
                        <td>${formatDate(contract.start_date) || ''}</td>
                        <td>${formatDate(contract.end_date) || ''}</td>
                        <td><span class="${statusClass}">${contract.status || ''}</span></td>
                        <td>${contract.position || 'Non spécifié'}</td>
                    </tr>
                `;
            });
            
            contractsHtml += `
                        </tbody>
                    </table>
                </div>
            `;
            
            // Injecter le HTML dans le modal
            $('#employeeDetailsModal .modal-body').html(contractsHtml);
            
            // Afficher le modal
            $('#employeeDetailsModal').modal('show');
        })
        .fail(function(xhr) {
            console.error('Erreur lors de la récupération des contrats:', xhr.responseText);
            showAlert('Erreur lors de la récupération des contrats', 'danger');
        });
}

// Fonction pour formater une date
function formatDate(dateStr) {
    if (!dateStr) return '';
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
