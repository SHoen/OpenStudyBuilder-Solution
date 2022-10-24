FROM python:3.7
RUN pip install pipenv
COPY Pipfile /tmp
RUN cd /tmp && pipenv install
COPY . /tmp/cmdr
WORKDIR /tmp/cmdr
RUN adduser appuser --disabled-password && chown -R appuser /tmp/cmdr
USER appuser
EXPOSE 8000
HEALTHCHECK CMD curl --fail http://localhost:8000/openapi.json || exit 1
CMD ["uvicorn", "clinical_mdr_api.main:app", "--host", "0.0.0.0", "--port", "8000"]