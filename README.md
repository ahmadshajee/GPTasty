# 🍳 TasteFusion - AI Recipe Generator

**TasteFusion** is a full-stack AI-powered recipe generator that learns your taste preferences from your meal history (home & outside eating) and creates personalized fusion recipes just for you!

![TasteFusion Demo](https://via.placeholder.com/800x400/E67E22/FFFFFF?text=TasteFusion+-+AI+Recipe+Generator)

## ✨ Features

- **📝 Log Your Meals** - Record what you eat at home and at restaurants
- **👤 Taste Profile Analysis** - AI analyzes your preferences (cuisines, flavors, ingredients)
- **✨ Fusion Recipe Generation** - Get personalized fusion recipes based on YOUR taste
- **🌍 Multi-Cuisine Fusion** - Blend Indian-Italian, Thai-Mexican, and more!
- **🎨 Beautiful UI** - Modern, responsive design with smooth interactions

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **AI Agent** | Pydantic AI |
| **Backend** | FastAPI (Python) |
| **LLM** | Google Gemini via OpenRouter (Free) |
| **Frontend** | HTML5, CSS3, Vanilla JS |
| **Deployment** | Railway (Backend) + Vercel/Netlify (Frontend) |

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- OpenRouter API Key (Free at [openrouter.ai](https://openrouter.ai))

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/tastefusion.git
cd tastefusion
```

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### 3. Run Backend

```bash
uvicorn main:app --reload
```

Backend will be running at `http://localhost:8000`

### 4. Run Frontend

Open `frontend/index.html` in your browser, or serve it:

```bash
cd frontend
python -m http.server 3000
```

Frontend will be at `http://localhost:3000`

## 🌐 Deployment

### Deploy Backend to Railway

1. Create account at [railway.app](https://railway.app)
2. Create new project → Deploy from GitHub
3. Select the `backend` folder
4. Add environment variable: `OPENROUTER_API_KEY`
5. Deploy! Note your Railway URL

### Deploy Frontend to Vercel

1. Update `API_URL` in `frontend/app.js` with your Railway URL
2. Create account at [vercel.com](https://vercel.com)
3. Import your GitHub repo
4. Set root directory to `frontend`
5. Deploy!

### Deploy Frontend to Netlify

1. Update `API_URL` in `frontend/app.js`
2. Drag and drop `frontend` folder to [netlify.com](https://netlify.com)
3. Done!

## 📁 Project Structure

```
TasteFusion/
├── backend/
│   ├── main.py              # FastAPI + Pydantic AI agent
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment variables template
│   ├── Dockerfile           # Docker configuration
│   ├── Procfile            # Heroku/Railway deployment
│   └── railway.toml        # Railway configuration
│
├── frontend/
│   ├── index.html          # Main HTML file
│   ├── styles.css          # Styling
│   ├── app.js              # Frontend JavaScript
│   ├── vercel.json         # Vercel configuration
│   └── netlify.toml        # Netlify configuration
│
└── README.md
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/meals` | Add a meal |
| GET | `/meals` | Get all meals |
| DELETE | `/meals/{index}` | Delete a meal |
| GET | `/profile` | Get taste profile |
| POST | `/generate-recipe` | Generate fusion recipe |
| POST | `/load-sample-data` | Load demo data |

## 🤖 How the AI Agent Works

The TasteFusion agent uses **Pydantic AI** to:

1. **Analyze Context** - Reads your meal history and taste profile
2. **Understand Preferences** - Identifies favorite cuisines, flavors, ingredients
3. **Generate Fusion** - Creates unique recipes blending your preferred cuisines
4. **Personalize** - Explains why YOU will love the recipe

```python
fusion_agent = Agent(
    model,
    system_prompt="You are TasteFusion Chef...",
    result_type=FusionRecipe,  # Structured output with Pydantic
    retries=3
)
```

## 📸 Screenshots

### Log Your Meals
![Log Meals](https://via.placeholder.com/400x300/FDF6E3/2C3E50?text=Log+Meals+UI)

### Taste Profile
![Taste Profile](https://via.placeholder.com/400x300/FDF6E3/2C3E50?text=Taste+Profile)

### Generated Recipe
![Recipe](https://via.placeholder.com/400x300/E67E22/FFFFFF?text=Fusion+Recipe)

## 🎥 Demo Video

[Watch 1-minute Loom Demo](https://loom.com/your-video-link)

## 📄 License

MIT License - feel free to use for your own projects!

## 🙏 Acknowledgments

- [Pydantic AI](https://ai.pydantic.dev/) - For the amazing AI agent framework
- [OpenRouter](https://openrouter.ai/) - For free LLM access
- [FastAPI](https://fastapi.tiangolo.com/) - For the blazing fast API framework

---

**Built with ❤️ for the SRM Internship Assignment**

*Made by [Your Name] - January 2026*
