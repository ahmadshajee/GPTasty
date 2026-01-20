/**
 * TasteFusion - AI Recipe Generator
 * Frontend JavaScript Application
 */

// ============== Configuration ==============
const API_URL = 'https://gptasty.onrender.com';

// ============== State ==============
let meals = [];
let tasteProfile = null;

// ============== DOM Elements ==============
const tabs = document.querySelectorAll('.tab');
const tabContents = document.querySelectorAll('.tab-content');
const mealForm = document.getElementById('meal-form');
const generateForm = document.getElementById('generate-form');
const mealsList = document.getElementById('meals-list');
const loadSampleBtn = document.getElementById('load-sample');
const mealTypeRadios = document.querySelectorAll('input[name="meal-type"]');
const restaurantGroup = document.getElementById('restaurant-group');
const toast = document.getElementById('toast');

// ============== Tab Navigation ==============
tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const targetTab = tab.dataset.tab;
        
        // Update tab buttons
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Update content
        tabContents.forEach(content => {
            content.classList.remove('active');
            if (content.id === targetTab) {
                content.classList.add('active');
            }
        });
        
        // Refresh profile when switching to profile tab
        if (targetTab === 'profile') {
            loadProfile();
        }
    });
});

// ============== Meal Type Toggle ==============
mealTypeRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
        if (e.target.value === 'outside') {
            restaurantGroup.style.display = 'block';
        } else {
            restaurantGroup.style.display = 'none';
        }
    });
});

// ============== Toast Notifications ==============
function showToast(message, type = 'info') {
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ============== API Helpers ==============
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API Error');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ============== Load Meals ==============
async function loadMeals() {
    try {
        const data = await apiCall('/meals');
        meals = data.meals || [];
        renderMeals();
    } catch (error) {
        // If API not available, use local state
        console.log('Using local state for meals');
        renderMeals();
    }
}

// ============== Render Meals ==============
function renderMeals() {
    if (meals.length === 0) {
        mealsList.innerHTML = '<p class="empty-state">No meals logged yet. Start adding your favorite dishes!</p>';
        return;
    }
    
    mealsList.innerHTML = meals.map((meal, index) => `
        <div class="meal-item">
            <div class="meal-info">
                <div class="meal-name">
                    ${meal.name}
                    <span class="meal-type-badge ${meal.meal_type}">${meal.meal_type === 'home' ? '🏠 Home' : '🍽️ Outside'}</span>
                </div>
                <div class="meal-meta">
                    ${meal.cuisine} ${meal.restaurant_name ? `• ${meal.restaurant_name}` : ''} 
                    ${meal.flavors.length > 0 ? `• ${meal.flavors.join(', ')}` : ''}
                </div>
            </div>
            <button class="meal-delete" onclick="deleteMeal(${index})" title="Remove meal">🗑️</button>
        </div>
    `).join('');
}

// ============== Add Meal ==============
mealForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const submitBtn = mealForm.querySelector('button[type="submit"]');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoading = submitBtn.querySelector('.btn-loading');
    
    // Get selected flavors
    const flavors = Array.from(document.querySelectorAll('.flavor-tags input:checked'))
        .map(cb => cb.value);
    
    // Get ingredients
    const ingredientsInput = document.getElementById('ingredients').value;
    const ingredients = ingredientsInput 
        ? ingredientsInput.split(',').map(i => i.trim()).filter(i => i)
        : [];
    
    const mealData = {
        name: document.getElementById('meal-name').value,
        cuisine: document.getElementById('cuisine').value,
        meal_type: document.querySelector('input[name="meal-type"]:checked').value,
        restaurant_name: document.getElementById('restaurant').value || null,
        ingredients: ingredients,
        flavors: flavors,
        notes: document.getElementById('notes').value || null
    };
    
    // Show loading state
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline';
    submitBtn.disabled = true;
    
    try {
        await apiCall('/meals', {
            method: 'POST',
            body: JSON.stringify(mealData)
        });
        
        showToast(`Added "${mealData.name}" to your history!`, 'success');
        mealForm.reset();
        
        // Reset flavors
        document.querySelectorAll('.flavor-tags input:checked')
            .forEach(cb => cb.checked = false);
        
        // Reload meals
        await loadMeals();
        
    } catch (error) {
        // Fallback: add to local state
        meals.push({
            ...mealData,
            timestamp: new Date().toISOString()
        });
        renderMeals();
        showToast(`Added "${mealData.name}" (offline mode)`, 'success');
        mealForm.reset();
    } finally {
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
        submitBtn.disabled = false;
    }
});

