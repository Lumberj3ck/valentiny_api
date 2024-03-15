FROM tiangolo/uvicorn-gunicorn:python3.11-slim


# COPY requirements.txt .
# RUN pip install -r requirements.txt
COPY ./requirements.txt /code/requirements.txt
# RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip install -r /code/requirements.txt

COPY ./app /app/app

