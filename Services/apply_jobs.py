from sqlalchemy.orm import joinedload
from datetime import datetime
from typing import Literal, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import selectinload
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from utilities.database import get_db                      # adjust to your project
from utilities.models import Applications, CandidateProfile, Jobs, User
from authentication.get_current_user import get_current_user

load_dotenv()

# ---------- AI gives only the match score ----------
class MatchScore(BaseModel):
    match_score: int = Field(
        ge=0, le=100,
        description=(
            "Integer from 0 to 100 showing how well the candidate fits the job, "
            "based only on evidence stated in the candidate summary."
        ),
    )


score_parser = PydanticOutputParser(pydantic_object=MatchScore)

score_prompt = ChatPromptTemplate.from_messages([
    ("system",
     """You are a careful recruiter assistant. Compare the candidate summary to the job and give a match score.

STRICT RULES:
1. Base the score ONLY on what is explicitly written in the candidate summary and job description. Do not assume or invent details.
2. Do NOT be influenced by buzzwords. A skill name alone is weak evidence; give credit only when the summary shows it used in a project, job, or achievement.
3. Missing job requirements lower the score.
4. Do not inflate the score.

SCORING GUIDE:
- 80-100: most requirements clearly demonstrated
- 50-79: partial match with some demonstrated requirements and some gaps
- 20-49: weak match, little demonstrated evidence
- 0-19: almost no relevant evidence

{format_instructions}"""),
    ("human",
     "JOB TITLE: {job_title}\n\nJOB DESCRIPTION:\n{job_description}\n\n"
     "CANDIDATE SUMMARY:\n{candidate_summary}"),
]).partial(format_instructions=score_parser.get_format_instructions())

llm = ChatGroq(model="openai/gpt-oss-120b")
score_chain = score_prompt | llm | score_parser


router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("/{job_id}", status_code=201)
async def apply_to_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = (
        await db.execute(select(Jobs).where(Jobs.id == job_id))
    ).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    profile = (
        await db.execute(
            select(CandidateProfile).where(CandidateProfile.user_id == current_user.id)
        )
    ).scalar_one_or_none()
    if not profile or not profile.AI_Resume_Summary:
        raise HTTPException(
            status_code=400,
            detail="Please upload your resume to create your profile before applying.",
        )

    already_applied = (
        await db.execute(
            select(Applications.id).where(
                Applications.job_id == job_id,
                Applications.applicant_id == current_user.id,
            )
        )
    ).first()
    if already_applied:
        raise HTTPException(status_code=409, detail="You have already applied to this job.")

    try:
        result = await score_chain.ainvoke({
            "job_title": job.title,
            "job_description": job.description,
            "candidate_summary": profile.AI_Resume_Summary,
        })
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to calculate match score.")

    application = Applications(
        job_id=job_id,
        applicant_id=current_user.id,
        match_score=result.match_score,
    )
    try:
        db.add(application)
        await db.commit()
        await db.refresh(application)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save the application.")

    return {
        "id": application.id,
        "job_id": application.job_id,
        "match_score": application.match_score,
        "interview_date": application.interview_date,
        "summary": profile.AI_Resume_Summary,   # profile se aati hai, yahan store nahi
        "interview_status": application.interview_status,
        "created_at": application.created_at,
    }

@router.get("/me")
async def my_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(Applications, CandidateProfile.AI_Resume_Summary)
            .join(CandidateProfile, CandidateProfile.user_id == Applications.applicant_id)
            .where(Applications.applicant_id == current_user.id)
            .order_by(Applications.created_at.desc())
        )
    ).all()

    return [
        {
            "id": a.id,
            "job_id": a.job_id,
            "match_score": a.match_score,
            "summary": summary,
            "interview_date": a.interview_date,
            "interview_status": a.interview_status,
            "created_at": a.created_at,
        }
        for a, summary in rows
    ]

@router.get("/job/{job_id}")
async def job_applications(
    job_id: int,
    skip: int = 0,
    limit: int = 20,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can view applicants.")

    job = await db.scalar(
        select(Jobs).where(Jobs.id == job_id, Jobs.recruiter_id == current_user.id)
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    result = await db.execute(
        select(Applications, CandidateProfile.AI_Resume_Summary)
        .where(
            Applications.job_id == job_id,
            CandidateProfile.user_id == Applications.applicant_id,
        )
        .order_by(Applications.match_score.desc(), Applications.id)
        .offset(skip)
        .limit(limit)
    )

    return [
        {
            "id": app.id,
            "applicant_id": app.applicant_id,
            "match_score": app.match_score,
            "summary": summary,
            "interview_status": app.interview_status,
            "interview_date": app.interview_date,
        }
        for app, summary in result.all()
    ]

@router.get("/{application_id}")
async def get_single_application(
    application_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Applications, CandidateProfile.AI_Resume_Summary)
        .outerjoin(CandidateProfile, CandidateProfile.user_id == Applications.applicant_id)
        .options(joinedload(Applications.job))
        .where(
            Applications.id == application_id,
        )
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Application not found")

    app, summary = row

    return {
        "id": app.id,
        "job_id": app.job_id,
        "job_title": app.job.title,
        "applicant_id": app.applicant_id,
        "match_score": app.match_score,
        "summary": summary,
        "interview_status": app.interview_status,
        "interview_date": app.interview_date,
    }

from datetime import datetime
from pydantic import BaseModel

class InterviewUpdate(BaseModel):
    interview_status: str | None = None
    interview_date: datetime | None = None

@router.patch("/{application_id}/interview")
async def update_interview(
    application_id: int,
    payload: InterviewUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can update interviews.")

    app = await db.scalar(
        select(Applications).where(
            Applications.id == application_id,
            Applications.job.has(Jobs.recruiter_id == current_user.id),
        )
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update.")

    for field, value in data.items():
        setattr(app, field, value)

    await db.commit()
    await db.refresh(app)

    return {
        "id": app.id,
        "interview_status": app.interview_status,
        "interview_date": app.interview_date,
    }