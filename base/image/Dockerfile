FROM python:3.6
COPY ./requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt
COPY ./*.py /app/
ENTRYPOINT ["python"]
CMD ["/app/app.py"]
