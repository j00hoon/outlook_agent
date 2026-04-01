# Project Status

## 1. What Is This Project?

This project is a web-based Outlook email assistant designed to collect emails from Outlook, store them locally, and prepare them for future AI-powered features such as summarization, search, and question answering.

In simple terms:

- It reads emails from Outlook.
- It stores useful emails in a local system.
- It prepares the data so AI can help users understand important messages later.

At the current stage, the project already includes email sync, local storage, folder selection, a basic chat interface, and the foundation for AI expansion.

이 프로젝트는 Outlook 이메일을 웹에서 더 쉽게 다루기 위한 보조 도구입니다. Outlook에서 메일을 가져와 로컬에 저장하고, 앞으로 AI가 요약하거나 검색하거나 질문에 답할 수 있도록 준비하는 구조를 가진 프로젝트입니다.

쉽게 말하면:

- Outlook 메일을 읽어옵니다.
- 필요한 메일을 내부 저장소에 보관합니다.
- 나중에 AI가 중요한 내용을 이해하고 도와줄 수 있게 데이터를 준비합니다.

현재 단계에서는 메일 동기화, 로컬 저장, 폴더 선택, 기본 채팅 UI, AI 확장 기반까지 갖춰져 있습니다.

---

## 2. Simple Explanation for Non-Technical Readers

This project helps people manage Outlook emails without manually opening many folders and reading every message one by one.

For example:

- A user selects `Inbox` and one or more subfolders.
- The user clicks `Sync New Emails`.
- The system reads new emails from Outlook.
- Those emails are saved into an internal database.
- Later, the system can be extended so the user can ask things like, "Please summarize client emails from last week."

So this is not just an email viewer. It is a system for collecting, organizing, and preparing email data so AI can support future work.

이 프로젝트는 사용자가 Outlook 메일함을 일일이 열어보고 하나씩 읽지 않아도 되도록 돕는 시스템입니다.

예를 들어:

- 사용자가 `Inbox`와 그 아래 하위 폴더들을 선택합니다.
- `Sync New Emails` 버튼을 누릅니다.
- 시스템이 Outlook에서 새 메일을 읽어옵니다.
- 읽어온 메일을 내부 데이터베이스에 저장합니다.
- 앞으로는 "지난주 고객 메일만 요약해줘" 같은 요청도 가능하도록 확장할 수 있습니다.

즉, 단순 메일 뷰어가 아니라 메일을 모으고 정리해서 AI가 활용할 수 있도록 준비하는 시스템입니다.

---

## 3. Project Structure

### Root Structure

```text
99. outlook_summarization/
├─ backend/                  # Backend server and local data
├─ frontend/                 # Web UI
├─ logs/                     # Runtime logs
├─ venv/                     # Python virtual environment
├─ requirements.txt          # Python dependency list
├─ start.ps1                 # Script to start Redis, backend, and frontend
├─ stop.ps1                  # Script to stop running services
└─ project_status.md         # This document
```

루트 구조는 위와 같습니다.

- `backend/`: 서버 코드와 데이터 저장소
- `frontend/`: 사용자가 보는 웹 화면
- `logs/`: 실행 로그
- `venv/`: Python 가상환경
- `start.ps1`: Redis, 백엔드, 프론트를 한 번에 실행하는 스크립트
- `stop.ps1`: 실행 중인 프로세스를 정리하는 스크립트

### Backend Structure

```text
backend/
├─ app/
│  ├─ main.py               # FastAPI entry point and API registration
│  ├─ outlook_reader.py     # Reads Outlook folders and emails
│  ├─ database.py           # SQLite connection and table definition
│  ├─ vector_store.py       # ChromaDB vector storage and search
│  ├─ summarizer.py         # LLM-based email summarization logic
│  ├─ chat_agent.py         # LLM-based email Q&A logic
│  ├─ routes/
│  │  ├─ emails.py          # Folder list and email retrieval API
│  │  └─ chat.py            # Chat route
│  ├─ models.py             # Additional model definitions
│  ├─ schemas.py            # Schema definitions
│  └─ crud.py               # Database helper logic
├─ emails.db                # SQLite database file
└─ chroma_db/               # Local ChromaDB storage
```

