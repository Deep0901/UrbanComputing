"""
Unit tests for the EnergyPricePredictor module.

These tests verify the core functionality of the machine learning pipeline
including feature engineering, model training, and metrics calculation.
"""

import pytest
import pandas as pd
import numpy as np
from app.predictor import EnergyPricePredictor


class TestEnergyPricePredictorInitialization:
    """Test predictor initialization."""
    
    def test_model_initializes_correctly(self):
        """Test that predictor initializes with correct default values."""
        predictor = EnergyPricePredictor()
        
        assert not predictor.is_trained
        assert len(predictor.feature_names) == 0
        assert predictor.X_train is None
        assert predictor.X_test is None
        assert predictor.predictions_train is None
        assert predictor.predictions_test is None


class TestFeatureEngineering:
    """Test feature engineering functionality."""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create sample energy data for testing."""
        dates = pd.date_range('2024-01-01', periods=48, freq='H')
        return pd.DataFrame({
            'datetime': dates,
            'energy_consumption': np.random.uniform(400, 600, 48),
            'price': np.random.uniform(50, 100, 48)
        })
    
    def test_feature_creation(self, sample_dataframe):
        """Test that features are created correctly."""
        predictor = EnergyPricePredictor()
        features = predictor.create_features(sample_dataframe)
        
        # Check that expected features exist
        expected_features = [
            'hour', 'day_of_week', 'month', 'day_of_month',
            'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos',
            'month_sin', 'month_cos', 'is_weekend', 'is_peak_hour',
            'consumption', 'consumption_squared', 'consumption_log'
        ]
        
        for feature in expected_features:
            assert feature in features.columns, f"Missing feature: {feature}"
    
    def test_feature_dimensions_match_input(self, sample_dataframe):
        """Test that feature engineering doesn't change number of rows."""
        predictor = EnergyPricePredictor()
        features = predictor.create_features(sample_dataframe)
        
        assert len(features) == len(sample_dataframe)
    
    def test_datetime_parsing(self):
        """Test that datetime column is properly parsed."""
        df = pd.DataFrame({
            'datetime': ['2024-01-01 00:00', '2024-01-01 01:00'],
            'energy_consumption': [450, 460],
            'price': [65, 67]
        })
        
        predictor = EnergyPricePredictor()
        features = predictor.create_features(df)
        
        assert pd.api.types.is_datetime64_any_dtype(features['datetime'])
    
    def test_cyclical_encoding_bounds(self, sample_dataframe):
        """Test that cyclical encoding produces valid sin/cos values."""
        predictor = EnergyPricePredictor()
        features = predictor.create_features(sample_dataframe)
        
        # Sin and cos should be bounded between -1 and 1
        for col in ['hour_sin', 'hour_cos', 'dow_sin', 'dow_cos', 'month_sin', 'month_cos']:
            assert (features[col] >= -1.0).all(), f"{col} has values < -1"
            assert (features[col] <= 1.0).all(), f"{col} has values > 1"


class TestModelTraining:
    """Test model training functionality."""
    
    @pytest.fixture
    def training_data(self):
        """Create realistic training data."""
        np.random.seed(42)
        dates = pd.date_range('2023-06-01', periods=720, freq='H')  # 30 days
        
        # Create realistic patterns
        hours = np.array([d.hour for d in dates])
        base_price = 70 + 15 * np.sin((hours - 8) * np.pi / 12)  # Daily peak around 8 AM
        price = base_price + np.random.normal(0, 5, len(dates))
        
        consumption = 500 + 100 * np.sin((hours - 6) * np.pi / 12) + np.random.normal(0, 30, len(dates))
        
        return pd.DataFrame({
            'datetime': dates,
            'energy_consumption': consumption,
            'price': price
        })
    
    def test_model_trains_successfully(self, training_data):
        """Test that model trains without errors."""
        predictor = EnergyPricePredictor()
        result = predictor.train(training_data)
        
        assert predictor.is_trained
        assert result is predictor  # Test chaining
    
    def test_train_test_split_correct(self, training_data):
        """Test that data is split correctly."""
        predictor = EnergyPricePredictor()
        predictor.train(training_data, test_size=0.2)
        
        total_samples = len(predictor.X_train) + len(predictor.X_test)
        assert total_samples == len(training_data)
        assert len(predictor.X_test) == pytest.approx(0.2 * len(training_data), abs=1)
    
    def test_feature_names_set_after_training(self, training_data):
        """Test that feature names are properly set."""
        predictor = EnergyPricePredictor()
        predictor.train(training_data)
        
        assert len(predictor.feature_names) > 0
        assert 'hour_sin' in predictor.feature_names


