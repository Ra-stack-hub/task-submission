import os
import sys
from backend.app.recommender import OccasionRecommender

def run_tests():
    print("=" * 60)
    print("RUNNING UNIT TESTS FOR OCCASION RECOMMENDATION ENGINE")
    print("=" * 60)
    
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "backend", "products.json")
    
    if not os.path.exists(data_path):
        print(f"Error: product data file not found at: {data_path}")
        print("Make sure you run tests from the project root directory.")
        sys.exit(1)
        
    print(f"Loading database from {data_path}...")
    try:
        recommender = OccasionRecommender(data_path)
        print("[SUCCESS] Database Loaded successfully.")
    except Exception as e:
        print(f"[ERROR] Loading failed: {str(e)}")
        sys.exit(1)
        
    print("-" * 60)
    print(f"Loaded {len(recommender.products)} products.")
    print(f"Indexed vocabulary size: {len(recommender.idf)} terms.")
    assert len(recommender.products) > 0, "No products loaded!"
    assert len(recommender.idf) > 0, "Recommender vocabulary is empty!"
    print("[SUCCESS] Catalog parsing & indexing asserted successfully.")
    
    print("-" * 60)
    print("Testing recommendations for 'wedding':")
    results = recommender.recommend("wedding", top_n=5)
    print(f"Found {len(results)} matches.")
    for idx, r in enumerate(results):
        print(f"  {idx+1}. [{r['match_score']}% Match] {r['title']} | Category: {r['vendor_category_desc']}")
        print(f"     Matched tags: {r['matched_terms']}")
        
    assert len(results) > 0, "No recommendations returned for 'wedding'!"
    print("[SUCCESS] Recommendation results asserted successfully.")
    
    print("-" * 60)
    print("Testing autocomplete suggestions for 'birth':")
    suggestions = recommender.get_auto_suggestions("birth")
    print(f"Suggestions found: {suggestions}")
    assert len(suggestions) > 0, "No autocomplete suggestions returned for 'birth'!"
    print("[SUCCESS] Autocomplete suggestions asserted successfully.")
    
    print("-" * 60)
    print("Testing fallback/empty state logic for non-existent category 'quantum physics':")
    empty_results = recommender.recommend("quantum physics")
    print(f"Found {len(empty_results)} matches.")
    assert len(empty_results) == 0, f"Expected 0 matches, found {len(empty_results)}!"
    print("[SUCCESS] Empty state filtering asserted successfully.")
    
    print("=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! THE ENGINE IS READY FOR PRODUCTION.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
