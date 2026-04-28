import { useState, useEffect } from 'react';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
import { Map } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { AlertTriangle, Info, Target } from 'lucide-react';

const PREDICT_API_URL = 'http://127.0.0.1:8000/api/predict';

const INITIAL_VIEW_STATE = {
  longitude: 0,
  latitude: 20,
  zoom: 1.5,
  pitch: 0,
  bearing: 0
};

export default function PredictPage() {
  const [predictions, setPredictions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hoverInfo, setHoverInfo] = useState(null);

  useEffect(() => {
    fetch(PREDICT_API_URL)
      .then(res => res.json())
      .then(data => {
        setPredictions(data);
        setIsLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch predictions", err);
        setIsLoading(false);
      });
  }, []);

  const layers = [
    new ScatterplotLayer({
      id: 'prediction-hotspots',
      data: predictions,
      pickable: true,
      opacity: 0.8,
      stroked: true,
      filled: true,
      radiusScale: 6,
      radiusMinPixels: 10,
      radiusMaxPixels: 100,
      lineWidthMinPixels: 1,
      getPosition: d => [d.longitude, d.latitude],
      getFillColor: d => {
        if (d.risk_ratio > 2.0) return [255, 50, 50, 200]; // Critical
        if (d.risk_ratio > 1.0) return [255, 140, 0, 200]; // Overdue
        return [255, 255, 100, 150]; // Low risk
      },
      getLineColor: d => [255, 255, 255, 200],
      getRadius: d => d.risk_ratio * 30000,
      onHover: info => setHoverInfo(info)
    })
  ];

  return (
    <div className="map-page-container" style={{display: 'flex', flexDirection: 'row'}}>
      {/* Sidebar Predictions Feed */}
      <div className="live-sidebar" style={{
        width: '400px', 
        height: '100%', 
        background: 'var(--panel-bg)',
        borderRight: '1px solid var(--border-color)',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        boxSizing: 'border-box'
      }}>
        <div style={{padding: '20px', borderBottom: '1px solid rgba(255,255,255,0.1)'}}>
          <h2 style={{margin: '0 0 10px 0', color: '#fff', display: 'flex', alignItems: 'center', gap: '10px'}}>
            <Target color="var(--accent-color)" /> Seismic Forecast
          </h2>
          
          <div style={{background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '8px', fontSize: '12px', color: '#8892b0', lineHeight: '1.5', marginTop: '15px'}}>
            <h4 style={{margin: '0 0 5px 0', color: '#c5c6c7', display: 'flex', alignItems: 'center', gap: '5px'}}>
              <Info size={14} /> The Seismic Gap Theory
            </h4>
            While exact prediction is impossible, this algorithm forecasts long-term probabilities. It calculates the historical average gap between Major Earthquakes (Mag &gt; 6.5) for each region. If the time since the last event exceeds this average, the region is mathematically "overdue" (Risk Ratio &gt; 1.0).
          </div>
        </div>
        
        <div style={{flexGrow: 1, overflowY: 'auto', padding: '15px', display: 'flex', flexDirection: 'column', gap: '15px'}}>
          {isLoading ? (
            <p style={{color: 'var(--accent-color)', textAlign: 'center'}}>Analyzing 125 years of seismic data...</p>
          ) : (
            predictions.map((p, i) => (
              <div key={p.country} className="live-card" style={{
                background: 'var(--glass-bg)',
                border: `1px solid ${p.risk_ratio > 2.0 ? '#ff3232' : p.risk_ratio > 1.0 ? '#ff8c00' : 'rgba(102, 252, 241, 0.3)'}`,
                borderRadius: '8px',
                padding: '15px',
                position: 'relative'
              }}>
                <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '8px', alignItems: 'center'}}>
                  <span style={{
                    fontSize: '10px', 
                    textTransform: 'uppercase', 
                    background: p.risk_ratio > 2.0 ? 'rgba(255,50,50,0.2)' : p.risk_ratio > 1.0 ? 'rgba(255,140,0,0.2)' : 'rgba(255,255,100,0.1)',
                    color: p.risk_ratio > 2.0 ? '#ff3232' : p.risk_ratio > 1.0 ? '#ff8c00' : '#ffff64',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontWeight: 'bold'
                  }}>
                    Risk Ratio: {p.risk_ratio}x
                  </span>
                  <span style={{fontSize: '11px', color: '#8892b0'}}>#{i + 1} Most Overdue</span>
                </div>
                <h4 style={{margin: '0 0 10px 0', color: '#fff', fontSize: '16px'}}>{p.country}</h4>
                
                <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '12px'}}>
                  <div>
                    <div style={{color: '#8892b0'}}>Avg Frequency</div>
                    <div style={{color: '#c5c6c7', fontWeight: 'bold'}}>Every {p.avg_gap_years} yrs</div>
                  </div>
                  <div>
                    <div style={{color: '#8892b0'}}>Last Major Event</div>
                    <div style={{color: '#ff6b6b', fontWeight: 'bold'}}>{p.last_event_year} ({p.years_since_last} yrs ago)</div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Map */}
      <div style={{flexGrow: 1, position: 'relative'}}>
        <DeckGL
          initialViewState={INITIAL_VIEW_STATE}
          controller={true}
          layers={layers}
          onViewStateChange={() => {
            if (hoverInfo) setHoverInfo(null);
          }}
        >
          <Map mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json" />
        </DeckGL>
        
        {/* Indicator */}
        <div style={{position: 'absolute', top: '20px', right: '20px', display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--glass-bg)', padding: '8px 15px', borderRadius: '20px', border: '1px solid var(--border-color)', color: '#fff', fontSize: '12px'}}>
          <AlertTriangle size={14} color="#ff3232" />
          Global Seismic Gap Hotspots
        </div>
      </div>

      {hoverInfo && hoverInfo.object && (
        <div className="tooltip" style={{ left: hoverInfo.x, top: hoverInfo.y }}>
          <h3 style={{
             color: hoverInfo.object.risk_ratio > 2.0 ? '#ff3232' : hoverInfo.object.risk_ratio > 1.0 ? '#ff8c00' : '#ffff64',
             borderBottom: 'none', margin: '0 0 5px 0'
          }}>{hoverInfo.object.country}</h3>
          <p style={{margin: 0, color: '#8892b0'}}>Risk Ratio: {hoverInfo.object.risk_ratio}x</p>
          <p style={{margin: '2px 0 0 0', color: '#8892b0'}}>Years Overdue: {hoverInfo.object.years_since_last - hoverInfo.object.avg_gap_years > 0 ? (hoverInfo.object.years_since_last - hoverInfo.object.avg_gap_years).toFixed(1) : 0}</p>
        </div>
      )}
    </div>
  );
}
