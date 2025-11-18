import os
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Any, Dict, Optional

from schemas import Job, Application
from database import create_document, get_documents, db

# bson comes with pymongo
from bson import ObjectId

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    doc = dict(doc)
    if doc.get("_id"):
        doc["id"] = str(doc.pop("_id"))
    # Convert any ObjectId nested values if needed
    for k, v in list(doc.items()):
        if isinstance(v, ObjectId):
            doc[k] = str(v)
    return doc


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# -----------------------------
# Careers API
# -----------------------------

@app.get("/careers/jobs")
def list_jobs() -> List[Dict[str, Any]]:
    try:
        docs = get_documents("job", {}, limit=None)
        return [serialize_doc(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/careers/jobs", status_code=201)
def create_job(job: Job) -> Dict[str, Any]:
    try:
        inserted_id = create_document("job", job)
        # Fetch created document
        doc = db["job"].find_one({"_id": ObjectId(inserted_id)})
        return serialize_doc(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/careers/jobs/{job_id}")
def get_job(job_id: str) -> Dict[str, Any]:
    try:
        if not ObjectId.is_valid(job_id):
            raise HTTPException(status_code=400, detail="Invalid job id")
        doc = db["job"].find_one({"_id": ObjectId(job_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Job not found")
        return serialize_doc(doc)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/careers/apply", status_code=201)
async def apply(request: Request,
                # Optional multipart form fields
                job_id: Optional[str] = Form(None),
                name: Optional[str] = Form(None),
                email: Optional[str] = Form(None),
                phone: Optional[str] = Form(None),
                linkedin: Optional[str] = Form(None),
                portfolio: Optional[str] = Form(None),
                cover_letter: Optional[str] = Form(None),
                consent: Optional[bool] = Form(False),
                cv: Optional[UploadFile] = File(None),
                portfolio_file: Optional[UploadFile] = File(None)) -> Dict[str, Any]:
    """
    Accepts either JSON (Application schema) or multipart/form-data with optional file uploads.
    Files are not stored as binary to keep demo simple; we store filenames, content types and sizes.
    """
    try:
        payload: Dict[str, Any] = {}
        content_type = request.headers.get("content-type", "")
        if content_type.startswith("multipart/form-data") or job_id is not None:
            # Build from form fields
            payload = {
                "job_id": job_id,
                "name": name,
                "email": email,
                "phone": phone,
                "linkedin": linkedin,
                "portfolio": portfolio,
                "cover_letter": cover_letter,
                "consent": bool(consent),
            }
            # Validate job exists if possible
            if payload.get("job_id") and ObjectId.is_valid(payload["job_id"]):
                exists = db["job"].find_one({"_id": ObjectId(payload["job_id"])})
                if not exists:
                    raise HTTPException(status_code=404, detail="Job not found for application")
            # Attach file metadata
            files_meta: Dict[str, Any] = {}
            for label, uploaded in ("cv", cv), ("portfolio_file", portfolio_file):
                if uploaded is not None:
                    b = await uploaded.read()
                    files_meta[label] = {
                        "filename": uploaded.filename,
                        "content_type": uploaded.content_type,
                        "size": len(b),
                    }
            if files_meta:
                payload["files"] = files_meta
        else:
            # JSON path
            data = await request.json()
            # Validate with Pydantic
            _app = Application(**data)
            payload = _app.dict()
            # Validate job exists if possible
            jid = payload.get("job_id")
            if jid and ObjectId.is_valid(jid):
                exists = db["job"].find_one({"_id": ObjectId(jid)})
                if not exists:
                    raise HTTPException(status_code=404, detail="Job not found for application")

        inserted_id = create_document("application", payload)
        doc = db["application"].find_one({"_id": ObjectId(inserted_id)})
        return serialize_doc(doc)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/careers/seed", status_code=201)
def seed_jobs():
    """Seed a few example jobs for demo purposes."""
    try:
        count = db["job"].count_documents({}) if db else 0
        if count > 0:
            return {"seeded": False, "message": "Jobs already exist"}
        examples = [
            {
                "title": "Senior SEO Strategist",
                "department": "Organic",
                "location": "Brighton, UK",
                "employment_type": "Full-time",
                "description": "Lead strategy across enterprise SEO accounts, collaborating with content, UX, and dev.",
                "responsibilities": [
                    "Own SEO strategy for key clients",
                    "Guide technical audits and roadmaps",
                    "Mentor junior team members"
                ],
                "requirements": [
                    "5+ years SEO experience",
                    "Strong technical SEO skills",
                    "Comfortable with stakeholder communication"
                ],
                "salary_range": "£45k–£60k DOE",
                "remote": True
            },
            {
                "title": "Performance Media Manager",
                "department": "Media",
                "location": "Hybrid / Brighton",
                "employment_type": "Full-time",
                "description": "Plan, launch and optimize paid search & social campaigns focused on measurable growth.",
                "responsibilities": [
                    "Own PPC & Paid Social across channels",
                    "Implement testing frameworks",
                    "Report insights and iterate"
                ],
                "requirements": [
                    "4+ years in performance media",
                    "Platform certifications",
                    "Strong analytical mindset"
                ],
                "salary_range": "£40k–£55k DOE",
                "remote": True
            },
            {
                "title": "Product Designer (UX/UI)",
                "department": "Creative",
                "location": "Remote (UK)",
                "employment_type": "Contract",
                "description": "Design simple, beautiful product experiences across web with accessibility in mind.",
                "responsibilities": [
                    "Translate strategy into UX flows",
                    "Create UI systems and prototypes",
                    "Collaborate with dev for implementation"
                ],
                "requirements": [
                    "Strong portfolio of shipped work",
                    "Accessibility knowledge",
                    "Proficiency in Figma"
                ],
                "salary_range": "Competitive",
                "remote": True
            }
        ]
        ids = []
        for ex in examples:
            ids.append(create_document("job", ex))
        return {"seeded": True, "count": len(ids), "ids": ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
