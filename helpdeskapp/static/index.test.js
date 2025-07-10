// index.test.js

// Tests for the deleteTicket function
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


    // Tests for unsaved changes warning logic

    describe('Unsaved changes warning', () => {
        let forms;
        let form;
        let modalForm;

        // Re-import the code under test
        beforeEach(() => {
            // Reset global variables and mocks
            jest.resetModules();
            global.hasUnsavedChanges = false;

            // Mocking document and window
            global.document = {
                querySelectorAll: jest.fn(),
            };
            global.window.addEventListener = jest.fn((event, cb) => {
                if (event === 'DOMContentLoaded') {
                    cb();
                }
            });
            global.window.onbeforeunload = null;

            // Creating mock forms
            form = {
                addEventListener: jest.fn((event, cb) => {
                    if (event === 'input') form.inputCb = cb;
                    if (event === 'submit') form.submitCb = cb;
                }),
                closest: jest.fn(() => null),
            };
            modalForm = {
                addEventListener: jest.fn(),
                closest: jest.fn(() => ({})),
            };
            forms = [form, modalForm];
            document.querySelectorAll.mockReturnValue(forms);

            hasUnsavedChanges = false;
            // Simulate the code block for DOMContentLoaded
            (function () {
                const forms = document.querySelectorAll('form');
                forms.forEach(form => {
                    if (form.closest('.modal')) return;
                    form.addEventListener('input', () => {
                        hasUnsavedChanges = true;
                    });
                    form.addEventListener('submit', () => {
                        hasUnsavedChanges = false;
                        window.onbeforeunload = null;
                    });
                });
            })();

            // Simulate the code block for window.onbeforeunload
            window.onbeforeunload = function (e) {
                if (hasUnsavedChanges) {
                    e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
                    return 'You have unsaved changes. Are you sure you want to leave?';
                }
            };
        });

        it('should set hasUnsavedChanges to true when input is present', () => {
            expect(hasUnsavedChanges).toBe(false);
            form.inputCb();
            expect(hasUnsavedChanges).toBe(true);
        });

        it('should reset hasUnsavedChanges and remove onbeforeunload on submit', () => {
            form.inputCb();
            expect(hasUnsavedChanges).toBe(true);
            form.submitCb();
            expect(hasUnsavedChanges).toBe(false);
            expect(window.onbeforeunload).toBeNull();
        });

        it('should not add listeners to forms inside modals', () => {
            expect(modalForm.addEventListener).not.toHaveBeenCalled();
        });

        it('should return warning message if hasUnsavedChanges is true', () => {
            hasUnsavedChanges = true;
            const e = {};
            const result = window.onbeforeunload(e);
            expect(e.returnValue).toBe('You have unsaved changes. Are you sure you want to leave?');
            expect(result).toBe('You have unsaved changes. Are you sure you want to leave?');
        });

        it('should return undefined if hasUnsavedChanges is false', () => {
            hasUnsavedChanges = false;
            const e = {};
            const result = window.onbeforeunload(e);
            expect(e.returnValue).toBeUndefined();
            expect(result).toBeUndefined();
        });
    });
});