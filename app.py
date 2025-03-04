from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import uuid
from datetime import datetime, timedelta
import sqlite3
from dotenv import load_dotenv
from auth.sqlite_auth import SQLiteAuth
from services.employee_service import EmployeeService
from admin.routes import admin_bp
from functools import wraps
import json

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))  # Clé secrète pour la session

# Enregistrer le blueprint d'administration
app.register_blueprint(admin_bp)

# Initialiser les services
auth = SQLiteAuth()
employee_service = EmployeeService()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'operator_id' not in session:
            return jsonify({"success": False, "error": "Non autorisé"}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    """Établit une connexion à la base de données SQLite"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'db', 'geogestion.db')
    conn = sqlite3.connect(db_path)
    return conn

def init_db():
    """Initialise la base de données"""
    conn = get_db_connection()
    cursor = conn.cursor()

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

    conn.commit()
    conn.close()

# Initialiser la base de données au démarrage
init_db()

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
        if operator[3] != password:
            return jsonify({
                'success': False,
                'error': 'Mot de passe incorrect'
            }), 401
        
        # Stocker les informations dans la session
        session['operator_id'] = operator[0]
        session['operator_name'] = operator[1]
        session['actor_type'] = operator[4]
        session['project_id'] = project_id  # Ajouter le project_id à la session
        
        print(f"Login réussi - Opérateur: {operator[1]}, Projet: {project_id}")  # Debug
        
        return jsonify({
            'success': True,
            'operator': {
                'id': operator[0],
                'name': operator[1],
                'phone': operator[2]
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
def dashboard():
    """Affiche le tableau de bord de l'opérateur"""
    if 'operator_id' not in session:
        return redirect(url_for('index'))
    
    # Récupérer le nom de l'opérateur
    operator = auth.get_operator_by_id(session['operator_id'])
    operator_name = operator['name'] if operator else 'Inconnu'
    
    return render_template('dashboard.html', operator_name=operator_name)

@app.route('/api/employees', methods=['GET'])
@login_required
def get_employees():
    """Récupère la liste des employés de l'opérateur connecté"""
    try:
        employees = employee_service.get_employees_by_operator(session['operator_id'])
        return jsonify(employees)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/employees/<employee_id>', methods=['GET'])
@login_required
def get_employee(employee_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Récupérer les informations de l'employé
        cursor.execute("""
            SELECT e.*, 
                   c.id as contract_id, 
                   c.start_date, 
                   c.end_date, 
                   c.status as contract_status,
                   c.type as contract_type
            FROM employees e
            LEFT JOIN contracts c ON e.id = c.employee_id
            WHERE e.id = ?
            ORDER BY c.created_at DESC
            LIMIT 1
        """, (employee_id,))
        
        row = cursor.fetchone()
        if row:
            employee = {
                'id': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'position': row[3],
                'contact': row[4],
                'gender': row[5],
                'birth_date': row[6],
                'additional_info': row[8]
            }
            
            if row[9]:
                employee['contract'] = {
                    'id': row[9],
                    'start_date': row[10],
                    'end_date': row[11],
                    'status': row[12],
                    'type': row[13]
                }
            
            return jsonify(employee)
        else:
            return jsonify({'error': 'Employé non trouvé'}), 404
            
    except Exception as e:
        print(f"Error getting employee: {str(e)}")
        return jsonify({'error': 'Erreur lors de la récupération de l\'employé'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/employees/<employee_id>/contracts', methods=['GET'])
@login_required
def get_employee_contracts(employee_id):
    """Récupère l'historique des contrats d'un employé"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vérifier que l'employé existe et appartient à l'opérateur connecté
        cursor.execute("""
            SELECT id, first_name, last_name 
            FROM employees 
            WHERE id = ? AND operator_id = ?
        """, (employee_id, session.get('operator_id')))
        
        employee = cursor.fetchone()
        if not employee:
            return jsonify({'error': 'Employé non trouvé'}), 404
        
        # Récupérer tous les contrats de l'employé
        cursor.execute("""
            SELECT 
                c.id,
                c.type,
                c.start_date,
                c.end_date,
                c.status,
                c.position,
                c.additional_terms
            FROM contracts c
            WHERE c.employee_id = ?
            ORDER BY c.start_date DESC
        """, (employee_id,))
        
        contracts = []
        for row in cursor.fetchall():
            contracts.append({
                'id': row[0],
                'type': row[1],
                'start_date': row[2],
                'end_date': row[3],
                'status': row[4],
                'position': row[5],
                'additional_terms': row[6]
            })
        
        return jsonify({
            'employee': {
                'id': employee[0],
                'first_name': employee[1],
                'last_name': employee[2]
            },
            'contracts': contracts
        })
        
    except Exception as e:
        print(f"Erreur lors de la récupération des contrats: {str(e)}")
        return jsonify({'error': 'Erreur lors de la récupération des contrats'}), 500
    finally:
        conn.close()

@app.route('/api/employees/<employee_id>', methods=['PUT'])
@login_required
def update_employee(employee_id):
    conn = None
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vérifier si l'employé existe
        cursor.execute("SELECT id FROM employees WHERE id = ?", (employee_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Employé non trouvé'}), 404
        
        # Mise à jour de l'employé
        cursor.execute("""
            UPDATE employees 
            SET first_name = ?,
                last_name = ?,
                position = ?,
                contact = ?,
                gender = ?,
                birth_date = ?,
                additional_info = ?
            WHERE id = ?
        """, (
            data.get('first_name'),
            data.get('last_name'),
            data.get('position'),
            data.get('contact'),
            data.get('gender'),
            data.get('birth_date'),
            data.get('additional_info'),
            employee_id
        ))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Employé mis à jour avec succès'})
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error updating employee: {str(e)}")
        return jsonify({'error': 'Erreur lors de la mise à jour de l\'employé'}), 500
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
        cursor.execute("SELECT id FROM employees WHERE id = ?", (employee_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Employé non trouvé'}), 404
        
        # Supprimer d'abord les contrats associés
        cursor.execute("DELETE FROM contracts WHERE employee_id = ?", (employee_id,))
        
        # Puis supprimer l'employé
        cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Employé supprimé avec succès'})
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error deleting employee: {str(e)}")
        return jsonify({'error': 'Erreur lors de la suppression de l\'employé'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/employees', methods=['POST'])
@login_required
def add_employee():
    """Ajoute un nouvel employé"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Données invalides"}), 400

        # Debug logs
        print("Données reçues:", json.dumps(data, indent=2))

        # Ajouter l'ID de l'opérateur aux données
        data['operator_id'] = session['operator_id']
        
        # Validation des données requises
        required_fields = ['first_name', 'last_name', 'position', 'gender']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                "success": False,
                "error": f"Champs requis manquants: {', '.join(missing_fields)}"
            }), 400

        # Ajout de l'employé
        try:
            if employee_service.add_employee(data):
                return jsonify({"success": True, "message": "Employé ajouté avec succès"})
            else:
                return jsonify({"success": False, "error": "Erreur lors de l'ajout de l'employé"}), 500
        except Exception as e:
            print("Erreur dans employee_service.add_employee:", str(e))
            return jsonify({"success": False, "error": str(e)}), 500
            
    except Exception as e:
        print(f"Erreur lors de l'ajout d'un employé: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

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
                last_contract[0],
                start_date,
                end_date,
                last_contract[1],
                last_contract[2],
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
def renew_employee_contracts():
    """Renouvelle les contrats des employés sélectionnés"""
    try:
        data = request.get_json()
        employee_ids = data.get('employee_ids', [])
        start_date = data.get('start_date')
        duration = data.get('duration')
        position = data.get('position')
        
        if not employee_ids:
            return jsonify({'success': False, 'error': 'Aucun employé sélectionné'}), 400
            
        if not all([start_date, duration, position]):
            return jsonify({'success': False, 'error': 'Tous les champs sont requis'}), 400

        # Calculer la date de fin
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = (start_date_obj + timedelta(days=int(duration) * 30)).strftime('%Y-%m-%d')
        except ValueError as e:
            return jsonify({'success': False, 'error': 'Format de date invalide'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for employee_id in employee_ids:
            # Vérifier que l'employé appartient à l'opérateur connecté
            cursor.execute("""
                SELECT id FROM employees 
                WHERE id = ? AND operator_id = ?
            """, (employee_id, session.get('operator_id')))
            
            if not cursor.fetchone():
                continue
                
            # Récupérer les informations du dernier contrat
            cursor.execute("""
                SELECT type, salary, department
                FROM contracts 
                WHERE employee_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (employee_id,))
            
            last_contract = cursor.fetchone()
            if not last_contract:
                continue

            # Mettre à jour le contrat existant
            cursor.execute("""
                UPDATE contracts 
                SET status = 'Expiré',
                    updated_at = ?
                WHERE employee_id = ? AND status = 'En cours'
            """, (datetime.now().isoformat(), employee_id))
            
            # Créer un nouveau contrat
            new_contract_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO contracts (
                    id, employee_id, type, start_date, end_date,
                    salary, department, position, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_contract_id,
                employee_id,
                last_contract[0],
                start_date,
                end_date,
                last_contract[1],
                last_contract[2],
                position,
                'En cours',
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
        return jsonify({'success': True, 'message': 'Contrats renouvelés avec succès'})
        
    except Exception as e:
        print(f"Erreur lors du renouvellement des contrats: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
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
                'total': stats[0] or 0,
                'male': stats[1] or 0,
                'female': stats[2] or 0,
                'available': stats[3] or 0,
                'unavailable': stats[4] or 0,
                'young_employees': stats[5] or 0
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
            SELECT id, nom, description 
            FROM projects 
            ORDER BY nom
        """)
        projects = [{'id': row[0], 'name': row[1], 'description': row[2]} 
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
            SELECT id, nom, description 
            FROM acteurs_type 
            ORDER BY nom
        """)
        actor_types = [{'id': row[0], 'name': row[1], 'description': row[2]} 
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
        actors = [{'id': row[0], 'name': row[1], 'contact': row[2]} 
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

        actor_type_name = actor_type[0]

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
                'id': row[0],
                'name': f"{row[1]} ({row[2]})" if row[2] else row[1],
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
                'id': row[0],
                'name': row[1],
                'contact': row[2],
                'email': row[3],
                'in_project': True
            } for row in cursor.fetchall()]

        conn.close()
        return jsonify({
            'success': True, 
            'actors': actors,
            'actor_type': actor_type_name,
            'project_name': project[1]
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
        
        regions = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
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
                'id': row[0],
                'name': row[1]
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
                'id': row[0],
                'name': row[1]
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
        
        regions = [dict(id=row[0], name=row[1]) for row in cursor.fetchall()]
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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, titre as name 
            FROM postes 
            WHERE deleted_at IS NULL
            ORDER BY titre
        """)
        postes = [dict(id=row[0], name=row[1]) for row in cursor.fetchall()]
        return jsonify({"success": True, "data": postes})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

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
        diplomes = [dict(id=row[0], name=row[1]) for row in cursor.fetchall()]
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
        ecoles = [dict(id=row[0], name=row[1]) for row in cursor.fetchall()]
        return jsonify({"success": True, "data": ecoles})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/categories')
def get_categories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, fonction as name 
            FROM type_poste 
            ORDER BY fonction
        """)
        categories = [dict(id=row[0], name=row[1]) for row in cursor.fetchall()]
        return jsonify({"success": True, "data": categories})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
