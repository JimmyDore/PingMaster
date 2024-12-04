import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import type { Service, TimeRange } from '../types/service';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

interface AggregatedStats {
  period: string;
  uptime_percentage: number;
  avg_response_time: number;
  status_counts: {
    up: number;
    down: number;
  };
  timestamps: string[];
  response_times: number[];
}

interface ServiceStats {
  service_id: string;
  stats_1h: AggregatedStats;
  stats_24h: AggregatedStats;
  stats_7d: AggregatedStats;
  stats_30d: AggregatedStats;
}

interface ServiceChartProps {
  service: Service;
  timeRange: TimeRange;
  onTimeRangeChange: (range: TimeRange) => void;
}

export default function ServiceChart({ service, timeRange, onTimeRangeChange }: ServiceChartProps) {
  const [stats, setStats] = React.useState<ServiceStats | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      try {
        const response = await fetch(`${import.meta.env.PUBLIC_API_URL}/services/${service.id}/stats/aggregated`);
        if (!response.ok) {
          throw new Error('Failed to fetch stats');
        }
        const data = await response.json();
        setStats(data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 60000); // Refresh every minute
    
    return () => clearInterval(interval);
  }, [service.id, timeRange]);

  if (loading || !stats) {
    return (
      <div className="animate-pulse bg-white p-6 rounded-lg shadow-sm">
        <div className="h-64 bg-gray-200 rounded"></div>
      </div>
    );
  }

  const currentStats = stats[`stats_${timeRange}`];

  const data = {
    labels: currentStats.timestamps,
    datasets: [
      {
        label: 'Response Time',
        data: currentStats.timestamps.map((timestamp, index) => ({
          x: new Date(timestamp),
          y: currentStats.response_times[index]
        })),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.1,
        fill: true
      }
    ]
  };

  const options = {
    responsive: true,
    interaction: {
      intersect: false,
      mode: 'index' as const
    },
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const responseTime = context.raw.y;
            return responseTime ? `Response Time: ${responseTime}ms` : 'No Response';
          }
        }
      }
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          unit: timeRange === '24h' ? 'hour' : timeRange === '7d' ? 'day' : 'week'
        },
        title: {
          display: true,
          text: 'Time'
        }
      },
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Response Time (ms)'
        }
      }
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {service.name} - Performance History
          </h3>
          <p className="text-sm text-gray-500">
            Uptime: {currentStats.uptime_percentage}% | Avg Response: {currentStats.avg_response_time}ms
          </p>
        </div>
        <div className="flex space-x-2">
          {(['1h', '24h', '7d', '30d'] as TimeRange[]).map((range) => (
            <button
              key={range}
              onClick={() => onTimeRangeChange(range)}
              className={`px-3 py-1 rounded text-sm font-medium ${
                timeRange === range
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>
      <Line data={data} options={options} />
    </div>
  );
}