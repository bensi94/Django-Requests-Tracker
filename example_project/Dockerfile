FROM python:3.11

EXPOSE 8000

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /app

CMD ["uvicorn", "example_project.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
