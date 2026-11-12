# AI-Powered Job Portal Backend

An AI-powered Job Portal Backend built using **FastAPI** and **PostgreSQL** to streamline the recruitment process. The system connects job seekers with relevant job opportunities through AI-based resume analysis, candidate-job matching, and personalized job recommendations.

## Features

- **User Authentication:** Secure user registration and login.
- **Job Management:** Create, update, delete, and view job postings.
- **Candidate Profiles:** Manage candidate information, skills, and qualifications.
- **Resume Upload:** Upload and manage candidate resumes.
- **Resume Analysis:** AI-powered analysis of uploaded resumes.
- **Job Matching:** Match candidates with suitable job opportunities based on their skills and qualifications.
- **Job Recommendations:** Provide personalized job recommendations.
- **Job Applications:** Allow candidates to apply for available jobs.

## Tech Stack

- **Backend:** FastAPI
- **Database:** PostgreSQL
- **Language:** Python
- **AI Integration:** AI-based resume analysis and job matching
- **API Style:** RESTful APIs

### 1. Clone the Repository

```bash
git clone <repository-url>
cd job-portal-backend
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
uvicorn app.main:app --reload
```

## API Documentation

After starting the server, access the interactive API documentation:

- **Swagger UI:** http://127.0.0.1:8000/docs

## Project Objective

The main objective of this project is to simplify and improve the recruitment process using modern backend technologies and AI integration. It helps employers find suitable candidates and enables job seekers to discover relevant job opportunities efficiently.