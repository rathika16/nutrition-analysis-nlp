from flask import Flask, render_template, request
import pandas as pd
import re
from rapidfuzz import process, fuzz

app = Flask(__name__)

# =========================
# LOAD DATASET
# =========================

df = pd.read_csv("data/merged_dataset.csv")


df.columns = df.columns.str.lower().str.strip()

# =========================
# FOOD DATABASE
# =========================

FOOD_DB = {}

for _, row in df.iterrows():

    FOOD_DB[str(row["food"]).lower().strip()] = {

        "calories": float(row["calories"]),
        "protein": float(row["protein"]),
        "fat": float(row["fat"]),
        "carbs": float(row["carbs"])
    }

# =========================
# CUSTOM FOODS
# =========================

CUSTOM_FOODS = {

    "goat meat": {
        "calories": 143,
        "protein": 27,
        "fat": 3,
        "carbs": 0
    },

    "ginger": {
        "calories": 80,
        "protein": 1.8,
        "fat": 0.8,
        "carbs": 18
    },

    "garlic": {
        "calories": 149,
        "protein": 6.4,
        "fat": 0.5,
        "carbs": 33
    },

    "turmeric powder": {
        "calories": 312,
        "protein": 9.7,
        "fat": 3.3,
        "carbs": 67
    },

    "red chilli powder": {
        "calories": 282,
        "protein": 12,
        "fat": 13,
        "carbs": 49
    },

    "garam masala": {
        "calories": 350,
        "protein": 10,
        "fat": 15,
        "carbs": 50
    },

    "salt": {
        "calories": 0,
        "protein": 0,
        "fat": 0,
        "carbs": 0
    },

    "mint leaves": {
        "calories": 44,
        "protein": 3.3,
        "fat": 0.7,
        "carbs": 8
    },

    "coriander leaves": {
        "calories": 23,
        "protein": 2.1,
        "fat": 0.5,
        "carbs": 3.7
    },

    "lemon juice": {
        "calories": 22,
        "protein": 0.3,
        "fat": 0.2,
        "carbs": 6.9
    },
    
    "coriander powder": {
    "calories": 298,
    "protein": 12,
    "fat": 18,
    "carbs": 55
},

"sambar powder": {
    "calories": 325,
    "protein": 10,
    "fat": 12,
    "carbs": 50
},

"water": {
    "calories": 0,
    "protein": 0,
    "fat": 0,
    "carbs": 0
},

"egg": {
    "calories": 155,
    "protein": 13,
    "fat": 11,
    "carbs": 1.1
},

"soy sauce": {
    "calories": 53,
    "protein": 8,
    "fat": 0.6,
    "carbs": 4.9
},

    "curd": {
        "calories": 61,
        "protein": 3.5,
        "fat": 3.3,
        "carbs": 4.7
    }
    
}

# =========================
# MERGE CUSTOM
# =========================

FOOD_DB.update(CUSTOM_FOODS)

# =========================
# UNIT MAP
# =========================

UNIT_MAP = {

    "kg": 1000,
    "g": 1,
    "gram": 1,
    "grams": 1,

    "cup": 200,
    "cups": 200,

    "tbsp": 15,
    "tablespoon": 15,

    "tsp": 5,
    "teaspoon": 5,

    "ml": 1,
    "ltr": 1000
}

# =========================
# CLEAN TEXT
# =========================

def clean_text(text):

    text = str(text).lower()

    # FRACTIONS
    text = text.replace("½", "0.5")
    text = text.replace("¼", "0.25")
    text = text.replace("¾", "0.75")

    # ALL DASH TYPES
    text = text.replace("-", " ")
    text = text.replace("–", " ")
    text = text.replace("—", " ")

    # REMOVE SPECIAL SYMBOLS
    text = re.sub(r"[^a-z0-9./ ]", " ", text)

    # EXTRA SPACES
    text = re.sub(r"\s+", " ", text)

    return text.strip()

# =========================
# QUANTITY
# =========================

