# 🛒 Price Tracker – Smart E-commerce Price Comparison

A hackathon-ready full-stack web application to compare product prices across multiple e-commerce platforms, track price history, and get alerts when prices drop.

Built using **Flask (Python)** and **Vanilla JavaScript** with a fast setup and demo-safe fallback system.

---

## 🚀 What It Does

* 🔍 Compare prices from **Amazon & Flipkart** (demo fallback for others)
* 💖 Create wishlists with **target price alerts**
* 📈 Track price trends & savings
* 👤 Secure login using JWT authentication
* 📊 Dashboard with basic analytics

---

## 🏗️ Tech Stack

* **Backend:** Flask, SQLAlchemy, JWT
* **Frontend:** HTML, CSS, Vanilla JS
* **Database:** SQLite
* **Scraping:** BeautifulSoup, Cloudscraper
* **API:** REST + CORS

---

## ⚡ How to Run (For Judges)

### 1️⃣ Prerequisites

* Python **3.8+**
* pip

### 2️⃣ Clone Repository

```bash
git clone <repository-url>
cd "Price comparison"
```

### 3️⃣ Setup Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\Activate

# Mac/Linux
source .venv/bin/activate
```

### 4️⃣ Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 5️⃣ Initialize Database (One-Time)

```bash
python -c "
from backend.app import db, create_app
app = create_app()
with app.app_context():
    db.create_all()
    print('Database initialized')
"
```

### 6️⃣ Run the Application

```bash
python backend/app.py
```

Open in browser:

```
http://localhost:5000
```

---

## 🌐 Important Pages

* Dashboard → `/`
* Product Search → `/product_search.html`
* Wishlist → `/wishlist.html`
* Login/Register → `/auth.html`
* API Health → `/api/health`

---

## 🧪 Demo Credentials

| Role  | Email                                         | Password    |
| ----- | --------------------------------------------- | ----------- |
| Admin | [admin@example.com](mailto:admin@example.com) | admin123    |
| User  | [test@example.com](mailto:test@example.com)   | password123 |

---

## 📝 Notes for Judges

* Database & admin account auto-created on first run
* Scraping respects rate limits
* Demo data used if live scraping fails
* No API keys required

---

## 👨‍💻 Developer

**Raga Sindhu**

🏆 *Hackathon Submission 2026*

Happy Price Tracking! 🎯
