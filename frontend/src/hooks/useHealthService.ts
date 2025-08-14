import { useState, useCallback } from 'react';
import { healthService } from '../services/healthService';

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

export const useHealthService = () => {
  const [healthData, setHealthData] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await healthService.getHealth();
      setHealthData(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to fetch health data'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    healthData,
    loading,
    error,
    fetchHealth,
  };
};

