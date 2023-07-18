import pika
import time
from queue import Queue

class RabbitMQConnection:
    def __init__(self, hostname, port, queue_name):
        self.hostname = hostname
        self.port = port
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.connected = False
        self.data_queue = Queue()

        # Call the connect() method to establish the RabbitMQ connection
        self.connect()
        
    def connect(self):
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.hostname, port=self.port))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name)
            self.connected = True
            print("Connection to RabbitMQ established.")
        except pika.exceptions.AMQPConnectionError as e:
            print("Failed to connect to RabbitMQ:", e)
            self.connected = False

    def is_connected(self):
        return self.connected

    def check_connection(self):
        if not self.is_connected():
            print("Connection lost. Attempting to reconnect...")
            self.connect()

    def publish_data(self, data):
        try:
            if not self.is_connected():
                print("RabbitMQ not connected. Queueing data...")
                self.data_queue.put(data)
                return

            self.check_connection()

            # Wait until the connection is reestablished
            while not self.is_connected():
                time.sleep(1)
                self.check_connection()

            # Publish the queued data first
            while not self.data_queue.empty():
                queued_data = self.data_queue.get()
                self.channel.basic_publish(exchange='',
                                           routing_key=self.queue_name,
                                           body=str(queued_data))
                print("Queued data published to RabbitMQ:", queued_data)

            # Now publish the current data
            self.channel.basic_publish(exchange='',
                                       routing_key=self.queue_name,
                                       body=str(data))
            print("Data published to RabbitMQ:", data)
        except pika.exceptions.AMQPChannelError as e:
            print("Failed to publish data. Channel error:", e)
        except pika.exceptions.AMQPConnectionError as e:
            print("Failed to publish data. Connection error:", e)
        except Exception as e:
            print("An error occurred while publishing data:", e)

    def close_connection(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            self.connected = False
            print("RabbitMQ connection closed.")

    def __del__(self):
        self.close_connection()
