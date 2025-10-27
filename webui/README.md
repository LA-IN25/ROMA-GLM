# ROMA WebUI

A modern web interface for managing, creating, and testing ROMA (Recursive Open Meta-Agents) hierarchical AI agent systems.

## Features

- 🎯 **Dashboard** - Real-time monitoring of agent executions and system health
- 🚀 **Quick Task Execution** - Start new agent tasks with configurable parameters
- 📊 **Execution Monitoring** - Track task progress, view DAG visualizations, and analyze results
- 🤖 **Agent Management** - Create, configure, and manage different agent profiles
- ⚙️ **Configuration Profiles** - Manage agent configurations for different use cases
- 📈 **Metrics & Analytics** - Detailed performance metrics and usage analytics
- 🔧 **Toolkit Management** - Enable/disable and configure agent toolkits
- 💾 **Checkpoint Management** - View and restore execution checkpoints

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **State Management**: React Query, Zustand
- **UI Components**: Headless UI, Heroicons
- **Visualization**: React Flow, Recharts
- **Code Editor**: Monaco Editor
- **API Client**: Axios with React Query

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- ROMA-DSPy backend running on `http://localhost:8000`

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd roma-webui
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.local.example .env.local
```

Edit `.env.local` and configure:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
src/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── Dashboard.tsx      # Main dashboard
│   ├── Header.tsx         # App header
│   ├── Sidebar.tsx        # Navigation sidebar
│   ├── QuickTaskForm.tsx  # Quick task execution form
│   └── ...                # Other components
├── lib/                   # Utilities and API client
│   └── api.ts            # API client with axios
├── types/                 # TypeScript type definitions
│   └── api.ts            # API response types
└── hooks/                 # Custom React hooks
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Configuration

### Environment Variables

- `NEXT_PUBLIC_API_URL` - ROMA-DSPy backend API URL (default: `http://localhost:8000`)

### Backend Integration

The WebUI connects to a ROMA-DSPy backend instance. Make sure:

1. The backend is running and accessible
2. CORS is properly configured to allow requests from the WebUI
3. API endpoints match the expected schema (see `src/types/api.ts`)

## Key Features

### Dashboard

- Real-time system health monitoring
- Recent execution overview
- Quick task execution
- Performance metrics

### Agent Management

- Create and configure agent profiles
- Manage agent parameters and toolkits
- Test agent configurations

### Execution Monitoring

- Real-time execution status updates
- Task DAG visualization
- Detailed execution traces
- Performance metrics

### Configuration Profiles

- Pre-configured agent setups
- Domain-specific configurations (e.g., crypto_agent, general)
- Custom profile creation

## Development

### Adding New Components

1. Create component in `src/components/`
2. Add TypeScript types in `src/types/`
3. Update API client if needed in `src/lib/api.ts`
4. Add to navigation in `src/components/Sidebar.tsx`

### API Integration

The API client (`src/lib/api.ts`) provides:

- Automatic error handling
- Request/response interceptors
- Type-safe API calls
- Toast notifications for user feedback

### Styling

The project uses Tailwind CSS with custom components defined in `src/app/globals.css`:

- `.btn` - Button styles
- `.card` - Card container styles
- `.badge` - Status badge styles
- `.input` - Form input styles

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Verify ROMA-DSPy backend is running
   - Check `NEXT_PUBLIC_API_URL` environment variable
   - Ensure CORS is configured on the backend

2. **Build Errors**
   - Run `npm run type-check` to check for TypeScript errors
   - Ensure all dependencies are installed

3. **Styling Issues**
   - Clear Next.js cache: `rm -rf .next`
   - Restart development server

## License

This project is licensed under the same license as ROMA-DSPy.