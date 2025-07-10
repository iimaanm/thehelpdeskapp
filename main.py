# Entry point for the Flask application: creates the app instance and runs Flask server
from helpdeskapp import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False)
