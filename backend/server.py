from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import httpx
import asyncio
from enum import Enum
import jwt
import bcrypt
import re
from twilio.rest import Client
import json


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Twilio setup
twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')

# Initialize Twilio client (mock for development)
if twilio_account_sid and twilio_account_sid != "mock_account_sid":
    twilio_client = Client(twilio_account_sid, twilio_auth_token)
else:
    twilio_client = None

# JWT Settings
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security
security = HTTPBearer()

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

class AlertType(str, Enum):
    WEATHER = "weather"
    DAMAGE = "damage"
    MAINTENANCE = "maintenance"
    DISEASE = "disease"

class UnitType(str, Enum):
    METER = "meter"
    FEET = "feet"
    INCH = "inch"

# User Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    age: int
    email: EmailStr
    phone_number: str
    password_hash: str
    notification_settings: Dict[str, bool] = Field(default_factory=lambda: {
        "weather_alerts": True,
        "maintenance_reminders": True,
        "damage_alerts": True,
        "sms_enabled": True,
        "email_enabled": True
    })
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    name: str
    age: int
    email: EmailStr
    phone_number: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserSettings(BaseModel):
    notification_settings: Dict[str, bool]

class Token(BaseModel):
    access_token: str
    token_type: str

# Existing Models
class Location(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    latitude: float
    longitude: float
    address: str
    city: str
    state: str
    country: str
    user_id: str
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
    plot_size: float
    unit_type: UnitType = UnitType.METER
    planting_method: PlantingMethod
    soil_type: SoilType
    selected_species: List[str]
    layout_config: Dict[str, Any]
    visualization_3d: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PlantationProject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    plot_design_id: str
    project_name: str
    manager_name: str
    manager_phone: str
    status: str = "planned"
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
    user_id: str
    project_id: str
    alert_type: AlertType
    severity: str
    message: str
    resolved: bool = False
    sms_sent: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SMSAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    phone_number: str
    message: str
    status: str = "pending"  # pending, sent, failed
    sent_at: Optional[datetime] = None
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
    location_id: str
    plot_size: float
    unit_type: UnitType = UnitType.METER
    planting_method: PlantingMethod
    soil_type: SoilType
    selected_species: List[str]

class PlantationProjectCreate(BaseModel):
    plot_design_id: str
    project_name: str
    manager_name: str
    manager_phone: str

class AlertCreate(BaseModel):
    project_id: str
    alert_type: AlertType
    severity: str
    message: str

# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def validate_phone_number(phone: str) -> bool:
    # Simple phone number validation
    phone_pattern = re.compile(r'^[\+]?[1-9][\d]{0,15}$')
    return phone_pattern.match(phone) is not None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def send_sms_alert(user_id: str, message: str):
    """Send SMS alert to user"""
    try:
        # Get user details
        user = await db.users.find_one({"id": user_id})
        if not user or not user.get("notification_settings", {}).get("sms_enabled", False):
            return False
        
        phone_number = user["phone_number"]
        
        # Create SMS record
        sms_record = SMSAlert(
            user_id=user_id,
            phone_number=phone_number,
            message=message
        )
        
        if twilio_client:
            # Send real SMS
            try:
                message = twilio_client.messages.create(
                    body=message,
                    from_=twilio_phone_number,
                    to=phone_number
                )
                sms_record.status = "sent"
                sms_record.sent_at = datetime.utcnow()
            except Exception as e:
                sms_record.status = "failed"
                logging.error(f"SMS send failed: {str(e)}")
        else:
            # Mock SMS for development
            sms_record.status = "sent"
            sms_record.sent_at = datetime.utcnow()
            logging.info(f"Mock SMS sent to {phone_number}: {message}")
        
        await db.sms_alerts.insert_one(sms_record.dict())
        return sms_record.status == "sent"
        
    except Exception as e:
        logging.error(f"SMS alert failed: {str(e)}")
        return False

def convert_to_meters(value: float, unit: UnitType) -> float:
    """Convert different units to meters"""
    if unit == UnitType.FEET:
        return value * 0.3048
    elif unit == UnitType.INCH:
        return value * 0.0254
    else:  # METER
        return value

def generate_3d_visualization(plot_size_meters: float, selected_species: List[str], planting_method: PlantingMethod) -> Dict[str, Any]:
    """Generate 3D visualization data"""
    
    # Calculate planting density based on method
    if planting_method == PlantingMethod.TERRACE:
        planting_density = 6  # Higher density for terrace
    else:
        planting_density = 4  # Standard Miyawaki density
    
    total_plants = int(plot_size_meters * planting_density)
    
    # Generate 3D structure
    visualization = {
        "plot_dimensions": {
            "area_meters": plot_size_meters,
            "estimated_length": round((plot_size_meters ** 0.5), 2),
            "estimated_width": round((plot_size_meters ** 0.5), 2)
        },
        "planting_structure": {
            "total_plants": total_plants,
            "density_per_sqm": planting_density,
            "spacing": "0.5m x 0.5m" if planting_method == PlantingMethod.GROUND else "0.4m x 0.4m"
        },
        "layers": {
            "canopy_layer": {
                "height_range": "15-30m",
                "plant_count": int(total_plants * 0.1),
                "species_ratio": 0.1,
                "color": "#2d5a27"
            },
            "sub_canopy": {
                "height_range": "5-15m", 
                "plant_count": int(total_plants * 0.2),
                "species_ratio": 0.2,
                "color": "#4a7c59"
            },
            "shrub_layer": {
                "height_range": "1-5m",
                "plant_count": int(total_plants * 0.3),
                "species_ratio": 0.3,
                "color": "#6b8e6b"
            },
            "ground_layer": {
                "height_range": "0-1m",
                "plant_count": int(total_plants * 0.4),
                "species_ratio": 0.4,
                "color": "#8fa68f"
            }
        },
        "growth_timeline": {
            "6_months": "Initial establishment",
            "1_year": "20% of mature size",
            "2_years": "60% of mature size",
            "3_years": "80% mature, self-sustaining"
        },
        "visualization_url": f"https://3d-miyawaki-viz.com/plot/{uuid.uuid4()}",
        "method_specific": {
            "terrace_levels": 3 if planting_method == PlantingMethod.TERRACE else 0,
            "drainage_system": "Terraced with proper drainage" if planting_method == PlantingMethod.TERRACE else "Ground level drainage"
        }
    }
    
    return visualization

# Authentication Routes
@api_router.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate phone number
    if not validate_phone_number(user_data.phone_number):
        raise HTTPException(status_code=400, detail="Invalid phone number format")
    
    # Create user
    user_dict = user_data.dict()
    user_dict["password_hash"] = hash_password(user_data.password)
    del user_dict["password"]
    
    user_obj = User(**user_dict)
    await db.users.insert_one(user_obj.dict())
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_obj.id}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_obj.id,
        "message": "User registered successfully"
    }

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    # Find user
    user = await db.users.find_one({"email": user_credentials.email})
    if not user or not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me")
