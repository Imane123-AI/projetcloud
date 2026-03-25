from flask import Flask, jsonify, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# ── Configuration base de données ─────────────────────────────
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'devops-master-dsbd-2026'

db = SQLAlchemy(app)

# ================================================================
# MODÈLES (Tables de la base de données)
# ================================================================

class Product(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    price       = db.Column(db.Float, nullable=False)
    stock       = db.Column(db.Integer, default=0)
    category    = db.Column(db.String(50))
    image_url   = db.Column(db.String(200))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'category': self.category,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat()
        }

class Order(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    customer    = db.Column(db.String(100), nullable=False)
    email       = db.Column(db.String(100), nullable=False)
    total       = db.Column(db.Float, nullable=False)
    status      = db.Column(db.String(20), default='pending')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    items       = db.relationship('OrderItem', backref='order', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'customer': self.customer,
            'email': self.email,
            'total': self.total,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    order_id   = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity   = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    product    = db.relationship('Product')

    def to_dict(self):
        return {
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'N/A',
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': self.quantity * self.unit_price
        }

# ================================================================
# INITIALISATION — Données de démonstration
# ================================================================

def seed_data():
    if Product.query.count() == 0:
        products = [
            Product(name="Laptop Pro X1",      price=12999.99, stock=15, category="Informatique",
                    description="Laptop haute performance Intel i9, 32GB RAM, 1TB SSD",
                    image_url="https://placehold.co/300x200/1a1a2e/ffffff?text=Laptop+Pro"),
            Product(name="Smartphone S24",     price=8499.99,  stock=30, category="Mobile",
                    description="Écran AMOLED 6.8\", 200MP, batterie 5000mAh",
                    image_url="https://placehold.co/300x200/16213e/ffffff?text=Smartphone"),
            Product(name="Casque Audio Pro",   price=1299.99,  stock=50, category="Audio",
                    description="Casque sans fil, réduction bruit active, 30h autonomie",
                    image_url="https://placehold.co/300x200/0f3460/ffffff?text=Casque"),
            Product(name="Tablette Tab Pro",   price=4999.99,  stock=20, category="Informatique",
                    description="Tablette 12.9\", puce M2, écran Liquid Retina",
                    image_url="https://placehold.co/300x200/533483/ffffff?text=Tablette"),
            Product(name="Montre Connectée",   price=2499.99,  stock=40, category="Wearable",
                    description="GPS intégré, suivi santé 24/7, étanche 50m",
                    image_url="https://placehold.co/300x200/e94560/ffffff?text=Montre"),
            Product(name="Clavier Mécanique",  price=899.99,   stock=25, category="Informatique",
                    description="Switch Cherry MX Red, RGB, layout FR",
                    image_url="https://placehold.co/300x200/1a1a2e/ffffff?text=Clavier"),
        ]
        db.session.add_all(products)
        db.session.commit()

# ================================================================
# ROUTES — Interface Web
# ================================================================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DevShop — E-Commerce DevOps</title>
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0a0a0f;
            --surface: #12121a;
            --card: #1a1a28;
            --accent: #e94560;
            --accent2: #533483;
            --text: #f0f0f5;
            --muted: #7a7a9a;
            --border: #2a2a3a;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: var(--bg);
            color: var(--text);
            font-family: 'DM Sans', sans-serif;
            min-height: 100vh;
        }
        /* ── Header ── */
        header {
            background: linear-gradient(135deg, var(--surface) 0%, #1a0a2e 100%);
            border-bottom: 1px solid var(--border);
            padding: 0 2rem;
            position: sticky; top: 0; z-index: 100;
            backdrop-filter: blur(10px);
        }
        .header-inner {
            max-width: 1200px; margin: 0 auto;
            display: flex; align-items: center;
            justify-content: space-between;
            height: 70px;
        }
        .logo {
            font-family: 'Syne', sans-serif;
            font-weight: 800; font-size: 1.6rem;
            background: linear-gradient(135deg, var(--accent), #ff8c69);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .logo span { color: var(--muted); -webkit-text-fill-color: var(--muted); font-weight: 400; font-size: 0.8rem; display: block; }
        nav a {
            color: var(--muted); text-decoration: none;
            margin-left: 2rem; font-size: 0.9rem;
            transition: color 0.2s;
        }
        nav a:hover { color: var(--accent); }
        /* ── Hero ── */
        .hero {
            background: linear-gradient(135deg, #0a0a0f 0%, #1a0a2e 50%, #0f1a3e 100%);
            padding: 5rem 2rem;
            text-align: center;
            position: relative; overflow: hidden;
        }
        .hero::before {
            content: '';
            position: absolute; inset: 0;
            background: radial-gradient(ellipse at 50% 50%, rgba(233,69,96,0.15) 0%, transparent 70%);
        }
        .hero h1 {
            font-family: 'Syne', sans-serif;
            font-size: clamp(2.5rem, 6vw, 5rem);
            font-weight: 800; line-height: 1.1;
            position: relative;
        }
        .hero h1 em {
            font-style: normal;
            background: linear-gradient(135deg, var(--accent), #ff8c69);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .hero p {
            color: var(--muted); margin-top: 1rem;
            font-size: 1.1rem; position: relative;
        }
        .badge {
            display: inline-block;
            background: rgba(233,69,96,0.15);
            border: 1px solid rgba(233,69,96,0.3);
            color: var(--accent);
            padding: 0.3rem 1rem; border-radius: 2rem;
            font-size: 0.8rem; margin-bottom: 1.5rem;
            position: relative;
        }
        /* ── Stats Bar ── */
        .stats-bar {
            background: var(--surface);
            border-top: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
            padding: 1.5rem 2rem;
        }
        .stats-inner {
            max-width: 1200px; margin: 0 auto;
            display: flex; gap: 3rem; justify-content: center;
            flex-wrap: wrap;
        }
        .stat { text-align: center; }
        .stat-value {
            font-family: 'Syne', sans-serif;
            font-size: 1.8rem; font-weight: 800;
            color: var(--accent);
        }
        .stat-label { color: var(--muted); font-size: 0.8rem; margin-top: 0.2rem; }
        /* ── Products ── */
        .section { max-width: 1200px; margin: 0 auto; padding: 3rem 2rem; }
        .section-title {
            font-family: 'Syne', sans-serif;
            font-size: 1.8rem; font-weight: 700;
            margin-bottom: 2rem;
            display: flex; align-items: center; gap: 1rem;
        }
        .section-title::after {
            content: ''; flex: 1; height: 1px;
            background: linear-gradient(90deg, var(--border), transparent);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.5rem;
        }
        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            transition: transform 0.3s, border-color 0.3s, box-shadow 0.3s;
        }
        .card:hover {
            transform: translateY(-6px);
            border-color: var(--accent);
            box-shadow: 0 20px 40px rgba(233,69,96,0.15);
        }
        .card-img {
            width: 100%; height: 180px;
            object-fit: cover; display: block;
        }
        .card-body { padding: 1.2rem; }
        .card-category {
            font-size: 0.7rem; text-transform: uppercase;
            letter-spacing: 0.1em; color: var(--accent);
            margin-bottom: 0.5rem;
        }
        .card-title {
            font-family: 'Syne', sans-serif;
            font-size: 1.1rem; font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .card-desc {
            color: var(--muted); font-size: 0.85rem;
            line-height: 1.5; margin-bottom: 1rem;
        }
        .card-footer {
            display: flex; align-items: center;
            justify-content: space-between;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
        }
        .price {
            font-family: 'Syne', sans-serif;
            font-size: 1.3rem; font-weight: 800;
            color: var(--accent);
        }
        .stock { color: var(--muted); font-size: 0.8rem; }
        .btn {
            background: linear-gradient(135deg, var(--accent), #c73652);
            color: white; border: none; padding: 0.5rem 1.2rem;
            border-radius: 8px; cursor: pointer;
            font-family: 'DM Sans', sans-serif;
            font-weight: 500; font-size: 0.85rem;
            transition: opacity 0.2s, transform 0.2s;
        }
        .btn:hover { opacity: 0.9; transform: scale(1.02); }
        /* ── API Docs ── */
        .api-section {
            background: var(--surface);
            border-top: 1px solid var(--border);
            padding: 3rem 2rem;
        }
        .api-inner { max-width: 1200px; margin: 0 auto; }
        .endpoints { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }
        .endpoint {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px; padding: 1rem;
        }
        .method {
            display: inline-block; padding: 0.2rem 0.6rem;
            border-radius: 4px; font-size: 0.75rem;
            font-weight: 700; margin-right: 0.5rem;
        }
        .get  { background: rgba(34,197,94,0.2);  color: #22c55e; }
        .post { background: rgba(59,130,246,0.2); color: #3b82f6; }
        .put  { background: rgba(234,179,8,0.2);  color: #eab308; }
        .del  { background: rgba(239,68,68,0.2);  color: #ef4444; }
        .route { font-family: monospace; font-size: 0.9rem; color: var(--text); }
        .ep-desc { color: var(--muted); font-size: 0.8rem; margin-top: 0.4rem; }
        /* ── Footer ── */
        footer {
            background: var(--surface);
            border-top: 1px solid var(--border);
            text-align: center; padding: 2rem;
            color: var(--muted); font-size: 0.85rem;
        }
        footer strong { color: var(--accent); }
        /* ── Animations ── */
        @keyframes fadeUp {
            from { opacity: 0; transform: translateY(20px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        .card { animation: fadeUp 0.5s ease both; }
        .card:nth-child(1) { animation-delay: 0.1s; }
        .card:nth-child(2) { animation-delay: 0.2s; }
        .card:nth-child(3) { animation-delay: 0.3s; }
        .card:nth-child(4) { animation-delay: 0.4s; }
        .card:nth-child(5) { animation-delay: 0.5s; }
        .card:nth-child(6) { animation-delay: 0.6s; }
    </style>
</head>
<body>

<header>
    <div class="header-inner">
        <div class="logo">DevShop <span>Projet DevOps — Master DSBD & IA</span></div>
        <nav>
            <a href="/">Accueil</a>
            <a href="/api/products">API</a>
            <a href="/health">Health</a>
        </nav>
    </div>
</header>

<section class="hero">
    <div class="badge">🚀 Déployé sur Kubernetes • CI/CD Jenkins</div>
    <h1>La boutique <em>tech</em><br>du futur</h1>
    <p>API REST complète — Flask + SQLite + Docker + Kubernetes</p>
</section>

<div class="stats-bar">
    <div class="stats-inner">
        <div class="stat">
            <div class="stat-value" id="total-products">—</div>
            <div class="stat-label">Produits</div>
        </div>
        <div class="stat">
            <div class="stat-value" id="total-orders">—</div>
            <div class="stat-label">Commandes</div>
        </div>
        <div class="stat">
            <div class="stat-value" id="total-revenue">—</div>
            <div class="stat-label">Chiffre d'affaires</div>
        </div>
        <div class="stat">
            <div class="stat-value">✅</div>
            <div class="stat-label">API Status</div>
        </div>
    </div>
</div>

<div class="section">
    <h2 class="section-title">Catalogue Produits</h2>
    <div class="grid" id="products-grid">
        <p style="color:var(--muted)">Chargement...</p>
    </div>
</div>

<div class="api-section">
    <div class="api-inner">
        <h2 class="section-title" style="font-family:Syne,sans-serif;font-size:1.8rem;font-weight:700;margin-bottom:2rem">
            Documentation API
        </h2>
        <div class="endpoints">
            <div class="endpoint">
                <span class="method get">GET</span><span class="route">/api/products</span>
                <p class="ep-desc">Liste tous les produits</p>
            </div>
            <div class="endpoint">
                <span class="method get">GET</span><span class="route">/api/products/&lt;id&gt;</span>
                <p class="ep-desc">Détail d'un produit</p>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span><span class="route">/api/products</span>
                <p class="ep-desc">Créer un produit</p>
            </div>
            <div class="endpoint">
                <span class="method put">PUT</span><span class="route">/api/products/&lt;id&gt;</span>
                <p class="ep-desc">Modifier un produit</p>
            </div>
            <div class="endpoint">
                <span class="method del">DELETE</span><span class="route">/api/products/&lt;id&gt;</span>
                <p class="ep-desc">Supprimer un produit</p>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span><span class="route">/api/orders</span>
                <p class="ep-desc">Passer une commande</p>
            </div>
            <div class="endpoint">
                <span class="method get">GET</span><span class="route">/api/orders</span>
                <p class="ep-desc">Liste toutes les commandes</p>
            </div>
            <div class="endpoint">
                <span class="method get">GET</span><span class="route">/api/stats</span>
                <p class="ep-desc">Statistiques du magasin</p>
            </div>
            <div class="endpoint">
                <span class="method get">GET</span><span class="route">/health</span>
                <p class="ep-desc">Health check Kubernetes</p>
            </div>
        </div>
    </div>
</div>

<footer>
    <strong>DevShop</strong> — Projet Final Master DSBD & IA •
    Flask + SQLAlchemy + Docker + Kubernetes + Jenkins CI/CD
</footer>

<script>
async function loadProducts() {
    const res  = await fetch('/api/products');
    const data = await res.json();
    const grid = document.getElementById('products-grid');
    grid.innerHTML = data.products.map(p => `
        <div class="card">
            <img class="card-img" src="${p.image_url}" alt="${p.name}">
            <div class="card-body">
                <div class="card-category">${p.category}</div>
                <div class="card-title">${p.name}</div>
                <div class="card-desc">${p.description}</div>
                <div class="card-footer">
                    <div>
                        <div class="price">${p.price.toLocaleString('fr-MA')} MAD</div>
                        <div class="stock">Stock : ${p.stock} unités</div>
                    </div>
                    <button class="btn">Commander</button>
                </div>
            </div>
        </div>
    `).join('');
}
async function loadStats() {
    const res  = await fetch('/api/stats');
    const data = await res.json();
    document.getElementById('total-products').textContent = data.total_products;
    document.getElementById('total-orders').textContent   = data.total_orders;
    document.getElementById('total-revenue').textContent  =
        data.total_revenue.toLocaleString('fr-MA') + ' MAD';
}
loadProducts();
loadStats();
</script>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# ================================================================
# ROUTES — API Produits
# ================================================================

@app.route('/api/products', methods=['GET'])
def get_products():
    category = request.args.get('category')
    query = Product.query
    if category:
        query = query.filter_by(category=category)
    products = query.all()
    return jsonify({
        "success": True,
        "total": len(products),
        "products": [p.to_dict() for p in products]
    })

@app.route('/api/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return jsonify({"success": True, "product": product.to_dict()})

@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('price'):
        return jsonify({"success": False, "error": "name et price requis"}), 400
    product = Product(
        name        = data['name'],
        description = data.get('description', ''),
        price       = data['price'],
        stock       = data.get('stock', 0),
        category    = data.get('category', 'Général'),
        image_url   = data.get('image_url', '')
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({"success": True, "product": product.to_dict()}), 201

@app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data    = request.get_json()
    if 'name'        in data: product.name        = data['name']
    if 'price'       in data: product.price       = data['price']
    if 'stock'       in data: product.stock       = data['stock']
    if 'description' in data: product.description = data['description']
    if 'category'    in data: product.category    = data['category']
    db.session.commit()
    return jsonify({"success": True, "product": product.to_dict()})

@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"success": True, "message": f"Produit {id} supprimé"})

# ================================================================
# ROUTES — API Commandes
# ================================================================

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data or not data.get('customer') or not data.get('items'):
        return jsonify({"success": False, "error": "customer et items requis"}), 400

    total = 0
    order_items = []

    for item in data['items']:
        product = Product.query.get(item['product_id'])
        if not product:
            return jsonify({"success": False, "error": f"Produit {item['product_id']} introuvable"}), 404
        if product.stock < item['quantity']:
            return jsonify({"success": False, "error": f"Stock insuffisant pour {product.name}"}), 400

        subtotal = product.price * item['quantity']
        total   += subtotal
        product.stock -= item['quantity']
        order_items.append(OrderItem(
            product_id = product.id,
            quantity   = item['quantity'],
            unit_price = product.price
        ))

    order = Order(
        customer = data['customer'],
        email    = data.get('email', ''),
        total    = round(total, 2),
        status   = 'confirmed'
    )
    db.session.add(order)
    db.session.flush()
    for item in order_items:
        item.order_id = order.id
        db.session.add(item)
    db.session.commit()
    return jsonify({"success": True, "order": order.to_dict()}), 201

@app.route('/api/orders', methods=['GET'])
def get_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify({"success": True, "total": len(orders), "orders": [o.to_dict() for o in orders]})

@app.route('/api/orders/<int:id>', methods=['GET'])
def get_order(id):
    order = Order.query.get_or_404(id)
    return jsonify({"success": True, "order": order.to_dict()})

# ================================================================
# ROUTES — Stats & Health
# ================================================================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_revenue = db.session.query(db.func.sum(Order.total)).scalar() or 0
    return jsonify({
        "success":        True,
        "total_products": Product.query.count(),
        "total_orders":   Order.query.count(),
        "total_revenue":  round(total_revenue, 2),
        "low_stock":      Product.query.filter(Product.stock < 5).count()
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200

@app.route('/api/info', methods=['GET'])
def info():
    return jsonify({
        "app":     "DevShop — E-Commerce API",
        "version": "2.0.0",
        "tech":    "Flask + SQLAlchemy + SQLite",
        "auteurs": "Master DSBD & IA 2026"
    })

# ================================================================
# LANCEMENT
# ================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(host='0.0.0.0', port=5000, debug=False)

