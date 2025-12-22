"""
=============================================================================
FUZZY LOGIC EXPLAINABILITY MODULE - CORE COMPONENT
=============================================================================

This module implements a comprehensive Fuzzy Inference System (FIS) for 
energy price and consumption analysis. It is the MAIN component of the 
explainability dashboard, providing human-understandable linguistic 
explanations using fuzzy logic principles.

Key Components:
1. Membership Functions - Triangular/Trapezoidal fuzzy sets
2. Fuzzy Variables - Price, Consumption, Time of Day, Volatility, Trend
3. Fuzzy Rule Engine - IF-THEN inference rules (Mamdani approach)
4. Defuzzification - Centroid method for crisp output
5. Linguistic Reasoning - Natural language generation

Theory Reference:
- Zadeh, L.A. (1965). Fuzzy Sets. Information and Control, 8(3), 338-353.
- Mamdani, E.H. (1974). Application of Fuzzy Algorithms for Control of 
  Simple Dynamic Plant. Proceedings of IEE, 121(12), 1585-1588.

Author: Energy Explainability Research Project
=============================================================================
"""

import numpy as np
import pandas as pd
import skfuzzy as fuzz
from skfuzzy import control as ctrl


# =============================================================================
# FUZZY ENERGY INFERENCE SYSTEM (FIS) - MAIN CLASS
# =============================================================================

