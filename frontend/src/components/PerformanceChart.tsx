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
import { useState } from 'react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface StatsData {
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

interface PerformanceChartProps {
  stats: {
    stats_1h: StatsData;
    stats_24h: StatsData;
    stats_7d: StatsData;
    stats_30d: StatsData;
  };
}

export default function PerformanceChart({ stats }: PerformanceChartProps) {
  const [selectedPeriod, setSelectedPeriod] = useState<'1h' | '24h' | '7d' | '30d'>('1h');
  
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    switch(selectedPeriod) {
      case '1h':
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      case '24h':
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      case '7d':
      case '30d':
        return date.toLocaleDateString();
    }
  };

  const currentStats = stats[`stats_${selectedPeriod}`];
  
  const chartData = {
    labels: currentStats.timestamps.map(formatTimestamp),
    datasets: [
      {
        label: 'Response Time (ms)',
        data: currentStats.response_times,
        borderColor: 'rgb(0, 149, 255)',
        backgroundColor: 'rgba(0, 149, 255, 0.5)',
        tension: 0.3,
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: true,
        text: `Performance History - ${selectedPeriod.toUpperCase()}`
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Response Time (ms)'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Time'
        }
      }
    }
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Performance History</h2>
        <div className="flex gap-2">
          {['1h', '24h', '7d', '30d'].map((period) => (
            <button
              key={period}
              onClick={() => setSelectedPeriod(period as '1h' | '24h' | '7d' | '30d')}
              className={`px-3 py-1 rounded ${
                selectedPeriod === period
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              {period}
            </button>
          ))}
        </div>
      </div>
      <div className="h-[400px]">
        <Line data={chartData} options={options} />
      </div>
      <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-gray-600">Uptime</p>
          <p className="text-xl font-semibold">{currentStats.uptime_percentage}%</p>
        </div>
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-gray-600">Avg Response Time</p>
          <p className="text-xl font-semibold">{currentStats.avg_response_time.toFixed(1)} ms</p>
        </div>
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-gray-600">Total Checks</p>
          <p className="text-xl font-semibold">
            {currentStats.status_counts.up + currentStats.status_counts.down}
          </p>
        </div>
      </div>
    </div>
  );
} 