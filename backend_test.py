#!/usr/bin/env python3
"""
Comprehensive Backend API Tests for Miyawaki Forest Planner Tool
Tests all core endpoints and business logic
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Backend URL from environment
BACKEND_URL = "https://26a90ab7-9c14-4dbe-a00d-997096dacb9e.preview.emergentagent.com/api"

class MiyawakiAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.user_id = None
        self.created_resources = {
            'users': [],
            'locations': [],
            'plots': [],
            'projects': [],
            'alerts': []
        }
    
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_health_check(self):
        """Test GET /api/ - Health check endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("Health Check", True, "API is responding correctly")
                    return True
                else:
                    self.log_test("Health Check", False, "Invalid response format", data)
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_create_location(self):
        """Test POST /api/locations - Create location entries"""
        try:
            # Test data for Bangalore, India (tropical climate)
            location_data = {
                "latitude": 12.9716,
                "longitude": 77.5946,
                "address": "Cubbon Park Area",
                "city": "Bangalore",
                "state": "Karnataka",
                "country": "India"
            }
            
            response = self.session.post(f"{self.base_url}/locations", json=location_data)
            if response.status_code == 200:
                data = response.json()
                if "id" in data and data["latitude"] == location_data["latitude"]:
                    self.created_resources['locations'].append(data["id"])
                    self.log_test("Create Location", True, "Location created successfully")
                    return data["id"]
                else:
                    self.log_test("Create Location", False, "Invalid response format", data)
                    return None
            else:
                self.log_test("Create Location", False, f"HTTP {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Create Location", False, f"Request error: {str(e)}")
            return None
    
    def test_get_locations(self):
        """Test GET /api/locations - Retrieve all locations"""
        try:
            response = self.session.get(f"{self.base_url}/locations")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get Locations", True, f"Retrieved {len(data)} locations")
                    return True
                else:
                    self.log_test("Get Locations", False, "Response is not a list", data)
                    return False
            else:
                self.log_test("Get Locations", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Get Locations", False, f"Request error: {str(e)}")
            return False
    
    def test_native_species_tropical(self):
        """Test GET /api/species/native - Get native species for tropical climate"""
        try:
            # Test with Bangalore coordinates (tropical)
            params = {
                "latitude": 12.9716,
                "longitude": 77.5946,
                "limit": 10
            }
            
            response = self.session.get(f"{self.base_url}/species/native", params=params)
            if response.status_code == 200:
                data = response.json()
                if "species" in data and "climate_zone" in data:
                    species_list = data["species"]
                    climate_zone = data["climate_zone"]
                    
                    if climate_zone == "tropical" and len(species_list) > 0:
                        # Check if species have required fields
                        first_species = species_list[0]
                        required_fields = ["scientific_name", "common_name", "plant_type", "miyawaki_layer"]
                        if all(field in first_species for field in required_fields):
                            self.log_test("Native Species (Tropical)", True, 
                                        f"Retrieved {len(species_list)} tropical species")
                            return True
                        else:
                            self.log_test("Native Species (Tropical)", False, 
                                        "Species missing required fields", first_species)
                            return False
                    else:
                        self.log_test("Native Species (Tropical)", False, 
                                    f"Wrong climate zone or no species: {climate_zone}")
                        return False
                else:
                    self.log_test("Native Species (Tropical)", False, "Invalid response format", data)
                    return False
            else:
                self.log_test("Native Species (Tropical)", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Native Species (Tropical)", False, f"Request error: {str(e)}")
            return False
    
    def test_native_species_temperate(self):
        """Test GET /api/species/native - Get native species for temperate climate"""
        try:
            # Test with London coordinates (temperate)
            params = {
                "latitude": 51.5074,
                "longitude": -0.1278,
                "limit": 10
            }
            
            response = self.session.get(f"{self.base_url}/species/native", params=params)
            if response.status_code == 200:
                data = response.json()
                if "species" in data and "climate_zone" in data:
                    climate_zone = data["climate_zone"]
                    species_list = data["species"]
                    
                    if climate_zone == "temperate" and len(species_list) > 0:
                        self.log_test("Native Species (Temperate)", True, 
                                    f"Retrieved {len(species_list)} temperate species")
                        return True
                    else:
                        self.log_test("Native Species (Temperate)", False, 
                                    f"Wrong climate zone or no species: {climate_zone}")
                        return False
                else:
                    self.log_test("Native Species (Temperate)", False, "Invalid response format", data)
                    return False
            else:
                self.log_test("Native Species (Temperate)", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Native Species (Temperate)", False, f"Request error: {str(e)}")
            return False
    
    def test_create_plot_design(self, location_id):
        """Test POST /api/plots - Create plot designs"""
        if not location_id:
            self.log_test("Create Plot Design", False, "No location ID available")
            return None
            
        try:
            plot_data = {
                "user_id": str(uuid.uuid4()),
                "location_id": location_id,
                "plot_size": 100.0,  # 100 square meters
                "planting_method": "ground",
                "soil_type": "loam",
                "selected_species": [str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())]
            }
            
            response = self.session.post(f"{self.base_url}/plots", json=plot_data)
            if response.status_code == 200:
                data = response.json()
                if "id" in data and data["plot_size"] == plot_data["plot_size"]:
                    self.created_resources['plots'].append(data["id"])
                    self.log_test("Create Plot Design", True, "Plot design created successfully")
                    return data["id"]
                else:
                    self.log_test("Create Plot Design", False, "Invalid response format", data)
                    return None
            else:
                self.log_test("Create Plot Design", False, f"HTTP {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Create Plot Design", False, f"Request error: {str(e)}")
            return None
    
    def test_get_plot_designs(self):
        """Test GET /api/plots - Retrieve plot designs"""
        try:
            response = self.session.get(f"{self.base_url}/plots")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get Plot Designs", True, f"Retrieved {len(data)} plot designs")
                    return True
                else:
                    self.log_test("Get Plot Designs", False, "Response is not a list", data)
                    return False
            else:
                self.log_test("Get Plot Designs", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Get Plot Designs", False, f"Request error: {str(e)}")
            return False
    
    def test_3d_design_generation(self, plot_id):
        """Test GET /api/plots/{plot_id}/3d-design - Get 3D visualization design"""
        if not plot_id:
            self.log_test("3D Design Generation", False, "No plot ID available")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/plots/{plot_id}/3d-design")
            if response.status_code == 200:
                data = response.json()
                required_fields = ["plot_id", "plot_size", "total_plants", "layers"]
                if all(field in data for field in required_fields):
                    layers = data["layers"]
                    # Check Miyawaki layer structure
                    expected_layers = ["canopy", "sub_canopy", "shrub", "ground"]
                    if all(layer in layers for layer in expected_layers):
                        # Verify planting density calculation (3-5 plants per sq meter)
                        plot_size = data["plot_size"]
                        total_plants = data["total_plants"]
                        density = total_plants / plot_size
                        if 3 <= density <= 5:
                            self.log_test("3D Design Generation", True, 
                                        f"Generated 3D design with {total_plants} plants, density: {density:.1f}/m²")
                            return True
                        else:
                            self.log_test("3D Design Generation", False, 
                                        f"Invalid planting density: {density:.1f}/m² (should be 3-5)")
                            return False
                    else:
                        self.log_test("3D Design Generation", False, "Missing Miyawaki layers", layers)
                        return False
                else:
                    self.log_test("3D Design Generation", False, "Missing required fields", data)
                    return False
            else:
                self.log_test("3D Design Generation", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("3D Design Generation", False, f"Request error: {str(e)}")
            return False
    
    def test_weather_data(self, location_id):
        """Test GET /api/weather/{location_id} - Get weather data for location"""
        if not location_id:
            self.log_test("Weather Data", False, "No location ID available")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/weather/{location_id}")
            if response.status_code == 200:
                data = response.json()
                required_fields = ["location_id", "temperature", "humidity", "weather_condition"]
                if all(field in data for field in required_fields):
                    self.log_test("Weather Data", True, 
                                f"Retrieved weather: {data['temperature']}°C, {data['weather_condition']}")
                    return True
                else:
                    self.log_test("Weather Data", False, "Missing required weather fields", data)
                    return False
            else:
                self.log_test("Weather Data", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Weather Data", False, f"Request error: {str(e)}")
            return False
    
    def test_soil_guidance(self):
        """Test GET /api/soil/guidance - Get soil preparation guidance by soil type"""
        soil_types = ["clay", "sandy", "loam", "rocky"]
        
        for soil_type in soil_types:
            try:
                params = {"soil_type": soil_type}
                response = self.session.get(f"{self.base_url}/soil/guidance", params=params)
                if response.status_code == 200:
                    data = response.json()
                    if "soil_type" in data and "guidance" in data:
                        guidance = data["guidance"]
                        required_fields = ["preparation", "ph_adjustment", "nutrients", "drainage"]
                        if all(field in guidance for field in required_fields):
                            self.log_test(f"Soil Guidance ({soil_type})", True, 
                                        f"Retrieved guidance for {soil_type} soil")
                        else:
                            self.log_test(f"Soil Guidance ({soil_type})", False, 
                                        "Missing guidance fields", guidance)
                            return False
                    else:
                        self.log_test(f"Soil Guidance ({soil_type})", False, 
                                    "Invalid response format", data)
                        return False
                else:
                    self.log_test(f"Soil Guidance ({soil_type})", False, 
                                f"HTTP {response.status_code}", response.text)
                    return False
            except Exception as e:
                self.log_test(f"Soil Guidance ({soil_type})", False, f"Request error: {str(e)}")
                return False
        
        return True
    
    def test_create_project(self, plot_id):
        """Test POST /api/projects - Create plantation projects"""
        if not plot_id:
            self.log_test("Create Project", False, "No plot ID available")
            return None
            
        try:
            project_data = {
                "user_id": str(uuid.uuid4()),
                "plot_design_id": plot_id,
                "project_name": "Urban Miyawaki Forest - Bangalore",
                "manager_name": "Dr. Priya Sharma",
                "manager_phone": "+91-9876543210"
            }
            
            response = self.session.post(f"{self.base_url}/projects", json=project_data)
            if response.status_code == 200:
                data = response.json()
                if "id" in data and data["project_name"] == project_data["project_name"]:
                    self.created_resources['projects'].append(data["id"])
                    self.log_test("Create Project", True, "Project created successfully")
                    return data["id"]
                else:
                    self.log_test("Create Project", False, "Invalid response format", data)
                    return None
            else:
                self.log_test("Create Project", False, f"HTTP {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Create Project", False, f"Request error: {str(e)}")
            return None
    
    def test_project_timeline(self, project_id):
        """Test GET /api/timeline/{project_id} - Get project care timeline"""
        if not project_id:
            self.log_test("Project Timeline", False, "No project ID available")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/timeline/{project_id}")
            if response.status_code == 200:
                data = response.json()
                if "project_id" in data and "phases" in data:
                    phases = data["phases"]
                    expected_phases = ["Preparation", "Planting", "Intensive Care", "Monitoring"]
                    phase_names = [phase["phase"] for phase in phases]
                    if all(expected in phase_names for expected in expected_phases):
                        self.log_test("Project Timeline", True, 
                                    f"Retrieved timeline with {len(phases)} phases")
                        return True
                    else:
                        self.log_test("Project Timeline", False, 
                                    f"Missing expected phases. Got: {phase_names}")
                        return False
                else:
                    self.log_test("Project Timeline", False, "Invalid response format", data)
                    return False
            else:
                self.log_test("Project Timeline", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Project Timeline", False, f"Request error: {str(e)}")
            return False
    
    def test_project_alerts(self, project_id):
        """Test GET /api/alerts/{project_id} - Get project alerts"""
        if not project_id:
            self.log_test("Project Alerts", False, "No project ID available")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/alerts/{project_id}")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    if len(data) > 0:
                        alert = data[0]
                        required_fields = ["id", "project_id", "alert_type", "severity", "message"]
                        if all(field in alert for field in required_fields):
                            self.log_test("Project Alerts", True, 
                                        f"Retrieved {len(data)} alerts")
                            return True
                        else:
                            self.log_test("Project Alerts", False, 
                                        "Alert missing required fields", alert)
                            return False
                    else:
                        self.log_test("Project Alerts", True, "No alerts found (valid)")
                        return True
                else:
                    self.log_test("Project Alerts", False, "Response is not a list", data)
                    return False
            else:
                self.log_test("Project Alerts", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Project Alerts", False, f"Request error: {str(e)}")
            return False
    
    def test_learning_resources(self):
        """Test GET /api/learning/resources - Get educational resources"""
        try:
            response = self.session.get(f"{self.base_url}/learning/resources")
            if response.status_code == 200:
                data = response.json()
                required_sections = ["articles", "videos", "case_studies"]
                if all(section in data for section in required_sections):
                    articles = data["articles"]
                    videos = data["videos"]
                    case_studies = data["case_studies"]
                    
                    if len(articles) > 0 and len(videos) > 0 and len(case_studies) > 0:
                        self.log_test("Learning Resources", True, 
                                    f"Retrieved {len(articles)} articles, {len(videos)} videos, {len(case_studies)} case studies")
                        return True
                    else:
                        self.log_test("Learning Resources", False, 
                                    "Empty resource sections", data)
                        return False
                else:
                    self.log_test("Learning Resources", False, 
                                "Missing required sections", data)
                    return False
            else:
                self.log_test("Learning Resources", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Learning Resources", False, f"Request error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🌳 Starting Miyawaki Forest Planner API Tests")
        print("=" * 60)
        
        # Test 1: Health Check
        if not self.test_health_check():
            print("❌ API is not responding. Stopping tests.")
            return False
        
        # Test 2: Location Management
        location_id = self.test_create_location()
        self.test_get_locations()
        
        # Test 3: Native Species API (Core Feature)
        self.test_native_species_tropical()
        self.test_native_species_temperate()
        
        # Test 4: Plot Design System
        plot_id = self.test_create_plot_design(location_id)
        self.test_get_plot_designs()
        self.test_3d_design_generation(plot_id)
        
        # Test 5: Weather and Soil Guidance
        self.test_weather_data(location_id)
        self.test_soil_guidance()
        
        # Test 6: Project Management
        project_id = self.test_create_project(plot_id)
        self.test_project_timeline(project_id)
        self.test_project_alerts(project_id)
        
        # Test 7: Learning Hub
        self.test_learning_resources()
        
        # Summary
        self.print_summary()
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🌳 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n🌳 Miyawaki Forest Planner API Testing Complete!")

def main():
    """Main test execution"""
    tester = MiyawakiAPITester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()