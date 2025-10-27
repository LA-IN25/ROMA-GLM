'use client';

import { Health } from '@/types/api';
import { 
  ChartBarIcon, 
  ServerIcon, 
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/react/24/outline';

interface HeaderProps {
  health: Health | null;
  onMenuClick: () => void;
}

export default function Header({ health, onMenuClick }: HeaderProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100';
      case 'unhealthy':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon className="w-4 h-4" />;
      case 'degraded':
      case 'unhealthy':
        return <ExclamationCircleIcon className="w-4 h-4" />;
      default:
        return <ServerIcon className="w-4 h-4" />;
    }
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Left side - Logo and title */}
          <div className="flex items-center">
            <button
              onClick={onMenuClick}
              className="md:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500"
            >
              <Bars3Icon className="h-6 w-6" />
            </button>
            <div className="flex-shrink-0 flex items-center ml-2 md:ml-0">
              <ChartBarIcon className="h-8 w-8 text-primary-600" />
              <h1 className="ml-3 text-xl font-bold text-gray-900">
                ROMA Agent Manager
              </h1>
            </div>
          </div>

          {/* Right side - Health status */}
          <div className="flex items-center space-x-4">
            {health ? (
              <div className="flex items-center space-x-4">
                {/* Status indicator */}
                <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(health.status)}`}>
                  {getStatusIcon(health.status)}
                  <span className="ml-1 capitalize">{health.status}</span>
                </div>

                {/* Version */}
                <div className="hidden sm:flex items-center text-sm text-gray-500">
                  <span className="font-mono">v{health.version}</span>
                </div>

                {/* Active executions */}
                <div className="hidden sm:flex items-center text-sm text-gray-500">
                  <ServerIcon className="w-4 h-4 mr-1" />
                  <span>{health.active_executions} active</span>
                </div>

                {/* Uptime */}
                <div className="hidden sm:flex items-center text-sm text-gray-500">
                  <ClockIcon className="w-4 h-4 mr-1" />
                  <span>{formatUptime(health.uptime_seconds)}</span>
                </div>

                {/* Storage status */}
                <div className="flex items-center">
                  <div className={`w-2 h-2 rounded-full mr-2 ${health.storage_connected ? 'bg-green-400' : 'bg-red-400'}`} />
                  <span className="text-sm text-gray-500 hidden sm:inline">
                    {health.storage_connected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <div className="animate-pulse flex space-x-2">
                  <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
                  <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
                  <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
                </div>
                <span className="text-sm text-gray-500">Checking health...</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}