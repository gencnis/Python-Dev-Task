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

        for notice in notices:
            entity_id = notice.get("entity_id")
            if entity_id not in self.cleaned_data:  # Check for duplicates using the set
                name = notice.get("name")
                lastname = notice.get("forename")
                date_of_birth = notice.get("date_of_birth")
                nationalities = notice.get("nationalities")
                image = notice.get("_links", {}).get("images", {})

                clean_item = {
                    "name": name,
                    "lastname": lastname,
                    "nationalities": nationalities,
                    "entity_id": entity_id,
                    "date_of_birth": date_of_birth,
                    "image": image,
                }

                clean_data.append(clean_item)
                self.cleaned_data.add(entity_id)  # Add the entity_id to the set

        self.total_cleaned_data += len(clean_data)
        print("counter:", self.total_cleaned_data)
        self.cleaned_data.update(item["entity_id"] for item in clean_data)  # Update the set

        # Publish the cleaned data
        for data_item in clean_data:
            self.rabbitmq_publisher.publish_data(data_item)
    

    def extract_by_wanted(self, nationalities, url):
        """
        Extract Interpol data by nationality (wantedBy).

        Parameters:
        - nationalities (list): A list of nationalities extracted from the Interpol website.
        - url (str): The base URL for the Interpol API.

        Returns:
        - more_than_160 (list): A list of nationalities with more than 160 entries.
        """

        more_than_160 = []

        for wanted_by in nationalities:
            try:
                # Make the HTTP request
                r = requests.get(url + "&arrestWarrantCountryId=" + wanted_by)
                r.raise_for_status()  # Check for HTTP errors

                # Check for rate limit exceeded
                if "X-RateLimit-Remaining" in r.headers and int(r.headers["X-RateLimit-Remaining"]) == 0:
                    print("Rate limit exceeded. Retrying in a few minutes...")
                    time.sleep(60)  # Wait for a minute and retry
                    r = requests.get(url + "&arrestWarrantCountryId=" + wanted_by)  # Retry the request

                # Process the response data
                response = r.json()  # Parse the response as JSON

                # Check if the response data is as expected
                if "_embedded" in response and "notices" in response["_embedded"]:
                    notices = response["_embedded"]["notices"]
                    print("Ülkelerden istenen: ", wanted_by, response["total"])  # Print information about the wantedBy nationality

                    if response["total"] > 160:
                        more_than_160.append(wanted_by)

                    # Clean the data for the current nationality
                    clean_data = self.clean_and_publish_data(notices)

                else:
                    print("Unexpected response format or missing data for nationality:", wanted_by)

            except requests.exceptions.RequestException as e:
                print("Error while fetching data for nationality:", wanted_by, e)
                # Handle connection errors, timeouts, etc.

            except json.JSONDecodeError as e:
                print("Error while parsing JSON response for nationality:", wanted_by, e)
                # Handle incomplete or unexpected data in the JSON response

            except requests.exceptions.HTTPError as e:
                print("HTTP error occurred for nationality:", wanted_by, e)
                # Handle specific HTTP status codes here (e.g., 404, 500)

            except Exception as e:
                print("An error occurred for nationality:", wanted_by, e)

            # Add a delay between requests to avoid rate limiting
            time.sleep(1)

        print("WantedBy nationalities with more than 160 entries:", more_than_160)
        return more_than_160


    def extract_by_gender(self, more_than_160_wanted, url):
        """
        Extract Interpol data by gender for nationalities with more than 160 entries.

        Parameters:
        - more_than_160_wanted (list): A list of nationalities with more than 160 entries.
        - url (str): The base URL for the Interpol API.

        Returns:
        - more_than_160 (list): A list of tuples (wantedBy, gender) with more than 160 entries.
        """
            
        more_than_160 = []
        genders = ["U", "F", "M"]

        for wanted_by in more_than_160_wanted:
            for gender in genders:
                try:
                    # Make the HTTP request
                    r = requests.get(url + "&arrestWarrantCountryId=" + wanted_by + "&sexId=" + gender)
                    r.raise_for_status()  # Check for HTTP errors

                    # Check for rate limit exceeded
                    if "X-RateLimit-Remaining" in r.headers and int(r.headers["X-RateLimit-Remaining"]) == 0:
                        print("Rate limit exceeded. Retrying in a few minutes...")
                        time.sleep(60)  # Wait for a minute and retry
                        r = requests.get(url + "&arrestWarrantCountryId=" + wanted_by + "&sexId=" + gender)  # Retry the request

                    # Process the response data
                    response = r.json()  # Parse the response as JSON

                    # Check if the response data is as expected
                    if "_embedded" in response and "notices" in response["_embedded"]:
                        notices = response["_embedded"]["notices"]
                        print("Ülkelerden istenen: ", wanted_by, response["total"])  # Print information about the wantedBy nationality

                        if response["total"] > 160:
                            more_than_160.append((wanted_by, gender))

                        # Clean the data for the current nationality and append it to the main data list
                        self.clean_and_publish_data(notices)

                    else:
                        print("Unexpected response format or missing data for nationality:", wanted_by)

                except requests.exceptions.RequestException as e:
                    print("Error while fetching data for nationality:", wanted_by, e)
                    # Handle connection errors, timeouts, etc.

                except json.JSONDecodeError as e:
                    print("Error while parsing JSON response for nationality:", wanted_by, e)
                    # Handle incomplete or unexpected data in the JSON response

                except requests.exceptions.HTTPError as e:
                    print("HTTP error occurred for nationality:", wanted_by, e)
                    # Handle specific HTTP status codes here (e.g., 404, 500)

                except Exception as e:
                    print("An error occurred for nationality:", wanted_by, e)

                # Add a delay between requests to avoid rate limiting
                time.sleep(1)

            print("WantedBy nationalities with more than 160 entries:", more_than_160)

        return more_than_160

    def extract_by_age(self, more_than_160_genders, url):
        """
        Extract Interpol data by age for nationalities with more than 160 entries.

        Parameters:
        - more_than_160_genders (list): A list of tuples (wantedBy, gender) with more than 160 entries.
        - url (str): The base URL for the Interpol API.

        Returns:
        - more_than_160 (list): A list of tuples (wantedBy, gender, age_interval) with more than 160 entries.
        """
            
        age_intervals = [  # Define a list of age intervals
            (18, 25),
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
            (36, 40),
            (40, 45),
            (45, 50),
            (50, 70),
            (70, 90),
            (90, 120)
        ]
        more_than_160 = []

        for wanted_by, gender in more_than_160_genders:
            for ageMin, ageMax in age_intervals:
                try:
                    # Make the HTTP request
                    r = requests.get(
                        url + "&arrestWarrantCountryId=" + wanted_by + "&sexId=" + gender +
                        "&ageMin=" + str(ageMin) + "&ageMax=" + str(ageMax)
                    )
                    r.raise_for_status()  # Check for HTTP errors

                    # Check for rate limit exceeded
                    if "X-RateLimit-Remaining" in r.headers and int(r.headers["X-RateLimit-Remaining"]) == 0:
                        print("Rate limit exceeded. Retrying in a few minutes...")
                        time.sleep(60)  # Wait for a minute and retry
                        r = requests.get(
                            url + "&arrestWarrantCountryId=" + wanted_by + "&sexId=" + gender +
                            "&ageMin=" + str(ageMin) + "&ageMax=" + str(ageMax)
                        )  # Retry the request

                    # Process the response data
                    response = r.json()  # Parse the response as JSON

                    # Check if the response data is as expected
                    if "_embedded" in response and "notices" in response["_embedded"]:
                        notices = response["_embedded"]["notices"]
                        print("Yaş ", ageMin, "-", ageMax, response["total"])  # Print information about the age interval

                        if response["total"] > 160:
                            more_than_160.append((wanted_by, gender, (ageMin, ageMax)))

                        # Clean the data for the current nationality and append it to the main data list
                        self.clean_and_publish_data(notices)

                    else:
                        print("Unexpected response format or missing data for age interval:", ageMin, "-", ageMax)

                except requests.exceptions.RequestException as e:
                    print("Error while fetching data for age interval:", ageMin, "-", ageMax, e)
                    # Handle connection errors, timeouts, etc.

                except json.JSONDecodeError as e:
                    print("Error while parsing JSON response for age interval:", ageMin, "-", ageMax, e)
                    # Handle incomplete or unexpected data in the JSON response

                except requests.exceptions.HTTPError as e:
                    print("HTTP error occurred for age interval:", ageMin, "-", ageMax, e)
                    # Handle specific HTTP status codes here (e.g., 404, 500)

                except Exception as e:
                    print("An error occurred for age interval:", ageMin, "-", ageMax, e)

                # Add a delay between requests to avoid rate limiting
                time.sleep(1)

        return more_than_160
    
    def extract_by_nationality(self, more_than_160_age, url, nationalities):
        """
        Extract Interpol data by nationality for age-gender combinations with more than 160 entries.

        Parameters:
        - more_than_160_age (list): A list of tuples (wantedBy, gender, age_interval) with more than 160 entries.
        - url (str): The base URL for the Interpol API.
        - nationalities (list): A list of nationalities extracted from the Interpol website.

        Returns:
        - more_than_160 (list): A list of tuples (wantedBy, gender, age_interval, nationality) with more than 160 entries.
        """

        more_than_160 = []
        
        for wantedBy, gender, age_interval in more_than_160_age:
            for nation in nationalities:
                try:
                    # Make the HTTP request
                    r = requests.get(
                        url + "&arrestWarrantCountryId=" + wantedBy + "&sexId=" + gender +
                        "&ageMin=" + str(age_interval[0]) + "&ageMax=" + str(age_interval[1]) +
                        "&nationality=" + nation
                    )
                    r.raise_for_status()
                    response = r.json()
                    notices = response["_embedded"]["notices"]
                    print("Ükesi ", nation, response["total"])

                    if response["total"] > 160:
                        more_than_160.append((wantedBy, gender, age_interval, nation))

                    # Clean the data for the current nationality and append it to the main data list
                    self.clean_and_publish_data(notices)

                except requests.exceptions.RequestException as e:
                    print("Error while fetching data for nationality:", nation, e)
                    # Handle connection errors, timeouts, etc.

                except json.JSONDecodeError as e:
                    print("Error while parsing JSON response for nationality:", nation, e)
                    # Handle incomplete or unexpected data in the JSON response

                except requests.exceptions.HTTPError as e:
                    print("HTTP error occurred for nationality:", nation, e)
                    # Handle specific HTTP status codes here (e.g., 404, 500)

                except Exception as e:
                    print("An error occurred for nationality:", nation, e)

                # Add a delay between requests to avoid rate limiting
                time.sleep(1)
        return more_than_160


    def extract_by_letter(self, more_than_160_nat, url):
        """
        Extract Interpol data by letter (forename and name) for nationality-age-gender combinations with more than 160 entries.

        Parameters:
        - more_than_160_nat (list): A list of tuples (wantedBy, gender, age_interval, nationality) with more than 160 entries.
        - url (str): The base URL for the Interpol API.

        Returns:
        - more_than_160 (list): A list of tuples (wantedBy, gender, age_interval, nationality) that failed to fetch data.
        """

        more_than_160 = []

        def make_request(self, url, params, more_than_160):
            """
            Make an HTTP request to the Interpol API with retries.

            This method handles making an HTTP GET request to the Interpol API with the given parameters.
            It also includes retry logic to handle potential network or API issues.

            Parameters:
            - url (str): The base URL for the Interpol API.
            - params (dict): The parameters to include in the API request.
            - more_than_160 (set): A set to store the failed requests.

            Returns:
            - list: A list of notice objects extracted from the API response.
            """

            max_retries = 3
            for retry in range(max_retries):
                try:
                    # Make the HTTP request
                    r = requests.get(url, params=params)
                    r.raise_for_status()  # Check for HTTP errors
                    response = r.json()  # Parse the response as JSON

                    if "_embedded" in response and "notices" in response["_embedded"]:
                        notices = response["_embedded"]["notices"]
                        return notices
                    else:
                        # The response did not contain the expected data
                        print("Unexpected response format or missing data.")
                        return []

                except requests.exceptions.RequestException as e:
                    print(f"Error while fetching data: {e}")
                    # Handle connection errors, timeouts, etc.
                    if retry < max_retries - 1:
                        print(f"Retrying ({retry+1}/{max_retries}) in a few seconds...")
                        time.sleep(5)  # Wait for a few seconds and retry
                    else:
                        print(f"Failed to fetch data after {max_retries} retries.")
                        more_than_160.add(params)  # Add the failed params tuple to more_than_160
                        return []

                except json.JSONDecodeError as e:
                    print(f"Error while parsing JSON response: {e}")
                    # Handle incomplete or unexpected data in the JSON response
                    more_than_160.add(params)  # Add the failed params tuple to more_than_160
                    return []

                except requests.exceptions.HTTPError as e:
                    print(f"HTTP error occurred: {e}")
                    # Handle specific HTTP status codes here (e.g., 404, 500)
                    more_than_160.add(params)  # Add the failed params tuple to more_than_160
                    return []

                except Exception as e:
                    print(f"An error occurred: {e}")
                    more_than_160.add(params)  # Add the failed params tuple to more_than_160
                    return []


        for wanted_by, gender, age_interval, nation in more_than_160_nat:
            age_min, age_max = age_interval
            for letter in string.ascii_uppercase:
                params = {
                    "arrestWarrantCountryId": wanted_by,
                    "sexId": gender,
                    "ageMin": str(age_min),
                    "ageMax": str(age_max),
                    "nationality": nation,
                    "forename": letter,
                }

                notices = self.make_request(url, params, more_than_160)
                # Pass the retrieved notices to clean_and_publish_data for processing
                self.clean_and_publish_data(notices)

                for fletter in string.ascii_uppercase:
                    params["name"] = fletter
                    self.make_request(url, params, more_than_160)
                    # Pass the retrieved notices to clean_and_publish_data for processing
                    self.clean_and_publish_data(notices)

        print("Failed to fetch data for the following tuples:")
        for params in more_than_160:
            print(params)

        return more_than_160


    def start_extraction(self):
        """
        Start the data extraction process.

        This method calls different extraction methods to fetch data based on certain criteria.
        """
        interpol_countries_extractor = InterpolCountriesExtractor("https://www.interpol.int/How-we-work/Notices/View-Red-Notices")
        nationalities = interpol_countries_extractor.get_extracted_nationalities()

        try:
            base_url = "https://ws-public.interpol.int/notices/v1/red?="

            more_than_160_wanted = self.extract_by_wanted(nationalities, base_url)
            more_than_160_gender = self.extract_by_gender(more_than_160_wanted, base_url)
            more_than_160_age = self.extract_by_age(more_than_160_gender, base_url)
            more_than_160_nat = self.extract_by_nationality(more_than_160_age, base_url, nationalities)
            more_than_160 = self.extract_by_letter(more_than_160_nat, base_url)
            print("You cannot get these: ", len(more_than_160))
            print(more_than_160)

        except Exception as e:
            print("Error in main:", e)
        
        print("Total data cleaned and published:", self.total_cleaned_data)

if __name__ == "__main__":
    rabbitmq_host = "container_c"  # Replace with the actual hostname or IP address of RabbitMQ
    rabbitmq_port = 5672  # The default port for RabbitMQ
    queue_name = "interpol_data"  # The name of the RabbitMQ queue

    data_extractor = InterpolDataExtractor(rabbitmq_host, rabbitmq_port, queue_name)
    data_extractor.start_extraction()