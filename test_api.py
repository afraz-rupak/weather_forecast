#!/usr/bin/env python3
"""
Comprehensive Weather Prediction API Test Runner

This script tests all endpoints of the Weather Prediction API with various scenarios
including success cases, error cases, and edge cases.
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List
import sys

class WeatherAPITester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip('/')
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def test_server_connection(self) -> bool:
        """Test if server is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                self.log_test("Server Connection", True, f"Server responding on {self.base_url}")
                return True
            else:
                self.log_test("Server Connection", False, f"Server returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Connection", False, f"Cannot connect to server: {str(e)}")
            return False
    
    def test_root_endpoint(self):
        """Test the root endpoint documentation"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            data = response.json()
            
            # Check required fields
            required_fields = ["project", "description", "endpoints", "github_repo"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if response.status_code == 200 and not missing_fields:
                self.log_test("Root Endpoint", True, f"Documentation loaded successfully")
            else:
                self.log_test("Root Endpoint", False, f"Missing fields: {missing_fields}")
                
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Error: {str(e)}")
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health/", timeout=10)
            data = response.json()
            
            # Check health response structure
            expected_fields = ["status", "message", "timestamp", "models"]
            missing_fields = [field for field in expected_fields if field not in data]
            
            models_loaded = data.get("models", {})
            rain_model = models_loaded.get("rain_model_loaded", False)
            precip_model = models_loaded.get("precipitation_model_loaded", False)
            
            if response.status_code == 200 and not missing_fields:
                model_status = f"Rain: {rain_model}, Precipitation: {precip_model}"
                self.log_test("Health Check", True, f"Status: {data['status']}, Models: {model_status}")
            else:
                self.log_test("Health Check", False, f"Missing fields: {missing_fields}")
                
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {str(e)}")
    
    def test_rain_prediction_valid_dates(self):
        """Test rain prediction with valid dates"""
        test_dates = [
            datetime.now().strftime("%Y-%m-%d"),  # Today
            (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),  # 7 days ago
            (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),  # 3 days from now
        ]
        
        for test_date in test_dates:
            try:
                response = requests.get(f"{self.base_url}/predict/rain/?date={test_date}", timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    # Validate response structure
                    if "input_date" in data and "prediction" in data:
                        prediction = data["prediction"]
                        if "date" in prediction and "will_rain" in prediction:
                            will_rain = prediction["will_rain"]
                            pred_date = prediction["date"]
                            self.log_test(f"Rain Prediction ({test_date})", True, 
                                        f"Prediction for {pred_date}: {'Rain' if will_rain else 'No Rain'}")
                        else:
                            self.log_test(f"Rain Prediction ({test_date})", False, "Invalid prediction structure")
                    else:
                        self.log_test(f"Rain Prediction ({test_date})", False, "Invalid response structure")
                else:
                    self.log_test(f"Rain Prediction ({test_date})", False, 
                                f"HTTP {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                self.log_test(f"Rain Prediction ({test_date})", False, f"Error: {str(e)}")
    
    def test_precipitation_prediction_valid_dates(self):
        """Test precipitation prediction with valid dates"""
        test_dates = [
            datetime.now().strftime("%Y-%m-%d"),  # Today
            (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),  # 5 days ago
            (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),  # 2 days from now
        ]
        
        for test_date in test_dates:
            try:
                response = requests.get(f"{self.base_url}/predict/precipitation/fall/?date={test_date}", timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    # Validate response structure
                    if "input_date" in data and "prediction" in data:
                        prediction = data["prediction"]
                        required_fields = ["start_date", "end_date", "precipitation_fall"]
                        if all(field in prediction for field in required_fields):
                            precip = prediction["precipitation_fall"]
                            start = prediction["start_date"]
                            end = prediction["end_date"]
                            self.log_test(f"Precipitation Prediction ({test_date})", True, 
                                        f"{start} to {end}: {precip}mm")
                        else:
                            self.log_test(f"Precipitation Prediction ({test_date})", False, "Invalid prediction structure")
                    else:
                        self.log_test(f"Precipitation Prediction ({test_date})", False, "Invalid response structure")
                else:
                    self.log_test(f"Precipitation Prediction ({test_date})", False, 
                                f"HTTP {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                self.log_test(f"Precipitation Prediction ({test_date})", False, f"Error: {str(e)}")
    
    def test_invalid_date_formats(self):
        """Test API with invalid date formats"""
        invalid_dates = [
            "2024-13-01",  # Invalid month
            "2024-02-30",  # Invalid day
            "invalid-date",  # Invalid format
            "2024/12/20",  # Wrong separator
            "20-12-2024",  # Wrong order
        ]
        
        for invalid_date in invalid_dates:
            try:
                # Test rain endpoint
                response = requests.get(f"{self.base_url}/predict/rain/?date={invalid_date}", timeout=10)
                if response.status_code in [400, 422]:
                    self.log_test(f"Invalid Date Rain ({invalid_date})", True, 
                                f"Correctly rejected with {response.status_code}")
                else:
                    self.log_test(f"Invalid Date Rain ({invalid_date})", False, 
                                f"Should reject but got {response.status_code}")
                
                # Test precipitation endpoint
                response = requests.get(f"{self.base_url}/predict/precipitation/fall/?date={invalid_date}", timeout=10)
                if response.status_code in [400, 422]:
                    self.log_test(f"Invalid Date Precipitation ({invalid_date})", True, 
                                f"Correctly rejected with {response.status_code}")
                else:
                    self.log_test(f"Invalid Date Precipitation ({invalid_date})", False, 
                                f"Should reject but got {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Invalid Date ({invalid_date})", False, f"Error: {str(e)}")
    
    def test_missing_parameters(self):
        """Test API endpoints without required parameters"""
        endpoints = [
            "/predict/rain/",
            "/predict/precipitation/fall/"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 422:
                    self.log_test(f"Missing Parameter {endpoint}", True, 
                                "Correctly rejected missing date parameter")
                else:
                    self.log_test(f"Missing Parameter {endpoint}", False, 
                                f"Should return 422 but got {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Missing Parameter {endpoint}", False, f"Error: {str(e)}")
    
    def test_api_documentation(self):
        """Test API documentation endpoints"""
        doc_endpoints = ["/docs", "/redoc"]
        
        for endpoint in doc_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    self.log_test(f"Documentation {endpoint}", True, "Documentation accessible")
                else:
                    self.log_test(f"Documentation {endpoint}", False, 
                                f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Documentation {endpoint}", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Weather Prediction API Tests")
        print("=" * 50)
        
        # Test server connection first
        if not self.test_server_connection():
            print("\n❌ Cannot connect to server. Make sure the API is running on", self.base_url)
            return False
        
        print("\n📊 Running API Tests...")
        
        # Core functionality tests
        self.test_root_endpoint()
        self.test_health_endpoint()
        
        # Prediction tests
        print("\n🌧️  Testing Rain Predictions...")
        self.test_rain_prediction_valid_dates()
        
        print("\n💧 Testing Precipitation Predictions...")
        self.test_precipitation_prediction_valid_dates()
        
        # Error handling tests
        print("\n🚫 Testing Error Handling...")
        self.test_invalid_date_formats()
        self.test_missing_parameters()
        
        # Documentation tests
        print("\n📚 Testing Documentation...")
        self.test_api_documentation()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"🎯 TEST SUMMARY")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📊 Total: {len(self.test_results)}")
        
        success_rate = (self.passed / len(self.test_results)) * 100 if self.test_results else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.failed > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"   - {result['test']}: {result['details']}")
        
        return self.failed == 0

def main():
    """Main function to run tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Weather Prediction API")
    parser.add_argument("--url", default="http://localhost:8001", 
                       help="Base URL of the API (default: http://localhost:8001)")
    parser.add_argument("--production", action="store_true",
                       help="Test production deployment (requires --url)")
    
    args = parser.parse_args()
    
    if args.production and args.url == "http://localhost:8001":
        print("❌ Please specify --url when using --production flag")
        sys.exit(1)
    
    print(f"🌦️  Weather Prediction API Tester")
    print(f"🔗 Testing URL: {args.url}")
    
    if args.production:
        print("☁️  Production mode - testing deployed API")
    else:
        print("🏠 Local mode - make sure to start the server first:")
        print("   cd weather_forecast/weather_forecast/weather_forecast")
        print("   python main.py")
    
    print()
    
    tester = WeatherAPITester(args.url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()