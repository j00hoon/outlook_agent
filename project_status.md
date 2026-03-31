📂 Project Overview

This project is a web application that fetches recent Outlook emails and summarizes them.
The backend is built with FastAPI (Python) and the frontend with Next.js (TypeScript).

Backend: Fetches Outlook emails using COM automation (win32com) and summarizes email content.
Frontend: Provides a UI to load emails on demand and displays email summaries.

이 프로젝트는 Outlook 이메일을 가져와 요약하는 웹 애플리케이션입니다.

- 백엔드: FastAPI (Python)
  - COM 자동화를 이용해 Outlook 이메일을 가져옴 (win32com)
- 프론트엔드: Next.js (TypeScript + React)
  - 버튼 클릭 시 이메일을 가져오고 요약 내용을 표시

📂 Project Structure
backend/
├─ app/
│ ├─ main.py # FastAPI entry point, FastAPI 진입점
│ ├─ routes/
│ │ └─ emails.py # FastAPI route for /emails API, /emails API 라우트
│ ├─ outlook_reader.py # Fetch emails from Outlook, Outlook에서 이메일 가져오기
│ └─ summarizer.py # Summarize email content, 이메일 요약
├─ venv/ # Python virtual environment, 파이썬 가상환경
frontend/
├─ app/
│ └─ page.tsx # Next.js main page (React client), Next.js 메인 페이지
├─ services/
│ └─ emailService.ts # API call helper for frontend, API 호출 헬퍼
├─ package.json

⚡ Project Behavior

1. Backend
   - /emails/ API fetches the most recent 10 emails from Outlook by default.
   - Each email contains: subject, body, sender, sender_email, received_time, summary.
   - COM initialization is handled properly to avoid errors (pythoncom.CoInitialize()).
2. Frontend
   - UI has a "Load Emails" button to fetch emails on demand.
   - Emails are displayed with subject, sender, received time, and summarized content.
   - Colors updated for better readability (purple theme).

- 백엔드
  - /emails/ API는 기본적으로 최근 10개 이메일을 가져옵니다
  - 이메일 데이터는 subject, body, sender, sender_email, received_time, summary를 포함
  - COM 초기화가 올바르게 처리됨 (pythoncom.CoInitialize())
- 프론트엔드
  - "Load Emails" 버튼 클릭 시 이메일 가져오기
  - 이메일은 제목, 보낸 사람, 수신 시간, 요약과 함께 표시
  - 읽기 편하도록 색상 업데이트 (보라색 테마)

🏁 Initial Setup

1. Backend Setup

# Create and activate virtual environment

python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies

pip install -r requirements.txt

# Start FastAPI server

uvicorn app.main:app --reload

# Open Swagger docs

http://127.0.0.1:8000/docs

2. Frontend Setup

# Navigate to frontend folder

cd frontend

# Install dependencies

npm install

# Start Next.js development server

npm run dev

# Open in browser

http://localhost:3000

## Execution Steps / 실행 순서

### English

1. **Start Backend (FastAPI)**

   - Navigate to the backend folder and run:
     ```powershell
     cd backend
     uvicorn app.main:app --reload
     ```
   - This will start the FastAPI server on port 8000. The frontend fetches emails from this API.

2. **Start Frontend (Next.js)**

   - If it's the first time setting up the project, install dependencies:
     ```powershell
     cd frontend
     npm install
     ```
   - Then start the frontend development server:
     ```powershell
     npm run dev
     ```
   - The React app will run on port 3000.

3. **Start Ollama LLaMA 3 model (Optional, for email summarization)**
   - If you want the email summarization feature, run:
     ```powershell
     ollama run llama3
     ```
   - This is only needed when using the summarization feature. If you only fetch emails, you can skip this.

**Summary:**

- Backend must always run for API requests.
- Frontend requires `npm run dev` to start the app.
- Ollama is required only if using the summarization feature.

⚙️ Notes & Tips

- Ensure Outlook is running for COM automation
- Backend fetches emails only when you click "Load Emails"
- You can change the number of emails with limit parameter
- Configure CORS in FastAPI if frontend & backend run on different ports

📌 Next Steps

- Store summarized emails in a database to avoid repeated fetches
- Add error handling for Outlook not running / COM errors
