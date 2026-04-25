import pandas as pd
try:
    print("Testing Tsunamis download...")
    df = pd.read_csv("https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/events/download", sep='\t')
    print(f"Downloaded {len(df)} tsunamis")
except Exception as e:
    print(e)
    
try:
    print("Testing Volcanoes events download...")
    df = pd.read_csv("https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/volcanoes/events/download", sep='\t')
    print(f"Downloaded {len(df)} volcano events")
except Exception as e:
    print(e)
    
try:
    print("Testing Volcanoes locs download...")
    df = pd.read_csv("https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/volcanoes/locs/download", sep='\t')
    print(f"Downloaded {len(df)} volcano locs. Columns: {df.columns.tolist()[:5]}")
except Exception as e:
    print(e)
