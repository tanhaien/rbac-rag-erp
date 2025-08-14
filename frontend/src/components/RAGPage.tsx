import React from 'react';

const RAGPage: React.FC = () => {
  return (
    <div className="page">
      <h1 className="page-title">RAG Pipeline</h1>
      <p className="page-description">
        Intelligent document processing with Retrieval-Augmented Generation for
        AI-powered responses.
      </p>

      <div className="card">
        <h3 className="card-title">🤖 RAG Pipeline Features</h3>
        <ul style={{ lineHeight: '1.8' }}>
          <li>
            <strong>Document Processing:</strong> Intelligent chunking and text
            extraction
          </li>
          <li>
            <strong>Vector Embeddings:</strong> Convert text to high-dimensional
            vectors
          </li>
          <li>
            <strong>Semantic Search:</strong> Find relevant documents using
            similarity
          </li>
          <li>
            <strong>AI Responses:</strong> Generate contextual answers from
            documents
          </li>
          <li>
            <strong>Streaming:</strong> Real-time response generation
          </li>
          <li>
            <strong>Access Control:</strong> Secure document access with RBAC
          </li>
        </ul>
      </div>

      <div className="card">
        <h3 className="card-title">🔧 Pipeline Components</h3>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '1rem',
          }}
        >
          <div>
            <h4>Document Processor</h4>
            <p>
              Chunks documents into manageable pieces while preserving context
            </p>
          </div>
          <div>
            <h4>Embedding Service</h4>
            <p>
              Converts text chunks into vector representations for similarity
              search
            </p>
          </div>
          <div>
            <h4>Vector Store</h4>
            <p>Stores and indexes document embeddings for fast retrieval</p>
          </div>
          <div>
            <h4>Search Service</h4>
            <p>Performs semantic search to find relevant document chunks</p>
          </div>
          <div>
            <h4>Response Generator</h4>
            <p>Generates AI-powered responses based on retrieved context</p>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="card-title">🚧 Coming Soon</h3>
        <p>
          RAG pipeline interface is currently under development. The backend API
          is ready with mock implementations for testing.
        </p>
        <p>
          <strong>Available Backend Endpoints:</strong>
        </p>
        <ul>
          <li>
            <code>POST /rag/query</code> - Query the RAG pipeline
          </li>
          <li>
            <code>POST /rag/query/stream</code> - Streaming RAG query
          </li>
          <li>
            <code>POST /rag/documents/{'{id}'}/process</code> - Process document
          </li>
          <li>
            <code>DELETE /rag/documents/{'{id}'}</code> - Remove document from
            RAG
          </li>
          <li>
            <code>GET /rag/stats</code> - Get RAG pipeline statistics
          </li>
        </ul>
      </div>
    </div>
  );
};

export default RAGPage;

