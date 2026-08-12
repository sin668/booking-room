FROM docker.m.daocloud.io/python:3.12-slim-bookworm
ENV TZ Asia/Shanghai
WORKDIR /home
COPY ./app /home/app
COPY ./.env ./pyproject.toml /home/
RUN pip install -e ".[dev]"
ENTRYPOINT []
CMD ["uvicorn","app.main:app","--host 0.0.0.0","--port 8000","--workers 4"]
