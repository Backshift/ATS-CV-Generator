from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import json
import uuid
import os
from json_to_cv import create_cv_for_api
from ats_analysis import analyze_cv, analyze_cv_api
from docx import Document
from io import BytesIO

app = FastAPI()
templates = Jinja2Templates(directory="html")

def delete_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Error deleting file {path}: {e}")

@app.get("/", response_class=HTMLResponse)
async def form_page(request: Request):
    return templates.TemplateResponse("page.html", {"request": request, "json_output": None})

@app.post("/", response_class=HTMLResponse)
async def handle_upload(
    request: Request,
    background_tasks: BackgroundTasks,
    json_file: UploadFile = File(None),
    json_text: str = Form("")
):
    json_data = None
    error = None

    try:
        if json_file and json_file.filename:
            content = await json_file.read()
            json_data = json.loads(content)
        elif json_text.strip():
            json_data = json.loads(json_text)
        else:
            error = "No JSON provided"
            return templates.TemplateResponse("page.html", {
                "request": request,
                "json_output": None,
                "error": error
            })

        output_path = f"/tmp/cv_{uuid.uuid4()}.docx"
        create_cv_for_api(json_data, output_path)

        # Schedule background deletion AFTER response is sent
        background_tasks.add_task(delete_file, output_path)

        return FileResponse(
            path=output_path,
            filename="cv.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        error = f"Invalid JSON: {e}"
        return templates.TemplateResponse("page.html", {
            "request": request,
            "json_output": None,
            "error": error
        })

MAX_DOCX_SIZE_MB = 12

@app.post("/ats-check", response_class=HTMLResponse)
async def ats_check(
    request: Request,
    cv_file: UploadFile = File(...)
):
    try:
        original_filename = cv_file.filename or ""
        
        # Extension Check
        if not original_filename.lower().endswith('.docx'):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .docx file.")

        # Content Type Check
        if cv_file.content_type != "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            raise HTTPException(status_code=400, detail="Invalid content type. Only DOCX files are allowed.")

        contents = await cv_file.read()

        # File Size Check
        if len(contents) > MAX_DOCX_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Max allowed size is 5MB.")

        # Validate DOCX structure
        try:
            doc = Document(BytesIO(contents))  # Try opening it directly
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Uploaded file is not a valid DOCX: {e}")

        # Save to temp location (you still need the file path for downstream use)
        temp_path = f"/tmp/{uuid.uuid4()}.docx"
        with open(temp_path, "wb") as f:
            f.write(contents)

        ats_result = analyze_cv_api(temp_path, original_filename)

        return templates.TemplateResponse("page.html", {
            "request": request,
            "json_output": None,
            "ats_result": ats_result
        })

    except HTTPException as he:
        # Catch validation errors
        return templates.TemplateResponse("page.html", {
            "request": request,
            "json_output": None,
            "ats_result": None,
            "error": he.detail
        })

    except Exception as e:
        # Catch unexpected errors
        return templates.TemplateResponse("page.html", {
            "request": request,
            "json_output": None,
            "ats_result": None,
            "error": f"Failed to analyze CV: {e}"
        })
    finally:
        # Clean up temp file if it was created
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/download-json")
async def download_example_json():
    example_data = {
        "name": "John Doe",
        "contact": "Somewhere, Earth",
        "phone": "+00-1234 567 890",
        "email": "johndoe@example.com",
        "location": "Somewhere, Earth",
        "job_title": "Software Engineer",
        "summary": "Experienced software engineer with a passion for building scalable applications, optimizing infrastructure, and enhancing user experiences. Skilled in full-stack development, security, and automation.",
        "personal_info": {},
        "strengths_and_expertise": [],
        "experience": [
            {
                "title": "Software Engineer",
                "company": "Tech Solutions Inc.",
                "dates": "Jan 2022 - Present",
                "description": {
                    "intro": "Developed and maintained web applications, optimized performance, and enhanced security.",
                    "details": [
                        "Designed and implemented scalable web applications.",
                        "Managed cloud infrastructure and security measures.",
                        "Collaborated with teams to improve UI/UX design.",
                        "Developed automation scripts for deployment and monitoring."
                    ]
                }
            },
            {
                "title": "Full Stack Developer",
                "company": "Innovate Tech",
                "dates": "Aug 2020 - Dec 2021",
                "description": {
                    "intro": "Worked on developing web applications using modern JavaScript frameworks and backend technologies.",
                    "details": [
                        "Built and maintained web applications using React and Node.js.",
                        "Optimized database queries for better performance.",
                        "Implemented CI/CD pipelines for automated deployment.",
                        "Conducted security audits and implemented fixes."
                    ]
                }
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "institution": "Global University",
                "year": "2018"
            }
        ],
        "skills": [
            {
                "category": "Frontend Development",
                "items": [
                    "HTML & CSS",
                    "JavaScript & TypeScript",
                    "React & Vue.js",
                    "Responsive Design",
                    "UI/UX Design"
                ]
            },
            {
                "category": "Backend Development",
                "items": [
                    "Node.js & Express",
                    "Python & Django",
                    "SQL & NoSQL Databases",
                    "REST & GraphQL APIs",
                    "Authentication & Security"
                ]
            },
            {
                "category": "DevOps & Cloud",
                "items": [
                    "Docker & Kubernetes",
                    "AWS & Azure",
                    "CI/CD Pipelines",
                    "Linux Server Administration",
                    "Monitoring & Logging"
                ]
            },
            {
                "category": "Soft Skills",
                "items": [
                    "Problem Solving",
                    "Team Collaboration",
                    "Communication",
                    "Leadership",
                    "Adaptability"
                ]
            }
        ]
    }

    # Save JSON to a temporary file
    temp_filename = f"/tmp/example_{uuid.uuid4()}.json"
    with open(temp_filename, "w") as f:
        json.dump(example_data, f, indent=4)

    # Return the file
    return FileResponse(
        temp_filename,
        filename="example_cv.json",
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=example_cv.json"}
    )