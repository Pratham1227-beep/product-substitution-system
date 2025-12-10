# ShopSmart - Product Substitution System

A Knowledge Graph-based product substitution system that suggests alternative products when requested items are out of stock, using classical graph traversal and rule-based reasoning (no ML/AI).

---

## How to Run Locally

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation Steps

1. **Navigate to project directory**
   ```bash
   cd shopkeeper_product_substitution_assistant
   ```

2. **Create virtual environment** (recommended)
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
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

## Knowledge Graph Design

### Node Types

The Knowledge Graph consists of **4 types of nodes**:

| Node Type | Description | Example |
|-----------|-------------|---------|
| **Product** | Individual products with properties (price, stock, id) | "Amul Butter", "Britannia Bread" |
| **Category** | Product categories | "Dairy", "Bakery", "Snacks", "Beverages" |
| **Brand** | Product manufacturers/brands | "Amul", "Britannia", "Nestle" |
| **Attribute** | Product characteristics/tags | "veg", "lactose_free", "sugar_free" |

### Edge Types (Relationships)

The graph uses **4 types of edges** to represent relationships:

| Edge Type | Direction | Description | Example |
|-----------|-----------|-------------|---------|
| **IS_A** | Product → Category | Product belongs to a category | "Amul Butter" → "Dairy" |
| **HAS_BRAND** | Product → Brand | Product is made by a brand | "Amul Butter" → "Amul" |
| **HAS_ATTRIBUTE** | Product → Attribute | Product has a specific attribute | "Amul Butter" → "veg" |
| **IS_SIMILAR_TO** | Category ↔ Category | Categories are related/similar (with weight) | "Dairy" ↔ "NonDairyMilk" (weight: 0.7) |

### Graph Structure Visualization

```
[Product: Amul Butter]
    ├── IS_A ──────────→ [Category: Dairy]
    ├── HAS_BRAND ─────→ [Brand: Amul]
    ├── HAS_ATTRIBUTE ─→ [Attribute: veg]
    ├── HAS_ATTRIBUTE ─→ [Attribute: lactose]
    └── HAS_ATTRIBUTE ─→ [Attribute: salted]

[Category: Dairy]
    └── IS_SIMILAR_TO ←──→ [Category: NonDairyMilk] (weight: 0.7)
```

---

## Search Method Used

### Multi-Stage Graph Traversal Algorithm

The system uses a **three-stage search strategy** to find substitutes:

#### **Stage 1: Exact Match Check**
- Check if requested Product node exists
- Verify `in_stock: True` property
- If available, display product (no substitutes needed)

#### **Stage 2: Same Category Search**
1. Start from the requested product node
2. Traverse the **IS_A** edge to find the product's category
3. From the category node, traverse back to all products in that category (BFS-like)
4. Apply constraint filtering (stock, price, attributes)

#### **Stage 3: Related Category Search**
1. From the current category node, traverse **IS_SIMILAR_TO** edges
2. Find all related/similar categories
3. For each related category, find all products (same as Stage 2)
4. Apply constraint filtering

### Constraint-Based Filtering (A-Priori)

All candidates must satisfy these **hard constraints**:

| Constraint | Rule |
|------------|------|
| **Stock Availability** | `stock > 0` |
| **Price Budget** | `price <= max_price` |
| **Required Attributes** | All required tags must be present |
| **Not Same Product** | Exclude the requested product itself |

### Scoring Formula

Each candidate is scored using a weighted formula:

```
Score = w_category × (1/d_cat) + w_brand × m_brand + w_price × (1 - P_ratio)
```

Where:
- **w_category = 10**: Weight for category match
- **w_brand = 5**: Weight for brand match
- **w_price = 1**: Weight for price consideration
- **d_cat**: Category distance (1 for same category, >1 for related categories)
- **m_brand**: Brand match (1 if matches preferred brand, 0 otherwise)
- **P_ratio**: Price ratio (candidate_price / max_price)

---

## Explanation Rule Mechanism

### Rule-Based Explanations

Each substitute is tagged with applicable rules, prioritized from highest to lowest:

| Rule Tag | Condition | Priority | Human Explanation |
|----------|-----------|----------|-------------------|
| `same_cat_same_brand` | Same Category AND Same Brand | 1 (Highest) | "This is from the same category and the brand you prefer." |
| `same_cat_all_tags` | Same Category AND All Attributes matched | 2 | "Best fit: Same product type and meets all your dietary requirements." |
| `related_cat_all_tags` | Related Category AND All Attributes matched | 3 | "Highly related product category that meets all your must-have tags." |
| `cheaper_option` | Price ≤ 70% of requested price | 4 | "A much cheaper option that still meets your needs." |
| `diff_brand_perfect_match` | Same Category, Different Brand, All tags matched | 5 | "Same product category, different brand, and fully meets your requirements." |

### How Explanations Are Generated

1. **Rule Checking**: For each candidate, check which rules apply based on explicit conditions
2. **Priority Sorting**: Sort applicable rules by priority (lower number = higher priority)
3. **Explanation Selection**: Use the highest priority rule to generate the explanation
4. **Display**: Show the human-readable explanation to the user

### Example Flow

**Requested Product:** Amul Butter (Rs. 56, Dairy, Out of Stock)  
**Candidate:** Mother Dairy Butter (Rs. 54, Dairy, In Stock)  
**User Requirements:** Max Price = Rs. 60, Tags = ["veg"]

