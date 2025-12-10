# Knowledge Graph-Based Product Substitution System

**Student Developer Assignment**

A Streamlit web application that suggests alternative products when requested items are out of stock, using Knowledge Graph traversal and classical reasoning (no ML/AI).

---

## System Overview

This system implements a multi-stage graph traversal algorithm with weighted scoring and rule-based explanations to find the best product substitutes based on category similarity, brand preferences, price constraints, and dietary requirements.

---

## Knowledge Graph Design

### Node Types

1. **Product**: Specific items (e.g., 'Amul Butter', 'Mother Dairy Butter')
   - Properties: `price`, `stock`, `in_stock`, `id`

2. **Category**: Broad classifications (e.g., 'Dairy', 'NonDairyMilk', 'Bakery', 'Snack')
   - Used for primary product classification

3. **Brand**: Manufacturers (e.g., 'Amul', 'Mother Dairy', 'Britannia')
   - Identifies product manufacturers

4. **Attribute**: Product properties (e.g., 'lactose_free', 'veg', 'sugar_free', 'organic')
   - Binary/categorical characteristics

### Edge Types

1. **IS_A**: Product → Category
   - Primary categorization relationship
   - Example: "Amul Butter" IS_A "Dairy"

2. **HAS_BRAND**: Product → Brand
   - Brand association
   - Example: "Amul Butter" HAS_BRAND "Amul"

3. **HAS_ATTRIBUTE**: Product → Attribute
   - Product characteristics
   - Example: "Amul Butter" HAS_ATTRIBUTE "veg"

4. **IS_SIMILAR_TO**: Category ↔ Category
   - Category similarity with weight property
   - Example: "Dairy" IS_SIMILAR_TO "NonDairyMilk" (weight: 0.7)

---

## Multi-Stage Traversal Algorithm

### Stage 1: Exact Match Search
- Check if requested Product node exists
- Verify `in_stock: True` property
- If available, display product (no substitutes needed)

### Stage 2: Same Category Search
1. Find Category of requested product via IS_A edge
2. Traverse from Category back to all Product nodes (inverse IS_A)
3. Apply A-Priori constraint filtering:
   - `in_stock == True`
   - `price <= max_price`
   - All required Attribute nodes connected via HAS_ATTRIBUTE

### Stage 3: Related Category Search
1. Traverse from initial Category to related Categories via IS_SIMILAR_TO edges
2. From related Categories, traverse to their Product nodes
3. Apply same A-Priori constraints as Stage 2

---

## Scoring Formula

Each candidate is scored using a weighted formula:

```
Score = w_category × (1/d_cat) + w_brand × m_brand + w_price × (1 - P_ratio)
```

Where:
- **w_category = 10**: Weight for category match
- **w_brand = 5**: Weight for brand match
- **w_price = 1**: Weight for price consideration
- **d_cat**: Category distance (1 for same category, >1 for related categories based on IS_SIMILAR_TO weight)
- **m_brand**: Brand match (1 if matches preferred brand, 0 otherwise)
- **P_ratio**: Price ratio (candidate_price / max_price)

### Example Calculation

Requested: Amul Butter (Rs. 56, Dairy, Out of Stock)
Candidate: Mother Dairy Butter (Rs. 54, Dairy, In Stock)
Max Price: Rs. 60
Preferred Brand: None

```
d_cat = 1.0 (same category)
m_brand = 0 (no preferred brand)
P_ratio = 54/60 = 0.9

Score = 10 × (1/1.0) + 5 × 0 + 1 × (1 - 0.9)
      = 10 + 0 + 0.1
      = 10.1
```

---

## Rule-Based Explanations

Each substitute is tagged with applicable rules, prioritized from highest to lowest:

| Rule Tag | Condition | Priority | Explanation |
|----------|-----------|----------|-------------|
| `same_cat_same_brand` | Same Category AND Same Brand | 1 (Highest) | "This is from the same category and the brand you prefer." |
| `same_cat_all_tags` | Same Category AND All Attributes matched | 2 | "Best fit: Same product type and meets all your dietary requirements." |
| `related_cat_all_tags` | Related Category AND All Attributes matched | 3 | "Highly related product category that meets all your must-have tags." |
| `cheaper_option` | Price ≤ 70% of requested price | 4 | "A much cheaper option that still meets your needs." |
| `diff_brand_perfect_match` | Same Category, Different Brand, All tags matched | 5 | "Same product category, different brand, and fully meets your requirements." |

The highest priority applicable rule is used for the explanation.

---

## Streamlit UI Features

### Input/Control Panel (Sidebar)

1. **Requested Product** (Selectbox)
   - Dropdown of all available products