// ============== Delete Meal ==============
async function deleteMeal(index) {
    try {
        await apiCall(`/meals/${index}`, { method: 'DELETE' });
        await loadMeals();
        showToast('Meal removed', 'success');
    } catch (error) {
        // Fallback: remove from local state
        meals.splice(index, 1);
        renderMeals();
        showToast('Meal removed (offline mode)', 'success');
    }
}

// ============== Load Sample Data ==============
loadSampleBtn.addEventListener('click', async () => {
    loadSampleBtn.disabled = true;
    loadSampleBtn.textContent = 'Loading...';
    
    try {
        await apiCall('/load-sample-data', { method: 'POST' });
        await loadMeals();
        showToast('Loaded sample meals! Check your taste profile.', 'success');
    } catch (error) {
        // Fallback: add sample data locally
        const sampleMeals = [
            { name: "Butter Chicken", cuisine: "Indian", ingredients: ["chicken", "butter", "tomatoes"], flavors: ["creamy", "spicy", "rich"], meal_type: "home" },
            { name: "Margherita Pizza", cuisine: "Italian", ingredients: ["dough", "tomatoes", "mozzarella"], flavors: ["savory", "cheesy"], meal_type: "outside", restaurant_name: "Domino's" },
            { name: "Pad Thai", cuisine: "Thai", ingredients: ["noodles", "shrimp", "peanuts"], flavors: ["sweet", "sour", "savory"], meal_type: "outside", restaurant_name: "Thai Express" },
            { name: "Dal Makhani", cuisine: "Indian", ingredients: ["lentils", "butter", "cream"], flavors: ["creamy", "smoky"], meal_type: "home" },
            { name: "Sushi Roll", cuisine: "Japanese", ingredients: ["rice", "salmon", "avocado"], flavors: ["fresh", "umami"], meal_type: "outside", restaurant_name: "Sushi House" },
            { name: "Tacos", cuisine: "Mexican", ingredients: ["pork", "pineapple", "tortillas"], flavors: ["spicy", "tangy"], meal_type: "outside" },
        ];
        meals.push(...sampleMeals);
        renderMeals();
        showToast('Loaded sample meals (offline mode)', 'success');
    } finally {
        loadSampleBtn.disabled = false;
        loadSampleBtn.textContent = 'Load Sample Data (Demo)';
    }
});

// ============== Load Profile ==============
async function loadProfile() {
    try {
        tasteProfile = await apiCall('/profile');
    } catch (error) {
        // Calculate locally
        tasteProfile = calculateLocalProfile();
    }
    
    renderProfile();
}

function calculateLocalProfile() {
    if (meals.length === 0) {
        return {
            meal_count: 0,
            favorite_cuisines: [],
            preferred_flavors: [],
            common_ingredients: [],
            home_vs_outside_ratio: 0.5
        };
    }
    
    const cuisines = {};
    const flavors = {};
    const ingredients = {};
    let homeCount = 0;
    
    meals.forEach(meal => {
        cuisines[meal.cuisine] = (cuisines[meal.cuisine] || 0) + 1;
        
        (meal.flavors || []).forEach(f => {
            flavors[f] = (flavors[f] || 0) + 1;
        });
        
        (meal.ingredients || []).forEach(i => {
            ingredients[i] = (ingredients[i] || 0) + 1;
        });
        
        if (meal.meal_type === 'home') homeCount++;
    });
    
    const sortByValue = (obj, limit) => 
        Object.entries(obj)
            .sort((a, b) => b[1] - a[1])
            .slice(0, limit)
            .map(([key]) => key);
    
    return {
        meal_count: meals.length,
        favorite_cuisines: sortByValue(cuisines, 5),
        preferred_flavors: sortByValue(flavors, 5),
        common_ingredients: sortByValue(ingredients, 10),
        home_vs_outside_ratio: homeCount / meals.length
    };
}

