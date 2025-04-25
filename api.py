from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import json
import uuid
import os
from json_to_cv import create_cv_for_api
from ats_analysis import analyze_cv, analyze_cv_api

app = FastAPI()
templates = Jinja2Templates(directory="html")

@app.get("/", response_class=HTMLResponse)
async def form_page(request: Request):
    return templates.TemplateResponse("page.html", {"request": request, "json_output": None})

@app.post("/", response_class=HTMLResponse)
async def handle_upload(
    request: Request,
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

        # Save DOCX and return it
        output_path = f"/tmp/cv_{uuid.uuid4()}.docx"
        create_cv_for_api(json_data, output_path)
        return FileResponse(output_path, filename="cv.docx", media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    except Exception as e:
        error = f"Invalid JSON: {e}"
        return templates.TemplateResponse("page.html", {
            "request": request,
            "json_output": None,
            "error": error
        })


@app.post("/ats-check", response_class=HTMLResponse)
async def ats_check(
    request: Request,
    cv_file: UploadFile = File(...)
):
    try:
        contents = await cv_file.read()
        original_filename = cv_file.filename or ""
        temp_path = f"/tmp/{uuid.uuid4()}.docx"
        with open(temp_path, "wb") as f:
            f.write(contents)

        # You can extract the name from the file or parse inside the function
        # But if it's required to compare filename to name inside CV:
        ats_result = analyze_cv_api(temp_path, original_filename)

        return templates.TemplateResponse("page.html", {
            "request": request,
            "json_output": None,
            "ats_result": ats_result
        })
    except Exception as e:
        return templates.TemplateResponse("page.html", {
            "request": request,
            "json_output": None,
            "ats_result": None,
            "error": f"Failed to analyze CV: {e}"
        })