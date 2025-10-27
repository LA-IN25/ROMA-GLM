'use client';

import { 
  HomeIcon,
  PlayIcon,
  CogIcon,
  DocumentTextIcon,
  ChartBarIcon,
  XMarkIcon,
  UserGroupIcon,
  FolderIcon
} from '@heroicons/react/24/outline';

interface SidebarProps {
  isOpen: boolean;
  activeTab: string;
  onTabChange: (tab: string) => void;
  onClose: () => void;
}

const navigation = [
  { name: 'Dashboard', href: 'dashboard', icon: HomeIcon },
  { name: 'Executions', href: 'executions', icon: PlayIcon },
  { name: 'Agents', href: 'agents', icon: UserGroupIcon },
  { name: 'Profiles', href: 'profiles', icon: FolderIcon },
  { name: 'Metrics', href: 'metrics', icon: ChartBarIcon },
  { name: 'Settings', href: 'settings', icon: CogIcon },
];

export default function Sidebar({ isOpen, activeTab, onTabChange, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 lg:hidden">
          <h2 className="text-lg font-semibold text-gray-900">Navigation</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <nav className="mt-8 px-3">
          <div className="space-y-1">
            {navigation.map((item) => {
              const isActive = activeTab === item.href;
              return (
                <button
                  key={item.name}
                  onClick={() => {
                    onTabChange(item.href);
                    onClose();
                  }}
                  className={`
                    w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-150
                    ${isActive
                      ? 'bg-primary-100 text-primary-700 border-r-2 border-primary-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }
                  `}
                >
                  <item.icon
                    className={`
                      mr-3 h-5 w-5 flex-shrink-0
                      ${isActive ? 'text-primary-500' : 'text-gray-400 group-hover:text-gray-500'}
                    `}
                    aria-hidden="true"
                  />
                  {item.name}
                </button>
              );
            })}
          </div>

          {/* Quick Actions Section */}
          <div className="mt-8">
            <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Quick Actions
            </h3>
            <div className="mt-3 space-y-1">
              <button
                onClick={() => onTabChange('executions')}
                className="w-full flex items-center px-3 py-2 text-sm text-gray-600 rounded-md hover:bg-gray-50 hover:text-gray-900 transition-colors duration-150"
              >
                <PlayIcon className="mr-3 h-5 w-5 text-gray-400" />
                New Execution
              </button>
              <button
                onClick={() => onTabChange('agents')}
                className="w-full flex items-center px-3 py-2 text-sm text-gray-600 rounded-md hover:bg-gray-50 hover:text-gray-900 transition-colors duration-150"
              >
                <UserGroupIcon className="mr-3 h-5 w-5 text-gray-400" />
                Create Agent
              </button>
              <button
                onClick={() => onTabChange('profiles')}
                className="w-full flex items-center px-3 py-2 text-sm text-gray-600 rounded-md hover:bg-gray-50 hover:text-gray-900 transition-colors duration-150"
              >
                <DocumentTextIcon className="mr-3 h-5 w-5 text-gray-400" />
                New Profile
              </button>
            </div>
          </div>

          {/* Help Section */}
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
            <div className="space-y-2">
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center text-sm text-gray-600 hover:text-gray-900"
              >
                <DocumentTextIcon className="mr-2 h-4 w-4" />
                API Documentation
              </a>
              <a
                href="https://github.com/sentient-agi/roma"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center text-sm text-gray-600 hover:text-gray-900"
              >
                <ChartBarIcon className="mr-2 h-4 w-4" />
                GitHub Repository
              </a>
            </div>
          </div>
        </nav>
      </div>
    </>
  );
}