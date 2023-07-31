/* @Author: Nisanur Genc */


// Function to check if any input field has a value and enable/disable the "Filter" button accordingly
function checkFields() {
  const name = document.getElementById("name").value;
  const forename = document.getElementById("forename").value;
  const nationalities = document.getElementById("nationalities");
  const dateOfBirth = document.getElementById("date_of_birth").value;

  // Check if the 'nationalities' field has the default selected option (disabled and selected)
  const isNationalityDefault = nationalities.selectedIndex === 0;

  // Calculate if the "Filter" button should be disabled or not
  const isFilterButtonDisabled = !(name || forename || dateOfBirth || !isNationalityDefault);

  // JavaScript code to handle the click event for the "Filter" button
  const filterButton = document.getElementById("find");
  filterButton.disabled = isFilterButtonDisabled;
  filterButton.classList.toggle("disabled", isFilterButtonDisabled);
}

// Call the checkFields function when the page loads
document.addEventListener("DOMContentLoaded", () => {
  checkFields(); // Set the initial state of the "Filter" button
  // Add event listeners to input fields to trigger checkFields() when their values change
  document.getElementById("name").addEventListener("input", checkFields);
  document.getElementById("forename").addEventListener("input", checkFields);
  document.getElementById("nationalities").addEventListener("change", checkFields);
  document.getElementById("date_of_birth").addEventListener("input", checkFields);
});

/// Add event listener to the form submission for "Filter" button
document.querySelector('form[action="/filter"]').addEventListener('submit', function(event) {
  event.preventDefault(); // Prevent the default form submission behavior
  const showButton = document.getElementById('showButton');
  showButton.dataset.clicked = 'true'; // Set the 'clicked' attribute to true when the button is clicked

  // Disable scrolling until the button is clicked
  document.body.classList.add('disable-scrolling');

  const formData = new FormData(event.target); // Gather form data
  updateTable('/filter', formData); // Call the updateTable function to fetch and display filtered data
});

      
    // Add event listener for the 'Reset' button to reset the 'Filter' button state
    document.getElementById("reset").addEventListener("click", () => {
      setTimeout(checkFields, 0); // Use a timeout to let the reset process complete before checking fields
    });

    // Add event listener to the showButton
    document.getElementById("showButton").addEventListener("click", function() {
      // Scroll the header up
      document.getElementById("header").scrollIntoView({ behavior: "smooth" });

      // Scroll to the mainBody div with the live data
      document.getElementById("mainBody").scrollIntoView({ behavior: "smooth" });
    });

    // Function to update the last refreshed time
    function updateLastRefreshedTime() {
      const lastRefreshedElement = document.getElementById('lastRefreshed');
      const currentTime = new Date();
      lastRefreshedElement.textContent = currentTime.getMinutes();
    }

    // Call the updateLastRefreshedTime and updateTotalRecords functions when the page loads
    document.addEventListener('DOMContentLoaded', () => {
      updateLastRefreshedTime();
      updateTotalRecords();
    });

    // Add an interval to update the last refreshed time every minute
    setInterval(updateLastRefreshedTime, 60000);

    async function updateTable(route, formData) {
      try {
        const response = await fetch(route, {
          method: 'POST',
          body: formData
        });
    
        const data = await response.json();
        const tableBody = document.getElementById('filteredResultsBody'); // Use the tbody of the filtered results table
    
        // Clear any existing table rows
        tableBody.innerHTML = '';
    
        // Add the filtered data to the table
        data.data.forEach(person => {
          const newRow = tableBody.insertRow();
    
          // Loop through the columns to create table cells
          const columns = ['image', 'entity_id', 'name', 'forename', 'nationalities', 'date_of_birth'];
          columns.forEach(column => {
            const newCell = newRow.insertCell();
    
            // For the 'image' column, create an img element
            if (column === 'image') {
              const imgElement = document.createElement('img');
              imgElement.src = `/images/${person.entity_id}.jpg`; 
              imgElement.alt = `Image for ${person.name}`;
              imgElement.style.width = '100px';
              imgElement.style.height = '100px';
              imgElement.style.objectFit = 'cover';
              newCell.appendChild(imgElement);
            } else {
              // For other columns, set the text content
              newCell.textContent = person[column];
            }
          });
        });
    
        // Update the total number of records with the value obtained from the response
        const totalPeopleElement = document.getElementById('totalPeople');
        totalPeopleElement.textContent = data.total_people;

          // Update the count of filtered people in the "filteredCount" element.
          const filteredCountElement = document.getElementById('filteredCount');
          filteredCountElement.textContent = data.data.length;
    
        // If the button was clicked, scroll to the table where the data is displayed
        const showButton = document.getElementById('showButton');
        if (showButton.dataset.clicked === 'true') {
          const filteredResultsElement = document.getElementById('filteredResults');
          filteredResultsElement.scrollIntoView({ behavior: 'smooth' });
    
          // Enable scrolling after clicking the showButton and scrolling to the filteredResults
          document.body.classList.remove('disable-scrolling');
        }
    
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    }


  // Add event listener to the form submission for "Live Data" button
  document.querySelector('form[action="/live_data"]').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission behavior
    const showButton = document.getElementById('showButton');
    showButton.dataset.clicked = 'true'; // Set the 'clicked' attribute to true when the button is clicked

    // Disable scrolling until the button is clicked
    document.body.classList.add('disable-scrolling');

    updateTable('/live_data'); // Call the updateTable function to fetch and display live data
  });


    // Add event listener to the showButton
    document.getElementById('showButton').addEventListener('click', function() {
      const searchBar = document.getElementById('searchBar');
      searchBar.disabled = false;
      searchBar.focus();
    });

    // JavaScript code to handle the click event for the "Filter" button
    $(document).ready(function() {
        $("#filterButton").click(function() {
            // Submit the form to the '/filter' route when the "Filter" button is clicked
            $("form").submit();
        });
    });