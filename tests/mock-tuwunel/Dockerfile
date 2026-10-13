# syntax=docker/dockerfile:1
#
# mock-tuwunel - tiny, dependency-free Matrix homeserver mock.
# Built from the tests/mock-tuwunel context and activated only under the
# `test` compose profile. Uses the Python standard library exclusively so
# the image stays small and the mock has zero external dependencies.

FROM python:3.12-slim

WORKDIR /app

COPY mock.py .

EXPOSE 8008

CMD ["python3", "mock.py"]
