import { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell
} from 'recharts';

const API_URL = 'http://127.0.0.1:8000/api/analytics';

const COLORS = {
  earthquake: '#ffcc00',
  tsunami: '#00c8ff',
  volcano: '#c800ff'
};

export default function AnalyticsPage() {
  const [data, setData] = useState({
    by_country: [],
    by_year: [],
    by_type: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(API_URL)
      .then(res => res.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch analytics", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="analytics-loading">Loading deep insights...</div>;
  }

  return (
    <div className="analytics-page">
      <div className="dashboard-header">
        <h2>Global Disaster Insights</h2>
        <p>Comprehensive historical analysis of natural hazards</p>
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
                />
                <Bar dataKey="count" fill="var(--accent-color)" radius={[0, 4, 4, 0]} />
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

        {/* Timeline Line Chart */}
        <div className="chart-card wide-card">
          <h3>Events Over Time (1900 - 2026)</h3>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.by_year} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
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
    </div>
  );
}
