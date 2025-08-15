import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Header from './components/Header';
import Footer from './components/Footer';
import HomePage from './components/HomePage';
import HealthPage from './components/HealthPage';
import LoginPage from './components/LoginPage';
import DocumentsPage from './components/DocumentsPage';
import RAGPage from './components/RAGPage';

// Protected Route component
const ProtectedRoute = ({ children }: { children: any }) => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return <div className="loading">Loading...</div>;
  }
  
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// Public Route component (redirects to home if already authenticated)
const PublicRoute = ({ children }: { children: any }) => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return <div className="loading">Loading...</div>;
  }
  
  return isAuthenticated ? <Navigate to="/" replace /> : <>{children}</>;
};

const AppRoutes = () => {
  return (
    <div className="App">
      <Header />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/health" element={<HealthPage />} />
          <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
          <Route path="/documents" element={<ProtectedRoute><DocumentsPage /></ProtectedRoute>} />
          <Route path="/rag" element={<ProtectedRoute><RAGPage /></ProtectedRoute>} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
};

const App = () => {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
};

export default App;
