// Function takes ticket id and sends a post request to the 'delete-ticket' endpoint to delete the ticket
function deleteTicket(ticketId) {
    if (confirm('Are you sure you want to delete this ticket?')) {
        fetch('/delete-ticket', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ticketId: ticketId }),
        })
        .then(response => {
            if (response.ok) {
                // Reloading the current page and allowing flash message to be shown
                window.location.reload();
            } else {
                alert('Error: Ticket could not be deleted.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An unexpected error occurred.');
        });
    }
}
