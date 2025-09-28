"""
Weather Prediction FastAPI Service

This API provides weather predictions using trained ML models with real-time weather data fetching.
User only needs to provide a date, and the system automatically fetches weather data from Open-Meteo API.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import joblib
import numpy as np
import requests
import json
import os
from typing import Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Weather Prediction API",
    description="AI-powered weather forecasting API for Sydney, Australia",
    version="1.0.0"
)

# Global variables
rain_model = None
precipitation_model = None

# Configuration - Use environment variables for deployment
MODELS_DIR = os.getenv("MODELS_DIR", os.path.join(os.path.dirname(__file__), "..", "models"))
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
CURRENT_URL = "https://api.open-meteo.com/v1/forecast"
SYDNEY_COORDS = {"latitude": -33.8678, "longitude": 151.2073}

# Model file paths - Use relative paths for deployment
RAIN_MODEL_PATH = os.path.join(MODELS_DIR, "rain_classifier_best_DummyClassifier_20250928_033307.joblib")
PRECIPITATION_MODEL_PATH = os.path.join(MODELS_DIR, "precipitation_regressor_best_GradientBoosting_20250928_052241.joblib")

class WeatherDataFetcher:
    """Fetch real-time weather data from Open-Meteo API"""
    
    @staticmethod
    def fetch_weather_for_date(input_date: str) -> Dict:
        """Fetch weather data for a specific date"""
        date_obj = datetime.strptime(input_date, "%Y-%m-%d")
        current_date = datetime.now()
        
        # Determine if we need historical or forecast data
        if date_obj.date() <= current_date.date():
            return WeatherDataFetcher._fetch_historical_data(input_date)
        else:
            return WeatherDataFetcher._fetch_forecast_data(input_date)
    
    @staticmethod
    def _fetch_historical_data(input_date: str) -> Dict:
        """Fetch historical weather data"""
        try:
            # Daily features for rain prediction
            daily_params = {
                **SYDNEY_COORDS,
                "start_date": input_date,
                "end_date": input_date,
                "daily": [
                    "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
                    "relative_humidity_2m_max", "relative_humidity_2m_min",
                    "pressure_msl_mean", "wind_speed_10m_max", "wind_speed_10m_mean",
                    "wind_direction_10m_dominant", "precipitation_sum", "rain_sum",
                    "shortwave_radiation_sum", "daylight_duration"
                ],
                "timezone": "Australia/Sydney"
            }
            
            daily_response = requests.get(BASE_URL, params=daily_params, timeout=10)
            daily_response.raise_for_status()
            daily_data = daily_response.json()["daily"]
            
            # Hourly features for precipitation prediction (get first hour)
            hourly_params = {
                **SYDNEY_COORDS,
                "start_date": input_date,
                "end_date": input_date,
                "hourly": [
                    "temperature_2m", "relative_humidity_2m", "dew_point_2m",
                    "precipitation", "rain", "pressure_msl", "cloud_cover",
                    "wind_speed_10m", "wind_direction_10m", "shortwave_radiation",
                    "surface_pressure", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high"
                ],
                "timezone": "Australia/Sydney"
            }
            
            hourly_response = requests.get(BASE_URL, params=hourly_params, timeout=10)
            hourly_response.raise_for_status()
            hourly_data = hourly_response.json()["hourly"]
            
            # Extract single day/hour values
            daily_features = {key: daily_data[key][0] for key in daily_data if key != "time"}
            hourly_features = {key: hourly_data[key][0] for key in hourly_data if key != "time"}
            
            return {
                "daily_features": daily_features,
                "hourly_features": hourly_features,
                "data_source": "historical"
            }
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch weather data: {str(e)}")
    
    @staticmethod
    def _fetch_forecast_data(input_date: str) -> Dict:
        """Fetch forecast weather data for future dates"""
        try:
            forecast_params = {
                **SYDNEY_COORDS,
                "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
                "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation"],
                "timezone": "Australia/Sydney",
                "forecast_days": 14
            }
            
            response = requests.get(CURRENT_URL, params=forecast_params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Find the specific date
            target_date = datetime.strptime(input_date, "%Y-%m-%d").date()
            daily_times = [datetime.fromisoformat(t).date() for t in data["daily"]["time"]]
            
            if target_date not in daily_times:
                raise ValueError(f"Forecast not available for {input_date}")
            
            date_index = daily_times.index(target_date)
            
            # Extract forecast data
            daily_features = {}
            for feature in data["daily"]:
                if feature != "time":
                    daily_features[feature] = data["daily"][feature][date_index]
            
            hourly_features = {}
            hourly_start_index = date_index * 24
            for feature in data["hourly"]:
                if feature != "time" and hourly_start_index < len(data["hourly"][feature]):
                    hourly_features[feature] = data["hourly"][feature][hourly_start_index]
            
            return {
                "daily_features": daily_features,
                "hourly_features": hourly_features,
                "data_source": "forecast"
            }
            
        except Exception as e:
            logger.error(f"Error fetching forecast data: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch forecast data: {str(e)}")

def load_models():
    """Load trained models"""
    global rain_model, precipitation_model
    
    try:
        if os.path.exists(RAIN_MODEL_PATH):
            rain_model = joblib.load(RAIN_MODEL_PATH)
            logger.info("Rain classification model loaded successfully")
        else:
            logger.warning(f"Rain model not found at {RAIN_MODEL_PATH}")
            
        if os.path.exists(PRECIPITATION_MODEL_PATH):
            precipitation_model = joblib.load(PRECIPITATION_MODEL_PATH)
            logger.info("Precipitation regression model loaded successfully")
        else:
            logger.warning(f"Precipitation model not found at {PRECIPITATION_MODEL_PATH}")
            
    except Exception as e:
        logger.error(f"Error loading models: {e}")

@app.on_event("startup")
async def startup_event():
    """Load models when the application starts"""
    load_models()

@app.get("/")
async def root():
    """Project description and endpoints"""
    return {
        "project": "Weather Prediction API",
        "description": "AI-powered weather forecasting service providing rain predictions and precipitation forecasts for Sydney, Australia",
        "objectives": [
            "Predict if it will rain in exactly 7 days (binary classification)",
            "Predict cumulative precipitation amount for next 3 days (regression)"
        ],
        "endpoints": {
            "/": "GET - Project description and documentation",
            "/health/": "GET - Health check and status",
            "/predict/rain/": "GET - Rain prediction for 7 days ahead",
            "/predict/precipitation/fall/": "GET - 3-day precipitation forecast"
        },
        "input_parameters": {
            "date": "Required date parameter in YYYY-MM-DD format"
        },
        "output_format": {
            "rain_prediction": {
                "input_date": "YYYY-MM-DD",
                "prediction": {
                    "date": "YYYY-MM-DD (7 days ahead)",
                    "will_rain": "boolean"
                }
            },
            "precipitation_prediction": {
                "input_date": "YYYY-MM-DD",
                "prediction": {
                    "start_date": "YYYY-MM-DD (next day)",
                    "end_date": "YYYY-MM-DD (3 days later)",
                    "precipitation_fall": "string (mm)"
                }
            }
        },
        "github_repo": "https://github.com/afrazrupak/weather_forecast",
        "location": "Sydney, Australia (-33.8678, 151.2073)"
    }

@app.get("/health/")
async def health_check():
    """Health check endpoint"""
    model_status = {
        "rain_model_loaded": rain_model is not None,
        "precipitation_model_loaded": precipitation_model is not None,
    }
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "message": "Welcome to the Weather Prediction API! All systems operational and ready to forecast Sydney's weather.",
            "timestamp": datetime.now().isoformat(),
            "models": model_status
        }
    )

@app.get("/predict/rain/")
async def predict_rain(date: str = Query(..., description="Date in YYYY-MM-DD format for which to predict rain 7 days ahead")):
    """Predict if it will rain in exactly 7 days"""
    if rain_model is None:
        raise HTTPException(status_code=503, detail="Rain prediction model not available")
    
    try:
        # Validate date format
        input_date_obj = datetime.strptime(date, "%Y-%m-%d")
        prediction_date = (input_date_obj + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Fetch weather data for the input date
        weather_data = WeatherDataFetcher.fetch_weather_for_date(date)
        daily_features = weather_data["daily_features"]
        
        # Prepare features for model (in the same order as training)
        feature_order = [
            "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
            "relative_humidity_2m_max", "relative_humidity_2m_min",
            "pressure_msl_mean", "wind_speed_10m_max", "wind_speed_10m_mean",
            "wind_direction_10m_dominant", "precipitation_sum", "rain_sum",
            "shortwave_radiation_sum", "daylight_duration"
        ]
        
        # Handle missing features with defaults
        features = []
        for feature in feature_order:
            if feature in daily_features:
                features.append(daily_features[feature])
            else:
                # Use reasonable defaults for missing features
                default_values = {
                    "temperature_2m_max": 20.0, "temperature_2m_min": 15.0, "temperature_2m_mean": 17.5,
                    "relative_humidity_2m_max": 80.0, "relative_humidity_2m_min": 60.0,
                    "pressure_msl_mean": 1013.25, "wind_speed_10m_max": 10.0, "wind_speed_10m_mean": 5.0,
                    "wind_direction_10m_dominant": 180.0, "precipitation_sum": 0.0, "rain_sum": 0.0,
                    "shortwave_radiation_sum": 10.0, "daylight_duration": 12.0
                }
                features.append(default_values.get(feature, 0.0))
        
        # Make prediction
        X = np.array(features).reshape(1, -1)
        prediction = rain_model.predict(X)[0]
        
        return {
            "input_date": date,
            "prediction": {
                "date": prediction_date,
                "will_rain": bool(prediction)
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD: {str(e)}")
    except Exception as e:
        logger.error(f"Error in rain prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.get("/predict/precipitation/fall/")
async def predict_precipitation(date: str = Query(..., description="Date in YYYY-MM-DD format for which to predict precipitation for next 3 days")):
    """Predict cumulative precipitation amount for the next 3 days"""
    if precipitation_model is None:
        raise HTTPException(status_code=503, detail="Precipitation prediction model not available")
    
    try:
        # Validate date format
        input_date_obj = datetime.strptime(date, "%Y-%m-%d")
        start_date = (input_date_obj + timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (input_date_obj + timedelta(days=3)).strftime("%Y-%m-%d")
        
        # Fetch weather data for the input date
        weather_data = WeatherDataFetcher.fetch_weather_for_date(date)
        hourly_features = weather_data["hourly_features"]
        
        # Prepare features for model (in the same order as training)
        feature_order = [
            "temperature_2m", "relative_humidity_2m", "dew_point_2m",
            "precipitation", "rain", "pressure_msl", "cloud_cover",
            "wind_speed_10m", "wind_direction_10m", "shortwave_radiation",
            "surface_pressure", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high"
        ]
        
        # Handle missing features with defaults
        features = []
        for feature in feature_order:
            if feature in hourly_features:
                features.append(hourly_features[feature])
            else:
                # Use reasonable defaults for missing features
                default_values = {
                    "temperature_2m": 18.0, "relative_humidity_2m": 70.0, "dew_point_2m": 12.0,
                    "precipitation": 0.0, "rain": 0.0, "pressure_msl": 1013.25, "cloud_cover": 50.0,
                    "wind_speed_10m": 8.0, "wind_direction_10m": 180.0, "shortwave_radiation": 200.0,
                    "surface_pressure": 1015.0, "cloud_cover_low": 30.0, "cloud_cover_mid": 20.0, "cloud_cover_high": 10.0
                }
                features.append(default_values.get(feature, 0.0))
        
        # Make prediction
        X = np.array(features).reshape(1, -1)
        prediction = precipitation_model.predict(X)[0]
        
        # Ensure prediction is not negative
        prediction = max(0.0, float(prediction))
        
        return {
            "input_date": date,
            "prediction": {
                "start_date": start_date,
                "end_date": end_date,
                "precipitation_fall": f"{prediction:.1f}"
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD: {str(e)}")
    except Exception as e:
        logger.error(f"Error in precipitation prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)