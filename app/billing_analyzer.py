"""
Swiss Billing Analysis Module
Analyze electricity bills with Swiss tariff structure (CHF)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional

# Swiss average prices (CHF) - ElCom 2024 data
SWISS_DEFAULTS = {
    "energy_rate": 0.1271,          # CHF/kWh energy component
    "grid_rate": 0.0962,            # CHF/kWh network/grid charges
    "taxes_levies_rate": 0.0230,    # CHF/kWh (KEV, SDL, municipal)
    "fixed_monthly": 10.50,         # CHF/month standing charge
    "vat_rate": 0.081,              # 8.1% Swiss VAT
    "avg_household_kwh": 4500 / 12, # ~375 kWh/month (4-person household)
    "avg_household_bill": 108.0,    # CHF/month average
}

# Regional multipliers (illustrative)
CANTON_MULTIPLIERS = {
    "Zürich": 1.00,
    "Bern": 0.95,
    "Geneva": 1.08,
    "Basel": 0.92,
    "Lausanne": 1.05,
    "Other": 1.00,
}

HOUSEHOLD_KWHS = {
    "1 person": 200,
    "2 persons": 300,
    "3 persons": 350,
    "4 persons": 375,
    "5+ persons": 450,
}


class BillingAnalyzer:
    """Analyzes Swiss electricity bills and provides detailed explanations"""

    def __init__(self):
        self.defaults = SWISS_DEFAULTS.copy()

    def analyze_bill(
        self,
        total_bill: float,
        canton: str = "Other",
        household_size: str = "4 persons",
        custom_rates: Optional[Dict] = None,
    ) -> Dict:
        """
        Analyze a Swiss electricity bill and provide breakdown.

        Args:
            total_bill: Total monthly bill (CHF)
            canton: Canton/city for regional adjustment
            household_size: Household size for comparison
            custom_rates: Optional overrides for rates

        Returns:
            Dictionary with full analysis
        """
        # Use custom rates if provided, else defaults
        rates = custom_rates if custom_rates else {}
        energy_rate = rates.get("energy_rate", self.defaults["energy_rate"])
        grid_rate = rates.get("grid_rate", self.defaults["grid_rate"])
        taxes_levies_rate = rates.get("taxes_levies_rate", self.defaults["taxes_levies_rate"])
        fixed_monthly = rates.get("fixed_monthly", self.defaults["fixed_monthly"])
        vat_rate = rates.get("vat_rate", self.defaults["vat_rate"])

        # Regional adjustment
        region_mult = CANTON_MULTIPLIERS.get(canton, 1.0)
        energy_rate *= region_mult
        grid_rate *= region_mult

        # Back-calculate kWh from bill
        # Bill = (kWh * (energy + grid + taxes) + fixed) * (1 + VAT)
        variable_rate = energy_rate + grid_rate + taxes_levies_rate
        bill_before_vat = total_bill / (1 + vat_rate)
        variable_portion = bill_before_vat - fixed_monthly
        estimated_kwh = variable_portion / variable_rate if variable_rate > 0 else 0
        estimated_kwh = max(estimated_kwh, 0)

        # Compute cost components
        energy_cost = estimated_kwh * energy_rate
        grid_cost = estimated_kwh * grid_rate
        taxes_levies = estimated_kwh * taxes_levies_rate
        subtotal = energy_cost + grid_cost + taxes_levies + fixed_monthly
        vat_amount = subtotal * vat_rate
        total_calculated = subtotal + vat_amount

        # Percentages
        total_for_pct = total_calculated if total_calculated > 0 else 1
        pct_energy = (energy_cost / total_for_pct) * 100
        pct_grid = (grid_cost / total_for_pct) * 100
        pct_taxes = (taxes_levies / total_for_pct) * 100
        pct_fixed = (fixed_monthly / total_for_pct) * 100
        pct_vat = (vat_amount / total_for_pct) * 100

        # Comparison with average
        avg_kwh = HOUSEHOLD_KWHS.get(household_size, 375)
        avg_bill = self.defaults["avg_household_bill"]
        diff_kwh_pct = ((estimated_kwh - avg_kwh) / avg_kwh) * 100 if avg_kwh else 0
        diff_bill_pct = ((total_bill - avg_bill) / avg_bill) * 100 if avg_bill else 0

        # Reason explanations
        reasons = self._generate_reasons(
            estimated_kwh, avg_kwh, pct_fixed, pct_grid, canton
        )

        # Assumptions text
        assumptions = (
            f"Energy: CHF {energy_rate:.4f}/kWh, Grid: CHF {grid_rate:.4f}/kWh, "
            f"Taxes/Levies: CHF {taxes_levies_rate:.4f}/kWh, Fixed: CHF {fixed_monthly:.2f}/mo, "
            f"VAT: {vat_rate*100:.1f}%. Regional multiplier ({canton}): {region_mult:.2f}. "
            f"Avg household ({household_size}): ~{avg_kwh} kWh/mo, ~CHF {avg_bill}/mo."
        )

        return {
            "total_bill": round(total_bill, 2),
            "total_calculated": round(total_calculated, 2),
            "estimated_kwh": round(estimated_kwh, 1),
            "avg_chf_per_kwh": round(total_bill / estimated_kwh, 4) if estimated_kwh > 0 else 0,
            "energy_cost": round(energy_cost, 2),
            "grid_cost": round(grid_cost, 2),
            "taxes_levies": round(taxes_levies, 2),
            "fixed_monthly": round(fixed_monthly, 2),
            "vat_amount": round(vat_amount, 2),
            "pct_energy": round(pct_energy, 1),
            "pct_grid": round(pct_grid, 1),
            "pct_taxes": round(pct_taxes, 1),
            "pct_fixed": round(pct_fixed, 1),
            "pct_vat": round(pct_vat, 1),
            "avg_kwh": avg_kwh,
            "avg_bill": avg_bill,
            "diff_kwh_pct": round(diff_kwh_pct, 1),
            "diff_bill_pct": round(diff_bill_pct, 1),
            "reasons": reasons,
            "assumptions": assumptions,
            "rates": {
                "energy_rate": energy_rate,
                "grid_rate": grid_rate,
                "taxes_levies_rate": taxes_levies_rate,
                "fixed_monthly": fixed_monthly,
                "vat_rate": vat_rate,
            },
            "canton": canton,
            "household_size": household_size,
        }

    def _generate_reasons(
        self,
        estimated_kwh: float,
        avg_kwh: float,
        pct_fixed: float,
        pct_grid: float,
        canton: str,
    ) -> Dict:
        """Generate reason explanations for bill components."""
        reasons = {}

        # Grid fees
        reasons["grid_fees"] = (
            "Grid/network charges cover the cost of maintaining and operating the electricity "
            "distribution network (poles, cables, transformers). These are regulated by ElCom and "
            "vary by region based on local infrastructure costs."
        )

        # Fixed costs
        reasons["fixed_costs"] = (
            "Fixed monthly charges cover metering, billing, and customer service regardless of "
            "how much electricity you use. Even with zero consumption, you pay this base fee."
        )

        # High bill with low usage
        if estimated_kwh < avg_kwh * 0.7 and pct_fixed > 15:
            reasons["high_bill_low_usage"] = (
                "Your bill may seem high relative to usage because fixed charges and grid fees "
                "make up a large share. These costs don't scale with consumption."
            )
        else:
            reasons["high_bill_low_usage"] = None

        # Seasonal effects
        reasons["seasonal"] = (
            "Swiss electricity prices can vary seasonally. Winter months often see higher demand "
            "(heating, lighting) which can increase both consumption and sometimes spot prices."
        )

        # Regional effects
        if canton in ["Geneva", "Lausanne"]:
            reasons["regional"] = (
                f"{canton} tends to have above-average electricity prices due to higher local "
                "utility and grid costs."
            )
        elif canton in ["Basel", "Bern"]:
            reasons["regional"] = (
                f"{canton} benefits from relatively lower electricity prices compared to the "
                "Swiss average."
            )
        else:
            reasons["regional"] = (
                "Electricity prices vary across Swiss cantons depending on local utility costs, "
                "grid infrastructure, and municipal fees."
            )

        return reasons

    def calculate_potential_savings(
        self,
        current_bill: float,
        canton: str = "Other",
        household_size: str = "4 persons",
        optimization_level: str = "moderate",
    ) -> Dict:
        """Calculate potential savings with optimization strategies."""
        analysis = self.analyze_bill(current_bill, canton, household_size)

        scenarios = {
            "conservative": {"reduction": 0.05, "desc": "Basic efficiency (LED, standby off)"},
            "moderate": {"reduction": 0.12, "desc": "Efficiency + load shifting"},
            "aggressive": {"reduction": 0.20, "desc": "Major upgrades + solar"},
        }
        scenario = scenarios.get(optimization_level, scenarios["moderate"])

        new_kwh = analysis["estimated_kwh"] * (1 - scenario["reduction"])
        rates = analysis["rates"]
        variable_rate = rates["energy_rate"] + rates["grid_rate"] + rates["taxes_levies_rate"]
        new_variable = new_kwh * variable_rate
        new_subtotal = new_variable + rates["fixed_monthly"]
        new_total = new_subtotal * (1 + rates["vat_rate"])

        monthly_savings = current_bill - new_total
        annual_savings = monthly_savings * 12

        return {
            "optimization_level": optimization_level,
            "description": scenario["desc"],
            "current_bill": round(current_bill, 2),
            "optimized_bill": round(new_total, 2),
            "monthly_savings": round(monthly_savings, 2),
            "annual_savings": round(annual_savings, 2),
            "percentage_savings": round((monthly_savings / current_bill) * 100, 1) if current_bill else 0,
            "actions": self._get_optimization_actions(optimization_level),
        }

    def _get_optimization_actions(self, level: str) -> list:
        actions = {
            "conservative": [
                "Replace bulbs with LED",
                "Turn off standby devices",
                "Use cold wash for laundry",
            ],
            "moderate": [
                "All conservative actions",
                "Shift heavy loads to off-peak hours",
                "Upgrade old appliances to A+++",
                "Install smart plugs/timers",
            ],
            "aggressive": [
                "All moderate actions",
                "Install rooftop solar (3-5 kW)",
                "Add home battery storage",
                "Switch to heat pump heating",
            ],
        }
        return actions.get(level, actions["moderate"])
