FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Poetry
RUN pip install --no-cache-dir poetry

# Set the working directory
WORKDIR /app

# Copy only the necessary files for installing dependencies
COPY pyproject.toml poetry.lock /app/

# Install dependencies
RUN poetry install --no-root --no-dev

# Copy the rest of the application code
COPY joypaper /app/joypaper

# Expose the port that the app runs on
EXPOSE 8000

# Run the FastAPI application
CMD ["poetry", "run", \
    "fastapi", "run", "joypaper/api.py", \
    "--host", "0.0.0.0", "--port", "8000"]
