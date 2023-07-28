"""
ManageData.py

This script contains the InterpolDataExtractor class, which is responsible for extracting data from the Interpol API,
cleaning it, and publishing the cleaned data to a RabbitMQ queue.

Dependencies:
- ExtractCountries: Custom module for extracting nationalities from the Interpol website
- RabbitMQConnection: Custom module for establishing a connection to RabbitMQ
- string: Python module for working with string constants
- time: Python module for adding delays between requests
- requests: Python library for making HTTP requests
- json: Python module for working with JSON data

@Author: Nisanur Genc

"""

from ExtractCountries import InterpolCountriesExtractor
from RabbitMQConnection import RabbitMQConnection
import string
import time
import requests
import json
import csv


class ExtractImages:
    def fetch_image_url(self, image_data, entity_id, max_retries=9, retry_delay=200):
        retries = 0

        while retries < max_retries:
            try:
                response = requests.get(image_data['href'])
                if response.status_code == 200:
                    image_json = response.json()

                    # Check if the '_embedded' key is present in the image JSON
                    if '_embedded' in image_json and 'images' in image_json['_embedded']:
                        images = image_json['_embedded']['images']
                        if images:
                            first_image = images[0]  # Take the first image from the list
                            if '_links' in first_image and 'self' in first_image['_links']:
                                image_url = first_image['_links']['self']['href']
                                print("image_url: ", image_url)
                                return image_url

                    print("Error: Image data is missing or in an unexpected format.")
                    return "No Image Available"
                elif response.status_code == 403:
                    # Retry after a delay
                    retries += 1
                    print(f"Received Forbidden (403) status code. Retrying ({retries}/{max_retries})...")
                    time.sleep(retry_delay)
                else:
                    # Other non-200 status codes are considered as errors
                    print(f"Error: Unexpected status code - {response.status_code}")
                    return "No Image Available"

            except requests.exceptions.RequestException as e:
                print(f"Error requesting image URL: {str(e)}")
                return "No Image Available"
            except json.JSONDecodeError as e:
                print(f"Error while parsing JSON response for image: {str(e)}")
                return "No Image Available"

        print(f"Max retries reached. Unable to fetch image URL.")
        return "No Image Available"

