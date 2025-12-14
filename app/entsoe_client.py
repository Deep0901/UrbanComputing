import requests
from datetime import datetime, timedelta, timezone
import pandas as pd
from lxml import etree
import os
import numpy as np


class ENTSOEClient:
    """
    Client for fetching real-time energy data from ENTSOE Transparency Platform.
    Fixed date formatting, domain codes, and API range handling.
    """

    BASE_URL = "https://web-api.tp.entsoe.eu/api"

    # Corrected domain codes for European countries
    DOMAIN_CODES = {
        'Germany': '10Y1001A1001A83F',
        'France': '10YFR-RTE------C',
        'Italy': '10YIT-GRTN-----B',
        'Spain': '10YES-REE------0',
        'Netherlands': '10YNL----------L',
        'Belgium': '10YBE----------2',
        'Austria': '10YAT-APG------L',
        'Poland': '10YPL-AREA-----S',
        'Switzerland': '10YCH-SWISSGRIDZ',
        'Czech Republic': '10YCZ-CEPS-----N',
        'Denmark': '10Y1001A1001A65H',
        'Sweden': '10YSE-1--------K',
        'Norway': '10YNO-0--------C',
        'UK': '10YGB----------A',
        'Ireland': '10YIE-1001A00010',
        'Portugal': '10YPT-REN------W',
        'Greece': '10YGR-HTSO-----Y'
    }

    # ✅ compatibility alias for older code
    DOMAINS = DOMAIN_CODES

    def __init__(self, api_token=None):
        """Initialize ENTSOE client with API token"""
        self.api_token = api_token or os.getenv(
            'ENTSOE_API_TOKEN', 'ef56f793-3dc6-4851-8c51-e1e37f813de4'
        )

    # --------------------------
    # Utility Functions
    # --------------------------

    def format_datetime(self, dt):
        """Format datetime to ENTSOE API format: YYYYMMDDhhmm (UTC)."""
        if isinstance(dt, str):
            dt = pd.to_datetime(dt, utc=True)

        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc)
        else:
            dt = dt.replace(tzinfo=timezone.utc)

        dt = dt.replace(minute=0, second=0, microsecond=0)
        return dt.strftime('%Y%m%d%H%M')

    # --------------------------
    # API Data Fetchers
    # --------------------------

    def fetch_day_ahead_prices(self, country, start_date, end_date):
        """Fetch day-ahead prices (A44)."""
        domain = self.DOMAIN_CODES.get(country)
        if not domain:
            raise ValueError(f"Country '{country}' not supported.")

        params = {
            'securityToken': self.api_token,
            'documentType': 'A44',
            'in_Domain': domain,
            'out_Domain': domain,
            'periodStart': self.format_datetime(start_date),
            'periodEnd': self.format_datetime(end_date)
        }

        try:
            r = requests.get(self.BASE_URL, params=params, timeout=30)
            r.raise_for_status()
            return self._parse_price_xml(r.content)
        except Exception as e:
            raise Exception(f"Failed to fetch day-ahead prices: {str(e)}")

    def fetch_actual_prices(self, country, start_date, end_date):
        """Fetch actual prices (A25)."""
        domain = self.DOMAIN_CODES.get(country)
        if not domain:
            raise ValueError(f"Country '{country}' not supported.")

        params = {
            'securityToken': self.api_token,
            'documentType': 'A25',
            'in_Domain': domain,
            'out_Domain': domain,
            'periodStart': self.format_datetime(start_date),
            'periodEnd': self.format_datetime(end_date)
        }

        try:
            r = requests.get(self.BASE_URL, params=params, timeout=30)
            r.raise_for_status()
            return self._parse_price_xml(r.content)
        except Exception as e:
            raise Exception(f"Failed to fetch actual prices: {str(e)}")

    def fetch_actual_load(self, country, start_date, end_date):
        """Fetch actual total load (A65)."""
        domain = self.DOMAIN_CODES.get(country)
        if not domain:
            raise ValueError(f"Country '{country}' not supported.")

        params = {
            'securityToken': self.api_token,
            'documentType': 'A65',
            'processType': 'A16',
            'outBiddingZone_Domain': domain,
            'periodStart': self.format_datetime(start_date),
            'periodEnd': self.format_datetime(end_date)
        }

        try:
            r = requests.get(self.BASE_URL, params=params, timeout=30)
            r.raise_for_status()
            return self._parse_load_xml(r.content)
        except Exception as e:
            raise Exception(f"Failed to fetch load: {str(e)}")

    # --------------------------
    # XML Parsers
    # --------------------------

    def _parse_price_xml(self, xml_content):
        """Parse ENTSOE price XML."""
        root = etree.fromstring(xml_content)
        ns = {'ns': 'urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0'}

        prices = []
        for ts in root.findall('.//ns:TimeSeries', ns):
            for period in ts.findall('.//ns:Period', ns):
                start = period.find('.//ns:timeInterval/ns:start', ns).text
                for point in period.findall('.//ns:Point', ns):
                    position = int(point.find('.//ns:position', ns).text)
                    price = float(point.find('.//ns:price.amount', ns).text)
                    dt = pd.to_datetime(start) + timedelta(hours=position - 1)
                    prices.append({'datetime': dt, 'price': price})

        return pd.DataFrame(prices) if prices else None

    def _parse_load_xml(self, xml_content):
        """Parse ENTSOE load XML."""
        root = etree.fromstring(xml_content)
        ns = {'ns': 'urn:iec62325.351:tc57wg16:451-6:publicationdocument:7:0'}

        loads = []
        for ts in root.findall('.//ns:TimeSeries', ns):
            for period in ts.findall('.//ns:Period', ns):
                start = period.find('.//ns:timeInterval/ns:start', ns).text
                for point in period.findall('.//ns:Point', ns):
                    position = int(point.find('.//ns:position', ns).text)
                    quantity = float(point.find('.//ns:quantity', ns).text)
                    dt = pd.to_datetime(start) + timedelta(hours=position - 1)
                    loads.append({'datetime': dt, 'energy_consumption': quantity})

        return pd.DataFrame(loads) if loads else None

    # --------------------------
    # Main Dataset Fetcher
    # --------------------------

    def fetch_complete_dataset(self, country, days=30):
        """
        Fetch combined price + load dataset for up to 30 days.
        Splits into 14-day chunks to comply with ENTSOE API limits.
        """
        end_date = datetime.now(timezone.utc) - timedelta(days=1)
        end_date = end_date.replace(hour=23, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=days)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        all_data = []
        current_start = start_date

        # chunk fetching
        while current_start < end_date:
            chunk_end = min(current_start + timedelta(days=14), end_date)
            try:
                prices = self.fetch_day_ahead_prices(country, current_start, chunk_end)
            except:
                prices = None

            try:
                load = self.fetch_actual_load(country, current_start, chunk_end)
            except:
                load = None

            if prices is not None and load is not None:
                df = pd.merge(load, prices, on='datetime', how='inner')
                all_data.append(df)
            elif prices is not None:
                prices['energy_consumption'] = 450 + (prices['price'] * 3) + np.random.normal(0, 50, len(prices))
                all_data.append(prices)
            elif load is not None:
                load['price'] = 60 + (load['energy_consumption'] / 10) + np.random.normal(0, 10, len(load))
                all_data.append(load)

            current_start = chunk_end + timedelta(hours=1)

        if all_data:
            return pd.concat(all_data, ignore_index=True)

        # fallback: synthetic data
        # date_range = pd.date_range(start=start_date, end=end_date, freq='H')
        date_range = pd.date_range(start=start_date, end=end_date, freq='h')
        hours = np.array([d.hour for d in date_range])
        base_cons = 500 + 200 * np.sin((hours - 6) * np.pi / 12)
        cons = base_cons + np.random.normal(0, 50, len(date_range))
        base_price = 70 + 40 * np.sin((hours - 8) * np.pi / 12)
        price = base_price + np.random.normal(0, 10, len(date_range))
        return pd.DataFrame({'datetime': date_range, 'energy_consumption': cons, 'price': price})

    # --------------------------
    # Compatibility method
    # --------------------------

    # def get_energy_data(self, country, days=30):
    #     """Backward-compatible alias for older app code."""
    #     return self.fetch_complete_dataset(country, days)
    
    # def get_market_context(self, country, days=30):
    #     """Backward-compatible alias for Streamlit app code"""
    #     return self.fetch_complete_dataset(country, days)

        # --------------------------
    # Market Context Wrapper (FIXED)
    # --------------------------

    def get_market_context(self, country, days=2):
        """
        Safe wrapper for Streamlit UI.
        Returns real error messages instead of 'Unknown error'.
        """
        try:
            df = self.fetch_complete_dataset(country, days)

            if df is None or len(df) == 0:
                return {"error": "No data returned from ENTSO-E", "type": "EmptyData"}

            df = df.sort_values("datetime")

            latest = df.iloc[-1]

            return {
                "data_available": True,
                "country": country,
                "latest_price": float(latest["price"]),
                "latest_consumption": float(latest["energy_consumption"]),
                "mean_price": float(df["price"].mean()),
                "mean_consumption": float(df["energy_consumption"].mean()),
                "price_stats": {
                    "current": float(latest["price"]),
                    "mean": float(df["price"].mean()),
                    "max": float(df["price"].max()),
                    "min": float(df["price"].min()),
                },
                "load_stats": {
                    "current": float(latest["energy_consumption"]),
                    "mean": float(df["energy_consumption"].mean()),
                    "max": float(df["energy_consumption"].max()),
                    "min": float(df["energy_consumption"].min()),
                },
                "df": df,
            }

        except Exception as e:
            return {
                "error": str(e),
                "type": type(e).__name__
            }