async def get_current_user_info(user_id: str = Depends(get_current_user)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Remove sensitive data
    user_safe = {k: v for k, v in user.items() if k not in ["password_hash"]}
    return user_safe

@api_router.put("/auth/settings")
async def update_user_settings(settings: UserSettings, user_id: str = Depends(get_current_user)):
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"notification_settings": settings.notification_settings, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Settings updated successfully"}

@api_router.delete("/auth/delete-account")
async def delete_user_account(user_id: str = Depends(get_current_user)):
    # Delete user and all related data
    await db.users.delete_one({"id": user_id})
    await db.locations.delete_many({"user_id": user_id})
    await db.plots.delete_many({"user_id": user_id})
    await db.projects.delete_many({"user_id": user_id})
    await db.alerts.delete_many({"user_id": user_id})
    await db.sms_alerts.delete_many({"user_id": user_id})
    
    return {"message": "Account deleted successfully"}

# Location Routes
@api_router.post("/locations", response_model=Location)
async def create_location(location: LocationCreate, user_id: str = Depends(get_current_user)):
    location_dict = location.dict()
    location_dict["user_id"] = user_id
    location_obj = Location(**location_dict)
    await db.locations.insert_one(location_obj.dict())
    return location_obj

@api_router.get("/locations", response_model=List[Location])
async def get_locations(user_id: str = Depends(get_current_user)):
    locations = await db.locations.find({"user_id": user_id}).to_list(1000)
    return [Location(**location) for location in locations]

# Main Routes
@api_router.get("/")
async def root():
    return {"message": "Miyawaki Forest Planner API"}

@api_router.get("/species/native")
async def get_native_species(
    latitude: float = Query(..., description="Latitude of the location"),
    longitude: float = Query(..., description="Longitude of the location"),
    limit: int = Query(20, description="Number of species to return")
):
    """Get native species for a specific location using climate-based recommendations"""
    try:
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
async def create_plot_design(plot: PlotDesignCreate, user_id: str = Depends(get_current_user)):
    plot_dict = plot.dict()
    plot_dict["user_id"] = user_id
    
    # Convert plot size to meters for calculations
    plot_size_meters = convert_to_meters(plot.plot_size, plot.unit_type)
    
    # Generate default layout_config
    plot_dict["layout_config"] = {
        "grid_pattern": "miyawaki_dense",
        "spacing": "0.5m x 0.5m" if plot.planting_method == PlantingMethod.GROUND else "0.4m x 0.4m",
        "layer_distribution": {
            "canopy": 0.1,
            "sub_canopy": 0.2,
            "shrub": 0.3,
            "ground": 0.4
        }
    }
    
    # Generate 3D visualization
    plot_dict["visualization_3d"] = generate_3d_visualization(
        plot_size_meters, 
        plot.selected_species, 
        plot.planting_method
    )
    
    plot_obj = PlotDesign(**plot_dict)
    await db.plots.insert_one(plot_obj.dict())
    return plot_obj

@api_router.get("/plots", response_model=List[PlotDesign])
async def get_plot_designs(user_id: str = Depends(get_current_user)):
    plots = await db.plots.find({"user_id": user_id}).to_list(1000)
    return [PlotDesign(**plot) for plot in plots]

@api_router.get("/plots/{plot_id}/3d-design")
async def get_3d_design(plot_id: str, user_id: str = Depends(get_current_user)):
    """Get 3D design visualization for a plot"""
    plot = await db.plots.find_one({"id": plot_id, "user_id": user_id})
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    
    return plot.get("visualization_3d", {})

@api_router.post("/projects", response_model=PlantationProject)
async def create_project(project: PlantationProjectCreate, user_id: str = Depends(get_current_user)):
    project_dict = project.dict()
    project_dict["user_id"] = user_id
    project_obj = PlantationProject(**project_dict)
    await db.projects.insert_one(project_obj.dict())
    
    # Send welcome SMS
    await send_sms_alert(
        user_id, 
        f"Welcome to Miyawaki Forest Planner! Your project '{project.project_name}' has been created successfully."
    )
    
    return project_obj

@api_router.get("/projects", response_model=List[PlantationProject])
async def get_projects(user_id: str = Depends(get_current_user)):
    projects = await db.projects.find({"user_id": user_id}).to_list(1000)
    return [PlantationProject(**project) for project in projects]

@api_router.get("/weather/{location_id}")
async def get_weather_data(location_id: str, user_id: str = Depends(get_current_user)):
    """Get current weather data for a location"""
    # Mock weather data with potential alerts
    weather_data = {
        "location_id": location_id,
        "temperature": 25.5,
        "humidity": 85,  # High humidity - potential alert
        "rainfall": 15.2,  # Heavy rain - potential alert
        "wind_speed": 25.8,  # Strong wind - potential alert
        "weather_condition": "Heavy Rain",
        "forecast": [
            {"day": "Today", "temp": 25, "condition": "Heavy Rain", "rain_chance": 90},
            {"day": "Tomorrow", "temp": 27, "condition": "Thunderstorms", "rain_chance": 85},
            {"day": "Day 3", "temp": 23, "condition": "Partly Cloudy", "rain_chance": 20}
        ],
        "alerts": [],
        "planting_advice": "Avoid heavy activities. Check drainage systems."
    }
    
    # Generate weather alerts
    if weather_data["rainfall"] > 10:
        weather_data["alerts"].append({
            "type": "weather",
            "severity": "high",
            "message": "Heavy rainfall detected! Check drainage and protect young plants."
        })
    
    if weather_data["wind_speed"] > 20:
        weather_data["alerts"].append({
            "type": "weather", 
            "severity": "medium",
            "message": "Strong winds detected. Secure plant supports and check for damage."
        })
    
    if weather_data["humidity"] > 80:
        weather_data["alerts"].append({
            "type": "weather",
            "severity": "medium", 
            "message": "High humidity levels may increase disease risk. Monitor plants closely."
        })
    
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
async def get_project_timeline(project_id: str, user_id: str = Depends(get_current_user)):
    """Get care timeline for a project"""
    project = await db.projects.find_one({"id": project_id, "user_id": user_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
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
                    "Ensure proper spacing",
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

@api_router.post("/alerts")
async def create_alert(alert: AlertCreate, user_id: str = Depends(get_current_user)):
    """Create a new alert for a project"""
    alert_dict = alert.dict()
    alert_dict["user_id"] = user_id
    alert_obj = Alert(**alert_dict)
    await db.alerts.insert_one(alert_obj.dict())
    
    # Send SMS alert
    sms_sent = await send_sms_alert(user_id, alert.message)
    if sms_sent:
        await db.alerts.update_one(
            {"id": alert_obj.id},
            {"$set": {"sms_sent": True}}
        )
    
    return alert_obj

@api_router.get("/alerts")
async def get_user_alerts(user_id: str = Depends(get_current_user)):
    """Get all alerts for the current user"""
    alerts = await db.alerts.find({"user_id": user_id}).to_list(1000)
    return [Alert(**alert) for alert in alerts]

@api_router.get("/alerts/{project_id}")
async def get_project_alerts(project_id: str, user_id: str = Depends(get_current_user)):
    """Get alerts for a specific project"""
    alerts = await db.alerts.find({"project_id": project_id, "user_id": user_id}).to_list(1000)
    return [Alert(**alert) for alert in alerts]

@api_router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, user_id: str = Depends(get_current_user)):
    """Mark an alert as resolved"""
    result = await db.alerts.update_one(
        {"id": alert_id, "user_id": user_id},
        {"$set": {"resolved": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert resolved successfully"}

@api_router.post("/simulate-plantation-issues")
async def simulate_plantation_issues(user_id: str = Depends(get_current_user)):
    """Simulate plantation issues for demonstration"""
    
    # Get user's projects
    projects = await db.projects.find({"user_id": user_id}).to_list(10)
    if not projects:
        raise HTTPException(status_code=404, detail="No projects found")
    
    project_id = projects[0]["id"]
    
    # Create sample alerts
    sample_alerts = [
        {
            "project_id": project_id,
            "alert_type": "weather",
            "severity": "high",
            "message": "⚠️ WEATHER ALERT: Heavy rainfall expected in next 24 hours. Check drainage systems and protect young plants from waterlogging."
        },
        {
            "project_id": project_id,
            "alert_type": "damage",
            "severity": "medium",
            "message": "🌱 DAMAGE ALERT: Pest infestation detected on shrub layer plants. Immediate inspection and treatment required."
        },
        {
            "project_id": project_id,
            "alert_type": "maintenance",
            "severity": "low",
            "message": "📅 MAINTENANCE REMINDER: Monthly pruning and health check scheduled for your Miyawaki forest."
        }
    ]
    
    created_alerts = []
    for alert_data in sample_alerts:
        alert_dict = alert_data.copy()
        alert_dict["user_id"] = user_id
        alert_obj = Alert(**alert_dict)
        await db.alerts.insert_one(alert_obj.dict())
        created_alerts.append(alert_obj)
        
        # Send SMS alert
        await send_sms_alert(user_id, alert_data["message"])
    
    return {
        "message": "Plantation issues simulated successfully",
        "alerts_created": len(created_alerts),
        "sms_sent": True
    }

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