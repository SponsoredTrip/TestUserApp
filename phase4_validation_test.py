#!/usr/bin/env python3
"""
Phase 4: Backend Validation Testing
Focused testing to validate critical functionality after frontend fixes
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import uuid

# Configuration
BASE_URL = "https://tripaggregator.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class Phase4Tester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS.copy()
        self.auth_token = None
        self.test_user_data = {
            "username": "phase4_user_" + str(uuid.uuid4())[:8],
            "email": f"phase4_{uuid.uuid4()}@example.com",
            "password": "SecurePass123!",
            "full_name": "Phase 4 Test User"
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

    def setup_authentication(self):
        """Setup authentication for tests that require it"""
        print("🔄 Setting up authentication...")
        
        try:
            # Register user
            response = requests.post(
                f"{self.base_url}/auth/register",
                headers=self.headers,
                json=self.test_user_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.auth_token = data["access_token"]
                    self.headers["Authorization"] = f"Bearer {self.auth_token}"
                    print("   ✅ Authentication setup successful")
                    return True
                else:
                    print("   ❌ No access token in registration response")
                    return False
            else:
                print(f"   ❌ Registration failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Authentication setup failed: {str(e)}")
            return False

    def test_sponsored_filter_api(self):
        """PRIORITY TEST 1: Sponsored Filter API - GET /api/agents?agent_type=sponsored"""
        print("🔄 Testing Sponsored Filter API...")
        
        try:
            response = requests.get(
                f"{self.base_url}/agents?agent_type=sponsored", 
                headers=self.headers, 
                timeout=10
            )
            
            if response.status_code == 200:
                agents = response.json()
                if isinstance(agents, list):
                    if len(agents) > 0:
                        # Verify all returned agents are actually subscribed
                        all_subscribed = all(agent.get("is_subscribed", False) for agent in agents)
                        
                        if all_subscribed:
                            self.log_result("Sponsored Filter API", True, 
                                          f"Successfully returned {len(agents)} subscribed agents")
                            return True
                        else:
                            non_subscribed = [a for a in agents if not a.get("is_subscribed", False)]
                            self.log_result("Sponsored Filter API", False, 
                                          f"Found {len(non_subscribed)} non-subscribed agents in sponsored filter")
                            return False
                    else:
                        self.log_result("Sponsored Filter API", False, 
                                      "No sponsored agents returned - this was the main user complaint!")
                        return False
                else:
                    self.log_result("Sponsored Filter API", False, "Invalid response format")
                    return False
            else:
                self.log_result("Sponsored Filter API", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Sponsored Filter API", False, f"Request failed: {str(e)}")
            return False

    def test_chat_api_functionality(self):
        """PRIORITY TEST 2: Chat API Functionality"""
        print("🔄 Testing Chat API Functionality...")
        
        if not self.auth_token:
            self.log_result("Chat API Functionality", False, "No auth token available")
            return False
        
        try:
            # First get a package ID
            packages_response = requests.get(f"{self.base_url}/packages", headers=self.headers, timeout=10)
            if packages_response.status_code != 200:
                self.log_result("Chat API Functionality", False, "Could not retrieve packages for chat test")
                return False
            
            packages = packages_response.json()
            if not packages:
                self.log_result("Chat API Functionality", False, "No packages available for chat test")
                return False
            
            package_id = packages[0]["id"]
            test_message = "I'm interested in this travel package. What are the inclusions?"
            
            # Test POST /api/chat/send
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
                    # Test GET /api/chat/{package_id}
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
                                self.log_result("Chat API Functionality", True, 
                                              f"✅ POST /api/chat/send and GET /api/chat/{package_id} both working correctly")
                                return True
                            else:
                                self.log_result("Chat API Functionality", False, 
                                              "Test message not found in retrieved messages")
                                return False
                        else:
                            self.log_result("Chat API Functionality", False, 
                                          "No messages retrieved or invalid format")
                            return False
                    else:
                        self.log_result("Chat API Functionality", False, 
                                      f"GET /api/chat/{package_id} failed: HTTP {get_response.status_code}")
                        return False
                else:
                    self.log_result("Chat API Functionality", False, 
                                  f"POST /api/chat/send unexpected response: {send_data}")
                    return False
            else:
                self.log_result("Chat API Functionality", False, 
                              f"POST /api/chat/send failed: HTTP {send_response.status_code}: {send_response.text}")
                return False
                
        except Exception as e:
            self.log_result("Chat API Functionality", False, f"Request failed: {str(e)}")
            return False

    def test_package_api_sponsored_pricing(self):
        """PRIORITY TEST 3: Package API with Sponsored Pricing"""
        print("🔄 Testing Package API with Sponsored Pricing...")
        
        try:
            response = requests.get(f"{self.base_url}/packages", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                packages = response.json()
                if isinstance(packages, list) and len(packages) > 0:
                    # Find sponsored packages
                    sponsored_packages = [pkg for pkg in packages if pkg.get("is_sponsored", False)]
                    
                    if sponsored_packages:
                        # Check for required sponsored pricing fields
                        required_fields = ["is_sponsored", "original_price", "sponsored_price", "discount_percentage"]
                        
                        valid_sponsored = 0
                        for pkg in sponsored_packages:
                            if all(field in pkg and pkg[field] is not None for field in required_fields):
                                # Verify pricing logic
                                if (pkg["original_price"] > pkg["sponsored_price"] and 
                                    pkg["sponsored_price"] == pkg["price"]):
                                    valid_sponsored += 1
                        
                        if valid_sponsored == len(sponsored_packages):
                            self.log_result("Package API with Sponsored Pricing", True, 
                                          f"All {len(sponsored_packages)} sponsored packages have correct pricing fields")
                            return True
                        else:
                            self.log_result("Package API with Sponsored Pricing", False, 
                                          f"Only {valid_sponsored}/{len(sponsored_packages)} sponsored packages have valid pricing")
                            return False
                    else:
                        self.log_result("Package API with Sponsored Pricing", False, 
                                      "No sponsored packages found")
                        return False
                else:
                    self.log_result("Package API with Sponsored Pricing", False, 
                                  "No packages returned or invalid format")
                    return False
            else:
                self.log_result("Package API with Sponsored Pricing", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Package API with Sponsored Pricing", False, f"Request failed: {str(e)}")
            return False

    def test_core_auth_data_apis(self):
        """PRIORITY TEST 4: Core Auth & Data APIs"""
        print("🔄 Testing Core Auth & Data APIs...")
        
        # Test POST /api/init-data
        try:
            init_response = requests.post(f"{self.base_url}/init-data", headers=self.headers, timeout=30)
            if init_response.status_code != 200:
                self.log_result("Core Auth & Data APIs - Init Data", False, 
                              f"POST /api/init-data failed: HTTP {init_response.status_code}")
                return False
            
            # Test GET /api/agents (general agent listing)
            agents_response = requests.get(f"{self.base_url}/agents", headers=self.headers, timeout=10)
            if agents_response.status_code != 200:
                self.log_result("Core Auth & Data APIs - Agents", False, 
                              f"GET /api/agents failed: HTTP {agents_response.status_code}")
                return False
            
            agents = agents_response.json()
            if not isinstance(agents, list) or len(agents) == 0:
                self.log_result("Core Auth & Data APIs - Agents", False, 
                              "No agents returned from GET /api/agents")
                return False
            
            # Test GET /api/ribbons (filter ribbons)
            ribbons_response = requests.get(f"{self.base_url}/ribbons", headers=self.headers, timeout=10)
            if ribbons_response.status_code != 200:
                self.log_result("Core Auth & Data APIs - Ribbons", False, 
                              f"GET /api/ribbons failed: HTTP {ribbons_response.status_code}")
                return False
            
            ribbons = ribbons_response.json()
            if not isinstance(ribbons, list) or len(ribbons) == 0:
                self.log_result("Core Auth & Data APIs - Ribbons", False, 
                              "No ribbons returned from GET /api/ribbons")
                return False
            
            # Test authentication flow (register + login)
            new_user_data = {
                "username": "auth_test_" + str(uuid.uuid4())[:8],
                "email": f"auth_test_{uuid.uuid4()}@example.com",
                "password": "TestPass123!",
                "full_name": "Auth Test User"
            }
            
            # Test POST /api/register
            register_response = requests.post(
                f"{self.base_url}/auth/register",
                headers=self.headers,
                json=new_user_data,
                timeout=10
            )
            
            if register_response.status_code != 200:
                self.log_result("Core Auth & Data APIs - Register", False, 
                              f"POST /api/register failed: HTTP {register_response.status_code}")
                return False
            
            register_data = register_response.json()
            if not all(key in register_data for key in ["access_token", "token_type", "user"]):
                self.log_result("Core Auth & Data APIs - Register", False, 
                              "Missing required fields in register response")
                return False
            
            # Test POST /api/login
            login_data = {
                "username": new_user_data["username"],
                "password": new_user_data["password"]
            }
            
            login_response = requests.post(
                f"{self.base_url}/auth/login",
                headers=self.headers,
                json=login_data,
                timeout=10
            )
            
            if login_response.status_code != 200:
                self.log_result("Core Auth & Data APIs - Login", False, 
                              f"POST /api/login failed: HTTP {login_response.status_code}")
                return False
            
            login_response_data = login_response.json()
            if not all(key in login_response_data for key in ["access_token", "token_type", "user"]):
                self.log_result("Core Auth & Data APIs - Login", False, 
                              "Missing required fields in login response")
                return False
            
            self.log_result("Core Auth & Data APIs", True, 
                          f"✅ All core APIs working: init-data, agents ({len(agents)}), ribbons ({len(ribbons)}), register, login")
            return True
                
        except Exception as e:
            self.log_result("Core Auth & Data APIs", False, f"Request failed: {str(e)}")
            return False

    def test_sponsored_filter_backend_fix(self):
        """Validate that the sponsored filter backend fix is working"""
        print("🔄 Testing Sponsored Filter Backend Fix...")
        
        try:
            # Test the specific fix: GET /api/agents?agent_type=sponsored should return subscribed agents
            sponsored_response = requests.get(
                f"{self.base_url}/agents?agent_type=sponsored", 
                headers=self.headers, 
                timeout=10
            )
            
            if sponsored_response.status_code == 200:
                sponsored_agents = sponsored_response.json()
                
                # Also get all agents to compare
                all_response = requests.get(f"{self.base_url}/agents", headers=self.headers, timeout=10)
                if all_response.status_code == 200:
                    all_agents = all_response.json()
                    
                    # Count subscribed agents in all agents
                    subscribed_count = len([a for a in all_agents if a.get("is_subscribed", False)])
                    sponsored_returned = len(sponsored_agents)
                    
                    if sponsored_returned > 0 and sponsored_returned == subscribed_count:
                        # Verify all returned agents are actually subscribed
                        all_subscribed = all(agent.get("is_subscribed", False) for agent in sponsored_agents)
                        
                        if all_subscribed:
                            self.log_result("Sponsored Filter Backend Fix", True, 
                                          f"✅ Backend fix working: {sponsored_returned} subscribed agents returned correctly")
                            return True
                        else:
                            self.log_result("Sponsored Filter Backend Fix", False, 
                                          "Some returned agents are not subscribed")
                            return False
                    else:
                        self.log_result("Sponsored Filter Backend Fix", False, 
                                      f"Count mismatch: {sponsored_returned} sponsored returned vs {subscribed_count} subscribed total")
                        return False
                else:
                    self.log_result("Sponsored Filter Backend Fix", False, 
                                  "Could not retrieve all agents for comparison")
                    return False
            else:
                self.log_result("Sponsored Filter Backend Fix", False, 
                              f"Sponsored filter request failed: HTTP {sponsored_response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Sponsored Filter Backend Fix", False, f"Request failed: {str(e)}")
            return False

    def run_phase4_validation(self):
        """Run Phase 4 validation tests"""
        print("=" * 70)
        print("🚀 PHASE 4: BACKEND VALIDATION TESTING")
        print("=" * 70)
        print(f"Testing against: {self.base_url}")
        print("Focus: Validate critical functionality after frontend fixes")
        print()
        
        # Setup authentication first
        auth_success = self.setup_authentication()
        
        # Priority tests as specified in review request
        test_sequence = [
            # PRIORITY TEST 1: Sponsored Filter API (main user complaint)
            self.test_sponsored_filter_api,
            self.test_sponsored_filter_backend_fix,
            
            # PRIORITY TEST 2: Chat API Functionality
            self.test_chat_api_functionality,
            
            # PRIORITY TEST 3: Package API with Sponsored Pricing
            self.test_package_api_sponsored_pricing,
            
            # PRIORITY TEST 4: Core Auth & Data APIs
            self.test_core_auth_data_apis,
        ]
        
        for test_func in test_sequence:
            test_func()
        
        # Print summary
        print("=" * 70)
        print("📊 PHASE 4 VALIDATION SUMMARY")
        print("=" * 70)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        
        if self.results['passed'] + self.results['failed'] > 0:
            success_rate = (self.results['passed'] / (self.results['passed'] + self.results['failed']) * 100)
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.results['errors']:
            print("\n🔍 FAILED TESTS:")
            for error in self.results['errors']:
                print(f"   • {error}")
        else:
            print("\n🎉 ALL PHASE 4 VALIDATION TESTS PASSED!")
            print("✅ Sponsored filter backend fix is working")
            print("✅ Chat functionality remains operational")
            print("✅ Package data has proper sponsored pricing fields")
            print("✅ Core functionality validated")
        
        print("=" * 70)
        
        return self.results['failed'] == 0

if __name__ == "__main__":
    tester = Phase4Tester()
    success = tester.run_phase4_validation()
    sys.exit(0 if success else 1)