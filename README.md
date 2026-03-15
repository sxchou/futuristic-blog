# 🚀 Futuristic Blog

A modern, futuristic personal blog system built with **Vue 3**, **FastAPI**, and **PostgreSQL**. Features a stunning dark theme UI with particle effects, real-time comments, admin dashboard, and email notifications.

![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=flat-square&logo=vue.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-336791?style=flat-square&logo=postgresql)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat-square&logo=typescript)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.x-06B6D4?style=flat-square&logo=tailwindcss)

## 📖 Table of Contents

- [Project Overview](#-project-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Local Development Setup](#-local-development-setup)
- [Railway Deployment](#-railway-deployment)
- [Environment Variables](#-environment-variables)
- [Important Notes](#-important-notes)
- [Screenshots](#-screenshots)
- [License](#-license)

---

## 🌟 Project Overview

**Futuristic Blog** is a full-stack personal blog system designed for developers and content creators who want a modern, visually appealing platform to share their thoughts and knowledge. The system features a futuristic dark theme with smooth animations, particle backgrounds, and a comprehensive admin dashboard.

### Target Audience
- Personal bloggers and developers
- Content creators who want a modern platform
- Anyone interested in full-stack Vue.js + FastAPI development

### Key Highlights
- 🎨 Futuristic dark theme with particle effects
- 📝 Markdown support with syntax highlighting
- 💬 Real-time comment system with nested replies
- 📊 Admin dashboard with analytics
- 📧 Email notifications (comment replies, pending approvals)
- 🔐 JWT-based authentication
- 📱 Fully responsive design

---

## ✨ Features

### 📝 Content Management

#### Articles
- Create, edit, and delete articles with Markdown support
- Automatic reading time calculation
- Cover image support
- Draft/Published status management
- Featured articles highlighting
- Category and tag organization
- SEO-friendly slugs

#### Categories & Tags
- Hierarchical content organization
- Color-coded categories
- Tag-based filtering
- Article count tracking

#### Resources
- Resource link management
- Category organization
- Click tracking
- Icon support

### 💬 Comment System

#### User Features
- Nested comment replies
- Reply to specific users
- Edit and delete own comments
- Real-time comment updates
- Markdown support in comments

#### Admin Features
- Comment moderation (approve/reject)
- Batch approval operations
- Audit log tracking
- Soft delete with record keeping
- Permanent delete option

### 📧 Email Notifications

- New comment notifications (admin)
- Comment reply notifications (users)
- Pending comment approval notifications
- Comment approval notifications
- Configurable email provider (SMTP/Resend)

### 🎛️ Admin Dashboard

#### Analytics
- Article views and trends
- Comment statistics
- User registration trends
- Access logs visualization
- Popular content tracking

#### User Management
- User list and roles
- Admin promotion/demotion
- Account verification status
- Profile management

#### System Settings
- Site configuration
- Email settings
- Notification preferences
- SEO settings

### 🔐 Authentication & Security

- JWT token-based authentication
- Password hashing with bcrypt
- Token refresh mechanism
- Role-based access control
- CORS protection
- Input validation and sanitization

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| Vue 3 | Frontend framework (Composition API) |
| TypeScript | Type safety |
| Vite | Build tool |
| TailwindCSS | Styling |
| Pinia | State management |
| Vue Router | Routing |
| Axios | HTTP client |
| Marked | Markdown parsing |
| Highlight.js | Code syntax highlighting |
| ECharts | Data visualization |

### Backend
| Technology | Purpose |
|------------|---------|
| FastAPI | REST API framework |
| SQLAlchemy | ORM |
| PostgreSQL | Primary database |
| Pydantic | Data validation |
| Python-JOSE | JWT handling |
| Passlib | Password hashing |
| Uvicorn | ASGI server |

### Deployment
| Platform | Purpose |
|----------|---------|
| Railway | Cloud hosting |
| Docker | Containerization |
| Nginx | Frontend server |

---

## 🚀 Local Development Setup

### Prerequisites

Ensure you have the following installed:

- **Node.js** >= 18.x ([Download](https://nodejs.org/))
- **Python** >= 3.11 ([Download](https://www.python.org/))
- **PostgreSQL** >= 14.x (optional, SQLite works for development)
- **Git** ([Download](https://git-scm.com/))

### Step 1: Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/futuristic-blog.git
cd futuristic-blog
```

### Step 2: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

Edit `backend/.env` with your configuration:

```env
# Database (SQLite for development)
DATABASE_URL=sqlite:///./futuristic_blog.db

# Security
SECRET_KEY=your-super-secret-key-change-in-production

# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com

# Frontend URL
FRONTEND_URL=http://localhost:3000

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# Email (optional for development)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=

# Resend API (alternative email provider)
RESEND_API_KEY=
RESEND_FROM_EMAIL=
EMAIL_PROVIDER=resend
```

### Step 3: Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env
```

Edit `frontend/.env`:

```env
VITE_API_BASE_URL=/api/v1
```

### Step 4: Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Step 5: Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Admin Panel**: http://localhost:3000/admin

### Default Admin Credentials

```
Username: admin
Password: admin123
```

⚠️ **Important**: Change the default admin password immediately after first login!

### Troubleshooting

#### Database Issues
```bash
# Reset database (development only)
rm backend/futuristic_blog.db
# Restart backend to recreate database
```

#### Port Already in Use
```bash
# Find and kill process on port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS:
lsof -i :8000
kill -9 <PID>
```

#### Node Modules Issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

## 🚂 Railway Deployment

Railway provides an easy deployment experience with automatic builds and PostgreSQL integration.

### Step 1: Create Railway Account

1. Go to [Railway.app](https://railway.app/)
2. Sign up with your GitHub account
3. Authorize Railway to access your repositories

### Step 2: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your `futuristic-blog` repository
4. Railway will auto-detect the configuration

### Step 3: Add PostgreSQL Database

1. In your project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will create a database and provide connection details

### Step 4: Configure Backend Service

Create `railway.json` in the root directory:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 5: Set Environment Variables

In Railway dashboard, go to your backend service → **Variables**:

```env
# Database (auto-linked from PostgreSQL addon)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Security - Generate a strong secret key
SECRET_KEY=your-very-long-random-secret-key-at-least-32-characters

# Admin credentials
ADMIN_USERNAME=your-admin-username
ADMIN_PASSWORD=your-secure-password
ADMIN_EMAIL=your-email@example.com

# Frontend URL (your Railway frontend URL)
FRONTEND_URL=https://your-frontend.railway.app

# CORS
CORS_ORIGINS=["https://your-frontend.railway.app"]

# Email Configuration (choose one)

# Option 1: SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
EMAIL_PROVIDER=smtp

# Option 2: Resend (recommended)
RESEND_API_KEY=re_xxxxxxxxxxxx
RESEND_FROM_EMAIL=noreply@yourdomain.com
EMAIL_PROVIDER=resend

# Timezone
TIMEZONE=Asia/Shanghai
```

### Step 6: Configure Frontend Service

The frontend will be served as static files. Create a `nixpacks.toml`:

```toml
[phases.setup]
nixPkgs = ['nodejs_18']

[phases.install]
cmds = ['cd frontend && npm install']

[phases.build]
cmds = ['cd frontend && npm run build']

[start]
cmd = 'cd frontend && npm install -g serve && serve -s dist -l $PORT'
```

### Step 7: Deploy

1. Push changes to your GitHub repository
2. Railway will automatically deploy
3. Check deployment logs for any errors

### Step 8: Configure Custom Domain (Optional)

1. Go to your service → **Settings** → **Domains**
2. Add your custom domain
3. Configure DNS records as instructed

---

## ⚙️ Environment Variables

### Backend Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | Database connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Yes | JWT secret key (32+ chars) | `your-super-secret-key...` |
| `ADMIN_USERNAME` | Yes | Default admin username | `admin` |
| `ADMIN_PASSWORD` | Yes | Default admin password | `SecurePass123!` |
| `ADMIN_EMAIL` | Yes | Admin email address | `admin@example.com` |
| `FRONTEND_URL` | Yes | Frontend URL for CORS | `https://blog.example.com` |
| `CORS_ORIGINS` | Yes | Allowed origins (JSON array) | `["https://example.com"]` |
| `TIMEZONE` | No | Application timezone | `Asia/Shanghai` |
| `SMTP_HOST` | Conditional | SMTP server host | `smtp.gmail.com` |
| `SMTP_PORT` | Conditional | SMTP server port | `587` |
| `SMTP_USER` | Conditional | SMTP username | `user@gmail.com` |
| `SMTP_PASSWORD` | Conditional | SMTP password | `app-password` |
| `SMTP_FROM_EMAIL` | Conditional | Sender email address | `noreply@example.com` |
| `RESEND_API_KEY` | Conditional | Resend API key | `re_xxxxxxxxxx` |
| `RESEND_FROM_EMAIL` | Conditional | Resend sender email | `noreply@yourdomain.com` |
| `EMAIL_PROVIDER` | No | Email provider | `smtp` or `resend` |

### Frontend Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `VITE_API_BASE_URL` | No | API base URL | `/api/v1` |

---

## ⚠️ Important Notes

### Email Functionality Requirements

For full email functionality, you need:

#### Option 1: SMTP (Gmail Example)
1. Enable 2-factor authentication on your Google account
2. Generate an App Password: Google Account → Security → App passwords
3. Use the app password as `SMTP_PASSWORD`

#### Option 2: Resend (Recommended)
1. Sign up at [Resend.com](https://resend.com/)
2. Verify your domain ownership
3. Generate an API key
4. **Note**: Free tier only allows sending to your verified email address
5. For production, verify a domain to send to any recipient

### Domain Ownership for Email

To send emails from a custom domain (e.g., `noreply@yourdomain.com`):

1. **Own the domain** - Purchase from a registrar (Namecheap, GoDaddy, etc.)
2. **Add DNS records** - Configure SPF, DKIM, and DMARC records
3. **Verify with email provider** - Complete domain verification process

### Security Considerations

1. **Secret Key**: Use a strong, random secret key (32+ characters)
2. **Admin Password**: Change default password immediately
3. **CORS**: Only allow your actual frontend domain
4. **Database**: Use PostgreSQL in production (not SQLite)
5. **HTTPS**: Always use HTTPS in production
6. **Environment Variables**: Never commit `.env` files

### Known Limitations

1. **Email Testing**: Resend free tier only sends to verified emails
2. **File Uploads**: Large files may require additional configuration
3. **Rate Limiting**: Not implemented (consider adding for production)
4. **Image Optimization**: Manual optimization recommended

### Performance Tips

1. Enable Redis for caching (configure `REDIS_URL`)
2. Use CDN for static assets
3. Optimize images before upload
4. Enable gzip compression in production

---

## 📸 Screenshots

### Home Page
The futuristic home page features particle backgrounds, smooth animations, and a clean article grid layout.

### Article View
Articles support Markdown with syntax highlighting, reading progress indicator, and nested comments.

### Admin Dashboard
Comprehensive analytics dashboard with charts for views, comments, and user activity.

### Comment System
Nested comments with reply functionality, moderation tools, and audit logging.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📞 Support

If you have any questions or issues, please open an issue on GitHub.

---

Made with ❤️ by [sxchou](https://github.com/sxchou)
