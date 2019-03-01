#FROM bucket.canfar.net/cadc/base-caom2-proxy
FROM base-proxy
COPY ./requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt
COPY . /app
ENTRYPOINT ["python"]
CMD ["app.py"]
