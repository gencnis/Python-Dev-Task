"""
app.py

This script is a Flask application that implements a web interface for filtering and displaying data from a SQLite database. 
It also includes functionality for consuming data from RabbitMQ and storing it in the database.

Dependencies:
- Flask: Python web framework
- SQLAlchemy: Python SQL toolkit and Object-Relational Mapping (ORM) library
- csv: Python module for reading CSV files
- json: Python module for working with JSON data
- pika: Python library for RabbitMQ integration

The script defines a Flask application with routes for rendering HTML templates, filtering data based on user input, and 
performing database operations. It uses SQLAlchemy for database operations and integrates with a SQLite database specified in the configuration.

The 'Person' class represents the database table schema using SQLAlchemy ORM. The class includes a __repr__ method for better 
representation of Person objects.

The script also includes helper functions for reading data from a CSV file, cleaning the database, and consuming data from RabbitMQ.

@Author: Nisanur Genc
"""


import time
from flask import Flask, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
import csv
import json
import pika

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    forename = db.Column(db.String(100))
    date_of_birth = db.Column(db.String(100))
    entity_id = db.Column(db.String(100))
    nationalities = db.Column(db.String)
    name = db.Column(db.String(100))
    image = db.Column(db.String(1000))

    def __repr__(self):
        return f"Person(id={self.id}, forename={self.forename}, date_of_birth={self.date_of_birth}, " \
               f"entity_id={self.entity_id}, nationalities={self.nationalities}, name={self.name}, image={self.image})"


@app.route('/')
def index():
    """Render the index.html template for the home page."""
    return render_template('index.html')


@app.route('/filter', methods=['POST'])
def filter_data():
    """Filter the data based on the provided criteria and return the results."""
    forename = request.form.get('name')
    date_of_birth = request.form.get('date_of_birth')
    entity_id = request.form.get('entity_id')
    nationalities = request.form.get('nationalities')
    name = request.form.get('lastname')
    image = request.form.get('image')

    # Filter the data based on the provided criteria
    filtered_data = Person.query
    if forename:
        filtered_data = filtered_data.filter(Person.forename.ilike(f"%{forename}%"))
    if date_of_birth:
        filtered_data = filtered_data.filter(Person.date_of_birth.ilike(f"%{date_of_birth}%"))
    if entity_id:
        filtered_data = filtered_data.filter(Person.entity_id.ilike(f"%{entity_id}%"))
    if nationalities:
        filtered_data = filtered_data.filter(Person.nationalities.ilike(f"%{nationalities}%"))
    if name:
        filtered_data = filtered_data.filter(Person.name.ilike(f"%{name}%"))
    if image:
        filtered_data = filtered_data.filter(Person.image.ilike(f"%{image}%"))

    results = filtered_data.all()

    return render_template('results.html', results=results)



def clean_database():
    """Clean the whole database by deleting all records."""
    db.session.query(Person).delete()
    db.session.commit()
    print("Database cleaned")


def consume_data():
    """Consume data from RabbitMQ and store it in the database."""
    print("Sleeping")
    time.sleep(25)
    print("Done sleeping")
    connection_parameters = pika.ConnectionParameters("container_c")
    connection = pika.BlockingConnection(connection_parameters)
    channel = connection.channel()
    channel.queue_declare(queue='interpol_data')

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

            # Check if the required keys are present in the data
            if 'entity_id' not in data:
                print("Error: 'entity_id' key not found in the consumed message")
                return

            # Extract the entity ID from the incoming data
            entity_id = data['entity_id']

            # Check if the entity ID already exists in the database
            existing_person = Person.query.filter_by(entity_id=entity_id).first()

            if existing_person:
                # Delete the existing person record
                Person.query.filter_by(entity_id=entity_id).delete()
                db.session.commit()
                print(f"Old data deleted for entity ID: {entity_id}")

            # Store the data in the database
            image_href = data.get('image', {}).get('href')
            nationalities_json = json.dumps(data.get('nationalities', []))
            person = Person(
                forename=data.get('name'),
                date_of_birth=data.get('date_of_birth'),
                entity_id=data['entity_id'],
                nationalities=nationalities_json,
                name=data.get('lastname'),
                image=image_href
            )
            db.session.add(person)
            db.session.commit()

            print(f"Data stored for entity ID: {entity_id}")

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON message: {str(e)}")
        except KeyError as e:
            print(f"Error accessing key in JSON message: {str(e)}")


    # Set up the callback function to consume messages from the 'letterbox' queue
    channel.basic_consume(queue='interpol_data', auto_ack=True, on_message_callback=callback)

    # Start consuming messages from the RabbitMQ queue
    print("Starting consuming")
    channel.start_consuming()



def main():
    with app.app_context():
        
        # Create the database tables if they don't exist
        db.create_all()
        print("---- Database created. ----")


        # Consume data from RabbitMQ
        consume_data()
        print("---- Data consumed. ----")

        # Run the Flask application in debug mode
        app.run(debug=True, threaded=True, host='0.0.0.0')

        

if __name__ == '__main__':
    main()