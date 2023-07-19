# Use a Python base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the project code to the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Define environment variables for RabbitMQ
ENV RABBITMQ_HOST rabbitmq
ENV RABBITMQ_PORT 5672
ENV QUEUE_NAME interpol_data

# Run the Python script directly without waiting for RabbitMQ
CMD ["python", "ManageData.py"]
