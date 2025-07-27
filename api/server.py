from flask import Flask
from api.routes import bp as dashboard_bp

app = Flask(__name__)
app.register_blueprint(dashboard_bp)

if __name__ == "__main__":
    app.run(debug=True)
