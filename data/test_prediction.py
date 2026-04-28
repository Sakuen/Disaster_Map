import sqlite3
import pandas as pd

def test_prediction():
    conn = sqlite3.connect('../backend/disasters.db')
    df = pd.read_sql_query("SELECT year, country, magnitude FROM disasters WHERE type='earthquake' AND magnitude >= 6.5 AND country IS NOT NULL AND country != 'Unknown' ORDER BY year ASC", conn)
    
    predictions = []
    
    for country, group in df.groupby('country'):
        if len(group) < 5:
            continue # Need enough data points
            
        years = group['year'].unique()
        if len(years) < 2: continue
            
        # Calculate gaps between significant earthquakes
        gaps = [years[i] - years[i-1] for i in range(1, len(years))]
        avg_gap = sum(gaps) / len(gaps)
        last_event = max(years)
        years_since_last = 2026 - last_event
        
        # Likelihood heuristic: if years_since_last > avg_gap, higher risk
        risk_ratio = years_since_last / avg_gap if avg_gap > 0 else 0
        
        predictions.append({
            'country': country,
            'events_count': len(group),
            'avg_gap_years': round(avg_gap, 1),
            'last_event_year': last_event,
            'years_since_last': years_since_last,
            'risk_ratio': round(risk_ratio, 2)
        })
        
    predictions.sort(key=lambda x: x['risk_ratio'], reverse=True)
    
    print("Top 10 High Risk Regions (Seismic Gap Theory):")
    for p in predictions[:10]:
        print(p)

if __name__ == "__main__":
    test_prediction()
