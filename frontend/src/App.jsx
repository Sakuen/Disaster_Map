import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import MapPage from './pages/MapPage';
import AnalyticsPage from './pages/AnalyticsPage';
import './index.css';

export default function App() {
  return (
    <div className="app-container">
      <Navbar />
      <div className="content-container">
        <Routes>
          <Route path="/" element={<MapPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
        </Routes>
      </div>
    </div>
  );
}