class TestModelMetrics:
    """Test model performance metrics."""
    
    @pytest.fixture
    def trained_predictor(self):
        """Create and train a predictor."""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=240, freq='H')
        df = pd.DataFrame({
            'datetime': dates,
            'energy_consumption': np.random.uniform(400, 600, 240),
            'price': np.random.uniform(50, 100, 240)
        })
        
        predictor = EnergyPricePredictor()
        predictor.train(df)
        return predictor
    
    def test_metrics_structure(self, trained_predictor):
        """Test that metrics return correct structure."""
        metrics = trained_predictor.get_metrics()
        
        assert 'train' in metrics
        assert 'test' in metrics
        assert 'mae' in metrics['train']
        assert 'rmse' in metrics['train']
        assert 'r2' in metrics['train']
    
    def test_metrics_reasonable_values(self, trained_predictor):
        """Test that metrics have reasonable values."""
        metrics = trained_predictor.get_metrics()
        
        # R² should be between -∞ and 1, typically 0-1 for good models
        assert metrics['train']['r2'] <= 1.0
        assert metrics['test']['r2'] <= 1.0
        
        # MAE and RMSE should be positive
        assert metrics['train']['mae'] >= 0
        assert metrics['train']['rmse'] >= 0
    
    def test_metrics_none_before_training(self):
        """Test that metrics return None before training."""
        predictor = EnergyPricePredictor()
        metrics = predictor.get_metrics()
        
        assert metrics is None


class TestFeatureImportance:
    """Test feature importance calculations."""
    
    @pytest.fixture
    def trained_predictor(self):
        """Create and train a predictor."""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=240, freq='H')
        df = pd.DataFrame({
            'datetime': dates,
            'energy_consumption': np.random.uniform(400, 600, 240),
            'price': np.random.uniform(50, 100, 240)
        })
        
        predictor = EnergyPricePredictor()
        predictor.train(df)
        return predictor
    
    def test_feature_importance_structure(self, trained_predictor):
        """Test feature importance DataFrame structure."""
        importance = trained_predictor.get_feature_importance()
        
        assert 'feature' in importance.columns
        assert 'coefficient' in importance.columns
        assert 'abs_coefficient' in importance.columns
        assert len(importance) == len(trained_predictor.feature_names)
    
    def test_feature_importance_sorted(self, trained_predictor):
        """Test that features are sorted by importance."""
        importance = trained_predictor.get_feature_importance()
        
        # Check that abs_coefficient is in descending order
        abs_coefs = importance['abs_coefficient'].values
        assert np.all(abs_coefs[:-1] >= abs_coefs[1:])
    
    def test_feature_importance_none_before_training(self):
        """Test that importance returns None before training."""
        predictor = EnergyPricePredictor()
        importance = predictor.get_feature_importance()
        
        assert importance is None


class TestErrorDistribution:
    """Test error distribution calculations."""
    
    @pytest.fixture
    def trained_predictor(self):
        """Create and train a predictor."""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=240, freq='H')
        df = pd.DataFrame({
            'datetime': dates,
            'energy_consumption': np.random.uniform(400, 600, 240),
            'price': np.random.uniform(50, 100, 240)
        })
        
        predictor = EnergyPricePredictor()
        predictor.train(df)
        return predictor
    
    def test_error_distribution_structure(self, trained_predictor):
        """Test error distribution dictionary structure."""
        errors = trained_predictor.get_error_distribution()
        
        expected_keys = [
            'mean_error', 'std_error', 'min_error', 'max_error',
            'median_error', 'q25_error', 'q75_error'
        ]
        
        for key in expected_keys:
            assert key in errors
    
    def test_error_distribution_ordering(self, trained_predictor):
        """Test that error percentiles are in correct order."""
        errors = trained_predictor.get_error_distribution()
        
        assert errors['min_error'] <= errors['q25_error']
        assert errors['q25_error'] <= errors['median_error']
        assert errors['median_error'] <= errors['q75_error']
        assert errors['q75_error'] <= errors['max_error']


