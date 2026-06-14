let clearUnsavedChanges;
let deleteTicket;
let getHasUnsavedChanges;
let handleBeforeUnload;
let initializeUnsavedChangesWarning;
let setHasUnsavedChanges;

function loadIndexModule() {
    jest.resetModules();
    global.confirm = jest.fn();
    global.fetch = jest.fn();
    global.alert = jest.fn();
    global.console = { error: jest.fn() };
    global.document = {
        querySelector: jest.fn(() => ({ getAttribute: jest.fn(() => 'test-csrf-token') })),
        querySelectorAll: jest.fn(() => []),
    };
    global.window = {
        addEventListener: jest.fn(),
        location: { reload: jest.fn() },
        onbeforeunload: null,
    };

    ({
        clearUnsavedChanges,
        deleteTicket,
        getHasUnsavedChanges,
        handleBeforeUnload,
        initializeUnsavedChangesWarning,
        setHasUnsavedChanges,
    } = require('./index.js'));
}

describe('deleteTicket', () => {
    beforeEach(() => {
        loadIndexModule();
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
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': 'test-csrf-token',
            },
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
        let form;
        let modalForm;

        beforeEach(() => {
            loadIndexModule();
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
            document.querySelectorAll.mockReturnValue([form, modalForm]);
            initializeUnsavedChangesWarning();
        });

        it('should set hasUnsavedChanges to true when input is present', () => {
            expect(getHasUnsavedChanges()).toBe(false);
            form.inputCb();
            expect(getHasUnsavedChanges()).toBe(true);
        });

        it('should reset hasUnsavedChanges and remove onbeforeunload on submit', () => {
            form.inputCb();
            expect(getHasUnsavedChanges()).toBe(true);
            form.submitCb();
            expect(getHasUnsavedChanges()).toBe(false);
            expect(window.onbeforeunload).toBeNull();
            clearUnsavedChanges();
        });

        it('should not add listeners to forms inside modals', () => {
            expect(modalForm.addEventListener).not.toHaveBeenCalled();
        });

        it('should return warning message if hasUnsavedChanges is true', () => {
            setHasUnsavedChanges(true);
            const e = {};
            const result = handleBeforeUnload(e);
            expect(e.returnValue).toBe('You have unsaved changes. Are you sure you want to leave?');
            expect(result).toBe('You have unsaved changes. Are you sure you want to leave?');
        });

        it('should return undefined if hasUnsavedChanges is false', () => {
            setHasUnsavedChanges(false);
            const e = {};
            const result = handleBeforeUnload(e);
            expect(e.returnValue).toBeUndefined();
            expect(result).toBeUndefined();
        });
    });
});