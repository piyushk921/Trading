import { useEffect, useState } from 'react';
import api from '../services/api';
import { Client } from '../types';

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalClients: 0,
    activeClients: 0,
    onboardingClients: 0,
    prospects: 0,
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await api.get<Client[]>('/clients');
      const clients = response.data;

      setStats({
        totalClients: clients.length,
        activeClients: clients.filter((c) => c.status === 'active').length,
        onboardingClients: clients.filter((c) => c.status === 'onboarding').length,
        prospects: clients.filter((c) => c.status === 'prospect').length,
      });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <div className="p-4">Loading...</div>;
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500">Total Clients</h3>
          <p className="mt-2 text-3xl font-bold text-gray-900">{stats.totalClients}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500">Active Clients</h3>
          <p className="mt-2 text-3xl font-bold text-green-600">{stats.activeClients}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500">Onboarding</h3>
          <p className="mt-2 text-3xl font-bold text-yellow-600">{stats.onboardingClients}</p>
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500">Prospects</h3>
          <p className="mt-2 text-3xl font-bold text-blue-600">{stats.prospects}</p>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>
        <p className="text-gray-500">No recent activity to display.</p>
      </div>
    </div>
  );
}
