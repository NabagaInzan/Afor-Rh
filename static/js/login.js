document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const usernameSelect = document.getElementById('username');
    const contactInput = document.getElementById('contact');
    const passwordInput = document.getElementById('password');
    const adminSwitch = document.getElementById('adminSwitch');
    const passwordToggle = document.querySelector('.password-toggle');
    const projectSelect = document.getElementById('project');
    const actorTypeSelect = document.getElementById('actorType');

    // Charger la liste des acteurs seulement si on n'est pas en mode admin
    function loadOperators() {
        if (!adminSwitch.checked) {
            fetch('/api/operators')
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.operators) {
                        usernameSelect.innerHTML = '<option value="">Sélectionnez un acteur</option>';
                        data.operators.forEach(operator => {
                            const option = document.createElement('option');
                            option.value = operator.id;
                            option.textContent = operator.name;
                            option.dataset.contact = operator.phone;
                            usernameSelect.appendChild(option);
                        });
                    }
                })
                .catch(error => console.error('Erreur lors du chargement des acteurs:', error));
        }
    }

    // Gérer le changement d'acteur
    usernameSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        if (selectedOption && !adminSwitch.checked) {
            contactInput.value = selectedOption.dataset.contact || '';
        }
    });

    // Gérer le switch admin
    adminSwitch.addEventListener('change', function() {
        const isAdmin = this.checked;
        
        // Mettre à jour l'interface selon le mode
        usernameSelect.disabled = isAdmin;
        contactInput.readOnly = !isAdmin;
        projectSelect.disabled = isAdmin;
        actorTypeSelect.disabled = isAdmin;
        
        // Réinitialiser les champs
        if (isAdmin) {
            usernameSelect.value = '';
            contactInput.value = '';
            projectSelect.value = '';
            actorTypeSelect.value = '';
            contactInput.type = 'email';
            contactInput.placeholder = "Email administrateur";
            contactInput.focus();
        } else {
            loadOperators();
            contactInput.type = 'text';
            contactInput.placeholder = "Contact";
            const selectedOption = usernameSelect.options[usernameSelect.selectedIndex];
            if (selectedOption) {
                contactInput.value = selectedOption.dataset.contact || '';
            }
        }
    });

    // Gérer l'affichage/masquage du mot de passe
    passwordToggle.addEventListener('click', function() {
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
        this.querySelector('i').classList.toggle('fa-eye');
        this.querySelector('i').classList.toggle('fa-eye-slash');
    });

    // Gérer la soumission du formulaire
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const isAdmin = adminSwitch.checked;
        const formData = isAdmin ? {
            email: contactInput.value,
            password: passwordInput.value
        } : {
            operator_id: usernameSelect.value,
            contact: contactInput.value,
            password: passwordInput.value,
            project: projectSelect.value
        };

        const url = isAdmin ? '/api/admin/login' : '/api/login';

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = data.redirect;
            } else {
                showError(data.error);
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showError('Une erreur est survenue. Veuillez réessayer.');
        });
    });

    // Fonction pour afficher les erreurs
    function showError(message) {
        const existingAlert = loginForm.querySelector('.alert');
        if (existingAlert) {
            existingAlert.remove();
        }

        const alert = document.createElement('div');
        alert.className = 'alert alert-danger';
        alert.textContent = message;
        loginForm.insertBefore(alert, loginForm.firstChild);
        
        setTimeout(() => alert.remove(), 3000);
    }

    // Charger les données initiales
    loadOperators();
});
