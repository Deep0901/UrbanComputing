# Contributing to Energy Price Explainability Dashboard

First of all, thank you for considering contributing! This document provides guidelines and instructions for contributing to the project.

## 🎯 Code of Conduct

This project is open to all respectful contributions. We are committed to providing a welcoming and inclusive environment for all contributors.

## 📋 Getting Started

### 1. Fork the Repository
If you're an external contributor:
```bash
# Fork the repository on GitHub
# Clone your fork locally
git clone https://github.com/yourusername/energy-explain.git
cd energy-explain
```

### 2. Set Up Development Environment
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install pytest pytest-cov black flake8 mypy
```

### 3. Create a Feature Branch
```bash
# Update main branch
git fetch origin
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/your-bug-name
```

## 🔧 Development Guidelines

### Code Style

We follow PEP 8 with some custom conventions:

1. **Line Length**: Maximum 100 characters
2. **Imports**: Organize as standard, third-party, local
3. **Type Hints**: Use type hints for all function parameters and returns
4. **Docstrings**: Use Google-style docstrings with examples

### Example Function:
```python
from typing import Dict, Optional
import pandas as pd

def process_energy_data(
    df: pd.DataFrame,
    country: str,
    window_size: int = 7
) -> Optional[Dict[str, float]]:
    """
    Process raw energy data into aggregated statistics.
    
    Calculates mean and standard deviation for price and consumption
    over specified window size.
    
    Args:
        df (pd.DataFrame): Input DataFrame with energy data
        country (str): Country code for data filtering
        window_size (int): Rolling window size in days (default: 7)
    
    Returns:
        Dict: Dictionary with statistics or None if processing fails
        Format: {
            'mean_price': float,
            'std_price': float,
            'mean_consumption': float,
            'std_consumption': float
        }
    
    Raises:
        ValueError: If window_size is negative
        KeyError: If required columns missing
    
    Example:
        >>> df = pd.DataFrame({...})
        >>> stats = process_energy_data(df, 'Germany')
        >>> print(stats['mean_price'])
        65.5
    """
    if window_size <= 0:
        raise ValueError("window_size must be positive")
    
    # Implementation
    return result
```

### File Organization

```
app/
├── __init__.py              # Package exports
├── config.py               # Configuration constants
├── logger_utils.py         # Logging utilities
├── entsoe_client.py        # ENTSOE API integration
├── predictor.py            # ML model
├── fuzzy_explainer.py      # Fuzzy logic engine
└── reason_extractor.py     # Market reasoning
```

## ✅ Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_predictor.py

# Run with coverage
pytest --cov=app tests/
```

### Writing Tests
Create test files in `tests/` directory following the pattern:
```python
import pytest
from app.predictor import EnergyPricePredictor
import pandas as pd

class TestEnergyPricePredictor:
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return pd.DataFrame({
            'datetime': pd.date_range('2024-01-01', periods=24, freq='H'),
            'energy_consumption': [450] * 24,
            'price': [65.5] * 24
        })
    
    def test_model_initialization(self):
        """Test that model initializes correctly."""
        predictor = EnergyPricePredictor()
        assert not predictor.is_trained
        assert len(predictor.feature_names) == 0
    
    def test_feature_creation(self, sample_data):
        """Test feature engineering."""
        predictor = EnergyPricePredictor()
        features = predictor.create_features(sample_data)
        
        assert 'hour_sin' in features.columns
        assert 'is_weekend' in features.columns
        assert len(features) == len(sample_data)
    
    def test_model_training(self, sample_data):
        """Test model training."""
        predictor = EnergyPricePredictor()
        predictor.train(sample_data)
        
        assert predictor.is_trained
        assert predictor.predictions_test is not None
        assert len(predictor.feature_names) > 0
```

## 📝 Commit Messages

Write clear, descriptive commit messages:

```
# Good
git commit -m "Add cyclical encoding for temporal features in feature engineering

- Implement sin/cos transformations for hour, day_of_week, month
- Improves model's ability to capture circular time patterns
- Fixes issue with discontinuity at midnight/week boundary"

# Avoid
git commit -m "fix stuff"
git commit -m "update"
```

### Commit Message Format
- Start with imperative verb (Add, Fix, Refactor, Update)
- Reference issues: "Fixes #123"
- Explain WHY, not just WHAT

