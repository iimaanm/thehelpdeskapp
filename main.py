# main.py
# Entry point for the Flask application. This file creates the app instance and runs the server.
from helpdeskapp import create_app

app = create_app()

if __name__ == '__main__':
    # Debug mode is ON for development. Turn OFF in production for security.
    app.run(debug=True)
