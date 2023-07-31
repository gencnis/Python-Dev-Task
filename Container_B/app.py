"""
app.py

This script defines a Flask web application with a PostgreSQL database. It includes functionalities to consume data from a RabbitMQ queue,
store it in the database, and provide endpoints for retrieving and filtering the data. The application also serves static files and images.

@Author: Nisanur Genc

"""



import json
from RabbitMQConsumer import RabbitMQConsumer
from db_registrar import DBRegistrar
from readFile import read_country_data
from flask import Flask, render_template, request, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
import threading


app = Flask(__name__, static_url_path='/static', static_folder='static')
# Used PostgreSQL instead of SQLite

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:bxhrYukUTq/6SJGSKvZzH/gCFyn/d5iaHraBuLBvznI=@postgres:5432/my_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
my_db = SQLAlchemy(app)
COUNTRY_NAMES = read_country_data("countries.txt")


class Person(my_db.Model):
    """Model class representing a Person entity in the database."""
    forename = my_db.Column(my_db.String(100))
    date_of_birth = my_db.Column(my_db.String(100))
    entity_id = my_db.Column(my_db.String(100), primary_key=True)
    nationalities = my_db.Column(my_db.String(1000))
    name = my_db.Column(my_db.String(100))
    image = my_db.Column(my_db.String(1000))

    def __repr__(self):
            return f"Person(forename={self.forename}, date_of_birth={self.date_of_birth}, " \
                f"entity_id={self.entity_id}, nationalities={self.nationalities}, " \
                f"name={self.name}, image={self.image}"



def clean_database():
    """Clean the whole database by deleting all records."""
    my_db.session.query(Person).delete()
    my_db.session.commit()
    print("Database cleaned")


@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve images from the 'image_data' directory."""
    return send_from_directory('./image_data', filename)


@app.route('/live_data', methods=['POST'])
def live_data():
    """Retrieve live data from the database and return it in JSON format."""
    total_people = Person.query.count()
    people = Person.query.all()

    # Format the nationalities field from JSON string to a list of country names
    for person in people:
        nationalities_list = json.loads(person.nationalities)
        person.nationalities = [COUNTRY_NAMES.get(country_code, country_code) for country_code in nationalities_list]

    # Convert the SQLAlchemy objects to dictionaries for JSON serialization
    data = [person.__dict__ for person in people]
    
    # Remove any unnecessary keys (e.g., '_sa_instance_state') from the dictionary
    for person_data in data:
        person_data.pop('_sa_instance_state', None)

    # Return the live data in JSON format
    return jsonify(total_people=total_people, data=data)


@app.route('/')
def index():
    """Render the index.html template for the home page."""
    return render_template('index.html')


@app.route('/filter', methods=['POST'])
def filter_data():
    """Filter the data based on the provided criteria and return the filtered results in JSON format."""
    forename = request.form.get('name')
    date_of_birth = request.form.get('date_of_birth')
    entity_id = request.form.get('entity_id')
    nationalities = request.form.get('nationalities')
    name = request.form.get('forename')
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
        filtered_data = filtered_data.filter(Person.image == image)

    results = filtered_data.all()

    # Format the nationalities field from JSON string to list of country names
    for person in results:
        nationalities_list = json.loads(person.nationalities) 
        person.nationalities = [COUNTRY_NAMES.get(country_code, country_code) for country_code in nationalities_list]

    # Convert the SQLAlchemy objects to dictionaries for JSON serialization
    data = [person.__dict__ for person in results]

    # Remove any unnecessary keys (e.g., '_sa_instance_state') from the dictionary
    for person_data in data:
        person_data.pop('_sa_instance_state', None)

    # Return the filtered results in JSON format
    return jsonify(data=data)



def start_rabbitmq_consumer():
    """Start the RabbitMQConsumer in a separate thread."""
    db_registrar = DBRegistrar(Person, my_db)  # Pass the Person model class and the database instance
    rabbitmq_consumer = RabbitMQConsumer(hostname="container_c", port=5672, queue_name="interpol_data", db_registrar=db_registrar)
    rabbitmq_consumer.consume_data()


def main():
    """Main function to start the Flask application, create database tables, and consume data from RabbitMQ."""
    # Create the database tables if they don't exist
    my_db.create_all()
    print("---- Database created. ----")
    # Start the RabbitMQ consumer in a separate thread
    consumer_thread = threading.Thread(target=start_rabbitmq_consumer)
    consumer_thread.start()

    # # Start the auto-refresh data thread
    # refresh_thread = threading.Thread(target=refresh_data)
    # refresh_thread.start()

    # Run the Flask application in debug mode
    app.run(debug=True, threaded=True, host='0.0.0.0')
    print("---- Data consumed and stored in the PostgreSQL database. ----")

if __name__ == '__main__':
    main()