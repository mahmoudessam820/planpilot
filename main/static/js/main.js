

// Close buttons
const closeButton = document.querySelectorAll('.close-button');
closeButton.forEach(button => {
    button.addEventListener('click', () => {
        button.parentElement.style.display = 'none';
    });
});

flatpickr("#datepicker", {
    // Configuration options for Flatpickr
    // You can customize the appearance and behavior here
});

// display the name of the file 
document.addEventListener('DOMContentLoaded', function() {

    const inputFile = document.getElementById('id_attachment');

    inputFile.addEventListener('change', function() {

        const fileNameDisplay = document.getElementById('file-name-display');

        if (inputFile.files.length > 0) {
            fileNameDisplay.textContent = inputFile.files[0].name;
        } else {
            fileNameDisplay.textContent = 'No file chosen';
        }

    });

});