2. **Max Price** (Numeric Input)
   - Maximum acceptable price for substitutes

3. **Required Tags** (Multi-Select)
   - Checkboxes for all Attribute nodes
   - Must-have attributes for substitutes

4. **Preferred Brand** (Selectbox)
   - Optional brand preference
   - Dropdown of all Brand nodes

5. **Find Alternatives** (Button)
   - Triggers the search algorithm

### Output Panel (Main Area)

1. **Exact Match Section**
   - Displays if requested product is in stock
   - Green "In Stock" badge
   - Product details (brand, price, category, attributes)

2. **Substitution Results Section**
   - Shown when product is out of stock
   - Message: "[Product Name] is currently Out of Stock. Here are the best alternatives:"
   - List of up to 3 substitutes with:
     - Product name and rank
     - Brand
     - Price
     - Stock availability
     - Match score
     - Rule-based explanation

3. **No Alternatives Found**
   - Displayed if no products match criteria
   - Suggestions to relax constraints

---

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Steps

1. **Clone/Download the project**
   ```bash
   cd shopkeeper_product_substitution_assistant
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Access the app**
   - Opens automatically in browser at `http://localhost:8501`

---

## Project Structure

```
shopkeeper_product_substitution_assistant/
├── app.py              # Streamlit UI
├── kg_logic.py         # Knowledge Graph implementation
├── data.json           # Product catalog
├── requirements.txt    # Dependencies
└── README.md          # This file
```

---

## File Descriptions

### app.py
- Streamlit web interface
- Input controls (product, price, tags, brand)
- Output display (exact match, substitutes, no results)
- Custom CSS styling

### kg_logic.py
- Knowledge Graph class using NetworkX
- Graph construction from JSON
- Multi-stage traversal algorithm
- Weighted scoring formula
- Rule-based explanation generation

### data.json
- Product catalog (42 products across 5 categories)
- Category relations with similarity weights
- Product attributes and pricing

---

## Example Usage

### Scenario 1: Out of Stock Product

**Input:**
- Requested Product: Amul Butter
- Max Price: Rs. 60
- Required Tags: ["veg"]
- Preferred Brand: None

**Output:**
- "Amul Butter is currently Out of Stock. Here are the best alternatives:"
- 1. Mother Dairy Butter (Rs. 54) - "Best fit: Same product type and meets all your dietary requirements."
- 2. Nutralite Fat Spread (Rs. 45) - "A much cheaper option that still meets your needs."

### Scenario 2: Product Available

**Input:**
- Requested Product: Britannia White Bread
- Max Price: Rs. 50
- Required Tags: ["veg"]

**Output:**
- "Britannia White Bread is currently In Stock!"
- No substitutes shown

### Scenario 3: Dietary Restrictions

**Input:**
- Requested Product: Amul Gold Milk (Out of Stock)
- Max Price: Rs. 120
- Required Tags: ["veg", "lactose_free"]

**Output:**
- Substitutes from NonDairyMilk category:
- 1. Raw Pressery Almond Milk (Rs. 100) - "Highly related product category that meets all your must-have tags."
- 2. Sofit Soya Milk (Rs. 110) - "Highly related product category that meets all your must-have tags."

---

## Technical Implementation

### No ML/AI Used
- Pure graph algorithms (NetworkX)
- Classical reasoning with explicit rules
- Deterministic scoring formula
- No embeddings, vector search, or LLM APIs

### Graph Traversal
- BFS-like traversal from Category nodes
- Weighted edge traversal for category similarity
- A-priori constraint filtering

### Scoring System
- Mathematical formula with fixed weights
- Category distance calculation
- Brand matching logic
- Price ratio normalization

### Rule Engine
- Explicit condition checking
- Priority-based rule selection
- Human-readable explanations

---

## Deployment

### Streamlit Cloud (Recommended)

1. Push code to GitHub
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub repository
4. Deploy `app.py`
5. Share public URL

### Local Deployment

```bash
streamlit run app.py --server.port 8501
```

---

## Assignment Deliverables

1. Deployed Streamlit web app
2. GitHub repository with:
   - Complete source code
   - README documentation
   - Requirements file
3. Knowledge Graph design documentation
4. Search algorithm explanation
5. Rule-based explanation mechanism

---

## System Specifications

- **Graph Library**: NetworkX 3.x
- **UI Framework**: Streamlit 1.x
- **Language**: Python 3.8+
- **Data Format**: JSON
- **No Dependencies On**: TensorFlow, PyTorch, scikit-learn, OpenAI, Anthropic, or any ML libraries

---

## Author

Student Developer Assignment
Date: December 2025

---

## License

Educational project for assignment purposes.
