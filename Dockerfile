FROM python:3.13.5

WORKDIR /app

ENV FLASK_BACKEND=app.py
ENV BACKEND_RUN_HOST=0.0.0.0

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . . 

EXPOSE 5000

CMD ["flask", "run", "--debug"]