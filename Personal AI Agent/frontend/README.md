# Personal AI Agent - Frontend

Modern Next.js frontend for the Personal AI Agent with hybrid deployment architecture.

## 🎯 Architecture

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Radix UI
- **Deployment**: Vercel (production) / localhost (development)
- **Backend Communication**: REST API to local backend

## 🚀 Quick Start

### Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Visit: http://localhost:3000
```

### Production Build
```bash
# Build for production
npm run build

# Start production server
npm start
```

## 🔧 Configuration

### Environment Variables

Create `.env.local` from the template:
```bash
cp .env.local.example .env.local
```

Key variables:
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)
- `NEXT_PUBLIC_APP_NAME`: Application name
- `NEXT_PUBLIC_DEBUG`: Enable debug mode

### Backend Connection

The frontend automatically connects to the backend API. Ensure your backend is running:
```bash
# In the backend directory
cd ../backend
python main.py
```

## 📁 Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── auth/              # Authentication pages
│   ├── chat/              # Chat interface
│   ├── documents/         # Document management
│   └── settings/          # Settings pages
├── components/            # React components
│   ├── ui/               # Base UI components (shadcn/ui)
│   ├── chat/             # Chat-specific components
│   ├── documents/        # Document-related components
│   ├── layout/           # Layout components
│   └── common/           # Shared components
├── lib/                  # Utility functions
│   ├── api.ts           # API client
│   ├── auth.ts          # Authentication utilities
│   └── utils.ts         # General utilities
├── hooks/               # Custom React hooks
└── styles/              # Global styles
```

## 🎨 Features

### ✅ Implemented
- Modern UI with Tailwind CSS
- TypeScript type safety
- Responsive design
- Dark/light theme support
- API client for backend communication

### 🚧 In Development
- Chat interface
- Document upload and management
- Gmail integration UI
- Authentication system
- Settings and preferences

### 📋 Planned
- Real-time notifications
- Offline support
- Mobile responsive design
- Accessibility improvements

## 🔌 API Integration

The frontend communicates with the local backend via REST API:

```typescript
// Example API usage
import { apiClient } from '@/lib/api'

// Ask a question
const response = await apiClient.askQuestion("What's in my documents?")

// Upload a document
const result = await apiClient.uploadDocument(file, "My Document")

// Check backend status
const isConnected = await apiClient.checkHealth()
```

## 🚀 Deployment

### Vercel Deployment (Recommended)

1. Push to GitHub
2. Connect repository to Vercel
3. Set environment variables:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
4. Deploy automatically

### Manual Deployment

```bash
npm run build
npm start
```

## 🧪 Testing

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Build verification
npm run build
```

## 🤝 Development

### Adding New Components

1. Create component in appropriate directory
2. Follow existing patterns and TypeScript types
3. Use Tailwind CSS for styling
4. Include proper error handling

### API Integration

1. Add new endpoints to `lib/api.ts`
2. Create corresponding TypeScript types
3. Implement error handling
4. Add loading states

## 📚 Documentation

- [Hybrid Deployment Guide](../hybrid_deployment.md)
- [Backend API Documentation](../backend/README.md)
- [Migration Guide](../MIGRATION_GUIDE.md)