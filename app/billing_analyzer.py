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

        # Build rates dict for reasons
        rates_dict = {
            "energy_rate": energy_rate,
            "grid_rate": grid_rate,
            "taxes_levies_rate": taxes_levies_rate,
            "fixed_monthly": fixed_monthly,
            "vat_rate": vat_rate,
        }

        # Reason explanations (dynamic, based on actual analysis)
        reasons = self._generate_reasons(
            estimated_kwh=estimated_kwh,
            avg_kwh=avg_kwh,
            pct_fixed=pct_fixed,
            pct_grid=pct_grid,
            canton=canton,
            total_bill=total_bill,
            avg_bill=avg_bill,
            household_size=household_size,
            rates=rates_dict,
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
        total_bill: float,
        avg_bill: float,
        household_size: str,
        rates: Dict,
    ) -> Dict:
        """Generate dynamic, realistic reason explanations based on actual bill analysis."""
        reasons = {}
        
        diff_kwh_pct = ((estimated_kwh - avg_kwh) / avg_kwh) * 100 if avg_kwh else 0
        diff_bill_pct = ((total_bill - avg_bill) / avg_bill) * 100 if avg_bill else 0
        
        # ===== MAIN REASON: Why is bill high/low/normal? =====
        if diff_bill_pct > 30:
            reasons["main_reason"] = {
                "title": "🔴 Your Bill is Significantly Higher Than Average",
                "explanation": (
                    f"Your bill of CHF {total_bill:.2f} is **{diff_bill_pct:.0f}% higher** than the "
                    f"typical {household_size} household (CHF {avg_bill:.2f}). "
                    f"This is primarily because you consumed **{estimated_kwh:.0f} kWh** this month, "
                    f"which is {diff_kwh_pct:.0f}% {'above' if diff_kwh_pct > 0 else 'below'} average."
                ),
                "severity": "high"
            }
        elif diff_bill_pct > 10:
            reasons["main_reason"] = {
                "title": "🟠 Your Bill is Above Average",
                "explanation": (
                    f"Your bill of CHF {total_bill:.2f} is **{diff_bill_pct:.0f}% higher** than average. "
                    f"Your consumption of {estimated_kwh:.0f} kWh suggests some room for optimization."
                ),
                "severity": "medium"
            }
        elif diff_bill_pct < -20:
            reasons["main_reason"] = {
                "title": "🟢 Your Bill is Below Average - Great Job!",
                "explanation": (
                    f"Your bill of CHF {total_bill:.2f} is **{abs(diff_bill_pct):.0f}% lower** than "
                    f"the typical {household_size} household. Your {estimated_kwh:.0f} kWh consumption "
                    f"shows you're being energy efficient!"
                ),
                "severity": "low"
            }
        else:
            reasons["main_reason"] = {
                "title": "🟡 Your Bill is Within Normal Range",
                "explanation": (
                    f"Your bill of CHF {total_bill:.2f} is close to the Swiss average for a "
                    f"{household_size} household. Your {estimated_kwh:.0f} kWh consumption is typical."
                ),
                "severity": "normal"
            }
        
        # ===== CONSUMPTION DRIVERS =====
        consumption_drivers = []
        
        if estimated_kwh > 400:
            consumption_drivers.append(
                "🔌 **High base consumption**: You may have energy-intensive appliances running "
                "(electric water heater, old refrigerator, or always-on devices)."
            )
        
        if estimated_kwh > avg_kwh * 1.3:
            consumption_drivers.append(
                "📈 **Above-average usage pattern**: Consider whether you've had guests, "
                "used heating/cooling more, or added new appliances recently."
            )
        
        if pct_grid > 40:
            consumption_drivers.append(
                f"🌐 **High grid charges ({pct_grid:.0f}%)**: Your region has above-average "
                "network costs. This is set by your local utility and regulated by ElCom."
            )
        
        if pct_fixed > 12:
            consumption_drivers.append(
                f"📋 **Fixed costs impact ({pct_fixed:.0f}%)**: With lower consumption, "
                "fixed charges take a bigger percentage of your bill."
            )
        
        # Seasonal consideration (winter months)
        import datetime
        current_month = datetime.datetime.now().month
        if current_month in [11, 12, 1, 2]:
            consumption_drivers.append(
                "❄️ **Winter season**: Higher lighting needs and potential electric heating "
                "typically increase consumption by 15-30% compared to summer."
            )
        elif current_month in [6, 7, 8]:
            consumption_drivers.append(
                "☀️ **Summer season**: If you use air conditioning, this can significantly "
                "increase your consumption during hot periods."
            )
        
        reasons["consumption_drivers"] = consumption_drivers if consumption_drivers else [
            "✅ No unusual consumption patterns detected."
        ]
        
        # ===== REGIONAL ANALYSIS =====
        region_mult = CANTON_MULTIPLIERS.get(canton, 1.0)
        if canton in ["Geneva", "Lausanne"]:
            reasons["regional_impact"] = {
                "title": f"📍 {canton} - Above Average Prices",
                "explanation": (
                    f"Electricity in {canton} costs about **{(region_mult-1)*100:.0f}% more** than "
                    "the Swiss average due to higher local utility costs, urban infrastructure "
                    "maintenance, and municipal fees."
                ),
                "impact": f"+{(region_mult-1)*total_bill:.2f} CHF extra on your bill"
            }
        elif canton in ["Basel", "Bern"]:
            reasons["regional_impact"] = {
                "title": f"📍 {canton} - Below Average Prices",
                "explanation": (
                    f"Good news! {canton} has **{abs(1-region_mult)*100:.0f}% lower** electricity "
                    "prices than the Swiss average, thanks to efficient local utilities."
                ),
                "impact": f"You save ~{abs(1-region_mult)*total_bill:.2f} CHF compared to average"
            }
        else:
            reasons["regional_impact"] = {
                "title": f"📍 {canton} - Average Prices",
                "explanation": (
                    f"Electricity prices in {canton} are close to the Swiss national average."
                ),
                "impact": "No significant regional premium or discount"
            }
        
        # ===== COST BREAKDOWN INSIGHTS =====
        cost_insights = []
        
        energy_rate = rates.get("energy_rate", 0.1271)
        if energy_rate > 0.14:
            cost_insights.append(
                f"⚡ **Energy rate is high** (CHF {energy_rate:.4f}/kWh): Consider comparing "
                "with other suppliers or negotiating your contract."
            )
        
        if rates.get("fixed_monthly", 10.50) > 12:
            cost_insights.append(
                f"📋 **High fixed charge** (CHF {rates.get('fixed_monthly', 10.50):.2f}/mo): "
                "This is above average. Check if your tariff plan suits your usage."
            )
        
        avg_price_per_kwh = total_bill / estimated_kwh if estimated_kwh > 0 else 0
        if avg_price_per_kwh > 0.30:
            cost_insights.append(
                f"💰 **High all-in price** (CHF {avg_price_per_kwh:.2f}/kWh): Your effective "
                "rate is above the Swiss average of ~0.27 CHF/kWh."
            )
        elif avg_price_per_kwh < 0.22 and avg_price_per_kwh > 0:
            cost_insights.append(
                f"✅ **Good rate** (CHF {avg_price_per_kwh:.2f}/kWh): Your effective rate "
                "is below average - you're getting a good deal!"
            )
        
        reasons["cost_insights"] = cost_insights if cost_insights else [
            "✅ Your rates appear to be within normal Swiss ranges."
        ]
        
        # ===== PERSONALIZED TIPS =====
        tips = []
        
        if diff_kwh_pct > 20:
            tips.extend([
                "🔍 **Identify energy vampires**: Use a power meter to check standby consumption of your devices.",
                "⏰ **Shift usage to off-peak**: Run dishwasher/washing machine during night hours (if your tariff supports it).",
                "🌡️ **Check heating efficiency**: If using electric heating, consider a heat pump upgrade.",
            ])
        
        if estimated_kwh > 300:
            tips.extend([
                "🧊 **Check your refrigerator**: Old fridges can use 3x more than modern A+++ models.",
                "💡 **LED lighting**: If not already done, switch all bulbs - LEDs use 80% less energy.",
            ])
        
        if pct_fixed > 15 and estimated_kwh < 250:
            tips.append(
                "📊 **Consider tariff change**: With low usage, a tariff with lower fixed fees "
                "but higher variable rates might save you money."
            )
        
        if canton in ["Geneva", "Lausanne", "Zürich"]:
            tips.append(
                "☀️ **Solar potential**: Urban areas often have good solar incentives. "
                "Check your canton's subsidy programs for rooftop solar."
            )
        
        # Default tips if none specific
        if not tips:
            tips = [
                "💡 **Maintain efficiency**: Keep appliances clean and well-maintained.",
                "🔌 **Smart power strips**: Use them to easily cut standby power.",
                "📱 **Monitor usage**: Consider a smart meter to track consumption patterns.",
            ]
        
        reasons["personalized_tips"] = tips
        
        # ===== QUICK ACTIONS =====
        if diff_bill_pct > 20:
            reasons["quick_actions"] = [
                f"1️⃣ **Immediate**: Check for devices left running (estimated 10-20 CHF/month savings)",
                f"2️⃣ **This week**: Replace any old incandescent bulbs with LED (saves ~5 CHF/month)",
                f"3️⃣ **This month**: Review your tariff and compare with alternatives",
            ]
        elif diff_bill_pct > 0:
            reasons["quick_actions"] = [
                f"1️⃣ **Easy win**: Reduce standby consumption by unplugging unused devices",
                f"2️⃣ **Habit change**: Turn off lights when leaving rooms",
                f"3️⃣ **Long-term**: Plan to replace old appliances when they fail",
            ]
        else:
            reasons["quick_actions"] = [
                f"1️⃣ **Maintain**: Keep up your good energy habits!",
                f"2️⃣ **Optimize further**: Consider time-of-use tariffs if available",
                f"3️⃣ **Future-proof**: Look into solar or home battery options",
            ]
        
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
