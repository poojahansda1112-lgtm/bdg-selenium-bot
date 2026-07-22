 FROM mcr.microsoft.com/playwright/python:v1.45.0-focal

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