백엔드는 Outlook에서 메일을 읽고, DB에 저장하고, API를 통해 프론트와 연결하는 역할을 합니다.

- `main.py`: FastAPI 서버 시작점
- `outlook_reader.py`: Outlook 연동 핵심 로직
- `database.py`: SQLite 연결과 테이블 생성
- `vector_store.py`: 의미 검색용 벡터 저장소
- `summarizer.py`: 이메일 요약용 AI 호출
- `chat_agent.py`: 이메일 기반 질의응답용 AI 호출

### Frontend Structure

```text
frontend/
├─ app/
│  ├─ layout.tsx            # Next.js layout
│  ├─ globals.css           # Global styles
│  └─ page.tsx              # Main page
├─ src/
│  ├─ components/
│  │  └─ Chatbot.tsx        # Chat UI component
│  └─ services/
│     ├─ emailService.ts    # Email API calls
│     └─ chatService.ts     # Chat API calls
├─ next.config.ts           # API rewrite configuration
├─ package.json             # Frontend dependencies
└─ tsconfig.json            # TypeScript configuration
```

프론트엔드는 사용자가 직접 보는 화면입니다.

- `page.tsx`: 메인 UI
- `emailService.ts`: 이메일 관련 API 호출
- `chatService.ts`: 채팅 관련 API 호출
- `next.config.ts`: 프론트에서 백엔드로 API 요청을 넘기는 설정

---

## 4. How the Project Works

### Overall Flow

1. The user opens the web app.
2. The UI loads the list of folders under Outlook Inbox.
3. The user can select `Inbox` itself and multiple Inbox subfolders.
4. The user clicks `Sync New Emails`.
5. The backend connects to Outlook and reads emails from the selected folders.
6. Already saved emails are skipped, and new emails are stored in SQLite.
7. The last sync time for each folder is stored in Redis.
8. The stored data can later be used for search, summarization, and AI-based answers.

전체 동작 흐름은 다음과 같습니다.

1. 사용자가 웹 앱을 엽니다.
2. 화면이 Outlook Inbox 아래 폴더 목록을 불러옵니다.
3. 사용자는 `Inbox` 자체와 여러 하위 폴더를 동시에 선택할 수 있습니다.
4. `Sync New Emails` 버튼을 누릅니다.
5. 백엔드가 Outlook에 연결해 선택된 폴더 메일을 읽습니다.
6. 이미 저장된 메일은 건너뛰고 새 메일만 SQLite에 저장합니다.
7. 폴더별 마지막 동기화 시간은 Redis에 저장됩니다.
8. 저장된 데이터는 앞으로 검색, 요약, AI 답변 기능에 활용될 수 있습니다.

### What the User Sees

- A sync button in the web UI
- Multi-select folder choice
- `Inbox` included as a selectable option
- A message showing how many new emails were synced
- A chat area prepared for future AI interaction

사용자 입장에서는 다음이 보입니다.

- 메일 동기화 버튼
- 여러 폴더를 고를 수 있는 선택 UI
- `Inbox` 자체도 선택 가능
- 새로 저장된 메일 수를 알려주는 메시지
- 앞으로 AI 대화 기능으로 확장할 수 있는 채팅 영역

### Internal System Behavior

- Frontend: provides the UI and sends API requests
- Backend: reads Outlook emails, stores them, and returns responses
- Redis: stores folder-specific last sync timestamps
- SQLite: stores email content and metadata
- ChromaDB: stores vectors for semantic search
- Ollama + Llama 3: local AI generation for summarization and Q&A

시스템 내부에서는 다음처럼 역할이 나뉩니다.

