from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import jwt
import bcrypt
from sample_data_generator import generate_comprehensive_sample_data
import json
import re
import math

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = "travel_app_secret_key_2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    full_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class Agent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # "travel" or "transport"
    description: str
    rating: float
    total_bookings: int
    location: str
    contact_phone: str
    contact_email: str
    image_base64: str
    services_offered: List[str] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Package(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    title: str
    description: str
    price: float
    duration: str
    duration_days: int = 0  # Parsed from duration string
    destination: str
    image_base64: str
    features: List[str]
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RibbonContent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    type: str  # "filter", "recommendation", "explore"
    items: List[dict]
    order: int
    is_active: bool = True

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    agent_id: str
    package_id: str
    status: str  # "pending", "confirmed", "completed", "cancelled"
    booking_date: datetime
    travel_date: datetime
    total_amount: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BudgetTravelRequest(BaseModel):
    budget: float
    num_persons: int
    num_days: int
    place: Optional[str] = None

class PackageCombination(BaseModel):
    packages: List[dict]  # List of package details with pricing
    transport_segments: List[dict]  # List of transport between packages
    total_cost: float
    total_days: int
    savings: float  # How much budget is left
    itinerary_summary: str

class BudgetTravelResponse(BaseModel):
    request: BudgetTravelRequest
    combinations: List[PackageCombination]
    total_combinations_found: int
    message: str

# Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def parse_duration_to_days(duration_str: str) -> int:
    """Parse duration string like '5 days 4 nights' or '3 days' to number of days"""
    # Extract numbers from duration string
    numbers = re.findall(r'\d+', duration_str.lower())
    if numbers:
        return int(numbers[0])  # First number is usually days
    return 1  # Default to 1 day

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat/2) * math.sin(dlat/2) + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2) * math.sin(dlon/2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

def calculate_transport_cost(distance_km: float, transport_type: str = "taxi") -> float:
    """Calculate transport cost based on distance and type"""
    rates = {
        "taxi": 15,  # ₹15 per km
        "bus": 5,    # ₹5 per km
        "other": 10  # ₹10 per km default
    }
    rate = rates.get(transport_type, rates["other"])
    return distance_km * rate

async def load_location_data():
    """Load location data from JSON file"""
    try:
        with open(ROOT_DIR / 'location_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

async def find_budget_combinations(
    budget: float, 
    num_persons: int, 
    num_days: int, 
    place_filter: Optional[str] = None
) -> List[PackageCombination]:
    """Find optimal package combinations within budget and days"""
    combinations = []
    
    # Get all active travel packages
    query = {"is_active": True, "agent_id": {"$exists": True}}
    
    # Filter by place if specified
    if place_filter:
        query["destination"] = {"$regex": place_filter, "$options": "i"}
    
    packages = await db.packages.find(query).to_list(100)
    
    # Get transport packages for inter-city travel
    transport_query = {"is_active": True}
    transport_agents = await db.agents.find({"type": "transport", "is_active": True}).to_list(50)
    transport_agent_ids = [agent["id"] for agent in transport_agents]
    
    transport_packages = await db.packages.find({
        "agent_id": {"$in": transport_agent_ids},
        "is_active": True
    }).to_list(100)
    
    # Parse package durations
    for package in packages:
        package['duration_days'] = parse_duration_to_days(package['duration'])
        package['cost_per_person'] = package['price']
        package['total_cost'] = package['price'] * num_persons
    
    # Find combinations using dynamic programming approach
    valid_packages = [p for p in packages if p['total_cost'] <= budget and p['duration_days'] <= num_days]
    
    # Simple greedy approach for now - can be enhanced with DP
    for i, pkg1 in enumerate(valid_packages):
        if pkg1['duration_days'] == num_days and pkg1['total_cost'] <= budget:
            # Single package fits perfectly
            combination = PackageCombination(
                packages=[{
                    "id": pkg1['id'],
                    "title": pkg1['title'],
                    "destination": pkg1['destination'],
                    "duration_days": pkg1['duration_days'],
                    "cost": pkg1['total_cost'],
                    "agent_id": pkg1['agent_id']
                }],
                transport_segments=[],
                total_cost=pkg1['total_cost'],
                total_days=pkg1['duration_days'],
                savings=budget - pkg1['total_cost'],
                itinerary_summary=f"{pkg1['title']} for {pkg1['duration_days']} days"
            )
            combinations.append(combination)
        
        # Look for combinations with other packages
        remaining_budget = budget - pkg1['total_cost']
        remaining_days = num_days - pkg1['duration_days']
        
        if remaining_days > 0 and remaining_budget > 0:
            for j, pkg2 in enumerate(valid_packages[i+1:], i+1):
                if pkg2['duration_days'] <= remaining_days and pkg2['total_cost'] <= remaining_budget:
                    # Calculate transport cost between destinations
                    transport_cost = 0
                    transport_segments = []
                    
                    if pkg1['destination'].lower() != pkg2['destination'].lower():
                        # Estimate transport cost (simplified)
                        estimated_distance = 200  # Default 200km between cities
                        transport_cost = calculate_transport_cost(estimated_distance) * num_persons
                        
                        if transport_cost <= remaining_budget - pkg2['total_cost']:
                            transport_segments.append({
                                "from": pkg1['destination'],
                                "to": pkg2['destination'],
                                "cost": transport_cost,
                                "distance_km": estimated_distance,
                                "type": "taxi"
                            })
                    
                    total_combination_cost = pkg1['total_cost'] + pkg2['total_cost'] + transport_cost
                    total_combination_days = pkg1['duration_days'] + pkg2['duration_days']
                    
                    if total_combination_cost <= budget and total_combination_days <= num_days:
                        combination = PackageCombination(
                            packages=[
                                {
                                    "id": pkg1['id'],
                                    "title": pkg1['title'],
                                    "destination": pkg1['destination'],
                                    "duration_days": pkg1['duration_days'],
                                    "cost": pkg1['total_cost'],
                                    "agent_id": pkg1['agent_id']
                                },
                                {
                                    "id": pkg2['id'],
                                    "title": pkg2['title'],
                                    "destination": pkg2['destination'],
                                    "duration_days": pkg2['duration_days'],
                                    "cost": pkg2['total_cost'],
                                    "agent_id": pkg2['agent_id']
                                }
                            ],
                            transport_segments=transport_segments,
                            total_cost=total_combination_cost,
                            total_days=total_combination_days,
                            savings=budget - total_combination_cost,
                            itinerary_summary=f"{pkg1['title']} ({pkg1['duration_days']} days) + {pkg2['title']} ({pkg2['duration_days']} days)"
                        )
                        combinations.append(combination)
    
    # Sort by best value (lowest cost, highest savings)
    combinations.sort(key=lambda x: (-x.savings, x.total_cost))
    
    return combinations[:5]  # Return top 5 combinations

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"username": username})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Authentication Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    # Create user
    hashed_password = hash_password(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name
    )
    
    await db.users.insert_one(user.dict())
    
    # Create token
    access_token = create_access_token(data={"sub": user.username})
    user_dict = user.dict()
    del user_dict["password_hash"]
    
    return {"access_token": access_token, "token_type": "bearer", "user": user_dict}

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user["username"]})
    # Remove MongoDB ObjectId and password_hash for JSON serialization
    if "_id" in user:
        del user["_id"]
    del user["password_hash"]
    
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    # Remove MongoDB ObjectId and password_hash for JSON serialization
    if "_id" in current_user:
        del current_user["_id"]
    if "password_hash" in current_user:
        del current_user["password_hash"]
    return current_user

