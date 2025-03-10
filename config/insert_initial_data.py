import sqlite3
import os
import sys
import uuid

# Ajouter le répertoire racine au PYTHONPATH
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from utils.logger import logger

def insert_initial_data():
    """Insère les données initiales dans la base de données SQLite"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'db', 'geogestion.db')
    
    operators_data = [
        {
            'name': 'CGEDS',
            'contact1': '(+225) 01 53 51 51 51',
            'contact2': None,
            'address1': 'BP 420 Grand Bassam',
            'address2': None,
            'email1': 'info@cgeds.com',
            'email2': None,
            'password': 'AFOR'
        },
        {
            'name': 'GROUPEMENT TVC ET CGE-SOTTI',
            'contact1': '(+41) 78 60 30 01 8',
            'contact2': '07 77 00 37 47',
            'address1': None,
            'address2': None,
            'email1': None,
            'email2': None,
            'password': 'AFOR'
        },
        {
            'name': 'CABINET TOPO BENHIBA',
            'contact1': '(+212) 05 37 36 40 69',
            'contact2': None,
            'address1': 'Résidence Paris N°7',
            'address2': 'B - KENITRA-MAROC',
            'email1': None,
            'email2': None,
            'password': 'AFOR'
        },
        {
            'name': 'GROUPEMENT GEOART / SETOM / CGEKA',
            'contact1': '+212 (0) 537 53 45 61',
            'contact2': None,
            'address1': None,
            'address2': None,
            'email1': 'tariqcouzi@gmail.com',
            'email2': None,
            'password': 'AFOR'
        },
        {
            'name': 'GROUPEMENT ALLIANCE IVOIRIENNE CITRAT/CGE SAKO/CDGE C. DOHOULOU/CGET/IVOIRE GEO AGRO',
            'contact1': '(+225) 0709804927',
            'contact2': '707905332',
            'address1': '06 BP 6070 Abidjan 06',
            'address2': None,
            'email1': 'sako.brahima@cabinetsako.com',
            'email2': 'info@citrat.ci',
            'password': 'AFOR'
        },
        {
            'name': 'GROUPEMENT ETAFAT-CGEA 2TF',
            'contact1': '(+212) 5 22 79 87 00/01',
            'contact2': None,
            'address1': 'Lotissement Salaj - Ain Diab 20180 Casablanca - Maroc',
            'address2': None,
            'email1': None,
            'email2': None,
            'password': 'AFOR'
        },
        {
            'name': 'GROUPEMENT AVICENNE CONSULT/ GROUPE DE GEOMATIQUE AZIMUT TERRABO INGENIEUR CONSEIL / CABINET DE GEOMETRE EXPERT /AKMEL YEDAGNE (GE-2ATY)',
            'contact1': '(+225) 05 05 26 24 42',
            'contact2': None,
            'address1': 'Menontin, Rue 9.281-Lot N° 2932',
            'address2': None,
            'email1': 'koneamed01@gmail.com',
            'email2': None,
            'password': 'AFOR'
        },
        {
            'name': 'GROUPEMENT CAG',
            'contact1': '225 01 40 00 06',
            'contact2': None,
            'address1': '21 BP 4380 Abidjan 21',
            'address2': None,
            'email1': 'Soro.nangaz@geometre',
            'email2': None,
            'password': 'AFOR'
        }
    ]

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insérer les opérateurs
        for operator in operators_data:
            cursor.execute("""
                INSERT INTO operators (
                    id, name, contact1, contact2, address1, address2,
                    email1, email2, password
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                str(uuid.uuid4()),
                operator['name'],
                operator['contact1'],
                operator['contact2'],
                operator['address1'],
                operator['address2'],
                operator['email1'],
                operator['email2'],
                operator['password']
            ))

        # Valider les changements
        conn.commit()
        logger.info(f"Données initiales insérées avec succès ({len(operators_data)} opérateurs)")
        
        # Vérifier les données insérées
        cursor.execute("SELECT COUNT(*) FROM operators")
        count = cursor.fetchone()[0]
        logger.info(f"Nombre total d'opérateurs dans la base : {count}")

        return True

    except Exception as e:
        logger.error(f"Erreur lors de l'insertion des données : {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    insert_initial_data()
