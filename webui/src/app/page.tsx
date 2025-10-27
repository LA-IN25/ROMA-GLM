'use client';

import { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Health } from '@/types/api';
import { apiClient } from '@/lib/api';
import Dashboard from '@/components/Dashboard';
import Header from '@/components/Header';
import Sidebar from '@/components/Sidebar';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const healthData = await apiClient.getHealth();
        setHealth(healthData);
      } catch (error) {
        console.error('Failed to fetch health:', error);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Poll every 30 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <Header
          health={health}
          onMenuClick={() => setSidebarOpen(!sidebarOpen)}
        />
        
        <div className="flex">
          <Sidebar
            isOpen={sidebarOpen}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            onClose={() => setSidebarOpen(false)}
          />
          
          <main className="flex-1 p-6">
            <div className="max-w-7xl mx-auto">
              {activeTab === 'dashboard' && <Dashboard />}
              {activeTab === 'executions' && (
                <div>
                  <h1 className="text-2xl font-semibold text-gray-900 mb-6">
                    Executions
                  </h1>
                  <p className="text-gray-600">
                    Execution management interface will be implemented here.
                  </p>
                </div>
              )}
              {activeTab === 'agents' && (
                <div>
                  <h1 className="text-2xl font-semibold text-gray-900 mb-6">
                    Agent Management
                  </h1>
                  <p className="text-gray-600">
                    Agent configuration and management interface will be implemented here.
                  </p>
                </div>
              )}
              {activeTab === 'profiles' && (
                <div>
                  <h1 className="text-2xl font-semibold text-gray-900 mb-6">
                    Configuration Profiles
                  </h1>
                  <p className="text-gray-600">
                    Profile management interface will be implemented here.
                  </p>
                </div>
              )}
              {activeTab === 'metrics' && (
                <div>
                  <h1 className="text-2xl font-semibold text-gray-900 mb-6">
                    Metrics & Analytics
                  </h1>
                  <p className="text-gray-600">
                    Metrics and analytics dashboard will be implemented here.
                  </p>
                </div>
              )}
            </div>
          </main>
        </div>
      </div>
    </QueryClientProvider>
  );
}