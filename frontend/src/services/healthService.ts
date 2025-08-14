const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface HealthStatus {
  status: string;
  env: string;
  debug: boolean;
  cerbos: {
    ok: boolean;
    host: string;
    error?: string;
  };
}

class HealthService {
  async getHealth(): Promise<HealthStatus> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching health data:', error);
      throw error;
    }
  }
}

export const healthService = new HealthService();

