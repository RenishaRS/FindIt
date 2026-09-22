from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename

from ai_matching import find_matches


app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = "uploads"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# =========================
# Database Setup
# =========================

def create_database():

    connection = sqlite3.connect("findit.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_type TEXT NOT NULL,
            item_name TEXT NOT NULL,
            location TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(items)")

    columns = [
        column[1]
        for column in cursor.fetchall()
    ]

    if "photo" not in columns:

        cursor.execute(
            "ALTER TABLE items ADD COLUMN photo TEXT"
        )

    if "status" not in columns:

        cursor.execute(
            "ALTER TABLE items ADD COLUMN status TEXT DEFAULT 'Active'"
        )

    connection.commit()
    connection.close()


create_database()


# =========================
# Home
# =========================

@app.route("/")
def home():

    return render_template("index.html")


# =========================
# Report Lost Item
# =========================

@app.route("/lost", methods=["GET", "POST"])
def lost():

    if request.method == "POST":

        item_name = request.form["item_name"]
        location = request.form["location"]
        date = request.form["date"]
        description = request.form["description"]

        photo = request.files.get("photo")
        photo_filename = None

        if photo and photo.filename:

            photo_filename = secure_filename(
                photo.filename
            )

            photo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    photo_filename
                )
            )

        connection = sqlite3.connect("findit.db")
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO items
            (
                item_type,
                item_name,
                location,
                date,
                description,
                photo,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Lost",
            item_name,
            location,
            date,
            description,
            photo_filename,
            "Active"
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("search"))

    return render_template("lost.html")


# =========================
# Report Found Item
# =========================

@app.route("/found", methods=["GET", "POST"])
def found():

    if request.method == "POST":

        item_name = request.form["item_name"]
        location = request.form["location"]
        date = request.form["date"]
        description = request.form["description"]

        photo = request.files.get("photo")
        photo_filename = None

        if photo and photo.filename:

            photo_filename = secure_filename(
                photo.filename
            )

            photo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    photo_filename
                )
            )

        connection = sqlite3.connect("findit.db")
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO items
            (
                item_type,
                item_name,
                location,
                date,
                description,
                photo,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Found",
            item_name,
            location,
            date,
            description,
            photo_filename,
            "Active"
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("search"))

    return render_template("found.html")


# =========================
# Uploaded Images
# =========================

@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# =========================
# Search
# =========================

@app.route("/search")
def search():

    search_text = request.args.get(
        "search",
        ""
    )

    item_type = request.args.get(
        "item_type",
        ""
    )

    connection = sqlite3.connect("findit.db")
    cursor = connection.cursor()

    query = """
        SELECT * FROM items
        WHERE (
            item_name LIKE ?
            OR location LIKE ?
            OR description LIKE ?
        )
    """

    parameters = [
        "%" + search_text + "%",
        "%" + search_text + "%",
        "%" + search_text + "%"
    ]

    if item_type:

        query += " AND item_type = ?"

        parameters.append(item_type)

    cursor.execute(
        query,
        parameters
    )

    items = cursor.fetchall()

    connection.close()

    return render_template(
        "search.html",
        items=items,
        search=search_text,
        item_type=item_type
    )


# =========================
# Item Details + AI Matching
# =========================

@app.route("/item/<int:item_id>")
def item_details(item_id):

    connection = sqlite3.connect("findit.db")
    cursor = connection.cursor()

    # Get selected item
    cursor.execute(
        "SELECT * FROM items WHERE id = ?",
        (item_id,)
    )

    item = cursor.fetchone()

    if item is None:

        connection.close()

        return "Item not found", 404


    # Only search for matches for LOST items
    if item[1] == "Lost":

        lost_item = {
            "item_name": item[2],
            "location": item[3],
            "description": item[5] or ""
        }


        # Get active FOUND items
        cursor.execute("""
            SELECT *
            FROM items
            WHERE item_type = 'Found'
            AND status = 'Active'
        """)

        found_rows = cursor.fetchall()

        found_items = []


        for found in found_rows:

            found_items.append({

                "id": found[0],

                "item_name": found[2],

                "location": found[3],

                "date": found[4],

                "description": found[5] or "",

                "photo": found[6],

                "status": found[7]

            })


        # Run AI matching
        matches = find_matches(
            lost_item,
            found_items,
            minimum_score=30
        )

    else:

        matches = []


    connection.close()


    return render_template(
        "item_details.html",
        item=item,
        matches=matches
    )


# =========================
# Claim Item
# =========================

@app.route(
    "/item/<int:item_id>/claim",
    methods=["POST"]
)
def claim_item(item_id):

    connection = sqlite3.connect("findit.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE items
        SET status = 'Claimed'
        WHERE id = ?
        """,
        (item_id,)
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for(
            "item_details",
            item_id=item_id
        )
    )


# =========================
# Run Application
# =========================

if __name__ == "__main__":

    app.run(debug=True)