## 🚀 Pull Request Process

### Before Submitting

1. **Update your branch**:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run tests**:
   ```bash
   pytest
   pytest --cov=app tests/
   ```

3. **Check code quality**:
   ```bash
   # Format code
   black app/ tests/
   
   # Check style
   flake8 app/ tests/ --max-line-length=100
   
   # Type checking
   mypy app/
   ```

4. **Update documentation**:
   - Update README if adding features
   - Update docstrings
   - Add comments for complex logic

### Submitting PR

1. Push your branch: `git push origin feature/your-feature-name`
2. Create Pull Request on GitHub
3. Fill out the PR template:
   ```
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation
   - [ ] Performance improvement
   
   ## Related Issues
   Fixes #123
   
   ## Testing
   Describe tests run
   
   ## Screenshots (if applicable)
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Added/updated tests
   - [ ] Updated documentation
   - [ ] No new warnings
   ```

4. Wait for review and address feedback

## 🐛 Bug Reports

### Reporting Bugs

Create an issue with:

```markdown
## Description
Clear description of the bug

## Steps to Reproduce
1. Load sample data
2. Train model
3. Click on "Feature Importance"

## Expected Behavior
Should display feature importance table

## Actual Behavior
Shows error: "AttributeError: ..."

## Environment
- Python: 3.11.x
- OS: Windows/Linux/macOS
- Streamlit: 1.50.0

## Error Log
[Paste full error trace]
```

## 💡 Feature Requests

Create an issue with:

```markdown
## Description
Clear description of the feature

## Use Case
Why would this feature be useful?

## Proposed Solution
How should this work?

## Alternatives Considered
Other approaches?
```

## 📚 Documentation

### Updating Docs

1. **README.md**: Update if changing user-facing features
2. **Docstrings**: Always update for code changes
3. **Type Hints**: Add for new functions/methods
4. **Comments**: Explain complex logic

### Documentation Standards

- Use clear, concise language
- Include code examples where helpful
- Keep documentation in sync with code
- Use markdown for formatting

## 🔄 Code Review Process

### What to Expect

1. **Initial Review**: Checks for:
   - Code style compliance
   - Test coverage
   - Documentation completeness
   - No breaking changes

2. **Feedback**: May request:
   - Changes to code
   - Additional tests
   - Documentation updates
   - Performance improvements

3. **Approval**: Merge if:
   - All comments resolved
   - Tests passing
   - Code review approved
   - Documentation updated

## 🎓 Project Structure & Architecture

### Key Components

1. **`app.py`** (Main Streamlit Dashboard)
   - UI layout and interactions
   - Session state management
   - Data flow orchestration

2. **`entsoe_client.py`** (Data Integration)
   - ENTSOE API communication
   - XML parsing
   - Data validation

3. **`predictor.py`** (ML Model)
   - Feature engineering
   - Model training
   - Performance metrics

4. **`fuzzy_explainer.py`** (Interpretability)
   - Fuzzy logic reasoning
   - Linguistic categorization
   - Natural language generation

5. **`reason_extractor.py`** (Market Analysis)
   - Market pattern detection
   - Driver identification
   - Contextual insights

### Data Flow

```
Raw Data (CSV/API)
    ↓
Data Validation
    ↓
Feature Engineering (predictor.py)
    ↓
Model Training
    ↓
Prediction Generation
    ↓
Dual Explanation
├─→ Numerical (metrics, importance)
└─→ Linguistic (fuzzy, market context)
    ↓
UI Visualization (app.py)
```

## 📦 Dependencies

### Adding New Dependencies

1. Verify necessity and alternatives
2. Add to `pyproject.toml` and `requirements.txt`
3. Update version pins in both files
4. Test with clean environment
5. Document in PR

### Dependency Management

- Keep dependencies minimal
- Pin versions for reproducibility
- Regular security updates

## 🚢 Release Process

(For maintainers)

1. Update version numbers
2. Update CHANGELOG
3. Tag release: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. Create GitHub release with notes

## ❓ Questions?

- Check README for usage questions
- Review existing issues/PRs
- Open a discussion issue
- Contact maintainers

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to making energy markets more explainable! 🚀