**Rules Applied:**
- ✓ `same_cat_all_tags` (Same category + all tags matched)
- ✓ `cheaper_option` (Rs. 54 ≤ 70% of Rs. 56)
- ✓ `diff_brand_perfect_match` (Same category, different brand, tags matched)

**Explanation Shown:** "Best fit: Same product type and meets all your dietary requirements." (highest priority rule)

---

## Design Description

### KG Modeling Details

**Graph Type:** Undirected graph using NetworkX

**Node Properties:**
- **Product nodes**: `price`, `stock`, `in_stock` (boolean), `id`
- **Category nodes**: No additional properties
- **Brand nodes**: No additional properties
- **Attribute nodes**: No additional properties

**Edge Properties:**
- **IS_A, HAS_BRAND, HAS_ATTRIBUTE**: `relation` property
- **IS_SIMILAR_TO**: `relation` property + `weight` (0.0-1.0)

**Data Source:** `data.json` with 42 products across 5 categories

### Search Approach

**Algorithm:** Multi-stage BFS-like traversal

**Stage 1 (Exact Match):**
- O(1) lookup in graph
- Check `in_stock` property

**Stage 2 (Same Category):**
- O(1) to get category via IS_A edge
- O(n) to traverse all products in category
- O(m) to filter by constraints (n = products in category, m = attributes)

**Stage 3 (Related Categories):**
- O(k) to get related categories via IS_SIMILAR_TO (k = number of similar categories)
- O(n×k) to traverse products in related categories
- O(m×k) to filter by constraints

**Scoring:** O(1) per candidate (simple arithmetic)

**Total Complexity:** O(n + k×n) where n = products per category, k = related categories

### Constraint Handling

**Hard Constraints (A-Priori Filtering):**
- Applied **before** scoring to reduce search space
- Candidates that fail any constraint are immediately excluded
- No partial matches - all constraints must be satisfied

**Constraint Types:**
1. **Stock Constraint**: Binary check (`stock > 0`)
2. **Price Constraint**: Comparison (`price <= max_price`)
3. **Attribute Constraint**: Set inclusion (all required tags must be present)

**Implementation:**
```python
# Pseudocode
if not product.in_stock:
    continue  # Skip this product
if product.price > max_price:
    continue  # Skip this product
if not all_required_tags_present(product):
    continue  # Skip this product
# Product passes all constraints - add to candidates
```

### Sample Rule Tags and Explanations

**Rule Tag:** `same_cat_same_brand`  
**Condition:** Product is in same category AND same brand as requested  
**Example:** Requested "Amul Butter" → Suggested "Amul Cheese Slices"  
**Explanation:** "This is from the same category and the brand you prefer."

---

**Rule Tag:** `same_cat_all_tags`  
**Condition:** Product is in same category AND matches all required tags  
**Example:** Requested "Amul Butter" (veg) → Suggested "Mother Dairy Butter" (veg)  
**Explanation:** "Best fit: Same product type and meets all your dietary requirements."

---

**Rule Tag:** `related_cat_all_tags`  
**Condition:** Product is in related category AND matches all required tags  
**Example:** Requested "Amul Gold Milk" (veg, lactose_free) → Suggested "Raw Pressery Almond Milk" (veg, lactose_free, vegan)  
**Explanation:** "Highly related product category that meets all your must-have tags."

---

**Rule Tag:** `cheaper_option`  
**Condition:** Product price ≤ 70% of requested product price  
**Example:** Requested "Amul Butter" (Rs. 56) → Suggested "Nutralite Fat Spread" (Rs. 45)  
**Explanation:** "A much cheaper option that still meets your needs."

---

**Rule Tag:** `diff_brand_perfect_match`  
**Condition:** Same category, different brand, all tags matched  
**Example:** Requested "Britannia Cheese Cubes" (veg, lactose) → Suggested "Amul Cheese Slices" (veg, lactose)  
**Explanation:** "Same product category, different brand, and fully meets your requirements."

---

## Project Structure

```
shopkeeper_product_substitution_assistant/
│
├── app.py                  # Streamlit UI (main application)
├── kg_logic.py            # Knowledge Graph logic and reasoning
├── data.json              # Product data and category relations
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── PROJECT_SUMMARY.md     # Project summary
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Streamlit | Web UI framework |
| **Graph Library** | NetworkX | Graph data structure and traversal |
| **Language** | Python 3.8+ | Core implementation |
| **Data Format** | JSON | Product catalog storage |

### Why These Technologies?

- **Streamlit**: Rapid prototyping, built-in widgets, easy deployment
- **NetworkX**: Powerful graph algorithms, easy to use, well-documented
- **No ML/Embeddings**: Assignment requires classical reasoning, not ML

---

## Key Features

- ✓ Knowledge Graph with 4 node types and 4 edge types
- ✓ Multi-stage graph traversal (same category → related categories)
- ✓ Weighted scoring formula (no ML)
- ✓ Rule-based explanations (explicit conditions)
- ✓ A-priori constraint filtering
- ✓ Up to 3 substitutes returned
- ✓ Clean, modern UI with HTML/CSS styling
- ✓ 42 products across 5 categories

---

## No ML/AI Used

This system uses **pure graph-based reasoning** with explicit rules:
- ✗ No TensorFlow, PyTorch, scikit-learn
- ✗ No OpenAI, Anthropic, or LLM APIs
- ✗ No embeddings or vector search
- ✓ Only NetworkX for graph algorithms
- ✓ Classical reasoning with deterministic rules

---

## Author

Student Developer Assignment  
Date: December 2025

---

## License

Educational project for assignment purposes.
