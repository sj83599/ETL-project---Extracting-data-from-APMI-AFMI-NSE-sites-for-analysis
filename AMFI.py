import requests
import pandas as pd
from datetime import datetime , timedelta
import calendar
import os

# =====================================
# INPUT DATE RANGE
# =====================================
start_date = "2026-01-01"
end_date = datetime.today().strftime("%Y-%m-%d")

start = datetime.strptime(start_date, "%Y-%m-%d")
end = datetime.strptime(end_date, "%Y-%m-%d")

# =====================================
# OUTPUT FOLDER
# =====================================
output_folder = "AMFI_Data"
os.makedirs(output_folder, exist_ok=True)

# =====================================
# REQUIRED SD_IDs
# =====================================
required_sd_ids = {
    119568,  # Aditya Birla SL Liquid Fund - Growth - Direct
    118474,  # BANDHAN Arbitrage Fund - Direct - Growth
    118364,  # BANDHAN Liquid Fund - Direct - Growth
    119125,  # DSP Liquidity Fund - Direct - Growth
    118968,  # HDFC Balanced Advantage Fund - Direct - Growth
    119091,  # HDFC Liquid Fund - Growth Option - Direct
    100868,  # HDFC Liquid Fund - Growth Plan
    130503,  # HDFC Small Cap Fund - Growth Option - Direct
    120364,  # ICICI Pru Arbitrage Fund - Direct - Growth
    120743,  # ICICI Pru Long Term Bond Fund - Direct - Growth
    119771,  # Kotak Arbitrage Fund - Direct - Growth
    144335,  # Kotak Balanced Advantage Fund - Direct - Growth
    106193,  # KOTAK GOLD ETF
    119766,  # Kotak Liquid Fund - Direct - Growth
    118778,  # Nippon India Small Cap Fund - Direct - Growth
    119574,  # SBI Arbitrage Opportunities Fund - Direct - Growth
    119800   # SBI Liquid Fund - Direct - Growth
}

# =====================================
# FUNCTION TO GET LAST DAY OF MONTH
# =====================================
def get_month_end(year, month):
    last_day = calendar.monthrange(year, month)[1]
    dt = datetime(year, month, last_day)

    # Saturday -> Friday
    if dt.weekday() == 5:
        dt -= timedelta(days=1)

    # Sunday -> Friday
    elif dt.weekday() == 6:
        dt -= timedelta(days=2)

    return dt

# =====================================
# START LOOP
# =====================================
year = start.year
month = start.month

while True:

    month_end = get_month_end(year, month)

    if month_end > end:
        break

    date_str = month_end.strftime("%Y-%m-%d")

    print(f"\nFetching data for {date_str}...")

    url = "https://www.amfiindia.com/api/nav-history"

    params = {
        "query_type": "all_for_date",
        "from_date": date_str
    }

    rows = []

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()

        json_data = response.json()

        for fund in json_data.get("data", []):

            amc_name = fund.get("mfName", "")

            for scheme in fund.get("schemes", []):

                scheme_name = scheme.get("schemeName", "")

                for nav in scheme.get("navs", []):

                    try:
                        sd_id = int(nav.get("SD_ID"))
                    except (TypeError, ValueError):
                        continue

                    # Filter only required schemes
                    if sd_id not in required_sd_ids:
                        continue

                    rows.append({
                        "Month_End_Date": date_str,
                        "AMC": amc_name,
                        "Scheme_Name": scheme_name,
                        "SD_ID": sd_id,
                        "NAV_Name": nav.get("NAV_Name"),
                        "NAV": nav.get("hNAV_Amt"),
                        "ISIN_RI": nav.get("ISIN_RI"),
                        "ISIN_PO": nav.get("ISIN_PO"),
                        "NAV_Date": nav.get("hNAV_Date"),
                        "Timestamp": nav.get("hNAV_Dtstamp"),
                        "Upload_Display": nav.get("hNAV_Upload_display")
                    })

    except Exception as e:
        print(f"Error fetching {date_str}: {e}")
        rows = []

    # =====================================
    # SAVE TO EXCEL
    # =====================================
    if rows:

        df = pd.DataFrame(rows)

        df["NAV_Date"] = pd.to_datetime(
            df["NAV_Date"],
            errors="coerce"
        ).dt.date

        df["NAV"] = pd.to_numeric(df["NAV"], errors="coerce")

        df = df.sort_values(
            by=["AMC", "Scheme_Name", "NAV_Date"]
        )

        file_name = f"AMFI_NAV_{date_str}.xlsx"
        file_path = os.path.join(output_folder, file_name)

        df.to_excel(file_path, index=False)

        print(f"Saved {len(df)} records to {file_name}")

    else:
        print(f"No matching schemes found for {date_str}")

    # Move to next month
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1

print("\n===================================")
print("All files downloaded successfully.")
print("Output Folder:", output_folder)
print("===================================")