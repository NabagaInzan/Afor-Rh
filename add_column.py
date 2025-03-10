import sqlite3
import os

# Assurez-vous que le répertoire data/db existe
os.makedirs('data/db', exist_ok=True)

conn = sqlite3.connect('data/db/geogestion.db')
cursor = conn.cursor()

# Ajouter la colonne additional_terms
try:
    cursor.execute('''
        ALTER TABLE contracts
        ADD COLUMN additional_terms TEXT
    ''')
    print("Colonne additional_terms ajoutée avec succès")
except Exception as e:
    print(f"Erreur lors de l'ajout de la colonne: {str(e)}")

conn.commit()
conn.close()
