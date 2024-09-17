FROM python:3.12-slim
LABEL authors="ElDavo"
# install requirements
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
# copy the rest of the files
COPY . /app
# run the app
CMD ["python", "app.py"]