- 프론트엔드: UI 제공, API 호출
- 백엔드: Outlook 읽기, 저장, 응답 처리
- Redis: 폴더별 마지막 sync 시간 저장
- SQLite: 메일 본문과 메타데이터 저장
- ChromaDB: 의미 기반 검색용 벡터 저장
- Ollama + Llama 3: 로컬 AI 요약 및 질의응답 준비

---

## 5. Technical Stack Used in This Project

Below is the technical stack currently confirmed from the codebase.

현재 코드 기준으로 확인되는 기술 스택은 아래와 같습니다.

### Backend

- Language: Python
- Framework: FastAPI
- Server: Uvicorn
- Validation: Pydantic
- ORM / DB access: SQLAlchemy
- Outlook integration: COM automation through `pywin32`
- HTTP client: `requests`

백엔드 기술은 다음과 같습니다.

- 언어: Python
- 프레임워크: FastAPI
- 서버: Uvicorn
- 데이터 검증: Pydantic
- DB 연결/ORM: SQLAlchemy
- Outlook 연동: `pywin32` 기반 COM 자동화
- HTTP 호출: `requests`

### Frontend

- Language: TypeScript
- Framework: Next.js
- UI library: React
- Styling: Tailwind CSS v4-based setup
- Linting: ESLint

프론트엔드 기술은 다음과 같습니다.

- 언어: TypeScript
- 프레임워크: Next.js
- UI 라이브러리: React
- 스타일링: Tailwind CSS v4 기반 설정
- 코드 품질 관리: ESLint

### Storage and Infrastructure

- Main email database: SQLite
- Cache / sync state store: Redis
- Redis runtime: Docker container `redis-stack-server` via `start.ps1`
- Vector database: ChromaDB
- Embedding model: `paraphrase-multilingual-MiniLM-L12-v2`

저장소와 인프라 관련 기술은 다음과 같습니다.

- 메일 저장 DB: SQLite
- 캐시 및 sync 상태 저장: Redis
- Redis 실행 방식: `start.ps1`에서 Docker 컨테이너 `redis-stack-server`
- 벡터 DB: ChromaDB
- 임베딩 모델: `paraphrase-multilingual-MiniLM-L12-v2`

### AI and Model Information

- Local LLM runtime: Ollama HTTP API
- Ollama endpoint: `http://localhost:11434/api/generate`
- Generation model currently referenced in code: `llama3`
- Current intended uses:
  - Email summarization
  - Email-based question answering

AI와 모델 관련 정보는 다음과 같습니다.

- 로컬 LLM 실행 방식: Ollama HTTP API
- Ollama 주소: `http://localhost:11434/api/generate`
- 현재 코드에 명시된 생성 모델: `llama3`
- 주요 용도:
  - 이메일 요약
  - 이메일 기반 질의응답

### Environment Assumptions

- Windows-based local environment
- Microsoft Outlook desktop app installed
- Outlook COM access available
- Local-first architecture
- Frontend: `localhost:3000`
- Backend: `localhost:8000`
- Ollama: `localhost:11434`
- Redis: `localhost:6379`

운영 환경 전제는 다음과 같습니다.

- Windows 로컬 환경
- Microsoft Outlook 데스크톱 앱 설치 필요
- Outlook COM 자동화 가능 환경 필요
- 로컬 중심 구조
- 프론트: `localhost:3000`
- 백엔드: `localhost:8000`
- Ollama: `localhost:11434`
- Redis: `localhost:6379`

---

## 6. Core Features Implemented So Far

### 6-1. Inbox and Subfolder Discovery

- The system can load subfolders under Outlook Inbox.
- The frontend shows those folders in a selectable UI.
- `Inbox` itself is also included as a selectable option.

현재 구현된 폴더 기능은 다음과 같습니다.

- Outlook Inbox 아래 하위 폴더 목록 조회 가능
- 프론트에서 폴더 선택 UI 제공
- `Inbox` 자체도 선택 옵션에 포함

