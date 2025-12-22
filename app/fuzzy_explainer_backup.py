import numpy as np
import pandas as pd
import skfuzzy as fuzz
from skfuzzy import control as ctrl

class FuzzyExplainer:
    """
    Fuzzy-based linguistic reasoning engine for energy price explanations.
    Translates numerical values into natural language using fuzzy logic.
    """
    
    def __init__(self):
        self.price_categories = {}
        self.consumption_categories = {}
        self.error_categories = {}
        
    def _categorize_value(self, value, thresholds):
        """
        Categorize a value based on thresholds.
        
        Args:
            value: Numerical value
            thresholds: Dict with 'low', 'moderate', 'high' thresholds
        
        Returns:
            String category: 'very_low', 'low', 'moderate', 'high', 'very_high'
        """
        if value < thresholds['low']:
            return 'very_low'
        elif value < thresholds['moderate_low']:
            return 'low'
        elif value < thresholds['moderate_high']:
            return 'moderate'
        elif value < thresholds['high']:
            return 'high'
        else:
            return 'very_high'
    
    def _get_linguistic_term(self, category):
        """
        Convert category to linguistic term.
        """
        terms = {
            'very_low': 'very low',
            'low': 'low',
            'moderate': 'moderate',
            'high': 'high',
            'very_high': 'very high'
        }
        return terms.get(category, 'moderate')
    
    def _get_trend_term(self, values):
        """
        Determine trend from a series of values.
        
        Returns:
            Linguistic description of trend
        """
        if len(values) < 2:
            return 'stable'
        
        recent = values[-5:] if len(values) >= 5 else values
        
        # Calculate simple linear trend
        x = np.arange(len(recent))
        coeffs = np.polyfit(x, recent, 1)
        slope = coeffs[0]
        
        # Normalize slope relative to mean
        mean_val = np.mean(recent)
        if mean_val > 0:
            relative_slope = (slope / mean_val) * 100
        else:
            relative_slope = 0
        
        if relative_slope > 2:
            return 'rising rapidly'
        elif relative_slope > 0.5:
            return 'rising gradually'
        elif relative_slope > -0.5:
            return 'stable'
        elif relative_slope > -2:
            return 'declining gradually'
        else:
            return 'declining rapidly'
    
    def analyze_data(self, df, model_metrics=None):
        """
        Analyze data and create fuzzy categorizations.
        
        Args:
            df: DataFrame with energy_consumption and price columns
            model_metrics: Optional model metrics for error analysis
        
        Returns:
            Dictionary with fuzzy analysis results
        """
        analysis = {
            'price': {},
            'consumption': {},
            'patterns': {},
            'model_performance': {}
        }
        
        # Price analysis
        prices = df['price'].values
        price_mean = np.mean(prices)
        price_std = np.std(prices)
        price_min = np.min(prices)
        price_max = np.max(prices)
        
        price_thresholds = {
            'low': price_mean - price_std,
            'moderate_low': price_mean - 0.3 * price_std,
            'moderate_high': price_mean + 0.3 * price_std,
            'high': price_mean + price_std
        }
        
        analysis['price']['current'] = float(prices[-1])
        analysis['price']['mean'] = float(price_mean)
        analysis['price']['category'] = self._categorize_value(prices[-1], price_thresholds)
        analysis['price']['linguistic'] = self._get_linguistic_term(analysis['price']['category'])
        analysis['price']['trend'] = self._get_trend_term(prices)
        analysis['price']['volatility'] = 'high' if price_std / price_mean > 0.15 else 'moderate' if price_std / price_mean > 0.08 else 'low'
        
        # Consumption analysis
        consumption = df['energy_consumption'].values
        cons_mean = np.mean(consumption)
        cons_std = np.std(consumption)
        
        cons_thresholds = {
            'low': cons_mean - cons_std,
            'moderate_low': cons_mean - 0.3 * cons_std,
            'moderate_high': cons_mean + 0.3 * cons_std,
            'high': cons_mean + cons_std
        }
        
        analysis['consumption']['current'] = float(consumption[-1])
        analysis['consumption']['mean'] = float(cons_mean)
        analysis['consumption']['category'] = self._categorize_value(consumption[-1], cons_thresholds)
        analysis['consumption']['linguistic'] = self._get_linguistic_term(analysis['consumption']['category'])
        analysis['consumption']['trend'] = self._get_trend_term(consumption)
        
        # Pattern detection
        if 'datetime' in df.columns:
            df_temp = df.copy()
            if not pd.api.types.is_datetime64_any_dtype(df_temp['datetime']):
                df_temp['datetime'] = pd.to_datetime(df_temp['datetime'])
            
            df_temp['hour'] = df_temp['datetime'].dt.hour
            peak_hours = df_temp[df_temp['hour'].isin([7, 8, 9, 18, 19, 20, 21])]
            off_peak_hours = df_temp[~df_temp['hour'].isin([7, 8, 9, 18, 19, 20, 21])]
            
            if len(peak_hours) > 0 and len(off_peak_hours) > 0:
                peak_price_mean = peak_hours['price'].mean()
                off_peak_price_mean = off_peak_hours['price'].mean()
                price_diff_pct = ((peak_price_mean - off_peak_price_mean) / off_peak_price_mean) * 100
                
                analysis['patterns']['peak_premium'] = float(price_diff_pct)
                analysis['patterns']['peak_pricing'] = 'significant' if price_diff_pct > 15 else 'moderate' if price_diff_pct > 5 else 'minimal'
        
        # Model performance analysis
        if model_metrics:
            test_metrics = model_metrics.get('test', {})
            r2 = test_metrics.get('r2', 0)
            mae = test_metrics.get('mae', 0)
            
            # Categorize model performance
            if r2 > 0.9:
                performance = 'excellent'
            elif r2 > 0.75:
                performance = 'good'
            elif r2 > 0.5:
                performance = 'moderate'
            else:
                performance = 'poor'
            
            analysis['model_performance']['r2'] = float(r2)
            analysis['model_performance']['mae'] = float(mae)
            analysis['model_performance']['category'] = performance
            
            # Error pattern analysis
            mae_rel = (mae / price_mean) * 100 if price_mean > 0 else 0
            
            if mae_rel < 5:
                error_desc = 'minimal deviations'
            elif mae_rel < 10:
                error_desc = 'small deviations'
            elif mae_rel < 20:
                error_desc = 'moderate deviations'
            else:
                error_desc = 'significant deviations'
            
            analysis['model_performance']['error_description'] = error_desc
            analysis['model_performance']['mae_percentage'] = float(mae_rel)
        
        return analysis
    
    def generate_explanation(self, analysis, include_context=True):
        """
        Generate natural language explanation based on fuzzy analysis.
        
        Args:
            analysis: Analysis results from analyze_data()
            include_context: Whether to include contextual information
        
        Returns:
            String with natural language explanation
        """
        explanations = []
        
        # Price explanation
        price_ling = analysis['price']['linguistic']
        price_trend = analysis['price']['trend']
        price_vol = analysis['price']['volatility']
        
        explanations.append(
            f"⚡ **Energy prices are currently {price_ling}** "
            f"(€{analysis['price']['current']:.2f}/MWh vs mean €{analysis['price']['mean']:.2f}/MWh)"
        )
        
        if price_trend != 'stable':
            explanations.append(f"📈 Prices are **{price_trend}** based on recent data")
        
        if price_vol == 'high':
            explanations.append(f"⚠️ Market volatility is **high**, indicating unstable pricing conditions")
        
        # Consumption explanation
        cons_ling = analysis['consumption']['linguistic']
        cons_trend = analysis['consumption']['trend']
        
        explanations.append(
            f"🔌 **Energy consumption is {cons_ling}** "
            f"({analysis['consumption']['current']:.2f} MW vs mean {analysis['consumption']['mean']:.2f} MW)"
        )
        
        if cons_trend != 'stable':
            explanations.append(f"📊 Demand is **{cons_trend}** in recent hours")
        
        # Fuzzy rule-based reasoning with realistic energy market logic
        if analysis['price']['category'] == 'very_high' and analysis['consumption']['category'] in ['high', 'very_high']:
            explanations.append(
                "🔥 **Peak demand period**: High consumption combined with elevated prices suggests peak hours "
                "(morning/evening rush) or extreme weather conditions driving up demand for heating/cooling"
            )
        elif analysis['price']['category'] == 'very_low' and analysis['consumption']['category'] == 'very_low':
            explanations.append(
                "🌙 **Off-peak/baseload period**: Low demand (1-5 AM) with abundant renewable generation "
                "(wind/solar) and nuclear baseload creating surplus capacity and minimal pricing"
            )
        elif analysis['price']['category'] in ['high', 'very_high'] and analysis['consumption']['category'] in ['low', 'very_low']:
            explanations.append(
                "⚡ **Supply constraints or fuel scarcity**: Elevated prices despite moderate demand suggests "
                "generation outages, transmission congestion, or high fossil fuel costs impacting wholesale prices"
            )
        elif analysis['price']['category'] in ['low', 'very_low'] and analysis['consumption']['category'] in ['high', 'very_high']:
            explanations.append(
                "🌱 **Renewable energy surplus**: High demand met by strong renewable generation "
                "(wind/solar) keeping prices low despite elevated consumption levels"
            )
        
        # Pattern insights with realistic energy context
        if 'patterns' in analysis and 'peak_pricing' in analysis['patterns']:
            peak_premium = analysis['patterns']['peak_premium']
            peak_cat = analysis['patterns']['peak_pricing']
            
            if peak_cat == 'significant':
                explanations.append(
                    f"🕐 **Time-of-use pricing effect is {peak_cat}**: "
                    f"+{peak_premium:.1f}% during peak hours (7-9 AM & 6-9 PM) reflects higher "
                    f"generation costs from peaker plants and grid capacity constraints"
                )
            elif peak_cat == 'moderate':
                explanations.append(
                    f"🕐 **Moderate peak pricing pattern**: "
                    f"+{peak_premium:.1f}% during peak hours indicates balanced supply-demand "
                    f"with adequate generation reserves"
                )
        
        # Model performance explanation with energy forecasting context
        if 'model_performance' in analysis and analysis['model_performance']:
            perf = analysis['model_performance']
            r2 = perf.get('r2', 0)
            error_desc = perf.get('error_description', 'unknown')
            
            explanations.append(
                f"🤖 **Forecasting accuracy is {perf['category']}** "
                f"(R² = {r2:.3f}) with {error_desc} from actual market prices"
            )
            
            if perf['category'] in ['good', 'excellent']:
                explanations.append(
                    "✅ Model reliably captures market dynamics including demand cycles, "
                    "seasonal patterns, and price volatility for day-ahead predictions"
                )
            elif perf['category'] == 'moderate':
                explanations.append(
                    "⚠️ Model shows moderate accuracy - market volatility or unexpected events "
                    "(outages, weather extremes) may affect prediction reliability"
                )
        
        return "\n\n".join(explanations)
    
    def generate_fuzzy_rules_summary(self):
        """
        Generate a summary of fuzzy rules used in the system.
        
        Returns:
            String describing the fuzzy logic rules
        """
        rules = [
            "**Fuzzy Inference Rules:**",
            "",
            "1️⃣ IF price is HIGH AND consumption is HIGH → Peak demand period",
            "2️⃣ IF price is LOW AND consumption is LOW → Off-peak period",
            "3️⃣ IF price is HIGH AND consumption is LOW → Supply constraint",
            "4️⃣ IF price is RISING AND demand is RISING → Increasing scarcity",
            "5️⃣ IF price is FALLING AND demand is FALLING → Surplus capacity",
            "6️⃣ IF volatility is HIGH → Unstable market conditions",
            "7️⃣ IF model error is LOW → Reliable predictions",
            "8️⃣ IF peak premium is HIGH → Strong time-of-use pricing"
        ]
        
        return "\n".join(rules)
    
    def get_color_code(self, category):
        """
        Get color code for linguistic category (for UI styling).
        
        Returns:
            Color name or hex code
        """
        colors = {
            'very_low': 'green',
            'low': 'lightgreen',
            'moderate': 'orange',
            'high': 'darkorange',
            'very_high': 'red'
        }
        return colors.get(category, 'gray')
