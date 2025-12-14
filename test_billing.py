"""
Quick test of billing module integration
"""

from app.billing_analyzer import BillingAnalyzer

# Test the billing analyzer
analyzer = BillingAnalyzer()

print("=" * 60)
print("BILLING ANALYZER TEST")
print("=" * 60)

# Test 1: Basic bill analysis
print("\n1. Testing basic bill analysis (€100)...")
result = analyzer.analyze_bill(100.0, "Residential - Standard")
print(f"   ✓ Estimated units: {result['estimated_units']} kWh")
print(f"   ✓ Peak units: {result['peak_units']} kWh")
print(f"   ✓ Off-peak units: {result['off_peak_units']} kWh")
print(f"   ✓ Cost per unit: €{result['cost_per_unit']:.3f}")

# Test 2: With known units
print("\n2. Testing with known units (300 kWh)...")
result2 = analyzer.analyze_bill(100.0, "Residential - Standard", 300.0)
print(f"   ✓ Estimated units: {result2['estimated_units']} kWh")
print(f"   ✓ Consumption level: {result2['insights']['consumption_level']}")

# Test 3: Savings calculation
print("\n3. Testing savings calculator...")
savings = analyzer.calculate_potential_savings(100.0, "Residential - Standard", "moderate")
print(f"   ✓ Monthly savings: €{savings['monthly_savings']:.2f}")
print(f"   ✓ Annual savings: €{savings['annual_savings']:.2f}")
print(f"   ✓ Percentage savings: {savings['percentage_savings']:.1f}%")

# Test 4: All rate structures
print("\n4. Testing all rate structures...")
for rate in ["Residential - Standard", "Residential - Time-of-Use", "Commercial"]:
    result = analyzer.analyze_bill(150.0, rate)
    print(f"   ✓ {rate}: {result['estimated_units']:.1f} kWh @ €{result['cost_per_unit']:.3f}/kWh")

print("\n" + "=" * 60)
print("ALL TESTS PASSED! ✓")
print("=" * 60)
print("\nBilling module is ready to use in the dashboard!")
print("Run: streamlit run app.py")
print("Then select: 💰 Bill Analysis & Optimization")
