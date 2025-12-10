import networkx as nx
import json
from typing import List, Dict, Optional, Tuple


class KnowledgeGraph:
    """
    Knowledge Graph for Product Substitution System
    
    Implements multi-stage traversal with weighted scoring and rule-based explanations.
    No ML, embeddings, or AI - pure graph algorithms and classical reasoning.
    """
    
    # Scoring weights (as per requirements)
    W_CATEGORY = 10
    W_BRAND = 5
    W_PRICE = 1
    
    # Rule priorities and explanations
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
        """Initialize Knowledge Graph from JSON data file"""
        self.graph = nx.Graph()
        self.product_prices = {}  # Store original prices for comparison
        self.load_data(data_file)
    
    def load_data(self, data_file: str) -> None:
        """
        Build Knowledge Graph from JSON data
        
        Nodes: Product, Category, Brand, Attribute
        Edges: IS_A, HAS_BRAND, HAS_ATTRIBUTE, IS_SIMILAR_TO
        """
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add Product nodes with properties
        for p in data['products']:
            self.graph.add_node(
                p['name'],
                type='product',
                price=p['price'],
                stock=p['stock'],
                id=p['id'],
                in_stock=(p['stock'] > 0)
            )
            self.product_prices[p['name']] = p['price']
            
            # Add Category nodes
            if not self.graph.has_node(p['category']):
                self.graph.add_node(p['category'], type='category')
            
            # Add Brand nodes
            if not self.graph.has_node(p['brand']):
                self.graph.add_node(p['brand'], type='brand')
            
            # Add edges: IS_A (Product -> Category)
            self.graph.add_edge(p['name'], p['category'], relation='IS_A')
            
            # Add edges: HAS_BRAND (Product -> Brand)
            self.graph.add_edge(p['name'], p['brand'], relation='HAS_BRAND')
            
            # Add Attribute nodes and HAS_ATTRIBUTE edges
            for attr in p['attributes']:
                if not self.graph.has_node(attr):
                    self.graph.add_node(attr, type='attribute')
                self.graph.add_edge(p['name'], attr, relation='HAS_ATTRIBUTE')
        
        # Add IS_SIMILAR_TO edges between categories (with weights)
        if 'category_relations' in data:
            for rel in data['category_relations']:
                self.graph.add_edge(
                    rel['source'],
                    rel['target'],
                    relation='IS_SIMILAR_TO',
                    weight=rel.get('weight', 0.5)
                )
    
    def get_neighbors_by_type(self, node: str, node_type: str) -> List[str]:
        """Get all neighboring nodes of a specific type"""
        if node not in self.graph:
            return []
        return [
            n for n in self.graph.neighbors(node)
            if self.graph.nodes[n].get('type') == node_type
        ]
    
    def get_product_category(self, product: str) -> Optional[str]:
        """Get category of a product via IS_A edge"""
        categories = self.get_neighbors_by_type(product, 'category')
        return categories[0] if categories else None
    
    def get_product_brand(self, product: str) -> Optional[str]:
        """Get brand of a product via HAS_BRAND edge"""
        brands = self.get_neighbors_by_type(product, 'brand')
        return brands[0] if brands else None
    
    def get_product_attributes(self, product: str) -> List[str]:
        """Get all attributes of a product via HAS_ATTRIBUTE edges"""
        return self.get_neighbors_by_type(product, 'attribute')
    
    def get_related_categories(self, category: str) -> List[Tuple[str, float]]:
        """
        Get related categories via IS_SIMILAR_TO edges with weights
        Returns list of (category_name, weight) tuples
        """
        if category not in self.graph:
            return []
        
        related = []
        for neighbor in self.graph.neighbors(category):
            if self.graph.nodes[neighbor].get('type') == 'category':
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
        cand_props = self.graph.nodes[candidate]
        cand_brand = self.get_product_brand(candidate)
        cand_price = cand_props['price']
        
        # Category score: w_category × (1/d_cat)
        category_score = self.W_CATEGORY * (1.0 / category_distance)
        
        # Brand score: w_brand × m_brand
        brand_match = 0
        if preferred_brand and cand_brand == preferred_brand:
            brand_match = 1
        brand_score = self.W_BRAND * brand_match
        
        # Price score: w_price × (1 - P_ratio)
        price_ratio = cand_price / max_price if max_price > 0 else 0
        price_score = self.W_PRICE * (1 - price_ratio)
        
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
        
        Returns list of rule tags in priority order
        """
        rules_applied = []
        
        cand_brand = self.get_product_brand(candidate)
        req_brand = self.get_product_brand(requested_product)
        cand_attrs = set(self.get_product_attributes(candidate))
        req_price = self.product_prices.get(requested_product, 0)
        cand_price = self.graph.nodes[candidate]['price']
        
        all_tags_matched = set(required_tags).issubset(cand_attrs)
        
        # Rule: same_cat_same_brand
        if same_category and cand_brand == req_brand:
            rules_applied.append("same_cat_same_brand")
        
        # Rule: same_cat_all_tags
        if same_category and all_tags_matched and required_tags:
            rules_applied.append("same_cat_all_tags")
        
        # Rule: related_cat_all_tags
        if not same_category and all_tags_matched and required_tags:
            rules_applied.append("related_cat_all_tags")
        
        # Rule: cheaper_option (≤ 70% of requested price)
        if req_price > 0 and cand_price <= (0.7 * req_price):
            rules_applied.append("cheaper_option")
        
        # Rule: diff_brand_perfect_match
        if same_category and cand_brand != req_brand and all_tags_matched:
            rules_applied.append("diff_brand_perfect_match")
        
        # Sort by priority
        rules_applied.sort(key=lambda r: self.RULES[r]['priority'])
        
        return rules_applied
    
    def generate_explanation(self, rule_tags: List[str]) -> str:
        """Generate human-readable explanation from rule tags"""
        if not rule_tags:
            return "Meets your basic requirements."
        
        # Use highest priority rule
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
        
        Stage 1: Check exact match
        Stage 2: Same category search
        Stage 3: Related category search
        
        Returns: List of up to 3 substitutes with scores and explanations
        """
        if requested_product not in self.graph:
            return []
        
        # Stage 1: Exact Match Check
        req_props = self.graph.nodes[requested_product]
        if req_props.get('in_stock', False):
            # Product is in stock - no substitutes needed
            return []
        
        # Get requested product details
        req_category = self.get_product_category(requested_product)
        if not req_category:
            return []
        
        candidates = []
        
        # Stage 2: Same Category Search
        same_category_products = self.get_neighbors_by_type(req_category, 'product')
        
        for product in same_category_products:
            if product == requested_product:
                continue
            
            # A-priori constraint filtering
            props = self.graph.nodes[product]
            
            # Check: in_stock = True
            if not props.get('in_stock', False):
                continue
            
            # Check: price <= max_price
            if props['price'] > max_price:
                continue
            
            # Check: all required attributes present
            product_attrs = set(self.get_product_attributes(product))
            if not set(required_tags).issubset(product_attrs):
                continue
            
            # Calculate score (category_distance = 1 for same category)
            score = self.calculate_score(
                product,
                requested_product,
                category_distance=1.0,
                preferred_brand=preferred_brand,
                max_price=max_price
            )
            
            # Determine applicable rules
            rule_tags = self.determine_rules(
                product,
                requested_product,
                same_category=True,
                preferred_brand=preferred_brand,
                required_tags=required_tags
            )
            
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
        
        # Stage 3: Related Category Search
        related_categories = self.get_related_categories(req_category)
        
        for rel_cat, similarity_weight in related_categories:
            related_products = self.get_neighbors_by_type(rel_cat, 'product')
            
            for product in related_products:
                # A-priori constraint filtering
                props = self.graph.nodes[product]
                
                if not props.get('in_stock', False):
                    continue
                
                if props['price'] > max_price:
                    continue
                
                product_attrs = set(self.get_product_attributes(product))
                if not set(required_tags).issubset(product_attrs):
                    continue
                
                # Calculate category distance (inverse of similarity weight)
                category_distance = 1.0 / similarity_weight if similarity_weight > 0 else 2.0
                
                # Calculate score
                score = self.calculate_score(
                    product,
                    requested_product,
                    category_distance=category_distance,
                    preferred_brand=preferred_brand,
                    max_price=max_price
                )
                
                # Determine applicable rules
                rule_tags = self.determine_rules(
                    product,
                    requested_product,
                    same_category=False,
                    preferred_brand=preferred_brand,
                    required_tags=required_tags
                )
                
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
        
        # Sort by score (descending) and return top 3
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[:3]
    
    def check_exact_match(self, product: str) -> bool:
        """Check if product is in stock (Stage 1)"""
        if product not in self.graph:
            return False
        return self.graph.nodes[product].get('in_stock', False)
    
    def get_product_details(self, product: str) -> Optional[Dict]:
        """Get all details of a product"""
        if product not in self.graph:
            return None
        
        props = self.graph.nodes[product].copy()
        props['category'] = self.get_product_category(product)
        props['brand'] = self.get_product_brand(product)
        props['attributes'] = self.get_product_attributes(product)
        
        return props
