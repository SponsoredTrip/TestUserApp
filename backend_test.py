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

    def test_sample_data_initialization(self):
        """Test the init-data endpoint"""
        print("🔄 Testing Sample Data Initialization...")
        
        try:
            response = requests.post(f"{self.base_url}/init-data", headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "initialized successfully" in data["message"]:
                    self.log_result("Sample Data Initialization", True, "Sample data created successfully")
                    return True
                else:
                    self.log_result("Sample Data Initialization", False, f"Unexpected response format: {data}")
                    return False
            else:
                self.log_result("Sample Data Initialization", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Sample Data Initialization", False, f"Request failed: {str(e)}")
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

    def test_get_agents(self):
        """Test get agents endpoint"""
        print("🔄 Testing Get Agents...")
        
        try:
            # Test getting all agents
            response = requests.get(f"{self.base_url}/agents", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                agents = response.json()
                if isinstance(agents, list) and len(agents) > 0:
                    # Check if agents have required fields
                    required_fields = ["id", "name", "type", "description", "rating"]
                    first_agent = agents[0]
                    if all(field in first_agent for field in required_fields):
                        self.log_result("Get All Agents", True, f"Retrieved {len(agents)} agents successfully")
                        
                        # Test filtering by type
                        travel_response = requests.get(
                            f"{self.base_url}/agents?agent_type=travel", 
                            headers=self.headers, 
                            timeout=10
                        )
                        if travel_response.status_code == 200:
                            travel_agents = travel_response.json()
                            travel_count = len([a for a in travel_agents if a["type"] == "travel"])
                            self.log_result("Get Travel Agents", True, f"Retrieved {travel_count} travel agents")
                            return True
                        else:
                            self.log_result("Get Travel Agents", False, 
                                          f"HTTP {travel_response.status_code}: {travel_response.text}")
                            return False
                    else:
                        self.log_result("Get Agents", False, f"Missing required fields in agent data: {first_agent}")
                        return False
                else:
                    self.log_result("Get Agents", False, "No agents returned or invalid format")
                    return False
            else:
                self.log_result("Get Agents", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Get Agents", False, f"Request failed: {str(e)}")
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

    def test_get_ribbons(self):
        """Test get ribbons endpoint"""
        print("🔄 Testing Get Ribbons...")
        
        try:
            response = requests.get(f"{self.base_url}/ribbons", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                ribbons = response.json()
                if isinstance(ribbons, list) and len(ribbons) > 0:
                    # Check if ribbons have required fields
                    required_fields = ["id", "title", "type", "items", "order"]
                    first_ribbon = ribbons[0]
                    if all(field in first_ribbon for field in required_fields):
                        # Check if we have different types of ribbons
                        ribbon_types = set(r["type"] for r in ribbons)
                        expected_types = {"filter", "recommendation", "explore"}
                        if ribbon_types.intersection(expected_types):
                            self.log_result("Get Ribbons", True, 
                                          f"Retrieved {len(ribbons)} ribbons with types: {list(ribbon_types)}")
                            return True
                        else:
                            self.log_result("Get Ribbons", False, f"Unexpected ribbon types: {list(ribbon_types)}")
                            return False
                    else:
                        self.log_result("Get Ribbons", False, f"Missing required fields in ribbon data: {first_ribbon}")
                        return False
                else:
                    self.log_result("Get Ribbons", False, "No ribbons returned or invalid format")
                    return False
            else:
                self.log_result("Get Ribbons", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Get Ribbons", False, f"Request failed: {str(e)}")
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

    def test_budget_travel_search_goa_example(self):
        """Test budget travel search with Goa example from requirements"""
        print("🔄 Testing Budget Travel Search - Goa Example...")
        
        # Test data from requirements: budget=50000, num_persons=2, num_days=6, place="goa"
        search_request = {
            "budget": 50000,
            "num_persons": 2,
            "num_days": 6,
            "place": "goa"
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
                    # Verify request echo
                    if data["request"]["budget"] == 50000 and data["request"]["place"] == "goa":
                        combinations = data["combinations"]
                        if isinstance(combinations, list) and len(combinations) > 0:
                            # Check first combination structure
                            first_combo = combinations[0]
                            combo_fields = ["packages", "transport_segments", "total_cost", "total_days", "savings", "itinerary_summary"]
                            
                            if all(field in first_combo for field in combo_fields):
                                # Verify constraints
                                if first_combo["total_cost"] <= 50000 and first_combo["total_days"] <= 6:
                                    # Check if Goa packages are included
                                    goa_packages = [pkg for pkg in first_combo["packages"] if "goa" in pkg["destination"].lower()]
                                    if goa_packages:
                                        self.log_result("Budget Travel Search - Goa Example", True, 
                                                      f"Found {len(combinations)} combinations, first combo: ₹{first_combo['total_cost']} for {first_combo['total_days']} days with {len(goa_packages)} Goa packages")
                                        return True
                                    else:
                                        self.log_result("Budget Travel Search - Goa Example", False, 
                                                      f"No Goa packages found in combinations despite place filter")
                                        return False
                                else:
                                    self.log_result("Budget Travel Search - Goa Example", False, 
                                                  f"Combination violates constraints: cost={first_combo['total_cost']}, days={first_combo['total_days']}")
                                    return False
                            else:
                                self.log_result("Budget Travel Search - Goa Example", False, 
                                              f"Missing combination fields: {combo_fields}")
                                return False
                        else:
                            self.log_result("Budget Travel Search - Goa Example", False, 
                                          f"No combinations found for Goa with budget ₹50,000")
                            return False
                    else:
                        self.log_result("Budget Travel Search - Goa Example", False, 
                                      f"Request echo mismatch: {data['request']}")
                        return False
                else:
                    self.log_result("Budget Travel Search - Goa Example", False, 
                                  f"Missing required fields: {required_fields}")
                    return False
            else:
                self.log_result("Budget Travel Search - Goa Example", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Budget Travel Search - Goa Example", False, f"Request failed: {str(e)}")
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
            self.test_sample_data_initialization,
            self.test_user_registration,
            self.test_user_login,
            self.test_get_current_user,
            self.test_get_agents,
            self.test_get_packages,
            self.test_get_ribbons,
            self.test_create_booking,
            self.test_get_user_bookings,
            # Budget Travel API Tests
            self.test_enhanced_sample_data,
            self.test_budget_travel_preview,
            self.test_budget_travel_search_goa_example,
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