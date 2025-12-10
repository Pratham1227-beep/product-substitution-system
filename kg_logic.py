import networkx as nx
import json
from typing import List, Dict, Optional, Tuple


class KnowledgeGraph:
    """
    Knowledge Graph for Product Substitution System
    
    Implements multi-stage traversal with weighted scoring and rule-based explanations.
    Uses NetworkX for graph data structure and traversal algorithms.
    
    No ML, embeddings, or AI - pure graph algorithms and classical reasoning.
    """
    
    # SCORING WEIGHTS (as per assignment requirements)
    W_CATEGORY = 10  # Weight for category match (highest priority)
    W_BRAND = 5      # Weight for brand match
    W_PRICE = 1      # Weight for price consideration
    
    # RULE-BASED EXPLANATIONS
    # Each rule has a priority (lower number = higher priority) and
    # a human-readable explanation text
    RULES = {
        "same_cat_same_brand": {
            "priority": 1,
            "explanation": "This is from the same category and the brand you prefer."
        },
        "same_cat_all_tags": {
            "priority": 2,
            "explanation": "Best fit: Same product type and meets all your dietary requirements."
        },
        "related_cat_all_tags": {
            "priority": 3,
            "explanation": "Highly related product category that meets all your must-have tags."
        },
        "cheaper_option": {
            "priority": 4,
            "explanation": "A much cheaper option that still meets your needs."
        },
        "diff_brand_perfect_match": {
            "priority": 5,
            "explanation": "Same product category, different brand, and fully meets your requirements."
        }
    }
    
    def __init__(self, data_file: str):
        """
        Initialize Knowledge Graph from JSON data file
        
        Args:
            data_file: Path to JSON file containing product catalog
        """
        # Create undirected graph using NetworkX
        self.graph = nx.Graph()
        
        # Store original product prices for comparison (cheaper option rule)
        self.product_prices = {}
        
        # Load data and build the graph
        self.load_data(data_file)
    
    def load_data(self, data_file: str) -> None:
        """
        Build Knowledge Graph from JSON data
        
        Creates nodes for:
        - Products (with price, stock, id properties)
        - Categories
        - Brands
        - Attributes
        
        Creates edges for:
        - IS_A: Product -> Category
        - HAS_BRAND: Product -> Brand
        - HAS_ATTRIBUTE: Product -> Attribute
        - IS_SIMILAR_TO: Category <-> Category (with weight)
        
        Args:
            data_file: Path to JSON file
        """
        # Load JSON data
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # ADD PRODUCT NODES AND EDGES
        for p in data['products']:
            # Add Product node with properties
            self.graph.add_node(
                p['name'],
                type='product',
                price=p['price'],
                stock=p['stock'],
                id=p['id'],
                in_stock=(p['stock'] > 0)  # Boolean flag for quick checking
            )
            
            # Store price for later comparison
            self.product_prices[p['name']] = p['price']
            
            # Add Category node (if not already exists)
            if not self.graph.has_node(p['category']):
                self.graph.add_node(p['category'], type='category')
            
            # Add Brand node (if not already exists)
            if not self.graph.has_node(p['brand']):
                self.graph.add_node(p['brand'], type='brand')
            
            # Add IS_A edge: Product -> Category
            self.graph.add_edge(p['name'], p['category'], relation='IS_A')
            
            # Add HAS_BRAND edge: Product -> Brand
            self.graph.add_edge(p['name'], p['brand'], relation='HAS_BRAND')
            
            # Add Attribute nodes and HAS_ATTRIBUTE edges
            for attr in p['attributes']:
                # Add Attribute node (if not already exists)
                if not self.graph.has_node(attr):
                    self.graph.add_node(attr, type='attribute')
                
                # Add HAS_ATTRIBUTE edge: Product -> Attribute
                self.graph.add_edge(p['name'], attr, relation='HAS_ATTRIBUTE')
        
        # ADD CATEGORY SIMILARITY EDGES
        # Add IS_SIMILAR_TO edges between categories (with weights)
        if 'category_relations' in data:
            for rel in data['category_relations']:
                self.graph.add_edge(
                    rel['source'],
                    rel['target'],
                    relation='IS_SIMILAR_TO',
                    weight=rel.get('weight', 0.5)  # Default weight if not specified
                )
    
    def get_neighbors_by_type(self, node: str, node_type: str) -> List[str]:
        """
        Get all neighboring nodes of a specific type
        
        Args:
            node: Node name to get neighbors for
            node_type: Type of neighbors to return ('product', 'category', 'brand', 'attribute')
        
        Returns:
            List of neighbor node names matching the specified type
        """
        if node not in self.graph:
            return []
        
        # Filter neighbors by type
        return [
            n for n in self.graph.neighbors(node)
            if self.graph.nodes[n].get('type') == node_type
        ]
    
    def get_product_category(self, product: str) -> Optional[str]:
        """
        Get category of a product via IS_A edge
        
        Args:
            product: Product name
        
        Returns:
            Category name or None if not found
        """
        categories = self.get_neighbors_by_type(product, 'category')
        return categories[0] if categories else None
    
    def get_product_brand(self, product: str) -> Optional[str]:
        """
        Get brand of a product via HAS_BRAND edge
        
        Args:
            product: Product name
        
        Returns:
            Brand name or None if not found
        """
        brands = self.get_neighbors_by_type(product, 'brand')
        return brands[0] if brands else None
    
    def get_product_attributes(self, product: str) -> List[str]:
        """
        Get all attributes of a product via HAS_ATTRIBUTE edges
        
        Args:
            product: Product name
        
        Returns:
            List of attribute names
        """
        return self.get_neighbors_by_type(product, 'attribute')
    
    def get_related_categories(self, category: str) -> List[Tuple[str, float]]:
        """
        Get related categories via IS_SIMILAR_TO edges with weights
        
        Args:
            category: Category name
        
        Returns:
            List of (category_name, weight) tuples
        """
        if category not in self.graph:
            return []
        
        related = []
        for neighbor in self.graph.neighbors(category):
            # Check if neighbor is a category
            if self.graph.nodes[neighbor].get('type') == 'category':
                # Get edge data to retrieve weight
                edge_data = self.graph.get_edge_data(category, neighbor)
                weight = edge_data.get('weight', 0.5) if edge_data else 0.5
                related.append((neighbor, weight))
        
        return related
    
    def calculate_score(
        self,
        candidate: str,
        requested_product: str,
        category_distance: float,
        preferred_brand: Optional[str],
        max_price: float
    ) -> float:
        """
        Calculate weighted score using the formula:
        Score = w_category × (1/d_cat) + w_brand × m_brand + w_price × (1 - P_ratio)
        
        Args:
            candidate: Candidate product name
            requested_product: Original requested product
            category_distance: Distance metric (1 for same, >1 for related)
            preferred_brand: User's preferred brand (optional)
            max_price: Maximum acceptable price
        
        Returns:
            Weighted score (float)
        """
        # Get candidate properties
        cand_props = self.graph.nodes[candidate]
        cand_brand = self.get_product_brand(candidate)
        cand_price = cand_props['price']
        
        # CATEGORY SCORE: w_category × (1/d_cat)
        # Higher score for same category (d_cat = 1)
        # Lower score for related categories (d_cat > 1)
        category_score = self.W_CATEGORY * (1.0 / category_distance)
        
        # BRAND SCORE: w_brand × m_brand
        # m_brand = 1 if matches preferred brand, 0 otherwise
        brand_match = 0
        if preferred_brand and cand_brand == preferred_brand:
            brand_match = 1
        brand_score = self.W_BRAND * brand_match
        
        # PRICE SCORE: w_price × (1 - P_ratio)
        # Higher score for cheaper products
        # P_ratio = candidate_price / max_price
        price_ratio = cand_price / max_price if max_price > 0 else 0
        price_score = self.W_PRICE * (1 - price_ratio)
        
        # TOTAL SCORE
        total_score = category_score + brand_score + price_score
        return round(total_score, 2)
    
    def determine_rules(
        self,
        candidate: str,
        requested_product: str,
        same_category: bool,
        preferred_brand: Optional[str],
        required_tags: List[str]
    ) -> List[str]:
        """
        Determine which rules apply to this candidate
        
        Checks explicit conditions for each rule and returns applicable rule tags
        sorted by priority (highest priority first).
        
        Args:
            candidate: Candidate product name
            requested_product: Original requested product
            same_category: Whether candidate is in same category
            preferred_brand: User's preferred brand
            required_tags: User's required attributes
        
        Returns:
            List of rule tags in priority order
        """
        rules_applied = []
        
        # Get product details
        cand_brand = self.get_product_brand(candidate)
        req_brand = self.get_product_brand(requested_product)
        cand_attrs = set(self.get_product_attributes(candidate))
        req_price = self.product_prices.get(requested_product, 0)
        cand_price = self.graph.nodes[candidate]['price']
        
        # Check if all required tags are present
        all_tags_matched = set(required_tags).issubset(cand_attrs)
        
        # RULE 1: same_cat_same_brand (Priority 1 - Highest)
        # Same Category AND Same Brand as requested product
        if same_category and cand_brand == req_brand:
            rules_applied.append("same_cat_same_brand")
        
        # RULE 2: same_cat_all_tags (Priority 2)
        # Same Category AND All Attributes matched
        if same_category and all_tags_matched and required_tags:
            rules_applied.append("same_cat_all_tags")
        
        # RULE 3: related_cat_all_tags (Priority 3)
        # Related Category AND All Attributes matched
        if not same_category and all_tags_matched and required_tags:
            rules_applied.append("related_cat_all_tags")
        
        # RULE 4: cheaper_option (Priority 4)
        # Price ≤ 70% of requested product price
        if req_price > 0 and cand_price <= (0.7 * req_price):
            rules_applied.append("cheaper_option")
        
        # RULE 5: diff_brand_perfect_match (Priority 5)
        # Same Category, Different Brand, All tags matched
        if same_category and cand_brand != req_brand and all_tags_matched:
            rules_applied.append("diff_brand_perfect_match")
        
        # Sort by priority (lower number = higher priority)
        rules_applied.sort(key=lambda r: self.RULES[r]['priority'])
        
        return rules_applied
    
    def generate_explanation(self, rule_tags: List[str]) -> str:
        """
        Generate human-readable explanation from rule tags
        
        Uses the highest priority rule to generate the explanation.
        
        Args:
            rule_tags: List of applicable rule tags (sorted by priority)
        
        Returns:
            Human-readable explanation string
        """
        if not rule_tags:
            return "Meets your basic requirements."
        
        # Use highest priority rule (first in sorted list)
        primary_rule = rule_tags[0]
        return self.RULES[primary_rule]['explanation']
    
    def find_substitutes(
        self,
        requested_product: str,
        max_price: float,
        required_tags: List[str],
        preferred_brand: Optional[str] = None
    ) -> List[Dict]:
        """
        Multi-stage graph traversal to find product substitutes
        
        Algorithm:
        Stage 1: Check exact match (is product in stock?)
        Stage 2: Same category search (BFS from category node)
        Stage 3: Related category search (traverse IS_SIMILAR_TO edges)
        
        All candidates are filtered by A-Priori constraints:
        - in_stock = True
        - price <= max_price
        - All required tags present
        
        Returns: List of up to 3 substitutes with scores and explanations
        
        Args:
            requested_product: Name of the out-of-stock product
            max_price: Maximum acceptable price
            required_tags: List of required attributes
            preferred_brand: Optional brand preference
        
        Returns:
            List of substitute dictionaries with name, brand, price, stock, score, explanation
        """
        # Check if product exists in graph
        if requested_product not in self.graph:
            return []
        
        # STAGE 1: EXACT MATCH CHECK
        # Check if requested product is in stock
        req_props = self.graph.nodes[requested_product]
        if req_props.get('in_stock', False):
            # Product is in stock - no substitutes needed
            return []
        
        # GET REQUESTED PRODUCT DETAILS
        # Get category of requested product via IS_A edge
        req_category = self.get_product_category(requested_product)
        if not req_category:
            return []
        
        # List to store all candidate products
        candidates = []
        
        # STAGE 2: SAME CATEGORY SEARCH
        # Get all products in the same category
        same_category_products = self.get_neighbors_by_type(req_category, 'product')
        
        for product in same_category_products:
            # Skip the requested product itself
            if product == requested_product:
                continue
            
            # ----------------------------------------------------------------
            # A-PRIORI CONSTRAINT FILTERING
            # ----------------------------------------------------------------
            props = self.graph.nodes[product]
            
            # Constraint 1: Check in_stock = True
            if not props.get('in_stock', False):
                continue
            
            # Constraint 2: Check price <= max_price
            if props['price'] > max_price:
                continue
            
            # Constraint 3: Check all required attributes present
            product_attrs = set(self.get_product_attributes(product))
            if not set(required_tags).issubset(product_attrs):
                continue
            
            # ----------------------------------------------------------------
            # CALCULATE SCORE
            # ----------------------------------------------------------------
            # Category distance = 1 for same category
            score = self.calculate_score(
                product,
                requested_product,
                category_distance=1.0,
                preferred_brand=preferred_brand,
                max_price=max_price
            )
            
            # ----------------------------------------------------------------
            # DETERMINE APPLICABLE RULES
            # ----------------------------------------------------------------
            rule_tags = self.determine_rules(
                product,
                requested_product,
                same_category=True,
                preferred_brand=preferred_brand,
                required_tags=required_tags
            )
            
            # Add to candidates list
            candidates.append({
                'name': product,
                'brand': self.get_product_brand(product),
                'price': props['price'],
                'stock': props['stock'],
                'score': score,
                'category_distance': 1.0,
                'rule_tags': rule_tags,
                'explanation': self.generate_explanation(rule_tags)
            })
        
        # STAGE 3: RELATED CATEGORY SEARCH
        # Get related categories via IS_SIMILAR_TO edges
        related_categories = self.get_related_categories(req_category)
        
        for rel_cat, similarity_weight in related_categories:
            # Get all products in this related category
            related_products = self.get_neighbors_by_type(rel_cat, 'product')
            
            for product in related_products:
                # ----------------------------------------------------------------
                # A-PRIORI CONSTRAINT FILTERING
                # ----------------------------------------------------------------
                props = self.graph.nodes[product]
                
                # Constraint 1: in_stock = True
                if not props.get('in_stock', False):
                    continue
                
                # Constraint 2: price <= max_price
                if props['price'] > max_price:
                    continue
                
                # Constraint 3: all required attributes present
                product_attrs = set(self.get_product_attributes(product))
                if not set(required_tags).issubset(product_attrs):
                    continue
                
                # ----------------------------------------------------------------
                # CALCULATE CATEGORY DISTANCE
                # ----------------------------------------------------------------
                # Category distance = inverse of similarity weight
                # Higher weight = more similar = lower distance
                category_distance = 1.0 / similarity_weight if similarity_weight > 0 else 2.0
                
                # ----------------------------------------------------------------
                # CALCULATE SCORE
                # ----------------------------------------------------------------
                score = self.calculate_score(
                    product,
                    requested_product,
                    category_distance=category_distance,
                    preferred_brand=preferred_brand,
                    max_price=max_price
                )
                
                # ----------------------------------------------------------------
                # DETERMINE APPLICABLE RULES
                # ----------------------------------------------------------------
                rule_tags = self.determine_rules(
                    product,
                    requested_product,
                    same_category=False,
                    preferred_brand=preferred_brand,
                    required_tags=required_tags
                )
                
                # Add to candidates list
                candidates.append({
                    'name': product,
                    'brand': self.get_product_brand(product),
                    'price': props['price'],
                    'stock': props['stock'],
                    'score': score,
                    'category_distance': category_distance,
                    'rule_tags': rule_tags,
                    'explanation': self.generate_explanation(rule_tags)
                })
        
        # SORT AND RETURN TOP 3
        # Sort by score (descending) and return top 3
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[:3]
    
    def check_exact_match(self, product: str) -> bool:
        """
        Check if product is in stock (Stage 1)
        
        Args:
            product: Product name
        
        Returns:
            True if product exists and is in stock, False otherwise
        """
        if product not in self.graph:
            return False
        return self.graph.nodes[product].get('in_stock', False)
    
    def get_product_details(self, product: str) -> Optional[Dict]:
        """
        Get all details of a product
        
        Args:
            product: Product name
        
        Returns:
            Dictionary with product details or None if not found
        """
        if product not in self.graph:
            return None
        
        # Copy node properties
        props = self.graph.nodes[product].copy()
        
        # Add related information
        props['category'] = self.get_product_category(product)
        props['brand'] = self.get_product_brand(product)
        props['attributes'] = self.get_product_attributes(product)
        
        return props

