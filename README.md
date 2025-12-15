# ⚡ Energy Price & Consumption Explainability Dashboard

A dual-explanation system research tool that compares **numerical machine learning explanations** with **natural language fuzzy reasoning** for energy market price predictions.

## 🎯 Project Overview

This dashboard demonstrates an innovative approach to AI explainability by presenting two complementary explanation methods:

- **Method A (Numerical)**: Statistical metrics, feature importance, and prediction error analysis using Linear Regression
- **Method B (Linguistic)**: Natural language explanations powered by fuzzy logic and real-time ENTSOE market context

The tool is designed for researchers and students to evaluate which explanation method is more effective for understanding energy price dynamics.

## ✨ Key Features

- **Dual Explanation System**: Side-by-side comparison of numerical vs. linguistic explanations
- **Multiple Data Sources**:
  - Pre-loaded sample data (7 days)
  - CSV upload capability
  - Real-time ENTSOE Transparency Platform API integration
- **Advanced Feature Engineering**: 
  - Cyclical encoding for temporal features
  - Peak hour detection
  - Energy consumption transformations
- **Fuzzy Logic Reasoning**: 
  - Natural language categorization of prices and consumption
  - Market trend analysis
  - Contextual insights from real-time energy data
- **Evaluation System**: Built-in student feedback collection form with export capability
- **Interactive Dashboard**: Real-time visualizations and metrics using Streamlit

## 📊 Technology Stack

| Component | Technology |
|-----------|-----------|
| **Web Framework** | Streamlit 1.50.0 |
| **ML Models** | Scikit-learn 1.7.2 |
| **Fuzzy Logic** | Scikit-fuzzy 0.5.0 |
| **Data Processing** | Pandas 2.3.3, NumPy 2.3.4 |
| **Data Visualization** | Matplotlib, Altair |
| **API Integration** | Requests 2.32.5 (ENTSOE) |
| **XML Parsing** | lxml 6.0.2 |
| **Environment Management** | Python-dotenv 1.2.1 |
| **Network Analysis** | NetworkX 3.5 |

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Virtual environment (recommended)
- ENTSOE API token (for real-time data) - Get it at: https://transparency.entsoe.eu/

### Installation

1. **Clone and navigate to project directory**:
   ```bash
   cd energy-explain
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/macOS
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your ENTSOE API token
   ```

5. **Generate sample data** (optional):
   ```bash
   python data/generate_sample_data.py
   ```

6. **Run the application**:
   ```bash
   streamlit run app.py
   ```

The dashboard will open at `http://localhost:8501`

## 📖 Usage Guide

### Step 1: Select Data Source
Choose from three options in the sidebar:
- **Sample Data**: Pre-loaded 7 days of hourly data
- **Upload CSV**: Provide your own dataset with columns: `datetime`, `energy_consumption`, `price`
- **Real-time ENTSOE Data**: Fetch live European energy market data (requires API token)

### Step 2: Train Model
Click "🚀 Train Model" to build the Linear Regression predictor with automated feature engineering.

### Step 3: View Explanations
Compare two methods side-by-side:
- **Method A**: Numerical analysis with metrics, feature importance, and prediction samples
- **Method B**: Linguistic explanations with fuzzy categorization and market context

### Step 4: Provide Feedback
Complete the evaluation form to help assess the effectiveness of each explanation method.

### Step 5: Export Results
Download all collected responses as CSV for further analysis.

## 🏗️ Project Structure

```
energy-explain/
├── app.py                          # Main Streamlit application
├── main.py                         # Entry point
├── debug.py                        # ENTSOE API debug utility
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── pyproject.toml                  # Project configuration
│
├── app/                            # Application modules
│   ├── __init__.py                # Package initialization
│   ├── entsoe_client.py           # ENTSOE API client
│   ├── predictor.py               # ML predictor model
│   ├── fuzzy_explainer.py         # Fuzzy logic engine
│   └── reason_extractor.py        # Market reasoning engine
│
├── data/                           # Data directory
│   ├── energy_data.csv            # Sample energy data
│   └── generate_sample_data.py    # Sample data generator
│
└── docs/                           # Documentation (optional)
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file with:
```env
ENTSOE_API_TOKEN=your_api_token_here
```

### ENTSOE Supported Countries
- Germany, France, Italy, Spain
- Netherlands, Belgium, Austria, Poland
- Switzerland, Czech Republic, Denmark, Sweden
- Norway, UK, Ireland, Portugal, Greece
