import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { RosProvider } from './context/RosContext';
import Navbar from './components/Navbar';
import ChatPanel from './components/ChatPanel';
import TelemetryInspector from './components/TelemetryInspector';
import ConfigPage from './pages/ConfigPage';
import MapPage from './pages/MapPage';
import NavigationPage from './pages/NavigationPage';
import LocalizationPage from './pages/LocalizationPage';
import RecoveryPage from './pages/RecoveryPage';
import './index.css';

function resolveRosbridgeUrl() {
  const explicitUrl = import.meta.env.VITE_ROSBRIDGE_URL;
  if (explicitUrl) {
    return explicitUrl;
  }

  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/rosbridge`;
  }

  return 'ws://localhost:5173/rosbridge';
}

function DashboardHome() {
  return (
    <main className="main-content">
      <ChatPanel />
      <TelemetryInspector />
    </main>
  );
}

export default function App() {
  return (
    <RosProvider url={resolveRosbridgeUrl()}>
      <BrowserRouter>
        <div className="app-container">
          <Navbar />
          <Routes>
            <Route path="/" element={<DashboardHome />} />
            <Route path="/config" element={<ConfigPage />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/navigation" element={<NavigationPage />} />
            <Route path="/localization" element={<LocalizationPage />} />
            <Route path="/recovery" element={<RecoveryPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </BrowserRouter>
    </RosProvider>
  );
}
