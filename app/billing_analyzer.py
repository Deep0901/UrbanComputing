"""
Billing Analysis Module
Analyze electricity bills and provide detailed breakdown
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple

class BillingAnalyzer:
    """Analyzes electricity bills and provides detailed explanations"""
    
    def __init__(self):
        # Common rate structures (per kWh)
        self.rate_structures = {
            "Residential - Standard": {
                "base_rate": 0.12,  # €/kWh
                "peak_rate": 0.18,  # €/kWh (6 AM - 10 PM)
                "off_peak_rate": 0.08,  # €/kWh (10 PM - 6 AM)
                "fixed_charge": 15.0,  # € per month
                "tax_rate": 0.21,  # 21% VAT
            },
            "Residential - Time-of-Use": {
                "base_rate": 0.10,
                "peak_rate": 0.22,
                "off_peak_rate": 0.06,
                "fixed_charge": 12.0,
                "tax_rate": 0.21,
            },
            "Commercial": {
                "base_rate": 0.15,
                "peak_rate": 0.25,
                "off_peak_rate": 0.10,
                "fixed_charge": 50.0,
                "tax_rate": 0.21,
            }
        }
        
    def analyze_bill(
        self,
        total_bill: float,
        rate_structure: str = "Residential - Standard",
        known_units: float = None
    ) -> Dict:
        """
        Analyze electricity bill and provide breakdown
        
        Args:
            total_bill: Total monthly bill amount (€)
            rate_structure: Type of rate plan
            known_units: If known, the total units consumed (kWh)
        
        Returns:
            Dictionary with detailed analysis
        """
        rates = self.rate_structures.get(rate_structure, self.rate_structures["Residential - Standard"])
        
        # Reverse calculate units if not provided
        if known_units is None:
            # Assume 70% peak, 30% off-peak usage pattern
            # Total bill = (units * weighted_rate + fixed_charge) * (1 + tax_rate)
            
            # Remove tax first
            bill_before_tax = total_bill / (1 + rates["tax_rate"])
            
            # Remove fixed charge
            energy_charges = bill_before_tax - rates["fixed_charge"]
            
            # Calculate weighted average rate (70% peak, 30% off-peak)
            weighted_rate = (0.70 * rates["peak_rate"]) + (0.30 * rates["off_peak_rate"])
            
            # Calculate total units
            estimated_units = energy_charges / weighted_rate if weighted_rate > 0 else 0
            
            # Estimate peak/off-peak breakdown
            peak_units = estimated_units * 0.70
            off_peak_units = estimated_units * 0.30
        else:
            estimated_units = known_units
            # Assume 70% peak, 30% off-peak
            peak_units = known_units * 0.70
            off_peak_units = known_units * 0.30
        
        # Calculate charges
        peak_charges = peak_units * rates["peak_rate"]
        off_peak_charges = off_peak_units * rates["off_peak_rate"]
        energy_charges = peak_charges + off_peak_charges
        fixed_charges = rates["fixed_charge"]
        
        subtotal = energy_charges + fixed_charges
        tax_amount = subtotal * rates["tax_rate"]
        total_calculated = subtotal + tax_amount
        
        # Daily/hourly breakdown
        daily_units = estimated_units / 30  # Assume 30 days
        hourly_units = daily_units / 24
        daily_cost = total_bill / 30
        
        # Cost per unit
        cost_per_unit = total_bill / estimated_units if estimated_units > 0 else 0
        
        # Generate insights
        insights = self._generate_insights(
            estimated_units, daily_units, cost_per_unit, 
            peak_units, off_peak_units, rates
        )
        
        return {
            "total_bill": total_bill,
            "estimated_units": round(estimated_units, 2),
            "peak_units": round(peak_units, 2),
            "off_peak_units": round(off_peak_units, 2),
            "peak_charges": round(peak_charges, 2),
            "off_peak_charges": round(off_peak_charges, 2),
            "energy_charges": round(energy_charges, 2),
            "fixed_charges": round(fixed_charges, 2),
            "tax_amount": round(tax_amount, 2),
            "total_calculated": round(total_calculated, 2),
            "daily_units": round(daily_units, 2),
            "hourly_units": round(hourly_units, 3),
            "daily_cost": round(daily_cost, 2),
            "cost_per_unit": round(cost_per_unit, 3),
            "rate_structure": rate_structure,
            "insights": insights,
            "rates": rates
        }
    
    def _generate_insights(
        self, 
        total_units: float, 
        daily_units: float, 
        cost_per_unit: float,
        peak_units: float,
        off_peak_units: float,
        rates: Dict
    ) -> Dict:
        """Generate insights about consumption patterns"""
        
        insights = {
            "consumption_level": "",
            "cost_efficiency": "",
            "recommendations": [],
            "comparison": ""
        }
        
        # Consumption level analysis
        if total_units < 200:
            insights["consumption_level"] = "🟢 Low consumption - Efficient usage"
        elif total_units < 400:
            insights["consumption_level"] = "🟡 Moderate consumption - Average household"
        elif total_units < 600:
            insights["consumption_level"] = "🟠 Above average consumption"
        else:
            insights["consumption_level"] = "🔴 High consumption - Review usage patterns"
        
        # Cost efficiency
        if cost_per_unit < 0.15:
            insights["cost_efficiency"] = "✅ Good rate - Below market average"
        elif cost_per_unit < 0.20:
            insights["cost_efficiency"] = "⚠️ Average rate - Consider time-of-use plans"
        else:
            insights["cost_efficiency"] = "❗ High rate - Negotiate or switch provider"
        
        # Recommendations
        insights["recommendations"].append(
            f"💡 Shift {round(peak_units * 0.2, 1)} kWh from peak to off-peak hours to save "
            f"€{round(peak_units * 0.2 * (rates['peak_rate'] - rates['off_peak_rate']), 2)}/month"
        )
        
        if daily_units > 15:
            insights["recommendations"].append(
                "⚡ High daily usage detected - Check for inefficient appliances or phantom loads"
            )
        
        if peak_units / (peak_units + off_peak_units) > 0.8:
            insights["recommendations"].append(
                "🌙 Most usage during peak hours - Consider running dishwasher/laundry at night"
            )
        
        # Comparison
        avg_household = 300  # kWh/month
        if total_units < avg_household * 0.7:
            insights["comparison"] = f"📊 You use {round((1 - total_units/avg_household)*100)}% less than average household"
        elif total_units > avg_household * 1.3:
            insights["comparison"] = f"📊 You use {round((total_units/avg_household - 1)*100)}% more than average household"
        else:
            insights["comparison"] = "📊 Your consumption is close to average household usage"
        
        return insights
    
    def calculate_potential_savings(
        self,
        current_bill: float,
        rate_structure: str,
        optimization_level: str = "moderate"
    ) -> Dict:
        """Calculate potential savings with optimization strategies"""
        
        analysis = self.analyze_bill(current_bill, rate_structure)
        
        savings_scenarios = {
            "conservative": {
                "peak_reduction": 0.10,  # 10% reduction in peak usage
                "efficiency_gain": 0.05,  # 5% overall reduction
                "description": "Basic efficiency improvements"
            },
            "moderate": {
                "peak_reduction": 0.20,  # 20% reduction
                "efficiency_gain": 0.10,  # 10% overall reduction
                "description": "Time-shifting and efficiency upgrades"
            },
            "aggressive": {
                "peak_reduction": 0.30,  # 30% reduction
                "efficiency_gain": 0.15,  # 15% overall reduction
                "description": "Major behavioral changes + smart home"
            }
        }
        
        scenario = savings_scenarios.get(optimization_level, savings_scenarios["moderate"])
        
        # Calculate new consumption
        new_peak_units = analysis["peak_units"] * (1 - scenario["peak_reduction"])
        new_off_peak_units = analysis["off_peak_units"] + (analysis["peak_units"] * scenario["peak_reduction"])
        
        # Apply efficiency gain
        new_peak_units *= (1 - scenario["efficiency_gain"])
        new_off_peak_units *= (1 - scenario["efficiency_gain"])
        
        # Calculate new bill
        rates = analysis["rates"]
        new_energy_charges = (new_peak_units * rates["peak_rate"]) + (new_off_peak_units * rates["off_peak_rate"])
        new_subtotal = new_energy_charges + rates["fixed_charge"]
        new_total = new_subtotal * (1 + rates["tax_rate"])
        
        monthly_savings = current_bill - new_total
        annual_savings = monthly_savings * 12
        percentage_savings = (monthly_savings / current_bill) * 100
        
        return {
            "optimization_level": optimization_level,
            "description": scenario["description"],
            "current_bill": round(current_bill, 2),
            "optimized_bill": round(new_total, 2),
            "monthly_savings": round(monthly_savings, 2),
            "annual_savings": round(annual_savings, 2),
            "percentage_savings": round(percentage_savings, 1),
            "new_peak_units": round(new_peak_units, 2),
            "new_off_peak_units": round(new_off_peak_units, 2),
            "actions": self._get_optimization_actions(optimization_level)
        }
    
    def _get_optimization_actions(self, level: str) -> list:
        """Get specific actions for optimization level"""
        
        actions = {
            "conservative": [
                "Switch to LED bulbs",
                "Unplug devices when not in use",
                "Use power strips to eliminate phantom loads",
                "Set thermostat 1-2°C lower in winter/higher in summer"
            ],
            "moderate": [
                "All conservative actions",
                "Run dishwasher/laundry during off-peak hours (after 10 PM)",
                "Install programmable thermostat",
                "Upgrade to Energy Star appliances",
                "Use timer switches for water heater"
            ],
            "aggressive": [
                "All moderate actions",
                "Install smart home energy management system",
                "Add solar panels (3-5 kW system)",
                "Upgrade to heat pump",
                "Add home battery storage",
                "Implement demand response automation"
            ]
        }
        
        return actions.get(level, actions["moderate"])
