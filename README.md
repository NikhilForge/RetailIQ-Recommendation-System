# 🛒 RetailIQ — Full-Stack Recommendation System

Association Rule Mining (Apriori) · FastAPI Backend · Vanilla JS Frontend

---

## 📁 Folder Structure

```
retail_recommender/
│
├── backend/
│   ├── main.py                  ← FastAPI application (all logic here)
│   ├── requirements.txt         ← Python dependencies
│   ├── export_rules.py          ← Helper: export rules from notebook to CSV
│   └── association_rules.csv    ← ⚠️ YOU MUST ADD THIS FILE (see Step 1)
│
└── frontend/
    └── index.html               ← Complete UI (open directly in browser)
```

---

## 🚀 Step-by-Step Setup

### Step 1 — Export your Association Rules CSV

In your Colab notebook, after **Step 7** (Generate Association Rules), run:

```python
# Add these TWO columns if they don't exist yet:
rules['antecedents_str'] = rules['antecedents'].apply(lambda x: ', '.join(sorted(x)))
rules['consequents_str'] = rules['consequents'].apply(lambda x: ', '.join(sorted(x)))

# Save to CSV
rules.to_csv("association_rules.csv", index=False)
print("✅ Saved!", rules.shape)
```

Then **download** `association_rules.csv` from Colab and place it at:
```
retail_recommender/backend/association_rules.csv
```

> **Note:** If the file is missing, the backend automatically uses 30 built-in demo rules so you can still test the app.

---

### Step 2 — Set Up Python Environment

```bash
# Navigate to the backend folder
cd retail_recommender/backend

# (Recommended) Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 3 — Start the FastAPI Server

```bash
# From inside retail_recommender/backend/
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

### Step 4 — Open the Frontend

Simply open the file in your browser:
```
retail_recommender/frontend/index.html
```

Double-click it, or right-click → "Open with" → your browser.

> The frontend calls `http://127.0.0.1:8000/recommend` automatically.

---

## 🧪 Test the API Manually

### Using the Interactive Docs (Swagger UI)
Open: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Using curl
```bash
curl -X POST "http://127.0.0.1:8000/recommend" \
     -H "Content-Type: application/json" \
     -d '{"items": ["Baked Bread/Buns/Rolls", "Cheese"]}'
```

### Expected Response
```json
{
  "recommendations": [
    {
      "product": "Soft Drinks",
      "confidence": 0.4263,
      "lift": 1.5029,
      "support": 0.095,
      "triggered_by": "Baked Bread/Buns/Rolls"
    },
    ...
  ],
  "message": "Found 5 recommendation(s) based on your basket."
}
```

---

## 📡 API Endpoints

| Method | Endpoint      | Description                        |
|--------|---------------|------------------------------------|
| GET    | `/`           | Health check                       |
| POST   | `/recommend`  | Get product recommendations        |
| GET    | `/products`   | List all available product names   |
| GET    | `/docs`       | Swagger interactive API docs       |

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| `Failed to fetch` in browser | Make sure the FastAPI server is running on port 8000 |
| `association_rules.csv not found` | Demo rules are used automatically — or add the file as described in Step 1 |
| CORS error in browser console | Already handled in `main.py` via `CORSMiddleware` |
| `ModuleNotFoundError: fastapi` | Run `pip install -r requirements.txt` |
| Port 8000 already in use | Run `uvicorn main:app --port 8001` and update `API_URL` in `index.html` |

---

## 📐 How the Recommendation Logic Works

```
Customer basket → [BAKED BREAD, EGGS]
       ↓
Scan all association rules
       ↓
Find rules where antecedents ⊆ basket items
  e.g.  BAKED BREAD → CHEESE  (lift=2.32, conf=0.38)
        BAKED BREAD → BEEF    (lift=2.23, conf=0.32)
        EGGS        → MILK    (lift=1.62, conf=0.39)
       ↓
Remove items already in basket
       ↓
Rank by LIFT (desc) → deduplicate → return top 5
```

**Lift > 1** = genuine positive association (not random)  
**Confidence** = reliability of the rule  
**Support** = how common the rule is across all transactions
