import streamlit as st
from kg_logic import KnowledgeGraph
import json

# Page configuration
st.set_page_config(
    page_title="Product Substitution System",
    layout="wide"
)

# Custom CSS with enhanced styling
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    
    /* Header Styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .header-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
    }
    
    .header-subtitle {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    /* Input Section */
    .input-section {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 1rem;
        border-bottom: 3px solid #667eea;
        padding-bottom: 0.5rem;
    }
    
    /* Product Card */
    .product-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 5px solid #4CAF50;
    }
    
    .product-card-out {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 5px solid #f44336;
    }
    
    .product-name {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 1rem;
    }
    
    .product-detail {
        font-size: 1rem;
        color: #4a5568;
        margin: 0.5rem 0;
    }
    
    .product-detail strong {
        color: #2d3748;
    }
    
    /* Search Criteria Box */
    .criteria-box {
        background: linear-gradient(135deg, #f6f8fb 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 2px solid #667eea;
    }
    
    .criteria-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #667eea;
        margin-bottom: 1rem;
    }
    
    /* Substitute Card */
    .substitute-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid #2196F3;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .substitute-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2196F3;
        margin-bottom: 1rem;
    }
    
    /* Explanation Box */
    .explanation-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 1.2rem;
        border-radius: 8px;
        margin-top: 1rem;
        border-left: 4px solid #2196F3;
    }
    
    .explanation-title {
        font-weight: 600;
        color: #1565c0;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
    }
    
    .explanation-text {
        color: #424242;
        line-height: 1.6;
    }
    
    /* Status Badges */
    .status-badge-success {
        background-color: #4CAF50;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .status-badge-error {
        background-color: #f44336;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Footer */
    .footer-box {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        color: #666;
        margin-top: 2rem;
    }
    
    .footer-box p {
        margin: 0.5rem 0;
    }
    
    .footer-box strong {
        color: #667eea;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Knowledge Graph
@st.cache_resource
def load_kg():
    return KnowledgeGraph("data.json")

kg = load_kg()

# Load product data
@st.cache_data
def load_products():
    with open("data.json", 'r', encoding='utf-8') as f:
        return json.load(f)

data = load_products()

# Header
st.markdown("""
    <div class="header-container">
        <h1 class="header-title">Product Substitution System</h1>
    </div>
""", unsafe_allow_html=True)

# Input Section
st.markdown('<div class="section-title">Find your products</div>', unsafe_allow_html=True)

# Create columns for input controls
col_input1, col_input2, col_input3, col_input4 = st.columns(4)

with col_input1:
    all_products = sorted([p['name'] for p in data['products']])
    requested_product = st.selectbox(
        "Requested Product",
        all_products,
        help="Select the product you want to purchase"
    )

with col_input2:
    max_price = st.number_input(
        "Max Price (Rs.)",
        min_value=0,
        max_value=500,
        value=150,
        step=10,
        help="Maximum acceptable price for substitutes"
    )

with col_input3:
    all_attributes = sorted(list(set([attr for p in data['products'] for attr in p['attributes']])))
    required_tags = st.multiselect(
        "Required Tags",
        all_attributes,
        help="Select must-have attributes"
    )

with col_input4:
    all_brands = sorted(list(set([p['brand'] for p in data['products']])))
    preferred_brand_option = st.selectbox(
        "Preferred Brand",
        ["None"] + all_brands,
        help="Select if you prefer a specific brand"
    )
    preferred_brand = None if preferred_brand_option == "None" else preferred_brand_option

# Find Alternatives Button
st.markdown("---")
search_button = st.button("Find Alternatives", type="primary", use_container_width=True)

st.markdown("---")

# Product Information Section
st.markdown('<div class="section-title">Product Information</div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    # Get product details
    product_details = kg.get_product_details(requested_product)
    
    if product_details:
        in_stock = product_details.get('in_stock', False)
        
        if in_stock:
            # Product is in stock
            st.markdown(f"""
                <div class="product-card">
                    <div class="product-name">{requested_product}</div>
                    <div class="product-detail"><strong>Brand:</strong> {product_details['brand']}</div>
                    <div class="product-detail"><strong>Category:</strong> {product_details['category']}</div>
                    <div class="product-detail"><strong>Price:</strong> Rs. {product_details['price']}</div>
                    <div class="product-detail"><strong>Attributes:</strong> {', '.join(product_details['attributes'])}</div>
                    <div style="margin-top: 1rem;">
                        <span class="status-badge-success">In Stock</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            # Out of Stock
            st.markdown(f"""
                <div class="product-card-out">
                    <div class="product-name">{requested_product}</div>
                    <div class="product-detail"><strong>Brand:</strong> {product_details['brand']}</div>
                    <div class="product-detail"><strong>Category:</strong> {product_details['category']}</div>
                    <div class="product-detail"><strong>Price:</strong> Rs. {product_details['price']}</div>
                    <div class="product-detail"><strong>Attributes:</strong> {', '.join(product_details['attributes'])}</div>
                    <div style="margin-top: 1rem;">
                        <span class="status-badge-error">Out of Stock</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="criteria-box">
            <div class="criteria-title">Search Criteria</div>
            <div class="product-detail"><strong>Max Price:</strong> Rs. {max_price}</div>
            <div class="product-detail"><strong>Preferred Brand:</strong> {preferred_brand if preferred_brand else 'Any'}</div>
            <div class="product-detail"><strong>Required Tags:</strong> {len(required_tags)}</div>
            <div style="margin-left: 1rem; margin-top: 0.5rem;">
                {('<br>'.join(['• ' + tag for tag in required_tags])) if required_tags else '• None'}
            </div>
        </div>
    """, unsafe_allow_html=True)

# Search Results
if search_button:
    st.markdown("---")
    st.markdown('<div class="section-title">Search Results</div>', unsafe_allow_html=True)
    
    # Check if product is in stock
    if kg.check_exact_match(requested_product):
        # Stage 1: Exact Match - Product is available
        st.success(f"**{requested_product}** is currently **In Stock**!")
        st.balloons()
        st.info("No substitutes needed - the requested product is available.")
    else:
        # Product is out of stock - find substitutes
        st.error(f"**{requested_product}** is currently **Out of Stock**. Here are the best alternatives:")
        
        # Find substitutes using Knowledge Graph
        substitutes = kg.find_substitutes(
            requested_product,
            max_price,
            required_tags,
            preferred_brand
        )
        
        if not substitutes:
            # No alternatives found
            st.warning("**No suitable alternatives found.**")
            st.info("We couldn't find any products that match all your criteria.")
            st.write("**Suggestions:**")
            st.write("• Increase your maximum price")
            st.write("• Remove some required tags")
            st.write("• Try selecting a different brand preference")
        else:
            # Display substitutes
            st.success(f"Found **{len(substitutes)}** alternative(s):")
            
            for idx, sub in enumerate(substitutes, 1):
                st.markdown(f"""
                    <div class="substitute-card">
                        <div class="substitute-header">#{idx} {sub['name']}</div>
                        <div class="product-detail"><strong>Brand:</strong> {sub['brand']}</div>
                        <div class="product-detail"><strong>Price:</strong> Rs. {sub['price']}</div>
                        <div class="product-detail"><strong>Stock Available:</strong> {sub['stock']} units
                    </div>
                    <div>
                        <div class="explanation-box">
                            <div class="explanation-title">Why this alternative?</div>
                            <div class="explanation-text">{sub['explanation']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
    <div class="footer-box">
        <p><strong>System Architecture:</strong> Knowledge Graph with Multi-Stage Traversal</p>
        <p>Nodes: Product, Category, Brand, Attribute | Edges: IS_A, HAS_BRAND, HAS_ATTRIBUTE, IS_SIMILAR_TO</p>
        <p>Scoring: Weighted formula with category distance, brand match, and price ratio</p>
        <p><strong>No ML, embeddings, or AI models used - Pure classical reasoning</strong></p>
    </div>
""", unsafe_allow_html=True)