### 6-2. Multi-Folder Email Sync

- Users can select multiple folders at once.
- The backend syncs the selected folders one by one.
- Duplicate folder selections are normalized internally.

현재 sync 기능은 다음과 같습니다.

- 여러 폴더를 한 번에 선택 가능
- 선택된 폴더들을 순차적으로 동기화
- 중복 선택은 내부적으로 정리

### 6-3. Delta Sync for New Emails Only

- Redis stores the last successful sync time per folder.
- The backend is designed to read only emails newer than the last sync.
- Duplicate emails are skipped based on stored IDs.

신규 메일만 저장하는 구조도 들어가 있습니다.

- Redis에 폴더별 마지막 동기화 시각 저장
- 그 이후 도착한 메일부터 읽도록 설계
- 이미 저장된 메일은 ID 기준으로 중복 저장 방지

### 6-4. Local Email Storage

- Emails read from Outlook are stored in SQLite.
- Stored fields include:
  - subject
  - sender
  - sender email
  - body preview
  - received time

메일 저장 기능도 구현되어 있습니다.

- Outlook에서 읽은 메일을 SQLite에 저장
- 저장 항목 예:
  - 제목
  - 보낸 사람
  - 보낸 사람 이메일
  - 본문 일부
  - 수신 시각

### 6-5. Basic Chat UI and Chat API Foundation

- The frontend has a chat input and message area.
- The backend exposes `/api/chat`.
- Redis-based response caching is already included.
- The current main chat response is still close to a placeholder, but the extension path is ready.

채팅 관련 기반도 준비되어 있습니다.

- 프론트에 채팅 입력창과 메시지 영역 존재
- 백엔드에 `/api/chat` API 존재
- Redis 기반 응답 캐시 구조 포함
- 현재 메인 응답은 샘플 성격이 있지만 확장 기반은 마련됨

### 6-6. Vector Search and AI Expansion Foundation

- Stored emails can be indexed into ChromaDB for semantic search.
- Related emails can be retrieved and passed to AI logic.
- Dedicated logic for email summarization already exists.

AI 확장 구조도 일부 구현되어 있습니다.

- 저장된 메일을 ChromaDB에 인덱싱 가능
- 질문과 관련된 메일을 검색해 AI에 전달 가능
- 이메일 요약 전용 로직이 분리되어 존재

---

## 7. One-Sentence Summary of the Current State

The project is currently at a stage where Outlook emails can be selectively synced from Inbox and Inbox subfolders, stored locally, and prepared for future AI-powered search, summarization, and question answering.

한 줄로 요약하면, 이 프로젝트는 Outlook 메일을 Inbox 및 하위 폴더에서 선택적으로 가져와 로컬에 저장하고, 앞으로 AI 검색, 요약, 질의응답으로 확장할 수 있는 기반이 마련된 상태입니다.

---

## 8. Strengths and Current Gaps

### What Is Already Strong

- Outlook integration works
- Multi-folder sync works
- Local DB storage works
- Redis integration exists
- Vector search foundation exists
- Local LLM integration code exists

현재 잘 갖춰진 점은 다음과 같습니다.

- Outlook 연동 가능
- 다중 폴더 sync 가능
- 로컬 DB 저장 가능
- Redis 연동 가능
- 벡터 검색 확장 기반 존재
- 로컬 LLM 연결 코드 존재

### What Still Needs Improvement

- Some chat logic is still mixed with placeholder behavior.
- Automatic vector indexing after sync is not fully wired into the main flow.
- Summaries are not yet deeply integrated into persistent storage usage.
- Error handling and runtime logging can be improved further.
- The UI can be made more friendly for non-technical users.

아직 보완이 필요한 점은 다음과 같습니다.

