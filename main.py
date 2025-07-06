# main.py
# Entry point for the Flask application: creates the app instance and runs Flask server
from helpdeskapp import create_app

app = create_app()

if __name__ == '__main__':
    # Debug mode is ON for development. Turn OFF in production for security.
    app.run(debug=True)
