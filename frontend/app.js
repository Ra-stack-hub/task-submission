// Occasion-Based Recommendation System Frontend Logic

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const themeToggle = document.getElementById("themeToggle");
    const devPanelBtn = document.getElementById("devPanelBtn");
    const closeDevPanel = document.getElementById("closeDevPanel");
    const devPanel = document.getElementById("devPanel");
    
    const occasionInput = document.getElementById("occasionInput");
    const clearSearchBtn = document.getElementById("clearSearch");
    const searchBtn = document.getElementById("searchBtn");
    const suggestionsList = document.getElementById("suggestionsList");
    
    const productsGrid = document.getElementById("productsGrid");
    const resultsSection = document.getElementById("resultsSection");
    const resultsTitle = document.getElementById("resultsTitle");
    const resultCount = document.getElementById("resultCount");
    const timingBadge = document.getElementById("timingBadge");
    
    // States
    const initialState = document.getElementById("initialState");
    const loadingState = document.getElementById("loadingState");
    const emptyState = document.getElementById("emptyState");
    const emptyMessage = document.getElementById("emptyMessage");
    
    // Metrics Elements
    const statProducts = document.getElementById("statProducts");
    const statCategories = document.getElementById("statCategories");
    const statVocab = document.getElementById("statVocab");
    const metricResponseTime = document.getElementById("metricResponseTime");
    const expandedTermsContainer = document.getElementById("expandedTerms");
    
    // State management variables
    let activeSuggestionIndex = -1;
    let suggestions = [];
    let debounceTimer = null;

    // --- 1. Theme Configuration ---
    const savedTheme = localStorage.getItem("theme") || "dark";
    document.documentElement.setAttribute("data-theme", savedTheme);

    themeToggle.addEventListener("click", () => {
        const currentTheme = document.documentElement.getAttribute("data-theme");
        const newTheme = currentTheme === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", newTheme);
        localStorage.setItem("theme", newTheme);
    });

    // --- 2. Developer Sidebar Panel Controls ---
    devPanelBtn.addEventListener("click", () => {
        devPanel.classList.add("open");
    });

    closeDevPanel.addEventListener("click", () => {
        devPanel.classList.remove("open");
    });

    // Close panel on clicking outside
    document.addEventListener("click", (e) => {
        if (!devPanel.contains(e.target) && !devPanelBtn.contains(e.target) && devPanel.classList.contains("open")) {
            devPanel.classList.remove("open");
        }
    });

    // Load catalog statistics on launch
    async function loadCatalogStats() {
        try {
            const res = await fetch("/api/stats");
            if (res.ok) {
                const stats = await res.json();
                statProducts.textContent = stats.total_products;
                statCategories.textContent = stats.total_categories;
                statVocab.textContent = stats.vocabulary_size;
            }
        } catch (err) {
            console.error("Failed to load catalog stats:", err);
        }
    }
    loadCatalogStats();

    // --- 3. Autocomplete / Suggestions ---
    occasionInput.addEventListener("input", () => {
        const query = occasionInput.value.trim();
        
        // Show/hide clear button
        if (occasionInput.value.length > 0) {
            clearSearchBtn.classList.remove("hidden");
        } else {
            clearSearchBtn.classList.add("hidden");
            hideSuggestions();
            return;
        }

        // Debounce API calls for autocomplete
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            fetchSuggestions(query);
        }, 250);
    });

    async function fetchSuggestions(query) {
        if (query.length < 2) {
            hideSuggestions();
            return;
        }

        try {
            const res = await fetch(`/api/suggestions?q=${encodeURIComponent(query)}`);
            if (res.ok) {
                suggestions = await res.json();
                renderSuggestions(suggestions);
            }
        } catch (err) {
            console.error("Suggestions fetch error:", err);
        }
    }

    function renderSuggestions(list) {
        if (list.length === 0) {
            hideSuggestions();
            return;
        }

        suggestionsList.innerHTML = "";
        activeSuggestionIndex = -1;
        
        list.forEach((item, index) => {
            const div = document.createElement("div");
            div.classList.add("suggestion-item");
            div.innerHTML = `<i class="fa-solid fa-clock-rotate-left"></i> <span>${item}</span>`;
            
            div.addEventListener("click", () => {
                occasionInput.value = item;
                hideSuggestions();
                triggerSearch(item);
            });
            
            suggestionsList.appendChild(div);
        });

        suggestionsList.classList.remove("hidden");
    }

    function hideSuggestions() {
        suggestionsList.classList.add("hidden");
        suggestionsList.innerHTML = "";
        activeSuggestionIndex = -1;
    }

    // Keyboard navigation inside Suggestions Dropdown
    occasionInput.addEventListener("keydown", (e) => {
        const items = suggestionsList.querySelectorAll(".suggestion-item");
        if (suggestionsList.classList.contains("hidden") || items.length === 0) {
            if (e.key === "Enter") {
                triggerSearch(occasionInput.value.trim());
            }
            return;
        }

        if (e.key === "ArrowDown") {
            e.preventDefault();
            activeSuggestionIndex = (activeSuggestionIndex + 1) % items.length;
            highlightSuggestion(items);
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            activeSuggestionIndex = (activeSuggestionIndex - 1 + items.length) % items.length;
            highlightSuggestion(items);
        } else if (e.key === "Enter") {
            e.preventDefault();
            if (activeSuggestionIndex > -1 && items[activeSuggestionIndex]) {
                const selectedText = items[activeSuggestionIndex].querySelector("span").textContent;
                occasionInput.value = selectedText;
                hideSuggestions();
                triggerSearch(selectedText);
            } else {
                triggerSearch(occasionInput.value.trim());
            }
        } else if (e.key === "Escape") {
            hideSuggestions();
        }
    });

    function highlightSuggestion(items) {
        items.forEach((item, index) => {
            if (index === activeSuggestionIndex) {
                item.classList.add("active");
                occasionInput.value = item.querySelector("span").textContent;
            } else {
                item.classList.remove("active");
            }
        });
    }

    // Clear Search Input
    clearSearchBtn.addEventListener("click", () => {
        occasionInput.value = "";
        clearSearchBtn.classList.add("hidden");
        occasionInput.focus();
        hideSuggestions();
    });

    // Close suggestions on outside clicks
    document.addEventListener("click", (e) => {
        if (!e.target.closest(".search-wrapper")) {
            hideSuggestions();
        }
    });

    // --- 4. Quick-Search Pills ---
    document.querySelectorAll(".pill-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const query = btn.getAttribute("data-query");
            occasionInput.value = query;
            clearSearchBtn.classList.remove("hidden");
            triggerSearch(query);
        });
    });

    searchBtn.addEventListener("click", () => {
        triggerSearch(occasionInput.value.trim());
    });

    // --- 5. Recommendation Fetch & Render ---
    async function triggerSearch(query) {
        if (!query) return;
        
        hideSuggestions();
        switchUIState("loading");
        
        try {
            const response = await fetch(`/api/recommend?occasion=${encodeURIComponent(query)}&limit=16`);
            if (!response.ok) {
                throw new Error("Failed to retrieve suggestions from backend server.");
            }
            
            const data = await response.json();
            
            // Populate metrics sidebar
            metricResponseTime.textContent = `${data.execution_time_ms} ms`;
            timingBadge.textContent = `in ${data.execution_time_ms}ms`;
            
            // Render Expansion tags
            renderExpansionTags(data.query_tokens_analyzed);

            if (data.results && data.results.length > 0) {
                renderProducts(data.results);
                resultsTitle.innerHTML = `Recommendations for <span>"${query}"</span>`;
                resultCount.textContent = `Found ${data.total_results} matching products`;
                switchUIState("results");
            } else {
                emptyMessage.textContent = `No matching products found in the catalog for "${query}". Try searching for categories like chocolates, books, wrapping paper, or decor.`;
                switchUIState("empty");
            }
        } catch (err) {
            console.error("Search error:", err);
            emptyMessage.textContent = "There was an error communicating with the recommendation engine. Please check that the server is running.";
            switchUIState("empty");
        }
    }

    function renderExpansionTags(tokens) {
        expandedTermsContainer.innerHTML = "";
        if (!tokens || tokens.length === 0) {
            expandedTermsContainer.innerHTML = '<span class="empty-tag">No terms analyzed</span>';
            return;
        }
        
        tokens.forEach(token => {
            const span = document.createElement("span");
            span.textContent = token;
            expandedTermsContainer.appendChild(span);
        });
    }

    function switchUIState(state) {
        initialState.classList.add("hidden");
        loadingState.classList.add("hidden");
        resultsSection.classList.add("hidden");
        emptyState.classList.add("hidden");

        if (state === "initial") {
            initialState.classList.remove("hidden");
        } else if (state === "loading") {
            loadingState.classList.remove("hidden");
        } else if (state === "results") {
            resultsSection.classList.remove("hidden");
        } else if (state === "empty") {
            emptyState.classList.remove("hidden");
        }
    }

    function renderProducts(products) {
        productsGrid.innerHTML = "";
        
        products.forEach((p, idx) => {
            const card = document.createElement("div");
            card.classList.add("product-card");
            card.style.animationDelay = `${idx * 0.05}s`; // Staggered entry animation

            // Relevance Badge Style
            let badgeClass = "match-med";
            if (p.match_score >= 60.0) {
                badgeClass = "match-high";
            }
            
            // Image handling (support files array)
            const imageUrl = p.files && p.files.length > 0 ? p.files[0] : "";
            let mediaSectionHtml = "";
            
            if (imageUrl) {
                mediaSectionHtml = `
                    <div class="card-media">
                        <img class="product-img" src="${imageUrl}" alt="${p.title}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                        <div class="img-fallback" style="display: none;">
                            <i class="fa-solid fa-gift"></i>
                            <span>Image Unavailable</span>
                        </div>
                    </div>
                `;
            } else {
                mediaSectionHtml = `
                    <div class="card-media">
                        <div class="img-fallback">
                            <i class="fa-solid fa-gift"></i>
                            <span>Gift Item</span>
                        </div>
                    </div>
                `;
            }

            // Price Formatting
            let priceHtml = "";
            if (p.price && p.price !== "N/A" && p.price !== "0" && p.price !== "1") {
                // If it is numeric, format nicely
                const parsedPrice = parseFloat(p.price);
                if (!isNaN(parsedPrice)) {
                    priceHtml = `&#8377;${parsedPrice.toLocaleString("en-IN")}`;
                } else {
                    priceHtml = p.price;
                }
            } else {
                priceHtml = "&#8377;499"; // Default aesthetic placeholder price
            }

            // Highlight matched terms
            let matchedTermsHtml = "";
            if (p.matched_terms && p.matched_terms.length > 0) {
                const tags = p.matched_terms.slice(0, 4).map(term => `<span class="reason-tag">${term}</span>`).join(" ");
                matchedTermsHtml = `
                    <div class="card-footer">
                        <div class="match-reason">
                            <i class="fa-solid fa-tag"></i> Matched: ${tags}
                        </div>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="match-badge ${badgeClass}">
                    <i class="fa-solid fa-circle-nodes"></i>
                    <span>${p.match_score}% Match</span>
                </div>
                ${mediaSectionHtml}
                <div class="card-body">
                    <span class="product-category">${p.vendor_category_desc || 'Catalog Product'}</span>
                    <h3 class="product-title" title="${p.title}">${p.title}</h3>
                    <div class="product-price-brand">
                        <span class="product-price">${priceHtml}</span>
                        <span class="product-brand">${p.vendor_id || 'Premium Brand'}</span>
                    </div>
                    <div class="product-description">
                        <span class="desc-snippet">${p.description_snippet}</span>
                        ${p.full_description.length > 150 ? `
                            <button class="desc-expand-btn">Read more <i class="fa-solid fa-chevron-down"></i></button>
                            <span class="desc-full">${p.full_description}</span>
                        ` : ''}
                    </div>
                </div>
                ${matchedTermsHtml}
            `;

            // Expand description event listener
            const expandBtn = card.querySelector(".desc-expand-btn");
            if (expandBtn) {
                expandBtn.addEventListener("click", () => {
                    const snippet = card.querySelector(".desc-snippet");
                    const full = card.querySelector(".desc-full");
                    
                    if (full.style.display === "inline" || full.style.display === "block") {
                        full.style.display = "none";
                        snippet.style.display = "inline";
                        expandBtn.innerHTML = 'Read more <i class="fa-solid fa-chevron-down"></i>';
                    } else {
                        full.style.display = "inline";
                        snippet.style.display = "none";
                        expandBtn.innerHTML = 'Show less <i class="fa-solid fa-chevron-up"></i>';
                    }
                });
            }

            productsGrid.appendChild(card);
        });
    }
});
