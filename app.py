from flask import Flask, jsonify, request, session, render_template, redirect, url_for
import sqlite3
import os
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from auth.sqlite_auth import SQLiteAuth
from services.employee_service import EmployeeService
from admin import admin_bp
from functools import wraps
import json
from dateutil.relativedelta import relativedelta

# Charger les variables d'environnement
load_dotenv()

def get_db_connection():
    """Établit une connexion à la base de données SQLite"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'db', 'geogestion.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par leur nom
    return conn

def init_db():
    """Initialise la base de données"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Créer la table administrators si elle n'existe pas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS administrators (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Ajouter un administrateur par défaut s'il n'existe pas
    cursor.execute("SELECT COUNT(*) FROM administrators")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO administrators (email, name, password)
            VALUES (?, ?, ?)
        """, ('admin@geogestion.com', 'Admin', 'admin123'))

    # Ajout des colonnes deleted_at et updated_at si elles n'existent pas
    try:
        cursor.execute("""
            ALTER TABLE employees 
            ADD COLUMN deleted_at DATETIME DEFAULT NULL;
        """)
    except:
        pass  # La colonne existe déjà

    try:
        cursor.execute("""
            ALTER TABLE employees 
            ADD COLUMN updated_at DATETIME DEFAULT NULL;
        """)
    except:
        pass

    try:
        cursor.execute("""
            ALTER TABLE contracts 
            ADD COLUMN deleted_at DATETIME DEFAULT NULL;
        """)
    except:
        pass

    try:
        cursor.execute("""
            ALTER TABLE contracts 
            ADD COLUMN updated_at DATETIME DEFAULT NULL;
        """)
    except:
        pass

    # Créer la table type_poste si elle n'existe pas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS type_poste (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fonction TEXT NOT NULL
        )
    """)

    # Vérifier si la table type_poste est vide
    cursor.execute("SELECT COUNT(*) FROM type_poste")
    if cursor.fetchone()[0] == 0:
        # Insérer des catégories par défaut
        default_categories = [
            ('Superviseur',),
            ('Agent de terrain',),
            ('Coordinateur',),
            ('Assistant',),
            ('Technicien',)
        ]
        cursor.executemany(
            "INSERT INTO type_poste (fonction) VALUES (?)",
            default_categories
        )
        print("Catégories par défaut ajoutées à la table type_poste")

    conn.commit()
    conn.close()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))  # Clé secrète pour la session
    
    # Enregistrer le blueprint d'administration
    app.register_blueprint(admin_bp)
    
    return app

app = create_app()

# Initialiser les services
auth = SQLiteAuth()
employee_service = EmployeeService()

