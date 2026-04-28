import { useState } from 'react';
import { Filter, ChevronLeft, ChevronRight } from 'lucide-react';

export default function Sidebar({ filters, setFilters }) {
  const [isOpen, setIsOpen] = useState(true);

  const toggleFilter = (type) => {
    setFilters(prev => ({ ...prev, [type]: !prev[type] }));
  };

  const updateRange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: parseFloat(value) }));
  };

  return (
    <>
      {/* Toggle Button */}
      <button 
        className="sidebar-toggle" 
        onClick={() => setIsOpen(!isOpen)}
        style={{ left: isOpen ? '320px' : '20px' }}
      >
        {isOpen ? <ChevronLeft size={20} /> : <Filter size={20} />}
      </button>

      {/* Sidebar Panel */}
      <div className={`sidebar-panel ${isOpen ? 'open' : 'closed'}`}>
        <h2>Advanced Filters</h2>
        
        <div className="filter-section">
          <h3>Disaster Types</h3>
          <label className="checkbox-label">
            <input type="checkbox" checked={filters.earthquake} onChange={() => toggleFilter('earthquake')} />
            <span style={{color: '#ffcc00'}}>●</span> Earthquakes
          </label>
          <label className="checkbox-label">
            <input type="checkbox" checked={filters.tsunami} onChange={() => toggleFilter('tsunami')} />
            <span style={{color: '#00c8ff'}}>●</span> Tsunamis
          </label>
          <label className="checkbox-label">
            <input type="checkbox" checked={filters.volcano} onChange={() => toggleFilter('volcano')} />
            <span style={{color: '#c800ff'}}>●</span> Volcanoes
          </label>
        </div>

        <div className="filter-section">
          <h3>Magnitude Range</h3>
          <div className="range-group">
            <label>Min Mag: {filters.min_mag.toFixed(1)}</label>
            <input 
              type="range" 
              min="0" max="10" step="0.1" 
              value={filters.min_mag} 
              onChange={(e) => updateRange('min_mag', e.target.value)} 
            />
          </div>
          <div className="range-group">
            <label>Max Mag: {filters.max_mag.toFixed(1)}</label>
            <input 
              type="range" 
              min="0" max="10" step="0.1" 
              value={filters.max_mag} 
              onChange={(e) => updateRange('max_mag', e.target.value)} 
            />
          </div>
        </div>

        <div className="filter-section">
          <h3>Depth (km) - Earthquakes</h3>
          <div className="range-group">
            <label>Min Depth: {filters.min_depth}</label>
            <input 
              type="range" 
              min="-100" max="1000" step="10" 
              value={filters.min_depth} 
              onChange={(e) => updateRange('min_depth', e.target.value)} 
            />
          </div>
          <div className="range-group">
            <label>Max Depth: {filters.max_depth}</label>
            <input 
              type="range" 
              min="-100" max="1000" step="10" 
              value={filters.max_depth} 
              onChange={(e) => updateRange('max_depth', e.target.value)} 
            />
          </div>
        </div>
      </div>
    </>
  );
}
