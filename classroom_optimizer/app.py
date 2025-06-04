from flask import Flask, render_template, request, redirect, url_for
import json
from optimizer import optimize_classrooms

app = Flask(__name__)

# Load data files (adjust paths as needed)
with open("data/courses.json") as f:
    courses = json.load(f)

with open("data/rooms.json") as f:
    rooms = json.load(f)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Run optimization on the data loaded from JSON
        result = optimize_classrooms(courses, rooms)
        return render_template("index.html", result=result)
    return render_template("index.html", result=None)

if __name__ == "__main__":
    app.run(debug=True)
