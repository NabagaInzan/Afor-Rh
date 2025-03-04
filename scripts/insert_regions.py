import sqlite3
import os
import uuid
from datetime import datetime

def get_db_connection():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'db', 'geogestion.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def insert_regions():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Lire les régions depuis le fichier
    regions_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'TXT.TXT')
    with open(regions_file, 'r', encoding='utf-8') as f:
        regions = [line.strip() for line in f.readlines() if line.strip()]
    
    # Insérer chaque région
    for region in regions:
        region_id = str(uuid.uuid4())
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            cursor.execute("""
                INSERT INTO regions (id, nom, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                nom = excluded.nom,
                updated_at = ?
            """, (region_id, region, now, now))
        except sqlite3.IntegrityError:
            print(f"La région {region} existe déjà")
    
    conn.commit()
    conn.close()
    print("Régions insérées avec succès")

if __name__ == '__main__':
    insert_regions()
