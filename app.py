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
st.markdown('<h1 class="main-header">⚡ Energy Price & Consumption Explainability Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Dual Explanation System: Numerical Analysis vs. Linguistic Fuzzy Reasoning</p>', unsafe_allow_html=True)

# Main navigation
main_mode = st.radio(
    "Select Module:",
    ["🔮 Price Forecasting & Analysis", "💰 Bill Analysis & Optimization"],
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
    st.header("💰 Electricity Bill Analysis & Optimization")
    
    # Initialize session state for billing analysis
    if 'billing_analysis' not in st.session_state:
        st.session_state.billing_analysis = None
    if 'billing_params' not in st.session_state:
        st.session_state.billing_params = {}
    
    analyzer = BillingAnalyzer()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Enter Your Bill Information")
        
        bill_amount = st.number_input(
            "Total Monthly Bill Amount (€):",
            min_value=0.0,
            max_value=10000.0,
            value=100.0,
            step=5.0,
            help="Enter your total electricity bill for the month"
        )
        
        rate_structure = st.selectbox(
            "Select Your Rate Plan:",
            ["Residential - Standard", "Residential - Time-of-Use", "Commercial"],
            help="Choose your electricity rate structure"
        )
        
        col_a, col_b = st.columns(2)
        with col_a:
            know_units = st.checkbox("I know my consumption (kWh)")
        
        units_consumed = None
        if know_units:
            with col_b:
                units_consumed = st.number_input(
                    "Total Units Consumed (kWh):",
                    min_value=0.0,
                    value=300.0,
                    step=10.0
                )
    
    with col2:
        st.info("""
        **How it works:**
        
        Enter your monthly bill amount and we'll analyze:
        - Estimated consumption
        - Cost breakdown
        - Usage patterns
        - Optimization opportunities
        - Potential savings
        """)
    
    if st.button("🔍 Analyze My Bill", type="primary", use_container_width=True):
        with st.spinner("Analyzing your electricity bill..."):
            st.session_state.billing_analysis = analyzer.analyze_bill(bill_amount, rate_structure, units_consumed)
            st.session_state.billing_params = {
                'bill_amount': bill_amount,
                'rate_structure': rate_structure,
                'units_consumed': units_consumed
            }
    
    # Display analysis if available
    if st.session_state.billing_analysis is not None:
        analysis = st.session_state.billing_analysis
        bill_amount = st.session_state.billing_params['bill_amount']
        rate_structure = st.session_state.billing_params['rate_structure']
        
        st.success("✅ Analysis Complete!")
            
        # Main metrics
        st.subheader("📊 Bill Breakdown")
        col1, col2, col3, col4 = st.columns(4)
            
        with col1:
            st.metric("Total Bill", f"€{analysis['total_bill']:.2f}")
        with col2:
            st.metric("Estimated Units", f"{analysis['estimated_units']:.1f} kWh")
        with col3:
            st.metric("Cost per kWh", f"€{analysis['cost_per_unit']:.3f}")
        with col4:
            st.metric("Daily Cost", f"€{analysis['daily_cost']:.2f}")
        
        st.divider()
            
        # Detailed breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💡 Consumption Details")
                
            st.markdown(f"""
            **Peak Hours Usage** (6 AM - 10 PM)
            - Units: **{analysis['peak_units']:.1f} kWh** ({analysis['peak_units']/analysis['estimated_units']*100:.0f}%)
            - Cost: **€{analysis['peak_charges']:.2f}**
            - Rate: **€{analysis['rates']['peak_rate']:.3f}/kWh**
            
            **Off-Peak Usage** (10 PM - 6 AM)
            - Units: **{analysis['off_peak_units']:.1f} kWh** ({analysis['off_peak_units']/analysis['estimated_units']*100:.0f}%)
            - Cost: **€{analysis['off_peak_charges']:.2f}**
            - Rate: **€{analysis['rates']['off_peak_rate']:.3f}/kWh**
            
            **Daily Average:** {analysis['daily_units']:.1f} kWh/day
            **Hourly Average:** {analysis['hourly_units']:.2f} kWh/hour
            """)
        
        with col2:
            st.subheader("💰 Cost Breakdown")
                
            # Create breakdown chart data
            breakdown_data = pd.DataFrame({
                'Component': ['Peak Energy', 'Off-Peak Energy', 'Fixed Charges', 'Taxes'],
                'Amount (€)': [
                    analysis['peak_charges'],
                    analysis['off_peak_charges'],
                    analysis['fixed_charges'],
                    analysis['tax_amount']
                ]
            })
            
            st.dataframe(breakdown_data, hide_index=True, use_container_width=True)
            
            st.markdown(f"""
            **Subtotal:** €{analysis['energy_charges'] + analysis['fixed_charges']:.2f}
            **Tax ({analysis['rates']['tax_rate']*100:.0f}%):** €{analysis['tax_amount']:.2f}
            **Total:** €{analysis['total_bill']:.2f}
            """)
        
        st.divider()
            
        # Insights
        st.subheader("🔍 Insights & Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **{analysis['insights']['consumption_level']}**
            
            **{analysis['insights']['cost_efficiency']}**
            
            **{analysis['insights']['comparison']}**
            """)
        
        with col2:
            st.markdown("**💡 Recommendations:**")
            for rec in analysis['insights']['recommendations']:
                st.markdown(f"- {rec}")
        
        st.divider()

        # Dual explanation system for billing
        st.subheader("🧭 Dual Explanation: Numerical vs Linguistic")
        tab_a, tab_b = st.tabs(["📊 Method A (Numerical)", "🗣️ Method B (Linguistic)"])

        with tab_a:
            st.markdown("**What you see:** dense numerical decomposition and cost engineering view")
            st.markdown(
                "Using a granular allocation, total cost can be expressed as: "
                "$C = E_p \, r_p + E_o \, r_o + F + T$, where $E_p$/$E_o$ are peak/off-peak kWh, $r_p$/$r_o$ are tariffs, $F$ fixed charges, $T$ tax."
            )
            col_a1, col_a2, col_a3 = st.columns(3)
            with col_a1:
                st.metric("Levelized Cost (LCU)", f"€{analysis['cost_per_unit']:.3f}/kWh")
            with col_a2:
                st.metric("Peak Share", f"{analysis['peak_units']/analysis['estimated_units']*100:.0f}% of energy")
            with col_a3:
                st.metric("Duty Cycle", f"{analysis['daily_units']:.1f} kWh/day")

            st.markdown("**Driver stack (numeric):**")
            st.markdown(f"- Peak cost vector: **€{analysis['peak_charges']:.2f}** at **€{analysis['rates']['peak_rate']:.3f}/kWh** → dominant marginal component")
            st.markdown(f"- Off-peak component: **€{analysis['off_peak_charges']:.2f}** at **€{analysis['rates']['off_peak_rate']:.3f}/kWh**")
            st.markdown(f"- Non-energy overhead (F+T): **€{analysis['fixed_charges'] + analysis['tax_amount']:.2f}** reducing elasticity of savings")
            st.markdown("- Sensitivity: shifting 10% of peak to off-peak reduces blended LCU proportionally to the tariff differential.")

        with tab_b:
            st.markdown("**What you see:** natural language, plain-English takeaway")
            st.info(
                f"Your bill of €{analysis['total_bill']:.2f} likely comes from about {analysis['estimated_units']:.0f} kWh. "
                f"Around {analysis['peak_units']/analysis['estimated_units']*100:.0f}% happens in expensive peak hours; moving some of that to cheaper off-peak hours can lower the average price."
            )
            st.markdown("**Plain-language highlights:**")
            st.markdown("- Peak-time use is the costly part; run big appliances outside peak when possible.")
            st.markdown("- Fixed and tax portions stay the same, but timing changes can still trim the energy part.")
            st.markdown("- If you’re far above a ~300 kWh/month benchmark, focus on trimming peak-heavy loads first.")
            
        # Savings calculator
        with st.expander("💰 Potential Savings Calculator", expanded=True):
            optimization_level = st.select_slider(
                "Select Optimization Strategy:",
                options=["conservative", "moderate", "aggressive"],
                value="moderate",
                key="optimization_level_slider"
            )
            
            savings = analyzer.calculate_potential_savings(bill_amount, rate_structure, optimization_level)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Monthly Savings",
                    f"€{savings['monthly_savings']:.2f}",
                    f"{savings['percentage_savings']:.1f}% reduction"
                )
            
            with col2:
                st.metric(
                    "Annual Savings",
                    f"€{savings['annual_savings']:.2f}",
                    "Estimated"
                )
            
            with col3:
                st.metric(
                    "Optimized Bill",
                    f"€{savings['optimized_bill']:.2f}",
                    f"-€{savings['monthly_savings']:.2f}"
                )
            
            st.markdown(f"**Strategy:** {savings['description']}")
            
            st.markdown("**🎯 Actions to Take:**")
            for action in savings['actions']:
                st.markdown(f"- {action}")
            
            # Comparison chart
            st.subheader("📊 Before vs After Comparison")
            
            comparison_df = pd.DataFrame({
                'Category': ['Current Bill', 'Optimized Bill', 'Monthly Savings'],
                'Amount (€)': [
                    savings['current_bill'],
                    savings['optimized_bill'],
                    savings['monthly_savings']
                ]
            })
            
            st.bar_chart(comparison_df.set_index('Category'))

# ===== PRICE FORECASTING MODULE (Original Content) =====
elif main_mode == "🔮 Price Forecasting & Analysis":

    # Main content
    if st.session_state.model_trained and st.session_state.predictor is not None:
        st.success("✅ Model is trained and ready for explanation analysis")
        
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
        
        tab1, tab2, tab3 = st.tabs(["Price Patterns", "Load Profiles", "Price-Load Relationship"])
        
        with tab1:
            st.markdown("### Electricity Price Over Time")
            price_chart_df = st.session_state.df[['datetime', 'price']].copy()
            price_chart_df = price_chart_df.set_index('datetime')
            st.line_chart(price_chart_df, use_container_width=True)
            
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
                st.line_chart(load_chart_df, use_container_width=True)
                
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
        
            with tab3:
                st.markdown("### Price-Load Correlation")
                scatter_df = st.session_state.df[['energy_consumption', 'price']].copy()
                scatter_df.columns = ['Load (MW)', 'Price (€/MWh)']
                st.scatter_chart(scatter_df, x='Load (MW)', y='Price (€/MWh)')
            
            correlation = st.session_state.df['energy_consumption'].corr(st.session_state.df['price'])
            st.metric("Pearson Correlation", f"{correlation:.3f}")
            
            if abs(correlation) > 0.7:
                st.success("✅ Strong correlation: Price heavily influenced by demand")
            elif abs(correlation) > 0.4:
                st.info("ℹ️ Moderate correlation: Price partially driven by demand")
            else:
                st.warning("⚠️ Weak correlation: Other factors may dominate pricing")
        
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
                    use_container_width=True
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
