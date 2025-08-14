import React from 'react';

const DocumentsPage: React.FC = () => {
  return (
    <div className="page">
      <h1 className="page-title">Document Management</h1>
      <p className="page-description">
        Upload, manage, and organize documents with role-based access control
        and intelligent processing.
      </p>

      <div className="card">
        <h3 className="card-title">📄 Document Features</h3>
        <ul style={{ lineHeight: '1.8' }}>
          <li>
            <strong>Secure Upload:</strong> Upload documents with automatic
            metadata extraction
          </li>
          <li>
            <strong>Access Control:</strong> Role-based permissions for document
            access
          </li>
          <li>
            <strong>Search & Filter:</strong> Find documents by title, content,
            or metadata
          </li>
          <li>
            <strong>Version Control:</strong> Track document versions and
            changes
          </li>
          <li>
            <strong>RAG Integration:</strong> Automatic processing for
            AI-powered search
          </li>
        </ul>
      </div>

      <div className="card">
        <h3 className="card-title">🚧 Coming Soon</h3>
        <p>
          Document management functionality is currently under development. The
          backend API is ready and the frontend interface will be implemented
          soon.
        </p>
        <p>
          <strong>Available Backend Endpoints:</strong>
        </p>
        <ul>
          <li>
            <code>GET /documents/</code> - List documents
          </li>
          <li>
            <code>POST /documents/</code> - Create document
          </li>
          <li>
            <code>GET /documents/{'{id}'}</code> - Get document
          </li>
          <li>
            <code>PUT /documents/{'{id}'}</code> - Update document
          </li>
          <li>
            <code>DELETE /documents/{'{id}'}</code> - Delete document
          </li>
        </ul>
      </div>
    </div>
  );
};

export default DocumentsPage;

