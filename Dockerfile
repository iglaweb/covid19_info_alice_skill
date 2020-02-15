FROM python:3.6

WORKDIR /app
COPY . /app

EXPOSE 5000

RUN pip install -r requirements.txt

# We need to define the command to launch when we are going to run the image.
# We use the keyword 'CMD' to do that.
# The following command will execute "python ./main.py".
CMD [ "python", "./main.py" ]
