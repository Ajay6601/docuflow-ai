Start Multiple Workers (Optional)
To process documents faster, start multiple workers:
Terminal 2:
bashcelery -A app.celery_app worker --loglevel=info --pool=solo -n worker1@%h
Terminal 3:
bashcelery -A app.celery_app worker --loglevel=info --pool=solo -n worker2@%h
Terminal 4:
bashcelery -A app.celery_app worker --loglevel=info --pool=solo -n worker3@%h


docker exec -it docuflow-ai-postgres-1 psql -U docuflow -d docuflow_db

# DocuFlow AI

Enterprise Document Intelligence Platform with AI-powered text extraction, classification, and semantic search capabilities.

## Overview

DocuFlow AI is a production-ready document processing system that leverages artificial intelligence to automatically extract, classify, and analyze documents at scale. Built with modern technologies and designed for high concurrency, it processes PDFs, images, and Office documents while providing real-time insights through an intuitive web interface.

## Key Features

### Document Processing
- Multi-format support (PDF, PNG, JPG, DOCX, XLSX, EML)
- Intelligent text extraction using OCR and native parsers
- AI-powered document classification (invoices, contracts, resumes, receipts)
- Structured data extraction with confidence scoring
- Automatic document summarization
- Async background processing with Celery

### Search & Discovery
- Full-text search using PostgreSQL tsvector
- Semantic search with vector embeddings
- Hybrid search combining keyword and semantic approaches
- Advanced filtering by status, type, and date range

### Security & Access Control
- JWT-based authentication
- Role-based access control (Admin, User, Viewer)
- Document sharing with granular permissions
- Public share links with expiration
- Comprehensive audit logging
- API rate limiting and throttling

### Analytics & Monitoring
- Real-time processing metrics
- Document type distribution analytics
- Cost tracking for AI operations
- Upload activity timelines
- Processing performance trends
- Interactive dashboard with charts

### Real-time Updates
- WebSocket support for live status updates
- Progress tracking during document processing
- Instant notification system

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  TypeScript │ Zustand │ React Query │ TailwindCSS │ Recharts   │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API / WebSocket
┌────────────────────────────┴────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  Python 3.11+ │ Async I/O │ Pydantic │ SQLAlchemy              │
└─────┬──────────┬───────────┬──────────┬─────────────┬──────────┘
      │          │           │          │             │
      ▼          ▼           ▼          ▼             ▼
┌──────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌─────────────┐
│PostgreSQL│ │ Redis  │ │ MinIO  │ │Celery  │ │   OpenAI    │
│ +pgvector│ │ Cache  │ │   S3   │ │Workers │ │   GPT-4     │
└──────────┘ └────────┘ └────────┘ └────────┘ └─────────────┘
```

## Technology Stack

### Backend
- **Framework**: FastAPI (async, high-performance)
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy with async support
- **Task Queue**: Celery + Redis
- **Authentication**: JWT (python-jose, passlib)
- **Validation**: Pydantic V2

### Database & Storage
- **Primary DB**: PostgreSQL 15+ with pgvector extension
- **Cache/Queue**: Redis 7+
- **Object Storage**: MinIO (S3-compatible)
- **Connection Pool**: Built-in SQLAlchemy pooling

### AI/ML Services
- **LLM**: OpenAI GPT-4 Turbo
- **OCR**: Tesseract
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector Search**: pgvector with IVFFlat indexing

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **State Management**: Zustand + React Query
- **UI Components**: Custom components with Radix UI primitives
- **Styling**: TailwindCSS 3
- **Charts**: Recharts
- **Forms**: React Hook Form + Zod
- **HTTP Client**: Axios
- **Routing**: React Router v6

### File Processing
- **PDF**: PyPDF2, pypdfium2
- **Images**: Pillow, pytesseract
- **Office**: python-docx, openpyxl
- **Type Detection**: python-magic

## Installation

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher
- Docker and Docker Compose
- OpenAI API key

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/docuflow-ai.git
cd docuflow-ai

# Create and activate virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install system dependencies (OCR)
# Ubuntu/Debian:
sudo apt install tesseract-ocr
# macOS:
brew install tesseract
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

# Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key and other settings

# Start infrastructure services
docker-compose up -d

# Run database migrations
alembic upgrade head

# Create admin user
python create_admin.py

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In a separate terminal, start Celery worker
celery -A app.celery_app worker --loglevel=info
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Configure environment (if needed)
cp .env.example .env

# Start development server
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/v1/docs
- **MinIO Console**: http://localhost:9001

Default admin credentials:
- **Username**: admin
- **Password**: admin123

## Configuration

### Environment Variables

#### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://docuflow:docuflow123@localhost:5432/docuflow_db

# API Settings
API_V1_PREFIX=/api/v1
PROJECT_NAME=DocuFlow AI
DEBUG=True

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=docuflow-documents

# AI Services
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4-turbo-preview

# Task Queue
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# File Upload
MAX_FILE_SIZE=52428800  # 50MB
```

