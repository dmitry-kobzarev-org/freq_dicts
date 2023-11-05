// script.js

document.addEventListener('DOMContentLoaded', function () {
    // Other JavaScript code ...

    // Retrieve the "info_id" from the info block
    const infoBlock = document.getElementById('info-block-id');

    // Function to update the info block content and "data-info-id"
    function updateInfoBlock(data) {
        infoBlock.textContent = data.info;
        infoBlock.setAttribute('data-info-id', data.id);
    }

    // Callback for the "left" button
    const leftButton = document.getElementById('left-button');
    leftButton.addEventListener('click', function () {
        // First callback: Call /api/process_log
        fetch('/api/process_log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(
                { button: 'left', info_id: infoBlock.getAttribute('data-info-id')})
        })
        .then(response => response.json())
        .then(data => {
            // Second callback: Call /api/get_data and update info block
            fetch('/api/get_data')
            .then(response => response.json())
            .then(updateInfoBlock)
            .catch(error => {
                console.error('Error fetching data:', error);
            });
        })
        .catch(error => {
            console.error('Error processing log:', error);
        });
    });

    // Callback for the "right" button
    const rightButton = document.getElementById('right-button');
    rightButton.addEventListener('click', function () {
        // First callback: Call /api/process_log
        fetch('/api/process_log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(
                 { button: 'right', info_id: infoBlock.getAttribute('data-info-id')})
        })
        .then(response => response.json())
        .then(data => {
            // Second callback: Call /api/get_data and update info block
            fetch('/api/get_data')
            .then(response => response.json())
            .then(updateInfoBlock)
            .catch(error => {
                console.error('Error fetching data:', error);
            });
        })
        .catch(error => {
            console.error('Error processing log:', error);
        });
    });

    // You can use "infoId" and "updateInfoBlock" in your JavaScript logic as needed
});
