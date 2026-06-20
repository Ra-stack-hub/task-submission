import json
import math
import os
import re
import numpy as np
from typing import List, Dict, Any, Tuple

# Hardcoded set of English stop words to ensure zero external dependency.
STOP_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'arent', 'as', 'at',
    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'cant', 'cannot', 'could',
    'couldnt', 'did', 'didnt', 'do', 'does', 'doesnt', 'doing', 'dont', 'down', 'during', 'each', 'few', 'for', 'from',
    'further', 'had', 'hadnt', 'has', 'hasnt', 'have', 'havent', 'having', 'he', 'hed', 'hell', 'hes', 'her', 'here',
    'heres', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'hows', 'i', 'id', 'ill', 'im', 'ive', 'if', 'in',
    'into', 'is', 'isnt', 'it', 'its', 'itself', 'lets', 'me', 'more', 'most', 'mustnt', 'my', 'myself', 'no', 'nor',
    'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own',
    'same', 'shant', 'she', 'shed', 'shell', 'shes', 'should', 'shouldnt', 'so', 'some', 'such', 'than', 'that', 'thats',
    'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'theres', 'these', 'they', 'theyd', 'theyll',
    'theyre', 'theyve', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'wasnt', 'we',
    'wed', 'well', 'were', 'weve', 'werent', 'what', 'whats', 'when', 'whens', 'where', 'wheres', 'which', 'while',
    'who', 'whos', 'whom', 'why', 'whys', 'with', 'wont', 'would', 'wouldnt', 'you', 'youd', 'youll', 'youre', 'youve',
    'your', 'yours', 'yourself', 'yourselves'
}

# Mapping of popular occasions to semantically related keywords to expand the query vector.
# This simulates semantic understanding without requiring heavy embedding models.
OCCASION_EXPANSIONS: Dict[str, List[str]] = {
    "wedding": [
        "wedding", "marriage", "anniversary", "bride", "groom", "ceremony", "couple", "love", 
        "gift", "celebration", "bridal", "romance", "party", "reception", "suit", "dress", "gold", 
        "decor", "silver", "sweet", "toast", "jewelry", "flowers", "invitation", "atelier"
    ],
    "marriage": [
        "wedding", "marriage", "anniversary", "bride", "groom", "ceremony", "couple", "love", 
        "gift", "celebration", "bridal", "romance", "party", "reception", "suit", "dress", "gold", 
        "decor", "silver", "sweet", "toast", "jewelry", "flowers"
    ],
    "anniversary": [
        "anniversary", "wedding", "marriage", "couple", "love", "romance", "gift", "celebration", 
        "chocolate", "roses", "flowers", "gold", "silver", "candlelight", "wine", "card", "memories"
    ],
    "birthday": [
        "birthday", "cake", "candles", "gift", "party", "celebration", "balloons", "wish", "surprise", 
        "present", "fun", "kid", "friend", "happy", "sweet", "treat", "wrapping", "box", "card", "chocolates"
    ],
    "diwali": [
        "diwali", "deepavali", "festival", "festive", "diya", "lights", "sweet", "gift", "celebration", 
        "ethnic", "decor", "clay", "puja", "prosperity", "gold", "traditional", "mithai", "dryfruit", "hampers"
    ],
    "valentine": [
        "valentine", "valentines", "romance", "love", "chocolate", "rose", "gift", "date", "heart", 
        "flower", "red", "sweetheart", "couple", "candlelight", "luxury", "perfume", "jewelry", "card"
    ],
    "office party": [
        "office", "corporate", "party", "colleague", "work", "meeting", "celebration", "gathering", 
        "team", "gift", "professional", "snack", "drink", "mug", "notebook", "desk", "coffee", "pen", "organizer"
    ],
    "corporate": [
        "office", "corporate", "party", "colleague", "work", "meeting", "celebration", "gathering", 
        "team", "gift", "professional", "snack", "drink", "mug", "notebook", "desk", "coffee", "pen", "organizer"
    ],
    "christmas": [
        "christmas", "xmas", "santa", "winter", "holiday", "gift", "tree", "decor", "bell", "sweet", 
        "cookie", "snow", "festive", "celebration", "red", "green", "carol", "socks", "chocolate", "wrapping"
    ],
    "baby shower": [
        "baby", "shower", "born", "infant", "mother", "parent", "toy", "cute", "kid", "gift", "diaper", 
        "nursery", "soft", "sweet", "clothes", "blanket", "cradle"
    ],
    "housewarming": [
        "house", "home", "warming", "new home", "decor", "kitchen", "gift", "candle", "plant", 
        "living room", "rug", "cup", "welcome", "frame", "vase", "cozy"
    ],
    "graduation": [
        "graduation", "grad", "degree", "success", "future", "gift", "congratulations", "party", 
        "pen", "book", "journal", "frame", "watch", "career"
    ],
    "halloween": [
        "halloween", "spooky", "scary", "ghost", "witch", "pumpkin", "candy", "costume", "party", 
        "october", "dark", "fun", "trick"
    ]
}

