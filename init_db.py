import sqlite3

conn = sqlite3.connect("magazzino.db")
cur = conn.cursor()

# UTENTI
cur.execute("""
CREATE TABLE utenti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# ARTICOLI
cur.execute("""
CREATE TABLE articoli (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codice TEXT,
    nome TEXT,
    formato TEXT,
    colore TEXT,
    quantita INTEGER DEFAULT 0
)
""")

# MOVIMENTI
cur.execute("""
CREATE TABLE movimenti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    articolo_id INTEGER,
    tipo TEXT,
    quantita INTEGER,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (articolo_id) REFERENCES articoli(id)
)
""")

# UTENTE ADMIN DI DEFAULT
cur.execute("INSERT INTO utenti VALUES (NULL, 'admin', 'admin')")

conn.commit()
conn.close()

print("Database creato con successo")
