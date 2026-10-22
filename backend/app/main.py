import os
import re
from random import SystemRandom
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from jose import JWTError, jwt
from pydantic import BaseModel, Field

from . import content, db


app = FastAPI(title="PrePora API", version="0.2.0")
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
allowed_origins = list({frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"})
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TestConfig(BaseModel):
    exam: Literal["NEET-UG", "CBSE Boards", "CUET-UG", "AIIMS Nursing"]
    subject: Literal["Physics", "Chemistry", "Biology", "Mixed"]
    questions: int = Field(ge=5, le=180)
    duration_minutes: int = Field(ge=15, le=240)
    difficulty: Literal["Easy", "Medium", "Hard", "Mixed"]
    negative_marking: bool = True
    class_level: Literal["11th", "12th", "Mixed"] = "Mixed"
    chapter: str | None = Field(default=None, max_length=160)


class AuthPayload(BaseModel):
    email: str = Field(min_length=3, max_length=160)
    password: str = Field(min_length=6, max_length=128)
    name: str | None = Field(default=None, max_length=80)


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    target_exam: Literal["NEET-UG", "CBSE Boards", "CUET-UG", "AIIMS Nursing"] | None = None
    target_date: date | None = None


class ProgressEvent(BaseModel):
    event_type: Literal["question_solved", "study_minutes", "session_completed"]
    value: int = Field(ge=1, le=10000)
    subject: Literal["Physics", "Chemistry", "Biology"] | None = None


class TestAttemptCreate(BaseModel):
    test_id: str = Field(min_length=1, max_length=120)
    config: dict[str, Any] = Field(default_factory=dict)
    score: float = Field(ge=0, le=100)
    correct: int = Field(ge=0, le=500)
    incorrect: int = Field(ge=0, le=500)
    unanswered: int = Field(ge=0, le=500)
    duration_seconds: int = Field(ge=0, le=86400)


class SessionAnswer(BaseModel):
    question_index: int = Field(ge=0, le=200)
    option: int | None = Field(default=None, ge=0, le=5)
    marked: bool = False


class StudyItemCreate(BaseModel):
    kind: Literal["queue", "planner", "mistake"] = "planner"
    subject: Literal["Physics", "Chemistry", "Biology"]
    class_level: Literal["11th", "12th", "Mixed"] = "Mixed"
    chapter: str = Field(min_length=2, max_length=160)
    title: str | None = Field(default=None, max_length=160)
    reason: str | None = Field(default=None, max_length=240)
    priority: Literal["High", "Medium", "Low"] = "Medium"
    duration_minutes: int = Field(default=15, ge=5, le=240)
    due_date: date | None = None


class TutorPayload(BaseModel):
    prompt: str = Field(min_length=1, max_length=1200)
    mode: Literal["Explain simply", "Step-by-step", "Quiz me", "Revision plan"] = "Explain simply"
    subject: Literal["Physics", "Chemistry", "Biology"] | None = None
    chapter: str | None = None


DEMO_QUESTIONS = [
    {"id": 1, "subject": "Physics", "chapter": "Electrostatics", "prompt": "Two point charges are placed in vacuum...", "options": ["Attraction", "Repulsion", "No force", "Depends on mass"], "answer": 1},
    {"id": 2, "subject": "Chemistry", "chapter": "Electrochemistry", "prompt": "The SI unit of molar conductivity is:", "options": ["S m² mol⁻¹", "S m⁻¹", "Ω m", "mol S⁻¹"], "answer": 0},
    {"id": 3, "subject": "Biology", "chapter": "Genetics", "prompt": "The physical basis of heredity is best represented by:", "options": ["Cell wall", "DNA sequence", "Ribosome", "Cytoplasm"], "answer": 1},
]

SESSION_QUESTIONS = [
    {"id": "phy-electrostatics-01", "subject": "Physics", "chapter": "Electric Charges and Fields", "text": "If both point charges are doubled while distance remains the same, the electrostatic force becomes:", "options": ["Half", "Double", "Four times", "Unchanged"], "answer": 2, "explanation": "Coulomb force is proportional to q₁q₂, so doubling both charges makes it four times."},
    {"id": "phy-current-01", "subject": "Physics", "chapter": "Current Electricity", "text": "For a conductor obeying Ohm’s law, which relation is correct?", "options": ["V = IR", "V = I/R", "R = VI", "P = I/R"], "answer": 0, "explanation": "At constant physical conditions, V = IR."},
    {"id": "phy-optics-01", "subject": "Physics", "chapter": "Ray Optics and Optical Instruments", "text": "The lens formula using the Cartesian sign convention is:", "options": ["1/f = 1/v − 1/u", "1/f = 1/u + 1/v", "f = u + v", "m = u/v only"], "answer": 0, "explanation": "For a thin lens, 1/f = 1/v − 1/u."},
    {"id": "chem-electrochem-01", "subject": "Chemistry", "chapter": "Electrochemistry", "text": "The standard cell potential is calculated as:", "options": ["E°anode − E°cathode", "E°cathode − E°anode", "E°anode + E°cathode", "nF/ΔG°"], "answer": 1, "explanation": "E°cell = E°cathode − E°anode."},
    {"id": "chem-kinetics-01", "subject": "Chemistry", "chapter": "Chemical Kinetics", "text": "The half-life of a first-order reaction is:", "options": ["0.693/k", "k/0.693", "1/k²", "2k"], "answer": 0, "explanation": "For first order kinetics, t₁/₂ = 0.693/k."},
    {"id": "chem-solutions-01", "subject": "Chemistry", "chapter": "Solutions", "text": "The osmotic pressure of a dilute solution is:", "options": ["π = CRT", "π = C/RT", "π = RT/C", "π = C + RT"], "answer": 0, "explanation": "For a dilute solution, π = CRT."},
    {"id": "bio-genetics-01", "subject": "Biology", "chapter": "Molecular Basis of Inheritance", "text": "The enzyme that joins Okazaki fragments is:", "options": ["DNA polymerase", "DNA ligase", "Helicase", "Primase"], "answer": 1, "explanation": "DNA ligase seals the nicks between Okazaki fragments."},
    {"id": "bio-health-01", "subject": "Biology", "chapter": "Human Health and Disease", "text": "Vaccination primarily produces:", "options": ["Passive immunity only", "Active acquired immunity", "No immune memory", "Only innate immunity"], "answer": 1, "explanation": "Vaccines stimulate active acquired immunity and memory cells."},
]

JWT_ALGORITHM = "HS256"
JWT_SECRET = os.getenv("JWT_SECRET", "development-only-change-this-secret")
if os.getenv("APP_ENV", "development").lower() == "production" and JWT_SECRET == "development-only-change-this-secret":
    raise RuntimeError("JWT_SECRET must be replaced before running PrePora in production.")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    return normalized


def display_name(email: str, requested_name: str | None = None) -> str:
    if requested_name and requested_name.strip():
        return " ".join(word.capitalize() for word in requested_name.strip().split())
    local_part = email.split("@", 1)[0]
    words = re.sub(r"[^a-zA-Z0-9]+", " ", local_part).split()
    return " ".join(word.capitalize() for word in words) or "Student"


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "target_exam": user["target_exam"],
        "target_date": user["target_date"],
        "created_at": user["created_at"],
    }


def issue_token(user_id: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(days=30)
    return jwt.encode({"sub": user_id, "exp": expires}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _user_from_header(authorization: str | None) -> dict[str, Any] | None:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Use a Bearer token.")
    try:
        payload = jwt.decode(authorization.removeprefix("Bearer "), JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
    except JWTError as error:
        raise HTTPException(status_code=401, detail="Your session has expired. Please log in again.") from error
    user = db.get_user(str(user_id)) if user_id else None
    if not user:
        raise HTTPException(status_code=401, detail="User account was not found.")
    return user


def optional_user(authorization: str | None = Header(default=None)) -> dict[str, Any] | None:
    return _user_from_header(authorization)


def required_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    user = _user_from_header(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Log in to access your workspace.")
    return user


def dashboard_for(user: dict[str, Any]) -> dict[str, Any]:
    progress = db.get_progress(user["id"])
    return {
        "demo": False,
        "user": public_user(user),
        "stats": {
            "questions_solved": progress["questions_solved"],
            "study_minutes": progress["study_minutes"],
            "accuracy": progress["accuracy"],
            "streak": progress["streak"],
            "sessions_completed": progress["sessions_completed"],
        },
        "weekly_activity": progress["weekly_activity"],
        "subject_accuracy": progress["subject_accuracy"],
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "prepora-api", "environment": os.getenv("APP_ENV", "development")}


@app.post("/api/auth/signup")
def signup(payload: AuthPayload) -> dict[str, Any]:
    email = normalize_email(payload.email)
    try:
        user = db.create_user(email, display_name(email, payload.name), payload.password)
    except Exception as error:
        if "UNIQUE constraint failed: users.email" in str(error):
            raise HTTPException(status_code=409, detail="An account with this email already exists.") from error
        raise
    return {"token": issue_token(user["id"]), "user": public_user(user), "dashboard": dashboard_for(user)}


@app.post("/api/auth/login")
def login(payload: AuthPayload) -> dict[str, Any]:
    email = normalize_email(payload.email)
    user = db.authenticate(email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    return {"token": issue_token(user["id"]), "user": public_user(user), "dashboard": dashboard_for(user)}


@app.get("/api/auth/me")
def me(user: dict[str, Any] = Depends(required_user)) -> dict[str, Any]:
    return {"user": public_user(user), "dashboard": dashboard_for(user)}


@app.get("/api/profile")
def profile(user: dict[str, Any] = Depends(required_user)) -> dict[str, Any]:
    return {"user": public_user(user)}


@app.patch("/api/profile")
def update_profile(payload: ProfileUpdate, user: dict[str, Any] = Depends(required_user)) -> dict[str, Any]:
    values = payload.model_dump(exclude_none=True)
    if "target_date" in values:
        values["target_date"] = values["target_date"].isoformat()
    updated = db.update_user(user["id"], values)
    return {"user": public_user(updated or user)}


@app.get("/api/exams")
def exams() -> list[dict[str, object]]:
    return [
        {"id": "neet", "name": "NEET-UG", "description": "Medical entrance preparation", "subjects": ["Physics", "Chemistry", "Biology"]},
        {"id": "cbse", "name": "CBSE Boards", "description": "Class 12 board examination", "subjects": ["Physics", "Chemistry", "Biology"]},
        {"id": "cuet", "name": "CUET-UG", "description": "Domain subject preparation", "subjects": ["Physics", "Chemistry", "Biology"]},
        {"id": "nursing", "name": "AIIMS Nursing", "description": "Nursing entrance preparation", "subjects": ["Physics", "Chemistry", "Biology"]},
    ]


@app.get("/api/content/chapters")
def content_chapters(class_level: Literal["11th", "12th", "Mixed"] = "Mixed", subject: Literal["All", "Physics", "Chemistry", "Biology"] = "All") -> dict[str, Any]:
    items = content.chapters(class_level, subject)
    return {"count": len(items), "chapters": items}


@app.get("/api/content/references")
def content_references(class_level: Literal["11th", "12th", "Mixed"] = "Mixed", subject: Literal["All", "Physics", "Chemistry", "Biology"] = "All", query: str = "") -> dict[str, Any]:
    items = content.references(class_level, subject, query)
    return {"count": len(items), "references": items, "notice": "Concise revision cards; verify important facts against approved NCERT or course material."}


@app.get("/api/content/questions")
def content_questions(class_level: Literal["11th", "12th", "Mixed"] = "Mixed", subject: Literal["Mixed", "Physics", "Chemistry", "Biology"] = "Mixed", difficulty: Literal["Easy", "Medium", "Hard", "Mixed"] = "Mixed", limit: int = 60) -> dict[str, Any]:
    items = content.question_bank(class_level, subject, difficulty)
    safe_limit = min(max(limit, 1), 500)
    return {"count": len(items), "questions": items[:safe_limit], "notice": "Chapter checks cover the full syllabus; imported PYQs should be labelled separately."}


@app.get("/api/dashboard")
def dashboard(user: dict[str, Any] | None = Depends(optional_user)) -> dict[str, object]:
    if user:
        return dashboard_for(user)
    return {
        "demo": True,
        "user": {"name": "Aarav Sharma", "target_exam": "NEET-UG", "target_date": str(date(2027, 5, 2))},
        "stats": {"questions_solved": 642, "study_minutes": 1840, "accuracy": 78, "streak": 12},
        "weekly_activity": [44, 62, 51, 78, 91, 64, 38],
        "subject_accuracy": {"Physics": 71, "Chemistry": 82, "Biology": 84},
    }


@app.post("/api/progress/events")
def progress_event(payload: ProgressEvent, user: dict[str, Any] = Depends(required_user)) -> dict[str, Any]:
    try:
        progress = db.record_progress_event(user["id"], payload.event_type, payload.value, payload.subject)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"progress": progress, "dashboard": dashboard_for(user)}


@app.post("/api/test-attempts")
def save_test_attempt(payload: TestAttemptCreate, user: dict[str, Any] = Depends(required_user)) -> dict[str, Any]:
    attempt = db.create_attempt(user["id"], payload.model_dump())
    db.record_progress_event(user["id"], "question_solved", payload.correct + payload.incorrect)
    db.record_progress_event(user["id"], "session_completed", 1)
    return {"attempt": attempt, "dashboard": dashboard_for(user)}


@app.get("/api/test-attempts")
def test_attempts(user: dict[str, Any] = Depends(required_user)) -> dict[str, Any]:
    return {"attempts": db.list_attempts(user["id"])}


@app.get("/api/study/items")
def study_items(kind: Literal["queue", "planner", "mistake"] | None = None, status: Literal["open", "completed"] | None = None, user: dict[str, Any] = Depends(required_user)) -> dict[str, Any]:
    return {"items": db.list_study_items(user["id"], kind, status)}


@app.post("/api/study/items")
def create_study_item(payload: StudyItemCreate, user: dict[str, Any] = Depends(required_user)) -> dict[str, Any]:
    values = payload.model_dump(exclude_none=True)
    if "due_date" in values:
        values["due_date"] = values["due_date"].isoformat()
    return {"item": db.create_study_item(user["id"], values)}


@app.post("/api/study/items/{item_id}/complete")
def complete_study_item(item_id: str, user: dict[str, Any] = Depends(required_user)) -> dict[str, Any]:
    item = db.complete_study_item(user["id"], item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Study item was not found.")
    db.record_progress_event(user["id"], "session_completed", 1)
    return {"item": item, "analytics": db.analytics(user["id"])}


@app.get("/api/analytics")
def analytics(user: dict[str, Any] = Depends(required_user)) -> dict[str, Any]:
    return db.analytics(user["id"])


@app.post("/api/tutor/respond")
def tutor_response(payload: TutorPayload, user: dict[str, Any] = Depends(required_user)) -> dict[str, Any]:
    query = payload.chapter or payload.prompt
    cards = content.references("Mixed", payload.subject or "All", query)
    card = cards[0] if cards else None
    lower = payload.prompt.lower()
    if payload.mode == "Quiz me":
        reply = f"Quick check: state the governing idea for {payload.chapter or 'this topic'} and write one formula or NCERT fact from memory. I will check the reasoning in your next message."
    elif payload.mode == "Revision plan":
        reply = f"15-minute plan for {payload.chapter or 'this topic'}: 4 min active recall, 6 min solve two questions, 3 min review one mistake, 2 min write the takeaway."
    elif card:
        reply = f"{card['content']} Next step: {card['note']}"
    elif "why" in lower or "explain" in lower:
        reply = "Start by naming the concept, then write the known quantities and the governing relation. Check units or conditions before substituting, and finish by explaining why the option follows."
    else:
        reply = "I can help with a formula, reaction, NCERT recall point or mistake. Include the chapter and what you tried so I can keep the explanation precise."
    return {"reply": reply, "source": card or {"label": "PrePora study method", "note": "Verify important facts against approved NCERT or course material."}}


@app.post("/api/photo/analyze")
async def analyze_photo(image: UploadFile = File(...), question_text: str = Form(default=""), user: dict[str, Any] = Depends(required_user)) -> dict[str, Any]:
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if image.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="Upload a JPG, PNG or WEBP image.")
    content_bytes = await image.read(10 * 1024 * 1024 + 1)
    if len(content_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller.")
    if question_text.strip():
        response = tutor_response(TutorPayload(prompt=question_text.strip(), mode="Step-by-step"), user)
        return {"status": "solved_with_context", "filename": image.filename, "content_type": image.content_type, "reply": response["reply"], "source": response["source"], "notice": "The typed question was grounded with the uploaded image context."}
    return {"status": "image_received", "filename": image.filename, "content_type": image.content_type, "reply": "The image is ready. Add the exact question text below so PrePora can explain it reliably until a vision provider is configured.", "notice": "OCR is intentionally not guessed in this development build."}


def session_with_expiry(user_id: str, session_id: str) -> dict[str, Any] | None:
    session = db.get_session(user_id, session_id)
    if session and session["status"] == "active" and datetime.fromisoformat(session["expires_at"]) <= datetime.now(timezone.utc):
        return db.submit_session(user_id, session_id)
    return session


@app.post("/api/tests/sessions")
def create_test_session(config: TestConfig, user: dict[str, Any] = Depends(required_user)) -> dict[str, Any]:
    # Curated seeds are intentionally only used for the broad mixed starter set.
    # Targeted class/chapter/difficulty tests must come from the filtered bank,
    # otherwise a Class 11 or Hard test could contain unrelated seed questions.
    curated = [question for question in SESSION_QUESTIONS if config.exam == "NEET-UG" and config.difficulty == "Mixed" and config.class_level == "Mixed" and (not config.chapter or config.chapter == "Full syllabus") and (config.subject == "Mixed" or question["subject"] == config.subject)]
    generated = content.question_bank(config.class_level, config.subject, config.difficulty)
    if config.chapter and config.chapter != "Full syllabus":
        generated = [question for question in generated if question["chapter"] == config.chapter or question["chapter"].endswith(f"· {config.chapter}")]
    available = curated + [question for question in generated if question["id"] not in {item["id"] for item in curated}]
    used_question_ids = db.list_used_question_ids(user["id"])
    fresh = [question for question in available if question["id"] not in used_question_ids]
    if not available:
        raise HTTPException(status_code=409, detail="No questions are available for this configuration. Choose another chapter, subject or difficulty.")
    # Fresh questions are always preferred. Once a focused chapter's finite
    # bank is exhausted, continue with a clearly labelled practice refresh so
    # a student can still request 30/60 questions. Repeats are not duplicated
    # inside the same test until the whole available pool has been cycled.
    SystemRandom().shuffle(fresh)
    selected = fresh[:config.questions]
    repeat_count = max(0, config.questions - len(selected))
    if repeat_count:
        refresh_pool = list(available)
        SystemRandom().shuffle(refresh_pool)
        for index in range(repeat_count):
            selected.append({**refresh_pool[index % len(refresh_pool)], "is_repeat": True})
    source = "NEET practice bank" if config.exam == "NEET-UG" else "CBSE chapter practice"
    questions = [{
        **question,
        "exam": config.exam,
        "source": "Practice refresh" if question.get("is_repeat") else source,
        "is_repeat": bool(question.get("is_repeat", False)),
        "id": f"{question['id']}-slot-{index + 1}",
    } for index, question in enumerate(selected)]
    session = db.create_session(user["id"], config.model_dump(), questions, config.duration_minutes)
    notice = "Fresh questions selected from the practice bank."
    if repeat_count:
        notice = f"{len(fresh)} fresh questions were available; the remaining {repeat_count} are clearly labelled practice refresh questions."
    return {"session": session, "question_count": len(questions), "notice": notice}


@app.get("/api/tests/sessions/{session_id}")
def get_test_session(session_id: str, user: dict[str, Any] = Depends(required_user)) -> dict[str, Any]:
    session = session_with_expiry(user["id"], session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Test session was not found.")
    return {"session": session}


@app.patch("/api/tests/sessions/{session_id}/answer")
def answer_test_session(session_id: str, payload: SessionAnswer, user: dict[str, Any] = Depends(required_user)) -> dict[str, Any]:
    current = session_with_expiry(user["id"], session_id)
    if not current:
        raise HTTPException(status_code=404, detail="Test session was not found.")
    if current["status"] != "active":
        raise HTTPException(status_code=409, detail="This test has already been submitted.")
    updated = db.save_session_answer(user["id"], session_id, payload.question_index, payload.option, payload.marked)
    if not updated:
        raise HTTPException(status_code=409, detail="This test is no longer accepting answers.")
    return {"session": updated}


@app.post("/api/tests/sessions/{session_id}/submit")
def submit_test_session(session_id: str, user: dict[str, Any] = Depends(required_user)) -> dict[str, Any]:
    current = db.get_session(user["id"], session_id)
    if not current:
        raise HTTPException(status_code=404, detail="Test session was not found.")
    if current["status"] == "submitted":
        return {"session": current}
    session = db.submit_session(user["id"], session_id)
    if not session:
        raise HTTPException(status_code=409, detail="This test could not be submitted.")
    db.create_attempt(user["id"], {"test_id": session_id, "config": session["config"], "score": session["score"], "correct": session["correct"], "incorrect": session["incorrect"], "unanswered": session["unanswered"], "duration_seconds": 0})
    for question_index, question in enumerate(session["questions"]):
        answer = session["answers"].get(str(question_index))
        if answer is None or answer != question.get("answer"):
            db.create_study_item(user["id"], {"kind": "mistake", "subject": question["subject"], "class_level": session["config"].get("class_level", "Mixed"), "chapter": question["chapter"], "title": f"Retry: {question['chapter']}", "reason": "Unanswered in a timed test; review the anchor before retrying." if answer is None else "Incorrect answer in a timed test; review the anchor before retrying.", "priority": "High", "duration_minutes": 15, "details": {"questionText": question.get("text", ""), "options": question.get("options", []), "selectedAnswer": answer, "correctAnswer": question.get("answer", 0), "explanation": question.get("explanation", "Review the concept anchor and compare your reasoning with the correct option.")}})
            db.create_study_item(user["id"], {"kind": "queue", "subject": question["subject"], "class_level": session["config"].get("class_level", "Mixed"), "chapter": question["chapter"], "title": f"Revise {question['chapter']}", "reason": "Generated from your latest incorrect answer.", "priority": "High", "duration_minutes": 15})
    db.record_progress_event(user["id"], "question_solved", session["correct"] + session["incorrect"])
    db.record_progress_event(user["id"], "session_completed", 1)
    return {"session": session, "dashboard": dashboard_for(user)}


@app.post("/api/tests/generate")
def generate_test(config: TestConfig) -> dict[str, object]:
    available = [q for q in DEMO_QUESTIONS if config.subject == "Mixed" or q["subject"] == config.subject]
    available.extend(content.question_bank("Mixed", config.subject, config.difficulty)[: max(config.questions, 1)])
    if not available:
        raise HTTPException(status_code=422, detail="No suitable questions are available for this configuration.")
    return {
        "id": f"demo-{datetime.utcnow().timestamp():.0f}",
        "status": "ready",
        "config": config.model_dump(),
        "question_count": config.questions,
        "questions": available,
        "message": "This development test uses clearly labelled demo questions. Import approved content to expand the bank.",
    }
