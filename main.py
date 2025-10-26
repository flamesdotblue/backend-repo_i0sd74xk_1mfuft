import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product as ProductSchema, Project as ProjectSchema, QuoteRequest, ContactMessage

app = FastAPI(title="Diwan Al-Ardiya API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    d = dict(doc)
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    return d


@app.get("/")
def root():
    return {"status": "ok", "service": "Diwan Al-Ardiya Backend"}


@app.get("/test")
def test_database():
    try:
        collections = db.list_collection_names() if db else []
        return {"backend": "running", "db_connected": bool(db), "collections": collections}
    except Exception as e:
        return {"backend": "running", "db_connected": False, "error": str(e)}


# ------ Products ------
@app.get("/api/categories")
def get_categories():
    return [
        "Timber & Plywood",
        "Steel & Rebar",
        "Fixings & Hardware",
        "HVAC & Installation",
    ]


@app.get("/api/products")
def list_products(category: Optional[str] = None, material_type: Optional[str] = None, size: Optional[str] = None, q: Optional[str] = None, limit: Optional[int] = 100):
    filt: Dict[str, Any] = {"is_active": True}
    if category:
        filt["category"] = category
    if material_type:
        filt["material_type"] = material_type
    if size:
        filt["size"] = size
    if q:
        # naive text search on title/description
        filt["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
        ]
    docs = get_documents("product", filt, limit)
    return [serialize_doc(d) for d in docs]


@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    try:
        doc = db["product"].find_one({"_id": ObjectId(product_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Product not found")
        return serialize_doc(doc)
    except Exception:
        raise HTTPException(status_code=404, detail="Product not found")


@app.post("/api/products")
def create_product(payload: ProductSchema):
    inserted_id = create_document("product", payload)
    return {"id": inserted_id}


# ------ Projects ------
@app.get("/api/projects")
def list_projects(limit: Optional[int] = 100):
    docs = get_documents("project", {"is_active": True}, limit)
    return [serialize_doc(d) for d in docs]


@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    try:
        doc = db["project"].find_one({"_id": ObjectId(project_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Project not found")
        return serialize_doc(doc)
    except Exception:
        raise HTTPException(status_code=404, detail="Project not found")


@app.post("/api/projects")
def create_project(payload: ProjectSchema):
    inserted_id = create_document("project", payload)
    return {"id": inserted_id}


# ------ Quote & Contact ------

class EmailResult(BaseModel):
    sent: bool
    detail: str


def maybe_send_email(subject: str, body: str) -> EmailResult:
    # Optional email sending via SMTP if environment is configured
    import smtplib
    from email.mime.text import MIMEText

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "0")) or None
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    email_to = os.getenv("EMAIL_TO")
    email_from = os.getenv("EMAIL_FROM", smtp_user or "noreply@example.com")

    if not (smtp_host and smtp_port and email_to):
        return EmailResult(sent=False, detail="SMTP not configured; entry logged to database only.")

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = email_from
        msg["To"] = email_to

        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.sendmail(email_from, [email_to], msg.as_string())
        return EmailResult(sent=True, detail="Email sent")
    except Exception as e:
        return EmailResult(sent=False, detail=f"Email error: {e}")


@app.post("/api/quote")
def create_quote(payload: QuoteRequest):
    # log to DB
    quote_id = create_document("quoterequest", payload)
    body = (
        f"New Quote Request\n\n"
        f"Name: {payload.name}\nCompany: {payload.company or '-'}\n"
        f"Email: {payload.email}\nPhone: {payload.phone or '-'}\n"
        f"Product: {payload.product or '-'}\n\nMessage:\n{payload.message or '-'}\n"
    )
    email_res = maybe_send_email("New Quote Request", body)
    return {"id": quote_id, "email": email_res.model_dump()}


@app.post("/api/contact")
def create_contact(payload: ContactMessage):
    msg_id = create_document("contactmessage", payload)
    body = (
        f"New Contact Message\n\n"
        f"Name: {payload.name}\nCompany: {payload.company or '-'}\n"
        f"Email: {payload.email}\nPhone: {payload.phone or '-'}\n"
        f"Interest: {payload.interest or '-'}\n\nMessage:\n{payload.message}\n"
    )
    email_res = maybe_send_email("New Contact Message", body)
    return {"id": msg_id, "email": email_res.model_dump()}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
