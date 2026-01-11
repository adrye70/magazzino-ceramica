from flask import Flask, render_template, request, redirect, session, send_file, url_for
import sqlite3
import pandas as pd
from functools import wraps

app = Flask(__name__)
app.secret_key = "chiave_super_segreta"
DB = "magazzino.db"

# -------------------------
# DATABASE
# -------------------------
def db_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# -------------------------
# LOGIN REQUIRED
# -------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated

# -------------------------
# LOGIN
# -------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = db_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM utenti WHERE username=? AND password=?",
            (username, password)
        )
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/dashboard")

    return render_template("login.html")

# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------------------------
# DASHBOARD
# -------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    conn = db_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM articoli")
    num_articoli = cur.fetchone()[0]

    cur.execute("SELECT SUM(quantita) FROM articoli")
    totale_pezzi = cur.fetchone()[0] or 0

    cur.execute("""
        SELECT tipo, SUM(quantita) as totale
        FROM movimenti
        GROUP BY tipo
    """)
    movimenti = cur.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        articoli=num_articoli,
        totale=totale_pezzi,
        movimenti=movimenti
    )

# -------------------------
# MAGAZZINO
# -------------------------
@app.route("/magazzino")
@login_required
def magazzino():
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM articoli")
    articoli = cur.fetchall()
    conn.close()
    return render_template("magazzino.html", articoli=articoli)

# -------------------------
# AGGIUNGI ARTICOLO
# -------------------------
@app.route("/articolo/add", methods=["POST"])
@login_required
def add_articolo():
    dati = (
        request.form["codice"],
        request.form["nome"],
        request.form["formato"],
        request.form["colore"]
    )

    conn = db_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO articoli (codice, nome, formato, colore, quantita)
        VALUES (?, ?, ?, ?, 0)
    """, dati)
    conn.commit()
    conn.close()

    return redirect("/magazzino")

# -------------------------
# CARICO / SCARICO
# -------------------------
@app.route("/movimento/<int:id>", methods=["GET", "POST"])
@login_required
def movimento(id):
    conn = db_conn()
    cur = conn.cursor()

    if request.method == "POST":
        tipo = request.form["tipo"]  # CARICO / SCARICO
        quantita = int(request.form["quantita"])

        if tipo == "SCARICO":
            quantita = -quantita

        cur.execute(
            "UPDATE articoli SET quantita = quantita + ? WHERE id = ?",
            (quantita, id)
        )

        cur.execute("""
            INSERT INTO movimenti (articolo_id, tipo, quantita)
            VALUES (?, ?, ?)
        """, (id, tipo, abs(quantita)))

        conn.commit()
        conn.close()
        return redirect("/magazzino")

    cur.execute("SELECT * FROM articoli WHERE id=?", (id,))
    articolo = cur.fetchone()
    conn.close()

    return render_template("movimento.html", articolo=articolo)

# -------------------------
# EXPORT EXCEL
# -------------------------
@app.route("/export")
@login_required
def export_excel():
    conn = db_conn()
    df = pd.read_sql_query("SELECT * FROM articoli", conn)
    conn.close()

    file = "magazzino.xlsx"
    df.to_excel(file, index=False)

    return send_file(file, as_attachment=True)

# -------------------------
# CANCELLA PRODOTTO
# -------------------------
@app.route("/articolo/delete/<int:id>", methods=["POST"])
@login_required
def delete_articolo(id):
    conn = db_conn()
    cur = conn.cursor()

    # (opzionale) controllo se esistono movimenti
    cur.execute("SELECT COUNT(*) FROM movimenti WHERE articolo_id = ?", (id,))
    movimenti = cur.fetchone()[0]

    if movimenti > 0:
        conn.close()
        return "Impossibile cancellare: articolo con movimenti registrati", 400

    cur.execute("DELETE FROM articoli WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect("/magazzino")


# -------------------------
# AVVIO
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
