import React, { useState, useEffect } from 'react';
import { documentService, Document, CreateDocumentRequest } from '../services/documentService';

const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState<CreateDocumentRequest>({
    title: '',
    content: '',
    description: '',
    tags: [],
    is_public: false,
  });

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const docs = await documentService.getDocuments();
      setDocuments(docs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await documentService.createDocument(createForm);
      setShowCreateForm(false);
      setCreateForm({ title: '', content: '', description: '', tags: [], is_public: false });
      loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create document');
    }
  };

  const handleDeleteDocument = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await documentService.deleteDocument(id);
        loadDocuments();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete document');
      }
    }
  };

  const handleProcessDocument = async (id: number) => {
    try {
      await documentService.processDocument(id);
      alert('Document processed successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process document');
    }
  };

  if (loading) {
    return <div className="loading">Loading documents...</div>;
  }

  return (
    <div className="page">
      <h1 className="page-title">Document Management</h1>
      <p className="page-description">
        Upload, manage, and organize documents with role-based access control
        and intelligent processing.
      </p>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 className="card-title">📄 Documents ({documents.length})</h3>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="btn btn-primary"
          >
            {showCreateForm ? 'Cancel' : 'Create Document'}
          </button>
        </div>

        {showCreateForm && (
          <form onSubmit={handleCreateDocument} className="create-form">
            <div className="form-group">
              <label htmlFor="title" className="form-label">Title</label>
              <input
                type="text"
                id="title"
                className="form-input"
                value={createForm.title}
                onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="content" className="form-label">Content</label>
              <textarea
                id="content"
                className="form-input"
                rows={5}
                value={createForm.content}
                onChange={(e) => setCreateForm({ ...createForm, content: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="description" className="form-label">Description</label>
              <input
                type="text"
                id="description"
                className="form-input"
                value={createForm.description}
                onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">
                <input
                  type="checkbox"
                  checked={createForm.is_public}
                  onChange={(e) => setCreateForm({ ...createForm, is_public: e.target.checked })}
                />
                Public Document
              </label>
            </div>
            <button type="submit" className="btn btn-primary">Create Document</button>
          </form>
        )}

        {documents.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📄</div>
            <h4>No documents yet</h4>
            <p>Create your first document to get started with the RAG pipeline.</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="btn btn-primary"
            >
              Create First Document
            </button>
          </div>
        ) : (
          <div className="documents-list">
            {documents.map((doc) => (
              <div key={doc.id} className="document-item">
                <div className="document-header">
                  <h4>{doc.title}</h4>
                  <div className="document-actions">
                                         <button
                       onClick={() => handleProcessDocument(doc.id)}
                       className="btn btn-secondary"
                       title="Process for RAG"
                     >
                       🔍 Process for RAG
                     </button>
                    <button
                      onClick={() => handleDeleteDocument(doc.id)}
                      className="btn btn-danger"
                      title="Delete document"
                    >
                      🗑️ Delete
                    </button>
                  </div>
                </div>
                <p className="document-description">{doc.description}</p>
                <div className="document-meta">
                  <span className="document-date">
                    Created: {new Date(doc.created_at).toLocaleDateString()}
                  </span>
                  <span className="document-visibility">
                    {doc.is_public ? '🌐 Public' : '🔒 Private'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentsPage;

