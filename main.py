from helpdeskapp import create_app

app = create_app()

if __name__ == '__main__':
    # Turn OFF in production
    app.run(debug=True)
