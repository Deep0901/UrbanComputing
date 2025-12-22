import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from app.predictor import EnergyPricePredictor
from app.entsoe_client import ENTSOEClient
from app.fuzzy_explainer import FuzzyExplainer
from app.reason_extractor import ReasonExtractor
from app.billing_analyzer import BillingAnalyzer
from app.evaluation_manager import EvaluationManager

st.set_page_config(
    page_title="Energy Price Explainability Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-live {
        color: #00c853;
        font-weight: bold;
    }
    .status-refreshing {
        color: #ffa726;
        font-weight: bold;
    }
    .category-very-low {
        color: #00c853;
        font-weight: bold;
    }
    .category-low {
        color: #64dd17;
        font-weight: bold;
    }
    .category-moderate {
        color: #ffa726;
        font-weight: bold;
    }
    .category-high {
        color: #ff6f00;
        font-weight: bold;
    }
    .category-very-high {
        color: #d32f2f;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'model_trained' not in st.session_state:
    st.session_state.model_trained = False
if 'predictor' not in st.session_state:
    st.session_state.predictor = None
if 'df' not in st.session_state:
    st.session_state.df = None
if 'data_source' not in st.session_state:
    st.session_state.data_source = 'sample'
if 'market_context' not in st.session_state:
    st.session_state.market_context = None
if 'fuzzy_analysis' not in st.session_state:
    st.session_state.fuzzy_analysis = None
if 'responses' not in st.session_state:
    st.session_state.responses = []
if 'eval_manager' not in st.session_state:
    st.session_state.eval_manager = EvaluationManager()

# Title
st.markdown('<h1 class="main-header">⚡ Fuzzy Logic Energy Explainability Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Mamdani Fuzzy Inference System for Energy Market Analysis & Linguistic Reasoning</p>', unsafe_allow_html=True)

# Main navigation
main_mode = st.radio(
    "Select Module:",
    ["💰 Bill Analysis & Optimization", "🔮 Price Forecasting & Analysis"],
    horizontal=True,
    key="main_mode"
)

st.divider()

# Sidebar
with st.sidebar:
    st.header("📊 Data Source Configuration")
    
    data_source_option = st.radio(
        "Select Data Source:",
        ["Sample Data (7 days)", "Upload CSV", "Real-time ENTSOE Data"],
        key="data_source_selector"
    )
    
    df = None
    market_context = None
    
    # Sample Data
    if data_source_option == "Sample Data (7 days)":
        st.info("Using pre-loaded 7 days of hourly energy consumption and price data")
        if os.path.exists('data/energy_data.csv'):
            df = pd.read_csv('data/energy_data.csv')
            df['datetime'] = pd.to_datetime(df['datetime'])
            st.success(f"✅ Loaded {len(df)} records")
            st.session_state.data_source = 'sample'
        else:
            st.error("Sample data file not found!")
    
    # CSV Upload
    elif data_source_option == "Upload CSV":
        st.info("Upload CSV with columns: datetime, energy_consumption, price")
        uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                
                # Validate columns
                required_cols = ['datetime', 'energy_consumption', 'price']
                if all(col in df.columns for col in required_cols):
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    st.success(f"✅ Loaded {len(df)} records")
                    st.session_state.data_source = 'upload'
                else:
                    st.error(f"Missing required columns. Found: {list(df.columns)}")
                    df = None
            except Exception as e:
                st.error(f"Error loading CSV: {str(e)}")
                df = None
    
    # ENTSOE Real-time Data
    elif data_source_option == "Real-time ENTSOE Data":
        st.info("Fetch live data from ENTSOE Transparency Platform")
        
        # API Token input
        api_token = st.text_input(
            "ENTSOE API Token:",
            type="password",
            value=os.getenv('ENTSOE_API_TOKEN', ''),
            help="Get your free token at: https://transparency.entsoe.eu/"
        )
        
        if api_token:
            country = st.selectbox(
                "Select Country/Region:",
                list(ENTSOEClient.DOMAINS.keys())
            )
            
            days = st.slider("Number of Days:", min_value=1, max_value=30, value=7)
            
            if st.button("🔄 Fetch ENTSOE Data", type="primary"):
                with st.spinner(f"Fetching data from {country}..."):
                    try:
                        client = ENTSOEClient(api_token)
                        df = client.fetch_complete_dataset(country, days)
                        market_context = client.get_market_context(country, days=1)
                        
                        st.session_state.df = df
                        st.session_state.market_context = market_context
                        st.session_state.data_source = 'entsoe'
                        
                        st.success(f"✅ Fetched {len(df)} records from {country}")
                        st.json({
                            'Records': len(df),
                            'Date Range': f"{df['datetime'].min()} to {df['datetime'].max()}",
                            'Price Range': f"€{df['price'].min():.2f} - €{df['price'].max():.2f}",
                            'Consumption Range': f"{df['energy_consumption'].min():.0f} - {df['energy_consumption'].max():.0f} MW"
                        })
                    except Exception as e:
                        st.error(f"Failed to fetch data: {str(e)}")
                        df = None
        else:
            st.warning("⚠️ Please enter your ENTSOE API token")
    
    # Store in session state
    if df is not None:
        st.session_state.df = df
    if market_context is not None:
        st.session_state.market_context = market_context
    
    st.divider()
    
    # Training section
    st.header("🤖 Model Training")
    
    if st.session_state.df is not None:
        if st.button("🚀 Train Model", type="primary"):
            with st.spinner("Training model..."):
                try:
                    predictor = EnergyPricePredictor()
                    predictor.train(st.session_state.df)
                    
                    st.session_state.predictor = predictor
                    st.session_state.model_trained = True
                    
                    # Generate fuzzy analysis
                    fuzzy = FuzzyExplainer()
                    metrics = predictor.get_metrics()
                    fuzzy_analysis = fuzzy.analyze_data(st.session_state.df, metrics)
                    st.session_state.fuzzy_analysis = fuzzy_analysis
                    
                    st.success("✅ Model trained successfully!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Training failed: {str(e)}")
    else:
        st.warning("Please load data first")
    
    st.divider()
    
    # Auto-refresh option
    st.header("🔄 Auto-Refresh")
    auto_refresh = st.checkbox("Enable Auto-Refresh (30 min)", value=False)
    
    if auto_refresh:
        st.info("🟢 Auto-refresh enabled")
        # Note: In production, you'd implement actual auto-refresh
        # For now, this is a placeholder

# ===== BILLING ANALYSIS MODULE =====
if main_mode == "💰 Bill Analysis & Optimization":
    st.header("💰 Swiss Electricity Bill Analysis")
    st.caption("Analyze your electricity bill with Swiss tariff structure (CHF). Based on ElCom 2024 average rates.")
    
    # Initialize session state for billing analysis
    if 'billing_analysis' not in st.session_state:
        st.session_state.billing_analysis = None
    if 'billing_params' not in st.session_state:
        st.session_state.billing_params = {}
    
    analyzer = BillingAnalyzer()
    
    # User Input Section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Enter Your Bill Information")
        
        bill_amount = st.number_input(
            "Monthly Bill Amount (CHF):",
            min_value=0.0,
            max_value=10000.0,
            value=120.0,
            step=5.0,
            help="Enter your total electricity bill for the month in Swiss Francs"
        )
        
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            canton = st.selectbox(
                "City / Canton (optional):",
                ["Other", "Zürich", "Bern", "Geneva", "Basel", "Lausanne"],
                help="Regional rates vary; select your area for better estimates"
            )
        with col_opt2:
            household_size = st.selectbox(
                "Household Size (optional):",
                ["4 persons", "1 person", "2 persons", "3 persons", "5+ persons"],
                help="Used for comparison with average consumption"
            )
    
    with col2:
        st.info("""
        **What you'll see:**
        
        ✅ Estimated monthly kWh  
        ✅ Cost breakdown (energy, grid, taxes, fixed, VAT)  
        ✅ Why each cost exists  
        ✅ % share of each component  
        ✅ Comparison with average household  
        ✅ Assumptions used  
        """)
    
    if st.button("🔍 Analyze My Bill", type="primary"):
        with st.spinner("Analyzing your electricity bill..."):
            st.session_state.billing_analysis = analyzer.analyze_bill(
                bill_amount,
                canton=canton,
                household_size=household_size,
            )
            st.session_state.billing_params = {
                'bill_amount': bill_amount,
                'canton': canton,
                'household_size': household_size,
            }
    
    # Display analysis if available
    if st.session_state.billing_analysis is not None:
        analysis = st.session_state.billing_analysis
        
        st.success("✅ Analysis Complete!")
        
        # ===== ESTIMATED CONSUMPTION =====
        st.subheader("⚡ Estimated Consumption")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Estimated Monthly Usage", f"{analysis['estimated_kwh']:.0f} kWh")
        with col2:
            st.metric("Average CHF per kWh", f"CHF {analysis['avg_chf_per_kwh']:.4f}")
        with col3:
            st.metric("Daily Average", f"{analysis['estimated_kwh']/30:.1f} kWh/day")
        
        st.divider()
        
        # ===== COST BREAKDOWN =====
        st.subheader("💰 Cost Breakdown")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            breakdown_data = pd.DataFrame({
                'Component': ['Energy Cost', 'Grid/Network Charges', 'Taxes & Levies', 'Fixed Monthly Charge', 'VAT (8.1%)'],
                'Amount (CHF)': [
                    analysis['energy_cost'],
                    analysis['grid_cost'],
                    analysis['taxes_levies'],
                    analysis['fixed_monthly'],
                    analysis['vat_amount']
                ],
                'Share (%)': [
                    analysis['pct_energy'],
                    analysis['pct_grid'],
                    analysis['pct_taxes'],
                    analysis['pct_fixed'],
                    analysis['pct_vat']
                ]
            })
            st.dataframe(breakdown_data, hide_index=True)
            
            st.markdown(f"""
            **Total (calculated):** CHF {analysis['total_calculated']:.2f}  
            **Your entered bill:** CHF {analysis['total_bill']:.2f}
            """)
        
        with col2:
            # Percentage pie visualization
            st.markdown("**Percentage Split**")
            pct_data = pd.DataFrame({
                'Component': ['Energy', 'Grid', 'Taxes/Levies', 'Fixed', 'VAT'],
                'Percent': [
                    analysis['pct_energy'],
                    analysis['pct_grid'],
                    analysis['pct_taxes'],
                    analysis['pct_fixed'],
                    analysis['pct_vat']
                ]
            })
            st.bar_chart(pct_data.set_index('Component'))
        
        st.divider()
        
        # ===== DYNAMIC REASON EXPLANATIONS =====
        st.subheader("🔍 Why Is Your Bill This Amount?")
        
        reasons = analysis['reasons']
        
        # Main reason (high/low/normal bill)
        main = reasons.get('main_reason', {})
        if main.get('severity') == 'high':
            st.error(f"**{main.get('title', '')}**\n\n{main.get('explanation', '')}")
        elif main.get('severity') == 'medium':
            st.warning(f"**{main.get('title', '')}**\n\n{main.get('explanation', '')}")
        elif main.get('severity') == 'low':
            st.success(f"**{main.get('title', '')}**\n\n{main.get('explanation', '')}")
        else:
            st.info(f"**{main.get('title', '')}**\n\n{main.get('explanation', '')}")
        
        # Consumption drivers
        with st.expander("📊 What's Driving Your Consumption?", expanded=True):
            for driver in reasons.get('consumption_drivers', []):
                st.markdown(driver)
        
        # Regional impact
        regional = reasons.get('regional_impact', {})
        with st.expander(regional.get('title', '📍 Regional Analysis'), expanded=False):
            st.markdown(regional.get('explanation', ''))
            if regional.get('impact'):
                st.markdown(f"**Impact:** {regional.get('impact')}")
        
        # Cost insights
        cost_insights = reasons.get('cost_insights', [])
        if cost_insights:
            with st.expander("💰 Cost Breakdown Insights", expanded=False):
                for insight in cost_insights:
                    st.markdown(insight)
        
        st.divider()
        
        # ===== PERSONALIZED TIPS & QUICK ACTIONS =====
        st.subheader("💡 Personalized Tips & Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🎯 Quick Actions (This Month)**")
            for action in reasons.get('quick_actions', []):
                st.markdown(action)
        
        with col2:
            st.markdown("**💡 Energy-Saving Tips For You**")
            for tip in reasons.get('personalized_tips', [])[:4]:
                st.markdown(tip)
        
        st.divider()
        
        # ===== COMPARISON =====
        st.subheader("📊 Comparison with Average Household")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            delta_kwh = f"{analysis['diff_kwh_pct']:+.0f}%" if analysis['diff_kwh_pct'] != 0 else "same"
            st.metric(
                "Your Usage vs Average",
                f"{analysis['estimated_kwh']:.0f} kWh",
                delta=delta_kwh,
                delta_color="inverse"
            )
        with col2:
            st.metric(
                f"Average ({analysis['household_size']})",
                f"{analysis['avg_kwh']} kWh/mo"
            )
        with col3:
            delta_bill = f"{analysis['diff_bill_pct']:+.0f}%" if analysis['diff_bill_pct'] != 0 else "same"
            st.metric(
                "Your Bill vs Average",
                f"CHF {analysis['total_bill']:.2f}",
                delta=delta_bill,
                delta_color="inverse"
            )
        
        # Comparison bar
        comparison_df = pd.DataFrame({
            'Category': ['Your Bill', 'Average Household'],
            'Amount (CHF)': [analysis['total_bill'], analysis['avg_bill']]
        })
        st.bar_chart(comparison_df.set_index('Category'))
        
        st.divider()
        
        # ===== ASSUMPTIONS NOTICE =====
        st.subheader("📝 Assumptions Used")
        st.info(analysis['assumptions'])
        
        st.divider()

        # ===== DUAL EXPLANATION SYSTEM =====
        st.subheader("🧭 Dual Explanation: Numerical vs Linguistic Language")
        tab_a, tab_b = st.tabs(["📊 Method A (Numerical)", "🗣️ Method B (Linguistic)"])

        with tab_a:
            st.markdown("**Technical Analysis with Formulas and Data**")
            
            # Bill formula
            st.markdown("### 📐 Bill Calculation Formula")
            st.code("Total = (kWh × (Energy + Grid + Taxes/Levies) + Fixed) × (1 + VAT)", language="text")
            
            variable_rate = analysis['rates']['energy_rate'] + analysis['rates']['grid_rate'] + analysis['rates']['taxes_levies_rate']
            
            st.markdown(f"""
            **Your bill breakdown:**
            - Estimated consumption: **{analysis['estimated_kwh']:.1f} kWh**
            - Variable rate: {analysis['rates']['energy_rate']:.4f} + {analysis['rates']['grid_rate']:.4f} + {analysis['rates']['taxes_levies_rate']:.4f} = **{variable_rate:.4f} CHF/kWh**
            - Variable cost: {analysis['estimated_kwh']:.1f} × {variable_rate:.4f} = **CHF {analysis['estimated_kwh'] * variable_rate:.2f}**
            - Fixed monthly: **CHF {analysis['rates']['fixed_monthly']:.2f}**
            - Subtotal: CHF {(analysis['estimated_kwh'] * variable_rate + analysis['rates']['fixed_monthly']):.2f}
            - VAT ({analysis['rates']['vat_rate']*100:.1f}%): **CHF {analysis['vat_amount']:.2f}**
            - **Total: CHF {analysis['total_calculated']:.2f}**
            """)
            
            st.markdown("### 📊 Statistical Comparison")
            diff_kwh = analysis['estimated_kwh'] - analysis['avg_kwh']
            diff_bill = analysis['total_bill'] - analysis['avg_bill']
            
            st.markdown(f"""
            | Metric | Your Value | Average ({analysis['household_size']}) | Difference |
            |--------|------------|-----------------|------------|
            | Consumption | {analysis['estimated_kwh']:.0f} kWh | {analysis['avg_kwh']} kWh | {diff_kwh:+.0f} kWh ({analysis['diff_kwh_pct']:+.1f}%) |
            | Monthly Bill | CHF {analysis['total_bill']:.2f} | CHF {analysis['avg_bill']:.2f} | CHF {diff_bill:+.2f} ({analysis['diff_bill_pct']:+.1f}%) |
            | Cost per kWh | CHF {analysis['avg_chf_per_kwh']:.4f} | CHF 0.2880 | CHF {analysis['avg_chf_per_kwh']-0.288:+.4f} |
            """)
            
            st.markdown("### 📈 Efficiency Metrics")
            efficiency_score = max(0, min(100, 100 - analysis['diff_kwh_pct']))
            st.progress(efficiency_score / 100, text=f"Energy Efficiency Score: {efficiency_score:.0f}/100")
            
            st.markdown(f"""
            - **Cost efficiency**: CHF {analysis['avg_chf_per_kwh']:.4f}/kWh (Swiss avg: ~0.27-0.29 CHF/kWh)
            - **Grid cost ratio**: {analysis['pct_grid']:.1f}% (typical: 35-40%)
            - **Fixed cost ratio**: {analysis['pct_fixed']:.1f}% (lower usage = higher ratio)
            """)

        with tab_b:
            st.markdown("**Plain Language Explanation**")
            
            # Dynamic intro based on bill level
            main_reason = analysis['reasons'].get('main_reason', {})
            
            if main_reason.get('severity') == 'high':
                st.error(f"""
                ### ⚠️ Your Bill is Higher Than Expected
                
                Your electricity bill of **CHF {analysis['total_bill']:.2f}** is significantly above 
                average for a {analysis['household_size']} household in Switzerland.
                
                **In simple terms:** You're paying about **CHF {analysis['total_bill'] - analysis['avg_bill']:.2f} more** 
                per month than similar households. Over a year, that's **CHF {(analysis['total_bill'] - analysis['avg_bill'])*12:.0f}** 
                that could be saved!
                """)
            elif main_reason.get('severity') == 'medium':
                st.warning(f"""
                ### 📊 Your Bill is Slightly Above Average
                
                Your bill of **CHF {analysis['total_bill']:.2f}** is a bit higher than typical.
                There's some room for savings without major lifestyle changes.
                """)
            elif main_reason.get('severity') == 'low':
                st.success(f"""
                ### 🌟 Great Job - You're Below Average!
                
                Your bill of **CHF {analysis['total_bill']:.2f}** is **lower than average**! 
                You're saving about **CHF {analysis['avg_bill'] - analysis['total_bill']:.2f}/month** 
                compared to similar households.
                """)
            else:
                st.info(f"""
                ### ✅ Your Bill is Normal
                
                Your bill of **CHF {analysis['total_bill']:.2f}** is typical for a {analysis['household_size']} 
                household in {analysis['canton']}. You're using energy responsibly.
                """)
            
            st.markdown("### 🏠 Where Does Your Money Go?")
            st.markdown(f"""
            Think of your CHF {analysis['total_bill']:.2f} bill like this:
            
            - 🔌 **CHF {analysis['energy_cost']:.2f}** ({analysis['pct_energy']:.0f}%) - The actual electricity you used
            - 🌐 **CHF {analysis['grid_cost']:.2f}** ({analysis['pct_grid']:.0f}%) - Maintaining the power lines, poles, and transformers that bring electricity to your home
            - 🏛️ **CHF {analysis['taxes_levies']:.2f}** ({analysis['pct_taxes']:.0f}%) - Taxes and fees supporting Switzerland's renewable energy goals
            - 📋 **CHF {analysis['fixed_monthly']:.2f}** ({analysis['pct_fixed']:.0f}%) - A fixed fee you pay even if you use zero electricity (like a subscription)
            - 💵 **CHF {analysis['vat_amount']:.2f}** ({analysis['pct_vat']:.0f}%) - Swiss VAT (value-added tax)
            """)
            
            st.markdown("### 💡 What Can You Do?")
            
            if analysis['diff_bill_pct'] > 15:
                st.markdown("""
                **Top 3 actions to reduce your bill:**
                1. 🔍 **Check for "energy vampires"** - devices that consume power even when off (TV, gaming consoles, chargers)
                2. 💡 **Switch to LED bulbs** - they use 80% less energy than traditional bulbs
                3. 🧊 **Check your fridge** - if it's over 10 years old, a new A+++ model could cut its energy use by 50%
                """)
            elif analysis['diff_bill_pct'] > 0:
                st.markdown("""
                **Small changes that add up:**
                1. ⏰ **Run appliances at night** - some tariffs offer cheaper off-peak rates
                2. 🌡️ **Lower heating by 1°C** - saves about 6% on heating costs
                3. 🧺 **Wash at 30°C** - modern detergents work well at lower temperatures
                """)
            else:
                st.markdown("""
                **Keep up the good work! A few more ideas:**
                1. ☀️ **Consider solar** - Switzerland has great incentives for rooftop solar
                2. 📊 **Get a smart meter** - track your usage in real-time
                3. 🔋 **Future-proof** - home batteries can store cheap night-time electricity
                """)
            
            # Simple comparison visual
            st.markdown("### 📊 How You Compare")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Your Monthly Bill",
                    f"CHF {analysis['total_bill']:.0f}",
                    f"{analysis['diff_bill_pct']:+.0f}% vs average",
                    delta_color="inverse"
                )
            with col2:
                st.metric(
                    "Average Household",
                    f"CHF {analysis['avg_bill']:.0f}",
                    f"{analysis['household_size']}"
                )
            
        # ===== SAVINGS CALCULATOR =====
        with st.expander("💰 Potential Savings Calculator", expanded=True):
            bill_amount = st.session_state.billing_params['bill_amount']
            canton = st.session_state.billing_params['canton']
            household_size = st.session_state.billing_params['household_size']
            
            optimization_level = st.select_slider(
                "Select Optimization Strategy:",
                options=["conservative", "moderate", "aggressive"],
                value="moderate",
                key="optimization_level_slider"
            )
            
            savings = analyzer.calculate_potential_savings(
                bill_amount, 
                canton=canton,
                household_size=household_size,
                optimization_level=optimization_level
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Monthly Savings",
                    f"CHF {savings['monthly_savings']:.2f}",
                    f"{savings['percentage_savings']:.1f}% reduction"
                )
            
            with col2:
                st.metric(
                    "Annual Savings",
                    f"CHF {savings['annual_savings']:.2f}",
                    "Estimated"
                )
            
            with col3:
                st.metric(
                    "Optimized Bill",
                    f"CHF {savings['optimized_bill']:.2f}",
                    f"-CHF {savings['monthly_savings']:.2f}"
                )
            
            st.markdown(f"**Strategy:** {savings['description']}")
            
            st.markdown("**🎯 Actions to Take:**")
            for action in savings['actions']:
                st.markdown(f"- {action}")
            
            # Comparison chart
            st.subheader("📊 Before vs After Comparison")
            
            comparison_df = pd.DataFrame({
                'Category': ['Current Bill', 'Optimized Bill', 'Monthly Savings'],
                'Amount (CHF)': [
                    savings['current_bill'],
                    savings['optimized_bill'],
                    savings['monthly_savings']
                ]
            })
            
            st.bar_chart(comparison_df.set_index('Category'))
        
        st.divider()
        
        # =============================================================================
        # ===== FUZZY LOGIC BILL ANALYSIS (BASED ON REAL ENTSOE DATA) =====
        # =============================================================================
        st.header("🧠 Fuzzy Logic Energy Market Analysis")
        
        # Check if model is trained with real data
        if st.session_state.model_trained and st.session_state.df is not None:
            st.success("✅ Real market data available - Fuzzy analysis using actual ENTSOE data")
            
            # Initialize fuzzy explainer with real data
            fuzzy = FuzzyExplainer()
            
            # Get metrics from trained model
            metrics = st.session_state.predictor.get_metrics()
            
            # Generate fuzzy analysis from real data
            if st.session_state.fuzzy_analysis is None:
                st.session_state.fuzzy_analysis = fuzzy.analyze_data(st.session_state.df, metrics)
            
            fuzzy_analysis = st.session_state.fuzzy_analysis
            
            # =================================================================
            # SECTION 1: FUZZY SYSTEM OVERVIEW
            # =================================================================
            st.subheader("📊 Fuzzy Inference System Overview")
            st.caption("Mamdani-type FIS trained on real European energy market data")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Input Variables", "5", help="Price, Consumption, Hour, Volatility, Trend")
            with col2:
                st.metric("Output Variables", "2", help="Market Condition, Consumption Recommendation")
            with col3:
                st.metric("Fuzzy Rules", "28", help="20 market rules + 8 recommendation rules")
            with col4:
                st.metric("Inference Method", "Mamdani", help="Max-Min composition with centroid defuzzification")
            
            # Data source indicator
            if st.session_state.data_source == 'entsoe':
                st.info(f"🌍 **Live Data**: Analysis based on real ENTSOE data from European energy markets")
            else:
                st.info(f"📊 **Data Source**: {st.session_state.data_source}")
            
            st.divider()
            
            # =================================================================
            # SECTION 2: CURRENT MARKET FUZZY EVALUATION
            # =================================================================
            st.subheader("🎯 Current Market Conditions (Fuzzy Evaluation)")
            
            if 'fuzzy_evaluation' in fuzzy_analysis:
                fe = fuzzy_analysis['fuzzy_evaluation']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    market_score = fe.get('market_condition_score', 50)
                    market_term = fe.get('market_condition_term', 'neutral')
                    
                    if market_score < 30:
                        color = "🟢"
                    elif market_score < 50:
                        color = "🟡"
                    elif market_score < 70:
                        color = "🟠"
                    else:
                        color = "🔴"
                    
                    st.markdown(f"### {color} Market Condition")
                    st.metric(
                        "Fuzzy Output Score",
                        f"{market_score:.1f}/100",
                        f"{market_term.upper()}"
                    )
                    st.progress(market_score / 100)
                    st.caption("0 = Very Favorable → 100 = Very Unfavorable")
                
                with col2:
                    rec_score = fe.get('recommendation_score', 50)
                    rec_term = fe.get('recommendation_term', 'normal')
                    
                    if rec_score > 70:
                        color = "🟢"
                    elif rec_score > 50:
                        color = "🟡"
                    elif rec_score > 30:
                        color = "🟠"
                    else:
                        color = "🔴"
                    
                    st.markdown(f"### {color} Consumption Recommendation")
                    st.metric(
                        "Fuzzy Output Score",
                        f"{rec_score:.1f}/100",
                        f"{rec_term.upper()}"
                    )
                    st.progress(rec_score / 100)
                    st.caption("0 = Avoid Consumption → 100 = Optimal Time")
            
            st.divider()
            
            # =================================================================
            # SECTION 3: BILL IMPACT FROM REAL MARKET DATA
            # =================================================================
            st.subheader("💰 Bill Impact Analysis (Based on Real Prices)")
            
            # Calculate bill impact from real price data
            current_price = fuzzy_analysis['price']['current']
            avg_price = fuzzy_analysis['price']['mean']
            min_price = fuzzy_analysis['price']['min']
            max_price = fuzzy_analysis['price']['max']
            
            # Estimate bill impact
            estimated_monthly_kwh = analysis['estimated_kwh']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                current_cost_estimate = (current_price / 1000) * estimated_monthly_kwh * 0.95  # Convert €/MWh to CHF/kWh approx
                st.metric("At Current Price", f"CHF {current_cost_estimate:.2f}", 
                         f"€{current_price:.2f}/MWh")
            with col2:
                optimal_cost = (min_price / 1000) * estimated_monthly_kwh * 0.95
                savings_vs_current = current_cost_estimate - optimal_cost
                st.metric("At Optimal Price", f"CHF {optimal_cost:.2f}",
                         f"Save CHF {savings_vs_current:.2f}")
            with col3:
                peak_cost = (max_price / 1000) * estimated_monthly_kwh * 0.95
                extra_vs_current = peak_cost - current_cost_estimate
                st.metric("At Peak Price", f"CHF {peak_cost:.2f}",
                         f"+CHF {extra_vs_current:.2f}")
            
            st.divider()
            
            # =================================================================
            # SECTION 4: MEMBERSHIP FUNCTION VISUALIZATION
            # =================================================================
            st.subheader("📈 Fuzzy Membership Functions (Real Data)")
            st.markdown("Visualize how current market values are fuzzified into linguistic terms")
            
            selected_var = st.selectbox(
                "Select Fuzzy Variable to Visualize:",
                ["price", "consumption", "hour", "volatility", "trend", "market_condition", "recommendation"],
                format_func=lambda x: {
                    'price': f'⚡ Price (€/MWh) - Current: €{fuzzy_analysis["price"]["current"]:.2f}',
                    'consumption': f'🔌 Consumption (%) - Current: {fuzzy_analysis["consumption"]["normalized"]:.1f}%',
                    'hour': '🕐 Hour of Day',
                    'volatility': f'📊 Volatility - σ={fuzzy_analysis["price"]["std"]:.2f}',
                    'trend': f'📈 Price Trend - {fuzzy_analysis["price"]["trend_pct"]:+.1f}%',
                    'market_condition': '🎯 Market Condition (Output)',
                    'recommendation': '💡 Recommendation (Output)'
                }.get(x, x)
            )
            
            mf_data = fuzzy.get_membership_visualization_data(selected_var)
            
            if mf_data:
                plot_df = pd.DataFrame({'x': mf_data['universe']})
                
                for term in mf_data:
                    if term != 'universe':
                        plot_df[term] = mf_data[term]
                
                st.line_chart(plot_df.set_index('x'))
                
                # Show current value memberships
                if selected_var in ['price', 'consumption', 'hour', 'volatility', 'trend']:
                    memberships = fuzzy_analysis.get('fuzzy_evaluation', {}).get('memberships', {}).get(selected_var, {})
                    
                    if memberships:
                        st.markdown("**Current Input Membership Degrees:**")
                        mem_cols = st.columns(len(memberships))
                        for i, (term, degree) in enumerate(memberships.items()):
                            with mem_cols[i]:
                                bar = "█" * int(degree * 10) + "░" * (10 - int(degree * 10))
                                st.markdown(f"**{term.replace('_', ' ').title()}**")
                                st.code(f"[{bar}] {degree:.3f}")
            
            st.divider()
            
            # =================================================================
            # SECTION 5: ACTIVE FUZZY RULES
            # =================================================================
            st.subheader("📋 Active Fuzzy Rules (Currently Firing)")
            st.markdown("Rules with firing strength > 0.3 based on real market conditions")
            
            active_rules = fuzzy_analysis.get('active_rules', [])
            
            if active_rules:
                for rule in active_rules[:6]:
                    strength = rule.get('strength', 0)
                    
                    if strength > 0.7:
                        st.success(f"**Rule {rule.get('rule_id', '?')}** | Strength: {strength:.2f}")
                    elif strength > 0.5:
                        st.warning(f"**Rule {rule.get('rule_id', '?')}** | Strength: {strength:.2f}")
                    else:
                        st.info(f"**Rule {rule.get('rule_id', '?')}** | Strength: {strength:.2f}")
                    
                    st.code(rule.get('rule', ''))
                    st.markdown(f"*{rule.get('interpretation', '')}*")
                    st.markdown("---")
            else:
                st.info("No rules currently firing above threshold. Market conditions are balanced.")
            
            st.divider()
            
            # =================================================================
            # SECTION 6: OPTIMAL CONSUMPTION TIMES
            # =================================================================
            st.subheader("⏰ Optimal Consumption Times (From Real Data)")
            
            df_temp = st.session_state.df.copy()
            df_temp['hour'] = pd.to_datetime(df_temp['datetime']).dt.hour
            hourly_prices = df_temp.groupby('hour')['price'].mean()
            
            # Find best and worst hours
            best_hours = hourly_prices.nsmallest(3)
            worst_hours = hourly_prices.nlargest(3)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🟢 Best Times to Use Energy")
                for hour, price in best_hours.items():
                    time_str = f"{hour:02d}:00 - {(hour+1)%24:02d}:00"
                    st.success(f"**{time_str}** - Avg €{price:.2f}/MWh")
                
                st.markdown("*Schedule high-consumption tasks during these hours*")
            
            with col2:
                st.markdown("### 🔴 Avoid These Times")
                for hour, price in worst_hours.items():
                    time_str = f"{hour:02d}:00 - {(hour+1)%24:02d}:00"
                    st.error(f"**{time_str}** - Avg €{price:.2f}/MWh")
                
                st.markdown("*Minimize usage during peak pricing*")
            
            # Show hourly price chart
            st.markdown("### 📊 Average Price by Hour")
            st.bar_chart(hourly_prices)
            
            st.divider()
            
            # =================================================================
            # SECTION 7: LINGUISTIC EXPLANATION
            # =================================================================
            st.subheader("🗣️ Natural Language Fuzzy Explanation")
            
            explanation = fuzzy.generate_explanation(fuzzy_analysis)
            st.markdown(explanation)
            
            st.divider()
            
            # =================================================================
            # SECTION 8: INTERACTIVE FUZZY SIMULATOR
            # =================================================================
            st.subheader("🎮 Interactive Fuzzy Inference Simulator")
            st.markdown("Test the fuzzy system with custom values")
            
            with st.expander("Open Fuzzy Simulator", expanded=False):
                sim_col1, sim_col2 = st.columns(2)
                
                with sim_col1:
                    sim_price = st.slider("Price (€/MWh)", 0, 200, int(fuzzy_analysis['price']['current']), key="sim_price_bill")
                    sim_consumption = st.slider("Consumption (%)", 0, 100, int(fuzzy_analysis['consumption']['normalized']), key="sim_cons_bill")
                    sim_hour = st.slider("Hour of Day", 0, 23, 12, key="sim_hour_bill")
                
                with sim_col2:
                    sim_volatility = st.slider("Volatility (σ)", 0, 50, int(fuzzy_analysis['price']['std']), key="sim_vol_bill")
                    sim_trend = st.slider("24h Trend (%)", -50, 50, int(fuzzy_analysis['price']['trend_pct']), key="sim_trend_bill")
                
                if st.button("🔄 Run Fuzzy Inference", type="primary", key="run_fuzzy_bill"):
                    sim_result = fuzzy.fuzzy_system.evaluate(
                        price_value=sim_price,
                        consumption_value=sim_consumption,
                        hour_value=sim_hour,
                        volatility_value=sim_volatility,
                        trend_value=sim_trend
                    )
                    
                    st.success("Fuzzy Inference Complete!")
                    
                    res_col1, res_col2 = st.columns(2)
                    with res_col1:
                        st.metric("Market Condition", f"{sim_result['market_condition']:.1f}/100")
                    with res_col2:
                        st.metric("Recommendation", f"{sim_result['recommendation']:.1f}/100")
                    
                    st.markdown("**Activated Rules:**")
                    for r in sim_result['active_rules'][:3]:
                        st.info(f"• {r['interpretation']}")
            
            st.divider()
            
            # =================================================================
            # SECTION 9: COMPLETE RULE BASE
            # =================================================================
            with st.expander("📖 View Complete Fuzzy Rule Base", expanded=False):
                rules_summary = fuzzy.generate_fuzzy_rules_summary()
                st.markdown(rules_summary)
            
            st.divider()
            
            # =================================================================
            # SECTION 10: FUZZY THEORY EXPLANATION
            # =================================================================
            with st.expander("📚 About Fuzzy Logic Theory", expanded=False):
                st.markdown("""
                ### What is Fuzzy Logic?
                
                Fuzzy logic is a form of many-valued logic that deals with approximate reasoning, 
                rather than fixed and exact reasoning. It was introduced by **Lotfi Zadeh** in 1965.
                
                ### Key Concepts
                
                **1. Fuzzy Sets**
                Unlike classical sets where an element either belongs or doesn't (0 or 1), 
                fuzzy sets allow partial membership between 0 and 1.
                
                **2. Membership Functions**
                Define how each point in the input space is mapped to a membership degree:
                - **Triangular (trimf)**: Defined by 3 points
                - **Trapezoidal (trapmf)**: Defined by 4 points
                
                **3. Fuzzy Rules (IF-THEN)**
                ```
                IF price is HIGH AND consumption is HIGH THEN market is UNFAVORABLE
                ```
                
                **4. Fuzzy Operations**
                - **AND**: Minimum operator (min)
                - **OR**: Maximum operator (max)
                - **NOT**: Complement (1 - μ)
                
                ### Mamdani Inference Process
                
                1. **Fuzzification**: Convert crisp inputs to fuzzy membership degrees
                2. **Rule Evaluation**: Apply IF-THEN rules using fuzzy operations
                3. **Aggregation**: Combine outputs from all rules
                4. **Defuzzification**: Convert fuzzy output to crisp value (centroid method)
                
                ### Why Fuzzy Logic for Energy Analysis?
                
                - **Handles Uncertainty**: Energy markets are inherently uncertain
                - **Human-Readable Rules**: IF-THEN format is intuitive
                - **Gradual Transitions**: No sharp category boundaries
                - **Expert Knowledge**: Rules encode domain expertise
                - **Explainability**: Every decision can be traced to specific rules
                
                ### References
                
                - Zadeh, L.A. (1965). Fuzzy Sets. Information and Control, 8(3), 338-353.
                - Mamdani, E.H. (1974). Application of Fuzzy Algorithms for Control.
                """)
        
        else:
            # No trained model - show instructions
            st.warning("⚠️ **Train the model first to enable Fuzzy Logic Analysis**")
            st.markdown("""
            ### How to Enable Fuzzy Analysis
            
            The fuzzy logic analysis requires real energy market data. Please:
            
            1. **Load Data** from the sidebar:
               - Use **Sample Data** for quick testing
               - Use **ENTSOE Data** for real European market analysis
            
            2. **Train the Model** by clicking the "Train Model" button
            
            3. Return here to see fuzzy analysis based on actual market conditions
            
            ---
            
            ### Why Real Data Matters
            
            The fuzzy inference system analyzes:
            - **Real price patterns** from European energy markets
            - **Actual consumption levels** and load profiles
            - **True market volatility** and price trends
            - **Peak hours** specific to your selected region
            
            This provides actionable insights for optimizing your electricity consumption and costs.
            """)