def clean_and_tokenize(text: str) -> List[str]:
    """Lowercases, removes punctuation, tokenizes by whitespace, and filters stop words."""
    if not text:
        return []
    # Lowercase and replace punctuation/special chars with a space
    text = text.lower()
    text = re.sub(r'[^\w\s\-]', ' ', text)  # Keep hyphens for potential compound words
    tokens = text.split()
    
    # Filter out stop words and single-letter junk tokens (unless they are numbers)
    return [t for t in tokens if t not in STOP_WORDS and (len(t) > 1 or t.isdigit())]

class OccasionRecommender:
    def __init__(self, data_file_path: str):
        self.data_file_path = data_file_path
        self.products: List[Dict[str, Any]] = []
        self.processed_docs: List[List[str]] = []
        self.idf: Dict[str, float] = {}
        self.product_vectors: List[Dict[str, float]] = []
        self.product_norms: List[float] = []
        self.product_embeddings: List[List[float]] = []
        
        # Load SentenceTransformer model
        from sentence_transformers import SentenceTransformer
        print("Loading SentenceTransformer model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("SentenceTransformer model loaded.")
        
        self.load_and_index_products()
        self.load_or_generate_embeddings()

    def load_or_generate_embeddings(self):
        """Loads product semantic embeddings from disk cache, or generates them if needed."""
        cache_path = os.path.join(os.path.dirname(self.data_file_path), "embeddings_cache.json")
        
        # Helper to compute file hash
        import hashlib
        hasher = hashlib.sha256()
        with open(self.data_file_path, 'rb') as f:
            hasher.update(f.read())
        current_hash = hasher.hexdigest()
        
        loaded_from_cache = False
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                if cache_data.get("sha256") == current_hash:
                    self.product_embeddings = cache_data.get("embeddings", [])
                    if len(self.product_embeddings) == len(self.products):
                        print("Loaded product embeddings from disk cache.")
                        loaded_from_cache = True
            except Exception as e:
                print(f"Failed to load embeddings cache: {str(e)}")
                
        if not loaded_from_cache:
            print("Generating product vector embeddings (this may take a few seconds on first boot)...")
            texts = []
            for p in self.products:
                texts.append(f"{p['title']} - {p['vendor_category_desc']}. {p['description']}")
            
            embeddings_tensors = self.model.encode(texts, convert_to_tensor=True)
            if hasattr(embeddings_tensors, "tolist"):
                self.product_embeddings = embeddings_tensors.tolist()
            else:
                self.product_embeddings = [x.tolist() if hasattr(x, "tolist") else list(x) for x in embeddings_tensors]
                
            try:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump({"sha256": current_hash, "embeddings": self.product_embeddings}, f)
                print("Computed and cached new product vector embeddings.")
            except Exception as e:
                print(f"Failed to write embeddings cache: {str(e)}")

    def normalize_product(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Maps varying input JSON schemas (PDF spec vs local products.json) to a consistent structure."""
        # Product ID
        product_id = payload.get("product_id") or payload.get("productId") or payload.get("id")
        
        # Vendor / Brand
        vendor_id = payload.get("vendor_id") or payload.get("vendorId") or payload.get("shopId") or payload.get("brand") or "Unknown Vendor"
        
        # Categories
        vendor_category = payload.get("vendor_category") or payload.get("categoryId") or "General"
        vendor_category_desc = payload.get("vendor_category_desc") or payload.get("brand") or "Products Catalog"
        
        # Title & Description
        title = payload.get("title") or payload.get("name") or "Unnamed Product"
        description = payload.get("description") or payload.get("shortDescription") or ""
        
        # Price and Stock (Useful metadata to display in cards!)
        price = payload.get("price", "N/A")
        
        # Files (Images) array
        files = payload.get("files")
        if not files:
            main_image = payload.get("mainImage")
            files = [main_image] if main_image else []
        elif isinstance(files, str):
            files = [files]
            
        return {
            "product_id": str(product_id),
            "vendor_id": str(vendor_id),
            "vendor_category": str(vendor_category),
            "vendor_category_desc": str(vendor_category_desc),
            "title": title,
            "description": description,
            "price": price,
            "files": files
        }

    def load_and_index_products(self):
        """Loads products from the JSON catalog, normalizes fields, and builds the TF-IDF search index."""
        if not os.path.exists(self.data_file_path):
            raise FileNotFoundError(f"Product data catalog file not found at {self.data_file_path}")
            
        with open(self.data_file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
        # Parse elements
        raw_list = raw_data if isinstance(raw_data, list) else list(raw_data.values())
        self.products = [self.normalize_product(item) for item in raw_list]
        
        # Prepare tokens for TF-IDF indexing
        self.processed_docs = []
        for p in self.products:
            # We construct a weighted document:
            # Title tokens are repeated 3 times to give high search relevance.
            # Category description tokens are repeated 2 times.
            # Description tokens are included 1 time.
            title_tokens = clean_and_tokenize(p["title"]) * 3
            category_tokens = clean_and_tokenize(p["vendor_category_desc"]) * 2
            desc_tokens = clean_and_tokenize(p["description"])
            
            combined_tokens = title_tokens + category_tokens + desc_tokens
            self.processed_docs.append(combined_tokens)
            
        # Calculate IDF (Inverse Document Frequency)
        total_docs = len(self.products)
        doc_frequencies: Dict[str, int] = {}
        
        for doc in self.processed_docs:
            unique_terms = set(doc)
            for term in unique_terms:
                doc_frequencies[term] = doc_frequencies.get(term, 0) + 1
                
        # IDF smoothing formula (equivalent to scikit-learn standard)
        self.idf = {}
        for term, df in doc_frequencies.items():
            self.idf[term] = math.log(1.0 + (total_docs / (1.0 + df))) + 1.0
            
        # Precompute TF-IDF vectors for all products
        self.product_vectors = []
        self.product_norms = []
        
        for doc in self.processed_docs:
            if not doc:
                self.product_vectors.append({})
                self.product_norms.append(0.0)
                continue
                
            # Compute Term Frequencies (TF = term_count / doc_len)
            doc_len = len(doc)
            tf_counts: Dict[str, int] = {}
            for term in doc:
                tf_counts[term] = tf_counts.get(term, 0) + 1
                
            # Compute TF-IDF weights
            vector = {}
            squared_sum = 0.0
            for term, count in tf_counts.items():
                tf = count / doc_len
                tfidf_val = tf * self.idf.get(term, 0.0)
                vector[term] = tfidf_val
                squared_sum += tfidf_val ** 2
                
            self.product_vectors.append(vector)
            self.product_norms.append(math.sqrt(squared_sum))

    def recommend(self, occasion_query: str, top_n: int = 15) -> List[Dict[str, Any]]:
        """
        Accepts an occasion string, matches it against catalog products using 
        synonym expansions and hybrid TF-IDF / semantic vector search, and returns ranked results.
        """
        if not occasion_query or not self.products:
            return []
            
        # Clean and tokenize the user query
        query_tokens = clean_and_tokenize(occasion_query)
        if not query_tokens:
            return []
            
        # Semantic Expansion: Check if query contains any of the known occasions.
        # If so, expand the query tokens to boost recall and semantic relevance.
        expanded_tokens = list(query_tokens)
        expansion_source = []
        
        # Check for phrase or word overlaps in our occasion expansion dictionary
        query_lower = occasion_query.lower()
        for key_occasion, synonyms in OCCASION_EXPANSIONS.items():
            if key_occasion in query_lower:
                # Add synonyms that are not already in query
                expansion_source.append(key_occasion)
                for syn in synonyms:
                    if syn not in expanded_tokens:
                        # Add synonym multiple times depending on core relevance
                        # To keep it balanced, we append it once
                        expanded_tokens.append(syn)
                        
        # Count term frequencies in query
        query_tf: Dict[str, int] = {}
        for token in expanded_tokens:
            # Boost core query tokens over expansion tokens
            weight = 3 if token in query_tokens else 1
            query_tf[token] = query_tf.get(token, 0) + weight
            
        # Compute query vector
        query_vector = {}
        query_squared_sum = 0.0
        query_len = sum(query_tf.values())
        
        for term, count in query_tf.items():
            if term in self.idf:
                tf = count / query_len
                tfidf_val = tf * self.idf[term]
                query_vector[term] = tfidf_val
                query_squared_sum += tfidf_val ** 2
                
        query_norm = math.sqrt(query_squared_sum)
        
        # Compute Semantic Cosine Similarity using SentenceTransformers
        query_emb = np.array(self.model.encode(occasion_query), dtype=np.float32)
        product_embs = np.array(self.product_embeddings, dtype=np.float32)
        
        dot_products = np.dot(product_embs, query_emb)
        product_norms = np.linalg.norm(product_embs, axis=1)
        query_norm_val = np.linalg.norm(query_emb)
        
        denom = product_norms * query_norm_val
        semantic_similarities = np.where(denom > 0, dot_products / denom, 0.0)
        
        results = []
        
        for idx, p_vector in enumerate(self.product_vectors):
            p_norm = self.product_norms[idx]
            keyword_similarity = 0.0
            matched_terms = []
            
            if p_norm > 0.0 and query_norm > 0.0:
                dot_product = 0.0
                for term, q_val in query_vector.items():
                    if term in p_vector:
                        dot_product += q_val * p_vector[term]
                        matched_terms.append(term)
                keyword_similarity = dot_product / (query_norm * p_norm)
                
            semantic_similarity = float(semantic_similarities[idx])
            
            # Combine scores: 70% Semantic, 30% Keyword
            hybrid_similarity = 0.7 * semantic_similarity + 0.3 * keyword_similarity
            
            # Boost score if the raw occasion string is found directly as a substring in the title
            raw_title_lower = self.products[idx]["title"].lower()
            for token in query_tokens:
                if token in raw_title_lower:
                    hybrid_similarity += 0.15  # 15% bonus for direct title match
                    break
                    
            # Cap similarity at 1.0 (100%) and clamp minimum to 0.0
            hybrid_similarity = max(0.0, min(hybrid_similarity, 1.0))
            match_percentage = round(hybrid_similarity * 100, 1)
            
            # Filter out low relevance matches (e.g. less than 3% match score)
            # Also filter out weak semantic-only matches with no keyword overlap to avoid false positives (e.g. 'quantum physics')
            if keyword_similarity == 0.0 and semantic_similarity < 0.25:
                pass
            elif match_percentage > 3.0:
                results.append((
                    match_percentage, 
                    semantic_similarity,
                    keyword_similarity,
                    self.products[idx], 
                    matched_terms
                ))
                
        # Sort results by similarity score descending, then by title
        results.sort(key=lambda x: (-x[0], x[3]["title"]))
        
        # Format response payload
        formatted_results = []
        for score, sem_score, key_score, product, matches in results[:top_n]:
            # Construct a snippet of description (up to 150 chars)
            desc = product["description"]
            desc_snippet = desc[:150] + "..." if len(desc) > 150 else desc
            
            formatted_results.append({
                "product_id": product["product_id"],
                "vendor_id": product["vendor_id"],
                "vendor_category": product["vendor_category"],
                "vendor_category_desc": product["vendor_category_desc"],
                "title": product["title"],
                "description_snippet": desc_snippet,
                "full_description": desc,
                "price": product["price"],
                "files": product["files"],
                "match_score": score,
                "semantic_score": round(sem_score * 100, 1),
                "keyword_score": round(key_score * 100, 1),
                "matched_terms": matches
            })
            
        return formatted_results

    def get_auto_suggestions(self, prefix: str, limit: int = 5) -> List[str]:
        """Provides autocomplete suggestions based on both indexed product titles/categories and popular occasions."""
        prefix_clean = prefix.lower().strip()
        if not prefix_clean:
            return []
            
        suggestions = set()
        
        # 1. First check popular occasions from expansions
        for occasion in OCCASION_EXPANSIONS.keys():
            if occasion.startswith(prefix_clean) or prefix_clean in occasion:
                suggestions.add(occasion.title())
                if len(suggestions) >= limit:
                    return list(suggestions)
                    
        # 2. Check product titles and categories
        for p in self.products:
            title = p["title"]
            category = p["vendor_category_desc"]
            
            if prefix_clean in title.lower():
                # Extract a neat phrase or just return title
                suggestions.add(title)
            elif prefix_clean in category.lower():
                suggestions.add(category)
                
            if len(suggestions) >= limit:
                break
                
        return list(suggestions)[:limit]
