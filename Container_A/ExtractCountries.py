"""
ExtractCountries.py

This script extracts the list of nationalities from the Interpol website.

Dependencies:
- requests: Python library for making HTTP requests
- BeautifulSoup: Python library for web scraping and HTML parsing

The main function 'extract' sends a GET request to the Interpol website and parses the HTML 
content using BeautifulSoup. It finds the select element with the name "nationality" and extracts 
the values (nationalities) from the option elements. The extracted nationalities are returned as a list.

@Author: Nisanur Genc
"""
import requests
from bs4 import BeautifulSoup

class InterpolCountriesExtractor:
    """
    A class for extracting nationalities from the Interpol website.

    This class provides methods to fetch the Interpol website's HTML content,
    extract nationalities from the HTML, and test the extraction process.

    Attributes:
    - url (str): The URL of the Interpol website for Red Notices.
    """

    def __init__(self, url):
        """
        Initialize the InterpolCountriesExtractor object.

        Parameters:
        - url (str): The URL of the Interpol website for Red Notices.
        """
        self.url = url

    def extract_nationalities(self, html_content):
        """
        Extract nationalities from the HTML content of the Interpol website.

        Parameters:
        - html_content (str): The HTML content of the Interpol website.

        Returns:
        - list: A list of nationalities extracted from the HTML.
        """
        nationality_list = []

        try:
            # Parse the HTML content using BeautifulSoup
            content = BeautifulSoup(html_content, "html.parser")
            select_elements = content.find_all("select", {"name": "nationality"})
            for select_element in select_elements:
                options = select_element.find_all("option")
                for opt in options:
                    if opt.has_attr('value'):
                        nationality_list.append(opt['value'])
        except (AttributeError, TypeError) as e:
            print("Error while parsing the HTML content:", e)

        return nationality_list

    def get_extracted_nationalities(self):
        """
        Fetch and extract nationalities from the Interpol website.

        Returns:
        - list: A list of nationalities extracted from the website.
        """
        # Send a GET request to the Interpol website and fetch the HTML content
        response = requests.get(self.url)
        if response.status_code == 200:
            html_content = response.text
            nationalities = self.extract_nationalities(html_content)
            return nationalities
        else:
            print("Failed to fetch the Interpol website. Status code:", response.status_code)
            return []

    def test_extraction(self):
        """
        Test the extraction of nationalities from the Interpol website.
        """
        nationalities = self.get_extracted_nationalities()
        print("Extracted Nationalities:", nationalities)

if __name__ == "__main__":
    # Create an instance of InterpolCountriesExtractor with the Interpol website URL
    interpol_countries_extractor = InterpolCountriesExtractor("https://www.interpol.int/How-we-work/Notices/View-Red-Notices")
    # Test the extraction of nationalities
    interpol_countries_extractor.test_extraction()