- 일부 채팅 로직은 아직 샘플 성격이 섞여 있음
- sync 후 자동 벡터 인덱싱이 메인 흐름에 완전히 연결되지 않음
- 요약 결과의 저장/활용 흐름이 아직 약함
- 예외 처리와 운영 로그를 더 강화할 필요가 있음
- 비전공자 친화적인 UI 설명을 더 보강할 수 있음

---

## 9. Recommended Next Improvements

### Product Features

- Automatic summarization after sync
- Priority classification for important emails
- Automatic action item extraction
- Grouping by client, project, or sender
- Search by date, sender, or keyword
- Unread-only filtering
- Attachment information display
- Scheduled sync for selected folders

제품 기능 측면에서 추가하면 좋은 것들은 다음과 같습니다.

- sync 후 자동 요약 생성
- 중요 메일 우선 분류
- 액션 아이템 자동 추출
- 고객/프로젝트/보낸 사람 기준 묶음 보기
- 날짜, 보낸 사람, 키워드 조건 검색
- 읽지 않은 메일만 보기
- 첨부파일 정보 표시
- 특정 폴더 정기 자동 sync

### AI Features

- Weekly summary of important emails
- Topic-based summary such as client-specific reports
- TODO generation from email content
- Better bilingual Korean/English responses
- Draft reply generation

AI 기능 측면에서 추천할 만한 확장입니다.

- 이번 주 중요 메일 요약
- 고객사/주제별 메일 보고서
- 메일 기반 업무 TODO 생성
- 한영 혼합 메일에 대한 자연스러운 응답
- 회신 초안 작성

### Technical and Operational Improvements

- Automatic ChromaDB indexing after sync
- Background job queue
- More tests
- Better error logging and monitoring
- `.env`-based configuration separation
- User/account separation
- Permission management
- Deployment-ready server structure

운영과 기술 측면에서의 개선 포인트입니다.

- sync 후 자동 ChromaDB 인덱싱
- 백그라운드 작업 큐 도입
- 테스트 코드 강화
- 에러 로깅 및 모니터링 강화
- `.env` 설정 분리
- 사용자/계정 분리
- 권한 관리
- 배포형 서버 구조 정리

### UI / UX Improvements

- A more intuitive folder selection UI
- Better sync progress display
- Recent sync history view
- Better failure messages
- Help section for non-technical users

UI/UX 측면에서 추가하면 좋은 점들입니다.

- 더 직관적인 폴더 선택 UI
- sync 진행 상태 시각화
- 최근 sync 이력 보기
- 실패 원인 안내 개선
- 비개발자용 도움말 영역 추가

---

## 10. Basic Requirements to Run the Project

To run this project properly, the following components should be available:

- Windows PC
- Microsoft Outlook desktop app
- An Outlook account configured in the app
- Python virtual environment
- Node.js / npm
- Redis
- Docker
- Ollama

이 프로젝트를 실행하려면 아래 요소들이 필요합니다.

- Windows PC
- Microsoft Outlook 데스크톱 앱
- Outlook 계정 연결
- Python 가상환경
- Node.js / npm
- Redis
- Docker
- Ollama

Typical runtime flow:

1. Start the Redis container
2. Start the FastAPI backend
3. Start the Next.js frontend
4. Start Ollama if AI features are needed
5. Open the web app and sync emails

일반적인 실행 순서는 다음과 같습니다.

1. Redis 컨테이너 실행
2. FastAPI 백엔드 실행
3. Next.js 프론트엔드 실행
4. 필요 시 Ollama 실행
5. 웹 화면에서 메일 sync 실행

---

## 11. Latest Reflected Changes

Recent updates reflected in this document:

- `Sync New Emails` can now sync selected Inbox subfolders
- Multiple folders can be selected at the same time
- `Inbox` itself is included as a selectable option
- Last sync time is tracked separately per selected folder

이번 문서에 반영된 최신 변경 사항은 다음과 같습니다.

- `Sync New Emails`에서 Inbox 하위 폴더 선택 가능
- 여러 폴더 동시 선택 가능
- `Inbox` 자체도 선택 가능
- 폴더별 마지막 sync 시간 개별 관리

