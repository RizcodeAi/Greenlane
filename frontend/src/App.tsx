import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './store/auth';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import FleetList from './pages/FleetList';
import ShipDetail from './pages/ShipDetail';
import VoyageLogs from './pages/VoyageLogs';
import EmissionsAnalytics from './pages/EmissionsAnalytics';
import Reports from './pages/Reports';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import ErrorBoundary from './components/ErrorBoundary';
import ProtectedRoute from './components/ProtectedRoute';

function AppContent() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-slate-950">
      {isAuthenticated && <Navbar />}
      <div className="flex">
        {isAuthenticated && <Sidebar />}
        <main className={isAuthenticated ? "flex-1 p-6" : ""}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/dashboard" element={
              <ProtectedRoute><Dashboard /></ProtectedRoute>
            } />
            <Route path="/fleet" element={
              <ProtectedRoute><FleetList /></ProtectedRoute>
            } />
            <Route path="/fleet/:id" element={
              <ProtectedRoute><ShipDetail /></ProtectedRoute>
            } />
            <Route path="/voyages" element={
              <ProtectedRoute><VoyageLogs /></ProtectedRoute>
            } />
            <Route path="/voyages/:id" element={
              <ProtectedRoute><VoyageLogs /></ProtectedRoute>
            } />
            <Route path="/emissions" element={
              <ProtectedRoute><EmissionsAnalytics /></ProtectedRoute>
            } />
            <Route path="/reports" element={
              <ProtectedRoute><Reports /></ProtectedRoute>
            } />
            <Route path="/" element={<Navigate to={isAuthenticated ? '/dashboard' : '/login'} />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
      <BrowserRouter>
        <ErrorBoundary>
          <AppContent />
        </ErrorBoundary>
      </BrowserRouter>
  );
}

export default App;
