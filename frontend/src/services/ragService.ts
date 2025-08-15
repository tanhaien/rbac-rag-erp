import { authService } from './authService';

export interface SearchQuery {
  query: string;
  max_results?: number;
  filters?: Record<string, any>;
}

export interface SearchResult {
  chunk: {
    id: string;
    document_id: number;
    content: string;
    chunk_index: number;
    metadata?: Record<string, any>;
  };
  similarity_score: number;
  rank: number;
}

export interface RAGResponse {
  query: string;
  answer: string;
  sources: SearchResult[];
  processing_time: number;
}

export interface RAGStats {
  total_chunks: number;
  vector_store_type: string;
  embedding_service: string;
  document_processor: string;
  use_real_services: boolean;
}

class RAGService {
  private baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  private async makeRequest(endpoint: string, options: RequestInit = {}) {
    const authHeader = authService.getAuthHeader();
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...authHeader,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Request failed');
    }

    return response.json();
  }

  // Query RAG pipeline
  async query(searchQuery: SearchQuery): Promise<RAGResponse> {
    return this.makeRequest('/rag/query', {
      method: 'POST',
      body: JSON.stringify(searchQuery),
    });
  }

  // Stream query response
  async queryStream(searchQuery: SearchQuery): Promise<ReadableStream<Uint8Array> | null> {
    const authHeader = authService.getAuthHeader();
    const response = await fetch(`${this.baseUrl}/rag/query/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeader,
      },
      body: JSON.stringify(searchQuery),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Request failed');
    }

    return response.body;
  }

  // Get RAG statistics
  async getStats(): Promise<RAGStats> {
    return this.makeRequest('/rag/stats');
  }

  // Process document through RAG
  async processDocument(documentId: number): Promise<{ message: string }> {
    return this.makeRequest(`/rag/documents/${documentId}/process`, {
      method: 'POST',
    });
  }

  // Delete document from RAG
  async deleteDocumentFromRAG(documentId: number): Promise<{ message: string }> {
    return this.makeRequest(`/rag/documents/${documentId}`, {
      method: 'DELETE',
    });
  }
}

export const ragService = new RAGService();
