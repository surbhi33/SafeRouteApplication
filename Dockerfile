FROM python:3.8
COPY requirements.txt requirements.txt
COPY . .
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "project/app.py"]
