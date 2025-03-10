#!/bin/bash

# Default values
JSON_FILE="cv_data.json"
OUTPUT_FILE="output_cv.docx"

# Help message
usage() {
    echo "Usage: $0 [-i input_json] [-o output_docx]"
    exit 1
}

# Parse command-line arguments
while getopts "i:o:h" opt; do
    case "$opt" in
        i) JSON_FILE="$OPTARG" ;;
        o) OUTPUT_FILE="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

# Ensure the output file's directory exists (to avoid issues with missing directories)
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Run the Python script inside the container using Docker Compose V2
docker compose run --rm cv_generator \
    -v "$(pwd)/$JSON_FILE:/app/$JSON_FILE" \
    -v "$(pwd)/$(dirname "$OUTPUT_FILE"):/app/output" \
    python json_to_cv.py

# Notify user
echo "CV generated: $OUTPUT_FILE"
