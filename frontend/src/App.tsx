import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import Header from './components/Header';
import Footer from './components/Footer';
import HomePage from './components/HomePage';
import HealthPage from './components/HealthPage';
import LoginPage from './components/LoginPage';
import DocumentsPage from './components/DocumentsPage';
import RAGPage from './components/RAGPage';

const App = () => {
  return (
    <Router>
      <div className="App">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/health" element={<HealthPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/rag" element={<RAGPage />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
};

export default App;
