# Project Configuration and Constants

# ============================================================================
# ENTSOE API Configuration
# ============================================================================
ENTSOE_BASE_URL = "https://web-api.tp.entsoe.eu/api"
ENTSOE_API_TIMEOUT = 30  # seconds

# ENTSOE Domain Codes for European Countries
ENTSOE_DOMAIN_CODES = {
    'Germany': '10Y1001A1001A83F',
    'France': '10YFR-RTE------C',
    'Italy': '10YIT-GRTN-----B',
    'Spain': '10YES-REE------0',
    'Netherlands': '10YNL----------L',
    'Belgium': '10YBE----------2',
    'Austria': '10YAT-APG------L',
    'Poland': '10YPL-AREA-----S',
    'Switzerland': '10YCH-SWISSGRIDZ',
    'Czech Republic': '10YCZ-CEPS-----N',
    'Denmark': '10Y1001A1001A65H',
    'Sweden': '10YSE-1--------K',
    'Norway': '10YNO-0--------C',
    'UK': '10YGB----------A',
    'Ireland': '10YIE-1001A00010',
    'Portugal': '10YPT-REN------W',
    'Greece': '10YGR-HTSO-----Y'
}

# ============================================================================
# Machine Learning Model Configuration
# ============================================================================
# Linear Regression Model Settings
ML_MODEL_TEST_SIZE = 0.2  # 80% train, 20% test
ML_MODEL_RANDOM_STATE = 42  # For reproducibility
ML_TARGET_COLUMN = 'price'

# Feature Engineering Settings
TEMPORAL_FEATURES = [
    'hour', 'day_of_week', 'month', 'day_of_month',
    'hour_sin', 'hour_cos',
    'dow_sin', 'dow_cos',
    'month_sin', 'month_cos',
    'is_weekend', 'is_peak_hour'
]

CONSUMPTION_FEATURES = [
    'consumption', 'consumption_squared', 'consumption_log'
]

PEAK_HOURS = [(7, 10), (18, 22)]  # 7-10 AM and 6-10 PM

# ============================================================================
# Fuzzy Logic Configuration
# ============================================================================
FUZZY_PRICE_THRESHOLDS = {
    'low': 30,
    'moderate_low': 50,
    'moderate_high': 75,
    'high': 100
}

FUZZY_CONSUMPTION_THRESHOLDS = {
    'low': 400,
    'moderate_low': 500,
    'moderate_high': 600,
    'high': 700
}

FUZZY_ERROR_THRESHOLDS = {
    'low': 2,
    'moderate_low': 5,
    'moderate_high': 10,
    'high': 15
}

# ============================================================================
# Streamlit UI Configuration
# ============================================================================
PAGE_TITLE = "Energy Price Explainability Dashboard"
PAGE_ICON = "⚡"
PAGE_LAYOUT = "wide"

# Color Codes for Status Indicators
COLOR_CODES = {
    'very_low': 'green',
    'low': 'green',
    'moderate': 'orange',
    'high': 'red',
    'very_high': 'red'
}

# Sidebar Styling
SIDEBAR_WIDTH = 300

# ============================================================================
# Data Configuration
# ============================================================================
SAMPLE_DATA_PATH = 'data/energy_data.csv'
DEFAULT_SAMPLE_DATA_DAYS = 7
ENTSOE_MAX_DAYS = 30  # ENTSOE API limit
ENTSOE_CHUNK_SIZE = 14  # Days per API request (to avoid rate limits)

# ============================================================================
# Session State Defaults
# ============================================================================
DEFAULT_SESSION_STATE = {
    'model_trained': False,
    'predictor': None,
    'df': None,
    'data_source': 'sample',
    'market_context': None,
    'fuzzy_analysis': None,
    'responses': []
}

# ============================================================================
# Evaluation Form Configuration
# ============================================================================
EVALUATION_RATING_SCALE = (1, 5)  # 1 to 5 stars
EVALUATION_SLIDER_DEFAULTS = {
    'method_a_helpfulness': 3,
    'method_b_helpfulness': 3,
    'understandability_a': 3,
    'understandability_b': 3
}

EVALUATION_PREFERENCE_OPTIONS = [
    "Select an option",
    "Method A (Numerical)",
    "Method B (Linguistic)",
    "Both Equally",
    "Neither"
]

# ============================================================================
# Debug & Logging Configuration
# ============================================================================
DEBUG_MODE = False
LOG_LEVEL = 'INFO'  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# ============================================================================
# Feature Importance Thresholds
# ============================================================================
TOP_FEATURES_COUNT = 8  # Show top N features in UI
MIN_FEATURE_IMPORTANCE = 0.001  # Minimum coefficient magnitude to display

# ============================================================================
# Market Context Thresholds
# ============================================================================
PRICE_VOLATILITY_THRESHOLD = 0.5  # 50% of mean price
DEMAND_CHANGE_THRESHOLD = 100  # MW change
PRICE_DEVIATION_THRESHOLD = 20  # Percentage deviation from mean

# ============================================================================
# Prediction Sampling
# ============================================================================
SAMPLE_PREDICTIONS_COUNT = 10
ERROR_PERCENTILES = [25, 75]  # Q1 and Q3 for quartile analysis

# ============================================================================
# Export Configuration
# ============================================================================
EXPORT_TIMESTAMP_FORMAT = '%Y%m%d_%H%M%S'
EXPORT_CSV_DELIMITER = ','

# ============================================================================
# URL References
# ============================================================================
ENTSOE_REGISTRATION_URL = "https://transparency.entsoe.eu/"
DOCUMENTATION_URL = "https://transparency.entsoe.eu/content/static_content/download?path=../API/documentation_v04.00.01_final.pdf"
