import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import GuardPanel from './pages/GuardPanel';
import DesignPanel from './pages/DesignPanel';
import LabPanel from './pages/LabPanel';
import EduPanel from './pages/EduPanel';
import ArenaPanel from './pages/ArenaPanel';
import Settings from './pages/Settings';

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="guard" element={<GuardPanel />} />
          <Route path="design" element={<DesignPanel />} />
          <Route path="lab" element={<LabPanel />} />
          <Route path="edu" element={<EduPanel />} />
          <Route path="arena" element={<ArenaPanel />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
