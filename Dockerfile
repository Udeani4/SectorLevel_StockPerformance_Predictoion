# FROM python:3.12-slim
# WORKDIR /app
# COPY . /app

# RUN apt update -y && apt install awscli -y

# RUN apt-get update && pip install -r requirements.txt
# CMD ["python3","app.py"]

FROM python:3.12-slim
WORKDIR /app

RUN apt update -y && apt install -y awscli

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /app

CMD ["python3", "ngx_app.py"]