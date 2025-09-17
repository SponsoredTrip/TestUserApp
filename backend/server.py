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
from bson import ObjectId

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
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Package(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    title: str
    description: str
    price: float
    duration: str
    destination: str
    image_base64: str
    features: List[str]
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
    
    # Sample Packages
    packages = [
        # Adventure Tours India packages
        {
            "id": str(uuid.uuid4()),
            "agent_id": travel_agent_1_id,
            "title": "Shimla Manali Adventure Trek",
            "description": "5-day adventure trekking tour covering beautiful mountain trails with camping and local cuisine",
            "price": 15000,
            "duration": "5 days 4 nights",
            "destination": "Shimla - Manali",
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "features": ["Professional guide", "Camping equipment", "All meals", "Transportation", "First aid kit"],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "agent_id": travel_agent_1_id,
            "title": "Himalayan Base Camp Trek",
            "description": "Ultimate 12-day trekking experience to Himalayan base camps with expert guides",
            "price": 35000,
            "duration": "12 days 11 nights",
            "destination": "Himachal Pradesh",
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "features": ["Expert mountaineer guide", "High altitude gear", "All meals", "Permits", "Medical support", "Photography service"],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        # Royal Rajasthan Tours packages
        {
            "id": str(uuid.uuid4()),
            "agent_id": travel_agent_2_id,
            "title": "Golden Triangle Heritage Tour",
            "description": "Classic 7-day tour covering Delhi, Agra, and Jaipur with heritage hotels and cultural experiences",
            "price": 25000,
            "duration": "7 days 6 nights",
            "destination": "Delhi - Agra - Jaipur",
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QSFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "features": ["Heritage hotel stay", "Professional guide", "All meals", "AC transportation", "Monument tickets", "Cultural shows"],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "agent_id": travel_agent_2_id,
            "title": "Rajasthan Royal Palace Tour",
            "description": "Luxury 10-day tour exploring magnificent palaces and forts of Rajasthan",
            "price": 45000,
            "duration": "10 days 9 nights",
            "destination": "Jaipur - Udaipur - Jodhpur - Jaisalmer",
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "features": ["5-star palace hotels", "Private guide", "Luxury transportation", "Royal dining", "Desert safari", "Folk performances"],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        # Swift Cabs packages
        {
            "id": str(uuid.uuid4()),
            "agent_id": transport_agent_1_id,
            "title": "Airport Transfer Service",
            "description": "Reliable airport pickup and drop service with professional drivers",
            "price": 800,
            "duration": "1 way trip",
            "destination": "Any Airport",
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
            "destination": "Multiple cities",
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