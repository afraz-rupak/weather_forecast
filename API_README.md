# Weather Prediction FastAPI Service

A high-performance REST API for weather predictions using trained machine learning models. This service provides two main prediction capabilities:

1. **Rain Prediction**: Binary classification - will it rain in exactly 7 days?
2. **Precipitation Forecasting**: Regression - cumulative precipitation amount for the next 3 days (72 hours)

## Quick Start

### 1. Install Dependencies

```bash
cd /Users/afrazrupak/weather_forecast
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
# Navigate to the project directory
cd weather_forecast

# Start the server
python main.py

# OR using uvicorn directly (recommended for production)
uvicorn weather_forecast.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: `http://localhost:8000`

### 3. Test the API

```bash
# Run the test script
python ../test_api.py
```

## API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Core Endpoints

#### 1. Rain Prediction (7-day forecast)
```
POST /predict/rain
```

**Example Request:**
```json
{
  "input_date": "2023-01-01",
  "temperature_2m_max": 25.5,
  "temperature_2m_min": 15.2,
  "temperature_2m_mean": 20.3,
  "relative_humidity_2m_max": 85.0,
  "relative_humidity_2m_min": 45.0,
  "pressure_msl_mean": 1013.25,
  "wind_speed_10m_max": 15.6,
  "wind_speed_10m_mean": 8.2,
  "wind_direction_10m_dominant": 180.0,
  "precipitation_sum": 2.5,
  "rain_sum": 2.0,
  "shortwave_radiation_sum": 15.8,
  "daylight_duration": 12.5
}
```

**Example Response:**
```json
{
  "input_date": "2023-01-01",
  "prediction": {
    "date": "2023-01-08",
    "will_rain": true,
    "confidence": 0.75
  }
}
```

#### 2. Precipitation Prediction (3-day forecast)
```
POST /predict/precipitation
```

**Example Request:**
```json
{
  "input_date": "2023-01-01",
  "temperature_2m": 22.3,
  "relative_humidity_2m": 65.0,
  "dew_point_2m": 15.8,
  "precipitation": 0.5,
  "rain": 0.3,
  "pressure_msl": 1013.25,
  "cloud_cover": 45.0,
  "wind_speed_10m": 12.5,
  "wind_direction_10m": 180.0,
  "shortwave_radiation": 250.0,
  "surface_pressure": 1015.0,
  "cloud_cover_low": 20.0,
  "cloud_cover_mid": 15.0,
  "cloud_cover_high": 10.0
}
```

**Example Response:**
```json
{
  "input_date": "2023-01-01",
  "prediction": {
    "start_date": "2023-01-02",
    "end_date": "2023-01-04",
    "precipitation_fall": "28.2",
    "unit": "mm",
    "period_hours": 72
  }
}
```

### Utility Endpoints

#### Health Check
```
GET /health
```
Returns API status and model loading status.

#### Model Information
```
GET /models/info
```
Returns metadata about the loaded ML models.

#### Sample Data
```
GET /predict/sample-data
```
Returns sample input data for testing both endpoints.

## Usage Examples

### Python (using requests)

```python
import requests

# Rain prediction
rain_response = requests.post('http://localhost:8000/predict/rain', json={
    "input_date": "2023-01-01",
    "temperature_2m_max": 25.5,
    # ... other required fields
})

# Precipitation prediction  
precip_response = requests.post('http://localhost:8000/predict/precipitation', json={
    "input_date": "2023-01-01", 
    "temperature_2m": 22.3,
    # ... other required fields
})
```

### cURL

```bash
# Rain prediction
curl -X POST "http://localhost:8000/predict/rain" \
     -H "Content-Type: application/json" \
     -d @rain_sample.json

# Precipitation prediction
curl -X POST "http://localhost:8000/predict/precipitation" \
     -H "Content-Type: application/json" \
     -d @precipitation_sample.json
```

## Models Used

- **Rain Classification**: DummyClassifier model (trained on daily weather data)
- **Precipitation Regression**: GradientBoosting model (trained on hourly weather data)

Models are automatically loaded from the `models/` directory on startup.

## Key Features

- **Fast Performance**: Built with FastAPI for high-performance async operations
- **Automatic Documentation**: Interactive Swagger UI and ReDoc documentation
- **Input Validation**: Pydantic models ensure data integrity
- **Error Handling**: Comprehensive error responses with helpful messages
- **Health Monitoring**: Health check endpoint for monitoring
- **Model Metadata**: Access to model information and performance metrics
- **Sample Data**: Built-in sample data for easy testing

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │───▶│  Model Loader   │───▶│ Trained Models  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       ├── Rain Classifier
         │                       │                       └── Precipitation Regressor
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│ REST Endpoints  │    │   Predictions   │
│                 │    │                 │
│ /predict/rain   │    │ • 7-day rain    │
│ /predict/precip │    │ • 3-day amount  │
│ /health         │    │                 │
│ /models/info    │    │                 │
└─────────────────┘    └─────────────────┘
```

## Development

### Running in Development Mode
```bash
uvicorn weather_forecast.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
python test_api.py
```

## Performance

- **Response Time**: < 100ms for single predictions
- **Concurrent Requests**: Supports high concurrency with async/await
- **Model Loading**: Models loaded once on startup for optimal performance

## Error Handling

The API includes comprehensive error handling:
- **400**: Bad Request (invalid input data)
- **503**: Service Unavailable (models not loaded)
- **500**: Internal Server Error (prediction failures)

## Monitoring

Use the health endpoint to monitor API status:
```bash
curl http://localhost:8000/health
```

Returns model loading status and overall API health.