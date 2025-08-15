import React, { useState, useEffect } from 'react';
import { ragService, SearchQuery, RAGResponse, RAGStats } from '../services/ragService';

const RAGPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState<RAGResponse | null>(null);
  const [streamingResponse, setStreamingResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<RAGStats | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const ragStats = await ragService.getStats();
      setStats(ragStats);
    } catch (err) {
      console.error('Failed to load RAG stats:', err);
    }
  };

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    setResponse(null);
    setStreamingResponse('');

    try {
      const searchQuery: SearchQuery = {
        query: query.trim(),
        max_results: 5,
      };

      const result = await ragService.query(searchQuery);
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Query failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStreamQuery = async () => {
    if (!query.trim()) return;

    setIsStreaming(true);
    setError(null);
    setResponse(null);
    setStreamingResponse('');

    try {
      const searchQuery: SearchQuery = {
        query: query.trim(),
        max_results: 5,
      };

      const stream = await ragService.queryStream(searchQuery);
      if (stream) {
        const reader = stream.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          setStreamingResponse(prev => prev + chunk);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Streaming query failed');
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">RAG Pipeline</h1>
      <p className="page-description">
        Intelligent document processing with Retrieval-Augmented Generation for
        AI-powered responses.
      </p>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="card">
        <h3 className="card-title">🔍 RAG Query Interface</h3>
        <form onSubmit={handleQuery} className="rag-query-form">
          <div className="form-group">
            <label htmlFor="query" className="form-label">Ask a question about your documents:</label>
            <textarea
              id="query"
              className="form-input"
              rows={3}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your question here..."
              disabled={isLoading || isStreaming}
            />
          </div>
          <div className="query-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isLoading || isStreaming || !query.trim()}
            >
              {isLoading ? 'Searching...' : 'Search'}
            </button>
            <button
              type="button"
              onClick={handleStreamQuery}
              className="btn btn-secondary"
              disabled={isLoading || isStreaming || !query.trim()}
            >
              {isStreaming ? 'Streaming...' : 'Stream Response'}
            </button>
          </div>
        </form>
      </div>

      {response && (
        <div className="card">
          <h3 className="card-title">📝 Response</h3>
          <div className="response-content">
            <p><strong>Query:</strong> {response.query}</p>
            <p><strong>Answer:</strong></p>
            <div className="answer-text">{response.answer}</div>
            <p className="response-meta">
              <strong>Processing time:</strong> {response.processing_time.toFixed(2)}s
            </p>
          </div>
          
          {response.sources.length > 0 && (
            <div className="sources-section">
              <h4>Sources:</h4>
              <div className="sources-list">
                {response.sources.map((source, index) => (
                  <div key={index} className="source-item">
                    <div className="source-header">
                      <span className="source-rank">#{source.rank}</span>
                      <span className="source-score">Score: {source.similarity_score.toFixed(3)}</span>
                    </div>
                    <div className="source-content">{source.chunk.content}</div>
                    <div className="source-meta">
                      Document ID: {source.chunk.document_id}, Chunk: {source.chunk.chunk_index}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {streamingResponse && (
        <div className="card">
          <h3 className="card-title">📝 Streaming Response</h3>
          <div className="streaming-content">
            <div className="streaming-text">{streamingResponse}</div>
            {isStreaming && <div className="streaming-indicator">...</div>}
          </div>
        </div>
      )}

      {stats && (
        <div className="card">
          <h3 className="card-title">📊 RAG Pipeline Statistics</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-label">Total Chunks:</span>
              <span className="stat-value">{stats.total_chunks}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Vector Store:</span>
              <span className="stat-value">{stats.vector_store_type}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Embedding Service:</span>
              <span className="stat-value">{stats.embedding_service}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Document Processor:</span>
              <span className="stat-value">{stats.document_processor}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Real Services:</span>
              <span className="stat-value">{stats.use_real_services ? 'Yes' : 'No'}</span>
            </div>
          </div>
        </div>
      )}

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
    </div>
  );
};

export default RAGPage;

