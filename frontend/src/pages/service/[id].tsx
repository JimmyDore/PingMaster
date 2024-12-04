import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import PerformanceChart from '@/components/PerformanceChart';

export default function ServiceDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [stats, setStats] = useState(null);
  
  useEffect(() => {
    if (!id) return;

    const fetchStats = async () => {
      const response = await fetch(`/api/services/${id}/stats/aggregated`);
      const data = await response.json();
      setStats(data);
    };
    
    fetchStats();
    const interval = setInterval(fetchStats, 60000); // Refresh every minute
    
    return () => clearInterval(interval);
  }, [id]);
  
  if (!stats) return <div>Loading...</div>;
  
  return (
    <div className="container mx-auto p-4">
      <PerformanceChart stats={stats} />
    </div>
  );
}