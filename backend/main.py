# ============================================================
# RETAIL RECOMMENDATION SYSTEM — FINAL PRODUCTION BACKEND
# ============================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import pandas as pd
import os
import ast

# ── App Setup ────────────────────────────────────────────────
app = FastAPI(
    title="Retail Recommendation API",
    description="Apriori-based recommender system",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE = os.path.dirname(__file__)

# ── SAFE PARSER (handles all CSV formats) ─────────────────────
def safe_parse_itemset(x):
    if pd.isna(x):
        return set()

    x = str(x).strip()

    # Case 1: simple comma-separated
    if "," in x and "{" not in x and "[" not in x:
        return set(i.strip().upper() for i in x.split(","))

    # Case 2: try Python parsing
    try:
        return set(ast.literal_eval(x))
    except:
        pass

    # Case 3: fallback cleaning
    x = x.replace("{", "").replace("}", "").replace("[", "").replace("]", "")
    return set(i.strip().upper() for i in x.split(",") if i.strip())


# ── Load Rules CSV ───────────────────────────────────────────
def load_rules_csv(filename):
    path = os.path.join(BASE, filename)
    if not os.path.exists(path):
        return None

    df = pd.read_csv(path)

    if "antecedents_str" in df.columns:
        df["antecedents_str"] = df["antecedents_str"].str.upper().str.strip()
        df["consequents_str"] = df["consequents_str"].str.upper().str.strip()
    else:
        df["antecedents"] = df["antecedents"].apply(safe_parse_itemset)
        df["consequents"] = df["consequents"].apply(safe_parse_itemset)

        df["antecedents_str"] = df["antecedents"].apply(lambda x: ", ".join(sorted(x)))
        df["consequents_str"] = df["consequents"].apply(lambda x: ", ".join(sorted(x)))

    return df


print("Loading CSVs...")

# ── Load association rules ───────────────────────────────────
rules_df = load_rules_csv("association_rules.csv")
if rules_df is not None:
    print(f"✅ association_rules.csv → {len(rules_df)} rules")
else:
    rules_df = pd.DataFrame(columns=["antecedents_str","consequents_str","support","confidence","lift"])

# ── Load strong rules ────────────────────────────────────────
strong_df = load_rules_csv("strong_association_rules.csv")
if strong_df is not None:
    print(f"✅ strong_association_rules.csv → {len(strong_df)} rules")
else:
    print("⚠️ deriving strong rules")
    strong_df = rules_df[
        (rules_df["confidence"] > 0.5) & (rules_df["lift"] > 1)
    ].copy()

# ── Load frequent itemsets ───────────────────────────────────
freq_path = os.path.join(BASE, "frequent_itemsets.csv")

if os.path.exists(freq_path):
    freq_df = pd.read_csv(freq_path)

    if "itemsets_str" not in freq_df.columns:
        freq_df["itemsets"] = freq_df["itemsets"].apply(safe_parse_itemset)
        freq_df["itemsets_str"] = freq_df["itemsets"].apply(
            lambda x: ", ".join(sorted(x))
        )
    else:
        freq_df["itemsets_str"] = freq_df["itemsets_str"].str.upper().str.strip()

    print(f"✅ frequent_itemsets.csv → {len(freq_df)} itemsets")
else:
    freq_df = pd.DataFrame(columns=["support","itemsets_str","itemset_length"])

print("🚀 Backend Ready!\n")


# ── Models ───────────────────────────────────────────────────
class RecommendRequest(BaseModel):
    items: List[str]
    use_strong_only: bool = False


class RecommendResponse(BaseModel):
    recommendations: List[dict]
    message: str
    rule_type: str


# ── Fuzzy Matching ───────────────────────────────────────────
def fuzzy_match(user_item, rule_item):
    u = user_item.upper().strip()
    r = rule_item.upper().strip()

    if u == r:
        return True
    if len(u) >= 3 and u in r:
        return True
    if len(r) >= 3 and r in u:
        return True

    return bool(set(u.split()) & set(r.split()))


# ── Recommendation Logic ─────────────────────────────────────
def get_recommendations(purchased_items, source_df, top_n=5):
    if source_df.empty:
        return []

    purchased = [i.upper().strip() for i in purchased_items]
    results = {}

    for _, row in source_df.iterrows():

        antecedents = [a.strip() for a in row["antecedents_str"].split(",")]

        if not all(any(fuzzy_match(u, ant) for u in purchased) for ant in antecedents):
            continue

        for product in row["consequents_str"].split(","):
            product = product.strip()

            if any(fuzzy_match(u, product) for u in purchased):
                continue

            if product not in results or row["lift"] > results[product]["lift"]:
                results[product] = {
                    "product": product.title(),
                    "confidence": round(float(row["confidence"]), 4),
                    "lift": round(float(row["lift"]), 4),
                    "support": round(float(row["support"]), 4),
                    "triggered_by": ", ".join(antecedents).title()
                }

    return sorted(
        results.values(),
        key=lambda x: (x["lift"], x["confidence"]),
        reverse=True
    )[:top_n]


# ── Popular fallback ─────────────────────────────────────────
def get_popular_products(exclude_items, top_n=5):
    from collections import Counter
    counter = Counter()

    source = strong_df if not strong_df.empty else rules_df

    for _, row in source.iterrows():
        for p in row["consequents_str"].split(","):
            p = p.strip()

            if not any(fuzzy_match(u, p) for u in exclude_items):
                counter[p] += float(row["support"])

    return [
        {
            "product": p.title(),
            "confidence": None,
            "lift": None,
            "support": round(score, 4),
            "triggered_by": "Popular items"
        }
        for p, score in counter.most_common(top_n)
    ]


# ── API Endpoints ────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "status": "ok",
        "rules": len(rules_df),
        "strong_rules": len(strong_df),
        "itemsets": len(freq_df),
        "docs": "/docs"
    }


@app.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest):

    if not request.items:
        raise HTTPException(400, "Items required")

    items = [i.strip() for i in request.items if i.strip()]

    # Tier 1
    recs = get_recommendations(items, strong_df)
    if recs:
        return {"recommendations": recs, "message": "Strong rules used", "rule_type": "strong"}

    # Tier 2
    recs = get_recommendations(items, rules_df)
    if recs:
        return {"recommendations": recs, "message": "All rules used", "rule_type": "all"}

    # Tier 3
    recs = get_popular_products(items)
    return {"recommendations": recs, "message": "Fallback popular items", "rule_type": "popular"}


# ── Run Server (LOCAL + RENDER) ──────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)