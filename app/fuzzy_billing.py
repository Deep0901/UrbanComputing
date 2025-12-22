"""
=============================================================================
FUZZY LOGIC BILLING ANALYSIS MODULE
=============================================================================

This module implements a Fuzzy Inference System (FIS) for electricity bill 
analysis and optimization recommendations. It uses Mamdani-type fuzzy 
inference to provide human-understandable explanations for billing patterns.

Key Components:
1. Fuzzy Variables for billing analysis
2. Membership functions for bill amounts, consumption, efficiency
3. Fuzzy rules for bill categorization and recommendations
4. Linguistic explanations based on fuzzy inference

Theory Reference:
- Zadeh, L.A. (1965). Fuzzy Sets. Information and Control, 8(3), 338-353.
- Mamdani, E.H. (1974). Application of Fuzzy Algorithms for Control.

Author: Energy Explainability Research Project
=============================================================================
"""

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from typing import Dict, List, Tuple


class FuzzyBillingSystem:
    """
    Fuzzy Inference System for Swiss Electricity Bill Analysis.
    
    This class implements a Mamdani-type FIS with:
    - 5 input variables (bill_amount, consumption, fixed_ratio, regional_factor, efficiency)
    - 2 output variables (bill_assessment, savings_potential)
    - 25+ fuzzy rules for comprehensive bill analysis
    
    The system provides transparent, explainable insights that are
    more intuitive than traditional numerical methods.
    """
    
    def __init__(self):
        """Initialize the Fuzzy Billing System with all variables and rules."""
        self._setup_fuzzy_variables()
        self._setup_fuzzy_rules()
        self._create_control_system()
    
    def _setup_fuzzy_variables(self):
        """
        Define fuzzy variables with triangular/trapezoidal membership functions.
        
        Swiss context:
        - Average household bill: ~108 CHF/month
        - Average consumption: ~375 kWh/month (4-person household)
        - Bill range: 30-400+ CHF/month depending on household
        """
        # =====================================================================
        # INPUT VARIABLE 1: BILL AMOUNT (CHF/month)
        # Universe: 0-500 CHF (covers most Swiss households)
        # =====================================================================
        self.bill_amount = ctrl.Antecedent(np.arange(0, 501, 1), 'bill_amount')
        
        self.bill_amount['very_low'] = fuzz.trapmf(self.bill_amount.universe, [0, 0, 40, 70])
        self.bill_amount['low'] = fuzz.trimf(self.bill_amount.universe, [50, 80, 110])
        self.bill_amount['medium'] = fuzz.trimf(self.bill_amount.universe, [90, 130, 180])
        self.bill_amount['high'] = fuzz.trimf(self.bill_amount.universe, [150, 220, 300])
        self.bill_amount['very_high'] = fuzz.trapmf(self.bill_amount.universe, [250, 350, 500, 500])
        
        # =====================================================================
        # INPUT VARIABLE 2: CONSUMPTION (kWh/month)
        # Universe: 0-800 kWh (covers 1-person to large households)
        # =====================================================================
        self.consumption = ctrl.Antecedent(np.arange(0, 801, 1), 'consumption')
        
        self.consumption['very_low'] = fuzz.trapmf(self.consumption.universe, [0, 0, 100, 200])
        self.consumption['low'] = fuzz.trimf(self.consumption.universe, [150, 250, 350])
        self.consumption['medium'] = fuzz.trimf(self.consumption.universe, [300, 400, 500])
        self.consumption['high'] = fuzz.trimf(self.consumption.universe, [450, 550, 650])
        self.consumption['very_high'] = fuzz.trapmf(self.consumption.universe, [600, 700, 800, 800])
        
        # =====================================================================
        # INPUT VARIABLE 3: DEVIATION FROM AVERAGE (%)
        # Universe: -100 to +100 (percentage difference from household average)
        # =====================================================================
        self.deviation = ctrl.Antecedent(np.arange(-100, 101, 1), 'deviation')
        
        self.deviation['much_below'] = fuzz.trapmf(self.deviation.universe, [-100, -100, -40, -20])
        self.deviation['below'] = fuzz.trimf(self.deviation.universe, [-35, -15, 5])
        self.deviation['average'] = fuzz.trimf(self.deviation.universe, [-10, 0, 10])
        self.deviation['above'] = fuzz.trimf(self.deviation.universe, [-5, 15, 35])
        self.deviation['much_above'] = fuzz.trapmf(self.deviation.universe, [20, 40, 100, 100])
        
        # =====================================================================
        # INPUT VARIABLE 4: FIXED COST RATIO (%)
        # Universe: 0-30% (percentage of bill that is fixed charges)
        # Higher ratio indicates low consumption household
        # =====================================================================
        self.fixed_ratio = ctrl.Antecedent(np.arange(0, 31, 1), 'fixed_ratio')
        
        self.fixed_ratio['very_low'] = fuzz.trapmf(self.fixed_ratio.universe, [0, 0, 4, 7])
        self.fixed_ratio['low'] = fuzz.trimf(self.fixed_ratio.universe, [5, 8, 12])
        self.fixed_ratio['medium'] = fuzz.trimf(self.fixed_ratio.universe, [10, 14, 18])
        self.fixed_ratio['high'] = fuzz.trimf(self.fixed_ratio.universe, [15, 20, 25])
        self.fixed_ratio['very_high'] = fuzz.trapmf(self.fixed_ratio.universe, [22, 27, 30, 30])
        
        # =====================================================================
        # INPUT VARIABLE 5: EFFICIENCY SCORE (0-100)
        # Based on kWh/CHF ratio compared to optimal
        # =====================================================================
        self.efficiency = ctrl.Antecedent(np.arange(0, 101, 1), 'efficiency')
        
        self.efficiency['very_poor'] = fuzz.trapmf(self.efficiency.universe, [0, 0, 15, 30])
        self.efficiency['poor'] = fuzz.trimf(self.efficiency.universe, [20, 35, 50])
        self.efficiency['average'] = fuzz.trimf(self.efficiency.universe, [40, 55, 70])
        self.efficiency['good'] = fuzz.trimf(self.efficiency.universe, [60, 75, 90])
        self.efficiency['excellent'] = fuzz.trapmf(self.efficiency.universe, [80, 90, 100, 100])
        
        # =====================================================================
        # OUTPUT VARIABLE 1: BILL ASSESSMENT (0-100)
        # 0 = Excellent (very low bill), 100 = Critical (needs attention)
        # =====================================================================
        self.bill_assessment = ctrl.Consequent(np.arange(0, 101, 1), 'bill_assessment')
        
        self.bill_assessment['excellent'] = fuzz.trapmf(self.bill_assessment.universe, [0, 0, 10, 25])
        self.bill_assessment['good'] = fuzz.trimf(self.bill_assessment.universe, [15, 30, 45])
        self.bill_assessment['normal'] = fuzz.trimf(self.bill_assessment.universe, [35, 50, 65])
        self.bill_assessment['concerning'] = fuzz.trimf(self.bill_assessment.universe, [55, 70, 85])
        self.bill_assessment['critical'] = fuzz.trapmf(self.bill_assessment.universe, [75, 90, 100, 100])
        
        # =====================================================================
        # OUTPUT VARIABLE 2: SAVINGS POTENTIAL (0-100)
        # 0 = Little room for savings, 100 = High potential
        # =====================================================================
        self.savings_potential = ctrl.Consequent(np.arange(0, 101, 1), 'savings_potential')
        
        self.savings_potential['minimal'] = fuzz.trapmf(self.savings_potential.universe, [0, 0, 10, 25])
        self.savings_potential['low'] = fuzz.trimf(self.savings_potential.universe, [15, 30, 45])
        self.savings_potential['moderate'] = fuzz.trimf(self.savings_potential.universe, [35, 50, 65])
        self.savings_potential['high'] = fuzz.trimf(self.savings_potential.universe, [55, 70, 85])
        self.savings_potential['very_high'] = fuzz.trapmf(self.savings_potential.universe, [75, 90, 100, 100])
    
    def _setup_fuzzy_rules(self):
        """
        Define fuzzy IF-THEN rules for bill analysis.
        
        Rule categories:
        1. Bill-Consumption relationship rules
        2. Deviation from average rules
        3. Efficiency assessment rules
        4. Savings potential rules
        """
        self.rules = []
        
        # =================================================================
        # RULE GROUP 1: Bill Amount Assessment Rules
        # =================================================================
        
        # Rule 1: Very high bill with high consumption = critical
        self.rules.append(ctrl.Rule(
            self.bill_amount['very_high'] & self.consumption['very_high'],
            self.bill_assessment['critical']
        ))
        
        # Rule 2: High bill with high consumption = concerning
        self.rules.append(ctrl.Rule(
            self.bill_amount['high'] & self.consumption['high'],
            self.bill_assessment['concerning']
        ))
        
        # Rule 3: Medium bill with medium consumption = normal
        self.rules.append(ctrl.Rule(
            self.bill_amount['medium'] & self.consumption['medium'],
            self.bill_assessment['normal']
        ))
        
        # Rule 4: Low bill with low consumption = good
        self.rules.append(ctrl.Rule(
            self.bill_amount['low'] & self.consumption['low'],
            self.bill_assessment['good']
        ))
        
        # Rule 5: Very low bill = excellent
        self.rules.append(ctrl.Rule(
            self.bill_amount['very_low'],
            self.bill_assessment['excellent']
        ))
        
        # =================================================================
        # RULE GROUP 2: Deviation-Based Assessment Rules
        # =================================================================
        
        # Rule 6: Much above average = critical
        self.rules.append(ctrl.Rule(
            self.deviation['much_above'],
            self.bill_assessment['critical']
        ))
        
        # Rule 7: Above average = concerning
        self.rules.append(ctrl.Rule(
            self.deviation['above'],
            self.bill_assessment['concerning']
        ))
        
        # Rule 8: Average deviation = normal
        self.rules.append(ctrl.Rule(
            self.deviation['average'],
            self.bill_assessment['normal']
        ))
        
        # Rule 9: Below average = good
        self.rules.append(ctrl.Rule(
            self.deviation['below'],
            self.bill_assessment['good']
        ))
        
        # Rule 10: Much below average = excellent
        self.rules.append(ctrl.Rule(
            self.deviation['much_below'],
            self.bill_assessment['excellent']
        ))
        
        # =================================================================
        # RULE GROUP 3: Efficiency-Based Rules
        # =================================================================
        
        # Rule 11: Very poor efficiency = critical
        self.rules.append(ctrl.Rule(
            self.efficiency['very_poor'],
            self.bill_assessment['critical']
        ))
        
        # Rule 12: Poor efficiency with high bill = critical
        self.rules.append(ctrl.Rule(
            self.efficiency['poor'] & self.bill_amount['high'],
            self.bill_assessment['critical']
        ))
        
        # Rule 13: Average efficiency = normal
        self.rules.append(ctrl.Rule(
            self.efficiency['average'],
            self.bill_assessment['normal']
        ))
        
        # Rule 14: Good efficiency = good assessment
        self.rules.append(ctrl.Rule(
            self.efficiency['good'],
            self.bill_assessment['good']
        ))
        
        # Rule 15: Excellent efficiency = excellent assessment
        self.rules.append(ctrl.Rule(
            self.efficiency['excellent'],
            self.bill_assessment['excellent']
        ))
        
        # =================================================================
        # RULE GROUP 4: Fixed Cost Ratio Rules
        # =================================================================
        
        # Rule 16: Very high fixed ratio (low consumption) = good potential
        self.rules.append(ctrl.Rule(
            self.fixed_ratio['very_high'],
            self.bill_assessment['good']
        ))
        
        # Rule 17: Very low fixed ratio (high consumption) with high bill = concerning
        self.rules.append(ctrl.Rule(
            self.fixed_ratio['very_low'] & self.bill_amount['high'],
            self.bill_assessment['concerning']
        ))
        
        # =================================================================
        # SAVINGS POTENTIAL RULES
        # =================================================================
        self.savings_rules = []
        
        # Rule S1: High bill + poor efficiency = very high savings potential
        self.savings_rules.append(ctrl.Rule(
            self.bill_amount['very_high'] & self.efficiency['poor'],
            self.savings_potential['very_high']
        ))
        
        # Rule S2: High bill + average efficiency = high savings potential
        self.savings_rules.append(ctrl.Rule(
            self.bill_amount['high'] & self.efficiency['average'],
            self.savings_potential['high']
        ))
        
        # Rule S3: Much above average = high savings potential
        self.savings_rules.append(ctrl.Rule(
            self.deviation['much_above'],
            self.savings_potential['very_high']
        ))
        
        # Rule S4: Above average = moderate savings potential
        self.savings_rules.append(ctrl.Rule(
            self.deviation['above'],
            self.savings_potential['high']
        ))
        
        # Rule S5: Average deviation with medium efficiency = moderate potential
        self.savings_rules.append(ctrl.Rule(
            self.deviation['average'] & self.efficiency['average'],
            self.savings_potential['moderate']
        ))
        
        # Rule S6: Below average = low savings potential
        self.savings_rules.append(ctrl.Rule(
            self.deviation['below'],
            self.savings_potential['low']
        ))
        
        # Rule S7: Much below average = minimal savings potential
        self.savings_rules.append(ctrl.Rule(
            self.deviation['much_below'],
            self.savings_potential['minimal']
        ))
        
        # Rule S8: Excellent efficiency = minimal savings potential
        self.savings_rules.append(ctrl.Rule(
            self.efficiency['excellent'],
            self.savings_potential['minimal']
        ))
        
        # Rule S9: Very low bill = minimal savings potential
        self.savings_rules.append(ctrl.Rule(
            self.bill_amount['very_low'],
            self.savings_potential['minimal']
        ))
        
        # Rule S10: High consumption + average efficiency = high potential
        self.savings_rules.append(ctrl.Rule(
            self.consumption['very_high'] & self.efficiency['average'],
            self.savings_potential['high']
        ))
        
        # Rule S11: Very high fixed ratio = low savings potential (already efficient/low usage)
        self.savings_rules.append(ctrl.Rule(
            self.fixed_ratio['very_high'],
            self.savings_potential['low']
        ))
        
        # Rule S12: Very low fixed ratio + high bill = high savings potential
        self.savings_rules.append(ctrl.Rule(
            self.fixed_ratio['very_low'] & self.bill_amount['high'],
            self.savings_potential['high']
        ))
        
        # Rule S13: Medium fixed ratio = moderate savings potential
        self.savings_rules.append(ctrl.Rule(
            self.fixed_ratio['medium'],
            self.savings_potential['moderate']
        ))
    
    def _create_control_system(self):
        """Create the fuzzy control systems for bill assessment and savings."""
        # Bill Assessment Control System
        self.bill_ctrl = ctrl.ControlSystem(self.rules)
        self.bill_sim = ctrl.ControlSystemSimulation(self.bill_ctrl)
        
        # Savings Potential Control System
        self.savings_ctrl = ctrl.ControlSystem(self.savings_rules)
        self.savings_sim = ctrl.ControlSystemSimulation(self.savings_ctrl)
    
    def evaluate(
        self,
        bill_amount: float,
        consumption: float,
        deviation: float,
        fixed_ratio: float,
        efficiency: float
    ) -> Dict:
        """
        Evaluate billing data using fuzzy inference.
        
        Args:
            bill_amount: Monthly bill in CHF
            consumption: Monthly consumption in kWh
            deviation: Percentage deviation from average (-100 to +100)
            fixed_ratio: Fixed cost as percentage of total bill
            efficiency: Efficiency score (0-100)
        
        Returns:
            Dictionary with fuzzy evaluation results
        """
        # Clip inputs to valid ranges
        bill_amount = np.clip(bill_amount, 0, 500)
        consumption = np.clip(consumption, 0, 800)
        deviation = np.clip(deviation, -100, 100)
        fixed_ratio = np.clip(fixed_ratio, 0, 30)
        efficiency = np.clip(efficiency, 0, 100)
        
        # Set inputs for bill assessment
        self.bill_sim.input['bill_amount'] = bill_amount
        self.bill_sim.input['consumption'] = consumption
        self.bill_sim.input['deviation'] = deviation
        self.bill_sim.input['fixed_ratio'] = fixed_ratio
        self.bill_sim.input['efficiency'] = efficiency
        
        # Set inputs for savings potential
        self.savings_sim.input['bill_amount'] = bill_amount
        self.savings_sim.input['consumption'] = consumption
        self.savings_sim.input['deviation'] = deviation
        self.savings_sim.input['fixed_ratio'] = fixed_ratio
        self.savings_sim.input['efficiency'] = efficiency
        
        # Compute fuzzy inference
        try:
            self.bill_sim.compute()
            bill_score = self.bill_sim.output['bill_assessment']
        except:
            bill_score = 50  # Default to neutral
        
        try:
            self.savings_sim.compute()
            savings_score = self.savings_sim.output['savings_potential']
        except:
            savings_score = 50  # Default to moderate
        
        # Calculate membership degrees for inputs
        memberships = self._calculate_memberships(
            bill_amount, consumption, deviation, fixed_ratio, efficiency
        )
        
        # Get linguistic terms
        bill_term = self._get_output_term(bill_score, 'bill_assessment')
        savings_term = self._get_output_term(savings_score, 'savings_potential')
        
        # Get active rules
        active_rules = self._get_active_rules(memberships)
        
        return {
            'bill_assessment_score': round(bill_score, 2),
            'bill_assessment_term': bill_term,
            'savings_potential_score': round(savings_score, 2),
            'savings_potential_term': savings_term,
            'memberships': memberships,
            'active_rules': active_rules,
            'inputs': {
                'bill_amount': bill_amount,
                'consumption': consumption,
                'deviation': deviation,
                'fixed_ratio': fixed_ratio,
                'efficiency': efficiency
            }
        }
    
    def _calculate_memberships(
        self,
        bill_amount: float,
        consumption: float,
        deviation: float,
        fixed_ratio: float,
        efficiency: float
    ) -> Dict:
        """Calculate membership degrees for all input variables."""
        memberships = {}
        
        # Bill amount memberships
        memberships['bill_amount'] = {
            'very_low': float(fuzz.interp_membership(self.bill_amount.universe, self.bill_amount['very_low'].mf, bill_amount)),
            'low': float(fuzz.interp_membership(self.bill_amount.universe, self.bill_amount['low'].mf, bill_amount)),
            'medium': float(fuzz.interp_membership(self.bill_amount.universe, self.bill_amount['medium'].mf, bill_amount)),
            'high': float(fuzz.interp_membership(self.bill_amount.universe, self.bill_amount['high'].mf, bill_amount)),
            'very_high': float(fuzz.interp_membership(self.bill_amount.universe, self.bill_amount['very_high'].mf, bill_amount)),
        }
        
        # Consumption memberships
        memberships['consumption'] = {
            'very_low': float(fuzz.interp_membership(self.consumption.universe, self.consumption['very_low'].mf, consumption)),
            'low': float(fuzz.interp_membership(self.consumption.universe, self.consumption['low'].mf, consumption)),
            'medium': float(fuzz.interp_membership(self.consumption.universe, self.consumption['medium'].mf, consumption)),
            'high': float(fuzz.interp_membership(self.consumption.universe, self.consumption['high'].mf, consumption)),
            'very_high': float(fuzz.interp_membership(self.consumption.universe, self.consumption['very_high'].mf, consumption)),
        }
        
        # Deviation memberships
        memberships['deviation'] = {
            'much_below': float(fuzz.interp_membership(self.deviation.universe, self.deviation['much_below'].mf, deviation)),
            'below': float(fuzz.interp_membership(self.deviation.universe, self.deviation['below'].mf, deviation)),
            'average': float(fuzz.interp_membership(self.deviation.universe, self.deviation['average'].mf, deviation)),
            'above': float(fuzz.interp_membership(self.deviation.universe, self.deviation['above'].mf, deviation)),
            'much_above': float(fuzz.interp_membership(self.deviation.universe, self.deviation['much_above'].mf, deviation)),
        }
        
        # Fixed ratio memberships
        memberships['fixed_ratio'] = {
            'very_low': float(fuzz.interp_membership(self.fixed_ratio.universe, self.fixed_ratio['very_low'].mf, fixed_ratio)),
            'low': float(fuzz.interp_membership(self.fixed_ratio.universe, self.fixed_ratio['low'].mf, fixed_ratio)),
            'medium': float(fuzz.interp_membership(self.fixed_ratio.universe, self.fixed_ratio['medium'].mf, fixed_ratio)),
            'high': float(fuzz.interp_membership(self.fixed_ratio.universe, self.fixed_ratio['high'].mf, fixed_ratio)),
            'very_high': float(fuzz.interp_membership(self.fixed_ratio.universe, self.fixed_ratio['very_high'].mf, fixed_ratio)),
        }
        
        # Efficiency memberships
        memberships['efficiency'] = {
            'very_poor': float(fuzz.interp_membership(self.efficiency.universe, self.efficiency['very_poor'].mf, efficiency)),
            'poor': float(fuzz.interp_membership(self.efficiency.universe, self.efficiency['poor'].mf, efficiency)),
            'average': float(fuzz.interp_membership(self.efficiency.universe, self.efficiency['average'].mf, efficiency)),
            'good': float(fuzz.interp_membership(self.efficiency.universe, self.efficiency['good'].mf, efficiency)),
            'excellent': float(fuzz.interp_membership(self.efficiency.universe, self.efficiency['excellent'].mf, efficiency)),
        }
        
        return memberships
    
    def _get_output_term(self, score: float, variable: str) -> str:
        """Get the dominant linguistic term for an output score."""
        if variable == 'bill_assessment':
            if score < 20:
                return 'excellent'
            elif score < 40:
                return 'good'
            elif score < 60:
                return 'normal'
            elif score < 80:
                return 'concerning'
            else:
                return 'critical'
        else:  # savings_potential
            if score < 20:
                return 'minimal'
            elif score < 40:
                return 'low'
            elif score < 60:
                return 'moderate'
            elif score < 80:
                return 'high'
            else:
                return 'very_high'
    
    def _get_active_rules(self, memberships: Dict) -> List[Dict]:
        """Determine which fuzzy rules are currently active based on memberships."""
        active_rules = []
        threshold = 0.3
        
        # Check bill-consumption rules
        for bill_term in ['very_high', 'high', 'medium', 'low', 'very_low']:
            for cons_term in ['very_high', 'high', 'medium', 'low', 'very_low']:
                bill_mem = memberships['bill_amount'].get(bill_term, 0)
                cons_mem = memberships['consumption'].get(cons_term, 0)
                strength = min(bill_mem, cons_mem)
                
                if strength > threshold:
                    active_rules.append({
                        'rule_id': f'BC_{bill_term}_{cons_term}',
                        'rule': f'IF bill is {bill_term.upper()} AND consumption is {cons_term.upper()}',
                        'strength': round(strength, 3),
                        'interpretation': self._get_rule_interpretation(bill_term, cons_term)
                    })
        
        # Check deviation rules
        for dev_term in ['much_above', 'above', 'average', 'below', 'much_below']:
            dev_mem = memberships['deviation'].get(dev_term, 0)
            if dev_mem > threshold:
                active_rules.append({
                    'rule_id': f'DEV_{dev_term}',
                    'rule': f'IF deviation from average is {dev_term.upper()}',
                    'strength': round(dev_mem, 3),
                    'interpretation': self._get_deviation_interpretation(dev_term)
                })
        
        # Check efficiency rules
        for eff_term in ['excellent', 'good', 'average', 'poor', 'very_poor']:
            eff_mem = memberships['efficiency'].get(eff_term, 0)
            if eff_mem > threshold:
                active_rules.append({
                    'rule_id': f'EFF_{eff_term}',
                    'rule': f'IF efficiency is {eff_term.upper()}',
                    'strength': round(eff_mem, 3),
                    'interpretation': self._get_efficiency_interpretation(eff_term)
                })
        
        # Sort by strength
        active_rules.sort(key=lambda x: x['strength'], reverse=True)
        return active_rules[:8]  # Return top 8 active rules
    
    def _get_rule_interpretation(self, bill_term: str, cons_term: str) -> str:
        """Get human-readable interpretation of bill-consumption rule."""
        interpretations = {
            ('very_high', 'very_high'): 'Very high bill with very high consumption indicates urgent need for energy efficiency measures',
            ('very_high', 'high'): 'Very high bill suggests possible inefficiencies or premium rates',
            ('very_high', 'medium'): 'Bill seems high relative to consumption - check your rates',
            ('high', 'high'): 'High usage is driving your elevated bill',
            ('high', 'medium'): 'Bill is somewhat high - there may be optimization opportunities',
            ('medium', 'medium'): 'Your bill is typical for your consumption level',
            ('medium', 'high'): 'Good value - reasonable bill for your consumption',
            ('low', 'low'): 'Low consumption keeping your bill manageable',
            ('low', 'medium'): 'Excellent efficiency - getting good value',
            ('very_low', 'very_low'): 'Minimal consumption resulting in very low bill',
            ('very_low', 'low'): 'Very efficient energy usage pattern',
        }
        return interpretations.get((bill_term, cons_term), 'Standard billing pattern detected')
    
    def _get_deviation_interpretation(self, dev_term: str) -> str:
        """Get interpretation for deviation from average."""
        interpretations = {
            'much_above': 'Your bill is significantly above average for similar households - high savings potential',
            'above': 'Your bill is above average - some room for improvement',
            'average': 'Your bill is typical for households like yours',
            'below': 'Your bill is below average - you are doing well',
            'much_below': 'Excellent! Your bill is significantly below average'
        }
        return interpretations.get(dev_term, '')
    
    def _get_efficiency_interpretation(self, eff_term: str) -> str:
        """Get interpretation for efficiency level."""
        interpretations = {
            'excellent': 'Your energy efficiency is excellent - minimal waste',
            'good': 'Good energy efficiency - keep up the good habits',
            'average': 'Average efficiency - some optimization possible',
            'poor': 'Below average efficiency - consider energy audit',
            'very_poor': 'Significant efficiency issues detected - immediate action recommended'
        }
        return interpretations.get(eff_term, '')
    
    def get_membership_data(self, variable: str) -> Dict:
        """Get membership function data for visualization."""
        var_map = {
            'bill_amount': self.bill_amount,
            'consumption': self.consumption,
            'deviation': self.deviation,
            'fixed_ratio': self.fixed_ratio,
            'efficiency': self.efficiency,
            'bill_assessment': self.bill_assessment,
            'savings_potential': self.savings_potential
        }
        
        if variable not in var_map:
            return {}
        
        var = var_map[variable]
        data = {'universe': var.universe.tolist()}
        
        for term in var.terms:
            data[term] = var[term].mf.tolist()
        
        return data
    
    def generate_fuzzy_rules_summary(self) -> str:
        """Generate a markdown summary of all fuzzy rules."""
        summary = """
## 📋 Fuzzy Billing Rules Summary

### Bill Assessment Rules (Mamdani Inference)

**Rule Group 1: Bill-Consumption Relationship**
| Rule | IF | THEN |
|------|-----|------|
| R1 | Bill is VERY_HIGH AND Consumption is VERY_HIGH | Assessment is CRITICAL |
| R2 | Bill is HIGH AND Consumption is HIGH | Assessment is CONCERNING |
| R3 | Bill is MEDIUM AND Consumption is MEDIUM | Assessment is NORMAL |
| R4 | Bill is LOW AND Consumption is LOW | Assessment is GOOD |
| R5 | Bill is VERY_LOW | Assessment is EXCELLENT |

**Rule Group 2: Deviation from Average**
| Rule | IF | THEN |
|------|-----|------|
| R6 | Deviation is MUCH_ABOVE | Assessment is CRITICAL |
| R7 | Deviation is ABOVE | Assessment is CONCERNING |
| R8 | Deviation is AVERAGE | Assessment is NORMAL |
| R9 | Deviation is BELOW | Assessment is GOOD |
| R10 | Deviation is MUCH_BELOW | Assessment is EXCELLENT |

**Rule Group 3: Efficiency Assessment**
| Rule | IF | THEN |
|------|-----|------|
| R11 | Efficiency is VERY_POOR | Assessment is CRITICAL |
| R12 | Efficiency is POOR AND Bill is HIGH | Assessment is CRITICAL |
| R13 | Efficiency is AVERAGE | Assessment is NORMAL |
| R14 | Efficiency is GOOD | Assessment is GOOD |
| R15 | Efficiency is EXCELLENT | Assessment is EXCELLENT |

### Savings Potential Rules

| Rule | IF | THEN |
|------|-----|------|
| S1 | Bill is VERY_HIGH AND Efficiency is POOR | Savings is VERY_HIGH |
| S2 | Bill is HIGH AND Efficiency is AVERAGE | Savings is HIGH |
| S3 | Deviation is MUCH_ABOVE | Savings is VERY_HIGH |
| S4 | Deviation is ABOVE | Savings is HIGH |
| S5 | Deviation is AVERAGE AND Efficiency is AVERAGE | Savings is MODERATE |
| S6 | Deviation is BELOW | Savings is LOW |
| S7 | Deviation is MUCH_BELOW | Savings is MINIMAL |
| S8 | Efficiency is EXCELLENT | Savings is MINIMAL |
| S9 | Bill is VERY_LOW | Savings is MINIMAL |
| S10 | Consumption is VERY_HIGH AND Efficiency is AVERAGE | Savings is HIGH |

### Fuzzy Operations
- **AND**: Minimum operator (min)
- **OR**: Maximum operator (max)
- **Defuzzification**: Centroid method
"""
        return summary
    
    def generate_linguistic_explanation(self, evaluation: Dict) -> str:
        """Generate natural language explanation from fuzzy evaluation."""
        bill_term = evaluation['bill_assessment_term']
        bill_score = evaluation['bill_assessment_score']
        savings_term = evaluation['savings_potential_term']
        savings_score = evaluation['savings_potential_score']
        inputs = evaluation['inputs']
        
        # Main assessment
        assessment_text = {
            'excellent': '🌟 **Excellent!** Your electricity bill is very well managed.',
            'good': '✅ **Good job!** Your bill is below average and well-controlled.',
            'normal': '📊 **Normal Range.** Your bill is typical for your household type.',
            'concerning': '⚠️ **Attention Needed.** Your bill is higher than expected.',
            'critical': '🔴 **Action Required!** Your bill is significantly above average.'
        }
        
        savings_text = {
            'minimal': 'There is minimal room for further savings - you are already efficient.',
            'low': 'Small optimizations could yield modest savings.',
            'moderate': 'There is moderate potential for savings through efficiency improvements.',
            'high': 'Significant savings are possible with the right changes.',
            'very_high': 'Major savings potential exists - consider an energy audit.'
        }
        
        explanation = f"""
### 🎯 Fuzzy Bill Assessment

{assessment_text.get(bill_term, 'Assessment in progress...')}

**Fuzzy Output Scores:**
- Bill Assessment: **{bill_score:.1f}/100** ({bill_term.upper()})
- Savings Potential: **{savings_score:.1f}/100** ({savings_term.upper()})

### 💡 Savings Analysis

{savings_text.get(savings_term, 'Analysis in progress...')}

### 📊 Input Fuzzification

Based on your inputs:
- **Bill Amount**: CHF {inputs['bill_amount']:.2f} → Fuzzified across membership functions
- **Consumption**: {inputs['consumption']:.0f} kWh → Determines usage category
- **Deviation**: {inputs['deviation']:+.1f}% → Comparison with average
- **Efficiency Score**: {inputs['efficiency']:.0f}/100 → Energy utilization rating

### 🔄 Active Fuzzy Rules

The following rules are currently influencing the assessment:
"""
        
        for rule in evaluation['active_rules'][:5]:
            explanation += f"\n- **{rule['rule']}** (Strength: {rule['strength']:.2f})\n  *{rule['interpretation']}*"
        
        return explanation


