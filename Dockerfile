FROM python:3.9

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Optional: only download punkt if you need it
RUN python -m nltk.downloader punkt

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8888", "--reload"]
