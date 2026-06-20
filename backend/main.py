import os
import sys

# Resolve paths and insert them into sys.path to prevent ModuleNotFoundError
# when running from different working directories or as a module/package
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
PARENT_DIR = os.path.dirname(BASE_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.recommender import OccasionRecommender, OCCASION_EXPANSIONS

DATA_FILE_PATH = os.path.join(BASE_DIR, "products.json")
FRONTEND_DIR = os.path.join(PARENT_DIR, "frontend")

# Ensure frontend directory exists
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Initialize recommender (None at startup, will load on startup event)
recommender = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global recommender
    try:
        if not os.path.exists(DATA_FILE_PATH):
            # Fallback path check if running from parent directory
            parent_data_path = os.path.join(os.path.dirname(BASE_DIR), "backend", "products.json")
            if os.path.exists(parent_data_path):
                recommender = OccasionRecommender(parent_data_path)
            else:
                raise FileNotFoundError(f"products.json not found at {DATA_FILE_PATH}")
        else:
            recommender = OccasionRecommender(DATA_FILE_PATH)
        print(f"Recommender index loaded successfully with {len(recommender.products)} products.")
    except Exception as e:
        print(f"Error loading recommender on startup: {str(e)}")
    yield

app = FastAPI(
    title="Occasion-Based Product Recommendation API",
    description="Intelligent search and recommendation system for occasions",
    version="1.0.0",
    lifespan=lifespan
)


# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/recommend")
def get_recommendations(
    occasion: str = Query(..., description="The occasion to match products against"),
    limit: int = Query(12, ge=1, le=50, description="Max number of products to return")
):
    if not recommender:
        raise HTTPException(status_code=503, detail="Recommendation engine is not initialized.")
    
    start_time = time.perf_counter()
    try:
        recommendations = recommender.recommend(occasion, top_n=limit)
        execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        
        # Extract metadata about the match (accumulate all expanded terms to match recommender engine)
        query_expanded = []
        occasion_lower = occasion.lower()
        for key, synonyms in OCCASION_EXPANSIONS.items():
            if key in occasion_lower:
                query_expanded.extend(synonyms)

        return {
            "status": "success",
            "query": occasion,
            "query_tokens_analyzed": list(set(query_expanded) if query_expanded else occasion.lower().split()),
            "execution_time_ms": execution_time_ms,
            "total_results": len(recommendations),
            "results": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Recommendation Error: {str(e)}")

@app.get("/api/suggestions")
def get_suggestions(
    q: str = Query(..., description="Prefix to autocomplete")
):
    if not recommender:
        return []
    try:
        return recommender.get_auto_suggestions(q, limit=6)
    except Exception as e:
        return []

@app.get("/api/stats")
def get_stats():
    if not recommender:
        raise HTTPException(status_code=503, detail="Recommendation engine is not initialized.")
    
    # Calculate some cool statistics for the developer panel
    unique_categories = set(p["vendor_category_desc"] for p in recommender.products)
    total_images = sum(1 for p in recommender.products if p["files"])
    total_vocab = len(recommender.idf)
    
    return {
        "total_products": len(recommender.products),
        "total_categories": len(unique_categories),
        "vocabulary_size": total_vocab,
        "products_with_images": total_images,
        "active_occasions_supported": list(OCCASION_EXPANSIONS.keys())
    }

# Fallback root route to serve index.html directly before mounting static files
@app.get("/")
def read_root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Occasion Recommendation Engine API is running. Build front-end inside frontend/ to view index.html."}

# Mount static files directory
# Note: we mount it at '/static' so that CSS/JS/Images can be served from '/static/styles.css', etc.
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    # Run server with correct app_dir so reload works from any working directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, app_dir=current_dir)

