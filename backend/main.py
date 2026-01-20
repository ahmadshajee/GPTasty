"""
TasteFusion - AI Recipe Generator Agent
Learns your taste preferences and creates personalized fusion recipes
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key from OpenRouter key for compatibility
os.environ['OPENAI_API_KEY'] = os.getenv('OPENROUTER_API_KEY', 'your-api-key-here')
os.environ['OPENAI_BASE_URL'] = 'https://openrouter.ai/api/v1'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== Data Models ==============

class Meal(BaseModel):
    """Model for a meal entry"""
    name: str = Field(..., min_length=1, max_length=200)
    cuisine: str = Field(..., min_length=1, max_length=100)
    ingredients: list[str] = Field(default_factory=list)
    flavors: list[str] = Field(default_factory=list)  # spicy, sweet, savory, etc.
    meal_type: str = Field(..., pattern="^(home|outside)$")
    restaurant_name: Optional[str] = None
    notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class MealInput(BaseModel):
    """Input model for adding a meal"""
    name: str = Field(..., min_length=1, max_length=200)
    cuisine: str = Field(..., min_length=1, max_length=100)
    ingredients: list[str] = Field(default_factory=list)
    flavors: list[str] = Field(default_factory=list)
    meal_type: str = Field(..., pattern="^(home|outside)$")
    restaurant_name: Optional[str] = None
    notes: Optional[str] = None

class FusionRequest(BaseModel):
    """Request model for generating fusion recipe"""
    fusion_style: Optional[str] = None  # e.g., "Italian-Indian", "Mexican-Thai"
    dietary_restrictions: list[str] = Field(default_factory=list)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    cooking_time: Optional[int] = None  # in minutes

class TasteProfile(BaseModel):
    """User's taste profile derived from meal history"""
    favorite_cuisines: list[str]
    preferred_flavors: list[str]
    common_ingredients: list[str]
    home_vs_outside_ratio: float
    meal_count: int

class FusionRecipe(BaseModel):
    """Generated fusion recipe"""
    name: str
    description: str
    fusion_of: list[str]
    ingredients: list[str]
    instructions: list[str]
    prep_time: int
    cook_time: int
    difficulty: str
    flavor_profile: list[str]
    why_youll_love_it: str

class UserPreferences(BaseModel):
    """Context for the AI agent"""
    meals: list[Meal]
    taste_profile: TasteProfile

# ============== In-Memory Storage ==============
# In production, use a proper database

meals_db: list[Meal] = []

