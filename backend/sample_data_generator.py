import uuid
import random
from datetime import datetime

def generate_comprehensive_sample_data():
    """Generate 50 travel agents + 50 transport agents with comprehensive data"""
    
    # Travel agent names
    travel_agent_names = [
        "Adventure Tours India", "Royal Rajasthan Tours", "Himalayan Trekking Co", "Kerala Backwaters Experience", 
        "Desert Safari Adventures", "Golden Triangle Expeditions", "Goa Beach Holidays", "Wildlife Safari Tours",
        "Mountain View Travels", "Cultural Heritage Tours", "Spice Route Adventures", "Tiger Trail Expeditions",
        "Coastal Paradise Tours", "Historic India Journeys", "Scenic Valley Tours", "Temple Trail Adventures",
        "Exotic India Travels", "Monsoon Escapes", "Yoga Retreat Tours", "Festival Tours India",
        "Luxury Palace Tours", "Budget Backpacker Trips", "Family Fun Adventures", "Romantic Getaways",
        "Corporate Travel Solutions", "Pilgrimage Tours India", "Photography Expeditions", "Culinary Tours India",
        "Ayurveda Wellness Tours", "Bollywood Theme Tours", "River Rafting Adventures", "Rock Climbing Expeditions",
        "Bird Watching Tours", "Motorcycle Tours India", "Train Journey Specialists", "Village Tourism India",
        "Textile Tours India", "Architecture Tours", "Fort & Palace Tours", "Lake District Adventures",
        "Tea Garden Tours", "Coffee Plantation Visits", "Tribal Culture Tours", "Handicraft Tours",
        "Street Food Adventures", "Shopping Tour Specialists", "Language Immersion Tours", "Music & Dance Tours",
        "Spiritual Journey Tours", "Medical Tourism India"
    ]
    
    # Transport agent names
    transport_agent_names = [
        "Swift Cabs", "City Taxi Services", "Highway Express", "Metro Connect Transport", 
        "Premium Car Rentals", "Budget Travel Cars", "Luxury Limousine Service", "Airport Shuttle Pro",
        "Interstate Bus Service", "Local Commute Solutions", "Executive Car Service", "Tourist Taxi Network",
        "Eco-Friendly Rides", "24/7 Cab Service", "Corporate Transport Solutions", "Family Travel Cars",
        "Adventure Vehicle Rentals", "Long Distance Cabs", "City Tour Vehicles", "Hotel Transfer Service",
        "Wedding Car Rentals", "Group Travel Solutions", "Motorcycle Taxi Service", "Electric Vehicle Cabs",
        "Vintage Car Rentals", "Sports Car Service", "Mini Bus Rentals", "Tempo Traveller Service",
        "AC Bus Service", "Volvo Coach Service", "Deluxe Car Rentals", "Economy Cab Service",
        "Railway Station Pickup", "Bus Terminal Service", "Port Transfer Service", "Hospital Transfer Cabs",
        "Shopping Mall Shuttles", "College Transport Service", "Office Commute Solutions", "Weekend Getaway Cars",
        "Night Cab Service", "Ladies Special Cabs", "Senior Citizen Transport", "Wheelchair Accessible Cabs",
        "Pet-Friendly Transport", "Luggage Transport Service", "Moving & Shifting Service", "Goods Transport",
        "Courier & Delivery Service", "Emergency Transport Service"
    ]
    
    # Indian cities
    indian_cities = [
        "Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad",
        "Jaipur", "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam",
        "Pimpri-Chinchwad", "Patna", "Vadodara", "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Faridabad",
        "Meerut", "Rajkot", "Kalyan-Dombivli", "Vasai-Virar", "Varanasi", "Srinagar", "Aurangabad", "Dhanbad",
        "Amritsar", "Navi Mumbai", "Allahabad", "Ranchi", "Howrah", "Coimbatore", "Jabalpur", "Gwalior",
        "Vijayawada", "Jodhpur", "Madurai", "Raipur", "Kota", "Chandigarh", "Guwahati", "Solapur", "Hubli-Dharwad", "Mysore"
    ]
    
    # Descriptions
    travel_descriptions = [
        "Specializing in adventure and trekking tours across India",
        "Luxury heritage tours with authentic cultural experiences", 
        "Budget-friendly backpacking adventures for young travelers",
        "Family-oriented tours with child-friendly activities",
        "Wildlife and nature photography expeditions",
        "Spiritual and pilgrimage journey specialists",
        "Romantic honeymoon packages and couple retreats",
        "Corporate team building and conference tours",
        "Authentic local cuisine and food tours",
        "Traditional festivals and cultural celebration tours",
        "Beach and coastal adventure packages",
        "Mountain and hill station retreats",
        "Desert safari and camel trekking tours",
        "Yoga and wellness retreat organizers",
        "Photography and art exploration tours"
    ]
    
    transport_descriptions = [
        "Reliable and affordable transportation for all occasions",
        "Premium car rental service with professional drivers",
        "24/7 taxi service covering the entire city",
        "Comfortable long-distance travel solutions",
        "Eco-friendly electric vehicle transportation",
        "Luxury chauffeur service for VIP clients",
        "Group transportation with spacious vehicles",
        "Airport and railway station transfer specialists",
        "Wedding and event transportation service",
        "Corporate and business travel solutions",
        "Tourist-friendly sightseeing vehicles",
        "Emergency and medical transport service",
        "Interstate and intercity travel experts",
        "Budget-friendly shared cab service",
        "Motorcycle and bike taxi service"
    ]
    
    travel_services = [
        ["Package Tours", "Hotel Booking", "Transport", "Guide Service"],
        ["Heritage Tours", "Palace Hotels", "Cultural Shows", "Luxury Travel"],
        ["Trekking", "Adventure Sports", "Camping", "Photography"],
        ["Wildlife Safari", "Nature Tours", "Bird Watching", "Eco Tours"],
        ["Beach Activities", "Water Sports", "Island Hopping", "Sunset Tours"],
        ["Pilgrimage", "Temple Tours", "Spiritual Guidance", "Meditation"],
        ["Honeymoon Packages", "Romantic Dinners", "Couple Activities", "Privacy"],
        ["Corporate Events", "Team Building", "Conference", "Business Travel"],
        ["Food Tours", "Cooking Classes", "Local Cuisine", "Street Food"],
        ["Festival Tours", "Cultural Shows", "Dance Performances", "Music Events"]
    ]
    
    transport_services = [
        ["City Rides", "Airport Transfer", "Outstation", "Rental Cars"],
        ["Luxury Cars", "Chauffeur Service", "VIP Transport", "Premium Experience"],
        ["24/7 Service", "Emergency Rides", "Night Service", "Quick Response"],
        ["Long Distance", "Interstate", "Highway Travel", "Comfortable Journey"],
        ["Electric Cars", "Eco-Friendly", "Green Transport", "Sustainable Travel"],
        ["Group Travel", "Large Vehicles", "Event Transport", "Multiple Passengers"],
        ["Tourist Service", "Sightseeing", "City Tours", "Guide Service"],
        ["Medical Transport", "Emergency Service", "Hospital Transfer", "Patient Care"]
    ]

    # Generate agents
    agents = []
    agent_ids = []
    
    # Generate 50 travel agents
    for i in range(50):
        agent_id = str(uuid.uuid4())
        agent_ids.append(agent_id)
        
        agents.append({
            "id": agent_id,
            "name": travel_agent_names[i],
            "type": "travel",
            "description": travel_descriptions[i % len(travel_descriptions)],
            "rating": round(3.5 + (i % 15) * 0.1, 1),
            "total_bookings": 50 + (i * 12) % 500,
            "location": indian_cities[i % len(indian_cities)],
            "contact_phone": f"+91-9{i:03d}{(i*7)%1000:03d}{(i*11)%100:02d}",
            "contact_email": f"{travel_agent_names[i].lower().replace(' ', '').replace('&', 'and')}@travel.com",
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "services_offered": travel_services[i % len(travel_services)],
            "is_active": True,
            "created_at": datetime.utcnow()
        })
    
    # Generate 50 transport agents  
    for i in range(50):
        agent_id = str(uuid.uuid4())
        agent_ids.append(agent_id)
        
        agents.append({
            "id": agent_id,
            "name": transport_agent_names[i],
            "type": "transport", 
            "description": transport_descriptions[i % len(transport_descriptions)],
            "rating": round(3.8 + (i % 12) * 0.1, 1),
            "total_bookings": 25 + (i * 8) % 300,
            "location": indian_cities[i % len(indian_cities)],
            "contact_phone": f"+91-8{i:03d}{(i*5)%1000:03d}{(i*13)%100:02d}",
            "contact_email": f"{transport_agent_names[i].lower().replace(' ', '').replace('&', 'and')}@transport.com",
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "services_offered": transport_services[i % len(transport_services)],
            "is_active": True,
            "created_at": datetime.utcnow()
        })
    
    return agents, agent_ids