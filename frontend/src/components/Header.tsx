import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Header: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <header className="header">
      <div className="header-content">
        <Link to="/" className="logo">
          RBAC-RAG ERP
        </Link>
        <nav className="nav">
          <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>
            Home
          </Link>
          <Link
            to="/health"
            className={`nav-link ${isActive('/health') ? 'active' : ''}`}
          >
            Health
          </Link>
          <Link
            to="/login"
            className={`nav-link ${isActive('/login') ? 'active' : ''}`}
          >
            Login
          </Link>
          <Link
            to="/documents"
            className={`nav-link ${isActive('/documents') ? 'active' : ''}`}
          >
            Documents
          </Link>
          <Link
            to="/rag"
            className={`nav-link ${isActive('/rag') ? 'active' : ''}`}
          >
            RAG
          </Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;

