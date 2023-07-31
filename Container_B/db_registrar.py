"""
db_registrar.py

This module contains the DBRegistrar class responsible for processing and storing data in the PostgreSQL database.

@Author: Nisanur Genc

"""

import json
import os
from flask_sqlalchemy import SQLAlchemy
import requests

class DBRegistrar:
    """Class for processing and storing data in the PostgreSQL database."""

    def __init__(self, person_model, db):
        """
        Initialize the DBRegistrar.

        :param person_model: The Person model class.
        :type person_model: class
        :param db: The SQLAlchemy database instance.
        :type db: flask_sqlalchemy.SQLAlchemy
        """
        self.person_model = person_model
        self.db = db


    def download_image(self, url, filename):
        """
        Download an image from the given URL and save it to the image_data directory.

        :param url: The URL of the image to download.
        :type url: str
        :param filename: The filename to use when saving the image.
        :type filename: str
        """
        try:
            response = requests.get(url)
            response.raise_for_status()

            # Check if the image_data directory exists, if not, create it
            image_dir = './image_data'
            print(f"Image Directory: {image_dir}")

            if not os.path.exists(image_dir):
                os.makedirs(image_dir, exist_ok=True)

            image_path = os.path.join(image_dir, filename)
            print(f"Image Path: {image_path}")

            with open(image_path, 'wb') as f:
                f.write(response.content)

            print(f"Image downloaded and saved to: {image_path}")
        
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred while downloading the image: {str(e)}")
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while downloading the image: {str(e)}")
        except Exception as e:
            print(f"Error downloading image: {str(e)}")



    def store_data_to_my_db(self, data):
        """
        Process and store the data in the PostgreSQL database.

        :param data: The data to be stored in the database.
        :type data: dict
        """
        
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
            image_data = data.get('image', "Unknown")
            
            image_url = data.get('image')
            if image_url:
                image_filename = f"{data['entity_id']}.jpg"  # You can adjust the filename as needed
                self.download_image(image_url, image_filename)

            nationalities_json = json.dumps(data.get('nationalities', []))

            person = self.person_model(
                forename=data.get('forename'),
                date_of_birth=data.get('date_of_birth'),
                entity_id=entity_id,
                nationalities=nationalities_json,
                name=data.get('name'),
                image=image_data,
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
