\# SupportAI – Enterprise AI Customer Support Assistant



An AI-powered customer support application that uses \*\*Retrieval-Augmented Generation (RAG)\*\* to answer customer queries using a structured knowledge base.



SupportAI retrieves relevant information from business documents and generates context-aware responses with source references, helping customers get accurate answers to common support questions.



\## Key Features



\- \*\*RAG-based Question Answering:\*\* Retrieves relevant knowledge before generating responses.

\- \*\*Hybrid Retrieval:\*\* Combines semantic search and BM25-based keyword retrieval.

\- \*\*Reranking:\*\* Uses a cross-encoder model to improve the relevance of retrieved documents.

\- \*\*Multiple Document Formats:\*\* Supports PDF, DOCX, TXT, CSV, and XLSX ingestion.

\- \*\*Source References:\*\* Provides supporting document references with generated answers.

\- \*\*Conversational Context:\*\* Maintains context across follow-up questions.

\- \*\*FastAPI Backend:\*\* Exposes REST API endpoints for customer conversations.

\- \*\*React Frontend:\*\* Provides an interactive customer support chat interface.

\- \*\*PostgreSQL:\*\* Stores application data.

\- \*\*ChromaDB:\*\* Stores document embeddings for vector retrieval.



\## Architecture



```text

&#x20;            Customer

&#x20;               |

&#x20;               v

&#x20;        React Frontend

&#x20;               |

&#x20;               v

&#x20;         FastAPI Backend

&#x20;               |

&#x20;               v

&#x20;       RAG Retrieval Pipeline

&#x20;               |

&#x20;       +-------+--------+

&#x20;       |                |

&#x20;       v                v

&#x20;  Vector Search     BM25 Search

&#x20;  (ChromaDB)        (Keyword)

&#x20;       |                |

&#x20;       +-------+--------+

&#x20;               |

&#x20;               v

&#x20;         Hybrid Results

&#x20;               |

&#x20;               v

&#x20;         Cross-Encoder

&#x20;            Reranking

&#x20;               |

&#x20;               v

&#x20;      Relevant Context

&#x20;               |

&#x20;               v

&#x20;         Groq LLM API

&#x20;               |

&#x20;               v

&#x20;      Generated Response

&#x20;               |

&#x20;               v

&#x20;       Source References

&#x20;               |

&#x20;               v

&#x20;         React Frontend

```



\## Technology Stack



| Component | Technologies |

|---|---|

| Frontend | React, JavaScript, Vite |

| Backend | Python, FastAPI |

| LLM | Groq API |

| Embeddings | BGE Small English |

| Vector Database | ChromaDB |

| Relational Database | PostgreSQL |

| Retrieval | Semantic Search, BM25 |

| Reranking | Cross-Encoder |

| Containerization | Docker, Docker Compose |

| API Documentation | Swagger / OpenAPI |



\## Project Structure



```text

SupportAI/

│

├── backend/

│   ├── app/

│   │   ├── agent/

│   │   ├── api/

│   │   ├── core/

│   │   ├── db/

│   │   ├── eval/

│   │   ├── rag/

│   │   ├── services/

│   │   └── main.py

│   │

│   └── test\_\*.py

│

├── data/

│   ├── documents/

│   └── generate\_docs.py

│

├── frontend/

│   └── src/

│

├── docker-compose.yml

└── README.md

```



\## Getting Started



\### Prerequisites



\- Python

\- Node.js and npm

\- Docker Desktop

\- Groq API key



\### 1. Clone the Repository



```bash

git clone https://github.com/Ishwari232003/SupportAI.git

cd SupportAI

```



\### 2. Configure Environment Variables



Create `backend/.env` and configure:



```env

GROQ\_API\_KEY=your\_groq\_api\_key

DATABASE\_URL=postgresql+psycopg2://support:support@127.0.0.1:5433/supportdb

```



Keep API keys and environment files private. Never commit them to GitHub.



\### 3. Start PostgreSQL



Configure `backend/.env.db` with the local PostgreSQL settings:



```env

POSTGRES\_USER=support

POSTGRES\_PASSWORD=support

POSTGRES\_DB=supportdb

```



Start the database:



```bash

docker compose up -d

```



\### 4. Start the Backend



```bash

cd backend

```



Activate the Python virtual environment and install the backend dependencies.



Start FastAPI:



```bash

uvicorn app.main:app --reload

```



Backend:



`http://127.0.0.1:8000`



API documentation:



`http://127.0.0.1:8000/docs`



\### 5. Start the Frontend



Open another terminal:



```bash

cd frontend

npm install

npm run dev

```



Frontend:



`http://localhost:5173`



\## API Endpoints



| Method | Endpoint | Description |

|---|---|---|

| GET | `/health` | Backend health check |

| POST | `/api/chat` | Submit a customer support query |



Interactive API documentation is available through Swagger UI at `/docs`.



\## Testing



The project includes test scripts covering areas such as:



\- RAG response generation

\- Document loading

\- Retrieval and ranking

\- Source quality

\- Evaluation test cases



The core application flow has also been manually tested, including customer queries, follow-up questions, return policy questions, warranty questions, order tracking, and troubleshooting.



\## Current Scope



The project currently focuses on the customer chat experience and backend RAG pipeline. The Knowledge Base navigation page is present, but its complete document-management interface is still under development.



\## Future Enhancements



\- Complete Knowledge Base management interface.

\- Document upload, update, and deletion through the UI.

\- Improved retrieval evaluation and relevance filtering.

\- Automated testing and CI/CD integration.

\- Deployment to a cloud platform.



\## Author



\*\*Ishwari Sunagar\*\*



\- GitHub: \[Ishwari232003](https://github.com/Ishwari232003)

\- Project: \[SupportAI](https://github.com/Ishwari232003/SupportAI)



\---



\*Built as an end-to-end AI customer support project using Retrieval-Augmented Generation.\*

