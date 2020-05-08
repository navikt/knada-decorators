FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

RUN pip install --upgrade pip

COPY requirements.txt /app/.
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py /app/main.py
