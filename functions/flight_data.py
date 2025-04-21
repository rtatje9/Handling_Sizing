import pandas as pd

def load_excel_data(file_path):
    """
    Loads flight data from an Excel file and returns:
    - Full DataFrame
    - Lists for: flight IDs, airports, departure hours, minutes, and days (Debugging)
    """

    # Read Excel file
    df = pd.read_excel(file_path)

    # Clean column names (remove spaces)
    df.columns = [col.strip() for col in df.columns]

    # Drop rows with any missing values in relevant columns
    required_columns = ['ID', 'Airport', 'Time', 'Day']
    df = df.dropna(subset=required_columns)

    # Parse date column to date data type
    df['Day'] = pd.to_datetime(df['Day'], dayfirst=True)

    # Force 'Time' column into 'HH:MM' format (ignore seconds if any)
    df['Departure Time'] = pd.to_datetime(df['Time'].astype(str).str[:5], format='%H:%M').dt.time

    # Extract hour and minute values from 'Departure Time'
    df['Hour'] = df['Departure Time'].apply(lambda t: t.hour)
    df['Minute'] = df['Departure Time'].apply(lambda t: t.minute)

    # Extract columns as individual variables (For debbugging)
    flight_ids = df['ID'].tolist()
    airports = df['Airport'].tolist()
    hours = df['Hour'].tolist()
    minutes = df['Minute'].tolist()
    days = df['Day'].tolist()

    return df