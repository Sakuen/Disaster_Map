import { useState, useEffect, useMemo } from 'react';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
import { Map } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Play, Pause } from 'lucide-react';
import './index.css';

const API_URL = 'http://127.0.0.1:8000/api/disasters';
const MIN_YEAR = 1900;
const MAX_YEAR = 2026;

const INITIAL_VIEW_STATE = {
  longitude: 0,
  latitude: 20,
  zoom: 1.5,
  pitch: 0,
  bearing: 0
};

export default function App() {
  const [data, setData] = useState([]);
  const [currentYear, setCurrentYear] = useState(2000);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hoverInfo, setHoverInfo] = useState(null);

  useEffect(() => {
    // Fetch all data upfront for smooth playback
    fetch(`${API_URL}?start_year=${MIN_YEAR}&end_year=${MAX_YEAR}&min_mag=6.0`)
      .then(res => res.json())
      .then(d => {
        if (d.features) {
          setData(d.features);
        }
      })
      .catch(err => console.error("Failed to fetch disaster data. Is the backend running?", err));
  }, []);

  useEffect(() => {
    let interval;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentYear(y => (y >= MAX_YEAR ? MIN_YEAR : y + 1));
      }, 300); // 300ms per year
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  // Show a trailing 5 year window so dots slowly fade
  const activeData = useMemo(() => {
    return data.filter(f => f.properties.year <= currentYear && f.properties.year >= currentYear - 5);
  }, [data, currentYear]);

  const layers = [
    new ScatterplotLayer({
      id: 'disasters-layer',
      data: activeData,
      pickable: true,
      opacity: 0.8,
      stroked: true,
      filled: true,
      radiusScale: 6,
      radiusMinPixels: 4,
      radiusMaxPixels: 100,
      lineWidthMinPixels: 1,
      getPosition: d => d.geometry.coordinates,
      // Color scaling depending on magnitude (Mag 6 -> Mag 9.5)
      getFillColor: d => {
        const mag = d.properties.magnitude;
        // Age of the event to fade opacity
        const age = currentYear - d.properties.year;
        const alpha = Math.max(0, 255 - (age * 40)); 
        
        if (mag > 8) return [255, 50, 50, alpha];
        if (mag > 7) return [255, 140, 0, alpha];
        return [255, 204, 0, alpha];
      },
      getLineColor: d => {
        const age = currentYear - d.properties.year;
        const alpha = Math.max(0, 255 - (age * 40));
        return [0, 0, 0, alpha > 0 ? 150 : 0];
      },
      getRadius: d => Math.pow((d.properties.magnitude - 5), 2) * 5000,
      onHover: info => setHoverInfo(info),
      updateTriggers: {
        getFillColor: [currentYear],
        getLineColor: [currentYear]
      }
    })
  ];

  return (
    <div className="app-container">
      <div className="map-container">
        <DeckGL
          initialViewState={INITIAL_VIEW_STATE}
          controller={true}
          layers={layers}
          onViewStateChange={() => {
            // Close tooltip on map interaction
            if (hoverInfo) setHoverInfo(null);
          }}
        >
          {/* Using Carto Voyager dark basemap for high contrast free tiles */}
          <Map 
            mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
          />
        </DeckGL>
      </div>

      <div className="overlay-panel title-panel">
        <h1>Global Disaster Map</h1>
        <p className="subtitle">Visualizing Earthquakes (Mag &gt; 6.0)</p>
        <p className="subtitle">Data from NOAA USGS Database</p>
      </div>

      <div className="overlay-panel timeline-container">
        <div className="controls-header">
          <button 
            className="play-button"
            onClick={() => setIsPlaying(!isPlaying)}
          >
            {isPlaying ? <><Pause size={18} /> Pause</> : <><Play size={18} /> Play Timeline</>}
          </button>
          <div className="year-display">{currentYear}</div>
        </div>
        <div className="slider-wrapper">
          <input 
            type="range" 
            min={MIN_YEAR} 
            max={MAX_YEAR} 
            value={currentYear} 
            onChange={(e) => {
              setCurrentYear(parseInt(e.target.value));
              setIsPlaying(false);
            }} 
          />
        </div>
      </div>

      {hoverInfo && hoverInfo.object && (
        <div className="tooltip" style={{ left: hoverInfo.x, top: hoverInfo.y }}>
          <h3>{hoverInfo.object.properties.title}</h3>
          <p><strong>Year:</strong> {hoverInfo.object.properties.year}</p>
          <p><strong>Magnitude:</strong> {hoverInfo.object.properties.magnitude.toFixed(1)}</p>
          <p><strong>Depth:</strong> {hoverInfo.object.properties.depth} km</p>
          {hoverInfo.object.properties.url && (
            <p><a href={hoverInfo.object.properties.url} target="_blank" rel="noreferrer" style={{color: 'var(--accent-color)'}}>View Event Details</a></p>
          )}
        </div>
      )}
    </div>
  );
}