def extract_quantity(text):

    text = clean_text(text)

    # SPECIAL CASES

    if "handful" in text:
        return 25

    if "to taste" in text:
        return 5

    # EGG FIX

    if "egg" in text:

        qty_match = re.search(r"(\d+)", text)

        if qty_match:
            eggs = float(qty_match.group(1))
            return eggs * 50

        return 50

    # NORMAL QUANTITY

    qty_match = re.search(r"(\d+\.?\d*)", text)

    if qty_match:
        qty = float(qty_match.group(1))
    else:
        qty = 1

    # UNIT MATCH

    unit_match = re.search(
        r"\b(kg|g|gram|grams|cup|cups|tbsp|tablespoon|tsp|teaspoon|ml|ltr)\b",
        text
    )

    if unit_match:

        unit = unit_match.group(1)

        multiplier = UNIT_MAP.get(unit, 1)

        grams = qty * multiplier

    else:

        # ONLY WHEN NO UNIT
        grams = qty * 50

    return round(grams, 2)

# =========================
# FOOD NAME
# =========================

def extract_food_name(text):

    text = clean_text(text)

    # SPECIAL CASES FIRST

    if "ginger garlic paste" in text:
        return ["ginger", "garlic"]

    if "ginger garlic" in text:
        return ["ginger", "garlic"]

    # REMOVE EXTRA WORDS

    remove_words = [

        "optional",
        "finely",
        "thinly",
        "chopped",
        "sliced",
        "for garnish",
        "to taste",
        "for boiling",
        "small",
        "medium",
        "large",
        "few",
        "handful",
        "juice of",
        "paste"
        "all purpose flour"
        "bone-in preferred"
    ]

    for word in remove_words:
        text = text.replace(word, "")

    # REMOVE NUMBERS

    text = re.sub(r"\b\d+\.?\d*\b", "", text)

    # REMOVE UNITS

    text = re.sub(
        r"(kg|g|gram|grams|cup|cups|tbsp|tablespoon|tsp|teaspoon|ml|ltr)",
        "",
        text
    )

    text = text.strip()

    # SPECIAL MAPPINGS

    mappings = {

        "mutton": "goat meat",

        "curd yogurt": "curd",
        "yogurt": "curd",

        "turmeric": "turmeric powder",

        "chilli powder": "red chilli powder",

        "mint": "mint leaves",

        "coriander": "coriander leaves",

        "lemon": "lemon juice",
        "all purpose flour": "maida",
        "spring onion": "onion",
        "egg": "egg",
    }

    for key, value in mappings.items():

        if key in text:
            return [value]

    return [text]

# =========================
# MATCH FOOD
# =========================

def match_food(food):

    food = clean_text(food)

    if food in FOOD_DB:
        return food

    match = process.extractOne(
        food,
        FOOD_DB.keys(),
        scorer=fuzz.token_sort_ratio
    )

    if match and match[1] >= 75:
        return match[0]

    return None

# =========================
# CALCULATE
# =========================

def calculate(food, grams):

    data = FOOD_DB[food]

    factor = grams / 100

    return {

        "calories": round(data["calories"] * factor, 2),
        "protein": round(data["protein"] * factor, 2),
        "fat": round(data["fat"] * factor, 2),
        "carbs": round(data["carbs"] * factor, 2)
    }

# =========================
# HOME
# =========================

@app.route("/", methods=["GET", "POST"])

def home():

    results = []

    total = {
        "calories": 0,
        "protein": 0,
        "fat": 0,
        "carbs": 0
    }

    user_input = ""

    if request.method == "POST":

        user_input = request.form["food"]

        lines = user_input.split("\n")

        for line in lines:

            line = line.strip()

            if not line:
                continue

            grams = extract_quantity(line)

            food_names = extract_food_name(line)

            split_grams = grams / len(food_names)

            for food_name in food_names:

                matched = match_food(food_name)

                if matched:

                    nutrition = calculate(
                        matched,
                        split_grams
                    )

                    results.append({

                        "food": matched,
                        "qty": round(split_grams, 2),

                        "cal": nutrition["calories"],
                        "protein": nutrition["protein"],
                        "fat": nutrition["fat"],
                        "carbs": nutrition["carbs"],

                        "status": "found"
                    })

                    total["calories"] += nutrition["calories"]
                    total["protein"] += nutrition["protein"]
                    total["fat"] += nutrition["fat"]
                    total["carbs"] += nutrition["carbs"]

                else:

                    results.append({

                        "food": food_name,
                        "qty": split_grams,

                        "cal": 0,
                        "protein": 0,
                        "fat": 0,
                        "carbs": 0,

                        "status": "missing"
                    })

    return render_template(
        "index.html",
        results=results,
        total=total,
        user_input=user_input
    )

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(debug=True)