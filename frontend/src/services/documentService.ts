import { authService } from './authService';

export interface Document {
  id: number;
  title: string;
  content: string;
  file_path?: string;
  file_type?: string;
  file_size?: number;
  description?: string;
  tags?: string[];
  owner_id: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateDocumentRequest {
  title: string;
  content: string;
  description?: string;
  tags?: string[];
  is_public?: boolean;
}

export interface UpdateDocumentRequest {
  title?: string;
  content?: string;
  description?: string;
  tags?: string[];
  is_public?: boolean;
}

class DocumentService {
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

  // Get all documents
  async getDocuments(): Promise<Document[]> {
    return this.makeRequest('/documents/');
  }

  // Get document by ID
  async getDocument(id: number): Promise<Document> {
    return this.makeRequest(`/documents/${id}`);
  }

  // Create document
  async createDocument(document: CreateDocumentRequest): Promise<Document> {
    return this.makeRequest('/documents/', {
      method: 'POST',
      body: JSON.stringify(document),
    });
  }

  // Update document
  async updateDocument(id: number, document: UpdateDocumentRequest): Promise<Document> {
    return this.makeRequest(`/documents/${id}`, {
      method: 'PUT',
      body: JSON.stringify(document),
    });
  }

  // Delete document
  async deleteDocument(id: number): Promise<void> {
    await this.makeRequest(`/documents/${id}`, {
      method: 'DELETE',
    });
  }

  // Process document through RAG
  async processDocument(id: number): Promise<{ message: string }> {
    return this.makeRequest(`/rag/documents/${id}/process`, {
      method: 'POST',
    });
  }

  // Delete document from RAG
  async deleteDocumentFromRAG(id: number): Promise<{ message: string }> {
    return this.makeRequest(`/rag/documents/${id}`, {
      method: 'DELETE',
    });
  }
}

export const documentService = new DocumentService();
