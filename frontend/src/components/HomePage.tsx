import React from 'react';
import { Link } from 'react-router-dom';

const HomePage: React.FC = () => {
  return (
    <div className="page">
      <h1 className="page-title">Welcome to RBAC-RAG ERP System</h1>
      <p className="page-description">
        A comprehensive Enterprise Resource Planning system with Role-Based
        Access Control and Retrieval-Augmented Generation capabilities for
        intelligent document processing.
      </p>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '2rem',
          marginTop: '2rem',
        }}
      >
        <div className="card">
          <h3 className="card-title">🔐 Authentication & Authorization</h3>
          <p>
            Secure user authentication with JWT tokens and role-based access
            control powered by Cerbos.
          </p>
          <Link to="/login" className="btn btn-primary">
            Login
          </Link>
        </div>

        <div className="card">
          <h3 className="card-title">📄 Document Management</h3>
          <p>
            Upload, store, and manage documents with fine-grained access control
            and metadata tracking.
          </p>
          <Link to="/documents" className="btn btn-primary">
            Manage Documents
          </Link>
        </div>

        <div className="card">
          <h3 className="card-title">🤖 RAG Pipeline</h3>
          <p>
            Intelligent document processing with vector embeddings, semantic
            search, and AI-powered responses.
          </p>
          <Link to="/rag" className="btn btn-primary">
            Try RAG
          </Link>
        </div>

        <div className="card">
          <h3 className="card-title">📊 System Health</h3>
          <p>
            Monitor system status, database connectivity, and service health in
            real-time.
          </p>
          <Link to="/health" className="btn btn-primary">
            Check Health
          </Link>
        </div>
      </div>

      <div className="card" style={{ marginTop: '2rem' }}>
        <h3 className="card-title">🚀 Key Features</h3>
        <ul style={{ lineHeight: '1.8' }}>
          <li>
            <strong>RBAC Security:</strong> Role-based access control with
            Cerbos policy engine
          </li>
          <li>
            <strong>Document Processing:</strong> Intelligent chunking and
            vector embeddings
          </li>
          <li>
            <strong>Semantic Search:</strong> AI-powered document retrieval and
            search
          </li>
          <li>
            <strong>RESTful API:</strong> FastAPI backend with comprehensive
            endpoints
          </li>
          <li>
            <strong>Modern UI:</strong> React frontend with responsive design
          </li>
          <li>
            <strong>Containerized:</strong> Docker support for easy deployment
          </li>
        </ul>
      </div>
    </div>
  );
};

export default HomePage;

