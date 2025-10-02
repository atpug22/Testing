# GitHub Integration Setup Guide

## Overview
LogPose now includes GitHub OAuth authentication and repository data fetching capabilities. Users can connect their GitHub accounts and analyze their team's productivity using real GitHub data.

## Features Added

### Backend
- ✅ GitHub OAuth authentication flow
- ✅ GitHub repository data fetching
- ✅ PR and commit analysis
- ✅ Team member metrics computation
- ✅ Timeline event generation
- ✅ Database integration for GitHub data

### Frontend
- ✅ GitHub login/logout flow
- ✅ Repository picker component
- ✅ Protected routes
- ✅ Authentication context
- ✅ Integration with existing Team Member Page

## Setup Instructions

### 1. GitHub OAuth App Setup

1. Go to [GitHub Developer Settings](https://github.com/settings/applications/new)
2. Create a new OAuth App with these settings:
   - **Application name**: LogPose
   - **Homepage URL**: `http://localhost:3000`
   - **Authorization callback URL**: `http://localhost:8000/api/v1/auth/github/callback`
3. Copy the Client ID and Client Secret

### 2. Environment Variables

Create a `.env` file in the project root:

```bash
# GitHub OAuth Configuration
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here

# Application URLs
APP_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# Database Configuration (already configured)
DATABASE_URL=postgresql://logpose:logpose@localhost:5432/logpose
```

### 3. Database Migration

The GitHub integration fields have been added to the User model. Run the migration:

```bash
alembic upgrade head
```

### 4. Start the Services

```bash
# Terminal 1: Backend
cd /Users/aryaman/Documents/Testing
python main.py

# Terminal 2: Frontend
cd /Users/aryaman/Documents/Testing/frontend
npm run dev
```

## Usage

### 1. Authentication Flow

1. Visit `http://localhost:3000`
2. Click "Connect with GitHub"
3. Authorize the application
4. You'll be redirected back to the dashboard

### 2. Repository Analysis

1. After logging in, you'll see a repository picker
2. Select a repository from your GitHub account
3. Choose analysis period (30-365 days)
4. Click "Fetch Repository Data"
5. The system will:
   - Fetch all PRs and commits
   - Analyze team productivity
   - Generate insights and metrics
   - Store data in the database

### 3. Team Member Pages

- Access team member analytics at `/member/{id}`
- View real GitHub data instead of mock data
- See actual PR metrics, timeline events, and insights

## API Endpoints

### Authentication
- `GET /api/v1/auth/github/login` - Initiate GitHub OAuth
- `GET /api/v1/auth/github/callback` - OAuth callback
- `GET /api/v1/auth/me` - Get current user
- `GET /api/v1/auth/repos` - Get user's repositories
- `POST /api/v1/auth/logout` - Logout

### GitHub Integration
- `POST /api/v1/github/repos/fetch` - Fetch repository data
- `GET /api/v1/github/status` - Get integration status

## Data Flow

1. **User Authentication**: GitHub OAuth → User creation/update → Session management
2. **Repository Selection**: List user repos → User selects repo → Fetch data
3. **Data Processing**: GitHub API → PR/commit analysis → Database storage
4. **Metrics Computation**: Stored data → Team member metrics → Insights generation
5. **Frontend Display**: Real data → Team Member Page → Analytics dashboard

## Security Notes

- GitHub access tokens are stored in the database (encrypt in production)
- Sessions are stored in memory (use Redis in production)
- OAuth state parameter prevents CSRF attacks
- All API endpoints require authentication

## Next Steps

1. Set up GitHub OAuth app
2. Configure environment variables
3. Test the integration
4. Deploy with proper security measures
5. Add more advanced analytics features

## Troubleshooting

### Common Issues

1. **"Not authenticated" errors**: Check if GitHub OAuth is properly configured
2. **Repository fetch fails**: Verify GitHub token has repo access
3. **Database errors**: Ensure migration was run successfully
4. **CORS issues**: Check frontend/backend URL configuration

### Debug Mode

Enable debug logging by setting `LOG_LEVEL=DEBUG` in your environment.
