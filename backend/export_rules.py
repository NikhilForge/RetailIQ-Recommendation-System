# ============================================================
# export_rules.py
# Run this ONCE inside your Colab notebook (or locally)
# after Step 7 to save the rules to a CSV file.
# ============================================================
# Paste and run this cell AFTER Step 7 in your notebook:
#
#   rules.to_csv("association_rules.csv", index=False)
#   print("✅ association_rules.csv saved!")
#
# Then copy association_rules.csv into:
#   retail_recommender/backend/association_rules.csv
#
# The required columns are:
#   antecedents_str  |  consequents_str  |  support  |  confidence  |  lift
# ============================================================

import pandas as pd

# If running locally with your existing rules DataFrame:
# rules.to_csv("association_rules.csv", index=False)

# Verify the saved file looks correct:
df = pd.read_csv("association_rules.csv")
print(f"Rows : {len(df)}")
print(f"Columns: {list(df.columns)}")
print(df.head(3))
