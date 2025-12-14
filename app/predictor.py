import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.model_selection import train_test_split
from datetime import datetime
from typing import Dict, Optional, Tuple, Any
from app.logger_utils import logger, ModelTrainingError


class EnergyPricePredictor:
    """
    Linear Regression-based predictor for energy prices with automated feature engineering.
    
    This class implements a complete ML pipeline including:
    - Automated feature engineering (temporal + consumption features)
    - Cyclical encoding for time-based features (hour, day of week, month)
    - Train/test split and model fitting
    - Comprehensive performance metrics
    - Feature importance analysis
    
    Attributes:
        model (LinearRegression): Trained scikit-learn LinearRegression model
        feature_names (list): Names of engineered features
        is_trained (bool): Whether the model has been trained
        X_train (np.ndarray): Training feature set
        X_test (np.ndarray): Test feature set
        y_train (np.ndarray): Training target values
        y_test (np.ndarray): Test target values
        predictions_train (np.ndarray): Predictions on training set
        predictions_test (np.ndarray): Predictions on test set
    
    Example:
        >>> predictor = EnergyPricePredictor()
        >>> predictor.train(df)
        >>> metrics = predictor.get_metrics()
        >>> feature_importance = predictor.get_feature_importance()
    """
    
    def __init__(self):
        """Initialize the energy price predictor with empty model."""
        self.model = LinearRegression()
        self.feature_names: list = []
        self.is_trained: bool = False
        self.X_train: Optional[np.ndarray] = None
        self.X_test: Optional[np.ndarray] = None
        self.y_train: Optional[np.ndarray] = None
        self.y_test: Optional[np.ndarray] = None
        self.predictions_train: Optional[np.ndarray] = None
        self.predictions_test: Optional[np.ndarray] = None
        
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create automated features from datetime and energy consumption.
        
        Implements comprehensive feature engineering including:
        - Temporal features: hour, day_of_week, month, day_of_month
        - Cyclical encoding: sin/cos transformations for periodic features
        - Time indicators: weekend, peak hours
        - Consumption transformations: linear, squared, log-transformed
        
        Args:
            df (pd.DataFrame): Input DataFrame with 'datetime' and 'energy_consumption' columns
        
        Returns:
            pd.DataFrame: DataFrame with additional engineered features
            
        Raises:
            KeyError: If required columns are missing
        
        Example:
            >>> df = pd.DataFrame({'datetime': [...], 'energy_consumption': [...]})
            >>> df_features = predictor.create_features(df)
            >>> print(df_features.columns)
        """
        df = df.copy()
        
        # Ensure datetime is parsed
        if not pd.api.types.is_datetime64_any_dtype(df['datetime']):
            df['datetime'] = pd.to_datetime(df['datetime'])
        
        # Extract temporal features
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week'] = df['datetime'].dt.dayofweek
        df['month'] = df['datetime'].dt.month
        df['day_of_month'] = df['datetime'].dt.day
        
        # Cyclical encoding for hour (0-23)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        # Cyclical encoding for day of week (0-6)
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Cyclical encoding for month (1-12)
        df['month_sin'] = np.sin(2 * np.pi * (df['month'] - 1) / 12)
        df['month_cos'] = np.cos(2 * np.pi * (df['month'] - 1) / 12)
        
        # Is weekend
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Is peak hour (7-9 AM, 6-9 PM)
        df['is_peak_hour'] = (((df['hour'] >= 7) & (df['hour'] <= 9)) | 
                              ((df['hour'] >= 18) & (df['hour'] <= 21))).astype(int)
        
        # Off-peak hours (late night/early morning: 1-5 AM)
        df['is_offpeak'] = ((df['hour'] >= 1) & (df['hour'] <= 5)).astype(int)
        
        # Business hours (9 AM - 5 PM on weekdays)
        df['is_business_hours'] = (
            (df['hour'] >= 9) & (df['hour'] <= 17) & (df['day_of_week'] < 5)
        ).astype(int)
        
        # Season indicators (Northern Hemisphere)
        df['is_winter'] = df['month'].isin([12, 1, 2]).astype(int)
        df['is_summer'] = df['month'].isin([6, 7, 8]).astype(int)
        df['is_spring'] = df['month'].isin([3, 4, 5]).astype(int)
        df['is_fall'] = df['month'].isin([9, 10, 11]).astype(int)
        
        # Energy consumption features
        if 'energy_consumption' in df.columns:
            df['consumption'] = df['energy_consumption']
            df['consumption_squared'] = df['energy_consumption'] ** 2
            df['consumption_log'] = np.log1p(df['energy_consumption'])
            
            # Rolling statistics (if enough data)
            if len(df) >= 24:
                df['consumption_rolling_mean_24h'] = df['energy_consumption'].rolling(
                    window=24, min_periods=1
                ).mean()
                df['consumption_rolling_std_24h'] = df['energy_consumption'].rolling(
                    window=24, min_periods=1
                ).std().fillna(0)
            
            # Lag features (previous hour consumption)
            df['consumption_lag_1h'] = df['energy_consumption'].shift(1).fillna(
                df['energy_consumption'].mean()
            )
            df['consumption_lag_24h'] = df['energy_consumption'].shift(24).fillna(
                df['energy_consumption'].mean()
            )
            
            # Price-to-demand ratio (if price exists)
            if 'price' in df.columns:
                df['price_demand_ratio'] = df['price'] / (df['energy_consumption'] + 1)
        
        return df
    
    def train(self, df: pd.DataFrame, target_column: str = 'price', 
              test_size: float = 0.2, random_state: int = 42) -> 'EnergyPricePredictor':
        """
        Train the linear regression model with automated feature engineering.
        
        Performs the following steps:
        1. Creates automated features from the input DataFrame
        2. Splits data into training and test sets
        3. Fits the LinearRegression model
        4. Generates predictions for both sets
        
        Args:
            df (pd.DataFrame): Input DataFrame with 'datetime', 'energy_consumption', 
                             and 'price' columns
            target_column (str): Name of target column (default: 'price')
            test_size (float): Fraction of data for testing (default: 0.2)
            random_state (int): Random seed for reproducibility (default: 42)
        
        Returns:
            EnergyPricePredictor: Self for method chaining
        
        Raises:
            ModelTrainingError: If training fails
            ValueError: If required columns are missing
            
        Example:
            >>> predictor = EnergyPricePredictor()
            >>> predictor.train(df)
            >>> print(predictor.is_trained)
            True
        """
        try:
            logger.info(f"Starting model training with {len(df)} samples")
            
            # Create features
            df_features = self.create_features(df)
            
            # Select feature columns (exclude datetime, original target, and intermediate columns)
            exclude_cols = ['datetime', 'price', 'energy_consumption', 'hour', 'day_of_week', 'month', 'day_of_month']
            feature_cols = [col for col in df_features.columns if col not in exclude_cols]
            
            self.feature_names = feature_cols
            logger.info(f"Created {len(feature_cols)} features: {feature_cols}")
            
            # Prepare X and y
            X = df_features[feature_cols].values
            y = df_features[target_column].values
            
            # Split data
            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
            
            logger.info(f"Split data: {len(self.X_train)} train, {len(self.X_test)} test")
            
            # Train model
            self.model.fit(self.X_train, self.y_train)
            
            # Generate predictions
            self.predictions_train = self.model.predict(self.X_train)
            self.predictions_test = self.model.predict(self.X_test)
            
            self.is_trained = True
            logger.info("Model training completed successfully")
            
            return self
            
        except Exception as e:
            logger.error(f"Model training failed: {str(e)}", exc_info=True)
            raise ModelTrainingError(f"Failed to train model: {str(e)}")
    
    def get_metrics(self) -> Optional[Dict[str, Dict[str, float]]]:
        """
        Calculate and return model performance metrics.
        
        Computes the following metrics for both training and test sets:
        - Mean Absolute Error (MAE)
        - Root Mean Squared Error (RMSE)
        - R² Score (coefficient of determination)
        
        Returns:
            Dict: Dictionary with train and test metrics, or None if not trained
            Format: {
                'train': {'mae': float, 'rmse': float, 'r2': float},
                'test': {'mae': float, 'rmse': float, 'r2': float}
            }
        
        Example:
            >>> metrics = predictor.get_metrics()
            >>> print(f"Test R²: {metrics['test']['r2']:.4f}")
        """
        if not self.is_trained:
            logger.warning("Cannot compute metrics: model not trained")
            return None
        
        # Training metrics
        train_mae = mean_absolute_error(self.y_train, self.predictions_train)
        train_rmse = np.sqrt(mean_squared_error(self.y_train, self.predictions_train))
        train_r2 = r2_score(self.y_train, self.predictions_train)
        
        # Test metrics
        test_mae = mean_absolute_error(self.y_test, self.predictions_test)
        test_rmse = np.sqrt(mean_squared_error(self.y_test, self.predictions_test))
        test_r2 = r2_score(self.y_test, self.predictions_test)
        
        metrics = {
            'train': {
                'mae': train_mae,
                'rmse': train_rmse,
                'r2': train_r2
            },
            'test': {
                'mae': test_mae,
                'rmse': test_rmse,
                'r2': test_r2
            }
        }
        
        logger.info(f"Metrics - Train R²: {train_r2:.4f}, Test R²: {test_r2:.4f}")
        return metrics
    
    def get_feature_importance(self) -> Optional[pd.DataFrame]:
        """
        Get feature importance based on absolute coefficient values.
        
        Returns a DataFrame sorted by absolute coefficient magnitude,
        representing the relative importance of each feature.
        
        Returns:
            pd.DataFrame: DataFrame with columns:
                - 'feature': Feature name
                - 'coefficient': Linear regression coefficient
                - 'abs_coefficient': Absolute value of coefficient
                Sorted by absolute coefficient (descending)
            None if model not trained
        
        Example:
            >>> importance = predictor.get_feature_importance()
            >>> print(importance.head(5))
        """
        if not self.is_trained:
            logger.warning("Cannot compute feature importance: model not trained")
            return None
        
        coefficients = self.model.coef_
        importance = pd.DataFrame({
            'feature': self.feature_names,
            'coefficient': coefficients,
            'abs_coefficient': np.abs(coefficients)
        }).sort_values('abs_coefficient', ascending=False)
        
        logger.info(f"Top 3 features: {', '.join(importance.head(3)['feature'].tolist())}")
        return importance
    
    def get_prediction_samples(self, n_samples: int = 10) -> Optional[pd.DataFrame]:
        """
        Get sample predictions vs actual values from test set.
        
        Args:
            n_samples (int): Number of samples to return (default: 10)
        
        Returns:
            pd.DataFrame: DataFrame with columns:
                - 'actual': Actual values from test set
                - 'predicted': Model predictions
                - 'error': Prediction error (actual - predicted)
            None if model not trained
        
        Example:
            >>> samples = predictor.get_prediction_samples(5)
            >>> print(samples)
        """
        if not self.is_trained:
            logger.warning("Cannot get prediction samples: model not trained")
            return None
        
        # Use test set
        indices = np.random.choice(len(self.y_test), min(n_samples, len(self.y_test)), replace=False)
        
        samples = pd.DataFrame({
            'actual': self.y_test[indices],
            'predicted': self.predictions_test[indices],
            'error': self.y_test[indices] - self.predictions_test[indices]
        })
        
        return samples
    
    def get_error_distribution(self) -> Optional[Dict[str, float]]:
        """
        Get error distribution statistics from test set predictions.
        
        Computes various percentiles and statistics of prediction errors.
        
        Returns:
            Dict: Dictionary containing:
                - 'mean_error': Mean of prediction errors
                - 'std_error': Standard deviation
                - 'min_error': Minimum error
                - 'max_error': Maximum error
                - 'median_error': Median error
                - 'q25_error': 25th percentile
                - 'q75_error': 75th percentile
            None if model not trained
        
        Example:
            >>> errors = predictor.get_error_distribution()
            >>> print(f"Mean error: {errors['mean_error']:.3f}")
        """
        if not self.is_trained:
            logger.warning("Cannot compute error distribution: model not trained")
            return None
        
        errors = self.y_test - self.predictions_test
        
        return {
            'mean_error': np.mean(errors),
            'std_error': np.std(errors),
            'min_error': np.min(errors),
            'max_error': np.max(errors),
            'median_error': np.median(errors),
            'q25_error': np.percentile(errors, 25),
            'q75_error': np.percentile(errors, 75)
        }
    
    def predict(self, df: pd.DataFrame) -> Optional[np.ndarray]:
        """
        Make predictions on new data.
        
        Args:
            df (pd.DataFrame): Input DataFrame with required columns
        
        Returns:
            np.ndarray: Predicted price values
        
        Raises:
            ValueError: If model not trained
        
        Example:
            >>> predictions = predictor.predict(new_df)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        df_features = self.create_features(df)
        X = df_features[self.feature_names].values
        predictions = self.model.predict(X)
        
        return predictions
    
    def get_model_summary(self) -> Optional[Dict[str, Any]]:
        """
        Get a complete summary of the model for numerical explanation.
        
        Aggregates all model information into a single dictionary.
        
        Returns:
            Dict: Complete model summary including metrics, features, and data info
            None if model not trained
        
        Example:
            >>> summary = predictor.get_model_summary()
            >>> print(summary.keys())
        """
        if not self.is_trained:
            logger.warning("Cannot get model summary: model not trained")
            return None
        
        return {
            'metrics': self.get_metrics(),
            'feature_importance': self.get_feature_importance(),
            'prediction_samples': self.get_prediction_samples(),
            'error_distribution': self.get_error_distribution(),
            'intercept': self.model.intercept_,
            'n_features': len(self.feature_names),
            'n_train_samples': len(self.y_train),
            'n_test_samples': len(self.y_test)
        }
        if not self.is_trained:
            return None
        
        # Training metrics
        train_mae = mean_absolute_error(self.y_train, self.predictions_train)
        train_rmse = np.sqrt(mean_squared_error(self.y_train, self.predictions_train))
        train_r2 = r2_score(self.y_train, self.predictions_train)
        
        # Test metrics
        test_mae = mean_absolute_error(self.y_test, self.predictions_test)
        test_rmse = np.sqrt(mean_squared_error(self.y_test, self.predictions_test))
        test_r2 = r2_score(self.y_test, self.predictions_test)
        
        return {
            'train': {
                'mae': train_mae,
                'rmse': train_rmse,
                'r2': train_r2
            },
            'test': {
                'mae': test_mae,
                'rmse': test_rmse,
                'r2': test_r2
            }
        }
    
    def get_feature_importance(self):
        """
        Get feature importance based on absolute coefficient values.
        """
        if not self.is_trained:
            return None
        
        coefficients = self.model.coef_
        importance = pd.DataFrame({
            'feature': self.feature_names,
            'coefficient': coefficients,
            'abs_coefficient': np.abs(coefficients)
        }).sort_values('abs_coefficient', ascending=False)
        
        return importance
    
    def get_prediction_samples(self, n_samples=10):
        """
        Get sample predictions vs actual values.
        """
        if not self.is_trained:
            return None
        
        # Use test set
        indices = np.random.choice(len(self.y_test), min(n_samples, len(self.y_test)), replace=False)
        
        samples = pd.DataFrame({
            'actual': self.y_test[indices],
            'predicted': self.predictions_test[indices],
            'error': self.y_test[indices] - self.predictions_test[indices]
        })
        
        return samples
    
    def get_error_distribution(self):
        """
        Get error distribution statistics.
        """
        if not self.is_trained:
            return None
        
        errors = self.y_test - self.predictions_test
        
        return {
            'mean_error': np.mean(errors),
            'std_error': np.std(errors),
            'min_error': np.min(errors),
            'max_error': np.max(errors),
            'median_error': np.median(errors),
            'q25_error': np.percentile(errors, 25),
            'q75_error': np.percentile(errors, 75)
        }
    
    def predict(self, df):
        """
        Make predictions on new data.
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        df_features = self.create_features(df)
        X = df_features[self.feature_names].values
        predictions = self.model.predict(X)
        
        return predictions
    
    def get_model_summary(self):
        """
        Get a complete summary of the model for numerical explanation.
        """
        if not self.is_trained:
            return None
        
        return {
            'metrics': self.get_metrics(),
            'feature_importance': self.get_feature_importance(),
            'prediction_samples': self.get_prediction_samples(),
            'error_distribution': self.get_error_distribution(),
            'intercept': self.model.intercept_,
            'n_features': len(self.feature_names),
            'n_train_samples': len(self.y_train),
            'n_test_samples': len(self.y_test)
        }