class FuzzyBillingExplainer:
    """
    High-level interface for fuzzy billing explanations.
    Integrates with the BillingAnalyzer for comprehensive analysis.
    """
    
    def __init__(self):
        self.fuzzy_system = FuzzyBillingSystem()
    
    def analyze_with_fuzzy(self, billing_analysis: Dict) -> Dict:
        """
        Perform fuzzy analysis on billing data.
        
        Args:
            billing_analysis: Output from BillingAnalyzer.analyze_bill()
        
        Returns:
            Dictionary with fuzzy evaluation and explanations
        """
        # Extract values from billing analysis
        bill_amount = billing_analysis.get('total_bill', 0)
        consumption = billing_analysis.get('estimated_kwh', 0)
        deviation = billing_analysis.get('diff_bill_pct', 0)
        fixed_ratio = billing_analysis.get('pct_fixed', 0)
        
        # Calculate efficiency score
        avg_chf_per_kwh = billing_analysis.get('avg_chf_per_kwh', 0.28)
        swiss_avg_rate = 0.28  # CHF/kWh
        if avg_chf_per_kwh > 0:
            # Higher rate = lower efficiency
            efficiency = max(0, min(100, (swiss_avg_rate / avg_chf_per_kwh) * 70))
        else:
            efficiency = 50
        
        # Run fuzzy evaluation
        fuzzy_eval = self.fuzzy_system.evaluate(
            bill_amount=bill_amount,
            consumption=consumption,
            deviation=deviation,
            fixed_ratio=fixed_ratio,
            efficiency=efficiency
        )
        
        # Generate explanation
        explanation = self.fuzzy_system.generate_linguistic_explanation(fuzzy_eval)
        
        return {
            'fuzzy_evaluation': fuzzy_eval,
            'explanation': explanation,
            'efficiency_score': efficiency
        }
    
    def get_membership_visualization_data(self, variable: str) -> Dict:
        """Get membership function data for visualization."""
        return self.fuzzy_system.get_membership_data(variable)
    
    def get_color_for_assessment(self, term: str) -> str:
        """Get color code for assessment term."""
        colors = {
            'excellent': 'green',
            'good': 'blue',
            'normal': 'orange',
            'concerning': 'orange',
            'critical': 'red',
            'minimal': 'green',
            'low': 'blue',
            'moderate': 'orange',
            'high': 'orange',
            'very_high': 'red'
        }
        return colors.get(term, 'gray')
    
    def generate_fuzzy_rules_summary(self) -> str:
        """Generate summary of fuzzy rules."""
        return self.fuzzy_system.generate_fuzzy_rules_summary()
