# db_registrar.py
import base64
import json
import requests

class DBRegistrar:
    def __init__(self, person_model, db):
        self.person_model = person_model
        self.db = db

        
    def store_data_to_my_db(self, data):
        """Process and store the data in the PostgreSQL database."""
        try:
            # Print the received message body to check the actual data
            print("Received Message Body:", data)

            # Check if the required key 'entity_id' is present in the data
            if 'entity_id' not in data:
                print("Error: 'entity_id' key not found in the consumed message")
                return

            # Handle missing or None values and replace them with "Unknown"
            for key in ['name', 'forename', 'date_of_birth']:
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
            existing_person = self.person_model.query.filter_by(entity_id=entity_id).first()

            if existing_person:
                # Delete the existing person record
                self.person_model.query.filter_by(entity_id=entity_id).delete()
                self.db.session.commit()
                print(f"Old data deleted for entity ID: {entity_id}")

            # Store the data in the database
            image_href = data.get('image', {}).get('href')
            image_data = None


            if image_href:
                # Fetch the image from the URL
                image_response = requests.get(image_href)
                print("Image requested.")
                if image_response.ok:
                    # Get the binary image content
                    image_content = image_response.content

                    # Encode the image bytes as base64 before storing as bytea
                    image_data = base64.b64encode(image_content)

                else:
                    image_data = b"Unknown"


            nationalities_json = json.dumps(data.get('nationalities', []))

            person = self.person_model(
                forename=data.get('name'),
                date_of_birth=data.get('date_of_birth'),
                entity_id=data['entity_id'],
                nationalities=nationalities_json,
                name=data.get('forename'),
                image=image_data
            )

            self.db.session.add(person)
            self.db.session.commit()
            print(f"Data stored for entity ID: {entity_id}")

        except Exception as e:
            self.db.session.rollback()  # Rollback the transaction if an error occurs
            print(f"Error storing data to the database: {str(e)}")
            # Print the data to investigate any potential issues
            print("Data that failed to be stored:", data)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON message in Database: {str(e)}")
            # If JSON decoding fails, print the received body to investigate the issue
            print("Received Message Body (Failed to Decode) in Database:", data.decode())
        except KeyError as e:
            print(f"Error accessing key in JSON message in Database: {str(e)}")


