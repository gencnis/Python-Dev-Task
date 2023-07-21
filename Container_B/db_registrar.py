# db_registrar.py
import json
import requests

class DBRegistrar:
    def __init__(self, person_model, db):
        self.person_model = person_model
        self.db = db


    def _get_image_url(self, image_data):
        try:
            response = requests.get(image_data['_links']['self']['href'])
            response.raise_for_status()
            image_json = response.json()

            # Check if the '_embedded' key is present in the image JSON
            if '_embedded' in image_json and 'images' in image_json['_embedded']:
                images = image_json['_embedded']['images']
                if images:
                    first_image = images[0]  # Take the first image from the list
                    if 'picture_id' in first_image and '_links' in first_image:
                        picture_id = first_image['picture_id']
                        links = first_image['_links']
                        if 'self' in links and 'href' in links['self']:
                            return links['self']['href']
            
            print("Error: Image data is missing or in an unexpected format.")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error requesting image URL: {str(e)}")
            return None
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing image JSON data: {str(e)}")
            return None

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

            print("data.get('image', {}).get('href'): ", data.get('image', {}).get('href'))
            # Store the data in the database
            image_href = data.get('image', {}).get('href')
            print("image_href: ", image_href)

            # Store the image URL directly as a string
            image_data = image_href if image_href else "Unknown"

            # Fetch and store the image URL in the database
            image_url = self._get_image_url(data['image'])
            if image_url:
                person_image_url = f"https://ws-public.interpol.int/notices/v1/red/{entity_id}/images/{image_url.split('/')[-1]}"
            else:
                person_image_url = None

            nationalities_json = json.dumps(data.get('nationalities', []))

            person = self.person_model(
                forename=data.get('name'),
                date_of_birth=data.get('date_of_birth'),
                entity_id=entity_id,
                nationalities=nationalities_json,
                name=data.get('forename'),
                image=image_data,
                image_url=person_image_url  # Store the fetched image URL in the database
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

    