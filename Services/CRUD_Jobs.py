from typing import List
from sqlalchemy import select, func
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query
from authentication.get_current_user import get_current_user
from utilities.models import User, Jobs
from utilities.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
    
class PosJobReq(BaseModel):
    title:str
    description:str
    company:str
    location:str
    salary:str
    type:str

class JobRes(BaseModel):
    id:int
    title:str
    description:str
    company:str
    location:str
    salary:str
    type:str

    class Config:
        from_attributes = True


class JobListRes(BaseModel):
    total: int           
    page: int
    limit: int
    total_pages: int
    jobs: list[JobRes]


router = APIRouter(tags=["Jobs"])

@router.get("/get_all_jobs", response_model=JobListRes)            #Using Pagination
async def get_all_jobs(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * limit

    result = await db.execute(
        select(Jobs)
        .offset(offset)
        .limit(limit)
    )

    jobs = result.scalars().all()
    total = (await db.execute(select(func.count(Jobs.id)))).scalar_one()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": ceil(total / limit),
        "jobs": jobs,
    }

@router.post("/post-job")
async def post_job(job: PosJobReq, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "recruiter":
        raise HTTPException(status_code=403,detail="You are not authorized to post a job")
    
    db_job = Jobs(
        recruiter_id=user.id,title=job.title,description=job.description,company=job.company,location=job.location,
        salary=job.salary,type=job.type
        )
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    return {"message": "Job posted successfully"}


@router.get("/jobs", response_model=list[JobRes])
async def get_all_jobs(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "recruiter":
        raise HTTPException(status_code=403,detail="You are not authorized to view jobs")
    
    result = await db.execute(select(Jobs).where(Jobs.recruiter_id == user.id))
    jobs = result.scalars().all()
    return jobs

@router.get("/job/{id}", response_model=JobRes)
async def get_job(id:int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "recruiter":
        raise HTTPException(status_code=403,detail="You are not authorized to view job")

    job = await db.execute(select(Jobs).where(Jobs.id == id, Jobs.recruiter_id == user.id))
    job = job.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404,detail="Job not found or you are not authorized to view this job")
    return job

@router.put("/job/{id}", response_model=JobRes)
async def update_job(id:int, job: PosJobReq, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    # if user.role != "recruiter":
    #     raise HTTPException(status_code=403,detail="You are not authorized to update job")
    
    result = await db.execute(select(Jobs).where(Jobs.id == id))# , Jobs.recruiter_id == user.id
    db_job = job.scalar_one_or_none()
    if not db_job:
        raise HTTPException(status_code=404,detail="Job not found or you are not authorized to update this job")
    
    db_job.title = job.title
    db_job.description = job.description
    db_job.company = job.company
    db_job.location = job.location
    db_job.salary = job.salary
    db_job.type = job.type
    await db_job.commit()
    await db_job.refresh(job)
    return db_job

@router.delete("/job/{id}")
async def delete_job(id:int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "recruiter":
        raise HTTPException(status_code=403,detail="You are not authorized to delete job")
    
    job = await db.execute(select(Jobs).where(Jobs.id == id, Jobs.recruiter_id == user.id)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404,detail="Job not found or you are not authorized to delete this job")
    await db.delete(job)
    await db.commit()
    return {"message": "Job deleted successfully"}

