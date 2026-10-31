from flask import Flask, request, redirect, render_template_string
import sqlite3

app = Flask(__name__)

# --- BASE DE DONNEES ---
def get_db():
    conn = sqlite3.connect("stock.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT,
        categorie TEXT,
        prix REAL,
        quantite INTEGER,
        seuil INTEGER
    )
    """)
    conn.commit()
    conn.close()

init_db()

# --- PAGE HTML (PC + TELEPHONE) ---
HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ma Boutique - Stock</title>
<style>
body{font-family:Arial; background:#f2f2f2; padding:10px; margin:0}
h1{text-align:center; color:#2c3e50}
.box{background:white; padding:15px; border-radius:12px; margin-bottom:15px; box-shadow:0 2px 5px #ccc}
input, select{width:100%; padding:12px; margin:5px 0; border:1px solid #ddd; border-radius:8px; font-size:16px; box-sizing:border-box}
button{width:100%; padding:13px; border:none; border-radius:8px; font-size:16px; font-weight:bold; cursor:pointer; margin-top:5px}
.btn-add{background:#27ae60; color:white}
.btn-in{background:#2980b9; color:white}
.btn-out{background:#e67e22; color:white}
.btn-del{background:#e74c3c; color:white}
table{width:100%; border-collapse:collapse; background:white; border-radius:12px; overflow:hidden}
th,td{padding:10px; text-align:left; border-bottom:1px solid #eee; font-size:14px}
.alerte{background:#ffdddd !important; color:red; font-weight:bold}
.total{text-align:center; font-size:20px; font-weight:bold; background:#2c3e50; color:white; padding:15px; border-radius:12px}
.search{display:flex; gap:5px}
.search input{flex:1}
.search button{width:auto; padding:12px 15px; background:#333; color:white}
</style>
</head>
<body>
<h1>📦 MA BOUTIQUE - STOCK</h1>

<div class="total">💰 Valeur totale : {{ total }} FCFA</div><br>

<div class="box">
<h3>🔍 Rechercher</h3>
<form action="/" method="get" class="search">
<input type="text" name="q" placeholder="Ex: Riz, Savon..." value="{{ q }}">
<button>🔍</button>
</form>
</div>

<div class="box">
<h3>➕ Ajouter un produit</h3>
<form action="/ajouter" method="post">
<input name="nom" placeholder="Nom du produit (Ex: Riz 25kg)" required>
<input name="categorie" placeholder="Catégorie (Ex: Alimentation)">
<input name="prix" type="number" placeholder="Prix en FCFA" required>
<input name="quantite" type="number" placeholder="Quantité de départ" required>
<input name="seuil" type="number" placeholder="Seuil alerte (Ex: 5)" value="5">
<button class="btn-add">AJOUTER AU STOCK</button>
</form>
</div>

{% for p in produits %}
<div class="box {% if p['quantite'] <= p['seuil'] %}alerte{% endif %}">
<b style="font-size:18px">{{ p['nom'] }}</b> - {{ p['categorie'] }}<br>
Prix : <b>{{ p['prix'] }} FCFA</b> | Quantité : <b>{{ p['quantite'] }}</b> | Seuil : {{ p['seuil'] }}<br>
Valeur : {{ p['prix'] * p['quantite'] }} FCFA<br>
{% if p['quantite'] <= p['seuil'] %}⚠️ STOCK BAS ! IL FAUT COMMANDER<br>{% endif %}

<form action="/mouvement" method="post" style="display:flex; gap:5px; margin-top:10px">
<input type="hidden" name="id" value="{{ p['id'] }}">
<input name="nb" type="number" placeholder="Qté" required style="flex:1">
<button class="btn-in" name="sens" value="1" style="flex:1">📥 ENTRÉE</button>
<button class="btn-out" name="sens" value="-1" style="flex:1">📤 SORTIE</button>
</form>
<form action="/supprimer" method="post">
<input type="hidden" name="id" value="{{ p['id'] }}">
<button class="btn-del">🗑️ SUPPRIMER</button>
</form>
</div>
{% endfor %}

</body>
</html>
"""

@app.route("/")
def index():
    q = request.args.get("q", "")
    conn = get_db()
    if q:
        produits = conn.execute("SELECT * FROM produits WHERE nom LIKE ? OR categorie LIKE ?", (f"%{q}%", f"%{q}%")).fetchall()
    else:
        produits = conn.execute("SELECT * FROM produits ORDER BY id DESC").fetchall()
    total = sum([p['prix'] * p['quantite'] for p in produits])
    conn.close()
    return render_template_string(HTML, produits=produits, total=total, q=q)

@app.route("/ajouter", methods=["POST"])
def ajouter():
    conn = get_db()
    conn.execute("INSERT INTO produits (nom, categorie, prix, quantite, seuil) VALUES (?,?,?,?,?)",
                 (request.form['nom'], request.form['categorie'], float(request.form['prix']), int(request.form['quantite']), int(request.form['seuil'])))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/mouvement", methods=["POST"])
def mouvement():
    id_ = request.form['id']
    nb = int(request.form['nb']) * int(request.form['sens'])
    conn = get_db()
    p = conn.execute("SELECT quantite FROM produits WHERE id=?", (id_,)).fetchone()
    nouvelle = p['quantite'] + nb
    if nouvelle < 0:
        nouvelle = 0
    conn.execute("UPDATE produits SET quantite=? WHERE id=?", (nouvelle, id_))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/supprimer", methods=["POST"])
def supprimer():
    conn = get_db()
    conn.execute("DELETE FROM produits WHERE id=?", (request.form['id'],))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    # host 0.0.0.0 = accessible depuis le téléphone sur le même WiFi
    app.run(host="0.0.0.0", port=5000, debug=True)