# Agent Routes
@api_router.get("/agents", response_model=List[Agent])
async def get_agents(agent_type: Optional[str] = None):
    query = {"is_active": True}
    if agent_type:
        query["type"] = agent_type
    
    agents = await db.agents.find(query).to_list(100)
    return [Agent(**agent) for agent in agents]

@api_router.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str):
    agent = await db.agents.find_one({"id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return Agent(**agent)

# Package Routes
@api_router.get("/packages", response_model=List[Package])
async def get_packages(agent_id: Optional[str] = None):
    query = {"is_active": True}
    if agent_id:
        query["agent_id"] = agent_id
    
    packages = await db.packages.find(query).to_list(100)
    return [Package(**package) for package in packages]

@api_router.get("/packages/{package_id}", response_model=Package)
async def get_package(package_id: str):
    package = await db.packages.find_one({"id": package_id})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return Package(**package)

# Ribbon Content Routes
@api_router.get("/ribbons", response_model=List[RibbonContent])
async def get_ribbons():
    ribbons = await db.ribbons.find({"is_active": True}).sort("order", 1).to_list(100)
    return [RibbonContent(**ribbon) for ribbon in ribbons]

# Booking Routes
@api_router.post("/bookings")
async def create_booking(
    package_id: str,
    travel_date: datetime,
    current_user: dict = Depends(get_current_user)
):
    package = await db.packages.find_one({"id": package_id})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    booking = Booking(
        user_id=current_user["id"],
        agent_id=package["agent_id"],
        package_id=package_id,
        status="pending",
        booking_date=datetime.utcnow(),
        travel_date=travel_date,
        total_amount=package["price"]
    )
    
    await db.bookings.insert_one(booking.dict())
    return {"message": "Booking created successfully", "booking_id": booking.id}

@api_router.get("/bookings", response_model=List[Booking])
async def get_user_bookings(current_user: dict = Depends(get_current_user)):
    bookings = await db.bookings.find({"user_id": current_user["id"]}).to_list(100)
    return [Booking(**booking) for booking in bookings]

# Budget Travel Routes
@api_router.post("/budget-travel", response_model=BudgetTravelResponse)
async def find_budget_travel_packages(request: BudgetTravelRequest):
    """Find optimal package combinations within budget and time constraints"""
    try:
        combinations = await find_budget_combinations(
            budget=request.budget,
            num_persons=request.num_persons,
            num_days=request.num_days,
            place_filter=request.place
        )
        
        if not combinations:
            return BudgetTravelResponse(
                request=request,
                combinations=[],
                total_combinations_found=0,
                message=f"No suitable package combinations found within ₹{request.budget} budget for {request.num_persons} persons and {request.num_days} days."
            )
        
        return BudgetTravelResponse(
            request=request,
            combinations=combinations,
            total_combinations_found=len(combinations),
            message=f"Found {len(combinations)} optimal package combinations within your budget!"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding budget combinations: {str(e)}")

@api_router.get("/budget-travel/preview")
async def get_budget_travel_preview():
    """Get a preview of available destinations and price ranges for budget travel"""
    try:
        # Get all active packages with basic stats
        packages = await db.packages.find({"is_active": True}).to_list(100)
        
        destinations = set()
        min_price = float('inf')
        max_price = 0
        duration_stats = {}
        
        for package in packages:
            destinations.add(package['destination'])
            min_price = min(min_price, package['price'])
            max_price = max(max_price, package['price'])
            
            duration_days = parse_duration_to_days(package['duration'])
            duration_stats[duration_days] = duration_stats.get(duration_days, 0) + 1
        
        return {
            "available_destinations": list(destinations),
            "price_range": {
                "min": min_price if min_price != float('inf') else 0,
                "max": max_price
            },
            "popular_durations": sorted(duration_stats.items(), key=lambda x: x[1], reverse=True)[:5],
            "total_packages": len(packages),
            "suggestion": f"Budget range: ₹{min_price}-₹{max_price} per person. Popular destinations: {', '.join(list(destinations)[:3])}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting budget preview: {str(e)}")

async def populate_sample_data():
    """Populate the database with comprehensive sample data"""
    
    # Clear existing data
    await db.agents.delete_many({})
    await db.packages.delete_many({})
    await db.ribbons.delete_many({})
    
    # Generate comprehensive sample agents (100 total)
    agents, agent_ids = generate_comprehensive_sample_data()
    
    # Insert agents
    await db.agents.insert_many(agents)
    
    # Select some agent IDs for packages
    travel_agent_ids = [agent['id'] for agent in agents if agent['type'] == 'travel'][:10]
    transport_agent_ids = [agent['id'] for agent in agents if agent['type'] == 'transport'][:5]

# Initialize sample data
@api_router.post("/init-data")
async def initialize_sample_data():
    # Clear existing data
    await db.agents.delete_many({})
    await db.packages.delete_many({})
    await db.ribbons.delete_many({})
    
    # Sample Travel Agents
    travel_agent_1_id = str(uuid.uuid4())
    travel_agent_2_id = str(uuid.uuid4())
    transport_agent_1_id = str(uuid.uuid4())
    
    travel_agents = [
        {
            "id": travel_agent_1_id,
            "name": "Adventure Tours India",
            "type": "travel",
            "description": "Specializing in adventure and trekking tours across India",
            "rating": 4.5,
            "total_bookings": 250,
            "location": "Shimla, Himachal Pradesh",
            "contact_phone": "+91-9876543210",
            "contact_email": "info@adventuretours.com",
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": travel_agent_2_id,
            "name": "Royal Rajasthan Tours",
            "type": "travel",
            "description": "Heritage and cultural tours of Rajasthan",
            "rating": 4.8,
            "total_bookings": 180,
            "location": "Jaipur, Rajasthan",
            "contact_phone": "+91-9123456789",
            "contact_email": "info@royalrajasthan.com",
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    # Sample Transport Agents
    transport_agents = [
        {
            "id": transport_agent_1_id,
            "name": "Swift Cabs",
            "type": "transport",
            "description": "Reliable taxi and cab services across major cities",
            "rating": 4.2,
            "total_bookings": 500,
            "location": "Delhi, Mumbai, Bangalore",
            "contact_phone": "+91-8765432109",
            "contact_email": "booking@swiftcabs.com",
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    # Insert agents
    await db.agents.insert_many(travel_agents + transport_agents)
    
    # Create dynamic agent ID lists
    travel_agent_ids = [agent['id'] for agent in travel_agents]
    transport_agent_ids = [agent['id'] for agent in transport_agents]
    
    # Sample Packages using dynamic agent IDs
    packages = [
        # Adventure Tours India packages
        {
            "id": str(uuid.uuid4()),
            "agent_id": travel_agent_ids[0] if travel_agent_ids else str(uuid.uuid4()),
            "title": "Shimla Manali Adventure Trek",
            "description": "5-day adventure trekking tour covering beautiful mountain trails with camping and local cuisine",
            "price": 15000,
            "duration": "5 days 4 nights",
            "duration_days": 5,
            "destination": "Shimla - Manali",
            "latitude": 31.1048,
            "longitude": 77.1734,
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "features": ["Professional guide", "Camping equipment", "All meals", "Transportation", "First aid kit"],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "agent_id": travel_agent_ids[1] if len(travel_agent_ids) > 1 else str(uuid.uuid4()),
            "title": "Himalayan Base Camp Trek",
            "description": "Ultimate 12-day trekking experience to Himalayan base camps with expert guides",
            "price": 35000,
            "duration": "12 days 11 nights",
            "duration_days": 12,
            "destination": "Himachal Pradesh",
            "latitude": 32.2431,
            "longitude": 77.1892,
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "features": ["Expert mountaineer guide", "High altitude gear", "All meals", "Permits", "Medical support", "Photography service"],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        # Add Goa packages for budget travel example
        {
            "id": str(uuid.uuid4()),
            "agent_id": travel_agent_ids[0] if travel_agent_ids else str(uuid.uuid4()),
            "title": "Goa Beach Adventure",
            "description": "3-day beach adventure with water sports and local sightseeing",
            "price": 10000,
            "duration": "3 days 2 nights",
            "duration_days": 3,
            "destination": "Goa",
            "latitude": 15.2993,
            "longitude": 74.1240,
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "features": ["Water sports", "Beach access", "Local guide", "Meals included", "Transportation"],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "agent_id": travel_agent_ids[1] if len(travel_agent_ids) > 1 else str(uuid.uuid4()),
            "title": "Goa Heritage Tour",
            "description": "2-day cultural and heritage exploration of Old Goa",
            "price": 8000,
            "duration": "2 days 1 night",
            "duration_days": 2,
            "destination": "Goa",
            "latitude": 15.5057,
            "longitude": 73.9964,
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "features": ["Heritage sites", "Cultural guide", "Local cuisine", "Transportation", "Photography"],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        # Royal Rajasthan Tours packages
        {
            "id": str(uuid.uuid4()),
            "agent_id": travel_agent_ids[1] if len(travel_agent_ids) > 1 else str(uuid.uuid4()),
            "title": "Golden Triangle Heritage Tour",
            "description": "Classic 7-day tour covering Delhi, Agra, and Jaipur with heritage hotels and cultural experiences",
            "price": 25000,
            "duration": "7 days 6 nights",
            "duration_days": 7,
            "destination": "Delhi - Agra - Jaipur",
            "latitude": 28.7041,
            "longitude": 77.1025,
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QSFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "features": ["Heritage hotel stay", "Professional guide", "All meals", "AC transportation", "Monument tickets", "Cultural shows"],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "agent_id": travel_agent_ids[1] if len(travel_agent_ids) > 1 else str(uuid.uuid4()),
            "title": "Rajasthan Royal Palace Tour",
            "description": "Luxury 10-day tour exploring magnificent palaces and forts of Rajasthan",
            "price": 45000,
            "duration": "10 days 9 nights",
            "duration_days": 10,
            "destination": "Jaipur - Udaipur - Jodhpur - Jaisalmer",
            "latitude": 26.9124,
            "longitude": 75.7873,
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "features": ["5-star palace hotels", "Private guide", "Luxury transportation", "Royal dining", "Desert safari", "Folk performances"],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        # Swift Cabs packages (enhanced)
        {
            "id": str(uuid.uuid4()),
            "agent_id": transport_agent_1_id,
            "title": "Airport Transfer Service",
            "description": "Reliable airport pickup and drop service with professional drivers",
            "price": 800,
            "duration": "1 way trip",
            "duration_days": 1,
            "destination": "Any Airport",
            "latitude": 28.5562,
            "longitude": 77.1000,
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "features": ["AC car", "Professional driver", "24/7 availability", "GPS tracking", "Toll included"],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "agent_id": transport_agent_1_id,
            "title": "Inter-city Travel Package",
            "description": "Comfortable inter-city travel with multiple stops and flexible timing",
            "price": 2500,
            "duration": "Per day",
            "duration_days": 1,
            "destination": "Multiple cities",
            "latitude": 28.7041,
            "longitude": 77.1025,
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "features": ["Luxury vehicle", "Experienced driver", "Fuel included", "Multiple stops", "Flexible schedule", "Refreshments"],
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    await db.packages.insert_many(packages)
    
    # Sample ribbons
    ribbons = [
        {
            "id": str(uuid.uuid4()),
            "title": "Filter Options",
            "type": "filter",
            "items": [
                {"name": "Travel Agents", "value": "travel", "icon": "🏔️"},
                {"name": "Transport", "value": "transport", "icon": "🚗"},
                {"name": "Adventure", "value": "adventure", "icon": "🏃"},
                {"name": "Heritage", "value": "heritage", "icon": "🏛️"}
            ],
            "order": 1,
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Recommended For You",
            "type": "recommendation",
            "items": [
                {"agent_id": travel_agents[0]["id"], "reason": "Based on your adventure preferences"},
                {"agent_id": travel_agents[1]["id"], "reason": "Highly rated in your area"}
            ],
            "order": 2,
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Explore More",
            "type": "explore",
            "items": [
                {"category": "Budget Travel", "count": 50, "image": "💰", "action": "budget_travel"},
                {"category": "Weekend Getaways", "count": 25, "image": "🏖️"},
                {"category": "Adventure Sports", "count": 15, "image": "🏔️"},
                {"category": "Cultural Tours", "count": 30, "image": "🏛️"}
            ],
            "order": 3,
            "is_active": True
        }
    ]
    
    await db.ribbons.insert_many(ribbons)
    
    return {"message": "Sample data initialized successfully"}

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