class FuzzyEnergySystem:
    """
    Complete Fuzzy Inference System (FIS) for energy market analysis.
    
    This class implements a Mamdani-type fuzzy inference system with:
    - 5 input variables (price, consumption, hour, volatility, trend)
    - 2 output variables (market_condition, recommendation)
    - 30+ fuzzy rules for comprehensive market analysis
    
    The system provides transparent, explainable insights that are 
    more intuitive than traditional numerical methods.
    
    Fuzzy Logic Advantages:
    1. Handles uncertainty and imprecision naturally
    2. Rules are human-readable (IF-THEN format)
    3. Gradual transitions between categories (no sharp boundaries)
    4. Mimics human expert reasoning
    """
    
    def __init__(self):
        """Initialize the Fuzzy Inference System with all variables and rules."""
        self._setup_fuzzy_variables()
        self._setup_fuzzy_rules()
        self._create_control_system()
    
    def _setup_fuzzy_variables(self):
        """
        Define fuzzy variables with triangular/trapezoidal membership functions.
        
        Membership Function Types:
        - Triangular (trimf): 3 points [a, b, c] - peak at b
        - Trapezoidal (trapmf): 4 points [a, b, c, d] - flat top between b and c
        
        Each variable has 5 linguistic terms (fuzzy sets):
        - Very Low, Low, Medium, High, Very High
        """
        # =====================================================================
        # INPUT VARIABLE 1: PRICE (€/MWh)
        # Universe: 0-200 €/MWh (covers typical European spot prices)
        # =====================================================================
        self.price = ctrl.Antecedent(np.arange(0, 201, 1), 'price')
        
        # Membership functions with overlapping regions for smooth transitions
        self.price['very_low'] = fuzz.trapmf(self.price.universe, [0, 0, 20, 40])
        self.price['low'] = fuzz.trimf(self.price.universe, [20, 45, 70])
        self.price['medium'] = fuzz.trimf(self.price.universe, [50, 80, 110])
        self.price['high'] = fuzz.trimf(self.price.universe, [90, 120, 150])
        self.price['very_high'] = fuzz.trapmf(self.price.universe, [130, 160, 200, 200])
        
        # =====================================================================
        # INPUT VARIABLE 2: CONSUMPTION (Normalized 0-100%)
        # Universe: 0-100 (percentage of maximum capacity)
        # =====================================================================
        self.consumption = ctrl.Antecedent(np.arange(0, 101, 1), 'consumption')
        
        self.consumption['very_low'] = fuzz.trapmf(self.consumption.universe, [0, 0, 15, 30])
        self.consumption['low'] = fuzz.trimf(self.consumption.universe, [15, 35, 55])
        self.consumption['medium'] = fuzz.trimf(self.consumption.universe, [40, 55, 70])
        self.consumption['high'] = fuzz.trimf(self.consumption.universe, [55, 75, 90])
        self.consumption['very_high'] = fuzz.trapmf(self.consumption.universe, [80, 90, 100, 100])
        
        # =====================================================================
        # INPUT VARIABLE 3: HOUR OF DAY
        # Universe: 0-23 hours
        # Terms: Night, Early Morning, Morning Peak, Afternoon, Evening Peak
        # =====================================================================
        self.hour = ctrl.Antecedent(np.arange(0, 24, 1), 'hour')
        
        self.hour['night'] = fuzz.trapmf(self.hour.universe, [0, 0, 4, 6])
        self.hour['early_morning'] = fuzz.trimf(self.hour.universe, [5, 7, 9])
        self.hour['morning_peak'] = fuzz.trimf(self.hour.universe, [7, 9, 12])
        self.hour['afternoon'] = fuzz.trimf(self.hour.universe, [11, 14, 17])
        self.hour['evening_peak'] = fuzz.trimf(self.hour.universe, [17, 20, 23])
        
        # =====================================================================
        # INPUT VARIABLE 4: PRICE VOLATILITY (Standard Deviation)
        # Universe: 0-50 €/MWh
        # =====================================================================
        self.volatility = ctrl.Antecedent(np.arange(0, 51, 1), 'volatility')
        
        self.volatility['very_low'] = fuzz.trapmf(self.volatility.universe, [0, 0, 3, 8])
        self.volatility['low'] = fuzz.trimf(self.volatility.universe, [5, 10, 15])
        self.volatility['medium'] = fuzz.trimf(self.volatility.universe, [12, 18, 25])
        self.volatility['high'] = fuzz.trimf(self.volatility.universe, [20, 30, 40])
        self.volatility['very_high'] = fuzz.trapmf(self.volatility.universe, [35, 45, 50, 50])
        
        # =====================================================================
        # INPUT VARIABLE 5: PRICE TREND (Percentage change over 24h)
        # Universe: -50% to +50%
        # =====================================================================
        self.trend = ctrl.Antecedent(np.arange(-50, 51, 1), 'trend')
        
        self.trend['falling_fast'] = fuzz.trapmf(self.trend.universe, [-50, -50, -30, -15])
        self.trend['falling'] = fuzz.trimf(self.trend.universe, [-25, -12, 0])
        self.trend['stable'] = fuzz.trimf(self.trend.universe, [-8, 0, 8])
        self.trend['rising'] = fuzz.trimf(self.trend.universe, [0, 12, 25])
        self.trend['rising_fast'] = fuzz.trapmf(self.trend.universe, [15, 30, 50, 50])
        
        # =====================================================================
        # OUTPUT VARIABLE 1: MARKET CONDITION
        # Universe: 0-100 (0=Very Favorable, 100=Very Unfavorable)
        # =====================================================================
        self.market_condition = ctrl.Consequent(np.arange(0, 101, 1), 'market_condition')
        
        self.market_condition['very_favorable'] = fuzz.trapmf(self.market_condition.universe, [0, 0, 10, 25])
        self.market_condition['favorable'] = fuzz.trimf(self.market_condition.universe, [15, 30, 45])
        self.market_condition['neutral'] = fuzz.trimf(self.market_condition.universe, [35, 50, 65])
        self.market_condition['unfavorable'] = fuzz.trimf(self.market_condition.universe, [55, 70, 85])
        self.market_condition['very_unfavorable'] = fuzz.trapmf(self.market_condition.universe, [75, 90, 100, 100])
        
        # =====================================================================
        # OUTPUT VARIABLE 2: CONSUMPTION RECOMMENDATION
        # Universe: 0-100 (0=Avoid consumption, 100=Optimal time)
        # =====================================================================
        self.recommendation = ctrl.Consequent(np.arange(0, 101, 1), 'recommendation')
        
        self.recommendation['avoid'] = fuzz.trapmf(self.recommendation.universe, [0, 0, 10, 25])
        self.recommendation['reduce'] = fuzz.trimf(self.recommendation.universe, [15, 30, 45])
        self.recommendation['normal'] = fuzz.trimf(self.recommendation.universe, [35, 50, 65])
        self.recommendation['increase'] = fuzz.trimf(self.recommendation.universe, [55, 70, 85])
        self.recommendation['optimal'] = fuzz.trapmf(self.recommendation.universe, [75, 90, 100, 100])
    
    def _setup_fuzzy_rules(self):
        """
        Define fuzzy IF-THEN rules using Mamdani inference method.
        
        Rule Format: IF (antecedent) THEN (consequent)
        Fuzzy Operations:
        - AND: Minimum (min) operator
        - OR: Maximum (max) operator
        
        Rules are based on energy market domain knowledge:
        - High demand + High price = Unfavorable market
        - Low demand + Low price = Favorable market  
        - Peak hours typically have higher prices
        - High volatility increases market risk
        """
        self.rules = []
        
        # =================================================================
        # RULE GROUP 1: Price-Consumption Interaction Rules (Core Rules)
        # These rules capture the supply-demand dynamics
        # =================================================================
        
        # Rule 1: Peak demand crisis
        self.rules.append(ctrl.Rule(
            self.price['very_high'] & self.consumption['very_high'],
            self.market_condition['very_unfavorable']
        ))
        
        # Rule 2: High stress on grid
        self.rules.append(ctrl.Rule(
            self.price['high'] & self.consumption['high'],
            self.market_condition['unfavorable']
        ))
        
        # Rule 3: Balanced market
        self.rules.append(ctrl.Rule(
            self.price['medium'] & self.consumption['medium'],
            self.market_condition['neutral']
        ))
        
        # Rule 4: Good market conditions
        self.rules.append(ctrl.Rule(
            self.price['low'] & self.consumption['low'],
            self.market_condition['favorable']
        ))
        
        # Rule 5: Optimal off-peak conditions
        self.rules.append(ctrl.Rule(
            self.price['very_low'] & self.consumption['very_low'],
            self.market_condition['very_favorable']
        ))
        
        # =================================================================
        # RULE GROUP 2: Supply Constraint Scenarios
        # High prices with low demand indicate supply issues
        # =================================================================
        
        # Rule 6: Supply crisis (high price despite low demand)
        self.rules.append(ctrl.Rule(
            self.price['very_high'] & self.consumption['low'],
            self.market_condition['unfavorable']
        ))
        
        # Rule 7: Generation shortage
        self.rules.append(ctrl.Rule(
            self.price['high'] & self.consumption['very_low'],
            self.market_condition['unfavorable']
        ))
        
        # =================================================================
        # RULE GROUP 3: Renewable Surplus Scenarios
        # Low prices with high demand indicate abundant supply
        # =================================================================
        
        # Rule 8: Renewable energy surplus (wind/solar abundance)
        self.rules.append(ctrl.Rule(
            self.price['very_low'] & self.consumption['high'],
            self.market_condition['very_favorable']
        ))
        
        # Rule 9: Good supply situation
        self.rules.append(ctrl.Rule(
            self.price['low'] & self.consumption['very_high'],
            self.market_condition['favorable']
        ))
        
        # =================================================================
        # RULE GROUP 4: Time-of-Day Rules
        # Account for typical daily price patterns
        # =================================================================
        
        # Rule 10: Night hours advantage
        self.rules.append(ctrl.Rule(
            self.hour['night'] & self.price['low'],
            self.market_condition['very_favorable']
        ))
        
        # Rule 11: Morning peak stress
        self.rules.append(ctrl.Rule(
            self.hour['morning_peak'] & self.price['high'],
            self.market_condition['unfavorable']
        ))
        
        # Rule 12: Evening peak crisis
        self.rules.append(ctrl.Rule(
            self.hour['evening_peak'] & self.price['very_high'],
            self.market_condition['very_unfavorable']
        ))
        
        # Rule 13: Afternoon normal
        self.rules.append(ctrl.Rule(
            self.hour['afternoon'] & self.price['medium'],
            self.market_condition['neutral']
        ))
        
        # =================================================================
        # RULE GROUP 5: Volatility Impact Rules
        # High volatility increases market uncertainty/risk
        # =================================================================
        
        # Rule 14: High volatility + high price = very bad
        self.rules.append(ctrl.Rule(
            self.volatility['very_high'] & self.price['high'],
            self.market_condition['very_unfavorable']
        ))
        
        # Rule 15: Rising volatility with rising trend
        self.rules.append(ctrl.Rule(
            self.volatility['high'] & self.trend['rising_fast'],
            self.market_condition['unfavorable']
        ))
        
        # Rule 16: Stable market conditions
        self.rules.append(ctrl.Rule(
            self.volatility['low'] & self.trend['stable'],
            self.market_condition['favorable']
        ))
        
        # Rule 17: Very stable with low prices
        self.rules.append(ctrl.Rule(
            self.volatility['very_low'] & self.price['low'],
            self.market_condition['very_favorable']
        ))
        
        # =================================================================
        # RULE GROUP 6: Trend-Based Rules
        # Price direction matters for decision-making
        # =================================================================
        
        # Rule 18: Prices falling from high = improving
        self.rules.append(ctrl.Rule(
            self.trend['falling_fast'] & self.price['high'],
            self.market_condition['neutral']
        ))
        
        # Rule 19: Prices rising from low = worsening
        self.rules.append(ctrl.Rule(
            self.trend['rising_fast'] & self.price['low'],
            self.market_condition['neutral']
        ))
        
        # Rule 20: Stable trend with medium price
        self.rules.append(ctrl.Rule(
            self.trend['stable'] & self.price['medium'],
            self.market_condition['neutral']
        ))
        
        # =================================================================
        # RECOMMENDATION RULES - When to consume energy
        # =================================================================
        self.recommendation_rules = []
        
        # Rule R1: Night + low price = optimal
        self.recommendation_rules.append(ctrl.Rule(
            self.price['very_low'] & self.hour['night'],
            self.recommendation['optimal']
        ))
        
        # Rule R2: Low price + low demand = optimal
        self.recommendation_rules.append(ctrl.Rule(
            self.price['low'] & self.consumption['low'],
            self.recommendation['optimal']
        ))
        
        # Rule R3: Evening peak + very high price = avoid
        self.recommendation_rules.append(ctrl.Rule(
            self.price['very_high'] & self.hour['evening_peak'],
            self.recommendation['avoid']
        ))
        
        # Rule R4: Morning peak + high price = reduce
        self.recommendation_rules.append(ctrl.Rule(
            self.price['high'] & self.hour['morning_peak'],
            self.recommendation['reduce']
        ))
        
        # Rule R5: Afternoon + medium price = normal
        self.recommendation_rules.append(ctrl.Rule(
            self.price['medium'] & self.hour['afternoon'],
            self.recommendation['normal']
        ))
        
        # Rule R6: Medium price + medium consumption = normal
        self.recommendation_rules.append(ctrl.Rule(
            self.price['medium'] & self.consumption['medium'],
            self.recommendation['normal']
        ))
        
        # Rule R7: Low price + low volatility = increase
        self.recommendation_rules.append(ctrl.Rule(
            self.price['low'] & self.volatility['low'],
            self.recommendation['increase']
        ))
        
        # Rule R8: Very low price + falling trend = optimal
        self.recommendation_rules.append(ctrl.Rule(
            self.price['very_low'] & self.trend['falling'],
            self.recommendation['optimal']
        ))
    
    def _create_control_system(self):
        """
        Create the fuzzy control system for inference.
        
        Uses Mamdani inference with:
        - AND operator: minimum
        - OR operator: maximum
        - Implication: minimum
        - Aggregation: maximum
        - Defuzzification: centroid
        """
        try:
            # Market condition control system
            self.market_ctrl = ctrl.ControlSystem(self.rules)
            self.market_sim = ctrl.ControlSystemSimulation(self.market_ctrl)
            
            # Recommendation control system
            self.rec_ctrl = ctrl.ControlSystem(self.recommendation_rules)
            self.rec_sim = ctrl.ControlSystemSimulation(self.rec_ctrl)
            
            self.system_ready = True
        except Exception as e:
            print(f"Warning: Could not create control system: {e}")
            self.market_sim = None
            self.rec_sim = None
            self.system_ready = False
    
    def evaluate(self, price_value, consumption_value, hour_value, 
                 volatility_value=10, trend_value=0):
        """
        Evaluate the fuzzy inference system with given inputs.
        
        This is the core fuzzy reasoning function that:
        1. Fuzzifies inputs (calculates membership degrees)
        2. Applies fuzzy rules (IF-THEN inference)
        3. Aggregates rule outputs
        4. Defuzzifies to get crisp output
        
        Args:
            price_value: Current price in €/MWh (0-200)
            consumption_value: Normalized consumption (0-100)
            hour_value: Hour of day (0-23)
            volatility_value: Price standard deviation (0-50)
            trend_value: 24h price change percentage (-50 to +50)
        
        Returns:
            dict with fuzzy outputs, membership degrees, and active rules
        """
        results = {
            'market_condition': 50,
            'recommendation': 50,
            'memberships': {},
            'active_rules': [],
            'defuzzified_outputs': {}
        }
        
        # Clip values to valid universe ranges
        price_value = np.clip(float(price_value), 0, 200)
        consumption_value = np.clip(float(consumption_value), 0, 100)
        hour_value = np.clip(int(hour_value), 0, 23)
        volatility_value = np.clip(float(volatility_value), 0, 50)
        trend_value = np.clip(float(trend_value), -50, 50)
        
        # =================================================================
        # STEP 1: FUZZIFICATION - Calculate membership degrees
        # =================================================================
        results['memberships'] = {
            'price': self._get_membership_degrees(self.price, price_value),
            'consumption': self._get_membership_degrees(self.consumption, consumption_value),
            'hour': self._get_membership_degrees(self.hour, hour_value),
            'volatility': self._get_membership_degrees(self.volatility, volatility_value),
            'trend': self._get_membership_degrees(self.trend, trend_value)
        }
        
        # =================================================================
        # STEP 2-4: INFERENCE AND DEFUZZIFICATION
        # =================================================================
        if self.market_sim is not None:
            try:
                # Set inputs
                self.market_sim.input['price'] = price_value
                self.market_sim.input['consumption'] = consumption_value
                self.market_sim.input['hour'] = hour_value
                self.market_sim.input['volatility'] = volatility_value
                self.market_sim.input['trend'] = trend_value
                
                # Compute (applies rules and defuzzifies)
                self.market_sim.compute()
                results['market_condition'] = float(self.market_sim.output['market_condition'])
            except Exception:
                results['market_condition'] = self._fallback_market_condition(
                    price_value, consumption_value, volatility_value
                )
        else:
            results['market_condition'] = self._fallback_market_condition(
                price_value, consumption_value, volatility_value
            )
        
        # Recommendation inference
        if self.rec_sim is not None:
            try:
                self.rec_sim.input['price'] = price_value
                self.rec_sim.input['consumption'] = consumption_value
                self.rec_sim.input['hour'] = hour_value
                self.rec_sim.input['volatility'] = volatility_value
                self.rec_sim.input['trend'] = trend_value
                self.rec_sim.compute()
                results['recommendation'] = float(self.rec_sim.output['recommendation'])
            except Exception:
                results['recommendation'] = self._fallback_recommendation(price_value, hour_value)
        else:
            results['recommendation'] = self._fallback_recommendation(price_value, hour_value)
        
        # =================================================================
        # STEP 5: Identify active rules for explanation
        # =================================================================
        results['active_rules'] = self._get_active_rules(results['memberships'])
        
        return results
    
    def _get_membership_degrees(self, variable, value):
        """
        Calculate membership degrees for all fuzzy sets of a variable.
        
        This is the fuzzification step - converting crisp input to 
        fuzzy membership values.
        
        Returns:
            dict: {term_name: membership_degree} for all terms
        """
        memberships = {}
        for term in variable.terms:
            degree = fuzz.interp_membership(
                variable.universe, 
                variable[term].mf, 
                value
            )
            memberships[term] = float(degree)
        return memberships
    
    def _fallback_market_condition(self, price, consumption, volatility):
        """Fallback when fuzzy control system unavailable."""
        price_score = (price / 200) * 100
        consumption_score = consumption
        volatility_score = (volatility / 50) * 100
        return 0.5 * price_score + 0.3 * consumption_score + 0.2 * volatility_score
    
    def _fallback_recommendation(self, price, hour):
        """Fallback recommendation calculation."""
        is_peak = (7 <= hour <= 9) or (18 <= hour <= 21)
        is_night = (1 <= hour <= 5)
        
        if is_night and price < 50:
            return 90
        elif is_peak and price > 100:
            return 20
        else:
            return 50 + (100 - price) / 4
    
    def _get_active_rules(self, memberships):
        """
        Determine which fuzzy rules are currently firing.
        
        A rule is considered "active" if its antecedent has 
        membership degree > 0.3 (firing threshold).
        """
        active = []
        threshold = 0.3
        
        price_m = memberships['price']
        cons_m = memberships['consumption']
        vol_m = memberships['volatility']
        trend_m = memberships['trend']
        hour_m = memberships['hour']
        
        # Check Price-Consumption rules
        if price_m.get('very_high', 0) > threshold and cons_m.get('very_high', 0) > threshold:
            active.append({
                'rule_id': 1,
                'rule': 'IF price is VERY_HIGH AND consumption is VERY_HIGH THEN market is VERY_UNFAVORABLE',
                'strength': min(price_m['very_high'], cons_m['very_high']),
                'interpretation': '🔥 Peak demand crisis - Grid under maximum stress'
            })
        
        if price_m.get('very_low', 0) > threshold and cons_m.get('very_low', 0) > threshold:
            active.append({
                'rule_id': 5,
                'rule': 'IF price is VERY_LOW AND consumption is VERY_LOW THEN market is VERY_FAVORABLE',
                'strength': min(price_m['very_low'], cons_m['very_low']),
                'interpretation': '🌙 Off-peak period - Optimal time for consumption'
            })
        
        if price_m.get('very_low', 0) > threshold and cons_m.get('high', 0) > threshold:
            active.append({
                'rule_id': 8,
                'rule': 'IF price is VERY_LOW AND consumption is HIGH THEN market is VERY_FAVORABLE',
                'strength': min(price_m['very_low'], cons_m['high']),
                'interpretation': '🌱 Renewable surplus - Wind/solar abundance'
            })
        
        if price_m.get('high', 0) > threshold and cons_m.get('low', 0) > threshold:
            active.append({
                'rule_id': 7,
                'rule': 'IF price is HIGH AND consumption is LOW THEN market is UNFAVORABLE',
                'strength': min(price_m['high'], cons_m['low']),
                'interpretation': '⚡ Supply constraint - Generation shortage or fuel scarcity'
            })
        
        # Volatility rules
        if vol_m.get('very_high', 0) > threshold:
            active.append({
                'rule_id': 14,
                'rule': 'IF volatility is VERY_HIGH THEN market_stability is LOW',
                'strength': vol_m['very_high'],
                'interpretation': '📊 High volatility - Unstable market conditions'
            })
        
        # Trend rules
        if trend_m.get('rising_fast', 0) > threshold:
            active.append({
                'rule_id': 15,
                'rule': 'IF trend is RISING_FAST THEN prices are INCREASING',
                'strength': trend_m['rising_fast'],
                'interpretation': '📈 Rapid price increase - Consider postponing consumption'
            })
        
        if trend_m.get('falling_fast', 0) > threshold:
            active.append({
                'rule_id': 18,
                'rule': 'IF trend is FALLING_FAST THEN prices are DECREASING',
                'strength': trend_m['falling_fast'],
                'interpretation': '📉 Rapid price decrease - Good time for energy-intensive tasks'
            })
        
        # Time-of-day rules
        if hour_m.get('night', 0) > threshold and price_m.get('low', 0) > threshold:
            active.append({
                'rule_id': 10,
                'rule': 'IF hour is NIGHT AND price is LOW THEN market is VERY_FAVORABLE',
                'strength': min(hour_m['night'], price_m['low']),
                'interpretation': '🌙 Night advantage - Lowest demand period'
            })
        
        if hour_m.get('evening_peak', 0) > threshold and price_m.get('very_high', 0) > threshold:
            active.append({
                'rule_id': 12,
                'rule': 'IF hour is EVENING_PEAK AND price is VERY_HIGH THEN market is VERY_UNFAVORABLE',
                'strength': min(hour_m['evening_peak'], price_m['very_high']),
                'interpretation': '🔴 Evening peak crisis - Maximum residential demand'
            })
        
        # Sort by strength (highest first)
        active.sort(key=lambda x: x['strength'], reverse=True)
        
        return active
    
    def get_membership_plot_data(self, variable_name):
        """
        Get data for plotting membership functions.
        
        Used for visualization in the dashboard.
        """
        variable_map = {
            'price': self.price,
            'consumption': self.consumption,
            'hour': self.hour,
            'volatility': self.volatility,
            'trend': self.trend,
            'market_condition': self.market_condition,
            'recommendation': self.recommendation
        }
        
        if variable_name not in variable_map:
            return None
        
        var = variable_map[variable_name]
        data = {'universe': var.universe.tolist()}
        
        for term in var.terms:
            data[term] = var[term].mf.tolist()
        
        return data
    
    def get_all_rules_summary(self):
        """Return formatted summary of all fuzzy rules."""
        return {
            'market_rules': len(self.rules),
            'recommendation_rules': len(self.recommendation_rules),
            'total_rules': len(self.rules) + len(self.recommendation_rules),
            'input_variables': ['price', 'consumption', 'hour', 'volatility', 'trend'],
            'output_variables': ['market_condition', 'recommendation']
        }


