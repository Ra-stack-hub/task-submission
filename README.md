Occasion-Based Product Recommendation System
Overview

This project is an AI-powered Occasion-Based Product Recommendation System that recommends relevant products based on user-entered occasions such as Birthday, Wedding, Anniversary, Diwali, Valentine's Day, Office Party, Housewarming, and more.

The system analyzes product information from the provided product catalog and ranks products according to their relevance to the selected occasion.

---

## 📋 Table of Contents
- [1. Overview](#1-overview)
- [2. Product Data Structure](#2-product-data-structure)
- [3. Task Requirements & Core Functionality](#3-task-requirements--core-functionality)
- [4. Recommendation Engine Architecture & Logic](#4-recommendation-engine-architecture--logic)
- [5. Technical Design Decisions & Rationale](#5-technical-design-decisions--rationale)
- [6. Project Directory Structure](#6-project-directory-structure)
- [7. Tech Stack](#7-tech-stack)
- [8. Getting Started & Local Setup](#8-getting-started--local-setup)
- [9. API Documentation](#9-api-documentation)
- [10. Running the Test Suite](#10-running-the-test-suite)
- [11. Submission Deliverables & Screenshots](#11-submission-deliverables--screenshots)
- [12. Citations & AI Tools Usage](#12-citations--ai-tools-usage)

---

## 1. Overview
The goal of this system is to ingest a product catalog and intelligently recommend relevant products matching a user-specified occasion (e.g., *Wedding, Birthday, Diwali, Valentine's Day, Office Party*). It demonstrates how to combine semantic understanding with traditional search techniques to achieve fast, high-recall recommendations that work seamlessly in real-world environments.

---

## 2. Product Data Structure
The application processes a product database with support for varying fields and schemas. The engine normalizes fields using a schema mapper implemented in [recommender.py](file:///c:/Users/raksh/OneDrive/Documents/Desktop/task%20submission/backend/app/recommender.py#L158-L194).

| Field | Type | Description |
| :--- | :--- | :--- |
| `product_id` / `productId` | `string`/`int` | Unique product identifier |
| `vendor_id` / `vendorId` | `string` | Brand or vendor who listed the product |
| `vendor_category` | `string` | Category slug/code assigned by vendor |
| `vendor_category_desc` | `string` | Human-readable category description |
| `title` | `string` | Product name (defaults to empty string) |
| `description` | `string` | Detailed product description |
| `files` | `array` | Product images/media file paths |

The extraction logic gracefully handles standard catalog fields as well as fallback attributes (e.g., mapping `name` to `title`, `shortDescription` to `description`, `mainImage` to `files` array, etc.).

---

## 3. Task Requirements & Core Functionality
The system fully satisfies all requirements detailed in the take-home assignment:
1. **Occasion Input**: Accepts free-form text input or quick-search pills (e.g., Birthday, Wedding, Diwali, Valentine, Office Party, Baby Shower, Housewarming).
2. **Relevance Computation**: Compares catalog items against the occasion using a combined NLP pipeline.
3. **Ranked Recommendations**: Outputs and displays a list of recommendations, ordered by match relevance, directly below the search bar without reloading the page.
4. **Rich Cards**: Each product card displays the Title, Category description, Description snippet, Price, and the corresponding Product Image (with a smooth glassmorphic hover effect and load-failure placeholders).
5. **No Matches State**: Renders a dedicated clean empty state if no products match the query (e.g., "quantum physics").
6. **Autocomplete Suggestions**: Provides real-time matching suggestions as the user types.

---

## 4. Recommendation Engine Architecture & Logic
The NLP pipeline in [recommender.py](file:///c:/Users/raksh/OneDrive/Documents/Desktop/task%20submission/backend/app/recommender.py) operates in four main stages to score products:

### Phase 1: Text Cleaning & Tokenization
Both product attributes and search queries are cleaned by:
- Lowercasing all characters.
- Removing punctuation/special characters (preserving hyphens).
- Filtering out standard English stop words (e.g., *the*, *and*, *with*, *for*) to focus strictly on content words.

### Phase 2: Occasion Synonym Expansion (Semantic Booster)
If the query contains one of the predefined key occasions, it triggers synonym expansion to increase query vocabulary and boost result recall:
- **Core query tokens** receive a high weight multiplier of **3.0**.
- **Synonym expanded tokens** receive a weight of **1.0**.

For example, a query of `"Wedding Ceremony"` expands the search terms to include:
`["wedding", "marriage", "anniversary", "bride", "groom", "ceremony", "couple", "love", "gift", "celebration", "bridal", "reception", "suit", "dress", "gold", "decor", "silver", "sweet", "jewelry", "flowers", "atelier"]`.

### Phase 3: Hybrid Scoring Pipeline
To balance accuracy and contextual understanding, the final similarity score is a hybrid calculation:
1. **Semantic Similarity (70% weight)**: Uses the **Sentence-Transformers `all-MiniLM-L6-v2`** model to encode the query and documents into 384-dimensional dense vectors, calculating the cosine angle:
   $$\text{Cosine Similarity} = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$$
2. **Keyword TF-IDF Similarity (30% weight)**: Built from scratch in pure Python using a term-frequency length-normalized vectorizer and smoothed inverse document frequency:
   $$\text{IDF}(t) = \ln\left(1 + \frac{N}{1 + \text{DF}(t)}\right) + 1.0$$
3. **Combination**: The scores are aggregated:
   $$\text{Score}_{\text{hybrid}} = 0.7 \times \text{Score}_{\text{semantic}} + 0.3 \times \text{Score}_{\text{keyword}}$$

### Phase 4: Exact Title Match Boost
To prevent highly matching items with shorter descriptions from scoring low, the algorithm applies a **+15% relevance bonus** if any token in the user's primary query is found directly inside the product's title. The final score is clamped between `0.0` and `1.0` (100%).

---

## 5. Technical Design Decisions & Rationale
- **Hybrid Similarity Model**: Standard TF-IDF is highly precise but fails when synonyms are used (e.g., searching for "Diwali" won't find products that only mention "festive lights" or "deepavali"). Semantic embeddings solve this by understanding the concept of occasions. Combining both ensures we don't lose exact keyword matches while benefiting from semantic search.
- **Embedding Cache System (`embeddings_cache.json`)**: Running Transformer inference on every product during startup is computationally heavy. The system checks if a cached embeddings file exists and matches the SHA-256 hash of the `products.json` file. If the catalog hasn't changed, it loads pre-computed vectors instantly, reducing startup boot time to less than 1 second.
- **Frontend Architecture**: Built using native HTML5, modern ES6 JavaScript, and Vanilla CSS variables (supporting dark/light theme triggers, responsive layout layouts, and staggered entry animations). This avoids the overhead of large frameworks like React or Next.js for a single-page app and ensures sub-millisecond rendering times.

---

## 6. Project Directory Structure
```text
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── recommender.py      # Custom TF-IDF index, expansion & Semantic embeddings
│   ├── main.py                 # FastAPI server, CORS configuration, & API routing
│   ├── products.json           # Catalog dataset of products
│   └── embeddings_cache.json   # Cached semantic vectors of the catalog
├── frontend/
│   ├── index.html              # HTML structure & NLP Metrics panel
│   ├── styles.css              # Custom Vanilla CSS styling, light/dark themes
│   └── app.js                  # Frontend controllers, fetch handlers, autocomplete suggestions
├── requirements.txt            # Python dependencies list
├── test_recommender.py         # Comprehensive unit tests for checking accuracy & metrics
└── README.md                   # System documentation & design rationale
```

---

## 7. Tech Stack
- **Backend API**: Python 3.10+, [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/)
- **Machine Learning & NLP**: [Sentence-Transformers](https://sbert.net/) (`all-MiniLM-L6-v2`), [NumPy](https://numpy.org/)
- **Frontend**: Vanilla HTML5, CSS3, ES6 JavaScript, [FontAwesome Icons](https://fontawesome.com/)

---

## 8. Getting Started & Local Setup

### 1. Prerequisites
- **Python**: Version `3.10` or higher installed.
- **Package Manager**: `pip` (included in Python installation).

### 2. Setup Virtual Environment & Install Dependencies
Run the following commands in your terminal or PowerShell from the project root:

```powershell
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate the virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# 3. Upgrade pip and install packages
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run the FastAPI Server
Start the development server using:
```bash
python backend/main.py
```
*The server will automatically map the dataset, check the embeddings cache (or compute them on first run), and start listening at **`http://127.0.0.1:8000`**.*

### 4. Access the Application
Open your web browser and navigate to:
```text
http://127.0.0.1:8000
```

---

## 9. API Documentation

### 1. Recommendation Endpoint
Returns a list of products matching the specified occasion.
- **URL**: `/api/recommend`
- **Method**: `GET`
- **Query Parameters**:
  - `occasion` (string, required): The search string representing the occasion.
  - `limit` (integer, optional, default: 12): Maximum results to return (range: 1-50).
- **Example Response**:
```json
{
  "status": "success",
  "query": "wedding",
  "query_tokens_analyzed": ["couple", "bride", "wedding", "love"],
  "execution_time_ms": 14.5,
  "total_results": 5,
  "results": [
    {
      "product_id": "1002",
      "vendor_id": "Petal & Oak",
      "vendor_category_desc": "Gifting",
      "title": "Engagement Gift Hamper",
      "description_snippet": "A beautiful collection of candles, roses, and gold-rimmed wine glasses...",
      "price": "$89.99",
      "files": ["http://example.com/image.jpg"],
      "match_score": 92.4,
      "semantic_score": 88.2,
      "keyword_score": 85.0,
      "matched_terms": ["couple", "gift"]
    }
  ]
}
```

### 2. Suggestions Endpoint
Autocompletes the occasion search string as the user types.
- **URL**: `/api/suggestions`
- **Method**: `GET`
- **Query Parameters**:
  - `q` (string, required): Prefix characters.
- **Response**: List of matching strings.

### 3. Stats Endpoint
Returns statistics about the loaded product dataset.
- **URL**: `/api/stats`
- **Method**: `GET`

---

## 10. Running the Test Suite
A unit test suite in [test_recommender.py](file:///c:/Users/raksh/OneDrive/Documents/Desktop/task%20submission/test_recommender.py) asserts that database indexing, query expansion, recommendation scoring, autocomplete suggestions, and empty states operate as expected.

To run tests, run:
```bash
# Ensure your virtual environment is active
python test_recommender.py
```

---

## 11. Submission Deliverables & Screenshots

### Required Screenshots
*Please place your application screenshots in these folders or references for submission evaluation:*

1. **Occasion Input Screen**:
   ![Occasion Input Screen]<img width="1000" height="2000" alt="screencapture-127-0-0-1-8000-2026-06-20-19_02_03 (1)" src="https://github.com/user-attachments/assets/320275dd-78c9-42fa-bb84-b4485573f1a3" />
)
   *(Alternative Local Path: `screenshots/input_screen.png`)*

2. **Product Recommendations Grid Results**:
   ![Product Recommendations Results](https://raw.githubusercontent.com/username/repo/main/screenshots/results_screen.png)
   *(Alternative Local Path: `screenshots/results_screen.png`)*

---

## 12. Citations & AI Tools Usage
- **Libraries used**:
  - `fastapi` & `uvicorn` (ASGI web framework and server)
  - `sentence-transformers` (pre-trained NLP model integration)
  - `numpy` (vectorized cosine calculations)
- **AI Coding Assistant**: Developed with the assistance of **Antigravity (built by Google DeepMind)**.

---
