# API Documentation

## Module Overview

This document provides comprehensive API documentation for all modules in the Energy Price Explainability Dashboard.

## Table of Contents

1. [app.py](#apppy) - Main Streamlit Application
2. [entsoe_client.py](#entsoe_clientpy) - ENTSOE API Integration
3. [predictor.py](#predictorpy) - Machine Learning Model
4. [fuzzy_explainer.py](#fuzzy_explainerpy) - Fuzzy Logic Engine
5. [reason_extractor.py](#reason_extractorpy) - Market Analysis
6. [config.py](#configpy) - Configuration

---

## app.py

Main Streamlit dashboard application for the Energy Price Explainability System.

### Configuration

```python
st.set_page_config(
    page_title="Energy Price Explainability Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

### Session State Keys

Key session state variables maintained throughout the app lifecycle:

| Key | Type | Description |
|-----|------|-------------|
| `model_trained` | bool | Whether ML model has been trained |
| `predictor` | EnergyPricePredictor | Trained model instance |
| `df` | DataFrame | Current dataset |
| `data_source` | str | Source of data ('sample', 'upload', 'entsoe') |
| `market_context` | dict | Real-time market data context |
| `fuzzy_analysis` | dict | Fuzzy logic analysis results |
| `responses` | list | Collected evaluation responses |

### Main Components

#### Data Loading
- Sample Data: Pre-loaded 7 days of hourly energy data
- CSV Upload: User-provided data with validation
- ENTSOE API: Real-time European energy market data

#### Model Training
Trains linear regression model with automated feature engineering

#### Dual Explanation Display
**Method A (Numerical)**: Statistical metrics and feature importance
**Method B (Linguistic)**: Natural language fuzzy reasoning

#### Evaluation Form
Collects user feedback on explanation methods with ratings and comments

---

## entsoe_client.py

### Class: ENTSOEClient

Handles all communication with ENTSOE Transparency Platform API.

#### Constructor

```python
ENTSOEClient(api_token: Optional[str] = None)
```

**Parameters:**
- `api_token` (str, optional): ENTSOE API token. If not provided, uses `ENTSOE_API_TOKEN` environment variable

**Attributes:**
- `api_token` (str): API authentication token
- `DOMAIN_CODES` (dict): Mapping of country names to ENTSOE domain codes

#### Methods

##### fetch_day_ahead_prices

```python
fetch_day_ahead_prices(
    country: str,
    start_date: Union[str, datetime],
    end_date: Union[str, datetime]
) -> Optional[pd.DataFrame]
```

Fetch day-ahead electricity prices from ENTSOE.

**Parameters:**
- `country` (str): Country name (e.g., 'Germany', 'France')
- `start_date`: Start date for data range
- `end_date`: End date for data range

**Returns:**
- DataFrame with columns: `datetime`, `price`
- None if request fails

**Raises:**
- `ValueError`: If country not supported
- `Exception`: If API request fails

**Example:**
```python
client = ENTSOEClient(api_token='your_token')
prices = client.fetch_day_ahead_prices('Germany', '2024-01-01', '2024-01-07')
```

##### fetch_actual_prices

```python
fetch_actual_prices(
    country: str,
    start_date: Union[str, datetime],
    end_date: Union[str, datetime]
) -> Optional[pd.DataFrame]
```

Fetch actual realized prices from ENTSOE.

**Parameters & Returns:** Same as `fetch_day_ahead_prices`

##### fetch_actual_load

```python
fetch_actual_load(
    country: str,
    start_date: Union[str, datetime],
    end_date: Union[str, datetime]
) -> Optional[pd.DataFrame]
```

Fetch actual total system load (energy consumption).

**Returns:**
- DataFrame with columns: `datetime`, `energy_consumption`

##### fetch_complete_dataset

```python
fetch_complete_dataset(
    country: str,
    days: int = 30
) -> Optional[pd.DataFrame]
```

Fetch combined price and load dataset for specified number of days.

**Parameters:**
- `country` (str): Country name
- `days` (int): Number of days to fetch (max 30, default 30)

**Returns:**
- DataFrame with columns: `datetime`, `price`, `energy_consumption`
- Automatically splits requests into 14-day chunks to comply with API limits
- Returns synthetic data if API unavailable

**Note:** Fetches data from 30 days ago to yesterday (respects data lag in ENTSOE)

##### get_market_context

```python
get_market_context(
    country: str,
    days: int = 2
) -> Dict[str, Any]
```

Safe wrapper returning structured market context dictionary.

**Parameters:**
- `country` (str): Country name
- `days` (int): Number of days for context (default 2)

**Returns:**
```python
{
    'data_available': bool,  # True if data fetched successfully
    'country': str,          # Country name
    'latest_price': float,   # Most recent price
    'latest_consumption': float,  # Most recent consumption
    'mean_price': float,     # Average price
    'mean_consumption': float,    # Average consumption
    'price_stats': {         # Detailed price statistics
        'current': float,
        'mean': float,
        'max': float,
        'min': float
    },
    'load_stats': {          # Detailed consumption statistics
        'current': float,
        'mean': float,
        'max': float,
        'min': float
    },
    'df': DataFrame,         # Raw data
    'error': str,            # Error message (if data_available=False)
    'type': str              # Error type (if data_available=False)
}
```

---

## predictor.py

### Class: EnergyPricePredictor

Linear regression-based electricity price predictor with advanced feature engineering.

#### Constructor

```python
EnergyPricePredictor()
```

#### Methods

##### create_features

```python
create_features(df: pd.DataFrame) -> pd.DataFrame
```

Generate 15+ automated features for ML model.

**Features Created:**
- Temporal: hour, day_of_week, month, day_of_month
- Cyclical: hour_sin/cos, dow_sin/cos, month_sin/cos
- Indicators: is_weekend, is_peak_hour
- Consumption: consumption, consumption_squared, consumption_log

**Example:**
```python
df_features = predictor.create_features(df)
print(df_features.columns)
```

##### train

```python
train(
    df: pd.DataFrame,
    target_column: str = 'price',
    test_size: float = 0.2,
    random_state: int = 42
) -> EnergyPricePredictor
```

Train the linear regression model.

**Parameters:**
- `df`: Input DataFrame with datetime, energy_consumption, price
- `target_column`: Target variable name (default 'price')
- `test_size`: Fraction for test set (default 0.2)
- `random_state`: Random seed (default 42)

**Returns:** Self (for method chaining)

**Raises:**
- `ModelTrainingError`: If training fails

**Example:**
```python
predictor = EnergyPricePredictor()
predictor.train(df)
metrics = predictor.get_metrics()
```

##### get_metrics

```python
get_metrics() -> Optional[Dict[str, Dict[str, float]]]
```

Calculate model performance metrics.

**Returns:**
```python
{
    'train': {
        'mae': float,    # Mean Absolute Error
        'rmse': float,   # Root Mean Squared Error
        'r2': float      # R² Score
    },
    'test': {
        'mae': float,
        'rmse': float,
        'r2': float
    }
}
```

##### get_feature_importance

```python
get_feature_importance() -> Optional[pd.DataFrame]
```

Get features ranked by importance.

**Returns:** DataFrame with columns:
- `feature`: Feature name
- `coefficient`: Linear regression coefficient
- `abs_coefficient`: Absolute coefficient value (for ranking)

**Note:** Sorted by `abs_coefficient` in descending order

##### get_prediction_samples

```python
get_prediction_samples(n_samples: int = 10) -> Optional[pd.DataFrame]
```

Get sample predictions from test set.

**Parameters:**
- `n_samples` (int): Number of samples (default 10)

**Returns:** DataFrame with columns:
- `actual`: Actual target values
- `predicted`: Model predictions
- `error`: Prediction error

##### get_error_distribution

```python
get_error_distribution() -> Optional[Dict[str, float]]
```

Get detailed error statistics.

**Returns:** Dictionary with keys:
- `mean_error`, `std_error`, `min_error`, `max_error`
- `median_error`, `q25_error`, `q75_error`

##### predict

```python
predict(df: pd.DataFrame) -> Optional[np.ndarray]
```

Make predictions on new data.

**Parameters:**
- `df`: Input DataFrame with required columns

**Returns:** Array of predicted prices

**Raises:**
- `ValueError`: If model not trained

##### get_model_summary

```python
get_model_summary() -> Optional[Dict[str, Any]]
```

Get complete model summary.

**Returns:** Dictionary containing all metrics, importance, samples, and metadata

---

## fuzzy_explainer.py

### Class: FuzzyExplainer

Converts numerical values into linguistic explanations using fuzzy logic.

#### Methods

##### analyze_data

```python
analyze_data(
    df: pd.DataFrame,
    model_metrics: Optional[Dict] = None
) -> Dict[str, Dict[str, Any]]
```

Analyze data and create fuzzy categorizations.

**Parameters:**
- `df`: Energy data with price and consumption columns
- `model_metrics`: Optional model metrics for error analysis

**Returns:**
```python
{
    'price': {
        'category': str,          # 'very_low', 'low', 'moderate', 'high', 'very_high'
        'linguistic': str,        # Natural language term
        'trend': str,             # 'rising rapidly', 'stable', etc.
        'percentage': float       # Percentage of readings in category
    },
    'consumption': {
        'category': str,
        'linguistic': str,
        'trend': str,
        'percentage': float
    },
    'correlation': {
        'value': float,           # Price-consumption correlation
        'interpretation': str     # Natural language description
    }
}
```

##### generate_explanation

```python
generate_explanation(analysis: Dict[str, Dict]) -> str
```

Generate natural language explanation from fuzzy analysis.

**Parameters:**
- `analysis`: Output from `analyze_data()`

**Returns:** Markdown-formatted explanation string

**Example:**
```python
analysis = fuzzy.analyze_data(df, metrics)
explanation = fuzzy.generate_explanation(analysis)
print(explanation)  # Markdown formatted text
```

##### get_color_code

```python
get_color_code(category: str) -> str
```

Get color code for category visualization.

**Parameters:**
- `category`: Category name ('very_low', 'low', etc.)

**Returns:** Color code string for Streamlit

**Mapping:**
- 'very_low': 'green'
- 'low': 'green'
- 'moderate': 'orange'
- 'high': 'red'
- 'very_high': 'red'

##### generate_fuzzy_rules_summary

```python
generate_fuzzy_rules_summary() -> str
```

Generate documentation of fuzzy inference rules.

**Returns:** Markdown-formatted rules documentation

---

## reason_extractor.py

### Class: ReasonExtractor

Extracts market insights and contextual reasoning from energy data.

#### Methods

##### extract_price_drivers

```python
extract_price_drivers(market_context: Dict[str, Any]) -> List[Dict[str, str]]
```

Identify factors driving price changes.

**Returns:** List of driver dictionaries:
```python
[
    {
        'factor': str,           # e.g., 'Price Movement', 'Demand Change'
        'description': str,      # Human-readable description
        'impact': str            # 'high' or 'moderate'
    }
]
```

##### generate_market_insight

```python
generate_market_insight(market_context: Dict[str, Any]) -> str
```

Generate comprehensive market insight narrative.

**Parameters:**
- `market_context`: Output from `ENTSOEClient.get_market_context()`

**Returns:** Markdown-formatted market insight string

**Features:**
- Current price and load summary
- Identified market drivers
- Contextual interpretations
- Impact indicators (🔴 high, 🟡 moderate)

---

## config.py

Configuration constants and settings.

### ENTSOE Configuration

```python
ENTSOE_BASE_URL = "https://web-api.tp.entsoe.eu/api"
ENTSOE_API_TIMEOUT = 30  # seconds
ENTSOE_DOMAIN_CODES = {
    'Germany': '10Y1001A1001A83F',
    'France': '10YFR-RTE------C',
    # ... 15+ countries
}
```

### ML Model Configuration

```python
ML_MODEL_TEST_SIZE = 0.2
ML_MODEL_RANDOM_STATE = 42
ML_TARGET_COLUMN = 'price'

TEMPORAL_FEATURES = [
    'hour', 'day_of_week', 'month', 'day_of_month',
    'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos',
    'month_sin', 'month_cos', 'is_weekend', 'is_peak_hour'
]
```

### Fuzzy Logic Configuration

```python
FUZZY_PRICE_THRESHOLDS = {
    'low': 30,
    'moderate_low': 50,
    'moderate_high': 75,
    'high': 100
}
```

### UI Configuration

```python
PAGE_TITLE = "Energy Price Explainability Dashboard"
PAGE_ICON = "⚡"
PAGE_LAYOUT = "wide"
```

---

## logger_utils.py

Logging configuration and error handling utilities.

### Functions

#### setup_logger

```python
setup_logger(name: str, level: int = logging.INFO) -> logging.Logger
```

Setup logger with console and file handlers.

**Parameters:**
- `name` (str): Logger name (typically `__name__`)
- `level`: Logging level (default INFO)

**Returns:** Configured logger instance

**Example:**
```python
from app.logger_utils import setup_logger

logger = setup_logger(__name__)
logger.info("Processing started")
```

#### log_exception

```python
log_exception(
    logger: logging.Logger,
    exception: Exception,
    context: str = ""
)
```

Log exception with context.

**Parameters:**
- `logger`: Logger instance
- `exception`: Exception to log
- `context`: Additional context info

#### safe_operation

```python
safe_operation(
    logger: logging.Logger,
    operation_name: str,
    operation_func: callable,
    *args,
    **kwargs
) -> Any
```

Execute operation with error handling.

**Returns:** Result of operation or None if error occurred

---

## Error Classes

### EnergyExplainException

Base exception for all application errors.

### DataLoadError

Raised when data loading fails.

### ENTSOEAPIError

Raised when ENTSOE API call fails.

### ModelTrainingError

Raised when model training fails.

### FuzzyAnalysisError

Raised when fuzzy analysis fails.

---

## Type Hints Reference

Key type hints used throughout the codebase:

```python
from typing import Dict, List, Optional, Any, Union, Tuple

# Common patterns
Optional[pd.DataFrame]  # DataFrame or None
Dict[str, float]       # String keys, float values
List[Dict[str, str]]   # List of string dictionaries
Union[str, datetime]   # Either string or datetime
Tuple[int, int]        # Pair of integers
```

---

## Example Workflows

### Complete Prediction Pipeline

```python
import pandas as pd
from app.predictor import EnergyPricePredictor
from app.fuzzy_explainer import FuzzyExplainer

# Load data
df = pd.read_csv('energy_data.csv')
df['datetime'] = pd.to_datetime(df['datetime'])

# Train model
predictor = EnergyPricePredictor()
predictor.train(df)

# Get numerical explanation
metrics = predictor.get_metrics()
importance = predictor.get_feature_importance()

# Get linguistic explanation
fuzzy = FuzzyExplainer()
analysis = fuzzy.analyze_data(df, metrics)
explanation = fuzzy.generate_explanation(analysis)

print("Model R²:", metrics['test']['r2'])
print("Explanation:", explanation)
```

### Real-Time Data Integration

```python
from app.entsoe_client import ENTSOEClient

client = ENTSOEClient(api_token='your_token')
context = client.get_market_context('Germany', days=7)

if context['data_available']:
    print(f"Current price: €{context['latest_price']:.2f}/MWh")
    print(f"Mean price: €{context['mean_price']:.2f}/MWh")
else:
    print(f"Error: {context['error']}")
```

---

## Version Information

| Component | Version |
|-----------|---------|
| Python | 3.11+ |
| Scikit-learn | 1.7.2 |
| Scikit-fuzzy | 0.5.0 |
| Streamlit | 1.50.0 |
| Pandas | 2.3.3 |
| NumPy | 2.3.4 |

---

## Additional Resources

- [ENTSOE API Documentation](https://transparency.entsoe.eu/content/static_content/download?path=../API/documentation_v04.00.01_final.pdf)
- [Scikit-learn Models](https://scikit-learn.org/stable/modules/linear_model.html)
- [Scikit-fuzzy Documentation](https://scikit-fuzzy.github.io/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [Type Hints Guide](https://docs.python.org/3/library/typing.html)
