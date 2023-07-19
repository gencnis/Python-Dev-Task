from RabbitMQConsumer import RabbitMQConsumer
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)
# Used PostgreSQL instead of SQLite

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:bxhrYukUTq/6SJGSKvZzH/gCFyn/d5iaHraBuLBvznI=@postgres:5432/my_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
my_db = SQLAlchemy(app)

class Person(my_db.Model):
    id = my_db.Column(my_db.Integer, primary_key=True)
    forename = my_db.Column(my_db.String(100))
    date_of_birth = my_db.Column(my_db.String(100))
    entity_id = my_db.Column(my_db.String(100))
    nationalities = my_db.Column(my_db.String)
    name = my_db.Column(my_db.String(100))
    image = my_db.Column(my_db.String(1000))

    def __repr__(self):
        return f"Person(id={self.id}, forename={self.forename}, date_of_birth={self.date_of_birth}, " \
               f"entity_id={self.entity_id}, nationalities={self.nationalities}, name={self.name}, image={self.image})"


def store_data_to_my_db(data):
    """Process and store the data in the PostgreSQL database."""
    try:
        # Print the received message body to check the actual data
        print("Received Message Body:", data)

        # Check if the required key 'entity_id' is present in the data
        if 'entity_id' not in data:
            print("Error: 'entity_id' key not found in the consumed message")
            return

        # Handle missing or None values and replace them with "Unknown"
        for key in ['name', 'lastname', 'date_of_birth']:
            if key in data and data[key] is not None:
                continue
            data[key] = "Unknown"

        # Handle the 'nationalities' field separately
        nationalities = data.get('nationalities')
        if nationalities is None:
            # If 'nationalities' is None, initialize it as a list with "Unknown"
            data['nationalities'] = ["Unknown"]

        # Extract the entity ID from the incoming data
        entity_id = data['entity_id']

        # Check if the entity ID already exists in the database
        existing_person = Person.query.filter_by(entity_id=entity_id).first()

        if existing_person:
            # Delete the existing person record
            Person.query.filter_by(entity_id=entity_id).delete()
            my_db.session.commit()
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
        my_db.session.add(person)
        my_db.session.commit()
        print(f"Data stored for entity ID: {entity_id}")

    except Exception as e:
        my_db.session.rollback()  # Rollback the transaction if an error occurs
        print(f"Error storing data to the database: {str(e)}")
        # Print the data to investigate any potential issues
        print("Data that failed to be stored:", data)

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON message in Database: {str(e)}")
        # If JSON decoding fails, print the received body to investigate the issue
        print("Received Message Body (Failed to Decode) in Database:", data.decode())
    except KeyError as e:
        print(f"Error accessing key in JSON message in Database: {str(e)}")


def clean_database():
    """Clean the whole database by deleting all records."""
    my_db.session.query(Person).delete()
    my_db.session.commit()
    print("Database cleaned")

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


def main():
    with app.app_context():
        # Create the database tables if they don't exist
        my_db.create_all()
        print("---- Database created. ----")

        # Create an instance of RabbitMQConsumer
        rabbitmq_consumer = RabbitMQConsumer(hostname="container_c", port=5672, queue_name="interpol_data", max_queue_length = 50000)

        # Override the get_data() method to handle the data in the RabbitMQConsumer
        def store_data(data):
            store_data_to_my_db(data)

        # Assign the get_data method in the RabbitMQConsumer instance to the store_data function
        rabbitmq_consumer.get_data = store_data

        # Consume data from RabbitMQ and process it using the overridden get_data() method
        rabbitmq_consumer.consume_data()
        print("---- Data consumed and stored in the PostgreSQL database. ----")

        # Run the Flask application in debug mode
        app.run(debug=True, threaded=True, host='0.0.0.0')

if __name__ == '__main__':
    main()