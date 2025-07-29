# Admin Panel for Stock Roulette

This admin panel provides comprehensive management tools for the Stock Roulette LLM game.

## 🚀 Features Implemented

### ✅ Authentication

- **Admin Login**: Secure password-based authentication
- **Session Management**: Token-based session handling
- **Route Guards**: Protected admin routes

### ✅ Player & Session Management

- **Sessions Overview**: Complete table of all game sessions
- **Advanced Filtering**: Filter by player name, date range, and status
- **Session Details**: View selected stocks, scores, and portfolio values
- **Session Actions**: Reset, archive, and delete sessions

### ✅ Leaderboard Management

- **Interactive Leaderboard**: Sortable by score, profit, session count
- **Performance Stats**: Total players, sessions, highest/average scores
- **Visual Chart**: Score distribution bar chart
- **CSV Export**: Download leaderboard data

### ✅ AI Agent Interaction Logs

- **Chat Transcript View**: Complete conversation history between AI and players
- **AI Suggestions Tracking**: Highlighted AI recommendations
- **Decision Outcomes**: Track how suggestions influenced player decisions
- **Session-specific Logs**: Filter logs by specific game sessions

### ✅ Admin Controls

- **Bulk Actions**: Reset, delete, or archive multiple sessions
- **Data Export**: Download sessions, logs, or complete datasets as CSV
- **Real-time Updates**: Live data refresh capabilities

## 🏗️ Architecture

### Store Management (Pinia)

- **AdminStore**: Centralized state management for all admin functionality
- **Error Handling**: Comprehensive error states and user feedback
- **Loading States**: UI feedback during async operations

### Components Structure

```
src/
├── stores/
│   └── adminStore.ts          # Admin state management
├── views/
│   ├── AdminLoginView.vue     # Authentication
│   ├── AdminDashboardView.vue # Main layout with navigation
│   ├── AdminSessionsView.vue  # Sessions management
│   ├── AdminLeaderboardView.vue # Leaderboard & stats
│   └── AdminChatLogsView.vue  # Chat logs & AI interactions
└── components/
    ├── AdminDemo.vue          # Development testing tools
    └── ErrorBoundary.vue      # Error handling component
```

### Routing

- `/admin/login` - Authentication page
- `/admin/sessions` - Sessions overview (default)
- `/admin/leaderboard` - Leaderboard and statistics
- `/admin/chat-logs` - AI interaction logs

## 🎨 UI/UX Features

### Responsive Design

- Mobile-friendly layouts
- Adaptive grid systems
- Touch-friendly interactions

### Visual Feedback

- Loading spinners and states
- Success/error notifications
- Interactive charts and graphs
- Color-coded status indicators

### Advanced Filtering

- Real-time search and filtering
- Date range selection
- Multi-criteria filtering
- Clear filter options

## 🔧 API Integration

### Expected Backend Endpoints

```
POST /admin/login              # Authentication
GET  /admin/sessions           # Fetch all sessions
GET  /admin/leaderboard        # Fetch leaderboard data
GET  /admin/chat-logs          # Fetch chat logs
GET  /admin/chat-logs/:sessionId # Fetch logs for specific session
POST /admin/sessions/:id/reset # Reset session
POST /admin/sessions/:id/archive # Archive session
DELETE /admin/sessions/:id     # Delete session
GET  /admin/export/:type       # Export data as CSV
```

### Data Models

See `src/stores/adminStore.ts` for complete TypeScript interfaces:

- `Session` - Game session data
- `ChatLog` - AI interaction records
- `LeaderboardEntry` - Player statistics

## 🚀 Getting Started

### Development Setup

1. Install dependencies: `npm install`
2. Start development server: `npm run dev`
3. Access admin panel: `http://localhost:5173/admin`

### Testing with Demo Data

- Use the demo component in the sessions view to create test data
- Demo component provides buttons to populate sessions and chat logs
- Useful for frontend development without backend

### Authentication

- Default admin access via `/admin/login`
- Configure admin password in backend
- Session tokens stored in localStorage

## 🔒 Security Features

- **Route Protection**: Admin routes require authentication
- **Token Management**: Secure session handling
- **Input Validation**: Form validation and sanitization
- **Error Boundaries**: Graceful error handling

## 📊 Analytics & Insights

The admin panel provides insights into:

- Player engagement patterns
- AI suggestion effectiveness
- Game completion rates
- Performance metrics
- Chat interaction analysis

## 🎯 Future Enhancements

Potential additions:

- Real-time dashboard updates via WebSocket
- Advanced analytics with charts
- Bulk operations for session management
- Player performance trends
- AI model performance analytics
- Automated reporting features

## 🤝 Integration Notes

This frontend is designed to work with:

- FastAPI backend (expected at `http://localhost:8000`)
- JWT-based authentication
- RESTful API endpoints
- CSV export functionality

The admin panel is fully functional for frontend development and ready for backend integration.