---

## 12. Easiest Final Description

This project is a personal work assistant system that gathers Outlook emails into a format that AI can understand more easily.

Right now, it is centered on syncing and storing emails by folder, and it is in a strong position to grow into a system that can summarize emails, answer questions, and help organize follow-up work.

가장 쉽게 말하면, 이 프로젝트는 Outlook 메일을 AI가 이해하기 쉬운 형태로 모아두는 개인 업무 비서 시스템입니다.

지금은 폴더별 메일을 가져오고 저장하는 기능이 중심이지만, 앞으로는 메일 요약, 질문 응답, 후속 업무 정리까지 확장하기 좋은 상태입니다.

---

## 13. Current April 2026 Status

Recent implementation work completed after the original project summary:

- The embedding model is now loaded from a local path under `backend/models/` instead of downloading from Hugging Face on each run.
- Offline model usage is enforced in the backend startup path so the embedding model can be reused locally.
- `start.ps1` and `stop.ps1` were reorganized to better manage Redis, backend, and frontend startup/shutdown flow.
- A DB inspection API was added so synced emails can be viewed directly from SQLite through `/emails/db` and `/emails/db/count`.
- The frontend now includes a `View Synced Emails` button that opens a panel showing recently synced emails from the local DB.
- The chat UI now shows visible loading feedback such as `Searching emails...` while a question is running.
- Chat retrieval logic was refactored away from one-off hardcoded topic handling toward a more general retrieval flow.
- The backend now combines semantic search, DB keyword search, and time filtering before sending retrieved email context to the LLM.
- Recent query parsing now supports time-window style questions such as recent days / last week.
- Sender-aware query filtering was added so questions like "emails from Sean or 조형동" can be handled through sender matching rather than only loose keyword matching.
- Redis is currently used for chat response caching and folder-specific last sync timestamps.
- SQLite remains the source of truth for synced email content, while ChromaDB remains the vector index for semantic retrieval.

현재 추가로 반영된 최신 구현 상태는 다음과 같습니다.

- 임베딩 모델은 이제 매번 Hugging Face에서 내려받지 않고 `backend/models/` 아래 로컬 경로에서 직접 로드됩니다.
- 백엔드 실행 시 오프라인 모델 사용이 기본 경로로 반영되어 로컬 모델 재사용이 가능해졌습니다.
- `start.ps1`, `stop.ps1`가 Redis, 백엔드, 프론트 실행/종료 흐름을 더 안정적으로 관리하도록 정리되었습니다.
- 동기화된 메일을 SQLite 기준으로 직접 확인할 수 있도록 `/emails/db`, `/emails/db/count` API가 추가되었습니다.
- 프론트에는 `View Synced Emails` 버튼이 추가되어 로컬 DB에 저장된 최근 메일을 화면에서 바로 확인할 수 있습니다.
- 질문 실행 중에는 `Searching emails...` 같은 로딩 표시가 보여서 현재 처리 상태를 알 수 있습니다.
- 채팅 retrieval 로직은 특정 주제 하드코딩 중심이 아니라 일반적인 검색 흐름으로 리팩터링되었습니다.
- 백엔드는 semantic search, DB keyword search, 시간 필터를 결합한 뒤 그 결과만 LLM에 전달합니다.
- 최근 N일, 지난주 같은 시간 조건 질문을 파싱하는 로직이 들어갔습니다.
- `Sean` 또는 `조형동`처럼 보낸 사람 조건이 포함된 질문은 sender matching 기반으로 필터링하도록 확장되었습니다.
- Redis는 현재 채팅 응답 캐시와 폴더별 마지막 sync 시각 저장에 사용됩니다.
- SQLite는 sync된 메일의 원본 저장소로 유지되고, ChromaDB는 semantic retrieval용 벡터 인덱스로 사용됩니다.
