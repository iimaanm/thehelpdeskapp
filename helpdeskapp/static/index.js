// Function takes ticket id and sends a post request to the 'delete-ticket' endpoint to delete the ticket
function deleteTicket(ticketId) {
    fetch('/delete-ticket', {
        method: 'POST',
        body: JSON.stringify({ ticketId: ticketId }),
    }).then((_res) => {
    window.location.href = '/';
});
}