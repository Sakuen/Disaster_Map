import { NavLink } from 'react-router-dom';
import { Map, BarChart2 } from 'lucide-react';

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <h1>Global Disaster Map</h1>
      </div>
      <div className="navbar-links">
        <NavLink to="/" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          <Map size={18} /> Map View
        </NavLink>
        <NavLink to="/analytics" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          <BarChart2 size={18} /> Analytics Insights
        </NavLink>
      </div>
    </nav>
  );
}