# Initialiser la base de données au démarrage
init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'operator_id' not in session:
            return jsonify({"success": False, "error": "Non autorisé"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Route principale qui affiche la page de connexion"""
    if 'operator_id' in session:
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/api/operators', methods=['GET'])
def get_operators():
    """Récupère la liste des acteurs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vérifier la structure de la table
        cursor.execute("SELECT * FROM operators LIMIT 1")
        row = cursor.fetchone()
        if row:
            print("Colonnes disponibles:", row)
        
        cursor.execute("""
            SELECT id, name, contact1, password 
            FROM operators 
            ORDER BY name
        """)
        operators = []
        for row in cursor.fetchall():
            operators.append({
                'id': row[0],
                'name': row[1],
                'phone': row[2],
                'password': row[3]
            })
        conn.close()
        return jsonify({'success': True, 'operators': operators})
    except Exception as e:
        print(f"Erreur lors de la récupération des acteurs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if conn:
            conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    conn = None
    try:
        data = request.get_json()
        phone = data.get('phone')
        password = data.get('password')
        project_id = data.get('project')
        
        if not all([phone, password, project_id]):
            return jsonify({
                'success': False,
                'error': 'Tous les champs sont requis'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Récupérer l'opérateur avec le projet sélectionné
        cursor.execute("""
            SELECT o.id, o.name, o.contact1 as phone, o.password, o.acteur_type_id
            FROM operators o
            INNER JOIN operator_projects op ON o.id = op.operator_id
            WHERE o.contact1 = ? AND op.project_id = ?
        """, (phone, project_id))
        
        operator = cursor.fetchone()
        
        if not operator:
            return jsonify({
                'success': False,
                'error': 'Opérateur non trouvé ou non associé à ce projet'
            }), 404
        
        # Vérifier le mot de passe
        if operator['password'] != password:
            return jsonify({
                'success': False,
                'error': 'Mot de passe incorrect'
            }), 401
        
        # Stocker les informations dans la session
        session['operator_id'] = operator['id']
        session['operator_name'] = operator['name']
        session['actor_type'] = operator['acteur_type_id']
        session['project_id'] = project_id  # Ajouter le project_id à la session
        
        print(f"Login réussi - Opérateur: {operator['name']}, Projet: {project_id}")  # Debug
        
        return jsonify({
            'success': True,
            'operator': {
                'id': operator['id'],
                'name': operator['name'],
                'phone': operator['phone']
            },
            'redirect': '/dashboard'
        })
        
    except Exception as e:
        print(f"Erreur lors du login: {str(e)}")  # Debug
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if conn:
            conn.close()

@app.route('/dashboard')
@login_required
def dashboard():
    operator_id = session.get('operator_id')
    if not operator_id:
        return redirect(url_for('login'))
        
    return render_template(
        'dashboard.html',
        operator_id=operator_id
    )

@app.route('/api/employees', methods=['GET'])
@login_required
def get_employees():
    """Récupère la liste des employés de l'opérateur connecté"""
    try:
        operator_id = session.get('operator_id')
        if not operator_id:
            return jsonify({"success": False, "error": "Non autorisé"}), 401
            
        employees = employee_service.get_employees_by_operator(operator_id)
        return jsonify({"success": True, "employees": employees})
    except Exception as e:
        print(f"Erreur lors de la récupération des employés: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/employees/<employee_id>', methods=['GET'])
@login_required
def get_employee(employee_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Récupérer les informations de l'employé avec les jointures nécessaires
        cur.execute("""
            SELECT 
                e.*,
                r.nom as region_nom,
                d.nom as departement_nom,
                sp.nom as sous_prefecture_nom,
                tp.fonction as poste_nom,
                c.start_date as contract_start,
                c.end_date as contract_end,
                c.salary as contract_salary,
                c.categorie as contract_category,
                c.position as contract_position,
                c.status as contract_status,
                dip.nom as diplome_nom,
                ec.nom as ecole_nom
            FROM employees e
            LEFT JOIN regions r ON e.region_id = r.id
            LEFT JOIN departements d ON e.departement_id = d.id
            LEFT JOIN sous_prefectures sp ON e.sous_prefecture_id = sp.id
            LEFT JOIN type_poste tp ON e.poste_id = tp.id
            LEFT JOIN contracts c ON e.id = c.employee_id AND c.deleted_at IS NULL
            LEFT JOIN diplomes dip ON e.diplome_id = dip.id
            LEFT JOIN ecoles ec ON e.ecole_id = ec.id
            WHERE e.id = ? AND e.deleted_at IS NULL
        """, (employee_id,))
        
        employee = cur.fetchone()
        
        if employee and str(employee['operator_id']) == str(session.get('operator_id')):
            # Convertir les dates en format ISO pour le frontend
            birth_date = employee['birth_date'] if employee['birth_date'] else None
            
            employee_data = {
                'id': employee['id'],
                'first_name': employee['first_name'],
                'last_name': employee['last_name'],
                'birth_date': birth_date,
                'gender': employee['gender'],
                'contact': employee['contact'],
                'region_id': employee['region_id'],
                'departement_id': employee['departement_id'],
                'sous_prefecture_id': employee['sous_prefecture_id'],
                'poste_id': employee['poste_id'],
                'contract_start': employee['contract_start'],
                'contract_end': employee['contract_end'],
                'contract_salary': employee['contract_salary'],
                'contract_category': employee['contract_category'],
                'contract_position': employee['contract_position'],
                'contract_status': employee['contract_status'],
                'region_nom': employee['region_nom'],
                'departement_nom': employee['departement_nom'],
                'sous_prefecture_nom': employee['sous_prefecture_nom'],
                'poste_nom': employee['poste_nom'],
                'diplome_nom': employee['diplome_nom'],
                'ecole_nom': employee['ecole_nom'],
                'availability': employee['availability']
            }
            
            return jsonify({
                'success': True,
                'employee': employee_data
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Employé non trouvé ou accès non autorisé'
            }), 404
            
    except Exception as e:
        print(f"Erreur lors de la récupération de l'employé: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

employee_service = EmployeeService()

@app.route('/api/employees/<employee_id>/contracts')
@login_required
def get_employee_contracts(employee_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Récupérer les informations de l'employé
        cursor.execute("SELECT first_name, last_name FROM employees WHERE id = ?", (employee_id,))
        employee = cursor.fetchone()
        
        if not employee:
            return jsonify({'success': False, 'error': 'Employé non trouvé'}), 404
        
        # Récupérer les contrats avec le poste directement depuis la table contracts
        query = """
            SELECT 
                c.id,
                c.type,
                c.start_date,
                c.end_date,
                c.position,
                CAST((julianday(c.end_date) - julianday(c.start_date)) / 30 AS INTEGER) as duration_months,
                CASE 
                    WHEN date('now') > date(c.end_date) THEN 'Expiré'
                    WHEN date('now') >= date(c.start_date) AND date('now') <= date(c.end_date) THEN 'En cours'
                    WHEN date('now') < date(c.start_date) THEN 'À venir'
                END as status
            FROM contracts c
            WHERE c.employee_id = ? AND c.deleted_at IS NULL
            ORDER BY c.start_date DESC
        """
        
        cursor.execute(query, (employee_id,))
        contracts = []
        
        for row in cursor.fetchall():
            contract = dict(row)
            # Formater la durée en mois
            if contract['duration_months']:
                contract['duration'] = f"{contract['duration_months']} mois"
            else:
                contract['duration'] = "Non spécifié"
            
            # Utiliser le poste directement depuis la table contracts
            contract['poste'] = contract['position'] if contract['position'] else "Non spécifié"
            
            contracts.append(contract)
        
        return jsonify({
            'success': True,
            'employee': {
                'first_name': employee['first_name'],
                'last_name': employee['last_name']
            },
            'contracts': contracts
        })
    
    except Exception as e:
        print(f"Erreur lors de la récupération des contrats: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Erreur lors de la récupération des contrats: {str(e)}"
        }), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/employees/<employee_id>', methods=['PUT'])
@login_required
def update_employee(employee_id):
    conn = None
    try:
        data = request.get_json()
        print(f"Tentative de modification de l'employé {employee_id}")
        print("Données reçues:", json.dumps(data, indent=2))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vérifier si l'employé existe
        cursor.execute("SELECT id FROM employees WHERE id = ? AND deleted_at IS NULL", (employee_id,))
        employee = cursor.fetchone()
        if not employee:
            print(f"Employé {employee_id} non trouvé")
            return jsonify({'success': False, 'error': 'Employé non trouvé'}), 404

        print(f"Employé {employee_id} trouvé, mise à jour en cours...")

        # Nettoyer les données avant la mise à jour
        update_fields = {
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'gender': data.get('gender'),
            'birth_date': data.get('birth_date'),
            'region_id': data.get('region_id'),
            'departement_id': data.get('departement_id'),
            'sous_prefecture_id': data.get('sous_prefecture_id'),
            'additional_info': data.get('additional_info'),
            'contact': data.get('contact'),
            'contract_duration': data.get('contract_duration'),
            'ecole_id': data.get('ecole_id') if data.get('ecole_id') and data.get('ecole_id') != '' else None,
            'diplome_id': data.get('diplome_id') if data.get('diplome_id') and data.get('diplome_id') != '' else None,
            'poste_id': data.get('poste_id') if data.get('poste_id') and data.get('poste_id') != '' else None,
            'availability': data.get('availability', 'Au siège')  # Changé de location à availability
        }

        # Construire la requête de mise à jour dynamiquement
        update_fields_filtered = {k: v for k, v in update_fields.items() if v is not None}
        update_query = """
            UPDATE employees 
            SET {} 
            WHERE id = ?
        """.format(
            ', '.join(f"{key} = ?" for key in update_fields_filtered.keys())
        )
        
        # Ajouter updated_at au champ et à la valeur
        update_fields_filtered['updated_at'] = 'CURRENT_TIMESTAMP'
        update_query = update_query.replace('updated_at = ?', 'updated_at = CURRENT_TIMESTAMP')
        
        # Préparer les paramètres
        update_params = list(update_fields_filtered.values())
        if 'CURRENT_TIMESTAMP' in update_params:
            update_params.remove('CURRENT_TIMESTAMP')
        update_params.append(employee_id)
        
        print("Requête de mise à jour:", update_query)
        print("Paramètres:", update_params)
        
        cursor.execute(update_query, update_params)
        
        # Marquer uniquement le dernier contrat comme terminé
        cursor.execute("""
            WITH LastContract AS (
                SELECT id
                FROM contracts
                WHERE employee_id = ? 
                AND deleted_at IS NULL
                ORDER BY start_date DESC
                LIMIT 1
            )
            UPDATE contracts 
            SET deleted_at = CURRENT_TIMESTAMP,
                status = 'Expiré'
            WHERE id IN (SELECT id FROM LastContract)
        """, (employee_id,))
        
        # Créer un nouveau contrat
        start_date = data.get('contract_start_date') or datetime.now().strftime('%Y-%m-%d')
        contract_duration = data.get('contract_duration', 3)
        end_date = datetime.strptime(start_date, '%Y-%m-%d') + relativedelta(months=int(contract_duration))
        current_date = datetime.now()
        
        # Déterminer le statut du contrat
        contract_status = 'En cours' if end_date.date() > current_date.date() else 'Expiré'
        
        # Récupérer le texte du poste si disponible, sinon utiliser le poste_id
        position = data.get('poste')  # Utiliser le texte du poste envoyé depuis le frontend
        print("Position from form:", position)  # Debug log
        
        if not position and data.get('poste_id'):
            # Si le texte du poste n'est pas disponible, essayer de le récupérer depuis la table postes
            cursor.execute("SELECT titre FROM postes WHERE id = ?", (data.get('poste_id'),))
            poste_result = cursor.fetchone()
            if poste_result:
                position = poste_result['titre']
                print("Position from database:", position)  # Debug log
            
        print("Final position value:", position)  # Debug log
        
        new_contract_id = str(uuid.uuid4())
        print("Contract data:", {  # Debug log
            'contract_id': new_contract_id,
            'employee_id': employee_id,
            'categorie': data.get('categorie'),
            'start_date': start_date,
            'end_date': end_date.strftime('%Y-%m-%d'),
            'status': contract_status,
            'diplome_id': data.get('diplome_id'),
            'ecoles_id': data.get('ecole_id'),
            'type': data.get('contract_type', 'CDD'),
            'position': position
        })
        
        cursor.execute("""
            INSERT INTO contracts (
                id, employee_id, categorie, start_date, end_date, status,
                diplome_id, ecoles_id, type, position,
                created_at, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """, (
            new_contract_id,
            employee_id,
            data.get('categorie'),
            start_date,
            end_date.strftime('%Y-%m-%d'),
            contract_status,
            data.get('diplome_id'),
            data.get('ecole_id'),
            data.get('contract_type', 'CDD'),
            position  # Utiliser la variable position qui contient le texte du poste
        ))
        
        print(f"Nouveau contrat {new_contract_id} créé pour l'employé avec le statut {contract_status}")

        conn.commit()
        print(f"Modification de l'employé {employee_id} réussie")
        
        return jsonify({
            'success': True, 
            'message': 'Employé et contrat mis à jour avec succès'
        })
            
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Erreur lors de la modification de l'employé {employee_id}: {str(e)}")
        return jsonify({
            'success': False, 
            'error': f"Erreur lors de la mise à jour: {str(e)}"
        }), 500
    finally:
        if conn:
            conn.close() 

@app.route('/api/employees/<employee_id>', methods=['DELETE'])
@login_required
def delete_employee(employee_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vérifier si l'employé existe
        cursor.execute("SELECT id FROM employees WHERE id = ? AND deleted_at IS NULL", (employee_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Employé non trouvé'}), 404
        
        # Supprimer d'abord les contrats associés
        cursor.execute("DELETE FROM contracts WHERE employee_id = ?", (employee_id,))
        
        # Puis supprimer l'employé
        cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        
        conn.commit()
        return jsonify({
            'success': True, 
            'message': 'Employé supprimé avec succès'
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error deleting employee: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'Erreur lors de la suppression de l\'employé'
        }), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/employees', methods=['POST'])
@login_required
def create_employee():
    conn = None
    try:
        data = request.get_json()
        print("Données avant création:", json.dumps(data, indent=2))
        
        # Valider les données requises
        required_fields = ['first_name', 'last_name', 'operator_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Le champ {field} est requis'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Générer un nouvel ID
        employee_id = str(uuid.uuid4())
        
        # Insérer l'employé
        insert_query = """
            INSERT INTO employees (
                id, operator_id, first_name, last_name, gender, birth_date,
                contact, contract_duration, region_id, departement_id,
                sous_prefecture_id, additional_info, availability,
                ecole_id, diplome_id, poste_id, created_at, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """
        
        # Préparer les paramètres
        params = [
            employee_id,
            data.get('operator_id'),
            data.get('first_name'),
            data.get('last_name'),
            data.get('gender'),
            data.get('birth_date'),
            data.get('contact'),
            data.get('contract_duration'),
            data.get('region_id'),
            data.get('departement_id'),
            data.get('sous_prefecture_id'),
            data.get('additional_info'),
            'Au siège',  # Valeur par défaut pour availability
            data.get('ecole_id') if data.get('ecole_id') and data.get('ecole_id') != '' else None,
            data.get('diplome_id') if data.get('diplome_id') and data.get('diplome_id') != '' else None,
            data.get('poste_id') if data.get('poste_id') and data.get('poste_id') != '' else None
        ]
        
        print("Paramètres de la requête:", tuple(params))
        cursor.execute(insert_query, params)
        
        # Créer le contrat initial
        start_date = data.get('contract_start_date') or datetime.now().strftime('%Y-%m-%d')
        contract_duration = data.get('contract_duration', 3)
        end_date = datetime.strptime(start_date, '%Y-%m-%d') + relativedelta(months=int(contract_duration))
        current_date = datetime.now()
        
        # Déterminer le statut du contrat
        contract_status = 'En cours' if end_date.date() > current_date.date() else 'Expiré'
        
        # Récupérer le texte du poste si disponible, sinon utiliser le poste_id
        position = data.get('poste')  # Utiliser le texte du poste envoyé depuis le frontend
        print("Position from form:", position)  # Debug log
        
        if not position and data.get('poste_id'):
            # Si le texte du poste n'est pas disponible, essayer de le récupérer depuis la table postes
            cursor.execute("SELECT titre FROM postes WHERE id = ?", (data.get('poste_id'),))
            poste_result = cursor.fetchone()
            if poste_result:
                position = poste_result['titre']
                print("Position from database:", position)  # Debug log
            
        print("Final position value:", position)  # Debug log
        
        contract_id = str(uuid.uuid4())
        print("Contract data:", {  # Debug log
            'contract_id': contract_id,
            'employee_id': employee_id,
            'categorie': data.get('categorie'),
            'start_date': start_date,
            'end_date': end_date.strftime('%Y-%m-%d'),
            'status': contract_status,
            'diplome_id': data.get('diplome_id'),
            'ecoles_id': data.get('ecole_id'),
            'type': data.get('contract_type', 'CDD'),
            'position': position
        })
        
        cursor.execute("""
            INSERT INTO contracts (
                id, employee_id, categorie, start_date, end_date, status,
                diplome_id, ecoles_id, type, position,
                created_at, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """, (
            contract_id,
            employee_id,
            data.get('categorie'),
            start_date,
            end_date.strftime('%Y-%m-%d'),
            contract_status,
            data.get('diplome_id'),
            data.get('ecole_id'),
            data.get('contract_type', 'CDD'),
            position  # Utiliser la variable position qui contient le texte du poste
        ))
        
        conn.commit()
        return jsonify({
            'success': True,
            'message': 'Employé créé avec succès',
            'employee_id': employee_id
        }), 201
            
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Erreur lors de la création de l'employé: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Erreur lors de la création: {str(e)}"
        }), 500
    finally:
        if conn:
            conn.close() 

@app.route('/api/employees/delete-multiple', methods=['POST'])
@login_required
def delete_multiple_employees():
    try:
        data = request.get_json()
        if not data or 'employee_ids' not in data:
            return jsonify({'error': 'Liste des employés manquante'}), 400

        employee_ids = data['employee_ids']
        if not employee_ids:
            return jsonify({'error': 'Aucun employé sélectionné'}), 400

        conn = sqlite3.connect('data/db/geogestion.db')
        cur = conn.cursor()

        try:
            # Supprimer les contrats associés
            placeholders = ','.join(['?' for _ in employee_ids])
            cur.execute(f"""
                DELETE FROM contracts 
                WHERE employee_id IN ({placeholders})
            """, employee_ids)

            # Supprimer les employés
            cur.execute(f"""
                DELETE FROM employees 
                WHERE id IN ({placeholders})
            """, employee_ids)

            conn.commit()
            return jsonify({
                'success': True,
                'message': f'{len(employee_ids)} employé(s) supprimé(s) avec succès'
            })

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cur.close()
            conn.close()

    except Exception as e:
        print(f"Erreur lors de la suppression multiple: {str(e)}")
        return jsonify({'error': 'Erreur lors de la suppression des employés'}), 500

@app.route('/api/contracts/renew', methods=['POST'])
@login_required
def renew_contracts():
    conn = None
    try:
        data = request.get_json()
        employee_ids = data.get('employee_ids')
        start_date = data.get('start_date')
        duration = data.get('duration')
        position = data.get('position')

        if not all([employee_ids, start_date, duration, position ]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Calculer la date de fin
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = (start_date_obj + timedelta(days=int(duration) * 30)).strftime('%Y-%m-%d')
        except ValueError as e:
            return jsonify({'error': 'Invalid date format'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        for employee_id in employee_ids:
            # Récupérer les informations du dernier contrat
            cursor.execute("""
                SELECT type, salary, department, status
                FROM contracts 
                WHERE employee_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (employee_id,))
            
            last_contract = cursor.fetchone()
            if not last_contract:
                return jsonify({'error': f'Aucun contrat trouvé pour l\'employé {employee_id}'}), 404

            # Créer un nouveau contrat
            new_contract_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO contracts (
                    id, employee_id, type, start_date, end_date,
                    salary, department, position, status, additional_terms,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_contract_id,
                employee_id,
                last_contract['type'],
                start_date,
                end_date,
                last_contract['salary'],
                last_contract['department'],
                position,
                'En cours',
                '',  # additional_terms
                now,
                now
            ))
            
            # Mettre à jour l'employé
            cursor.execute("""
                UPDATE employees 
                SET position = ?,
                    contract_duration = ?,
                    updated_at = ?
                WHERE id = ?
            """, (position, duration, now, employee_id))

        conn.commit()
        return jsonify({'success': True, 'message': 'Contrats renouvelés avec succès'}), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error renewing contracts: {str(e)}")
        return jsonify({'error': 'Erreur lors du renouvellement des contrats'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/employees/renew', methods=['POST'])
@login_required
def renew_employee_contract():
    try:
        data = request.get_json()
        print("Données reçues pour le renouvellement:", data)
        
        # Validation des champs requis de base
        required_fields = ['employee_ids', 'start_date', 'duration', 'poste_id', 'categorie', 'diplome_id', 'ecole_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Le champ {field} est requis'
                }), 400

        # Calculer la date de fin
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        duration_months = int(data['duration'])
        end_date = start_date + relativedelta(months=duration_months)
        
        conn = get_db_connection()
        cursor = conn.cursor()

        # Récupérer le nom du poste
        cursor.execute("SELECT titre FROM postes WHERE id = ?", (data['poste_id'],))
        poste_result = cursor.fetchone()
        if not poste_result:
            return jsonify({
                'success': False,
                'error': 'Poste non trouvé'
            }), 400
        poste_title = poste_result['titre']

        for employee_id in data['employee_ids']:
            # Créer un nouveau contrat
            contract_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            # Insérer le nouveau contrat
            cursor.execute("""
                INSERT INTO contracts (
                    id, employee_id, start_date, end_date, 
                    categorie, diplome_id, ecole_id,
                    status, created_at, updated_at, position
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contract_id,
                employee_id,
                data['start_date'],
                end_date.strftime('%Y-%m-%d'),
                data['categorie'],
                data['diplome_id'],
                data['ecole_id'],
                'En cours',
                now,
                now,
                poste_title  # Utiliser le titre du poste au lieu de l'ID
            ))

            # Mettre à jour la disponibilité de l'employé
            availability = 'interieur' if data.get('location') == 'interieur' else 'siege'
            cursor.execute("""
                UPDATE employees 
                SET availability = ?,
                    updated_at = ?
                WHERE id = ?
            """, (availability, now, employee_id))

            # Vérifier si tous les champs de localisation sont présents
            if (data.get('location') == 'interieur' and 
                data.get('region_id') and 
                data.get('departement_id') and 
                data.get('sous_prefecture_id')):
                
                location_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO employee_locations (
                        id, employee_id, contract_id, 
                        region_id, departement_id, sous_prefecture_id,
                        date_debut, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    location_id,
                    employee_id,
                    contract_id,
                    data['region_id'],
                    data['departement_id'],
                    data['sous_prefecture_id'],
                    data['start_date'],
                    now
                ))

        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contrat(s) renouvelé(s) avec succès'
        })

    except Exception as e:
        print(f"Erreur lors du renouvellement du contrat: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return jsonify({
            'success': False,
            'error': f"Erreur lors du renouvellement: {str(e)}"
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Récupère les statistiques des employés"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        operator_id = session.get('operator_id')

        if not operator_id:
            return jsonify({"error": "Opérateur non connecté"}), 401

        # Statistiques de base
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN gender = 'M' THEN 1 ELSE 0 END) as male,
                SUM(CASE WHEN gender = 'F' THEN 1 ELSE 0 END) as female,
                SUM(CASE WHEN availability = 'Disponible' THEN 1 ELSE 0 END) as available,
                SUM(CASE WHEN availability = 'Non disponible' THEN 1 ELSE 0 END) as unavailable,
                SUM(CASE 
                    WHEN birth_date IS NOT NULL 
                    AND (julianday('now') - julianday(birth_date)) / 365.25 BETWEEN 14 AND 35 
                    THEN 1 ELSE 0 END
                ) as young_employees
            FROM employees 
            WHERE operator_id = ? 
        """, (operator_id,))
        
        stats = cursor.fetchone()
        if stats:
            return jsonify({
                'total': stats['total'] or 0,
                'male': stats['male'] or 0,
                'female': stats['female'] or 0,
                'available': stats['available'] or 0,
                'unavailable': stats['unavailable'] or 0,
                'young_employees': stats['young_employees'] or 0
            })
        else:
            return jsonify({
                'total': 0,
                'male': 0,
                'female': 0,
                'available': 0,
                'unavailable': 0,
                'young_employees': 0
            })
        
    except Exception as e:
        print(f"Erreur lors de la récupération des statistiques: {str(e)}")
        return jsonify({'error': 'Erreur lors de la récupération des statistiques'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/health')
def health_check():
    """Route de vérification de santé pour Render"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    """Change le mot de passe de l'acteur connecté"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': 'Tous les champs sont requis'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vérifier le mot de passe actuel
        cursor.execute("""
            SELECT password FROM operators 
            WHERE id = ? AND password = ?
        """, (session.get('operator_id'), current_password))
        
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Mot de passe actuel incorrect'}), 401
            
        # Mettre à jour le mot de passe
        cursor.execute("""
            UPDATE operators 
            SET password = ?
            WHERE id = ?
        """, (new_password, session.get('operator_id')))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Mot de passe modifié avec succès'})
        
    except Exception as e:
        print(f"Erreur lors du changement de mot de passe: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/logout')
def logout():
    """Déconnexion de l'opérateur"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Récupère la liste des projets"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nom as name, description 
            FROM projects 
            ORDER BY nom
        """)
        projects = [{'id': row['id'], 'name': row['name'], 'description': row['description']} 
                   for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'projects': projects})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/actor_types', methods=['GET'])
def get_actor_types():
    """Récupère la liste des types d'acteurs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nom as name, description 
            FROM acteurs_type 
            ORDER BY nom
        """)
        actor_types = [{'id': row['id'], 'name': row['name'], 'description': row['description']} 
                      for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'actor_types': actor_types})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/actors/<actor_type_id>', methods=['GET'])
def get_actors_by_type(actor_type_id):
    """Récupère la liste des acteurs par type"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, contact1 
            FROM operators 
            WHERE acteur_type_id = ?
            ORDER BY name
        """, (actor_type_id,))
        actors = [{'id': row['id'], 'name': row['name'], 'contact': row['contact1']} 
                 for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'actors': actors})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/actors/<project_id>/<actor_type_id>', methods=['GET'])
def get_actors_by_project_and_type(project_id, actor_type_id):
    """Récupère la liste des acteurs selon le projet et leur type"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Récupérer le nom du type d'acteur
        cursor.execute("""
            SELECT nom 
            FROM acteurs_type 
            WHERE id = ?
        """, (actor_type_id,))
        actor_type = cursor.fetchone()

        if not actor_type:
            return jsonify({'success': False, 'error': 'Type d\'acteur non trouvé'}), 404

        actor_type_name = actor_type['nom']

        # Vérifier si le projet existe
        cursor.execute("""
            SELECT id, nom 
            FROM projects 
            WHERE id = ?
        """, (project_id,))
        project = cursor.fetchone()

        if not project:
            return jsonify({'success': False, 'error': 'Projet non trouvé'}), 404

        if "Ecole" in actor_type_name:
            # Pour les écoles partenaires
            cursor.execute("""
                SELECT e.id, e.nom as name, e.sigle
                FROM ecoles e
                INNER JOIN school_projects sp ON e.id = sp.school_id 
                WHERE sp.project_id = ?
                ORDER BY e.nom
            """, (project_id,))
            
            actors = [{
                'id': row['id'],
                'name': f"{row['name']} ({row['sigle']})" if row['sigle'] else row['name'],
                'in_project': True
            } for row in cursor.fetchall()]

        else:
            # Pour les opérateurs et agences d'exécution
            cursor.execute("""
                SELECT o.id, o.name, o.contact1, o.email1
                FROM operators o
                INNER JOIN operator_projects op ON o.id = op.operator_id 
                WHERE op.project_id = ? 
                AND o.acteur_type_id = ?
                ORDER BY o.name
            """, (project_id, actor_type_id,))
            
            actors = [{
                'id': row['id'],
                'name': row['name'],
                'contact': row['contact1'],
                'email': row['email1'],
                'in_project': True
            } for row in cursor.fetchall()]

        conn.close()
        return jsonify({
            'success': True, 
            'actors': actors,
            'actor_type': actor_type_name,
            'project_name': project['nom']
        })

    except Exception as e:
        print(f"Erreur lors de la récupération des acteurs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/regions/<project_id>', methods=['GET'])
def get_regions_by_project(project_id):
    """Récupère les régions liées à un projet"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT r.id, r.name
            FROM regions r
            JOIN project_regions pr ON r.id = pr.region_id
            WHERE pr.project_id = ?
            ORDER BY r.name
        """, (project_id,))
        
        regions = [{'id': row['id'], 'name': row['name']} for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'regions': regions})
    except Exception as e:
        print(f"Erreur lors de la récupération des régions: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/departements/<region_id>')
def get_departements(region_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vérifier si la région existe
        cursor.execute("SELECT id FROM regions WHERE id = ? AND deleted_at IS NULL", (region_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Région non trouvée"}), 404

        # Récupérer les départements
        cursor.execute("""
            SELECT id, nom as name 
            FROM departements 
            WHERE region_id = ? 
            AND deleted_at IS NULL 
            ORDER BY nom
        """, (region_id,))
        
        departements = []
        for row in cursor.fetchall():
            departements.append({
                'id': row['id'],
                'name': row['name']
            })
        
        print(f"Départements trouvés pour la région {region_id}:", departements)  # Debug
        return jsonify({"success": True, "data": departements})
    except Exception as e:
        print(f"Erreur lors de la récupération des départements: {str(e)}")  # Debug
        return jsonify({"success": False, "error": str(e)})
    finally:
        if conn:
            conn.close()

@app.route('/api/sousprefectures/<departement_id>')
def get_sousprefectures(departement_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vérifier si le département existe
        cursor.execute("SELECT id FROM departements WHERE id = ? AND deleted_at IS NULL", (departement_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Département non trouvé"}), 404

        # Récupérer les sous-préfectures
        cursor.execute("""
            SELECT id, nom as name 
            FROM sous_prefectures 
            WHERE departement_id = ? 
            AND deleted_at IS NULL 
            ORDER BY nom
        """, (departement_id,))
        
        sousprefectures = []
        for row in cursor.fetchall():
            sousprefectures.append({
                'id': row['id'],
                'name': row['name']
            })
        
        print(f"Sous-préfectures trouvées pour le département {departement_id}:", sousprefectures)  # Debug
        return jsonify({"success": True, "data": sousprefectures})
    except Exception as e:
        print(f"Erreur lors de la récupération des sous-préfectures: {str(e)}")  # Debug
        return jsonify({"success": False, "error": str(e)})
    finally:
        if conn:
            conn.close()

@app.route('/api/regions')
def get_regions():
    try:
        # Récupérer le project_id de la session
        project_id = session.get('project_id')
        if not project_id:
            return jsonify({"success": False, "error": "Aucun projet sélectionné"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Récupérer les régions associées au projet via project_regions
        cursor.execute("""
            SELECT r.id, r.nom as name 
            FROM regions r
            INNER JOIN project_regions pr ON r.id = pr.region_id
            WHERE pr.project_id = ?
            AND r.deleted_at IS NULL 
            ORDER BY r.nom
        """, (project_id,))
        
        regions = [dict(id=row['id'], name=row['name']) for row in cursor.fetchall()]
        print(f"Régions trouvées pour le projet {project_id}:", regions)  # Debug
        
        return jsonify({"success": True, "data": regions})
    except Exception as e:
        print(f"Erreur lors de la récupération des régions: {str(e)}")  # Debug
        return jsonify({"success": False, "error": str(e)})
    finally:
        if conn:
            conn.close()

@app.route('/api/postes')
def get_postes():
    """Récupère la liste des postes actifs"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, titre 
            FROM postes 
            WHERE deleted_at IS NULL
            ORDER BY titre
        """)
        postes = [{"id": row[0], "titre": row[1]} for row in cursor.fetchall()]
        return jsonify({"success": True, "data": postes})
    except Exception as e:
        print(f"Erreur lors de la récupération des postes: {str(e)}")
        return jsonify({"success": False, "error": str(e)})
    finally:
        if conn:
            conn.close()

@app.route('/api/diplomes')
def get_diplomes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nom as name 
            FROM diplomes 
            ORDER BY nom
        """)
        diplomes = [dict(id=row['id'], name=row['name']) for row in cursor.fetchall()]
        return jsonify({"success": True, "data": diplomes})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/ecoles')
def get_ecoles():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nom as name 
            FROM ecoles 
            ORDER BY nom
        """)
        ecoles = [dict(id=row['id'], name=row['name']) for row in cursor.fetchall()]
        return jsonify({"success": True, "data": ecoles})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/categories')
def get_categories():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vérifier si la table existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='type_poste'
        """)
        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Table type_poste not found"})
            
        # Compter le nombre d'entrées
        cursor.execute("SELECT COUNT(*) FROM type_poste")
        count = cursor.fetchone()[0]
        
        # Récupérer les données
        cursor.execute("""
            SELECT id, fonction as name
            FROM type_poste 
            ORDER BY fonction
        """)
        categories = []
        for row in cursor.fetchall():
            categories.append({
                "id": row[0],
                "name": row[1]
            })
        
        conn.close()
        return jsonify({
            "success": True, 
            "count": count,
            "data": categories
        })
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({
            "success": False, 
            "error": str(e)
        })

@app.route('/api/employees/operator')
@login_required
def get_operator_employees():
    """Récupère les employés de l'opérateur connecté"""
    try:
        operator_id = session.get('operator_id')
        if not operator_id:
            return jsonify({
                'error': 'Opérateur non connecté',
                'success': False
            }), 401

        print(f"Récupération des employés pour l'opérateur: {operator_id}")  # Debug log
        
        employees = employee_service.get_employees_by_operator(operator_id)
        print(f"Nombre d'employés trouvés: {len(employees)}")  # Debug log
        
        return jsonify(employees)
        
    except Exception as e:
        print(f"Erreur dans get_operator_employees: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/api/current-operator', methods=['GET'])
@login_required
def get_current_operator():
    try:
        # Récupérer l'ID de l'opérateur depuis la session
        operator_id = session.get('operator_id')
        if not operator_id:
            return jsonify({'success': False, 'message': 'Non authentifié'}), 401
            
        # Connexion à la base de données
        conn = get_db_connection()
        cur = conn.cursor()

        # Récupérer les informations de l'opérateur
        cur.execute('SELECT id, name FROM operators WHERE id = ?', (operator_id,))
        operator = cur.fetchone()

        # Fermer la connexion
        cur.close()
        conn.close()

        if operator:
            return jsonify({
                'success': True,
                'operator': {
                    'id': operator['id'],
                    'name': operator['name']
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Opérateur non trouvé'}), 404

    except Exception as e:
        print('Erreur lors de la récupération de l\'opérateur:', str(e))
        return jsonify({'success': False, 'message': 'Erreur serveur'}), 500

@app.route('/api/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET':
        return render_template('admin/login.html')
    
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return jsonify({
                'success': False,
                'error': 'Tous les champs sont requis'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT email, name, password
            FROM administrators 
            WHERE email = ?
        """, (email,))
        
        admin = cursor.fetchone()
        
        if not admin:
            return jsonify({
                'success': False,
                'error': 'Administrateur non trouvé'
            }), 404
        
        if admin['password'] != password:
            return jsonify({
                'success': False,
                'error': 'Mot de passe incorrect'
            }), 401
        
        session['admin_id'] = admin['email']
        session['admin_name'] = admin['name']
        
        return jsonify({
            'success': True,
            'redirect': '/admin/dashboard'
        })
        
    except Exception as e:
        print(f"Erreur de connexion admin: {str(e)}")  # Ajout de log pour le debug
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/api/contracts/<contract_id>/renew', methods=['POST'])
@login_required
def renew_contract(contract_id):
    conn = None
    try:
        data = request.get_json()
        print(f"Tentative de reconduction du contrat {contract_id}")
        print("Données reçues:", json.dumps(data, indent=2))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Récupérer l'ancien contrat
        cursor.execute("""
            SELECT c.*, e.first_name, e.last_name, e.position, e.ecole_id, e.diplome_id, e.poste_id
            FROM contracts c
            JOIN employees e ON c.employee_id = e.id
            WHERE c.id = ? AND c.deleted_at IS NULL
        """, (contract_id,))
        old_contract = cursor.fetchone()
        
        if not old_contract:
            return jsonify({'success': False, 'error': 'Contrat non trouvé'}), 404
            
        # Marquer l'ancien contrat comme expiré
        cursor.execute("""
            UPDATE contracts 
            SET deleted_at = CURRENT_TIMESTAMP,
                status = 'Expiré'
            WHERE id = ?
        """, (contract_id,))
        
        # Créer un nouveau contrat
        new_contract_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO contracts (
                id, employee_id, type, start_date, end_date,
                salary, department, status,
                created_at, updated_at, position
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_contract_id,
            old_contract['employee_id'],
            old_contract['type'],
            data.get('start_date'),
            data.get('end_date'),
            old_contract['salary'],
            old_contract['department'],
            'En cours',
            now,
            now,
            data.get('poste')  # Ajout du poste dans le contrat
        ))
        
        conn.commit()
        print(f"Contrat {contract_id} reconduit avec succès. Nouveau contrat: {new_contract_id}")
        
        return jsonify({
            'success': True,
            'message': 'Contrat reconduit avec succès',
            'new_contract_id': new_contract_id
        })
            
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Erreur lors de la reconduction du contrat {contract_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Erreur lors de la reconduction: {str(e)}"
        }), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/contracts/<contract_id>', methods=['GET'])
@login_required
def get_contract(contract_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.*, e.first_name, e.last_name, e.position, e.ecole_id, e.diplome_id, e.poste_id
            FROM contracts c
            JOIN employees e ON c.employee_id = e.id
            WHERE c.id = ? AND c.deleted_at IS NULL
        """, (contract_id,))
        contract = cursor.fetchone()
        
        if not contract:
            return jsonify({'success': False, 'error': 'Contrat non trouvé'}), 404
            
        return jsonify({
            'success': True,
            'contract': dict(contract)
        })
            
    except Exception as e:
        print(f"Erreur lors de la récupération du contrat {contract_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Erreur lors de la récupération: {str(e)}"
        }), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)
