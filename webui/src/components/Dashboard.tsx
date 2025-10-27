'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { 
  ChartBarIcon, 
  PlayIcon, 
  CheckCircleIcon, 
  ExclamationCircleIcon,
  ClockIcon,
  CpuChipIcon,
  DocumentTextIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon
} from '@heroicons/react/24/outline';
import { apiClient } from '@/lib/api';
import { Execution, Health } from '@/types/api';
import QuickTaskForm from './QuickTaskForm';

interface DashboardStats {
  totalExecutions: number;
  activeExecutions: number;
  completedExecutions: number;
  failedExecutions: number;
  averageExecutionTime: number;
  totalTokensUsed: number;
  totalCost: number;
}

export default function Dashboard() {
  const [health, setHealth] = useState<Health | null>(null);
  const [showQuickTask, setShowQuickTask] = useState(false);

  // Fetch health data
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
  }, []);

  // Fetch recent executions
  const { data: executionsData, isLoading: executionsLoading } = useQuery({
    queryKey: ['recent-executions'],
    queryFn: () => apiClient.getExecutions(0, 10),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Calculate dashboard stats
  const stats: DashboardStats = executionsData?.executions.reduce(
    (acc, execution) => {
      acc.totalExecutions++;
      
      if (execution.status === 'running') {
        acc.activeExecutions++;
      } else if (execution.status === 'completed') {
        acc.completedExecutions++;
      } else if (execution.status === 'failed') {
        acc.failedExecutions++;
      }

      return acc;
    },
    {
      totalExecutions: 0,
      activeExecutions: 0,
      completedExecutions: 0,
      failedExecutions: 0,
      averageExecutionTime: 0,
      totalTokensUsed: 0,
      totalCost: 0,
    }
  ) || {
    totalExecutions: 0,
    activeExecutions: 0,
    completedExecutions: 0,
    failedExecutions: 0,
    averageExecutionTime: 0,
    totalTokensUsed: 0,
    totalCost: 0,
  };

  const statCards = [
    {
      name: 'Total Executions',
      value: stats.totalExecutions,
      icon: DocumentTextIcon,
      color: 'bg-blue-500',
      trend: null,
    },
    {
      name: 'Active Executions',
      value: stats.activeExecutions,
      icon: PlayIcon,
      color: 'bg-green-500',
      trend: stats.activeExecutions > 0 ? 'up' : null,
    },
    {
      name: 'Completed',
      value: stats.completedExecutions,
      icon: CheckCircleIcon,
      color: 'bg-emerald-500',
      trend: 'up',
    },
    {
      name: 'Failed',
      value: stats.failedExecutions,
      icon: ExclamationCircleIcon,
      color: 'bg-red-500',
      trend: stats.failedExecutions > 0 ? 'down' : null,
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-4 h-4" />;
      case 'running':
        return <PlayIcon className="w-4 h-4" />;
      case 'failed':
        return <ExclamationCircleIcon className="w-4 h-4" />;
      default:
        return <ClockIcon className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Monitor and manage your ROMA agent executions</p>
        </div>
        <button
          onClick={() => setShowQuickTask(!showQuickTask)}
          className="btn btn-primary"
        >
          <PlayIcon className="w-4 h-4 mr-2" />
          Quick Task
        </button>
      </div>

      {/* Quick Task Form */}
      {showQuickTask && (
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">Start New Task</h3>
          </div>
          <div className="card-body">
            <QuickTaskForm onSubmit={() => setShowQuickTask(false)} />
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => (
          <div key={stat.name} className="card">
            <div className="card-body">
              <div className="flex items-center">
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <stat.icon className="w-6 h-6 text-white" />
                </div>
                <div className="ml-4 flex-1">
                  <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                </div>
                {stat.trend && (
                  <div className="ml-2">
                    {stat.trend === 'up' ? (
                      <ArrowTrendingUpIcon className="w-5 h-5 text-green-500" />
                    ) : (
                      <ArrowTrendingDownIcon className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* System Health */}
      {health && (
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">System Health</h3>
          </div>
          <div className="card-body">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="flex items-center">
                <CpuChipIcon className="w-5 h-5 text-gray-400 mr-2" />
                <div>
                  <p className="text-sm text-gray-600">Version</p>
                  <p className="font-medium">{health.version}</p>
                </div>
              </div>
              <div className="flex items-center">
                <ClockIcon className="w-5 h-5 text-gray-400 mr-2" />
                <div>
                  <p className="text-sm text-gray-600">Uptime</p>
                  <p className="font-medium">{Math.floor(health.uptime_seconds / 3600)}h {Math.floor((health.uptime_seconds % 3600) / 60)}m</p>
                </div>
              </div>
              <div className="flex items-center">
                <ChartBarIcon className="w-5 h-5 text-gray-400 mr-2" />
                <div>
                  <p className="text-sm text-gray-600">Storage</p>
                  <p className="font-medium">{health.storage_connected ? 'Connected' : 'Disconnected'}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Executions */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Recent Executions</h3>
        </div>
        <div className="card-body">
          {executionsLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          ) : executionsData?.executions.length === 0 ? (
            <div className="text-center py-8">
              <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No executions yet</p>
              <p className="text-sm text-gray-500 mt-2">Start your first task to see it here</p>
            </div>
          ) : (
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Goal
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Progress
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {executionsData?.executions.map((execution) => (
                    <tr key={execution.execution_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900 truncate max-w-xs">
                          {execution.initial_goal}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(execution.status)}`}>
                          {getStatusIcon(execution.status)}
                          <span className="ml-1 capitalize">{execution.status}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-1 mr-2">
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-primary-600 h-2 rounded-full"
                                style={{
                                  width: `${execution.total_tasks > 0 ? (execution.completed_tasks / execution.total_tasks) * 100 : 0}%`
                                }}
                              />
                            </div>
                          </div>
                          <span className="text-sm text-gray-600">
                            {execution.completed_tasks}/{execution.total_tasks}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {format(new Date(execution.created_at), 'MMM d, h:mm a')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}