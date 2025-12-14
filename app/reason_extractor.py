import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class ReasonExtractor:
    """
    API-based contextual reasoning engine.
    Extracts real market insights from ENTSOE data to explain price fluctuations.
    """
    
    def __init__(self, entsoe_client=None):
        """
        Initialize with optional ENTSOE client.
        
        Args:
            entsoe_client: ENTSOEClient instance (optional)
        """
        self.entsoe_client = entsoe_client
    
    def extract_price_drivers(self, market_context):
        """
        Extract key drivers of price changes from market context.
        
        Args:
            market_context: Dictionary from entsoe_client.get_market_context()
        
        Returns:
            List of identified price drivers with descriptions
        """
        if not market_context.get('data_available', False):
            return []
        
        drivers = []
        
        # Price trend analysis
        if 'trends' in market_context:
            trends = market_context['trends']
            
            if 'price_direction' in trends:
                direction = trends['price_direction']
                change = trends.get('price_change', 0)
                
                if abs(change) > 5:
                    drivers.append({
                        'factor': 'Price Movement',
                        'description': f"Prices are {direction} by €{abs(change):.2f}/MWh",
                        'impact': 'high' if abs(change) > 10 else 'moderate'
                    })
            
            # Demand trend
            if 'load_direction' in trends:
                load_dir = trends['load_direction']
                load_change = trends.get('load_change', 0)
                
                if abs(load_change) > 100:
                    drivers.append({
                        'factor': 'Demand Change',
                        'description': f"Energy demand is {load_dir} ({abs(load_change):.0f} MW shift)",
                        'impact': 'high' if abs(load_change) > 500 else 'moderate'
                    })
        
        # Price level analysis
        if 'price_stats' in market_context:
            price_stats = market_context['price_stats']
            current = price_stats.get('current', 0)
            mean = price_stats.get('mean', 0)
            max_price = price_stats.get('max', 0)
            min_price = price_stats.get('min', 0)
            
            deviation = ((current - mean) / mean * 100) if mean > 0 else 0
            
            if abs(deviation) > 20:
                if deviation > 0:
                    drivers.append({
                        'factor': 'Above-Average Pricing',
                        'description': f"Current price is {abs(deviation):.1f}% above the recent average",
                        'impact': 'high'
                    })
                else:
                    drivers.append({
                        'factor': 'Below-Average Pricing',
                        'description': f"Current price is {abs(deviation):.1f}% below the recent average",
                        'impact': 'high'
                    })
            
            # Price range analysis
            price_range = max_price - min_price
            if price_range > mean * 0.5:
                drivers.append({
                    'factor': 'High Price Volatility',
                    'description': f"Prices vary widely (€{min_price:.2f} - €{max_price:.2f})",
                    'impact': 'moderate'
                })
        
        # Load level analysis
        if 'load_stats' in market_context:
            load_stats = market_context['load_stats']
            current_load = load_stats.get('current', 0)
            mean_load = load_stats.get('mean', 0)
            max_load = load_stats.get('max', 0)
            
            load_ratio = (current_load / mean_load) if mean_load > 0 else 1
            
            if load_ratio > 1.15:
                drivers.append({
                    'factor': 'High Demand Period',
                    'description': f"Consumption is {(load_ratio - 1) * 100:.1f}% above average",
                    'impact': 'high'
                })
            elif load_ratio < 0.85:
                drivers.append({
                    'factor': 'Low Demand Period',
                    'description': f"Consumption is {(1 - load_ratio) * 100:.1f}% below average",
                    'impact': 'moderate'
                })
            
            # Peak capacity check
            capacity_usage = (current_load / max_load * 100) if max_load > 0 else 0
            if capacity_usage > 90:
                drivers.append({
                    'factor': 'Near Peak Capacity',
                    'description': f"System operating at {capacity_usage:.1f}% of recent maximum",
                    'impact': 'high'
                })
        
        return drivers
    
    def generate_market_insight(self, market_context):
        """
        Generate comprehensive market insight narrative.
        
        Args:
            market_context: Dictionary from entsoe_client.get_market_context()
        
        Returns:
            String with market insight narrative
        """
        if not market_context.get('data_available', False):
            error_msg = market_context.get('error', 'Unknown error')
            return f"❌ **Market data unavailable**: {error_msg}"
        
        country = market_context.get('country', 'Unknown')
        insights = []
        
        insights.append(f"## 🌍 Real-Time Market Insights: {country}")
        insights.append("")
        
        # Current conditions
        if 'price_stats' in market_context and 'load_stats' in market_context:
            price = market_context['price_stats'].get('current', 0)
            load = market_context['load_stats'].get('current', 0)
            
            insights.append(f"**Current Conditions:**")
            insights.append(f"- Electricity Price: €{price:.2f}/MWh")
            insights.append(f"- System Load: {load:.0f} MW")
            insights.append("")
        
        # Extract and display price drivers
        drivers = self.extract_price_drivers(market_context)
        
        if drivers:
            insights.append(f"**Key Market Factors:**")
            insights.append("")
            
            for i, driver in enumerate(drivers, 1):
                impact_emoji = "🔴" if driver['impact'] == 'high' else "🟡"
                insights.append(f"{impact_emoji} **{driver['factor']}**: {driver['description']}")
            
            insights.append("")
        
        # Market interpretation
        insights.append(f"**Market Interpretation:**")
        
        # Generate contextual interpretation
        interpretations = self._generate_interpretation(market_context, drivers)
        for interp in interpretations:
            insights.append(f"- {interp}")
        
        return "\n".join(insights)
    
    def _generate_interpretation(self, market_context, drivers):
        """
        Generate contextual interpretations based on drivers.
        
        Returns:
            List of interpretation strings
        """
        interpretations = []
        
        # Check for specific patterns
        high_price = any(d['factor'] in ['Above-Average Pricing', 'High Demand Period'] for d in drivers)
        low_price = any(d['factor'] == 'Below-Average Pricing' for d in drivers)
        high_volatility = any(d['factor'] == 'High Price Volatility' for d in drivers)
        rising_demand = any(d['factor'] == 'Demand Change' and 'increasing' in d['description'] for d in drivers)
        falling_demand = any(d['factor'] == 'Demand Change' and 'decreasing' in d['description'] for d in drivers)
        
        # Generate contextual explanations
        if high_price and rising_demand:
            interpretations.append(
                "Rising demand is pushing prices higher, typical during peak business hours or extreme weather"
            )
        
        if low_price and falling_demand:
            interpretations.append(
                "Lower demand allows prices to drop, often seen during night hours or weekends"
            )
        
        if high_price and not rising_demand:
            interpretations.append(
                "High prices despite stable demand may indicate supply constraints or fuel cost pressures"
            )
        
        if high_volatility:
            interpretations.append(
                "High market volatility suggests rapid changes in supply-demand balance or renewable generation"
            )
        
        # Time-based context
        current_hour = datetime.now().hour
        
        if 7 <= current_hour <= 9:
            interpretations.append(
                "Morning peak hours typically see increased industrial and commercial activity"
            )
        elif 18 <= current_hour <= 21:
            interpretations.append(
                "Evening peak hours feature high residential consumption and continued business operations"
            )
        elif 22 <= current_hour or current_hour <= 6:
            interpretations.append(
                "Night hours generally show lower demand and reduced prices"
            )
        
        # Weekday context
        current_weekday = datetime.now().weekday()
        
        if current_weekday >= 5:
            interpretations.append(
                "Weekend periods typically have lower industrial demand compared to weekdays"
            )
        
        if not interpretations:
            interpretations.append(
                "Market conditions are relatively stable with normal supply-demand balance"
            )
        
        return interpretations
    
    def get_reasoning_summary(self, df, market_context=None):
        """
        Get complete reasoning summary combining data analysis and market context.
        
        Args:
            df: DataFrame with energy data
            market_context: Optional market context from ENTSOE
        
        Returns:
            Dictionary with comprehensive reasoning
        """
        summary = {
            'data_insights': {},
            'market_insights': {},
            'combined_narrative': ''
        }
        
        # Data-driven insights
        if not df.empty:
            recent_prices = df['price'].tail(24).values if len(df) >= 24 else df['price'].values
            recent_consumption = df['energy_consumption'].tail(24).values if len(df) >= 24 else df['energy_consumption'].values
            
            summary['data_insights'] = {
                'price_mean_24h': float(np.mean(recent_prices)),
                'price_std_24h': float(np.std(recent_prices)),
                'consumption_mean_24h': float(np.mean(recent_consumption)),
                'price_trend': 'increasing' if recent_prices[-1] > np.mean(recent_prices) else 'decreasing',
                'consumption_trend': 'increasing' if recent_consumption[-1] > np.mean(recent_consumption) else 'decreasing'
            }
        
        # Market context insights
        if market_context and market_context.get('data_available', False):
            summary['market_insights'] = {
                'country': market_context.get('country', 'Unknown'),
                'drivers': self.extract_price_drivers(market_context),
                'narrative': self.generate_market_insight(market_context)
            }
        
        return summary
    
    def format_for_display(self, reasoning_summary):
        """
        Format reasoning summary for dashboard display.
        
        Args:
            reasoning_summary: Output from get_reasoning_summary()
        
        Returns:
            Formatted string for display
        """
        output = []
        
        if 'market_insights' in reasoning_summary and reasoning_summary['market_insights']:
            output.append(reasoning_summary['market_insights'].get('narrative', ''))
        
        if 'data_insights' in reasoning_summary and reasoning_summary['data_insights']:
            data = reasoning_summary['data_insights']
            output.append("")
            output.append("**Data-Driven Insights:**")
            output.append(f"- 24h Average Price: €{data.get('price_mean_24h', 0):.2f}/MWh")
            output.append(f"- Price Trend: {data.get('price_trend', 'stable').capitalize()}")
            output.append(f"- Demand Trend: {data.get('consumption_trend', 'stable').capitalize()}")
        
        return "\n".join(output) if output else "No reasoning data available"
