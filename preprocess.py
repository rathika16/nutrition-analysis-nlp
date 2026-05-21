import pandas as pd
import re

# =========================
# LOAD DATASETS
# =========================

ifct = pd.read_csv(
    "data/ifct2017_compositions.csv",
    low_memory=False
)

food = pd.read_csv(
    "data/food.csv",
    low_memory=False
)

food_nutrient = pd.read_csv(
    "data/food_nutrient.csv",
    low_memory=False
)

existing = pd.read_csv(
    "data/nutrition_final.csv"
)

# =========================
# USDA NUTRIENT IDS
# =========================

NUTRIENT_MAP = {
    1008: "calories",
    1003: "protein",
    1004: "fat",
    1005: "carbs"
}

# =========================
# CLEAN FOOD FUNCTION
# =========================

def clean_food(text):

    text = str(text).lower().strip()

    text = re.sub(r"\([^)]*\)", "", text)

    text = text.replace("-", " ")
    text = text.replace("/", " ")

    text = re.sub(r"[^a-zA-Z ]", " ", text)

    remove_words = [

        "raw",
        "cooked",
        "boiled",
        "fried",
        "chopped",
        "fresh",
        "without salt",
        "with salt",
        "steamed",
        "baked",
        "roasted",
        "boneless",
        "skinless",
        "lean",
        "only",
        "paste",
        "powder"

    ]

    for word in remove_words:
        text = text.replace(word, "")

    text = re.sub(r"\s+", " ", text)

    return text.strip()

# =========================
# USDA PROCESSING
# =========================

food = food[[
    "fdc_id",
    "description"
]]

food.columns = [
    "fdc_id",
    "food"
]

food["food"] = food["food"].apply(clean_food)

food_nutrient = food_nutrient[
    food_nutrient["nutrient_id"].isin(
        NUTRIENT_MAP.keys()
    )
]

food_nutrient["nutrient"] = (
    food_nutrient["nutrient_id"]
    .map(NUTRIENT_MAP)
)

pivot = food_nutrient.pivot_table(
    index="fdc_id",
    columns="nutrient",
    values="amount",
    aggfunc="mean"
).reset_index()

usda = pd.merge(
    food,
    pivot,
    on="fdc_id",
    how="inner"
)

usda = usda[[
    "food",
    "calories",
    "protein",
    "fat",
    "carbs"
]]

# =========================
# IFCT PROCESSING
# =========================

print(ifct.columns)

ifct = ifct.rename(columns={

    "name": "food",

    "enerc": "calories",

    "protcnt": "protein",

    "fatce": "fat",

    "choavldf": "carbs"
})

ifct = ifct[[
    "food",
    "calories",
    "protein",
    "fat",
    "carbs"
]]

ifct["food"] = ifct["food"].apply(clean_food)

# =========================
# EXISTING DATASET CLEAN
# =========================

existing["food"] = existing["food"].apply(
    clean_food
)

# =========================
# MERGE ALL DATASETS
# =========================

merged = pd.concat([

    ifct,
    usda,
    existing

], ignore_index=True)

# =========================
# CLEAN NUMERIC VALUES
# =========================

for col in [
    "calories",
    "protein",
    "fat",
    "carbs"
]:

    merged[col] = pd.to_numeric(
        merged[col],
        errors="coerce"
    )

merged = merged.dropna(subset=[
    "calories",
    "protein",
    "fat",
    "carbs"
])

# =========================
# REMOVE DUPLICATES
# =========================

merged = merged.groupby(
    "food",
    as_index=False
).agg({

    "calories": "mean",
    "protein": "mean",
    "fat": "mean",
    "carbs": "mean"

})

# =========================
# ADD CUSTOM INGREDIENTS
# =========================

extra = pd.DataFrame([

    # MEAT

    ["chicken", 239, 27, 14, 0],
    ["broiler chicken", 215, 27, 11, 0],
    ["chicken breast", 165, 31, 3.6, 0],
    ["chicken leg", 216, 27, 12, 0],
    ["mutton", 294, 25, 21, 0],
    ["goat meat", 143, 27, 3, 0],
    ["beef", 250, 26, 15, 0],
    ["fish", 206, 22, 12, 0],
    ["prawn", 99, 24, 0.3, 0],
    ["egg", 155, 13, 11, 1.1],

    # VEGETABLES

    ["onion", 40, 1.1, 0.1, 9],
    ["tomato", 18, 0.9, 0.2, 3.9],
    ["potato", 77, 2, 0.1, 17],
    ["carrot", 41, 0.9, 0.2, 10],
    ["beans", 31, 1.8, 0.1, 7],
    ["peas", 81, 5, 0.4, 14],
    ["capsicum", 20, 0.9, 0.2, 4.6],
    ["cauliflower", 25, 1.9, 0.3, 5],
    ["cabbage", 25, 1.3, 0.1, 6],
    ["brinjal", 25, 1, 0.2, 6],

    # SPICES

    ["ginger", 80, 1.8, 0.8, 18],
    ["garlic", 149, 6.4, 0.5, 33],
    ["turmeric powder", 312, 9.7, 3.3, 67],
    ["red chilli powder", 282, 12, 13, 49],
    ["green chilli", 40, 2, 0.2, 9],
    ["pepper", 251, 10, 3.3, 64],
    ["coriander powder", 298, 12, 18, 55],
    ["cumin", 375, 18, 22, 44],
    ["mustard seeds", 508, 26, 36, 28],
    ["garam masala", 350, 10, 15, 50],

    # LEAVES

    ["mint leaves", 44, 3.3, 0.7, 8],
    ["coriander leaves", 23, 2.1, 0.5, 3.7],
    ["curry leaves", 108, 6.1, 1, 18],

    # DAIRY

    ["milk", 42, 3.4, 1, 5],
    ["curd", 61, 3.5, 3.3, 4.7],
    ["paneer", 265, 18, 20, 3],
    ["butter", 717, 0.9, 81, 0.1],
    ["ghee", 900, 0, 100, 0],
    ["cashews", 553, 18, 44, 30],
    ["water", 0, 0, 0, 0],
    ["tamarind", 239, 2.8, 0.6, 62.5],
    ["sambar powder", 325, 12, 6, 58],
    ["water", 0, 0, 0, 0],

    # OILS

    ["oil", 884, 0, 100, 0],

    # RICE & GRAINS

    ["rice", 130, 2.7, 0.3, 28],
    ["basmati rice", 130, 2.7, 0.3, 28],
    ["wheat flour", 364, 10, 1, 76],

    # OTHER

    ["salt", 0, 0, 0, 0],
    ["lemon juice", 22, 0.3, 0.2, 6.9]

], columns=[

    "food",
    "calories",
    "protein",
    "fat",
    "carbs"

])

merged = pd.concat([
    merged,
    extra
], ignore_index=True)

# =========================
# FINAL CLEAN
# =========================

merged["food"] = merged["food"].apply(clean_food)

merged = merged.groupby(
    "food",
    as_index=False
).mean()

merged = merged.sort_values("food")

# =========================
# SAVE FINAL DATASET
# =========================

merged.to_csv(
    "data/merged_dataset.csv",
    index=False
)

print("Merged dataset created successfully!")
print("Total foods:", len(merged))