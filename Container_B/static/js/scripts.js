    // Function to check if any input field has a value and enable/disable the "Filter" button accordingly
    function checkFields() {
        const name = document.getElementById("name").value;
        const forename = document.getElementById("forename").value;
        const nationalities = document.getElementById("nationalities");
        const dateOfBirth = document.getElementById("date_of_birth").value;
  
        // Check if the 'nationalities' field has the default selected option (disabled and selected)
        const isNationalityDefault = nationalities.selectedIndex === 0;
  
        const filterButton = document.getElementById("find");
        const isFilterButtonDisabled = !(name.trim() || forename.trim() || (nationalities.value && !isNationalityDefault) || dateOfBirth.trim());
  
        // Toggle the "disabled" attribute based on the button's disabled state
        filterButton.disabled = isFilterButtonDisabled;
        filterButton.classList.toggle("disabled", isFilterButtonDisabled);
      }
  
      // Call the checkFields function when the page loads
      document.addEventListener("DOMContentLoaded", checkFields);
  
      // Add event listeners for 'input' and 'change' events to each input field
      const inputFields = document.querySelectorAll(".form-control");
      inputFields.forEach(input => {
        input.addEventListener("input", checkFields);
        input.addEventListener("change", checkFields);
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
  
      async function updateTable() {
        try {
          const response = await fetch('/live_data', {
            method: 'POST'
            // Add other headers if needed
          });
      
          const data = await response.json();
          const tableBody = document.querySelector('tbody');
      
          // Clear any existing table rows
          tableBody.innerHTML = '';
      
          // Add the live data to the table
          data.data.forEach(person => {
            const newRow = tableBody.insertRow();
      
            // Loop through the columns to create table cells
            const columns = ['image', 'entity_id', 'name', 'forename', 'nationalities', 'date_of_birth'];
            columns.forEach(column => {
              const newCell = newRow.insertCell();
      
              // For the 'image' column, create an img element
              if (column === 'image') {
                const imgElement = document.createElement('img');
                imgElement.src = `/images/${person.entity_id}.jpg`; // Assuming the image filenames are 'entity_id.jpg'
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
      
          // If the button was clicked, scroll to the table where the live data is displayed
          const showButton = document.getElementById('showButton');
          if (showButton.dataset.clicked === 'true') {
            const mainBodyElement = document.getElementById('mainBody');
            mainBodyElement.scrollIntoView({ behavior: 'smooth' });
      
            // Enable scrolling after clicking the showButton and scrolling to the mainBody
            document.body.classList.remove('disable-scrolling');
          }
      
        } catch (error) {
          console.error('Error fetching live data:', error);
        }
      }
  
      // Add event listener to the form submission
      document.querySelector('form[action="/live_data"]').addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent the default form submission behavior
        const showButton = document.getElementById('showButton');
        showButton.dataset.clicked = 'true'; // Set the 'clicked' attribute to true when the button is clicked
  
        // Disable scrolling until the button is clicked
        document.body.classList.add('disable-scrolling');
  
        updateTable(); // Call the updateTable function to fetch and display live data
      });
  
      // Add event listener to the showButton
      document.getElementById('showButton').addEventListener('click', function() {
        const searchBar = document.getElementById('searchBar');
        searchBar.disabled = false;
        searchBar.focus();
      });