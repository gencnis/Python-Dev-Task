"""
RabbitMQConnection.py

This script defines the RabbitMQConnection class, which is responsible for establishing a connection to RabbitMQ, publishing data to the queue,
and handling reconnections in case of connection failures.

Dependencies:
- pika: Python library for RabbitMQ integration
- time: Python module for adding delays between connection retries
- queue.Queue: Python module for implementing a thread-safe queue for queuing data during connection failures

@Author: Nisanur Genc

"""

import queue
import pika
import time

class RabbitMQConnection:
    def __init__(self, hostname, port, queue_name):
        """
        Constructor for the RabbitMQConnection class.

        Parameters:
        - hostname (str): The hostname or IP address of the RabbitMQ server.
        - port (int): The port number for the RabbitMQ server (default is usually 5672).
        - queue_name (str): The name of the queue to which data will be published.
        """
        self.hostname = hostname
        self.port = port
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.connected = False
        self.data_queue = queue.Queue()

        # Sleep for a few seconds to allow other components to initialize before connecting to RabbitMQ
        print("Sleeping for 5 seconds to allow other components to initialize...")
        time.sleep(5)
        print("Done sleeping")

        # Establish the RabbitMQ connection
        self.connect()

    def connect(self):
        """
        Connect to RabbitMQ and attempt retries in case of connection failure.

        This method is called by the constructor to establish the connection to RabbitMQ.
        If the connection fails, it will attempt to reconnect with a maximum number of retries.
        """
        max_retries = 5
        retry_interval = 5  # Retry every 5 seconds
        retry_count = 0

        while not self.is_connected() and retry_count < max_retries:
            try:
                # Establish the RabbitMQ connection
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.hostname, port=self.port)
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue_name)
                self.connected = True
                print("Connection to RabbitMQ established.")
            except pika.exceptions.AMQPConnectionError as e:
                print("Failed to connect to RabbitMQ:", e)
                self.connected = False
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Retrying in {retry_interval} seconds...")
                    time.sleep(retry_interval)

        if not self.is_connected():
            print("Failed to establish connection after retries.")
        else:
            # Connection successful, publish any queued data
            while not self.data_queue.empty():
                queued_data = self.data_queue.get()
                self.channel.basic_publish(exchange='',
                                           routing_key=self.queue_name,
                                           body=str(queued_data))
                print("Queued data published to RabbitMQ:", queued_data)

    def is_connected(self):
        """
        Check if the connection to RabbitMQ is established.

        Returns:
        - bool: True if connected, False otherwise.
        """
        return self.connected

    def check_connection(self):
        """
        Check the connection status and attempt reconnection if necessary.

        This method is used to verify the connection status and handle reconnection attempts in case of connection loss.
        """
        if not self.is_connected():
            print("Connection lost. Attempting to reconnect...")
            self.connect()

    def publish_data(self, data):
        """
        Publish data to RabbitMQ.

        Parameters:
        - data (str): The data to be published to the RabbitMQ queue in string format.
        """
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
        """
        Close the RabbitMQ connection if it is open.

        This method is called when the object is deleted or when the connection needs to be closed explicitly.
        """
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            self.connected = False
            print("RabbitMQ connection closed.")

    def __del__(self):
        """
        Destructor for the RabbitMQConnection class.

        This method is called when the object is deleted, ensuring that the RabbitMQ connection is closed properly.
        """
        self.close_connection()