# ===== PRICE FORECASTING MODULE =====
elif main_mode == "🔮 Price Forecasting & Analysis":

    # Main content
    if st.session_state.model_trained and st.session_state.predictor is not None:
        st.success("✅ Model trained - Fuzzy Logic explainability ready")
        
        # Quick link to Fuzzy Analysis
        st.info("💡 **Tip:** Visit the **💰 Bill Analysis & Optimization** module for comprehensive fuzzy inference analysis of your electricity bills!")
        
        # Display data summary with realistic energy market metrics
        with st.expander("📊 Energy Market Data Summary", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Records", len(st.session_state.df))
            with col2:
                avg_price = st.session_state.df['price'].mean()
                peak_price = st.session_state.df['price'].max()
                st.metric("Avg Price", f"€{avg_price:.2f}", delta=f"Peak: €{peak_price:.2f}")
            with col3:
                avg_cons = st.session_state.df['energy_consumption'].mean()
                peak_cons = st.session_state.df['energy_consumption'].max()
                st.metric("Avg Load", f"{avg_cons:.0f} MW", delta=f"Peak: {peak_cons:.0f} MW")
            with col4:
                r2 = st.session_state.predictor.get_metrics()['test']['r2']
                st.metric("Model R²", f"{r2:.3f}")
            
            # Additional market insights
            st.markdown("#### Market Characteristics")
            insight_cols = st.columns(3)
            
            with insight_cols[0]:
                price_volatility = st.session_state.df['price'].std()
                st.metric("Price Volatility (σ)", f"€{price_volatility:.2f}")
            
            with insight_cols[1]:
                load_factor = (st.session_state.df['energy_consumption'].mean() / 
                              st.session_state.df['energy_consumption'].max() * 100)
                st.metric("Load Factor", f"{load_factor:.1f}%")
            
            with insight_cols[2]:
                price_range = st.session_state.df['price'].max() - st.session_state.df['price'].min()
                st.metric("Price Range", f"€{price_range:.2f}")
        
        st.divider()
        
        # Add realistic time series visualization
        st.header("📈 Energy Market Time Series")
        
        tab1, tab2 = st.tabs(["Price Patterns", "Load Profiles"])
        
        with tab1:
            st.markdown("### Electricity Price Over Time")
            price_chart_df = st.session_state.df[['datetime', 'price']].copy()
            price_chart_df = price_chart_df.set_index('datetime')
            st.line_chart(price_chart_df)
            
            col1, col2 = st.columns(2)
            with col1:
                # Price distribution
                st.markdown("#### Price Distribution")
                price_hist = pd.DataFrame({
                    'Price (€/MWh)': st.session_state.df['price']
                })
                st.bar_chart(price_hist['Price (€/MWh)'].value_counts().sort_index())
            
            with col2:
                    # Peak vs Off-peak
                    st.markdown("#### Peak vs Off-Peak Prices")
                    df_temp = st.session_state.df.copy()
                    df_temp['hour'] = pd.to_datetime(df_temp['datetime']).dt.hour
                    df_temp['period'] = df_temp['hour'].apply(
                        lambda x: 'Peak' if (7 <= x <= 9) or (18 <= x <= 21) 
                        else 'Off-Peak' if (1 <= x <= 5) else 'Standard'
                    )
                    period_prices = df_temp.groupby('period')['price'].mean()
                    st.bar_chart(period_prices)
        
            with tab2:
                st.markdown("### System Load Over Time")
                load_chart_df = st.session_state.df[['datetime', 'energy_consumption']].copy()
                load_chart_df = load_chart_df.set_index('datetime')
                st.line_chart(load_chart_df)
                
                col1, col2 = st.columns(2)
                with col1:
                    # Hourly average load
                    st.markdown("#### Average Load by Hour")
                    df_temp = st.session_state.df.copy()
                    df_temp['hour'] = pd.to_datetime(df_temp['datetime']).dt.hour
                    hourly_avg = df_temp.groupby('hour')['energy_consumption'].mean()
                    st.line_chart(hourly_avg)
                
                with col2:
                    # Day of week pattern
                    st.markdown("#### Average Load by Day of Week")
                    df_temp['day'] = pd.to_datetime(df_temp['datetime']).dt.day_name()
                    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    daily_avg = df_temp.groupby('day')['energy_consumption'].mean().reindex(day_order)
                    st.bar_chart(daily_avg)
        
        st.divider()
        
        # Dual Explanation View
        st.header("🔍 Dual Explanation System")
        col_a, col_b = st.columns(2)
        
        # METHOD A: Numerical Explanation
        with col_a:
            st.markdown("### 📈 Method A: Numerical Explanation")
            st.markdown("*Quantitative statistical insights*")
            
            with st.container():
                metrics = st.session_state.predictor.get_metrics()
                feature_importance = st.session_state.predictor.get_feature_importance()
                
                # Performance Metrics
                st.markdown("#### Model Performance Metrics")
                
                metric_cols = st.columns(3)
                with metric_cols[0]:
                    st.metric("R² Score", f"{metrics['test']['r2']:.4f}")
                with metric_cols[1]:
                    st.metric("MAE", f"{metrics['test']['mae']:.2f}")
                with metric_cols[2]:
                    st.metric("RMSE", f"{metrics['test']['rmse']:.2f}")
                
                # Feature Importance
                st.markdown("#### Feature Importance")
                top_features = feature_importance.head(8)
                
                st.dataframe(
                    top_features[['feature', 'coefficient', 'abs_coefficient']].style.format({
                        'coefficient': '{:.4f}',
                        'abs_coefficient': '{:.4f}'
                    }),
                    hide_index=True
                )
                
                # Model Coefficients
                with st.expander("📊 All Model Coefficients"):
                    st.dataframe(
                        feature_importance[['feature', 'coefficient']].style.format({
                            'coefficient': '{:.4f}'
                        }),
                        hide_index=True
                    )
                
                # Prediction Samples
                st.markdown("#### Sample Predictions vs Actual")
                samples = st.session_state.predictor.get_prediction_samples(10)
                
                st.dataframe(
                    samples.style.format({
                        'actual': '{:.2f}',
                        'predicted': '{:.2f}',
                        'error': '{:.2f}'
                    }).background_gradient(subset=['error'], cmap='RdYlGn_r')
                )
                
                # Error Distribution
                st.markdown("#### Error Distribution Statistics")
                error_dist = st.session_state.predictor.get_error_distribution()
                
                error_df = pd.DataFrame({
                    'Statistic': ['Mean Error', 'Std Error', 'Min Error', 'Max Error', 'Median Error'],
                    'Value': [
                        error_dist['mean_error'],
                        error_dist['std_error'],
                        error_dist['min_error'],
                        error_dist['max_error'],
                        error_dist['median_error']
                    ]
                })
                
                st.dataframe(
                    error_df.style.format({'Value': '{:.3f}'}),
                    hide_index=True
                )
        
        # METHOD B: Linguistic Explanation
        with col_b:
            st.markdown("### 🗣️ Method B: Linguistic Explanation")
            st.markdown("*Natural language fuzzy reasoning*")
            
            with st.container():
                # Status indicator
                if st.session_state.data_source == 'entsoe':
                    st.markdown('<p class="status-live">🟢 LIVE DATA</p>', unsafe_allow_html=True)
                
                # Fuzzy Analysis
                if st.session_state.fuzzy_analysis:
                    fuzzy = FuzzyExplainer()
                    explanation = fuzzy.generate_explanation(st.session_state.fuzzy_analysis)
                    
                    st.markdown("#### 🔮 Fuzzy Linguistic Explanation")
                    st.markdown(explanation)
                    
                    # Color-coded current status
                    price_category = st.session_state.fuzzy_analysis['price']['category']
                    cons_category = st.session_state.fuzzy_analysis['consumption']['category']
                    
                    st.markdown("---")
                    st.markdown("#### Current Classification")
                    
                    status_cols = st.columns(2)
                    with status_cols[0]:
                        color = fuzzy.get_color_code(price_category)
                        st.markdown(f"**Price Level:** :{color}[{st.session_state.fuzzy_analysis['price']['linguistic'].upper()}]")
                    
                    with status_cols[1]:
                        color = fuzzy.get_color_code(cons_category)
                        st.markdown(f"**Consumption Level:** :{color}[{st.session_state.fuzzy_analysis['consumption']['linguistic'].upper()}]")
                
                # ENTSOE Market Context
                if (
                    st.session_state.market_context is not None
                    and isinstance(st.session_state.market_context, dict)
                    and st.session_state.market_context.get('data_available', False)
                ):
                    st.markdown("---")
                    st.markdown("#### 🌍 Real-Time Market Context")
                    
                    reason_extractor = ReasonExtractor()
                    market_insight = reason_extractor.generate_market_insight(st.session_state.market_context)
                    
                    st.markdown(market_insight)
                
                # Fuzzy Rules
                with st.expander("📋 View Fuzzy Inference Rules"):
                    fuzzy = FuzzyExplainer()
                    rules = fuzzy.generate_fuzzy_rules_summary()
                    st.markdown(rules)
        
        st.divider()
        
        # ===== ENHANCED EVALUATION FORM =====
        st.divider()
        st.header("📝 Comparative Evaluation Form")
        st.markdown("Help us improve by comparing the two explanation methods across multiple dimensions")
        
        eval_manager = st.session_state.eval_manager
        
        # Tabs for form and results
        tab_form, tab_results = st.tabs(["📋 Evaluation", "📊 Analytics"])
        
        with tab_form:
            st.markdown("### Method Comparison Questionnaire")
            st.info("Rate each method on the dimensions below. This helps us understand which approach works better for different audiences.")
            
            with st.form("evaluation_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    participant_id = st.text_input(
                        "Participant ID:",
                        placeholder="e.g., Student_001 or Expert_A01"
                    )
                
                with col2:
                    preference = st.selectbox(
                        "Which method do you prefer overall?",
                        ["Select an option", "Method A (Numerical)", "Method B (Linguistic)", "Both Equally", "Neither"]
                    )
                
                st.markdown("---")
                st.markdown("### Detailed Ratings (1 = Poor, 5 = Excellent)")
                
                # Create comparison cards
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.markdown("#### 📊 Method A: Numerical")
                    st.markdown("*Statistical metrics, feature importance, prediction samples*")
                    
                    method_a_helpfulness = st.slider(
                        "Helpfulness",
                        min_value=1, max_value=5, value=3,
                        help="How helpful for understanding price drivers?",
                        key="a_helpfulness"
                    )
                    
                    method_a_understandability = st.slider(
                        "Ease of Understanding",
                        min_value=1, max_value=5, value=3,
                        help="How easy to grasp the concepts?",
                        key="a_understandability"
                    )
                    
                    method_a_speed = st.slider(
                        "Quick Comprehension",
                        min_value=1, max_value=5, value=3,
                        help="How quickly can you understand the main points?",
                        key="a_speed"
                    )
                    
                    method_a_practical = st.slider(
                        "Practical Usefulness",
                        min_value=1, max_value=5, value=3,
                        help="How applicable to real-world decisions?",
                        key="a_practical"
                    )
                
                with col_b:
                    st.markdown("#### 🗣️ Method B: Linguistic")
                    st.markdown("*Natural language explanations with fuzzy reasoning*")
                    
                    method_b_helpfulness = st.slider(
                        "Helpfulness",
                        min_value=1, max_value=5, value=3,
                        help="How helpful for understanding price drivers?",
                        key="b_helpfulness"
                    )
                    
                    method_b_understandability = st.slider(
                        "Ease of Understanding",
                        min_value=1, max_value=5, value=3,
                        help="How easy to grasp the concepts?",
                        key="b_understandability"
                    )
                    
                    method_b_speed = st.slider(
                        "Quick Comprehension",
                        min_value=1, max_value=5, value=3,
                        help="How quickly can you understand the main points?",
                        key="b_speed"
                    )
                    
                    method_b_practical = st.slider(
                        "Practical Usefulness",
                        min_value=1, max_value=5, value=3,
                        help="How applicable to real-world decisions?",
                        key="b_practical"
                    )
                
                st.markdown("---")
                
                comments = st.text_area(
                    "📝 Additional Comments (Optional):",
                    placeholder="Share any observations, suggestions, or detailed feedback about either method...",
                    height=100
                )
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    submitted = st.form_submit_button("✅ Submit Evaluation", type="primary")
                with col2:
                    st.form_submit_button("Reset Form")
                
                if submitted:
                    if not participant_id or preference == "Select an option":
                        st.error("⚠️ Please fill in Participant ID and select a preference.")
                    else:
                        response = {
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'participant_id': participant_id,
                            'preference': preference,
                            'method_a_helpfulness': method_a_helpfulness,
                            'method_b_helpfulness': method_b_helpfulness,
                            'method_a_understandability': method_a_understandability,
                            'method_b_understandability': method_b_understandability,
                            'method_a_speed': method_a_speed,
                            'method_b_speed': method_b_speed,
                            'method_a_practical': method_a_practical,
                            'method_b_practical': method_b_practical,
                            'comments': comments,
                            'data_source': st.session_state.data_source
                        }
                        
                        # Save to database
                        if eval_manager.save_response(response):
                            st.success("✅ Thank you! Your evaluation has been recorded.")
                            st.balloons()
                        else:
                            st.error("❌ Error saving your response. Please try again.")
        
        with tab_results:
            st.markdown("### 📊 Evaluation Results & Analytics")
            
            responses_df = eval_manager.get_all_responses()
            total_count = eval_manager.get_response_count()
            
            if total_count > 0:
                st.success(f"✅ {total_count} evaluation(s) collected")
                
                # Key metrics
                analytics = eval_manager.get_analytics()
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Total Evaluations",
                        total_count
                    )
                
                with col2:
                    method_a_avg = analytics['method_a_avg_helpfulness']
                    st.metric(
                        "Method A Avg Helpfulness",
                        f"{method_a_avg:.2f}/5",
                        f"{(method_a_avg/5)*100:.0f}%"
                    )
                
                with col3:
                    method_b_avg = analytics['method_b_avg_helpfulness']
                    st.metric(
                        "Method B Avg Helpfulness",
                        f"{method_b_avg:.2f}/5",
                        f"{(method_b_avg/5)*100:.0f}%"
                    )
                
                with col4:
                    preference_data = analytics['preference_counts']
                    most_preferred = max(preference_data, key=preference_data.get) if preference_data else "N/A"
                    st.metric(
                        "Most Preferred",
                        most_preferred.split('(')[0].strip()
                    )
                
                st.divider()
                
                # Detailed Comparison Charts
                st.markdown("#### 📊 Detailed Methods Comparison")
                
                comparison_data = pd.DataFrame({
                    'Dimension': ['Helpfulness', 'Understandability', 'Speed', 'Practical'],
                    'Method A': [
                        analytics['method_a_avg_helpfulness'],
                        analytics['method_a_avg_understandability'],
                        analytics['method_a_avg_speed'],
                        analytics['method_a_avg_practical']
                    ],
                    'Method B': [
                        analytics['method_b_avg_helpfulness'],
                        analytics['method_b_avg_understandability'],
                        analytics['method_b_avg_speed'],
                        analytics['method_b_avg_practical']
                    ]
                })
                
                # Create custom comparison visualization
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.bar_chart(comparison_data.set_index('Dimension'), height=400)
                
                with col2:
                    st.markdown("**Interpretation:**")
                    for idx, row in comparison_data.iterrows():
                        winner = "🟢 Method A" if row['Method A'] > row['Method B'] else "🔵 Method B" if row['Method B'] > row['Method A'] else "⚪ Tie"
                        st.markdown(f"**{row['Dimension']}:** {winner}")
                
                st.divider()
                
                # Preference and additional charts
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Preference Distribution")
                    if 'preference_counts' in analytics and analytics['preference_counts']:
                        pref_df = pd.DataFrame(
                            list(analytics['preference_counts'].items()),
                            columns=['Preference', 'Count']
                        )
                        st.bar_chart(pref_df.set_index('Preference'))
                    else:
                        st.info("No preference data available yet")
                
                with col2:
                    st.markdown("#### Data Source Distribution")
                    if 'data_source_counts' in analytics and analytics['data_source_counts']:
                        source_df = pd.DataFrame(
                            list(analytics['data_source_counts'].items()),
                            columns=['Data Source', 'Count']
                        )
                        st.bar_chart(source_df.set_index('Data Source'))
                    else:
                        st.info("No data source info available")
                
                st.divider()
                
                # Participant Comments Section
                st.markdown("#### 💬 Participant Feedback & Comments")
                
                # Filter comments
                comments_df = responses_df[responses_df['comments'].notna() & (responses_df['comments'] != '')]
                
                if len(comments_df) > 0:
                    st.info(f"📝 {len(comments_df)} participant(s) provided comments")
                    
                    # Display comments in a nice format
                    for idx, row in comments_df.iterrows():
                        with st.expander(f"💭 {row['participant_id']} - {row['timestamp']} - Prefers: {row['preference']}"):
                            st.markdown(f"**Participant:** {row['participant_id']}")
                            st.markdown(f"**Timestamp:** {row['timestamp']}")
                            st.markdown(f"**Preference:** {row['preference']}")
                            st.markdown(f"**Ratings:**")
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown(f"- Method A Helpfulness: **{row['method_a_helpfulness']}/5**")
                                st.markdown(f"- Method A Understandability: **{row['method_a_understandability']}/5**")
                                st.markdown(f"- Method A Speed: **{row['method_a_speed']}/5**")
                                st.markdown(f"- Method A Practical: **{row['method_a_practical']}/5**")
                            with col_b:
                                st.markdown(f"- Method B Helpfulness: **{row['method_b_helpfulness']}/5**")
                                st.markdown(f"- Method B Understandability: **{row['method_b_understandability']}/5**")
                                st.markdown(f"- Method B Speed: **{row['method_b_speed']}/5**")
                                st.markdown(f"- Method B Practical: **{row['method_b_practical']}/5**")
                            st.divider()
                            st.markdown("**📝 Comment:**")
                            st.info(row['comments'])
                else:
                    st.info("No comments provided yet")
                
                st.divider()
                
                # Data table
                st.markdown("#### All Responses (Raw Data)")
                st.dataframe(
                    responses_df[['timestamp', 'participant_id', 'preference', 
                                  'method_a_helpfulness', 'method_b_helpfulness',
                                  'comments']],
                    
                )
                
                # Export options
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    csv_data = responses_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download as CSV",
                        data=csv_data,
                        file_name=f"evaluations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    json_data = responses_df.to_json(indent=2, orient='records')
                    st.download_button(
                        "📥 Download as JSON",
                        data=json_data,
                        file_name=f"evaluations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                
                with col3:
                    if st.button("🗑️ Clear All Responses", type="secondary"):
                        if eval_manager.delete_all_responses():
                            st.success("All responses cleared!")
                            st.rerun()
                        else:
                            st.error("Error clearing responses")
                
            else:
                st.info("📭 No evaluations collected yet. Fill out the evaluation form to get started!")

    else:
        # Instructions when model not trained
        st.info("👈 Please load data and train the model using the sidebar to begin")
        
        st.markdown("""
        ## How to Use This Dashboard
    
    ### Step 1: Select Data Source
    Choose from three options:
    - **Sample Data**: Pre-loaded 7 days of hourly data
    - **Upload CSV**: Provide your own dataset (requires: datetime, energy_consumption, price columns)
    - **Real-time ENTSOE Data**: Fetch live data from European energy markets (requires free API token)
    
    ### Step 2: Train Model
    Click "Train Model" to build the Linear Regression predictor with automated feature engineering
    
    ### Step 3: Compare Explanations
    View side-by-side comparison:
    - **Method A (Numerical)**: Statistical metrics, feature importance, prediction samples
    - **Method B (Linguistic)**: Natural language explanations using fuzzy logic + real market context
    
    ### Step 4: Provide Feedback
    Complete the evaluation form to help improve explainability methods
    
    ### Step 5: Export Results
    Download all responses as CSV for analysis
    
    ---
    
    ### About ENTSOE API
    To use real-time data, get your free API token at:
    **https://transparency.entsoe.eu/**
    
        Supported countries: Germany, France, Italy, Spain, Netherlands, Belgium, Austria, Poland, 
        Switzerland, Czech Republic, Denmark, Sweden, Norway, UK, Ireland, Portugal, Greece
        """)

# Footer
# st.divider()
# st.markdown("""
# <div style='text-align: center; color: #666; padding: 1rem;'>
#     <p>⚡ Energy Price & Consumption Explainability Dashboard | Dual Explanation System Research Tool</p>
#     <p><small>Powered by Scikit-learn, Scikit-fuzzy, and ENTSOE Transparency Platform API</small></p>
# </div>
# """, unsafe_allow_html=True)
