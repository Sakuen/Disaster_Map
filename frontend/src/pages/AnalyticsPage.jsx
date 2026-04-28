import { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell
} from 'recharts';
import { X } from 'lucide-react';

const API_URL = 'http://127.0.0.1:8000/api/analytics';
const DETAILS_API_URL = 'http://127.0.0.1:8000/api/details';

const COLORS = {
  earthquake: '#ffcc00',
  tsunami: '#00c8ff',
  volcano: '#c800ff'
};

export default function AnalyticsPage() {
  const [data, setData] = useState({
    by_country: [],
    by_year: [],
    by_type: [],
    by_fatalities: [],
    by_damage: []
  });
  const [loading, setLoading] = useState(true);
  
  const [activeFilters, setActiveFilters] = useState({ country: null, type: null, year: null });
  const [clickedInfo, setClickedInfo] = useState(null);
  const [detailsData, setDetailsData] = useState(null);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (activeFilters.country) params.append('country', activeFilters.country);
    if (activeFilters.type) params.append('type', activeFilters.type);
    if (activeFilters.year) params.append('year', activeFilters.year);

    fetch(`${API_URL}?${params.toString()}`)
      .then(res => res.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch analytics", err);
        setLoading(false);
      });
  }, [activeFilters]);

  useEffect(() => {
    if (clickedInfo) {
      setIsLoadingDetails(true);
      setDetailsData(null);
      const year = clickedInfo.year;
      const title = clickedInfo.title;
      const type = clickedInfo.type;
      
      // Safety check in case type is missing from the data
      if (!type) {
        setIsLoadingDetails(false);
        return;
      }
      
      fetch(`${DETAILS_API_URL}?year=${year}&title=${encodeURIComponent(title)}&type=${encodeURIComponent(type)}`)
        .then(res => res.json())
        .then(data => {
          setDetailsData(data);
          setIsLoadingDetails(false);
        })
        .catch(err => {
          console.error("Failed to fetch details", err);
          setIsLoadingDetails(false);
        });
    } else {
      setDetailsData(null);
    }
  }, [clickedInfo]);

  if (loading) {
    return <div className="analytics-loading">Loading deep insights...</div>;
  }

  return (
    <div className="analytics-page">
      <div className="dashboard-header">
        <h2>Global Disaster Insights</h2>
        <p>Comprehensive historical analysis of natural hazards</p>
        
        {(activeFilters.country || activeFilters.type || activeFilters.year) && (
          <div className="active-filters" style={{display: 'flex', gap: '10px', marginTop: '15px', alignItems: 'center'}}>
            <span style={{color: '#8892b0', fontSize: '14px'}}>Filters:</span>
            {activeFilters.country && <span className="filter-badge" style={{background: 'rgba(102, 252, 241, 0.2)', padding: '4px 10px', borderRadius: '12px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--accent-color)'}}>{activeFilters.country} <X size={14} style={{cursor: 'pointer'}} onClick={() => setActiveFilters(prev => ({...prev, country: null}))}/></span>}
            {activeFilters.type && <span className="filter-badge" style={{background: 'rgba(102, 252, 241, 0.2)', padding: '4px 10px', borderRadius: '12px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--accent-color)'}}>{activeFilters.type} <X size={14} style={{cursor: 'pointer'}} onClick={() => setActiveFilters(prev => ({...prev, type: null}))}/></span>}
            {activeFilters.year && <span className="filter-badge" style={{background: 'rgba(102, 252, 241, 0.2)', padding: '4px 10px', borderRadius: '12px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--accent-color)'}}>{activeFilters.year} <X size={14} style={{cursor: 'pointer'}} onClick={() => setActiveFilters(prev => ({...prev, year: null}))}/></span>}
            <button onClick={() => setActiveFilters({country: null, type: null, year: null})} style={{background: 'none', border: '1px solid #ff6b6b', color: '#ff6b6b', borderRadius: '4px', padding: '2px 8px', fontSize: '12px', cursor: 'pointer', marginLeft: '10px'}}>Clear All</button>
          </div>
        )}
      </div>
      
      <div className="dashboard-grid">
        {/* Top Countries Bar Chart */}
        <div className="chart-card">
          <h3>Top 15 Most Affected Regions</h3>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.by_country} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis type="number" stroke="#8892b0" />
                <YAxis dataKey="country" type="category" stroke="#8892b0" width={100} tick={{fontSize: 12}} />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: 'rgba(11, 12, 16, 0.95)', borderColor: 'var(--border-color)', borderRadius: '8px' }}
                  itemStyle={{ color: 'var(--accent-color)' }}
                  cursor={{fill: 'rgba(255,255,255,0.05)'}}
                />
                <Bar 
                  dataKey="count" 
                  fill="var(--accent-color)" 
                  radius={[0, 4, 4, 0]} 
                  onClick={(data) => setActiveFilters(prev => ({...prev, country: data.payload ? data.payload.country : null}))}
                  style={{ cursor: 'pointer' }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Disaster Type Distribution */}
        <div className="chart-card">
          <h3>Disaster Distribution</h3>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.by_type}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                  onClick={(data) => setActiveFilters(prev => ({...prev, type: data.name}))}
                  style={{ cursor: 'pointer' }}
                >
                  {data.by_type.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.name.toLowerCase()] || '#8884d8'} />
                  ))}
                </Pie>
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: 'rgba(11, 12, 16, 0.95)', borderColor: 'var(--border-color)', borderRadius: '8px' }}
                />
                <Legend iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Deadliest Disasters */}
        <div className="chart-card">
          <h3>Top 10 Deadliest Events</h3>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.by_fatalities} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis type="number" stroke="#8892b0" />
                <YAxis dataKey="title" type="category" stroke="#8892b0" width={140} tick={{fontSize: 10}} />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: 'rgba(11, 12, 16, 0.95)', borderColor: 'var(--border-color)', borderRadius: '8px' }}
                  itemStyle={{ color: '#ff6b6b' }}
                  cursor={{fill: 'rgba(255,255,255,0.05)'}}
                />
                <Bar 
                  dataKey="fatalities" 
                  fill="#ff6b6b" 
                  radius={[0, 4, 4, 0]} 
                  name="Fatalities" 
                  onClick={(data) => setClickedInfo(data.payload ? data.payload : data)}
                  style={{ cursor: 'pointer' }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Costliest Disasters */}
        <div className="chart-card">
          <h3>Top 10 Costliest Events (Millions USD)</h3>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.by_damage} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis type="number" stroke="#8892b0" />
                <YAxis dataKey="title" type="category" stroke="#8892b0" width={140} tick={{fontSize: 10}} />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: 'rgba(11, 12, 16, 0.95)', borderColor: 'var(--border-color)', borderRadius: '8px' }}
                  itemStyle={{ color: '#4CAF50' }}
                  cursor={{fill: 'rgba(255,255,255,0.05)'}}
                />
                <Bar 
                  dataKey="damage_millions" 
                  fill="#4CAF50" 
                  radius={[0, 4, 4, 0]} 
                  name="Damage (M USD)" 
                  onClick={(data) => setClickedInfo(data.payload ? data.payload : data)}
                  style={{ cursor: 'pointer' }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Timeline Line Chart */}
        <div className="chart-card wide-card">
          <h3>Events Over Time (1900 - 2026)</h3>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart 
                data={data.by_year} 
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                onClick={(data) => { if (data && data.activeLabel) setActiveFilters(prev => ({...prev, year: data.activeLabel})) }}
                style={{ cursor: 'pointer' }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="year" stroke="#8892b0" />
                <YAxis stroke="#8892b0" />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: 'rgba(11, 12, 16, 0.95)', borderColor: 'var(--border-color)', borderRadius: '8px' }}
                />
                <Legend />
                <Line type="monotone" dataKey="earthquake" stroke={COLORS.earthquake} dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="tsunami" stroke={COLORS.tsunami} dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="volcano" stroke={COLORS.volcano} dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {clickedInfo && (
        <div className="overlay-panel details-panel" style={{position: 'absolute', top: '20px', right: '30px', zIndex: 1000}}>
          <div className="details-header" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start'}}>
            <h2 style={{margin: '0 0 10px 0', color: 'var(--accent-color)', fontSize: '20px'}}>{clickedInfo.title}</h2>
            <button onClick={() => setClickedInfo(null)} style={{background: 'none', border: 'none', color: '#fff', cursor: 'pointer'}}><X size={20}/></button>
          </div>
          
          <div className="details-meta" style={{display: 'flex', gap: '15px', marginBottom: '15px', color: '#c5c6c7', fontSize: '14px'}}>
            <span><strong>Year:</strong> {clickedInfo.year}</span>
            {clickedInfo.type && <span><strong>Type:</strong> <span style={{textTransform: 'capitalize'}}>{clickedInfo.type}</span></span>}
            {clickedInfo.fatalities && <span><strong>Fatalities:</strong> {clickedInfo.fatalities}</span>}
            {clickedInfo.damage_millions && <span><strong>Damage:</strong> ${clickedInfo.damage_millions}M</span>}
          </div>

          <div className="details-content">
            {isLoadingDetails ? (
              <p>Fetching media and historical records...</p>
            ) : detailsData && detailsData.found ? (
              <>
                {detailsData.image && (
                  <img src={detailsData.image} alt={detailsData.title} style={{width: '100%', borderRadius: '8px', marginBottom: '10px'}} />
                )}
                <p style={{fontSize: '14px', lineHeight: '1.5', color: '#e2e8f0'}}>{detailsData.extract}</p>
                <a href={detailsData.url} target="_blank" rel="noreferrer" style={{color: 'var(--accent-color)', display: 'inline-block', marginTop: '10px', marginBottom: '10px'}}>Read Full Article on Wikipedia</a>
              </>
            ) : (
              <p style={{color: '#8892b0', marginBottom: '10px'}}>No advanced Wikipedia media coverage found for this exact event.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
