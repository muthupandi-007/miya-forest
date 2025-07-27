from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import httpx
import asyncio
from enum import Enum


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class PlantingMethod(str, Enum):
    GROUND = "ground"
    TERRACE = "terrace"

class PlantType(str, Enum):
    TREE = "tree"
    SHRUB = "shrub"
    GROUNDCOVER = "groundcover"

class SoilType(str, Enum):
    CLAY = "clay"
    SANDY = "sandy"
    LOAM = "loam"
    ROCKY = "rocky"

# Models
class Location(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    latitude: float
    longitude: float
    address: str
    city: str
    state: str
    country: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NativeSpecies(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scientific_name: str
    common_name: str
    plant_type: PlantType
    height_range: str
    growth_rate: str
    water_needs: str
    soil_preferences: List[SoilType]
    climate_zone: str
    native_region: str
    benefits: List[str]
    planting_season: str
    care_instructions: str
    miyawaki_layer: int  # 1-4 (ground, shrub, sub-tree, canopy)

class PlotDesign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    location_id: str
    plot_size: float  # in square meters
    planting_method: PlantingMethod
    soil_type: SoilType
    selected_species: List[str]  # species IDs
    layout_config: Dict[str, Any]  # 3D layout configuration
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PlantationProject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    plot_design_id: str
    project_name: str
    manager_name: str
    manager_phone: str
    status: str = "planned"  # planned, in_progress, monitoring, completed
    planted_date: Optional[datetime] = None
    weather_alerts: bool = True
    iot_enabled: bool = False
    maintenance_schedule: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WeatherData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    location_id: str
    temperature: float
    humidity: float
    rainfall: float
    wind_speed: float
    weather_condition: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    alert_type: str  # weather, damage, maintenance
    severity: str  # low, medium, high
    message: str
    resolved: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Create models for API requests
class LocationCreate(BaseModel):
    latitude: float
    longitude: float
    address: str
    city: str
    state: str
    country: str

class PlotDesignCreate(BaseModel):
    user_id: str
    location_id: str
    plot_size: float
    planting_method: PlantingMethod
    soil_type: SoilType
    selected_species: List[str]

class PlantationProjectCreate(BaseModel):
    user_id: str
    plot_design_id: str
    project_name: str
    manager_name: str
    manager_phone: str

# Routes
@api_router.get("/")
async def root():
    return {"message": "Miyawaki Forest Planner API"}

@api_router.post("/locations", response_model=Location)
async def create_location(location: LocationCreate):
    location_dict = location.dict()
    location_obj = Location(**location_dict)
    await db.locations.insert_one(location_obj.dict())
    return location_obj

@api_router.get("/locations", response_model=List[Location])
async def get_locations():
    locations = await db.locations.find().to_list(1000)
    return [Location(**location) for location in locations]

@api_router.get("/species/native")
async def get_native_species(
    latitude: float = Query(..., description="Latitude of the location"),
    longitude: float = Query(..., description="Longitude of the location"),
    limit: int = Query(20, description="Number of species to return")
):
    """Get native species for a specific location using GBIF API"""
    try:
        # Mock native species data for MVP (in production, would use GBIF API)
        # For now, return region-specific species based on coordinates
        
        # Determine climate zone based on latitude
        climate_zone = "temperate"
        if latitude < 23.5:
            climate_zone = "tropical"
        elif latitude > 66.5:
            climate_zone = "polar"
        
        # Mock species data based on climate zone
        species_data = await get_mock_species_data(climate_zone, limit)
        
        return {
            "location": {"latitude": latitude, "longitude": longitude},
            "climate_zone": climate_zone,
            "species": species_data,
            "total_count": len(species_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching species data: {str(e)}")

async def get_mock_species_data(climate_zone: str, limit: int) -> List[Dict]:
    """Mock species data for different climate zones"""
    
    tropical_species = [
        {
            "id": str(uuid.uuid4()),
            "scientific_name": "Ficus benghalensis",
            "common_name": "Banyan Tree",
            "plant_type": "tree",
            "height_range": "15-30m",
            "growth_rate": "fast",
            "water_needs": "moderate",
            "soil_preferences": ["loam", "clay"],
            "climate_zone": "tropical",
            "benefits": ["Air purification", "Shade", "Wildlife habitat"],
            "planting_season": "Monsoon",
            "care_instructions": "Water regularly, prune dead branches",
            "miyawaki_layer": 4
        },
        {
            "id": str(uuid.uuid4()),
            "scientific_name": "Azadirachta indica",
            "common_name": "Neem Tree",
            "plant_type": "tree",
            "height_range": "10-20m",
            "growth_rate": "moderate",
            "water_needs": "low",
            "soil_preferences": ["sandy", "loam"],
            "climate_zone": "tropical",
            "benefits": ["Pest control", "Medicinal", "Air purification"],
            "planting_season": "Monsoon",
            "care_instructions": "Drought tolerant, minimal care needed",
            "miyawaki_layer": 3
        },
        {
            "id": str(uuid.uuid4()),
            "scientific_name": "Ixora coccinea",
            "common_name": "Flame of the Woods",
            "plant_type": "shrub",
            "height_range": "1-3m",
            "growth_rate": "moderate",
            "water_needs": "moderate",
            "soil_preferences": ["loam", "clay"],
            "climate_zone": "tropical",
            "benefits": ["Flowering", "Butterfly attraction", "Decorative"],
            "planting_season": "Monsoon",
            "care_instructions": "Regular watering, pruning after flowering",
            "miyawaki_layer": 2
        }
    ]
    
    temperate_species = [
        {
            "id": str(uuid.uuid4()),
            "scientific_name": "Quercus robur",
            "common_name": "English Oak",
            "plant_type": "tree",
            "height_range": "20-40m",
            "growth_rate": "slow",
            "water_needs": "moderate",
            "soil_preferences": ["loam", "clay"],
            "climate_zone": "temperate",
            "benefits": ["Wildlife habitat", "Timber", "Carbon sequestration"],
            "planting_season": "Spring",
            "care_instructions": "Water in first year, minimal care after establishment",
            "miyawaki_layer": 4
        },
        {
            "id": str(uuid.uuid4()),
            "scientific_name": "Cornus sanguinea",
            "common_name": "Common Dogwood",
            "plant_type": "shrub",
            "height_range": "3-6m",
            "growth_rate": "moderate",
            "water_needs": "moderate",
            "soil_preferences": ["loam", "clay"],
            "climate_zone": "temperate",
            "benefits": ["Berry production", "Wildlife food", "Autumn color"],
            "planting_season": "Spring/Fall",
            "care_instructions": "Prune in late winter, regular watering",
            "miyawaki_layer": 2
        }
    ]
    
    if climate_zone == "tropical":
        return tropical_species[:limit]
    else:
        return temperate_species[:limit]

@api_router.post("/plots", response_model=PlotDesign)
async def create_plot_design(plot: PlotDesignCreate):
    plot_dict = plot.dict()
    plot_obj = PlotDesign(**plot_dict)
    await db.plots.insert_one(plot_obj.dict())
    return plot_obj

@api_router.get("/plots", response_model=List[PlotDesign])
async def get_plot_designs():
    plots = await db.plots.find().to_list(1000)
    return [PlotDesign(**plot) for plot in plots]

@api_router.get("/plots/{plot_id}/3d-design")
async def get_3d_design(plot_id: str):
    """Generate 3D design configuration for a plot"""
    plot = await db.plots.find_one({"id": plot_id})
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    
    # Generate 3D layout based on plot size and species
    plot_size = plot["plot_size"]
    species_ids = plot["selected_species"]
    
    # Calculate planting density (Miyawaki method: 3-5 plants per sq meter)
    planting_density = 4  # plants per sq meter
    total_plants = int(plot_size * planting_density)
    
    # Mock 3D design data
    design_3d = {
        "plot_id": plot_id,
        "plot_size": plot_size,
        "total_plants": total_plants,
        "layers": {
            "canopy": {"height": "15-30m", "density": 0.1, "species_count": int(total_plants * 0.1)},
            "sub_canopy": {"height": "5-15m", "density": 0.2, "species_count": int(total_plants * 0.2)},
            "shrub": {"height": "1-5m", "density": 0.3, "species_count": int(total_plants * 0.3)},
            "ground": {"height": "0-1m", "density": 0.4, "species_count": int(total_plants * 0.4)}
        },
        "plant_spacing": "0.5m x 0.5m",
        "visualization_url": f"https://3d-forest-viz.com/plot/{plot_id}",  # Mock URL
        "estimated_growth_years": 3
    }
    
    return design_3d

@api_router.post("/projects", response_model=PlantationProject)
async def create_project(project: PlantationProjectCreate):
    project_dict = project.dict()
    project_obj = PlantationProject(**project_dict)
    await db.projects.insert_one(project_obj.dict())
    return project_obj

@api_router.get("/projects", response_model=List[PlantationProject])
async def get_projects():
    projects = await db.projects.find().to_list(1000)
    return [PlantationProject(**project) for project in projects]

@api_router.get("/weather/{location_id}")
async def get_weather_data(location_id: str):
    """Get current weather data for a location (mocked for MVP)"""
    # Mock weather data
    weather_data = {
        "location_id": location_id,
        "temperature": 25.5,
        "humidity": 65,
        "rainfall": 2.5,
        "wind_speed": 8.2,
        "weather_condition": "Partly Cloudy",
        "forecast": [
            {"day": "Today", "temp": 25, "condition": "Partly Cloudy", "rain_chance": 20},
            {"day": "Tomorrow", "temp": 27, "condition": "Sunny", "rain_chance": 5},
            {"day": "Day 3", "temp": 23, "condition": "Rainy", "rain_chance": 80}
        ],
        "planting_advice": "Good conditions for watering. Avoid heavy activities during rain forecast."
    }
    return weather_data

@api_router.get("/soil/guidance")
async def get_soil_guidance(soil_type: SoilType = Query(...)):
    """Get soil preparation guidance based on soil type"""
    guidance = {
        "clay": {
            "preparation": [
                "Add organic compost to improve drainage",
                "Mix in sand to reduce compaction",
                "Create raised beds for better drainage",
                "Add perlite or vermiculite for aeration"
            ],
            "ph_adjustment": "Clay soil is often alkaline, add sulfur if needed",
            "nutrients": "Rich in nutrients but may need phosphorus",
            "drainage": "Poor drainage - needs improvement"
        },
        "sandy": {
            "preparation": [
                "Add organic matter to retain moisture",
                "Mix in compost for nutrient retention",
                "Add clay to improve water holding capacity",
                "Use mulch to prevent erosion"
            ],
            "ph_adjustment": "Often acidic, add lime if needed",
            "nutrients": "Low in nutrients, needs regular fertilization",
            "drainage": "Excellent drainage but may dry out quickly"
        },
        "loam": {
            "preparation": [
                "Add compost to maintain fertility",
                "Light tilling to prepare planting area",
                "Test pH and adjust if needed",
                "Add mulch after planting"
            ],
            "ph_adjustment": "Usually neutral, minimal adjustment needed",
            "nutrients": "Well-balanced nutrients",
            "drainage": "Good drainage and water retention"
        },
        "rocky": {
            "preparation": [
                "Remove large rocks and debris",
                "Add significant amounts of topsoil",
                "Create terraced areas if on slopes",
                "Use raised beds for better growing conditions"
            ],
            "ph_adjustment": "Varies widely, test and adjust accordingly",
            "nutrients": "Usually low in nutrients, needs enrichment",
            "drainage": "Can be poor or excellent depending on rock type"
        }
    }
    
    return {
        "soil_type": soil_type,
        "guidance": guidance[soil_type],
        "miyawaki_tips": [
            "Create 1-meter deep planting pits",
            "Mix native soil with 30% organic matter",
            "Ensure proper drainage before planting",
            "Add mycorrhizal fungi for better root development"
        ]
    }

@api_router.get("/timeline/{project_id}")
async def get_project_timeline(project_id: str):
    """Get care timeline for a project"""
    # Mock timeline data
    timeline = {
        "project_id": project_id,
        "phases": [
            {
                "phase": "Preparation",
                "duration": "2 weeks",
                "tasks": [
                    "Site survey and soil testing",
                    "Soil preparation and amendment",
                    "Species selection and procurement",
                    "Layout marking and pit digging"
                ]
            },
            {
                "phase": "Planting",
                "duration": "1 week",
                "tasks": [
                    "Plant according to Miyawaki layers",
                    "Ensure proper spacing (0.5m x 0.5m)",
                    "Water thoroughly after planting",
                    "Apply mulch around plants"
                ]
            },
            {
                "phase": "Intensive Care",
                "duration": "3 years",
                "tasks": [
                    "Daily watering for first month",
                    "Weekly watering for next 6 months",
                    "Monthly monitoring and pruning",
                    "Weed control and pest management"
                ]
            },
            {
                "phase": "Monitoring",
                "duration": "Ongoing",
                "tasks": [
                    "Monthly health assessments",
                    "Seasonal pruning as needed",
                    "Weather-based care adjustments",
                    "Growth tracking and documentation"
                ]
            }
        ],
        "milestones": [
            {"month": 1, "expected": "95% survival rate"},
            {"month": 6, "expected": "Visible growth and branching"},
            {"month": 12, "expected": "Forest floor coverage"},
            {"month": 36, "expected": "Self-sustaining ecosystem"}
        ]
    }
    return timeline

@api_router.get("/alerts/{project_id}")
async def get_project_alerts(project_id: str):
    """Get alerts for a project"""
    # Mock alerts data
    alerts = [
        {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "alert_type": "weather",
            "severity": "medium",
            "message": "Heavy rain expected tomorrow. Ensure proper drainage.",
            "resolved": False,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "alert_type": "maintenance",
            "severity": "low",
            "message": "Monthly pruning due for shrub layer plants.",
            "resolved": False,
            "created_at": datetime.utcnow()
        }
    ]
    return alerts

@api_router.get("/learning/resources")
async def get_learning_resources():
    """Get educational resources about Miyawaki method"""
    resources = {
        "articles": [
            {
                "title": "Understanding the Miyawaki Method",
                "description": "Learn about the revolutionary forest restoration technique",
                "url": "https://example.com/miyawaki-method",
                "category": "basics"
            },
            {
                "title": "Native Species Selection Guide",
                "description": "How to choose the right plants for your region",
                "url": "https://example.com/species-selection",
                "category": "species"
            },
            {
                "title": "Soil Preparation for Dense Forests",
                "description": "Essential soil preparation techniques",
                "url": "https://example.com/soil-prep",
                "category": "soil"
            }
        ],
        "videos": [
            {
                "title": "Miyawaki Forest Creation Process",
                "description": "Step-by-step video guide",
                "url": "https://example.com/video1",
                "duration": "15 minutes"
            },
            {
                "title": "3 Years of Forest Growth Time-lapse",
                "description": "See the transformation over time",
                "url": "https://example.com/video2",
                "duration": "5 minutes"
            }
        ],
        "case_studies": [
            {
                "title": "Urban Forest in Tokyo",
                "description": "Successful city center forest restoration",
                "location": "Tokyo, Japan",
                "size": "500 sq meters",
                "success_rate": "98%"
            },
            {
                "title": "Bangalore Tech Park Forest",
                "description": "Corporate campus forest implementation",
                "location": "Bangalore, India",
                "size": "2000 sq meters",
                "success_rate": "96%"
            }
        ]
    }
    return resources

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()