# =============================================================================
# FUZZY BILL ANALYZER
# =============================================================================

class FuzzyBillAnalyzer:
    """
    Fuzzy logic-based electricity bill analyzer.
    
    Uses fuzzy inference to evaluate bill efficiency and provide
    linguistic assessments of energy costs.
    """
    
    def __init__(self):
        """Initialize fuzzy bill analysis system."""
        self._setup_fuzzy_variables()
        self._setup_rules()
    
    def _setup_fuzzy_variables(self):
        """Define fuzzy variables for bill analysis."""
        # Bill amount (CHF) - Swiss context
        self.bill = ctrl.Antecedent(np.arange(0, 501, 1), 'bill')
        self.bill['very_low'] = fuzz.trapmf(self.bill.universe, [0, 0, 30, 60])
        self.bill['low'] = fuzz.trimf(self.bill.universe, [40, 80, 120])
        self.bill['medium'] = fuzz.trimf(self.bill.universe, [100, 150, 200])
        self.bill['high'] = fuzz.trimf(self.bill.universe, [180, 250, 350])
        self.bill['very_high'] = fuzz.trapmf(self.bill.universe, [300, 400, 500, 500])
        
        # Consumption (kWh per month)
        self.kwh = ctrl.Antecedent(np.arange(0, 1001, 1), 'kwh')
        self.kwh['very_low'] = fuzz.trapmf(self.kwh.universe, [0, 0, 100, 200])
        self.kwh['low'] = fuzz.trimf(self.kwh.universe, [150, 250, 350])
        self.kwh['medium'] = fuzz.trimf(self.kwh.universe, [300, 400, 550])
        self.kwh['high'] = fuzz.trimf(self.kwh.universe, [500, 650, 800])
        self.kwh['very_high'] = fuzz.trapmf(self.kwh.universe, [750, 900, 1000, 1000])
        
        # Efficiency score output (0-100)
        self.efficiency = ctrl.Consequent(np.arange(0, 101, 1), 'efficiency')
        self.efficiency['very_poor'] = fuzz.trapmf(self.efficiency.universe, [0, 0, 10, 25])
        self.efficiency['poor'] = fuzz.trimf(self.efficiency.universe, [15, 30, 45])
        self.efficiency['average'] = fuzz.trimf(self.efficiency.universe, [35, 50, 65])
        self.efficiency['good'] = fuzz.trimf(self.efficiency.universe, [55, 70, 85])
        self.efficiency['excellent'] = fuzz.trapmf(self.efficiency.universe, [75, 90, 100, 100])
    
    def _setup_rules(self):
        """Define fuzzy rules for bill efficiency analysis."""
        self.rules = [
            # Poor efficiency: High bill for low consumption
            ctrl.Rule(self.bill['very_high'] & self.kwh['low'], self.efficiency['very_poor']),
            ctrl.Rule(self.bill['high'] & self.kwh['low'], self.efficiency['poor']),
            ctrl.Rule(self.bill['high'] & self.kwh['medium'], self.efficiency['poor']),
            
            # Average efficiency
            ctrl.Rule(self.bill['medium'] & self.kwh['medium'], self.efficiency['average']),
            ctrl.Rule(self.bill['low'] & self.kwh['low'], self.efficiency['average']),
            ctrl.Rule(self.bill['high'] & self.kwh['high'], self.efficiency['average']),
            
            # Good efficiency
            ctrl.Rule(self.bill['low'] & self.kwh['medium'], self.efficiency['good']),
            ctrl.Rule(self.bill['medium'] & self.kwh['high'], self.efficiency['good']),
            
            # Excellent efficiency
            ctrl.Rule(self.bill['very_low'] & self.kwh['medium'], self.efficiency['excellent']),
            ctrl.Rule(self.bill['low'] & self.kwh['high'], self.efficiency['excellent']),
            ctrl.Rule(self.bill['medium'] & self.kwh['very_high'], self.efficiency['excellent']),
        ]
        
        try:
            self.ctrl_system = ctrl.ControlSystem(self.rules)
            self.sim = ctrl.ControlSystemSimulation(self.ctrl_system)
            self.system_ready = True
        except Exception:
            self.sim = None
            self.system_ready = False
    
    def analyze(self, bill_amount, estimated_kwh):
        """
        Analyze bill using fuzzy inference.
        
        Returns efficiency assessment with membership details.
        """
        result = {
            'efficiency_score': 50,
            'efficiency_term': 'average',
            'bill_category': 'medium',
            'consumption_category': 'medium',
            'memberships': {},
            'interpretation': ''
        }
        
        bill_val = np.clip(float(bill_amount), 0, 500)
        kwh_val = np.clip(float(estimated_kwh), 0, 1000)
        
        # Calculate memberships
        result['memberships']['bill'] = {}
        for term in self.bill.terms:
            result['memberships']['bill'][term] = float(
                fuzz.interp_membership(self.bill.universe, self.bill[term].mf, bill_val)
            )
        
        result['memberships']['kwh'] = {}
        for term in self.kwh.terms:
            result['memberships']['kwh'][term] = float(
                fuzz.interp_membership(self.kwh.universe, self.kwh[term].mf, kwh_val)
            )
        
        # Get dominant categories
        result['bill_category'] = max(result['memberships']['bill'].items(), key=lambda x: x[1])[0]
        result['consumption_category'] = max(result['memberships']['kwh'].items(), key=lambda x: x[1])[0]
        
        # Run fuzzy inference
        if self.sim is not None:
            try:
                self.sim.input['bill'] = bill_val
                self.sim.input['kwh'] = kwh_val
                self.sim.compute()
                result['efficiency_score'] = float(self.sim.output['efficiency'])
            except Exception:
                # Fallback
                cost_per_kwh = bill_amount / estimated_kwh if estimated_kwh > 0 else 0.5
                result['efficiency_score'] = max(0, min(100, 100 - (cost_per_kwh - 0.288) * 200))
        
        # Convert score to linguistic term
        score = result['efficiency_score']
        if score < 20:
            result['efficiency_term'] = 'very poor'
            result['interpretation'] = 'Your energy costs are significantly higher than expected for your consumption level.'
        elif score < 40:
            result['efficiency_term'] = 'poor'
            result['interpretation'] = 'Your energy efficiency could be improved. Consider reviewing your tariff or usage patterns.'
        elif score < 60:
            result['efficiency_term'] = 'average'
            result['interpretation'] = 'Your energy costs are typical for your consumption level.'
        elif score < 80:
            result['efficiency_term'] = 'good'
            result['interpretation'] = 'You are getting good value for your energy consumption.'
        else:
            result['efficiency_term'] = 'excellent'
            result['interpretation'] = 'Excellent efficiency! Your costs are very low relative to consumption.'
        
        return result


