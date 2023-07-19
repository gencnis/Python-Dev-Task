import json
import pika
import time

class RabbitMQConsumer:
    def __init__(self, hostname, port, queue_name):
        """
        Constructor for the RabbitMQConsumer class.

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

    def consume_data(self, data_callback):
        """
        Consume data from RabbitMQ and store it in the PostgreSQL database.

        This method will handle reconnections and consume data from RabbitMQ using the callback function.

        Parameters:
        - data_callback (function): The callback function to be executed with the consumed data.
        """
    
        print("Sleeping for 5 seconds to allow other components to initialize...")
        time.sleep(5)
        print("Done sleeping")
        connection_parameters = pika.ConnectionParameters(self.hostname, self.port)
        connection = pika.BlockingConnection(connection_parameters)
        channel = connection.channel()
        channel.queue_declare(queue=self.queue_name)


        def callback(ch, method, properties, body):
            try:
                # Attempt to decode the message body as JSON
                try:
                    data = json.loads(body.decode())
                except json.JSONDecodeError:
                    # If JSON decoding fails, try fixing the format by replacing single quotes with double quotes
                    body_str = body.decode()
                    fixed_body_str = body_str.replace("'", '"')
                    data = json.loads(fixed_body_str)

                # Pass the data to the data_callback for processing
                data_callback(data)

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON message in Consumer: {str(e)}")
                # If JSON decoding fails, print the received body to investigate the issue
                print("Received Message Body (Failed to Decode) in Consumer:", body.decode())
            except KeyError as e:
                print(f"Error accessing key in JSON message in Consumer: {str(e)}")


        # Set up the callback function to consume messages from the 'interpol_data' queue
        channel.basic_consume(queue=self.queue_name, auto_ack=True, on_message_callback=callback)

        # Start consuming messages from the RabbitMQ queue
        print("Starting consuming")
        channel.start_consuming()


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
        Destructor for the RabbitMQConsumer class.

        This method is called when the object is deleted, ensuring that the RabbitMQ connection is closed properly.
        """
        self.close_connection()
