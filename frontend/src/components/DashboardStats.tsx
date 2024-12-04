import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const mockData = {
  labels: ['1m ago', '2m ago', '3m ago', '4m ago', '5m ago'],
  datasets: [
    {
      label: 'Response Time (ms)',
      data: [250, 245, 260, 255, 240],
      borderColor: 'rgb(59, 130, 246)',
      tension: 0.1
    }
  ]
};

const options = {
  responsive: true,
  plugins: {
    legend: {
      position: 'top' as const,
    },
    title: {
      display: true,
      text: 'Response Time Trend'
    }
  }
};

interface ApiService {
  id: string;
  name: string;
  url: string;
  refresh_frequency: string;
  stats: {
    status: boolean;
    response_time: number;
    ping_date: string;
  }[] | null;
}

export default function DashboardStats() {
  const [services, setServices] = useState<ApiService[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchServices = async () => {
    try {
      const response = await fetch(`${import.meta.env.PUBLIC_API_URL}/services/`);
      if (!response.ok) {
        throw new Error('Failed to fetch services');
      }
      const data = await response.json();
      setServices(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServices();
  }, []);

  useEffect(() => {
    const handleRefresh = () => {
      console.log('Refreshing dashboard stats...');
      fetchServices();
    };

    document.addEventListener('refreshServices', handleRefresh);

    return () => {
      document.removeEventListener('refreshServices', handleRefresh);
    };
  }, []);

  const stats = {
    totalServices: services.length,
    upPercentage: calculateUpPercentage(services),
    avgResponseTime: calculateAvgResponseTime(services)
  };

  if (loading) {
    return <div className="animate-pulse">Loading stats...</div>;
  }

  if (error) {
    return <div className="text-red-600">Error: {error}</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h3 className="text-sm font-medium text-gray-500">Total Services</h3>
        <p className="mt-2 text-3xl font-semibold text-gray-900">{stats.totalServices}</p>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h3 className="text-sm font-medium text-gray-500">Uptime</h3>
        <p className="mt-2 text-3xl font-semibold text-green-600">{stats.upPercentage}%</p>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h3 className="text-sm font-medium text-gray-500">Avg Response Time</h3>
        <p className="mt-2 text-3xl font-semibold text-gray-900">{stats.avgResponseTime}ms</p>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-sm md:col-span-1">
        <Line options={options} data={mockData} />
      </div>
    </div>
  );
}

function calculateUpPercentage(services: ApiService[]): number {
  if (services.length === 0) return 0;
  
  const servicesWithStats = services.filter(service => service.stats && service.stats.length > 0);
  if (servicesWithStats.length === 0) return 0;
  
  const upServices = servicesWithStats.filter(service => service.stats![0].status);
  return Math.round((upServices.length / servicesWithStats.length) * 100);
}

function calculateAvgResponseTime(services: ApiService[]): number {
  const responseTimes = services
    .filter(service => service.stats && service.stats.length > 0)
    .map(service => service.stats![0].response_time)
    .filter(time => time !== null);

  if (responseTimes.length === 0) return 0;
  
  const sum = responseTimes.reduce((acc, time) => acc + time, 0);
  return Math.round(sum / responseTimes.length);
}