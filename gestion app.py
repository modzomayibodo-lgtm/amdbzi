import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

# ---------- BASE DE DONNEES ----------
conn = sqlite3.connect("stock.db")
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS produits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    categorie TEXT,
    prix REAL,
    quantite INTEGER,
    seuil INTEGER
)
""")
conn.commit()

# ---------- FONCTIONS ----------
def afficher():
    for row in tree.get_children():
        tree.delete(row)
    cur.execute("SELECT * FROM produits")
    total_valeur = 0
    for p in cur.fetchall():
        id_, nom, cat, prix, qte, seuil = p
        valeur = prix * qte
        total_valeur += valeur
        # Couleur si stock bas
        tag = "alerte" if qte <= seuil else "normal"
        tree.insert("", "end", values=(id_, nom, cat, f"{prix:.0f} FCFA", qte, seuil, f"{valeur:.0f} FCFA"), tags=(tag,))
    tree.tag_configure("alerte", background="#ffcccc")
    tree.tag_configure("normal", background="white")
    lbl_total.config(text=f"Valeur totale du stock : {total_valeur:.0f} FCFA")

def ajouter():
    nom = e_nom.get().strip()
    if not nom:
        messagebox.showwarning("Erreur", "Entre le nom du produit")
        return
    try:
        prix = float(e_prix.get() or 0)
        qte = int(e_qte.get() or 0)
        seuil = int(e_seuil.get() or 5)
    except ValueError:
        messagebox.showerror("Erreur", "Prix / Quantité / Seuil doivent être des nombres")
        return
    cur.execute("INSERT INTO produits (nom, categorie, prix, quantite, seuil) VALUES (?,?,?,?,?)",
                (nom, e_cat.get(), prix, qte, seuil))
    conn.commit()
    effacer_champs()
    afficher()

def selection(event=None):
    sel = tree.selection()
    if not sel:
        return
    vals = tree.item(sel[0])["values"]
    e_nom.delete(0, "end"); e_nom.insert(0, vals[1])
    e_cat.delete(0, "end"); e_cat.insert(0, vals[2])
    e_prix.delete(0, "end"); e_prix.insert(0, str(vals[3]).replace(" FCFA",""))
    e_qte.delete(0, "end"); e_qte.insert(0, vals[4])
    e_seuil.delete(0, "end"); e_seuil.insert(0, vals[5])

def modifier():
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Erreur", "Sélectionne un produit d'abord")
        return
    id_ = tree.item(sel[0])["values"][0]
    cur.execute("UPDATE produits SET nom=?, categorie=?, prix=?, quantite=?, seuil=? WHERE id=?",
                (e_nom.get(), e_cat.get(), float(e_prix.get()), int(e_qte.get()), int(e_seuil.get()), id_))
    conn.commit()
    afficher()

def supprimer():
    sel = tree.selection()
    if not sel:
        return
    if messagebox.askyesno("Confirmer", "Supprimer ce produit ?"):
        id_ = tree.item(sel[0])["values"][0]
        cur.execute("DELETE FROM produits WHERE id=?", (id_,))
        conn.commit()
        afficher()

def entree_sortie(sens):
    # sens = +1 pour Entrée, -1 pour Sortie
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Erreur", "Sélectionne un produit")
        return
    id_ = tree.item(sel[0])["values"][0]
    cur.execute("SELECT quantite FROM produits WHERE id=?", (id_,))
    qte_actuelle = cur.fetchone()[0]
    try:
        nb = int(e_mouvement.get())
    except:
        messagebox.showerror("Erreur", "Entre une quantité pour le mouvement")
        return
    nouvelle = qte_actuelle + (nb * sens)
    if nouvelle < 0:
        messagebox.showerror("Erreur", "Stock insuffisant !")
        return
    cur.execute("UPDATE produits SET quantite=? WHERE id=?", (nouvelle, id_))
    conn.commit()
    afficher()

def rechercher():
    mot = e_search.get().strip()
    for row in tree.get_children():
        tree.delete(row)
    cur.execute("SELECT * FROM produits WHERE nom LIKE ? OR categorie LIKE ?", (f"%{mot}%", f"%{mot}%"))
    for p in cur.fetchall():
        tree.insert("", "end", values=(p[0], p[1], p[2], f"{p[3]:.0f} FCFA", p[4], p[5], f"{p[3]*p[4]:.0f} FCFA"))

def effacer_champs():
    for e in [e_nom, e_cat, e_prix, e_qte, e_seuil]:
        e.delete(0, "end")

# ---------- INTERFACE ----------
root = tk.Tk()
root.title("Gestion de Stock - Ma Boutique")
root.geometry("900x550")

# Formulaire
frame = tk.Frame(root, pady=10)
frame.pack()

tk.Label(frame, text="Nom:").grid(row=0, column=0)
e_nom = tk.Entry(frame, width=20); e_nom.grid(row=0, column=1, padx=5)

tk.Label(frame, text="Catégorie:").grid(row=0, column=2)
e_cat = tk.Entry(frame, width=15); e_cat.grid(row=0, column=3, padx=5)

tk.Label(frame, text="Prix (FCFA):").grid(row=1, column=0, pady=5)
e_prix = tk.Entry(frame, width=20); e_prix.grid(row=1, column=1)

tk.Label(frame, text="Quantité:").grid(row=1, column=2)
e_qte = tk.Entry(frame, width=15); e_qte.grid(row=1, column=3)

tk.Label(frame, text="Seuil alerte:").grid(row=2, column=0)
e_seuil = tk.Entry(frame, width=20); e_seuil.insert(0, "5"); e_seuil.grid(row=2, column=1)

# Boutons
btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)
tk.Button(btn_frame, text="➕ Ajouter", bg="#4CAF50", fg="white", command=ajouter).pack(side="left", padx=5)
tk.Button(btn_frame, text="✏️ Modifier", bg="#2196F3", fg="white", command=modifier).pack(side="left", padx=5)
tk.Button(btn_frame, text="🗑️ Supprimer", bg="#f44336", fg="white", command=supprimer).pack(side="left", padx=5)

# Mouvement de stock
tk.Label(root, text="Mouvement de stock (Entrée / Sortie) :").pack()
mouv_frame = tk.Frame(root)
mouv_frame.pack()
e_mouvement = tk.Entry(mouv_frame, width=10); e_mouvement.pack(side="left", padx=5)
tk.Button(mouv_frame, text="📥 ENTRÉE +", command=lambda: entree_sortie(1)).pack(side="left", padx=5)
tk.Button(mouv_frame, text="📤 SORTIE -", command=lambda: entree_sortie(-1)).pack(side="left", padx=5)

# Recherche
search_frame = tk.Frame(root)
search_frame.pack(pady=10)
tk.Label(search_frame, text="🔍 Rechercher :").pack(side="left")
e_search = tk.Entry(search_frame, width=30); e_search.pack(side="left", padx=5)
tk.Button(search_frame, text="Chercher", command=rechercher).pack(side="left")
tk.Button(search_frame, text="Tout afficher", command=afficher).pack(side="left", padx=5)

# Tableau
cols = ("ID", "Nom", "Catégorie", "Prix", "Qté", "Seuil", "Valeur")
tree = ttk.Treeview(root, columns=cols, show="headings")
for c in cols:
    tree.heading(c, text=c)
    tree.column(c, width=120)
tree.pack(fill="both", expand=True, padx=10)
tree.bind("<<TreeviewSelect>>", selection)

lbl_total = tk.Label(root, text="Valeur totale du stock : 0 FCFA", font=("Arial", 12, "bold"))
lbl_total.pack(pady=10)

afficher()
root.mainloop()