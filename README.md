# Weather Forecast API

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Weather prediction REST API for Sydney, Australia using machine learning models trained on historical weather data.

## Overview

This project provides a FastAPI-based web service that predicts:
1. **Rain Prediction**: Will it rain in exactly 7 days? (Binary classification)
2. **Precipitation Forecasting**: Cumulative precipitation amount for the next 3 days (Regression)

The API automatically fetches real-time weather data from Open-Meteo API and uses trained ML models to make predictions.

## Quick Start

### 1. Setup Environment
```bash
cd /Users/afrazrupak/weather_forecast
source .venv/bin/activate  # Activate virtual environment
pip install -r requirements.txt
```

### 2. Start the API Server
```bash
cd weather_forecast/weather_forecast
python main.py
```
The API will be available at: `http://localhost:8001`

### 3. Test the API
```bash
# Run comprehensive test suite
cd /Users/afrazrupak/weather_forecast
python test_weather_api.py

# Or test individual endpoints
curl "http://localhost:8001/predict/rain/?date=2023-06-15"
curl "http://localhost:8001/predict/precipitation/fall/?date=2023-06-15"
```

## API Endpoints

### Core Prediction Endpoints

#### Rain Prediction (7-day forecast)
```
GET /predict/rain/?date=YYYY-MM-DD
```
**Input**: Date in YYYY-MM-DD format
**Output**: Rain prediction for exactly 7 days ahead
```json
{
  "input_date": "2023-06-15",
  "prediction": {
    "date": "2023-06-22",
    "will_rain": true
  }
}
```

#### Precipitation Prediction (3-day forecast)
```
GET /predict/precipitation/fall/?date=YYYY-MM-DD
```
**Input**: Date in YYYY-MM-DD format
**Output**: Cumulative precipitation for next 3 days
```json
{
  "input_date": "2023-06-15",
  "prediction": {
    "start_date": "2023-06-16",
    "end_date": "2023-06-18",
    "precipitation_fall": "2.3"
  }
}
```

### Utility Endpoints

- `GET /` - Project description and API documentation
- `GET /health/` - Health check and model status
- Interactive documentation: `http://localhost:8001/docs`

## Usage Examples

### Python Client
```python
import requests

# Rain prediction
response = requests.get("http://localhost:8001/predict/rain/", 
                       params={"date": "2023-06-15"})
rain_data = response.json()
print(f"Will it rain on {rain_data['prediction']['date']}? {rain_data['prediction']['will_rain']}")

# Precipitation prediction
response = requests.get("http://localhost:8001/predict/precipitation/fall/", 
                       params={"date": "2023-06-15"})
precip_data = response.json()
print(f"Expected precipitation: {precip_data['prediction']['precipitation_fall']} mm")
```

### Command Line (cURL)
```bash
# Rain prediction
curl "http://localhost:8001/predict/rain/?date=2023-06-15" | jq '.'

# Precipitation prediction
curl "http://localhost:8001/predict/precipitation/fall/?date=2023-06-15" | jq '.'

# Health check
curl "http://localhost:8001/health/" | jq '.'
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

async function getRainPrediction(date) {
    const response = await axios.get(`http://localhost:8001/predict/rain/`, {
        params: { date: date }
    });
    return response.data;
}

// Usage
getRainPrediction('2023-06-15').then(data => {
    console.log(`Rain prediction for ${data.prediction.date}: ${data.prediction.will_rain}`);
});
```

## Key Features

- **Real-time Data Fetching**: Automatically retrieves weather data from Open-Meteo API
- **Simple Input**: User only needs to provide a date (YYYY-MM-DD format)
- **Trained ML Models**: Uses DummyClassifier and GradientBoosting models
- **Sydney Location**: Coordinates (-33.8678, 151.2073) for accurate local predictions
- **Fast API**: Built with FastAPI for high-performance async operations
- **Comprehensive Testing**: Includes test suites for all endpoints
- **Error Handling**: Proper HTTP status codes and validation

## Models Used

- **Rain Classification**: DummyClassifier model trained on daily weather features
- **Precipitation Regression**: GradientBoosting model trained on hourly weather features

Models are automatically loaded from the `models/` directory on startup:
- `rain_classifier_best_DummyClassifier_20250928_033307.joblib`
- `precipitation_regressor_best_GradientBoosting_20250928_052241.joblib`

## Project Structure

```
├── LICENSE                    <- Open-source license
├── Makefile                   <- Convenience commands for development
├── README.md                  <- Project documentation
├── requirements.txt           <- Python dependencies
├── test_api.py               <- Legacy API test script
├── test_weather_api.py       <- Main API test suite
├── API_README.md             <- Detailed API documentation
│
├── data/                     <- Weather datasets
│   ├── external/             <- Third-party data sources
│   ├── interim/              <- Intermediate processed data
│   ├── processed/            <- Final datasets for modeling
│   └── raw/                  <- Original weather data
│       ├── daily_with_targets.csv
│       └── hourly_with_targets.csv
│
├── models/                   <- Trained ML models and metadata
│   ├── rain_classifier_best_DummyClassifier_20250928_033307.joblib
│   ├── precipitation_regressor_best_GradientBoosting_20250928_052241.joblib
│   ├── model_summary_*.txt
│   └── *_metadata_*.json
│
├── notebooks/               <- Jupyter notebooks for analysis
│   ├── data_colletion.ipynb
│   ├── Daily weather forecasting EDA.ipynb
│   ├── Hourly weather forecasting EDA.ipynb
│   └── experiment notebooks
│
├── reports/                 <- Generated analysis and figures
│   └── figures/
│
└── weather_forecast/        <- Main source code
    ├── __init__.py
    ├── main.py              <- FastAPI application
    └── __pycache__/
```

## Development

### Running in Development Mode
```bash
cd weather_forecast/weather_forecast
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### Running Tests
```bash
# Comprehensive API testing
python test_weather_api.py

# Legacy tests
python test_api.py
```

### Adding New Features
1. Modify `main.py` to add new endpoints
2. Update test scripts to include new functionality
3. Update documentation in README.md and API_README.md

## Architecture

The API follows a simple but effective architecture:

```
User Request (date only)
    ↓
FastAPI Router
    ↓
WeatherDataFetcher → Open-Meteo API (Sydney coordinates)
    ↓
Feature Processing
    ↓
ML Model Prediction (Rain/Precipitation)
    ↓
JSON Response
```

## Data Sources

- **Weather Data**: Open-Meteo API (historical and forecast data)
- **Location**: Sydney, Australia (-33.8678, 151.2073)
- **Features**: Temperature, humidity, pressure, wind, precipitation, radiation, etc.

## Performance

- **Response Time**: < 2 seconds (including external API calls)
- **Concurrent Requests**: Supports multiple simultaneous requests
- **Model Loading**: Models loaded once on startup for optimal performance
- **Caching**: Consider implementing caching for frequently requested dates

## Error Handling

- **400**: Bad Request (invalid date format)
- **503**: Service Unavailable (models not loaded)
- **500**: Internal Server Error (API or prediction failures)

## Monitoring and Health Checks

Use the health endpoint to monitor API status:
```bash
curl http://localhost:8001/health/
```

Response includes:
- API status
- Model loading status
- Timestamp
- Welcome message

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## License

This project is licensed under the terms specified in the LICENSE file.

---

For detailed API documentation, see [API_README.md](../API_README.md)

