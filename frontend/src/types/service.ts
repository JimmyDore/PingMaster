export interface Service {
  id: string;
  name: string;
  type: 'API' | 'Landing Page' | 'Server';
  url: string;
  status: 'up' | 'down';
  responseTime: number;
  lastCheck: Date;
}

export interface ServiceStats {
  timestamps: string[];
  status: number[];
  responseTime: (number | null)[];
}

export type TimeRange = '1h' | '24h' | '7d' | '30d';

interface ApiService {
  // ... propriétés existantes ...
  has_notification: boolean;
  notification?: {
    webhook_url: string;
    alert_frequency: 'DAILY' | 'ALWAYS';
  };
}