# debug_entsoe.py
import traceback
from app.entsoe_client import ENTSOEClient

def main():
    print("Python executable:", __import__("sys").executable)
    # If you have a real token, set it here or export ENTSOE_API_TOKEN before running:
    # client = ENTSOEClient(api_token="YOUR_TOKEN")
    client = ENTSOEClient(api_token=None)

    try:
        ctx = client.get_market_context("Germany", days=2)
        print("RETURNED (type):", type(ctx))
        if isinstance(ctx, dict):
            for k, v in ctx.items():
                if k == "df" and v is not None:
                    print("df head:")
                    print(v.head().to_string())
                else:
                    print(f"{k}: {v}")
        else:
            print(ctx)
    except Exception:
        print("EXCEPTION:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