def get_taste_profile() -> TasteProfile:
    """Analyze meals to create taste profile"""
    if not meals_db:
        return TasteProfile(
            favorite_cuisines=[],
            preferred_flavors=[],
            common_ingredients=[],
            home_vs_outside_ratio=0.5,
            meal_count=0
        )
    
    cuisines: dict[str, int] = {}
    flavors: dict[str, int] = {}
    ingredients: dict[str, int] = {}
    home_count = 0
    
    for meal in meals_db:
        # Count cuisines
        cuisines[meal.cuisine] = cuisines.get(meal.cuisine, 0) + 1
        
        # Count flavors
        for flavor in meal.flavors:
            flavors[flavor] = flavors.get(flavor, 0) + 1
        
        # Count ingredients
        for ingredient in meal.ingredients:
            ingredients[ingredient] = ingredients.get(ingredient, 0) + 1
        
        if meal.meal_type == "home":
            home_count += 1
    
    # Get top items
    top_cuisines = sorted(cuisines.items(), key=lambda x: x[1], reverse=True)[:5]
    top_flavors = sorted(flavors.items(), key=lambda x: x[1], reverse=True)[:5]
    top_ingredients = sorted(ingredients.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return TasteProfile(
        favorite_cuisines=[c[0] for c in top_cuisines],
        preferred_flavors=[f[0] for f in top_flavors],
        common_ingredients=[i[0] for i in top_ingredients],
        home_vs_outside_ratio=home_count / len(meals_db) if meals_db else 0.5,
        meal_count=len(meals_db)
    )

# ============== Pydantic AI Agent ==============

# Create the Fusion Recipe Agent using OpenRouter (via OpenAI-compatible API)
fusion_agent = Agent(
    'openai:google/gemini-2.0-flash-exp:free',
    system_prompt="""You are TasteFusion Chef, an expert culinary AI that creates personalized fusion recipes.

Your role:
1. Analyze the user's taste profile from their meal history
2. Understand their preferences (home cooking vs restaurant, flavor profiles, favorite cuisines)
3. Create innovative fusion recipes that combine elements from their favorite cuisines
4. Ensure recipes are practical and match their skill level

Guidelines:
- Be creative but practical - recipes should be actually cookable
- Respect dietary restrictions strictly
- Explain WHY the user will love this recipe based on their preferences
- Provide clear, step-by-step instructions
- Include prep and cooking times
- Balance familiar flavors with exciting new combinations

Always return a complete, detailed recipe with all required fields.""",
    output_type=FusionRecipe,
    retries=3
)

@fusion_agent.system_prompt
def add_user_context(ctx: RunContext[UserPreferences]) -> str:
    """Add user's taste profile to the context"""
    prefs = ctx.deps
    
    if not prefs.meals:
        return """
Note: This user is new and hasn't logged any meals yet.
Create a universally appealing fusion recipe that showcases interesting flavor combinations.
Suggest they log some meals to get more personalized recommendations.
"""
    
    home_meals = [m for m in prefs.meals if m.meal_type == "home"]
    outside_meals = [m for m in prefs.meals if m.meal_type == "outside"]
    
    context = f"""
User's Taste Profile Analysis:
- Total meals logged: {prefs.taste_profile.meal_count}
- Favorite cuisines: {', '.join(prefs.taste_profile.favorite_cuisines) or 'Not enough data'}
- Preferred flavors: {', '.join(prefs.taste_profile.preferred_flavors) or 'Not enough data'}
- Common ingredients: {', '.join(prefs.taste_profile.common_ingredients) or 'Not enough data'}
- Home cooking ratio: {prefs.taste_profile.home_vs_outside_ratio:.0%}

Recent Home Meals:
{chr(10).join([f"- {m.name} ({m.cuisine}): {', '.join(m.flavors)}" for m in home_meals[-5:]]) or 'None logged'}

Recent Restaurant/Outside Meals:
{chr(10).join([f"- {m.name} ({m.cuisine}) at {m.restaurant_name or 'unknown'}: {', '.join(m.flavors)}" for m in outside_meals[-5:]]) or 'None logged'}

Create a fusion recipe that combines elements from their favorite cuisines and matches their flavor preferences.
"""
    return context

# ============== FastAPI Application ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 TasteFusion API starting up...")
    logger.info("📊 Ready to analyze your taste and create fusion recipes!")
    yield
    logger.info("👋 TasteFusion API shutting down...")

app = FastAPI(
    title="TasteFusion API",
    description="AI-powered recipe generator that learns your taste preferences",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== API Endpoints ==============

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "TasteFusion API",
        "version": "1.0.0",
        "message": "Ready to create delicious fusion recipes! 🍳"
    }

@app.post("/meals", status_code=status.HTTP_201_CREATED)
async def add_meal(meal_input: MealInput) -> dict:
    """Add a new meal to the user's history"""
    try:
        meal = Meal(
            name=meal_input.name,
            cuisine=meal_input.cuisine,
            ingredients=meal_input.ingredients,
            flavors=meal_input.flavors,
            meal_type=meal_input.meal_type,
            restaurant_name=meal_input.restaurant_name,
            notes=meal_input.notes
        )
        meals_db.append(meal)
        logger.info(f"Added meal: {meal.name} ({meal.cuisine})")
        
        return {
            "success": True,
            "message": f"Added '{meal.name}' to your meal history",
            "meal_count": len(meals_db)
        }
    except Exception as e:
        logger.error(f"Error adding meal: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/meals")
async def get_meals() -> dict:
    """Get all logged meals"""
    return {
        "meals": [meal.model_dump() for meal in meals_db],
        "count": len(meals_db)
    }

@app.delete("/meals/{index}")
async def delete_meal(index: int) -> dict:
    """Delete a meal by index"""
    if index < 0 or index >= len(meals_db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal not found"
        )
    
    removed = meals_db.pop(index)
    logger.info(f"Removed meal: {removed.name}")
    
    return {
        "success": True,
        "message": f"Removed '{removed.name}' from history"
    }

@app.get("/profile")
async def get_profile() -> TasteProfile:
    """Get the user's taste profile"""
    return get_taste_profile()

@app.post("/generate-recipe")
async def generate_fusion_recipe(request: FusionRequest) -> dict:
    """Generate a personalized fusion recipe using AI"""
    try:
        logger.info(f"Generating fusion recipe with params: {request}")
        
        # Prepare user context
        taste_profile = get_taste_profile()
        user_prefs = UserPreferences(
            meals=meals_db,
            taste_profile=taste_profile
        )
        
        # Build the prompt
        prompt_parts = ["Create a unique fusion recipe for me."]
        
        if request.fusion_style:
            prompt_parts.append(f"Fusion style: {request.fusion_style}")
        
        if request.dietary_restrictions:
            prompt_parts.append(f"Dietary restrictions: {', '.join(request.dietary_restrictions)}")
        
        prompt_parts.append(f"Difficulty level: {request.difficulty}")
        
        if request.cooking_time:
            prompt_parts.append(f"Maximum cooking time: {request.cooking_time} minutes")
        
        prompt = " ".join(prompt_parts)
        
        # Run the agent
        result = await fusion_agent.run(prompt, deps=user_prefs)
        
        logger.info(f"Generated recipe: {result.data.name}")
        
        return {
            "success": True,
            "recipe": result.data.model_dump(),
            "taste_profile_used": taste_profile.model_dump()
        }
        
    except Exception as e:
        logger.error(f"Error generating recipe: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recipe: {str(e)}"
        )

@app.post("/generate-weekly-menu")
async def generate_weekly_menu() -> dict:
    """Generate a week's worth of fusion recipes"""
    try:
        taste_profile = get_taste_profile()
        user_prefs = UserPreferences(
            meals=meals_db,
            taste_profile=taste_profile
        )
        
        recipes = []
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for day in days:
            prompt = f"Create a unique fusion recipe for {day}. Make it different from typical weekday meals if it's a weekend."
            result = await fusion_agent.run(prompt, deps=user_prefs)
            recipes.append({
                "day": day,
                "recipe": result.data.model_dump()
            })
            logger.info(f"Generated {day} recipe: {result.data.name}")
        
        return {
            "success": True,
            "weekly_menu": recipes
        }
        
    except Exception as e:
        logger.error(f"Error generating weekly menu: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate weekly menu: {str(e)}"
        )

# ============== Sample Data Endpoint (for demo) ==============

@app.post("/load-sample-data")
async def load_sample_data() -> dict:
    """Load sample meal data for demonstration"""
    sample_meals = [
        MealInput(
            name="Butter Chicken",
            cuisine="Indian",
            ingredients=["chicken", "butter", "tomatoes", "cream", "garam masala"],
            flavors=["creamy", "spicy", "rich"],
            meal_type="home",
            notes="Mom's recipe"
        ),
        MealInput(
            name="Margherita Pizza",
            cuisine="Italian",
            ingredients=["dough", "tomatoes", "mozzarella", "basil"],
            flavors=["savory", "cheesy", "herby"],
            meal_type="outside",
            restaurant_name="Domino's"
        ),
        MealInput(
            name="Pad Thai",
            cuisine="Thai",
            ingredients=["rice noodles", "shrimp", "peanuts", "tamarind", "bean sprouts"],
            flavors=["sweet", "sour", "savory", "nutty"],
            meal_type="outside",
            restaurant_name="Thai Express"
        ),
        MealInput(
            name="Dal Makhani",
            cuisine="Indian",
            ingredients=["black lentils", "butter", "cream", "tomatoes", "spices"],
            flavors=["creamy", "smoky", "rich"],
            meal_type="home"
        ),
        MealInput(
            name="Sushi Roll",
            cuisine="Japanese",
            ingredients=["rice", "nori", "salmon", "avocado", "cucumber"],
            flavors=["fresh", "umami", "light"],
            meal_type="outside",
            restaurant_name="Sushi House"
        ),
        MealInput(
            name="Tacos Al Pastor",
            cuisine="Mexican",
            ingredients=["pork", "pineapple", "onions", "cilantro", "tortillas"],
            flavors=["spicy", "sweet", "tangy"],
            meal_type="outside",
            restaurant_name="Taco Bell"
        ),
        MealInput(
            name="Palak Paneer",
            cuisine="Indian",
            ingredients=["spinach", "paneer", "onions", "garlic", "cream"],
            flavors=["creamy", "mild", "healthy"],
            meal_type="home"
        ),
        MealInput(
            name="Kung Pao Chicken",
            cuisine="Chinese",
            ingredients=["chicken", "peanuts", "dried chilies", "soy sauce", "vegetables"],
            flavors=["spicy", "sweet", "crunchy"],
            meal_type="outside",
            restaurant_name="Wok Express"
        )
    ]
    
    for meal_input in sample_meals:
        meal = Meal(
            name=meal_input.name,
            cuisine=meal_input.cuisine,
            ingredients=meal_input.ingredients,
            flavors=meal_input.flavors,
            meal_type=meal_input.meal_type,
            restaurant_name=meal_input.restaurant_name,
            notes=meal_input.notes
        )
        meals_db.append(meal)
    
    logger.info(f"Loaded {len(sample_meals)} sample meals")
    
    return {
        "success": True,
        "message": f"Loaded {len(sample_meals)} sample meals",
        "total_meals": len(meals_db)
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