class InterpolDataExtractor:
    def __init__(self, hostname, port, queue_name):
        """
        Constructor for the InterpolDataExtractor class.

        Parameters:
        - hostname (str): The hostname or IP address of the RabbitMQ server.
        - port (int): The port number for the RabbitMQ server (default is usually 5672).
        - queue_name (str): The name of the queue to which data will be published.
        """
        self.total_cleaned_data = 0
        self.cleaned_data = set()  # Change from list to set
        self.rabbitmq_publisher = RabbitMQConnection(hostname, port, queue_name)

    def clean_and_publish_data(self, notices):
        """
        Clean the data for each notice and publish it to RabbitMQ.

        Parameters:
        - notices (list): A list of Interpol notices obtained from the API response.
        """
        clean_data = []
        image_extractor = ExtractImages()  # Create an instance of the ExtractImages class

        for notice in notices:
            entity_id = notice.get("entity_id")
            if entity_id not in self.cleaned_data:  # Check for duplicates using the set
                name = notice.get("name") or "Unknown"
                forename = notice.get("forename") or "Unknown"
                date_of_birth = notice.get("date_of_birth") or "Unknown"
                nationalities = notice.get("nationalities")
                if nationalities is None:
                    nationalities = ["Unknown"]
                image_data = notice.get("_links", {}).get("images", {}) or "Unknown"

                print("image_data: ", image_data)
                # Fetch the image URL using the ExtractImages class
                image_url = image_extractor.fetch_image_url(image_data, entity_id)

                clean_item = {
                    "name": name,
                    "forename": forename,
                    "nationalities": nationalities,
                    "entity_id": entity_id,
                    "date_of_birth": date_of_birth,
                    "image": image_url,  # Use the fetched image URL here
                }

                clean_data.append(clean_item)
                self.cleaned_data.add(entity_id)  # Add the entity_id to the set

        self.total_cleaned_data += len(clean_data)
        print("counter:", self.total_cleaned_data)
        self.cleaned_data.update(item["entity_id"] for item in clean_data)  # Update the set

        # Publish the cleaned data
        for data_item in clean_data:
            self.rabbitmq_publisher.publish_data(data_item)

    @staticmethod
    def fetch_data_with_retry(url, max_retries=15, retry_delay=300):
        retries = 0

        while retries < max_retries:
            try:
                # Make the HTTP request
                r = requests.get(url)
                r.raise_for_status()  # Check for HTTP errors

                # Check for rate limit exceeded
                if "X-RateLimit-Remaining" in r.headers and int(r.headers["X-RateLimit-Remaining"]) == 0:
                    print("Rate limit exceeded. Retrying in a few minutes...")
                    print(retries, "retries so far.")
                    retries += 1
                    print("Waiting to retry..")
                    time.sleep(retry_delay)  # Wait for the retry delay
                    continue  # Retry the request

                # Process the response data
                return r.json()  # For example, return the JSON data

            except requests.exceptions.RequestException as e:
                print(f"Error while fetching data: {e}")
            except json.JSONDecodeError as e:
                print(f"Error while parsing JSON response: {e}")
            except requests.exceptions.HTTPError as e:
                print(f"HTTP error occurred: {e}")
            except Exception as e:
                print(f"An error occurred: {e}")

            retries += 1
            time.sleep(retry_delay)  # Wait for the retry delay

        print("Max retries reached. Unable to fetch data.")
        return None  # Return None or handle the retry limit exceeded situation as needed


    def extract_by_age(self, url):
        """
        Extract Interpol data by age for nationalities with more than 160 entries.

        Parameters:
        - more_than_160_genders (list): A list of tuples (wantedBy, gender) with more than 160 entries.
        - url (str): The base URL for the Interpol API.
            
        Returns:
        - more_than_160 (list): A list of nationalities with more than 160 entries.
        """

        age_intervals = [  # Define a list of age intervals
            (18, 24),
            (25, 25),
            (26, 26),
            (27, 27),
            (28, 28),
            (29, 29),
            (30, 30),
            (31, 31),
            (32, 32),
            (33, 33),
            (34, 34),
            (35, 35),
            (36, 36),
            (37, 37),
            (38, 38),
            (39, 39),
            (40, 40),
            (41, 41),
            (42, 42),
            (43, 43),
            (44, 44),
            (45, 45),
            (46, 46),
            (47, 47),
            (48, 48),
            (49, 49),
            (50, 50),
            (51, 51),
            (52, 52),
            (53, 53),
            (54, 54),
            (55, 55),
            (56, 56),
            (57, 57),
            (58, 58),
            (59, 59),
            (60, 60),
            (61, 61),
            (62, 62),
            (63, 63),
            (64, 64),
            (65, 65),
            (66, 66),
            (67, 67),
            (68, 68),
            (69, 69),
            (70, 75),
            (76, 80),
            (81, 85),
            (86, 89),
            (90, 120)
        ]
        more_than_160 = []

        for ageMin, ageMax in age_intervals:
            page = 1
            while True:
                url_with_params = url + "&ageMin=" + str(ageMin) + "&ageMax=" + str(ageMax)
                data = self.fetch_data_with_retry(url_with_params, max_retries=15, retry_delay=120)

                # Check if the response data is as expected
                if "_embedded" in data and "notices" in data["_embedded"]:
                    notices = data["_embedded"]["notices"]
                    print("Yaş ", ageMin, "-", ageMax, data["total"])  # Print information about the age interval
        
                    if data["total"] > 160:
                        more_than_160.append((ageMin, ageMax))

                    # Clean the data for the current nationality
                    self.clean_and_publish_data(notices)

                else:
                    print("Unexpected response format or missing data for age interval:", ageMin, "-", ageMax)

                   # Add a delay between requests to avoid rate limiting
                time.sleep(1)

                # Check if there are more pages, if not, break the loop
                if "last" in data["_links"]:
                    last_page_url = data["_links"]["last"]["href"]
                    max_pages = int(last_page_url.split("page=")[-1])
                    page += 1  # Increment the page number for the next iteration
                else:
                    print("No more pages for age interval:", ageMin, "-", ageMax)
                    break

                # Check if we have reached the maximum number of pages
                if page > max_pages:
                    print("Reached the maximum number of pages for age interval:", ageMin, "-", ageMax)
                    break
                
        print("Age interval with more than 160 entries:", more_than_160)
        return more_than_160


    def extract_by_gender(self, more_than_160_age, url):
        """
        Extract Interpol data by gender for nationalities with more than 160 entries.

        Parameters:
        - more_than_160_age (list): A list of tuples (ageMin, ageMax) with more than 160 entries.
        - url (str): The base URL for the Interpol API.

        Returns:
        - more_than_160 (list): A list of tuples (age interval, gender) with more than 160 entries.
        """
        more_than_160 = []
        genders = ["U", "F", "M"]

        for ageMin, ageMax in more_than_160_age:
            for gender in genders:
                page = 1

                while True:
                    url_with_params = f"{url}&sexId={gender}&ageMin={ageMin}&ageMax={ageMax}&page={page}"
                    data = self.fetch_data_with_retry(url_with_params, max_retries=15, retry_delay=120)

                    # Check if the response data is as expected
                    if "_embedded" in data and "notices" in data["_embedded"]:
                        notices = data["_embedded"]["notices"]
                        print("Age", ageMin, "-", ageMax, "Gender", gender, "Page", page, data["total"])  # Print information about the age, gender, and page

                        if data["total"] > 160:
                            more_than_160.append((ageMin, ageMax, gender))

                        # Clean the data for the current age and gender
                        self.clean_and_publish_data(notices)

                    else:
                        print("Unexpected response format or missing data for age", ageMin, "-", ageMax, "Gender", gender)
                        break

                    # Add a delay between requests to avoid rate limiting
                    time.sleep(1)

                    # Check if there are more pages, if not, break the loop
                    if "last" in data["_links"]:
                        last_page_url = data["_links"]["last"]["href"]
                        max_pages = int(last_page_url.split("page=")[-1])
                        page += 1  # Increment the page number for the next iteration
                    else:
                        print("No more pages for age", ageMin, "-", ageMax, "Gender", gender)
                        break

                    # Check if we have reached the maximum number of pages
                    if page > max_pages:
                        print("Reached the maximum number of pages for age", ageMin, "-", ageMax, "Gender", gender)
                        break

        print("Age and Gender with more than 160 entries:", more_than_160)
        return more_than_160


    def extract_by_wanted(self, more_than_160_gender, url, nationalities):
        """
        Extract Interpol data by nationality (wantedBy).

        Parameters:
        - nationalities (list): A list of nationalities extracted from the Interpol website.
        - url (str): The base URL for the Interpol API.

        Returns:
        - more_than_160 (list): A list of nationalities with more than 160 entries.
        """
        more_than_160 = []

        for ageMin, ageMax, gender in more_than_160_gender:
            for wanted_by in nationalities:
                page = 1

                while True:
                    url_with_params = f"{url}&sexId={gender}&ageMin={ageMin}&ageMax={ageMax}&arrestWarrantCountryId={wanted_by}&page={page}"
                    data = self.fetch_data_with_retry(url_with_params, max_retries=15, retry_delay=120)

                    # Check if the response data is as expected
                    if "_embedded" in data and "notices" in data["_embedded"]:
                        notices = data["_embedded"]["notices"]
                        print("Ülkelerden istenen:", wanted_by, "Gender", gender, "Page", page, data["total"])  # Print information about the wantedBy nationality

                        if data["total"] > 160:
                            more_than_160.append((ageMin, ageMax, gender, wanted_by))

                        # Clean the data for the current nationality
                        self.clean_and_publish_data(notices)

                    else:
                        print("Unexpected response format or missing data for nationality:", wanted_by)
                        break

                    # Add a delay between requests to avoid rate limiting
                    time.sleep(1)

                    # Check if there are more pages, if not, break the loop
                    if "last" in data["_links"]:
                        last_page_url = data["_links"]["last"]["href"]
                        max_pages = int(last_page_url.split("page=")[-1])
                        page += 1  # Increment the page number for the next iteration
                    else:
                        print("No more pages for", wanted_by, "Gender", gender)
                        break

                    # Check if we have reached the maximum number of pages
                    if page > max_pages:
                        print("Reached the maximum number of pages for", wanted_by, "Gender", gender)
                        break

        print("WantedBy nationalities with more than 160 entries:", more_than_160)
        return more_than_160


    def extract_by_nationality(self, more_than_160_wanted, url, nationalities):
        """
        Extract Interpol data by nationality.

        Parameters:
        - nationalities (list): A list of nationalities extracted from the Interpol website.
        - url (str): The base URL for the Interpol API.

        Returns:
        - more_than_160 (list): A list of nationalities with more than 160 entries.
        """
        more_than_160 = []

        for ageMin, ageMax, gender, wanted_by, nation in more_than_160_wanted:
            for nation in nationalities:
                page = 1

                while True:
                    url_with_params = f"{url}&sexId={gender}&ageMin={ageMin}&ageMax={ageMax}&arrestWarrantCountryId={wanted_by}&nationality={nation}&page={page}"
                    data = self.fetch_data_with_retry(url_with_params, max_retries=15, retry_delay=120)

                    # Check if the response data is as expected
                    if "_embedded" in data and "notices" in data["_embedded"]:
                        notices = data["_embedded"]["notices"]
                        print("Ülkesi:", nation, "Gender", gender, "WantedBy", wanted_by, "Page", page, data["total"])

                        if data["total"] > 160:
                            more_than_160.append((ageMin, ageMax, gender, wanted_by, nation))

                        # Clean the data for the current nationality
                        self.clean_and_publish_data(notices)

                    else:
                        print("Unexpected response format or missing data for nationality:", wanted_by, "Gender", gender, "WantedBy", wanted_by)
                        break

                    # Add a delay between requests to avoid rate limiting
                    time.sleep(1)

                    # Check if there are more pages, if not, break the loop
                    if "last" in data["_links"]:
                        last_page_url = data["_links"]["last"]["href"]
                        max_pages = int(last_page_url.split("page=")[-1])
                        page += 1  # Increment the page number for the next iteration
                    else:
                        print("No more pages for", nation, "Gender", gender, "WantedBy", wanted_by)
                        break

                    # Check if we have reached the maximum number of pages
                    if page > max_pages:
                        print("Reached the maximum number of pages for", nation, "Gender", gender, "WantedBy", wanted_by)
                        break

        print("Nationalities with more than 160 entries:", more_than_160)
        return more_than_160

    def extract_by_forename(self, more_than_160_nat, url):

        more_than_160 = []


        for ageMin, ageMax, gender, wanted_by, nation, forename in more_than_160_nat:
            for forename in string.ascii_uppercase:
                page = 1

                while True:
                    url_with_params = f"{url}&sexId={gender}&ageMin={ageMin}&ageMax={ageMax}&arrestWarrantCountryId={wanted_by}&nationality={nation}&forename={forename}&page={page}"
                    data = self.fetch_data_with_retry(url_with_params, max_retries=15, retry_delay=120)

                    # Check if the response data is as expected
                    if "_embedded" in data and "notices" in data["_embedded"]:
                        notices = data["_embedded"]["notices"]
                        print("Soyadı harfi:", forename, "Gender", gender, "WantedBy", wanted_by, "Nationality", nation, "Page", page, data["total"]) 

                        if data["total"] > 160:
                            more_than_160.append((ageMin, ageMax, gender, wanted_by, nation, forename))

                        # Clean the data for the current nationality
                        self.clean_and_publish_data(notices)

                    else:
                        print("Unexpected response format or missing data for nationality:", wanted_by, "Gender", gender, "WantedBy", wanted_by)
                        break

                    # Add a delay between requests to avoid rate limiting
                    time.sleep(1)

                    # Check if there are more pages, if not, break the loop
                    if "last" in data["_links"]:
                        last_page_url = data["_links"]["last"]["href"]
                        max_pages = int(last_page_url.split("page=")[-1])
                        page += 1  # Increment the page number for the next iteration
                    else:
                        print("No more pages for", forename, "Gender", gender, "WantedBy", wanted_by, "Nationality", nation)
                        break

                    # Check if we have reached the maximum number of pages
                    if page > max_pages:
                        print("Reached the maximum number of pages for", forename, "Gender", gender, "WantedBy", wanted_by, "Nationality", nation)
                        break

        print("Forenames with more than 160 entries:", more_than_160)
        return more_than_160


    def extract_by_name(self, more_than_160_forename, url):

        more_than_160 = []

        for ageMin, ageMax, gender, wanted_by, nation, forename in more_than_160_forename:
            for name in string.ascii_uppercase:
                page = 1

                while True:
                    url_with_params = f"{url}&sexId={gender}&ageMin={ageMin}&ageMax={ageMax}&arrestWarrantCountryId={wanted_by}&nationality={nation}&forename={forename}&name={name}&page={page}"
                    data = self.fetch_data_with_retry(url_with_params, max_retries=15, retry_delay=120)

                    # Check if the response data is as expected
                    if "_embedded" in data and "notices" in data["_embedded"]:
                        notices = data["_embedded"]["notices"]
                        print("Adının harfi:", name, "Forename", forename, "Gender", gender, "WantedBy", wanted_by, "Nationality", nation, "Page", page, data["total"]) 

                        if data["total"] > 160:
                            more_than_160.append((ageMin, ageMax, gender, wanted_by, nation, forename, name))

                        # Clean the data for the current nationality
                        self.clean_and_publish_data(notices)

                    else:
                        print("Unexpected response format or missing data for nationality:", wanted_by, "Forename", forename, "Gender", gender, "WantedBy", wanted_by)
                        break

                    # Add a delay between requests to avoid rate limiting
                    time.sleep(1)

                    # Check if there are more pages, if not, break the loop
                    if "last" in data["_links"]:
                        last_page_url = data["_links"]["last"]["href"]
                        max_pages = int(last_page_url.split("page=")[-1])
                        page += 1  # Increment the page number for the next iteration
                    else:
                        print("No more pages for", name, "Forename", forename, "Gender", gender, "WantedBy", wanted_by, "Nationality", nation)
                        break

                    # Check if we have reached the maximum number of pages
                    if page > max_pages:
                        print("Reached the maximum number of pages for", name, "Forename", forename, "Gender", gender, "WantedBy", wanted_by, "Nationality", nation)
                        break

        print("Names with more than 160 entries:", more_than_160)
        return more_than_160



    def start_extraction(self):
        """
        Start the data extraction process.

        This method calls different extraction methods to fetch data based on certain criteria.
        """
        start_time = time.time()  # Record the start time
        interpol_countries_extractor = InterpolCountriesExtractor("https://www.interpol.int/How-we-work/Notices/View-Red-Notices")
        nationalities = interpol_countries_extractor.get_extracted_nationalities()

        try:
            base_url = "https://ws-public.interpol.int/notices/v1/red?="

            more_than_160_age = self.extract_by_age(base_url)
            more_than_160_gender = self.extract_by_gender(more_than_160_age, base_url)
            more_than_160_wanted = self.extract_by_wanted(more_than_160_gender, base_url, nationalities)  
            more_than_160_nat = self.extract_by_nationality(more_than_160_wanted, base_url, nationalities) 
            more_than_160_forename = self.extract_by_forename(more_than_160_nat, base_url)
            more_than_160 = self.extract_by_name(more_than_160_forename, base_url)
            print("You cannot get these: ", len(more_than_160))

        except Exception as e:
            print("Error in main:", e)
        

        print("Total data cleaned and published:", self.total_cleaned_data)

        elapsed_minutes = (time.time() - start_time) / 60  # Calculate elapsed minutes
        print("Total data cleaned and published:", self.total_cleaned_data)
        print(f"Time elapsed: {elapsed_minutes:.2f} minutes")


if __name__ == "__main__":
    rabbitmq_host = "container_c"  # Replace with the actual hostname or IP address of RabbitMQ
    rabbitmq_port = 5672  # The default port for RabbitMQ
    queue_name = "interpol_data"  # The name of the RabbitMQ queue

    data_extractor = InterpolDataExtractor(rabbitmq_host, rabbitmq_port, queue_name)
    data_extractor.start_extraction()