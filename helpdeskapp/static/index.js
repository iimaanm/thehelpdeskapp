// Function takes ticket id and sends a post request to the 'delete-ticket' endpoint to delete the ticket
function deleteTicket(ticketId) {
    if (confirm('Are you sure you want to delete this ticket?')) {
        const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
        const csrfToken = csrfTokenMeta ? csrfTokenMeta.getAttribute('content') : '';

        fetch('/delete-ticket', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ ticketId: ticketId }),
        })
        .then(response => {
            if (response.ok) {
                // Reloading the current page and allowing flash message to be shown
                window.location.reload();
            } else {
                alert('Error: Ticket could not be deleted');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An unexpected error occurred');
        });
    }
}

// Warning user if there are unsaved changes on a form
let hasUnsavedChanges = false;

function markUnsavedChanges() {
    hasUnsavedChanges = true;
}

function clearUnsavedChanges() {
    hasUnsavedChanges = false;
    window.onbeforeunload = null;
}

function handleBeforeUnload(e) {
    if (hasUnsavedChanges) {
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return 'You have unsaved changes. Are you sure you want to leave?';
    }

    return undefined;
}

function initializeUnsavedChangesWarning() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        // Skip form inside modals
        if (form.closest('.modal')) return;
        form.addEventListener('input', markUnsavedChanges);
        // On submit, reset hasUnsavedChanges flag and remove warning
        form.addEventListener('submit', clearUnsavedChanges);
    });

    window.onbeforeunload = handleBeforeUnload;
}

// Mark form as having Unsaved Changes on input change
window.addEventListener('DOMContentLoaded', function () {
    initializeUnsavedChangesWarning();
});

window.deleteTicket = deleteTicket;

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        clearUnsavedChanges,
        deleteTicket,
        getHasUnsavedChanges: function () {
            return hasUnsavedChanges;
        },
        handleBeforeUnload,
        initializeUnsavedChangesWarning,
        markUnsavedChanges,
        setHasUnsavedChanges: function (value) {
            hasUnsavedChanges = value;
        },
    };
}