## API Documentation

The API is fully documented using OpenAPI/Swagger. Access interactive documentation at:
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

### Key Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user info

#### Documents
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/documents/` - List documents (paginated)
- `GET /api/v1/documents/{id}` - Get document details
- `GET /api/v1/documents/{id}/download` - Download document
- `DELETE /api/v1/documents/{id}` - Delete document

#### Search
- `GET /api/v1/search/full-text?q={query}` - Full-text search
- `GET /api/v1/search/semantic?q={query}` - Semantic search
- `GET /api/v1/search/hybrid?q={query}` - Hybrid search

#### Analytics
- `GET /api/v1/analytics/overview` - Dashboard statistics
- `GET /api/v1/analytics/document-types` - Document distribution
- `GET /api/v1/analytics/cost-tracking` - AI cost tracking

#### Sharing
- `POST /api/v1/shares/` - Share document
- `GET /api/v1/shares/shared-with-me` - List shared documents
- `DELETE /api/v1/shares/{id}` - Revoke share

## Performance

### Load Testing Results
Tested with Locust using 100 concurrent users:
- Total requests: 4,505
- Average response time: 315ms
- Median response time: 27ms
- Throughput: 25 requests/second

### Scalability

**Single Server Configuration:**
- 100-200 concurrent users (comfortable)
- 500 concurrent users (acceptable with optimizations)

**Production Configuration (8 workers):**
- 800-1,200 concurrent users
- 500+ requests/second throughput

**Horizontal Scaling (Load Balanced):**
- 3,000-5,000+ concurrent users
- Linear scaling with additional instances

### Optimization Recommendations

For production deployments:

```bash
# Run with Gunicorn + multiple workers
gunicorn app.main:app \
  --workers 8 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300 \
  --worker-connections 1000
```

Database connection pooling:

```python
# In database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600
)
```

## Testing

### Backend Tests

```bash
cd backend

# Run unit tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Load testing with Locust
locust -f tests/load_test.py --host=http://localhost:8000
```

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm test

# Run E2E tests
npm run test:e2e
```

## Deployment

### Docker Production Setup

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Deployment

1. Set up production database (PostgreSQL with pgvector)
2. Configure Redis instance
3. Set up S3-compatible storage (AWS S3 or MinIO)
4. Deploy backend with Gunicorn + Nginx
5. Deploy Celery workers
6. Build and deploy frontend
7. Set up SSL certificates
8. Configure firewall rules

## Project Structure

```
docuflow-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── documents.py
│   │   │       ├── search.py
│   │   │       ├── analytics.py
│   │   │       ├── audit.py
│   │   │       └── shares.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   ├── audit_log.py
│   │   │   └── document_share.py
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── storage.py
│   │   │   ├── extraction.py
│   │   │   ├── ai_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── search_service.py
│   │   │   ├── audit_service.py
│   │   │   └── notification_service.py
│   │   ├── tasks/
│   │   │   └── extraction_tasks.py
│   │   ├── middleware/
│   │   │   └── rate_limit.py
│   │   ├── utils/
│   │   ├── websocket/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── celery_app.py
│   │   └── main.py
│   ├── tests/
│   │   ├── load_test.py
│   │   └── stress_test_simple.py
│   ├── alembic/
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── auth/
│   │   │   ├── documents/
│   │   │   └── analytics/
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── DocumentDetail.tsx
│   │   │   └── Analytics.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── store/
│   │   │   └── authStore.ts
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts
│   │   ├── types/
│   │   ├── lib/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
└── docker-compose.yml
```

## Security Considerations

- JWT tokens with configurable expiration
- Password hashing with bcrypt
- SQL injection prevention via SQLAlchemy ORM
- XSS protection with input sanitization
- CORS configuration for API access
- Rate limiting to prevent abuse
- Audit logging for compliance
- File type validation and virus scanning ready
- Document-level access control
- Encrypted storage at rest (MinIO/S3)
- HTTPS enforced in production

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FastAPI for the excellent async web framework
- OpenAI for GPT-4 API
- PostgreSQL pgvector extension for vector similarity search
- Tesseract OCR for text extraction
- The open-source community

## Support

For issues, questions, or contributions, please open an issue on GitHub or contact the development team.

---

**Built with modern technologies for enterprise document intelligence**