# =============================================================================
# MAIN FUZZY EXPLAINER CLASS
# =============================================================================

class FuzzyExplainer:
    """
    Main fuzzy-based explainer for energy market analysis.
    
    This is the primary interface class that combines:
    - FuzzyEnergySystem for market analysis
    - FuzzyBillAnalyzer for bill efficiency
    - Natural language generation
    """
    
    def __init__(self):
        """Initialize all fuzzy subsystems."""
        self.fuzzy_system = FuzzyEnergySystem()
        self.bill_analyzer = FuzzyBillAnalyzer()
    
    def analyze_data(self, df, model_metrics=None):
        """
        Perform comprehensive fuzzy analysis on energy data.
        
        This is the main analysis function that:
        1. Extracts statistics from data
        2. Runs fuzzy inference
        3. Identifies active rules
        4. Generates linguistic assessments
        
        Args:
            df: DataFrame with datetime, price, energy_consumption
            model_metrics: Optional model performance metrics
        
        Returns:
            dict with complete fuzzy analysis
        """
        analysis = {
            'price': {},
            'consumption': {},
            'patterns': {},
            'model_performance': {},
            'fuzzy_evaluation': {},
            'active_rules': []
        }
        
        # Extract statistics
        price_current = float(df['price'].iloc[-1])
        price_mean = float(df['price'].mean())
        price_std = float(df['price'].std())
        price_min = float(df['price'].min())
        price_max = float(df['price'].max())
        
        cons_current = float(df['energy_consumption'].iloc[-1])
        cons_mean = float(df['energy_consumption'].mean())
        cons_std = float(df['energy_consumption'].std())
        cons_min = float(df['energy_consumption'].min())
        cons_max = float(df['energy_consumption'].max())
        
        # Normalize consumption to 0-100
        if cons_max > cons_min:
            cons_normalized = ((cons_current - cons_min) / (cons_max - cons_min)) * 100
        else:
            cons_normalized = 50
        
        # Calculate 24h trend
        if len(df) >= 24:
            price_24h_ago = float(df['price'].iloc[-24])
            trend_pct = ((price_current - price_24h_ago) / price_24h_ago * 100) if price_24h_ago > 0 else 0
        else:
            trend_pct = 0
        
        # Get current hour
        if 'datetime' in df.columns:
            current_hour = pd.to_datetime(df['datetime'].iloc[-1]).hour
        else:
            current_hour = 12
        
        # =================================================================
        # RUN FUZZY INFERENCE
        # =================================================================
        fuzzy_result = self.fuzzy_system.evaluate(
            price_value=price_current,
            consumption_value=cons_normalized,
            hour_value=current_hour,
            volatility_value=min(price_std, 50),
            trend_value=np.clip(trend_pct, -50, 50)
        )
        
        analysis['fuzzy_evaluation'] = {
            'market_condition_score': fuzzy_result['market_condition'],
            'recommendation_score': fuzzy_result['recommendation'],
            'memberships': fuzzy_result['memberships'],
            'market_condition_term': self._score_to_term(fuzzy_result['market_condition'], 'market'),
            'recommendation_term': self._score_to_term(fuzzy_result['recommendation'], 'recommendation')
        }
        
        analysis['active_rules'] = fuzzy_result['active_rules']
        
        # =================================================================
        # PRICE ANALYSIS
        # =================================================================
        price_category = self._categorize_value(price_current, price_mean, price_std)
        
        analysis['price'] = {
            'current': price_current,
            'mean': price_mean,
            'std': price_std,
            'min': price_min,
            'max': price_max,
            'category': price_category,
            'linguistic': self._get_linguistic_term(price_category),
            'trend': self._get_trend_term(trend_pct),
            'trend_pct': trend_pct,
            'volatility': 'high' if price_std > 20 else 'medium' if price_std > 10 else 'low',
            'memberships': fuzzy_result['memberships']['price']
        }
        
        # =================================================================
        # CONSUMPTION ANALYSIS
        # =================================================================
        cons_category = self._categorize_value(cons_current, cons_mean, cons_std)
        
        if len(df) >= 6:
            cons_recent = df['energy_consumption'].tail(6).values
            cons_trend = ((cons_recent[-1] - cons_recent[0]) / cons_recent[0] * 100) if cons_recent[0] > 0 else 0
        else:
            cons_trend = 0
        
        analysis['consumption'] = {
            'current': cons_current,
            'mean': cons_mean,
            'std': cons_std,
            'min': cons_min,
            'max': cons_max,
            'normalized': cons_normalized,
            'category': cons_category,
            'linguistic': self._get_linguistic_term(cons_category),
            'trend': self._get_trend_term(cons_trend),
            'trend_pct': cons_trend,
            'memberships': fuzzy_result['memberships']['consumption']
        }
        
        # =================================================================
        # TEMPORAL PATTERNS
        # =================================================================
        if 'datetime' in df.columns:
            df_temp = df.copy()
            df_temp['hour'] = pd.to_datetime(df_temp['datetime']).dt.hour
            
            peak_hours = df_temp[df_temp['hour'].isin([7, 8, 9, 18, 19, 20, 21])]
            off_peak = df_temp[~df_temp['hour'].isin([7, 8, 9, 18, 19, 20, 21])]
            
            if len(peak_hours) > 0 and len(off_peak) > 0:
                peak_avg = float(peak_hours['price'].mean())
                offpeak_avg = float(off_peak['price'].mean())
                premium = ((peak_avg - offpeak_avg) / offpeak_avg * 100) if offpeak_avg > 0 else 0
                
                analysis['patterns'] = {
                    'peak_premium': premium,
                    'peak_pricing': 'significant' if premium > 15 else 'moderate' if premium > 5 else 'minimal',
                    'peak_price_avg': peak_avg,
                    'offpeak_price_avg': offpeak_avg,
                    'current_hour': current_hour,
                    'is_peak_hour': current_hour in [7, 8, 9, 18, 19, 20, 21],
                    'hour_memberships': fuzzy_result['memberships']['hour']
                }
        
        # =================================================================
        # MODEL PERFORMANCE
        # =================================================================
        if model_metrics:
            test = model_metrics.get('test', {})
            r2 = test.get('r2', 0)
            mae = test.get('mae', 0)
            
            if r2 > 0.9:
                perf = 'excellent'
            elif r2 > 0.75:
                perf = 'good'
            elif r2 > 0.5:
                perf = 'moderate'
            else:
                perf = 'poor'
            
            mae_pct = (mae / price_mean * 100) if price_mean > 0 else 0
            
            analysis['model_performance'] = {
                'r2': float(r2),
                'mae': float(mae),
                'category': perf,
                'mae_percentage': mae_pct,
                'error_description': self._get_error_description(mae_pct),
                'reliability': 'high' if r2 > 0.8 else 'medium' if r2 > 0.6 else 'low'
            }
        
        return analysis
    
    def _score_to_term(self, score, term_type='market'):
        """Convert numerical score to linguistic term."""
        if term_type == 'market':
            if score < 20:
                return 'very favorable'
            elif score < 40:
                return 'favorable'
            elif score < 60:
                return 'neutral'
            elif score < 80:
                return 'unfavorable'
            else:
                return 'very unfavorable'
        else:
            if score < 20:
                return 'avoid consumption'
            elif score < 40:
                return 'reduce consumption'
            elif score < 60:
                return 'normal consumption'
            elif score < 80:
                return 'increase consumption'
            else:
                return 'optimal for consumption'
    
    def _categorize_value(self, value, mean, std):
        """Categorize using z-score."""
        if std == 0:
            std = 1
        z = (value - mean) / std
        
        if z < -1.5:
            return 'very_low'
        elif z < -0.5:
            return 'low'
        elif z < 0.5:
            return 'moderate'
        elif z < 1.5:
            return 'high'
        else:
            return 'very_high'
    
    def _get_linguistic_term(self, category):
        """Convert category to human-readable term."""
        terms = {
            'very_low': 'very low',
            'low': 'relatively low',
            'moderate': 'moderate',
            'high': 'relatively high',
            'very_high': 'very high'
        }
        return terms.get(category, 'unknown')
    
    def _get_trend_term(self, pct):
        """Convert percentage to trend term."""
        if pct < -15:
            return 'falling rapidly'
        elif pct < -5:
            return 'decreasing'
        elif pct < 5:
            return 'stable'
        elif pct < 15:
            return 'increasing'
        else:
            return 'rising rapidly'
    
    def _get_error_description(self, mae_pct):
        """Get linguistic error description."""
        if mae_pct < 5:
            return 'minimal deviations (high accuracy)'
        elif mae_pct < 10:
            return 'small deviations (good accuracy)'
        elif mae_pct < 20:
            return 'moderate deviations (acceptable)'
        else:
            return 'significant deviations (limited accuracy)'
    
    def generate_explanation(self, analysis, include_context=True):
        """
        Generate comprehensive natural language explanation.
        
        Creates human-readable text from fuzzy analysis results.
        """
        sections = []
        
        # =================================================================
        # FUZZY MARKET ASSESSMENT
        # =================================================================
        if 'fuzzy_evaluation' in analysis:
            fe = analysis['fuzzy_evaluation']
            market_term = fe.get('market_condition_term', 'neutral')
            rec_term = fe.get('recommendation_term', 'normal')
            market_score = fe.get('market_condition_score', 50)
            
            sections.append(
                f"## 🎯 Fuzzy Market Assessment\n\n"
                f"**Market Condition:** {market_term.upper()} (Score: {market_score:.1f}/100)\n\n"
                f"**Recommendation:** {rec_term.capitalize()}"
            )
        
        # =================================================================
        # PRICE ANALYSIS
        # =================================================================
        price = analysis.get('price', {})
        if price:
            sections.append(
                f"## ⚡ Price Analysis\n\n"
                f"**Status:** Prices are **{price.get('linguistic', 'unknown')}** "
                f"(€{price.get('current', 0):.2f}/MWh vs avg €{price.get('mean', 0):.2f})\n\n"
                f"**Trend:** {price.get('trend', 'stable')} ({price.get('trend_pct', 0):+.1f}%)\n\n"
                f"**Volatility:** {price.get('volatility', 'medium')}"
            )
        
        # =================================================================
        # CONSUMPTION ANALYSIS  
        # =================================================================
        cons = analysis.get('consumption', {})
        if cons:
            sections.append(
                f"## 🔌 Consumption Analysis\n\n"
                f"**Status:** Demand is **{cons.get('linguistic', 'unknown')}** "
                f"({cons.get('current', 0):.0f} MW vs avg {cons.get('mean', 0):.0f})\n\n"
                f"**Trend:** {cons.get('trend', 'stable')}"
            )
        
        # =================================================================
        # ACTIVE FUZZY RULES
        # =================================================================
        rules = analysis.get('active_rules', [])
        if rules:
            rules_text = "## 📋 Active Fuzzy Rules\n\n"
            for r in rules[:5]:
                bar = "█" * int(r['strength'] * 10) + "░" * (10 - int(r['strength'] * 10))
                rules_text += f"**Rule {r.get('rule_id', '?')}:** `{r['rule']}`\n"
                rules_text += f"- Firing Strength: [{bar}] {r['strength']:.2f}\n"
                rules_text += f"- {r['interpretation']}\n\n"
            sections.append(rules_text)
        
        # =================================================================
        # TIME PATTERNS
        # =================================================================
        patterns = analysis.get('patterns', {})
        if patterns and 'peak_pricing' in patterns:
            premium = patterns.get('peak_premium', 0)
            is_peak = patterns.get('is_peak_hour', False)
            
            sections.append(
                f"## 🕐 Time-of-Use Analysis\n\n"
                f"**Peak Premium:** {patterns.get('peak_pricing', 'minimal').capitalize()} "
                f"({premium:+.1f}%)\n\n"
                f"**Current:** {'⚠️ Peak hour' if is_peak else '✅ Off-peak hour'}"
            )
        
        # =================================================================
        # MODEL PERFORMANCE
        # =================================================================
        model = analysis.get('model_performance', {})
        if model:
            sections.append(
                f"## 🤖 Prediction Model\n\n"
                f"**Accuracy:** {model.get('category', 'unknown').capitalize()} "
                f"(R² = {model.get('r2', 0):.3f})\n\n"
                f"**Reliability:** {model.get('reliability', 'unknown')}\n\n"
                f"**Errors:** {model.get('error_description', '')}"
            )
        
        return "\n\n---\n\n".join(sections)
    
    def generate_fuzzy_rules_summary(self):
        """Generate comprehensive rules documentation."""
        return """
## 🧠 Fuzzy Inference System - Rule Base

### Mamdani-Type Fuzzy Inference

**Fuzzy Set Operations:**
- **AND (∧):** Minimum operator: μ(A∧B) = min(μA, μB)
- **OR (∨):** Maximum operator: μ(A∨B) = max(μA, μB)
- **NOT (¬):** Complement: μ(¬A) = 1 - μA

**Defuzzification:** Centroid (Center of Gravity)

---

### Market Condition Rules

| # | IF (Antecedent) | THEN (Consequent) |
|---|-----------------|-------------------|
| 1 | price=VERY_HIGH ∧ consumption=VERY_HIGH | market=VERY_UNFAVORABLE |
| 2 | price=HIGH ∧ consumption=HIGH | market=UNFAVORABLE |
| 3 | price=MEDIUM ∧ consumption=MEDIUM | market=NEUTRAL |
| 4 | price=LOW ∧ consumption=LOW | market=FAVORABLE |
| 5 | price=VERY_LOW ∧ consumption=VERY_LOW | market=VERY_FAVORABLE |
| 6 | price=VERY_HIGH ∧ consumption=LOW | market=UNFAVORABLE |
| 7 | price=HIGH ∧ consumption=VERY_LOW | market=UNFAVORABLE |
| 8 | price=VERY_LOW ∧ consumption=HIGH | market=VERY_FAVORABLE |
| 9 | price=LOW ∧ consumption=VERY_HIGH | market=FAVORABLE |
| 10 | hour=NIGHT ∧ price=LOW | market=VERY_FAVORABLE |
| 11 | hour=MORNING_PEAK ∧ price=HIGH | market=UNFAVORABLE |
| 12 | hour=EVENING_PEAK ∧ price=VERY_HIGH | market=VERY_UNFAVORABLE |
| 13 | hour=AFTERNOON ∧ price=MEDIUM | market=NEUTRAL |
| 14 | volatility=VERY_HIGH ∧ price=HIGH | market=VERY_UNFAVORABLE |
| 15 | volatility=HIGH ∧ trend=RISING_FAST | market=UNFAVORABLE |
| 16 | volatility=LOW ∧ trend=STABLE | market=FAVORABLE |
| 17 | volatility=VERY_LOW ∧ price=LOW | market=VERY_FAVORABLE |
| 18 | trend=FALLING_FAST ∧ price=HIGH | market=NEUTRAL |
| 19 | trend=RISING_FAST ∧ price=LOW | market=NEUTRAL |
| 20 | trend=STABLE ∧ price=MEDIUM | market=NEUTRAL |

---

### Consumption Recommendation Rules

| # | IF (Antecedent) | THEN (Consequent) |
|---|-----------------|-------------------|
| R1 | price=VERY_LOW ∧ hour=NIGHT | recommendation=OPTIMAL |
| R2 | price=LOW ∧ consumption=LOW | recommendation=OPTIMAL |
| R3 | price=VERY_HIGH ∧ hour=EVENING_PEAK | recommendation=AVOID |
| R4 | price=HIGH ∧ hour=MORNING_PEAK | recommendation=REDUCE |
| R5 | price=MEDIUM ∧ hour=AFTERNOON | recommendation=NORMAL |
| R6 | price=MEDIUM ∧ consumption=MEDIUM | recommendation=NORMAL |
| R7 | price=LOW ∧ volatility=LOW | recommendation=INCREASE |
| R8 | price=VERY_LOW ∧ trend=FALLING | recommendation=OPTIMAL |
"""
    
    def get_membership_visualization_data(self, variable_name):
        """Get data for membership function plots."""
        return self.fuzzy_system.get_membership_plot_data(variable_name)
    
    def get_color_code(self, category):
        """Get color for category display."""
        colors = {
            'very_low': 'green',
            'low': 'lightgreen', 
            'moderate': 'orange',
            'high': 'darkorange',
            'very_high': 'red'
        }
        return colors.get(category, 'gray')
    
    def get_market_condition_color(self, term):
        """Get color for market condition."""
        colors = {
            'very favorable': '#00c853',
            'favorable': '#64dd17',
            'neutral': '#ffa726',
            'unfavorable': '#ff6f00',
            'very unfavorable': '#d32f2f'
        }
        return colors.get(term, '#666666')
