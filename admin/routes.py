from flask import Blueprint, jsonify, request, session, render_template
from functools import wraps
import sqlite3
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def get_db_connection():
    """Établit une connexion à la base de données SQLite"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'db', 'geogestion.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par leur nom
    return conn

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return jsonify({"success": False, "error": "Non autorisé"}), 401
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/stats/gender', methods=['GET'])
@admin_required
def get_gender_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                CASE gender 
                    WHEN 'M' THEN 'Hommes'
                    WHEN 'F' THEN 'Femmes'
                    ELSE 'Non spécifié'
                END as gender,
                COUNT(*) as count
            FROM employees
            WHERE deleted_at IS NULL
            GROUP BY gender
            ORDER BY count DESC
        """)

        stats = [{'gender': row['gender'], 'count': row['count']} for row in cursor.fetchall()]

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@admin_bp.route('/stats/age', methods=['GET'])
@admin_required
def get_age_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            WITH age_groups AS (
                SELECT 
                    CASE 
                        WHEN (julianday('now') - julianday(birth_date))/365.25 < 25 THEN '18-24'
                        WHEN (julianday('now') - julianday(birth_date))/365.25 < 35 THEN '25-34'
                        WHEN (julianday('now') - julianday(birth_date))/365.25 < 45 THEN '35-44'
                        WHEN (julianday('now') - julianday(birth_date))/365.25 < 55 THEN '45-54'
                        ELSE '55+'
                    END as range,
                    COUNT(*) as count
                FROM employees
                WHERE deleted_at IS NULL AND birth_date IS NOT NULL
                GROUP BY range
                ORDER BY 
                    CASE range
                        WHEN '18-24' THEN 1
                        WHEN '25-34' THEN 2
                        WHEN '35-44' THEN 3
                        WHEN '45-54' THEN 4
                        ELSE 5
                    END
            )
            SELECT * FROM age_groups
        """)

        stats = [{'range': row['range'], 'count': row['count']} for row in cursor.fetchall()]

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@admin_bp.route('/stats/geo/<type>', methods=['GET'])
@admin_required
def get_geo_stats(type):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if type == 'region':
            query = """
                SELECT r.nom as name, COUNT(e.id) as count
                FROM regions r
                LEFT JOIN employees e ON r.id = e.region_id AND e.deleted_at IS NULL
                GROUP BY r.id, r.nom
                HAVING count > 0
                ORDER BY count DESC
            """
        elif type == 'departement':
            query = """
                SELECT d.nom as name, COUNT(e.id) as count
                FROM departements d
                LEFT JOIN employees e ON d.id = e.departement_id AND e.deleted_at IS NULL
                GROUP BY d.id, d.nom
                HAVING count > 0
                ORDER BY count DESC
            """
        else:  # sous_prefecture
            query = """
                SELECT sp.nom as name, COUNT(e.id) as count
                FROM sous_prefectures sp
                LEFT JOIN employees e ON sp.id = e.sous_prefecture_id AND e.deleted_at IS NULL
                GROUP BY sp.id, sp.nom
                HAVING count > 0
                ORDER BY count DESC
            """

        cursor.execute(query)
        stats = [{'name': row['name'], 'count': row['count']} for row in cursor.fetchall()]

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@admin_bp.route('/stats/positions', methods=['GET'])
@admin_required
def get_position_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT tp.fonction as position, COUNT(e.id) as count
            FROM type_poste tp
            LEFT JOIN employees e ON tp.id = e.poste_id AND e.deleted_at IS NULL
            GROUP BY tp.id, tp.fonction
            HAVING count > 0
            ORDER BY count DESC
        """)

        stats = [{'position': row['position'], 'count': row['count']} for row in cursor.fetchall()]

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@admin_bp.route('/stats/categories', methods=['GET'])
@admin_required
def get_category_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.categorie as category, COUNT(e.id) as count
            FROM contracts c
            JOIN employees e ON c.employee_id = e.id 
            WHERE e.deleted_at IS NULL AND c.deleted_at IS NULL
            GROUP BY c.categorie
            HAVING count > 0
            ORDER BY count DESC
        """)

        stats = [{'category': row['category'], 'count': row['count']} for row in cursor.fetchall()]

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@admin_bp.route('/stats/diplomas', methods=['GET'])
@admin_required
def get_diploma_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT d.nom as diploma, COUNT(e.id) as count
            FROM diplomes d
            LEFT JOIN employees e ON d.id = e.diplome_id AND e.deleted_at IS NULL
            GROUP BY d.id, d.nom
            HAVING count > 0
            ORDER BY count DESC
        """)

        stats = [{'diploma': row['diploma'], 'count': row['count']} for row in cursor.fetchall()]

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@admin_bp.route('/stats/general', methods=['GET'])
@admin_required
def get_general_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Total des employés
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM employees 
            WHERE deleted_at IS NULL
        """)
        total_employees = cursor.fetchone()['total']

        # Âge moyen
        cursor.execute("""
            SELECT AVG((julianday('now') - julianday(birth_date))/365.25) as avg_age
            FROM employees
            WHERE deleted_at IS NULL AND birth_date IS NOT NULL
        """)
        average_age = cursor.fetchone()['avg_age'] or 0

        # Ratio hommes/femmes
        cursor.execute("""
            SELECT gender, COUNT(*) as count
            FROM employees
            WHERE deleted_at IS NULL AND gender IS NOT NULL
            GROUP BY gender
        """)
        gender_counts = {row['gender']: row['count'] for row in cursor.fetchall()}
        total = sum(gender_counts.values())
        male_ratio = (gender_counts.get('M', 0) / total * 100) if total > 0 else 0

        # Ancienneté moyenne
        cursor.execute("""
            SELECT AVG((julianday('now') - julianday(created_at))/365.25) as avg_tenure
            FROM employees
            WHERE deleted_at IS NULL AND created_at IS NOT NULL
        """)
        average_tenure = cursor.fetchone()['avg_tenure'] or 0

        return jsonify({
            'success': True,
            'stats': {
                'total_employees': total_employees,
                'average_age': round(average_age, 1),
                'male_ratio': round(male_ratio, 1),
                'average_tenure': round(average_tenure, 1)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@admin_bp.route('/operators', methods=['GET'])
@admin_required
def get_operators():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT o.*, at.nom as actor_type_name 
            FROM operators o 
            LEFT JOIN acteurs_type at ON o.acteur_type_id = at.id 
            WHERE o.deleted_at IS NULL
        """)
        
        operators = [{
            'id': row['id'],
            'name': row['name'],
            'phone': row['phone1'],
            'email': row['email1'],
            'actor_type': row['actor_type_name']
        } for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'operators': operators
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@admin_bp.route('/actor-types', methods=['GET'])
@admin_required
def get_actor_types():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM acteurs_type 
            WHERE deleted_at IS NULL
            ORDER BY nom
        """)
        
        types = [{
            'id': row['id'],
            'name': row['nom'],
            'description': row['description']
        } for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'types': types
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@admin_bp.route('/projects', methods=['GET'])
@admin_required
def get_projects():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*, r.nom as region_name 
            FROM projects p
            LEFT JOIN regions r ON p.region_id = r.id
            WHERE p.deleted_at IS NULL
        """)
        
        projects = [{
            'id': row['id'],
            'name': row['nom'],
            'description': row['description'],
            'region': row['region_name']
        } for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'projects': projects
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@admin_bp.route('/schools', methods=['GET'])
@admin_required
def get_schools():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT e.*, r.nom as region_name 
            FROM ecoles e
            LEFT JOIN regions r ON e.region_id = r.id
            WHERE e.deleted_at IS NULL
        """)
        
        schools = [{
            'id': row['id'],
            'name': row['nom'],
            'region': row['region_name']
        } for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'schools': schools
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
