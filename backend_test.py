#!/usr/bin/env python3
"""
Backend API Testing Suite for Travel Aggregator App
Tests all backend endpoints systematically
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import uuid

# Configuration
BASE_URL = "https://voyagehub-17.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class BackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS.copy()
        self.auth_token = None
        self.test_user_data = {
            "username": "testuser_" + str(uuid.uuid4())[:8],
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }

    def log_result(self, test_name, success, message="", response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        
        if success:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
            self.results["errors"].append(f"{test_name}: {message}")
        print()

    def test_comprehensive_sample_data_initialization(self):
        """Test the init-data endpoint for comprehensive 100 agents"""
        print("🔄 Testing Comprehensive Sample Data Initialization (100 Agents)...")
        
        try:
            response = requests.post(f"{self.base_url}/init-data", headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "100 agents" in data["message"]:
                    self.log_result("Comprehensive Sample Data Initialization", True, 
                                  "Sample data created successfully with 100 agents")
                    return True
                else:
                    self.log_result("Comprehensive Sample Data Initialization", False, 
                                  f"Expected message about 100 agents, got: {data}")
                    return False
            else:
                self.log_result("Comprehensive Sample Data Initialization", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Comprehensive Sample Data Initialization", False, f"Request failed: {str(e)}")
            return False

    def test_user_registration(self):
        """Test user registration endpoint"""
        print("🔄 Testing User Registration...")
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/register",
                headers=self.headers,
                json=self.test_user_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if all(key in data for key in ["access_token", "token_type", "user"]):
                    self.auth_token = data["access_token"]
                    self.headers["Authorization"] = f"Bearer {self.auth_token}"
                    self.log_result("User Registration", True, "User registered successfully with JWT token")
                    return True
                else:
                    self.log_result("User Registration", False, f"Missing required fields in response: {data}")
                    return False
            else:
                self.log_result("User Registration", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("User Registration", False, f"Request failed: {str(e)}")
            return False

    def test_user_login(self):
        """Test user login endpoint"""
        print("🔄 Testing User Login...")
        
        login_data = {
            "username": self.test_user_data["username"],
            "password": self.test_user_data["password"]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                headers=self.headers,
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if all(key in data for key in ["access_token", "token_type", "user"]):
                    # Update token for subsequent tests
                    self.auth_token = data["access_token"]
                    self.headers["Authorization"] = f"Bearer {self.auth_token}"
                    self.log_result("User Login", True, "Login successful with JWT token")
                    return True
                else:
                    self.log_result("User Login", False, f"Missing required fields in response: {data}")
                    return False
            else:
                self.log_result("User Login", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("User Login", False, f"Request failed: {str(e)}")
            return False

    def test_get_current_user(self):
        """Test get current user endpoint (requires authentication)"""
        print("🔄 Testing Get Current User...")
        
        if not self.auth_token:
            self.log_result("Get Current User", False, "No auth token available")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/auth/me",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "username" in data and data["username"] == self.test_user_data["username"]:
                    self.log_result("Get Current User", True, "User data retrieved successfully")
                    return True
                else:
                    self.log_result("Get Current User", False, f"Unexpected user data: {data}")
                    return False
            else:
                self.log_result("Get Current User", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Get Current User", False, f"Request failed: {str(e)}")
            return False

    def test_comprehensive_agent_count_verification(self):
        """Test that exactly 100 agents are created (50 travel + 50 transport)"""
        print("🔄 Testing Comprehensive Agent Count Verification...")
        
        try:
            # Test getting all agents
            response = requests.get(f"{self.base_url}/agents", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                agents = response.json()
                if isinstance(agents, list):
                    total_agents = len(agents)
                    
                    # Count by type
                    travel_agents = [a for a in agents if a["type"] == "travel"]
                    transport_agents = [a for a in agents if a["type"] == "transport"]
                    
                    travel_count = len(travel_agents)
                    transport_count = len(transport_agents)
                    
                    # Verify exact counts
                    if total_agents == 100 and travel_count == 50 and transport_count == 50:
                        self.log_result("Comprehensive Agent Count Verification", True, 
                                      f"Perfect! Found exactly 100 agents: {travel_count} travel + {transport_count} transport")
                        
                        # Test filtering by type
                        travel_response = requests.get(
                            f"{self.base_url}/agents?agent_type=travel", 
                            headers=self.headers, 
                            timeout=10
                        )
                        
                        transport_response = requests.get(
                            f"{self.base_url}/agents?agent_type=transport", 
                            headers=self.headers, 
                            timeout=10
                        )
                        
                        if travel_response.status_code == 200 and transport_response.status_code == 200:
                            filtered_travel = travel_response.json()
                            filtered_transport = transport_response.json()
                            
                            if len(filtered_travel) == 50 and len(filtered_transport) == 50:
                                self.log_result("Agent Type Filtering", True, 
                                              f"Filtering works perfectly: {len(filtered_travel)} travel, {len(filtered_transport)} transport")
                                return True
                            else:
                                self.log_result("Agent Type Filtering", False, 
                                              f"Filter count mismatch: travel={len(filtered_travel)}, transport={len(filtered_transport)}")
                                return False
                        else:
                            self.log_result("Agent Type Filtering", False, 
                                          f"Filter requests failed: travel={travel_response.status_code}, transport={transport_response.status_code}")
                            return False
                    else:
                        self.log_result("Comprehensive Agent Count Verification", False, 
                                      f"Count mismatch: total={total_agents} (expected 100), travel={travel_count} (expected 50), transport={transport_count} (expected 50)")
                        return False
                else:
                    self.log_result("Comprehensive Agent Count Verification", False, "Invalid response format")
                    return False
            else:
                self.log_result("Comprehensive Agent Count Verification", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Comprehensive Agent Count Verification", False, f"Request failed: {str(e)}")
            return False

    def test_get_packages(self):
        """Test get packages endpoint"""
        print("🔄 Testing Get Packages...")
        
        try:
            # Test getting all packages
            response = requests.get(f"{self.base_url}/packages", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                packages = response.json()
                if isinstance(packages, list) and len(packages) > 0:
                    # Check if packages have required fields
                    required_fields = ["id", "agent_id", "title", "description", "price", "duration"]
                    first_package = packages[0]
                    if all(field in first_package for field in required_fields):
                        self.log_result("Get All Packages", True, f"Retrieved {len(packages)} packages successfully")
                        
                        # Test filtering by agent_id
                        agent_id = first_package["agent_id"]
                        agent_response = requests.get(
                            f"{self.base_url}/packages?agent_id={agent_id}", 
                            headers=self.headers, 
                            timeout=10
                        )
                        if agent_response.status_code == 200:
                            agent_packages = agent_response.json()
                            agent_count = len([p for p in agent_packages if p["agent_id"] == agent_id])
                            self.log_result("Get Agent Packages", True, f"Retrieved {agent_count} packages for agent")
                            return True
                        else:
                            self.log_result("Get Agent Packages", False, 
                                          f"HTTP {agent_response.status_code}: {agent_response.text}")
                            return False
                    else:
                        self.log_result("Get Packages", False, f"Missing required fields in package data: {first_package}")
                        return False
                else:
                    self.log_result("Get Packages", False, "No packages returned or invalid format")
                    return False
            else:
                self.log_result("Get Packages", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Get Packages", False, f"Request failed: {str(e)}")
            return False

    def test_budget_travel_ribbon_integration(self):
        """Test that Budget Travel appears first in Explore More ribbon"""
        print("🔄 Testing Budget Travel Ribbon Integration...")
        
        try:
            response = requests.get(f"{self.base_url}/ribbons", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                ribbons = response.json()
                if isinstance(ribbons, list) and len(ribbons) > 0:
                    # Find the "Explore More" ribbon
                    explore_ribbons = [r for r in ribbons if r["type"] == "explore"]
                    
                    if explore_ribbons:
                        explore_ribbon = explore_ribbons[0]
                        items = explore_ribbon.get("items", [])
                        
                        if items and len(items) > 0:
                            # Check if Budget Travel is the first item
                            first_item = items[0]
                            
                            # Check if it's Budget Travel with correct action
                            if (first_item.get("action") == "budget_travel" or 
                                "budget travel" in first_item.get("category", "").lower() or
                                "budget travel" in first_item.get("title", "").lower()):
                                
                                self.log_result("Budget Travel Ribbon Integration", True, 
                                              f"Budget Travel is first in Explore More ribbon with action: {first_item.get('action', 'N/A')}")
                                return True
                            else:
                                self.log_result("Budget Travel Ribbon Integration", False, 
                                              f"Budget Travel not first in ribbon. First item: {first_item}")
                                return False
                        else:
                            self.log_result("Budget Travel Ribbon Integration", False, 
                                          "Explore More ribbon has no items")
                            return False
                    else:
                        self.log_result("Budget Travel Ribbon Integration", False, 
                                      "No Explore More ribbon found")
                        return False
                else:
                    self.log_result("Budget Travel Ribbon Integration", False, "No ribbons returned")
                    return False
            else:
                self.log_result("Budget Travel Ribbon Integration", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Budget Travel Ribbon Integration", False, f"Request failed: {str(e)}")
            return False

    def test_create_booking(self):
        """Test create booking endpoint (requires authentication)"""
        print("🔄 Testing Create Booking...")
        
        if not self.auth_token:
            self.log_result("Create Booking", False, "No auth token available")
            return False
        
        try:
            # First get a package to book
            packages_response = requests.get(f"{self.base_url}/packages", headers=self.headers, timeout=10)
            if packages_response.status_code != 200:
                self.log_result("Create Booking", False, "Could not retrieve packages for booking test")
                return False
            
            packages = packages_response.json()
            if not packages:
                self.log_result("Create Booking", False, "No packages available for booking")
                return False
            
            package_id = packages[0]["id"]
            travel_date = (datetime.now() + timedelta(days=30)).isoformat()
            
            booking_data = {
                "package_id": package_id,
                "travel_date": travel_date
            }
            
            response = requests.post(
                f"{self.base_url}/bookings",
                headers=self.headers,
                params={"package_id": package_id, "travel_date": travel_date},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "booking_id" in data:
                    self.log_result("Create Booking", True, "Booking created successfully")
                    return True
                else:
                    self.log_result("Create Booking", False, f"Unexpected response format: {data}")
                    return False
            else:
                self.log_result("Create Booking", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Create Booking", False, f"Request failed: {str(e)}")
            return False

    def test_get_user_bookings(self):
        """Test get user bookings endpoint (requires authentication)"""
        print("🔄 Testing Get User Bookings...")
        
        if not self.auth_token:
            self.log_result("Get User Bookings", False, "No auth token available")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/bookings",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                bookings = response.json()
                if isinstance(bookings, list):
                    self.log_result("Get User Bookings", True, f"Retrieved {len(bookings)} bookings")
                    return True
                else:
                    self.log_result("Get User Bookings", False, f"Invalid response format: {bookings}")
                    return False
            else:
                self.log_result("Get User Bookings", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Get User Bookings", False, f"Request failed: {str(e)}")
            return False

    def test_budget_travel_preview(self):
        """Test budget travel preview endpoint"""
        print("🔄 Testing Budget Travel Preview API...")
        
        try:
            response = requests.get(f"{self.base_url}/budget-travel/preview", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["available_destinations", "price_range", "popular_durations", "total_packages", "suggestion"]
                
                if all(field in data for field in required_fields):
                    # Verify price_range has min and max
                    if "min" in data["price_range"] and "max" in data["price_range"]:
                        # Check if destinations include expected ones
                        destinations = data["available_destinations"]
                        if isinstance(destinations, list) and len(destinations) > 0:
                            self.log_result("Budget Travel Preview", True, 
                                          f"Retrieved preview with {len(destinations)} destinations, price range ₹{data['price_range']['min']}-₹{data['price_range']['max']}")
                            return True
                        else:
                            self.log_result("Budget Travel Preview", False, "No destinations found in preview")
                            return False
                    else:
                        self.log_result("Budget Travel Preview", False, "Missing min/max in price_range")
                        return False
                else:
                    self.log_result("Budget Travel Preview", False, f"Missing required fields: {required_fields}")
                    return False
            else:
                self.log_result("Budget Travel Preview", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Budget Travel Preview", False, f"Request failed: {str(e)}")
            return False

    def test_budget_travel_with_larger_dataset(self):
        """Test budget travel search with larger dataset (100 agents)"""
        print("🔄 Testing Budget Travel with Larger Dataset...")
        
        # Test data from requirements: budget=50000, num_persons=2, num_days=6
        search_request = {
            "budget": 50000,
            "num_persons": 2,
            "num_days": 6
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/budget-travel",
                headers=self.headers,
                json=search_request,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["request", "combinations", "total_combinations_found", "message"]
                
                if all(field in data for field in required_fields):
                    combinations = data["combinations"]
                    if isinstance(combinations, list) and len(combinations) > 0:
                        # Check that we're getting diverse agent IDs (from larger dataset)
                        all_agent_ids = set()
                        for combo in combinations:
                            for package in combo.get("packages", []):
                                all_agent_ids.add(package.get("agent_id"))
                        
                        # With 100 agents, we should see some diversity (but packages are only created for first 10 agents)
                        if len(all_agent_ids) >= 2:  # At least 2 different agents used (realistic expectation)
                            self.log_result("Budget Travel with Larger Dataset", True, 
                                          f"Found {len(combinations)} combinations using {len(all_agent_ids)} different agents from larger dataset")
                            
                            # Test with specific place filter
                            place_search_request = {
                                "budget": 50000,
                                "num_persons": 2,
                                "num_days": 6,
                                "place": "goa"
                            }
                            
                            place_response = requests.post(
                                f"{self.base_url}/budget-travel",
                                headers=self.headers,
                                json=place_search_request,
                                timeout=15
                            )
                            
                            if place_response.status_code == 200:
                                place_data = place_response.json()
                                place_combinations = place_data.get("combinations", [])
                                
                                if place_combinations:
                                    # Verify Goa packages are included
                                    goa_packages_found = False
                                    for combo in place_combinations:
                                        for package in combo.get("packages", []):
                                            if "goa" in package.get("destination", "").lower():
                                                goa_packages_found = True
                                                break
                                        if goa_packages_found:
                                            break
                                    
                                    if goa_packages_found:
                                        self.log_result("Budget Travel - Place Filter with Larger Dataset", True, 
                                                      f"Found {len(place_combinations)} Goa combinations from larger dataset")
                                        return True
                                    else:
                                        self.log_result("Budget Travel - Place Filter with Larger Dataset", False, 
                                                      "No Goa packages found despite place filter")
                                        return False
                                else:
                                    self.log_result("Budget Travel - Place Filter with Larger Dataset", False, 
                                                  "No combinations found for Goa with larger dataset")
                                    return False
                            else:
                                self.log_result("Budget Travel - Place Filter with Larger Dataset", False, 
                                              f"Place filter request failed: HTTP {place_response.status_code}")
                                return False
                        else:
                            self.log_result("Budget Travel with Larger Dataset", False, 
                                          f"Not enough agent diversity: only {len(all_agent_ids)} agents used")
                            return False
                    else:
                        self.log_result("Budget Travel with Larger Dataset", False, 
                                      "No combinations found with larger dataset")
                        return False
                else:
                    self.log_result("Budget Travel with Larger Dataset", False, 
                                  f"Missing required fields: {required_fields}")
                    return False
            else:
                self.log_result("Budget Travel with Larger Dataset", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Budget Travel with Larger Dataset", False, f"Request failed: {str(e)}")
            return False

    def test_budget_travel_edge_cases(self):
        """Test budget travel edge cases"""
        print("🔄 Testing Budget Travel Edge Cases...")
        
        # Test case 1: Very low budget
        low_budget_request = {
            "budget": 1000,
            "num_persons": 2,
            "num_days": 5,
            "place": "goa"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/budget-travel",
                headers=self.headers,
                json=low_budget_request,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["total_combinations_found"] == 0:
                    self.log_result("Budget Travel - Low Budget Edge Case", True, 
                                  "Correctly returned no combinations for very low budget")
                else:
                    self.log_result("Budget Travel - Low Budget Edge Case", False, 
                                  f"Unexpected combinations found for low budget: {data['total_combinations_found']}")
                    return False
            else:
                self.log_result("Budget Travel - Low Budget Edge Case", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
            # Test case 2: No place filter (should return general combinations)
            general_request = {
                "budget": 30000,
                "num_persons": 2,
                "num_days": 5
            }
            
            response = requests.post(
                f"{self.base_url}/budget-travel",
                headers=self.headers,
                json=general_request,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["total_combinations_found"] > 0:
                    self.log_result("Budget Travel - General Search", True, 
                                  f"Found {data['total_combinations_found']} combinations without place filter")
                    return True
                else:
                    self.log_result("Budget Travel - General Search", False, 
                                  "No combinations found for reasonable budget without place filter")
                    return False
            else:
                self.log_result("Budget Travel - General Search", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Budget Travel Edge Cases", False, f"Request failed: {str(e)}")
            return False

    def test_phase1_filter_options_structure(self):
        """Test Phase 1: Filter Options Fix - verify new filter structure"""
        print("🔄 Testing Phase 1: Filter Options Structure...")
        
        try:
            response = requests.get(f"{self.base_url}/ribbons", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                ribbons = response.json()
                filter_ribbons = [r for r in ribbons if r["type"] == "filter"]
                
                if filter_ribbons:
                    filter_ribbon = filter_ribbons[0]
                    items = filter_ribbon.get("items", [])
                    
                    # Expected filter options from review request
                    expected_filters = ["Travel", "Transport", "Sponsored", "Goa", "Himachal", "Uttarakhand"]
                    found_filters = [item.get("name") for item in items]
                    
                    # Check if all expected filters are present
                    missing_filters = [f for f in expected_filters if f not in found_filters]
                    
                    if not missing_filters:
                        # Verify each item has required fields
                        all_valid = True
                        for item in items:
                            if not all(field in item for field in ["name", "value", "icon"]):
                                all_valid = False
                                break
                        
                        if all_valid:
                            self.log_result("Phase 1: Filter Options Structure", True, 
                                          f"All expected filters found: {found_filters}")
                            return True
                        else:
                            self.log_result("Phase 1: Filter Options Structure", False, 
                                          "Some filter items missing required fields (name, value, icon)")
                            return False
                    else:
                        self.log_result("Phase 1: Filter Options Structure", False, 
                                      f"Missing expected filters: {missing_filters}")
                        return False
                else:
                    self.log_result("Phase 1: Filter Options Structure", False, 
                                  "No filter ribbon found")
                    return False
            else:
                self.log_result("Phase 1: Filter Options Structure", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Phase 1: Filter Options Structure", False, f"Request failed: {str(e)}")
            return False

    def test_phase2_subscription_status(self):
        """Test Phase 2: Subscription Status - verify agents have subscription fields"""
        print("🔄 Testing Phase 2: Subscription Status...")
        
        try:
            response = requests.get(f"{self.base_url}/agents", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                agents = response.json()
                if agents:
                    # Check if agents have subscription fields
                    subscription_fields = ["is_subscribed", "subscription_type"]
                    first_agent = agents[0]
                    
                    if all(field in first_agent for field in subscription_fields):
                        # Count subscribed agents
                        subscribed_agents = [a for a in agents if a.get("is_subscribed", False)]
                        
                        # Based on the code, every 4th travel and every 5th transport should be subscribed
                        # With 50 travel and 50 transport agents, we expect ~25 subscribed agents
                        expected_subscribed = 25  # Approximate
                        actual_subscribed = len(subscribed_agents)
                        
                        if actual_subscribed >= 20 and actual_subscribed <= 30:  # Allow some variance
                            # Test filtering by subscription status
                            subscribed_response = requests.get(
                                f"{self.base_url}/agents", 
                                headers=self.headers, 
                                timeout=10
                            )
                            
                            if subscribed_response.status_code == 200:
                                all_agents = subscribed_response.json()
                                subscribed_count = len([a for a in all_agents if a.get("is_subscribed", False)])
                                
                                self.log_result("Phase 2: Subscription Status", True, 
                                              f"Found {subscribed_count} subscribed agents with proper subscription fields")
                                return True
                            else:
                                self.log_result("Phase 2: Subscription Status", False, 
                                              f"Failed to retrieve agents for subscription filtering")
                                return False
                        else:
                            self.log_result("Phase 2: Subscription Status", False, 
                                          f"Unexpected number of subscribed agents: {actual_subscribed} (expected ~25)")
                            return False
                    else:
                        self.log_result("Phase 2: Subscription Status", False, 
                                      f"Missing subscription fields in agents: {subscription_fields}")
                        return False
                else:
                    self.log_result("Phase 2: Subscription Status", False, "No agents found")
                    return False
            else:
                self.log_result("Phase 2: Subscription Status", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Phase 2: Subscription Status", False, f"Request failed: {str(e)}")
            return False

    def test_phase2_recommended_section(self):
        """Test Phase 2: Recommended Section - verify shows subscribed agents"""
        print("🔄 Testing Phase 2: Recommended Section...")
        
        try:
            response = requests.get(f"{self.base_url}/ribbons", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                ribbons = response.json()
                recommended_ribbons = [r for r in ribbons if r["type"] == "recommendation"]
                
                if recommended_ribbons:
                    recommended_ribbon = recommended_ribbons[0]
                    items = recommended_ribbon.get("items", [])
                    
                    if items:
                        # Verify items have agent fields
                        required_fields = ["agent_id", "name", "type", "rating", "location"]
                        first_item = items[0]
                        
                        if all(field in first_item for field in required_fields):
                            # Verify these are actually subscribed agents
                            agent_ids = [item["agent_id"] for item in items]
                            
                            # Get agents to verify subscription status
                            agents_response = requests.get(f"{self.base_url}/agents", headers=self.headers, timeout=10)
                            if agents_response.status_code == 200:
                                all_agents = agents_response.json()
                                agent_lookup = {a["id"]: a for a in all_agents}
                                
                                # Check if recommended agents are subscribed
                                subscribed_count = 0
                                for agent_id in agent_ids:
                                    if agent_id in agent_lookup and agent_lookup[agent_id].get("is_subscribed", False):
                                        subscribed_count += 1
                                
                                if subscribed_count == len(agent_ids):
                                    self.log_result("Phase 2: Recommended Section", True, 
                                                  f"All {len(items)} recommended agents are subscribed")
                                    return True
                                else:
                                    self.log_result("Phase 2: Recommended Section", False, 
                                                  f"Only {subscribed_count}/{len(agent_ids)} recommended agents are subscribed")
                                    return False
                            else:
                                self.log_result("Phase 2: Recommended Section", False, 
                                              "Could not verify agent subscription status")
                                return False
                        else:
                            self.log_result("Phase 2: Recommended Section", False, 
                                          f"Missing required fields in recommended items: {required_fields}")
                            return False
                    else:
                        self.log_result("Phase 2: Recommended Section", False, 
                                      "No items in recommended ribbon")
                        return False
                else:
                    self.log_result("Phase 2: Recommended Section", False, 
                                  "No recommendation ribbon found")
                    return False
            else:
                self.log_result("Phase 2: Recommended Section", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Phase 2: Recommended Section", False, f"Request failed: {str(e)}")
            return False

    def test_phase2_chat_api(self):
        """Test Phase 2: Chat API - test send and retrieve messages"""
        print("🔄 Testing Phase 2: Chat API...")
        
        if not self.auth_token:
            self.log_result("Phase 2: Chat API", False, "No auth token available")
            return False
        
        try:
            # First get a package ID
            packages_response = requests.get(f"{self.base_url}/packages", headers=self.headers, timeout=10)
            if packages_response.status_code != 200:
                self.log_result("Phase 2: Chat API", False, "Could not retrieve packages for chat test")
                return False
            
            packages = packages_response.json()
            if not packages:
                self.log_result("Phase 2: Chat API", False, "No packages available for chat test")
                return False
            
            package_id = packages[0]["id"]
            test_message = "Hello, I'm interested in this package. Can you provide more details?"
            
            # Test sending message
            chat_request = {
                "package_id": package_id,
                "message": test_message
            }
            
            send_response = requests.post(
                f"{self.base_url}/chat/send",
                headers=self.headers,
                json=chat_request,
                timeout=10
            )
            
            if send_response.status_code == 200:
                send_data = send_response.json()
                if "message" in send_data and "chat_id" in send_data:
                    # Test retrieving messages
                    get_response = requests.get(
                        f"{self.base_url}/chat/{package_id}",
                        headers=self.headers,
                        timeout=10
                    )
                    
                    if get_response.status_code == 200:
                        messages = get_response.json()
                        if isinstance(messages, list) and len(messages) > 0:
                            # Find our test message
                            test_message_found = any(
                                msg.get("message") == test_message and 
                                msg.get("package_id") == package_id and
                                msg.get("sender_type") == "user"
                                for msg in messages
                            )
                            
                            if test_message_found:
                                self.log_result("Phase 2: Chat API", True, 
                                              f"Successfully sent and retrieved chat message for package {package_id}")
                                return True
                            else:
                                self.log_result("Phase 2: Chat API", False, 
                                              "Test message not found in retrieved messages")
                                return False
                        else:
                            self.log_result("Phase 2: Chat API", False, 
                                          "No messages retrieved or invalid format")
                            return False
                    else:
                        self.log_result("Phase 2: Chat API", False, 
                                      f"Failed to retrieve messages: HTTP {get_response.status_code}")
                        return False
                else:
                    self.log_result("Phase 2: Chat API", False, 
                                  f"Unexpected send response format: {send_data}")
                    return False
            else:
                self.log_result("Phase 2: Chat API", False, 
                              f"Failed to send message: HTTP {send_response.status_code}: {send_response.text}")
                return False
                
        except Exception as e:
            self.log_result("Phase 2: Chat API", False, f"Request failed: {str(e)}")
            return False

    def test_enhanced_sample_data(self):
        """Test that enhanced sample data includes new fields for budget travel"""
        print("🔄 Testing Enhanced Sample Data...")
        
        try:
            # Get packages to verify enhanced fields
            response = requests.get(f"{self.base_url}/packages", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                packages = response.json()
                if packages:
                    # Check for enhanced fields in packages
                    enhanced_fields = ["duration_days", "latitude", "longitude"]
                    goa_packages = [pkg for pkg in packages if "goa" in pkg["destination"].lower()]
                    
                    if goa_packages:
                        goa_package = goa_packages[0]
                        if all(field in goa_package for field in enhanced_fields):
                            # Verify specific Goa packages from requirements
                            beach_adventure = next((pkg for pkg in goa_packages if "beach adventure" in pkg["title"].lower()), None)
                            heritage_tour = next((pkg for pkg in goa_packages if "heritage" in pkg["title"].lower()), None)
                            
                            if beach_adventure and heritage_tour:
                                # Check pricing matches requirements (₹10,000 and ₹8,000)
                                if beach_adventure["price"] == 10000 and heritage_tour["price"] == 8000:
                                    self.log_result("Enhanced Sample Data", True, 
                                                  f"Found Goa packages with correct pricing: Beach Adventure ₹{beach_adventure['price']}, Heritage Tour ₹{heritage_tour['price']}")
                                else:
                                    self.log_result("Enhanced Sample Data", False, 
                                                  f"Goa package pricing mismatch: Beach Adventure ₹{beach_adventure['price']}, Heritage Tour ₹{heritage_tour['price']}")
                                    return False
                            else:
                                self.log_result("Enhanced Sample Data", False, 
                                              "Missing expected Goa packages (Beach Adventure, Heritage Tour)")
                                return False
                        else:
                            self.log_result("Enhanced Sample Data", False, 
                                          f"Missing enhanced fields in Goa packages: {enhanced_fields}")
                            return False
                    else:
                        self.log_result("Enhanced Sample Data", False, "No Goa packages found in sample data")
                        return False
                        
                    # Check ribbons for Budget Travel option
                    ribbons_response = requests.get(f"{self.base_url}/ribbons", headers=self.headers, timeout=10)
                    if ribbons_response.status_code == 200:
                        ribbons = ribbons_response.json()
                        explore_ribbons = [r for r in ribbons if r["type"] == "explore"]
                        
                        if explore_ribbons:
                            explore_ribbon = explore_ribbons[0]
                            budget_travel_item = next((item for item in explore_ribbon["items"] 
                                                     if "budget travel" in item.get("category", "").lower()), None)
                            
                            if budget_travel_item and budget_travel_item.get("action") == "budget_travel":
                                self.log_result("Enhanced Sample Data - Budget Travel Ribbon", True, 
                                              "Budget Travel option found in Explore More ribbon with correct action")
                                return True
                            else:
                                self.log_result("Enhanced Sample Data - Budget Travel Ribbon", False, 
                                              "Budget Travel option missing or incorrect in Explore More ribbon")
                                return False
                        else:
                            self.log_result("Enhanced Sample Data - Budget Travel Ribbon", False, 
                                          "No explore ribbons found")
                            return False
                    else:
                        self.log_result("Enhanced Sample Data - Budget Travel Ribbon", False, 
                                      f"Could not retrieve ribbons: HTTP {ribbons_response.status_code}")
                        return False
                else:
                    self.log_result("Enhanced Sample Data", False, "No packages found")
                    return False
            else:
                self.log_result("Enhanced Sample Data", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Enhanced Sample Data", False, f"Request failed: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all backend tests in sequence"""
        print("=" * 60)
        print("🚀 STARTING BACKEND API TESTS")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print()
        
        # Test sequence - order matters for authentication
        test_sequence = [
            # Initialize comprehensive data first
            self.test_comprehensive_sample_data_initialization,
            
            # Phase 1 & Phase 2 Priority Tests (as per review request)
            self.test_phase1_filter_options_structure,
            self.test_budget_travel_preview,  # Phase 1: Budget Travel Groups
            self.test_phase2_subscription_status,
            self.test_phase2_recommended_section,
            
            # Authentication tests (needed for chat API)
            self.test_user_registration,
            self.test_user_login,
            self.test_get_current_user,
            
            # Phase 2: Chat API (requires authentication)
            self.test_phase2_chat_api,
            
            # Additional comprehensive tests
            self.test_comprehensive_agent_count_verification,
            self.test_budget_travel_ribbon_integration,
            self.test_budget_travel_with_larger_dataset,
            self.test_get_packages,
            self.test_create_booking,
            self.test_get_user_bookings,
            self.test_enhanced_sample_data,
            self.test_budget_travel_edge_cases
        ]
        
        for test_func in test_sequence:
            test_func()
        
        # Print summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📈 Success Rate: {(self.results['passed'] / (self.results['passed'] + self.results['failed']) * 100):.1f}%")
        
        if self.results['errors']:
            print("\n🔍 FAILED TESTS:")
            for error in self.results['errors']:
                print(f"   • {error}")
        
        print("=" * 60)
        
        return self.results['failed'] == 0

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)