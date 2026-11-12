from sqlalchemy import select
from utilities.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import profile
from fastapi import File, UploadFile, APIRouter, Depends, HTTPException 
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from utilities.models import CandidateProfile, User
from authentication.get_current_user import get_current_user
import io
from pypdf import PdfReader

load_dotenv()

class ResumeAnalysis(BaseModel):
    AI_Resume_Summary: str = Field(
        description=(
            "A single professional summary of 5-8 sentences, written only from "
            "facts stated in the resume. It covers: who the candidate is "
            "(role/field, education, experience level), the key projects they "
            "have actually built (what each does and the tech used), and their "
            "strongest points such as achievements, certifications, or "
            "standout strengths that are explicitly stated."
        )
    )


parser = PydanticOutputParser(pydantic_object=ResumeAnalysis)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     """You are a careful resume analyst. Read the resume text and write one concise professional summary.

STRICT RULES:
1. Base everything ONLY on what is explicitly written in the resume. Do not assume, infer, or invent details.
2. Do NOT be influenced by buzzwords. A keyword like "AI", "Machine Learning", "LLM", "Cloud", or "Leadership" appearing in a skills list does NOT mean the candidate has real experience with it. Mention a skill as a strength only if the resume shows it used in a project, job, or achievement.
3. If a skill is listed but has no supporting context, either leave it out or describe it neutrally as "listed skill".
4. Do not exaggerate. Avoid inflated words like "expert", "world-class", "cutting-edge" unless the resume itself supports them with evidence.
5. If the resume has no projects or achievements, say so briefly instead of guessing.
6. Keep the tone professional, factual, and concise.

WHAT THE SUMMARY MUST INCLUDE (as flowing text, not bullet points):
- Who the candidate is: role/field, education, and experience level.
- Their key projects: what each one does and the technologies used, as stated in the resume.
- Their best points: achievements, certifications, and strengths backed by evidence in the resume.

{format_instructions}"""),
    ("human", "Resume text:\n\n{resume_text}")
])

prompt = prompt.partial(format_instructions=parser.get_format_instructions())

llm = ChatGroq(model="openai/gpt-oss-120b")
chain = prompt | llm | parser

router = APIRouter(prefix="/user/profile", tags=["user profile"])

MAX_PDF_SIZE = 5 * 1024 * 1024  # 5 MB
MIN_TEXT_LENGTH = 50            # below this, we treat the PDF as scanned/image-only


async def extract_text_from_pdf(file: UploadFile) -> str:
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(data) > MAX_PDF_SIZE:
        raise HTTPException(status_code=413, detail="PDF is too large (max 5 MB).")

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            reader.decrypt("")  # works only for PDFs with an empty password
        text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read the PDF file.")

    if len(text) < MIN_TEXT_LENGTH:
        raise HTTPException(
            status_code=422,
            detail="Scanned PDFs are not supported. Please upload a text-based PDF (not a scan or image).",
        )

    return text


router = APIRouter(prefix="/user/profile", tags=["user profile"])


@router.post("/")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    resume: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    resume_text = await extract_text_from_pdf(resume)

    try:
        result = await chain.ainvoke({"resume_text": resume_text})
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to analyze the resume.")

    check = await db.scalar(
        select(CandidateProfile)
        .where(
            CandidateProfile.user_id == current_user.id,
        )
    )

    if check:
        check.AI_Resume_Summary = result.AI_Resume_Summary
        await db.commit()
        return {"AI_Resume_Summary": result.AI_Resume_Summary}

    profile = CandidateProfile(user_id=current_user.id, AI_Resume_Summary=result.AI_Resume_Summary)
    db.add(profile)
    await db.commit()
    return {"AI_Resume_Summary": result.AI_Resume_Summary}