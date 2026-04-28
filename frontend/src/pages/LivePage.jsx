import { useState, useEffect, useMemo } from 'react';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
import { Map } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { AlertTriangle, Activity, Bell, Clock } from 'lucide-react';

const LIVE_API_URL = 'http://127.0.0.1:8000/api/live';

const INITIAL_VIEW_STATE = {
  longitude: 0,
  latitude: 20,
  zoom: 1.5,
  pitch: 0,
  bearing: 0
};

export default function LivePage() {
  const [events, setEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [hoverInfo, setHoverInfo] = useState(null);
  
  const fetchLiveEvents = () => {
    fetch(LIVE_API_URL)
      .then(res => res.json())
      .then(data => {
        setEvents(data);
        setLastUpdated(new Date());
        setIsLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch live events", err);
        setIsLoading(false);
      });
  };

  useEffect(() => {
    fetchLiveEvents();
    const interval = setInterval(fetchLiveEvents, 30000); // Poll every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const layers = [
    new ScatterplotLayer({
      id: 'live-events-layer',
      data: events,
      pickable: true,
      opacity: 0.8,
      stroked: true,
      filled: true,
      radiusScale: 6,
      radiusMinPixels: 6,
      radiusMaxPixels: 100,
      lineWidthMinPixels: 2,
      getPosition: d => [d.longitude, d.latitude],
      getFillColor: d => {
        const level = d.alert_level.toLowerCase();
        if (level === 'red') return [255, 50, 50, 200];
        if (level === 'orange') return [255, 140, 0, 200];
        return [0, 255, 100, 200]; // Green
      },
      getLineColor: d => [255, 255, 255, 200],
      getRadius: d => d.magnitude * 5000,
      onHover: info => setHoverInfo(info),
      updateTriggers: {
        getFillColor: [events]
      }
    })
  ];

  return (
    <div className="map-page-container" style={{display: 'flex', flexDirection: 'row'}}>
      {/* Sidebar Live Feed */}
      <div className="live-sidebar" style={{
        width: '350px', 
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
            <Activity color="var(--accent-color)" /> Live Warnings
          </h2>
          <p style={{color: '#8892b0', fontSize: '12px', margin: 0}}>
            Monitoring global API streams (USGS, GDACS).<br/>
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>
        
        <div style={{flexGrow: 1, overflowY: 'auto', padding: '15px', display: 'flex', flexDirection: 'column', gap: '15px'}}>
          {isLoading && events.length === 0 ? (
            <p style={{color: 'var(--accent-color)', textAlign: 'center'}}>Establishing uplink...</p>
          ) : events.length === 0 ? (
            <p style={{color: '#8892b0', textAlign: 'center'}}>No active alerts detected.</p>
          ) : (
            events.map((ev, i) => (
              <div key={ev.id} className="live-card" style={{
                background: 'var(--glass-bg)',
                border: `1px solid ${ev.alert_level === 'red' ? '#ff3232' : ev.alert_level === 'orange' ? '#ff8c00' : 'rgba(102, 252, 241, 0.3)'}`,
                borderRadius: '8px',
                padding: '15px',
                cursor: 'pointer',
                transition: 'all 0.2s',
                position: 'relative',
                overflow: 'hidden'
              }}>
                <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '8px'}}>
                  <span style={{
                    fontSize: '10px', 
                    textTransform: 'uppercase', 
                    background: ev.alert_level === 'red' ? 'rgba(255,50,50,0.2)' : ev.alert_level === 'orange' ? 'rgba(255,140,0,0.2)' : 'rgba(0,255,100,0.2)',
                    color: ev.alert_level === 'red' ? '#ff3232' : ev.alert_level === 'orange' ? '#ff8c00' : '#00ff64',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontWeight: 'bold'
                  }}>
                    {ev.alert_level}
                  </span>
                  <span style={{fontSize: '11px', color: '#8892b0'}}>{ev.source}</span>
                </div>
                <h4 style={{margin: '0 0 5px 0', color: '#fff', fontSize: '14px', lineHeight: '1.4'}}>{ev.title}</h4>
                {ev.time && (
                  <div style={{display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: 'var(--accent-color)', marginBottom: '10px'}}>
                    <Clock size={12} /> {new Date(ev.time).toLocaleString()}
                  </div>
                )}
                <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#c5c6c7'}}>
                  <span style={{textTransform: 'capitalize'}}>{ev.type}</span>
                  <span>Mag: {ev.magnitude.toFixed(1)}</span>
                </div>
                {ev.url && (
                  <a href={ev.url} target="_blank" rel="noreferrer" style={{display: 'block', marginTop: '10px', fontSize: '11px', color: 'var(--accent-color)', textDecoration: 'none'}}>View Official Report ↗</a>
                )}
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
        
        {/* Pulsing indicator top right */}
        <div style={{position: 'absolute', top: '20px', right: '20px', display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--glass-bg)', padding: '8px 15px', borderRadius: '20px', border: '1px solid var(--border-color)', color: '#fff', fontSize: '12px'}}>
          <div style={{width: '8px', height: '8px', background: '#ff3232', borderRadius: '50%', boxShadow: '0 0 10px #ff3232'}}></div>
          Live Threat Map
        </div>
      </div>

      {hoverInfo && hoverInfo.object && (
        <div className="tooltip" style={{ left: hoverInfo.x, top: hoverInfo.y }}>
          <h3 style={{
             color: hoverInfo.object.alert_level === 'red' ? '#ff3232' : hoverInfo.object.alert_level === 'orange' ? '#ff8c00' : '#00ff64',
             borderBottom: 'none', margin: '0 0 5px 0'
          }}>{hoverInfo.object.title}</h3>
          <p style={{margin: 0, color: '#8892b0'}}>Magnitude: {hoverInfo.object.magnitude}</p>
          <p style={{margin: '2px 0 0 0', color: '#8892b0'}}>Source: {hoverInfo.object.source}</p>
        </div>
      )}
    </div>
  );
}
