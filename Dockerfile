# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the application files into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir python-docx nltk pyspellchecker

# Download necessary NLTK data (punkt tokenizer)
RUN python -m nltk.downloader punkt

# Command to run the script
CMD ["python", "json_to_cv.py"]