class TestPredictions:
    """Test prediction functionality."""
    
    @pytest.fixture
    def trained_predictor(self):
        """Create and train a predictor."""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=240, freq='H')
        df = pd.DataFrame({
            'datetime': dates,
            'energy_consumption': np.random.uniform(400, 600, 240),
            'price': np.random.uniform(50, 100, 240)
        })
        
        predictor = EnergyPricePredictor()
        predictor.train(df)
        return predictor
    
    def test_get_prediction_samples(self, trained_predictor):
        """Test getting prediction samples."""
        samples = trained_predictor.get_prediction_samples(n_samples=10)
        
        assert len(samples) <= 10
        assert 'actual' in samples.columns
        assert 'predicted' in samples.columns
        assert 'error' in samples.columns
    
    def test_predict_on_new_data(self, trained_predictor):
        """Test making predictions on new data."""
        new_data = pd.DataFrame({
            'datetime': pd.date_range('2024-02-01', periods=24, freq='H'),
            'energy_consumption': np.random.uniform(400, 600, 24),
            'price': np.random.uniform(50, 100, 24)
        })
        
        predictions = trained_predictor.predict(new_data)
        
        assert len(predictions) == len(new_data)
        assert np.all(np.isfinite(predictions))
    
    def test_predict_before_training_raises_error(self):
        """Test that predicting before training raises error."""
        predictor = EnergyPricePredictor()
        
        df = pd.DataFrame({
            'datetime': pd.date_range('2024-01-01', periods=10, freq='H'),
            'energy_consumption': [450] * 10,
            'price': [65] * 10
        })
        
        with pytest.raises(ValueError, match="Model must be trained"):
            predictor.predict(df)


class TestModelSummary:
    """Test model summary functionality."""
    
    @pytest.fixture
    def trained_predictor(self):
        """Create and train a predictor."""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=240, freq='H')
        df = pd.DataFrame({
            'datetime': dates,
            'energy_consumption': np.random.uniform(400, 600, 240),
            'price': np.random.uniform(50, 100, 240)
        })
        
        predictor = EnergyPricePredictor()
        predictor.train(df)
        return predictor
    
    def test_model_summary_completeness(self, trained_predictor):
        """Test that summary contains all expected components."""
        summary = trained_predictor.get_model_summary()
        
        expected_keys = [
            'metrics', 'feature_importance', 'prediction_samples',
            'error_distribution', 'intercept', 'n_features',
            'n_train_samples', 'n_test_samples'
        ]
        
        for key in expected_keys:
            assert key in summary, f"Missing key in summary: {key}"
    
    def test_model_summary_none_before_training(self):
        """Test that summary returns None before training."""
        predictor = EnergyPricePredictor()
        summary = predictor.get_model_summary()
        
        assert summary is None


class TestIntegration:
    """Integration tests for complete workflow."""
    
    def test_complete_workflow(self):
        """Test complete pipeline from data to predictions."""
        # Setup
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=240, freq='H')
        df = pd.DataFrame({
            'datetime': dates,
            'energy_consumption': np.random.uniform(400, 600, 240),
            'price': np.random.uniform(50, 100, 240)
        })
        
        # Train
        predictor = EnergyPricePredictor()
        predictor.train(df)
        
        # Verify training
        assert predictor.is_trained
        
        # Get metrics
        metrics = predictor.get_metrics()
        assert metrics is not None
        
        # Get importance
        importance = predictor.get_feature_importance()
        assert importance is not None
        
        # Get samples
        samples = predictor.get_prediction_samples()
        assert samples is not None
        
        # Make predictions
        new_df = pd.DataFrame({
            'datetime': pd.date_range('2024-03-01', periods=24, freq='H'),
            'energy_consumption': [500] * 24,
            'price': [70] * 24
        })
        predictions = predictor.predict(new_df)
        assert len(predictions) == 24


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
