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

export default function DashboardStats() {
  const stats = {
    totalServices: 10,
    upPercentage: 90,
    avgResponseTime: 280
  };

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