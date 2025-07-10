// index.test.js

// Mocking global functions and objects
global.confirm = jest.fn();
global.fetch = jest.fn();
global.alert = jest.fn();
global.window = { location: { reload: jest.fn() } };
global.console = { error: jest.fn() };

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

describe('deleteTicket', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should not call fetch if confirm is false', () => {
        confirm.mockReturnValue(false);
        deleteTicket(123);
        expect(fetch).not.toHaveBeenCalled();
    });

    it('should call fetch with correct parameters if confirm is true', () => {
        confirm.mockReturnValue(true);
        fetch.mockResolvedValue({ ok: true });
        deleteTicket(124);
        expect(fetch).toHaveBeenCalledWith('/delete-ticket', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticketId: 124 }),
        });
    });

    it('should reload window if response is ok', async () => {
        confirm.mockReturnValue(true);
        fetch.mockResolvedValue({ ok: true });
        await deleteTicket(789);
        // Waiting for promise chain
        await Promise.resolve();
        expect(window.location.reload).toHaveBeenCalled();
    });

    it('should alert with an error if response is not ok', async () => {
        confirm.mockReturnValue(true);
        fetch.mockResolvedValue({ ok: false });
        await deleteTicket(101);
        await Promise.resolve();
        expect(alert).toHaveBeenCalledWith('Error: Ticket could not be deleted');
    });

    it('should alert with an error if fetch throws', async () => {
        confirm.mockReturnValue(true);
        fetch.mockRejectedValue(new Error('Network error'));
        await deleteTicket(202);
        await Promise.resolve();
        expect(console.error).toHaveBeenCalled();
        expect(alert).toHaveBeenCalledWith('An unexpected error occurred');
    });
});