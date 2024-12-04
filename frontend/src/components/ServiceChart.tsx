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
import { format } from 'date-fns';
import type { Service, ServiceStats, TimeRange } from '../types/service';

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
        // Simulate API call
        const mockStats: ServiceStats = {
          timestamps: Array.from({ length: 24 }, (_, i) => 
            new Date(Date.now() - i * 3600000).toISOString()
          ).reverse(),
          status: Array.from({ length: 24 }, () => Math.random() > 0.1 ? 1 : 0),
          responseTime: Array.from({ length: 24 }, (_, i) => 
            Math.random() > 0.1 ? Math.floor(Math.random() * 300) + 100 : null
          )
        };
        setStats(mockStats);
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [service.id, timeRange]);

  if (loading || !stats) {
    return (
      <div className="animate-pulse bg-white p-6 rounded-lg shadow-sm">
        <div className="h-64 bg-gray-200 rounded"></div>
      </div>
    );
  }

  const data = {
    labels: stats.timestamps,
    datasets: [
      {
        label: 'Response Time',
        data: stats.timestamps.map((timestamp, index) => ({
          x: new Date(timestamp),
          y: stats.responseTime[index]
        })),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: stats.status.map(status => 
          status === 1 ? 'rgba(34, 197, 94, 0.5)' : 'rgba(239, 68, 68, 0.5)'
        ),
        pointBackgroundColor: stats.status.map(status =>
          status === 1 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'
        ),
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
            const index = context.dataIndex;
            const status = stats.status[index];
            const responseTime = stats.responseTime[index];
            return [
              `Status: ${status === 1 ? 'Up' : 'Down'}`,
              responseTime ? `Response Time: ${responseTime}ms` : 'No Response'
            ];
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
        <h3 className="text-lg font-semibold text-gray-900">
          {service.name} - Performance History
        </h3>
        <div className="flex space-x-2">
          {(['24h', '7d', '30d'] as TimeRange[]).map((range) => (
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