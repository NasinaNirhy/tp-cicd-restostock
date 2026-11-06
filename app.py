from datetime import datetime, timedelta
from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for
import json
import os

app = Flask(__name__)

CURRENT_VERSION = "2.0.0"

# Données enrichies pour Resto Manager
inventory = [
    {
        "id": 1,
        "name": "Poulet",
        "category": "Viandes",
        "quantity": 2,
        "unit": "kg",
        "price": 8.5,
        "min_threshold": 5,
        "expiry_date": "2026-06-10",
    },
    {
        "id": 2,
        "name": "Huile",
        "category": "Épicerie",
        "quantity": 1,
        "unit": "L",
        "price": 3.0,
        "min_threshold": 3,
        "expiry_date": "2027-01-01",
    },
    {
        "id": 3,
        "name": "Tomates",
        "category": "Légumes",
        "quantity": 10,
        "unit": "kg",
        "price": 2.5,
        "min_threshold": 4,
        "expiry_date": (datetime.now() + timedelta(days=1)).strftime(
            "%Y-%m-%d"
        ),  # Bientôt périmé (2 jours)
    },
    {
        "id": 4,
        "name": "Riz",
        "category": "Épicerie",
        "quantity": 25,
        "unit": "kg",
        "price": 1.8,
        "min_threshold": 10,
        "expiry_date": "2028-05-12",
    },
]

movements = [
    {
        "product": "Poulet",
        "type": "Sortie",
        "quantity": "-2 kg",
        "date": "2026-06-05 14:30",
    },
    {
        "product": "Riz",
        "type": "Entrée",
        "quantity": "+10 kg",
        "date": "2026-06-05 10:15",
    },
    {
        "product": "Huile",
        "type": "Sortie",
        "quantity": "-1 L",
        "date": "2026-06-04 18:00",
    },
]

suppliers = [
    {
        "name": "AgriViande Paris",
        "phone": "01 23 45 67 89",
        "address": "12 rue de la Rungis",
        "email": "contact@agriviande.fr",
    },
    {
        "name": "Metro Pro",
        "phone": "01 98 76 54 32",
        "address": "45 av. des Marchés",
        "email": "commandes@metro.fr",
    },
]

orders = [
    {
        "supplier": "AgriViande Paris",
        "items": "Poulet (20 kg)",
        "date": "2026-06-04",
        "status": "En attente",
        "delivery_date": "2026-06-08",
    }
]


@app.route("/", methods=["GET"])
def index():
  active_tab = request.args.get("tab", "dashboard")

  # Calculs pour le Dashboard
  total_products = len(inventory)
  total_stock_value = sum(item["quantity"] * item["price"] for item in inventory)

  low_stocks = [i for i in inventory if i["quantity"] <= i["min_threshold"]]

  # Gestion des péremptions (proche dans les 3 jours ou déjà dépassée)
  today = datetime.now().date()
  expiring_soon = []
  for item in inventory:
    if item["expiry_date"]:
      exp_date = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
      delta_days = (exp_date - today).days
      if 0 <= delta_days <= 3:
        expiring_soon.append({**item, "days_left": delta_days})

  return render_template(
      "index.html",
      active_tab=active_tab,
      inventory=inventory,
      movements=movements,
      suppliers=suppliers,
      orders=orders,
      total_products=total_products,
      total_stock_value=round(total_stock_value, 2),
      low_stocks=low_stocks,
      expiring_soon=expiring_soon,
      version=CURRENT_VERSION,
  )


# --- Routes obligatoires du TP ---
@app.route("/health", methods=["GET"])
def health_check():
  return jsonify({"status": "healthy"}), 200


@app.route("/version", methods=["GET"])
def version_check():
  return jsonify({"version": CURRENT_VERSION}), 200


# --- Fonctionnalités Métier ---
@app.route("/add_product", methods=["POST"])
def add_product():
  name = request.form.get("name")
  category = request.form.get("category")
  quantity = float(request.form.get("quantity", 0))
  unit = request.form.get("unit", "unité")
  price = float(request.form.get("price", 0))
  min_threshold = float(request.form.get("min_threshold", 5))
  expiry_date = request.form.get("expiry_date")

  new_id = max([i["id"] for i in inventory], default=0) + 1
  inventory.append({
      "id": new_id,
      "name": name,
      "category": category,
      "quantity": quantity,
      "unit": unit,
      "price": price,
      "min_threshold": min_threshold,
      "expiry_date": expiry_date,
  })

  # Enregistrement du mouvement automatique
  movements.insert(
      0,
      {
          "product": name,
          "type": "Création / Entrée",
          "quantity": f"+{quantity} {unit}",
          "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
      },
  )
  return redirect(url_for("index", tab="products"))


@app.route("/movement", methods=["POST"])
def register_movement():
  prod_name = request.form.get("product_name")
  m_type = request.form.get("type")  # Entrée, Sortie, Perte
  qty = float(request.form.get("quantity", 0))
  motif = request.form.get("motif", "")

  for item in inventory:
    if item["name"] == prod_name:
      if m_type == "Entrée":
        item["quantity"] += qty
        mov_str = f"+{qty} {item['unit']}"
      elif m_type in ["Sortie", "Perte"]:
        item["quantity"] = max(0, item["quantity"] - qty)
        mov_str = f"-{qty} {item['unit']} ({motif})" if motif else f"-{qty} {item['unit']}"
      
      movements.insert(
          0,
          {
              "product": prod_name,
              "type": m_type,
              "quantity": mov_str,
              "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
          },
      )
      break

  return redirect(url_for("index", tab="movements"))


@app.route("/backup", methods=["GET"])
def backup_data():
  backup_filename = "inventory_backup.json"
  data = {"inventory": inventory, "movements": movements, "suppliers": suppliers}
  with open(backup_filename, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
  return send_file(backup_filename, as_attachment=True)


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)