function renderProfile() {
    if (!tasteProfile) return;
    
    document.getElementById('total-meals').textContent = tasteProfile.meal_count;
    
    const homePercent = Math.round(tasteProfile.home_vs_outside_ratio * 100);
    document.getElementById('home-percent').textContent = `${homePercent}%`;
    document.querySelector('.ratio-fill').style.width = `${homePercent}%`;
    
    const renderTags = (elementId, items) => {
        const element = document.getElementById(elementId);
        if (items.length === 0) {
            element.innerHTML = '<span class="tag">Log more meals to see</span>';
        } else {
            element.innerHTML = items.map(item => `<span class="tag">${item}</span>`).join('');
        }
    };
    
    renderTags('fav-cuisines', tasteProfile.favorite_cuisines);
    renderTags('fav-flavors', tasteProfile.preferred_flavors);
    renderTags('common-ingredients', tasteProfile.common_ingredients);
}

// ============== Generate Recipe ==============
generateForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const submitBtn = generateForm.querySelector('button[type="submit"]');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoading = submitBtn.querySelector('.btn-loading');
    const recipeResult = document.getElementById('recipe-result');
    
    // Get dietary restrictions
    const dietaryRestrictions = Array.from(document.querySelectorAll('.diet-tags input:checked'))
        .map(cb => cb.value);
    
    const cookingTime = document.getElementById('cooking-time').value;
    
    const requestData = {
        fusion_style: document.getElementById('fusion-style').value || null,
        difficulty: document.getElementById('difficulty').value,
        dietary_restrictions: dietaryRestrictions,
        cooking_time: cookingTime ? parseInt(cookingTime) : null
    };
    
    // Show loading state
    btnText.style.display = 'none';
    btnLoading.style.display = 'flex';
    submitBtn.disabled = true;
    recipeResult.style.display = 'none';
    
    try {
        const response = await apiCall('/generate-recipe', {
            method: 'POST',
            body: JSON.stringify(requestData)
        });
        
        renderRecipe(response.recipe);
        recipeResult.style.display = 'block';
        
        // Scroll to result
        recipeResult.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        showToast('Recipe generated! Scroll down to see it.', 'success');
        
    } catch (error) {
        showToast(`Error: ${error.message}. Make sure the backend is running.`, 'error');
    } finally {
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
        submitBtn.disabled = false;
    }
});

function renderRecipe(recipe) {
    document.getElementById('recipe-name').textContent = recipe.name;
    document.getElementById('recipe-description').textContent = recipe.description;
    document.getElementById('prep-time').textContent = recipe.prep_time;
    document.getElementById('cook-time').textContent = recipe.cook_time;
    document.getElementById('recipe-difficulty').textContent = 
        recipe.difficulty.charAt(0).toUpperCase() + recipe.difficulty.slice(1);
    
    // Fusion tags
    document.getElementById('fusion-of').innerHTML = 
        recipe.fusion_of.map(cuisine => `<span class="fusion-tag">${cuisine}</span>`).join('');
    
    // Ingredients
    document.getElementById('recipe-ingredients').innerHTML = 
        recipe.ingredients.map(ing => `<li>${ing}</li>`).join('');
    
    // Instructions
    document.getElementById('recipe-instructions').innerHTML = 
        recipe.instructions.map(step => `<li>${step}</li>`).join('');
    
    // Flavors
    document.getElementById('recipe-flavors').innerHTML = 
        recipe.flavor_profile.map(flavor => `<span class="flavor-badge">${flavor}</span>`).join('');
    
    // Why you'll love it
    document.getElementById('why-love').textContent = recipe.why_youll_love_it;
}

// ============== Initialize ==============
document.addEventListener('DOMContentLoaded', () => {
    loadMeals();
    console.log('🍳 TasteFusion loaded! Ready to create delicious fusion recipes.');
});

// Make deleteMeal available globally
window.deleteMeal = deleteMeal;
