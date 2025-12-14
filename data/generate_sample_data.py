import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate 7 days of hourly data
start_date = datetime(2024, 10, 1, 0, 0, 0)
dates = [start_date + timedelta(hours=i) for i in range(168)]

# Set random seed for reproducibility
np.random.seed(42)

# Create realistic energy consumption patterns
consumption = []
for i, date in enumerate(dates):
    hour = date.hour
    day_of_week = date.weekday()
    
    # Base consumption pattern
    base = 50
    
    # Daily pattern (higher during day, lower at night)
    if 6 <= hour <= 22:
        hourly_factor = 1.3 + 0.3 * np.sin((hour - 6) * np.pi / 16)
    else:
        hourly_factor = 0.7
    
    # Weekly pattern (lower on weekends)
    if day_of_week >= 5:  # Weekend
        weekly_factor = 0.85
    else:
        weekly_factor = 1.0
    
    # Add some random noise
    noise = np.random.normal(0, 5)
    
    value = base * hourly_factor * weekly_factor + noise
    consumption.append(max(20, value))  # Ensure non-negative

# Create realistic price patterns correlated with consumption
prices = []
for i, cons in enumerate(consumption):
    hour = dates[i].hour
    
    # Base price
    base_price = 50
    
    # Price increases with consumption
    consumption_factor = (cons / 60) * 30
    
    # Peak hour pricing (higher during 7-9 AM and 6-9 PM)
    if (7 <= hour <= 9) or (18 <= hour <= 21):
        peak_factor = 20
    else:
        peak_factor = 0
    
    # Add random variation
    noise = np.random.normal(0, 5)
    
    price = base_price + consumption_factor + peak_factor + noise
    prices.append(max(20, price))  # Ensure non-negative

# Create DataFrame
df = pd.DataFrame({
    'datetime': dates,
    'energy_consumption': consumption,
    'price': prices
})

# Save to CSV
df.to_csv('data/energy_data.csv', index=False)
print(f"Generated {len(df)} rows of sample data")
print(df.head(10))
print(f"\nConsumption range: {df['energy_consumption'].min():.2f} - {df['energy_consumption'].max():.2f}")
print(f"Price range: {df['price'].min():.2f} - {df['price'].max():.2f}")
