from flask import Flask, render_template, request, redirect, url_for, send_from_directory, g
import sqlite3
import re
import os
from datetime import datetime
import json
from markdown import markdown
from urllib.parse import urlencode
from urllib.parse import quote_plus
import pandas as pd
import numpy as np

# Functions

# Extract postcode from address
def extract_postcode(address):
    postcode_search = re.search(r'\b(\d{4})\b', address)
    return postcode_search.group(1) if postcode_search else None

# function that generates the search page URL and includes the existing query parameters
def get_url_with_params(endpoint, **kwargs):
    args = request.args.to_dict()  # Create a mutable copy of request.args
    args.update(kwargs)
    return url_for(endpoint, **args)

# Function to calculate value scores
def calculate_value_scores(listings):
    df = pd.DataFrame(listings)

    # Calculate counts per suburb
    count_per_suburb = df['suburb'].value_counts()

    # Convert price column to numeric, handling non-numeric values as NaN
    df['price'] = pd.to_numeric(df['price'], errors='coerce')

    avg_price_per_suburb = df.groupby('suburb')['price'].mean()
    avg_score_per_suburb = df.groupby('suburb')['greatness_score'].mean()

    df['price_diff'] = df.apply(lambda row: row['price'] - avg_price_per_suburb[row['suburb']], axis=1)
    df['score_diff'] = df.apply(lambda row: row['greatness_score'] - avg_score_per_suburb[row['suburb']], axis=1)

    # Calculate price_diff_norm and score_diff_norm by adding a small positive constant to avoid division by zero
    df['price_diff_norm'] = (df['price_diff'] - df['price_diff'].min() + 0.01) / (df['price_diff'].max() - df['price_diff'].min() + 0.01)
    df['score_diff_norm'] = (df['score_diff'] - df['score_diff'].min() + 0.01) / (df['score_diff'].max() - df['score_diff'].min() + 0.01)

    # Calculate the inverse of price_diff_norm
    df['price_diff_inverse'] = 1 / df['price_diff_norm']

    # Calculate the value_score
    df['value_score'] = df.apply(lambda row: (row['price_diff_inverse'] * row['score_diff_norm'])
                                if count_per_suburb[row['suburb']] >= 5 and np.isfinite(row['price'])
                                else np.nan,
                                axis=1)

    # Compute percentiles
    df['value_score_percentile'] = df['value_score'].dropna().rank(pct=True).apply(lambda x: round(x * 100))

    return df.to_dict('records')

# Define app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

app.jinja_env.filters['urlencode'] = quote_plus
app.jinja_env.globals.update(get_url_with_params=get_url_with_params)


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('listings.db')
        g.db.row_factory = sqlite3.Row

        cursor = g.db.cursor()

        cursor.execute("SELECT * FROM listings")
        listings = [dict(row) for row in cursor.fetchall()]
        value_scores = calculate_value_scores(listings) 

        # Iterate over each listing and update value_score in the database
        for item in value_scores:
            cursor.execute("UPDATE listings SET value_score = ?, value_score_percentile = ? WHERE id = ?", (item['value_score'], item['value_score_percentile'], item['id']))

        g.db.commit()
        
    return g.db




# Close the database connection
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()



# Custom Jinja filter to format date and time
@app.template_filter('format_datetime')
def format_datetime(value, format='%B %d, %Y at %H.%M'):
    """Format a date time to (Default): 'June 19, 2023 at 20.00'"""
    if value is None:
        return ""
    return datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f').strftime(format)

# Parse Markdown text from description
@app.template_filter('markdown')
def render_markdown(markdown_text):
    """Render Markdown text to HTML."""
    return markdown(markdown_text)

# Home page
@app.route('/')
def index():
    # Connect to the database and get the most recent 'date_added'
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(date_added) as last_scraped_date FROM listings")
        last_scraped_date = cursor.fetchone()['last_scraped_date']

        # Fetch the 5 latest listings
        cursor.execute("SELECT * FROM listings ORDER BY date_added DESC LIMIT 10")
        latest_listings = cursor.fetchall()

        # Fetch some statistics
        cursor.execute("SELECT COUNT(*) as total_listings, ROUND(AVG(price), 2) as avg_price, ROUND(AVG(greatness_score), 2) as avg_greatness_score, ROUND(AVG(value_score), 2) as avg_value_score, ROUND(MAX(value_score), 2) as max_value_score FROM listings")
        stats = cursor.fetchone()

        # Fetch the suburb with the highest average greatness_score
        cursor.execute("SELECT suburb, ROUND(AVG(greatness_score),2) as avg_greatness FROM listings GROUP BY suburb ORDER BY avg_greatness DESC LIMIT 1")
        top_suburb = cursor.fetchone()

        # Fetch the suburb with the most listings
        cursor.execute("SELECT suburb, COUNT(*) as listing_count FROM listings GROUP BY suburb ORDER BY listing_count DESC LIMIT 1")
        most_listings_suburb = cursor.fetchone()

        # Fetch the suburb with the highest average price
        cursor.execute("SELECT suburb, ROUND(AVG(price),2) as avg_price_suburb FROM listings GROUP BY suburb ORDER BY avg_price_suburb DESC LIMIT 1")
        most_expensive_suburb = cursor.fetchone()


    return render_template('index.html', last_scraped_date=last_scraped_date, latest_listings=latest_listings, stats=stats, top_suburb=top_suburb, most_listings_suburb=most_listings_suburb, most_expensive_suburb=most_expensive_suburb)

# Custom Jinja filter to check if a file exists
@app.template_filter('check_file_exists')
def check_file_exists(file_path):
    return os.path.isfile(file_path)

# Search listings
@app.route('/search', methods=['GET', 'POST'])
def search():
    page = request.args.get('page', 1, type=int)
    if page == "":
        page = 1
    query = ""
    listings = []  # Initialize empty list for listings
    searched = False  # Initialize as False, change to True when a search is performed
    per_page = 10
    params = []
    form_data = {}

    # Check for reset action
    if 'reset' in request.form:
        return redirect(url_for('search'))

    # Get suburbs from form
    suburbs = request.args.getlist('suburbs') if request.args.get('suburbs') else []
    
    if request.method == 'GET':
        form_data = request.args.to_dict()
        searched = True  # Set searched to True as a search is being performed

        # Retrieve search criteria from the form
        keyword = request.args.get('keyword')
        address = request.args.get('address')
        bedrooms = request.args.get('bedrooms')
        bathrooms = request.args.get('bathrooms')
        min_price = request.args.get('min_price')
        max_price = request.args.get('max_price')
        min_score = request.args.get('min_score')
        max_score = request.args.get('max_score')
        ranking = request.args.get('ranking')

        # Retrieve date range from the form
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Split keyword into individual terms
        terms = re.split(r'\s+(?=(?:[^\']*\'[^\']*\')*[^\']*$)', keyword) if keyword else ['']

        # Retrieve selected keywords
        keywords = request.args.getlist('keywords')

        # Construct the SQL query based on the search criteria
        query = "SELECT * FROM listings WHERE ("

        # Add conditions for each term using boolean operators
        for i, term in enumerate(terms):
            if i > 0:
                query += " AND "
            query += "(description LIKE ? OR features LIKE ?)"
            params.extend(['%' + term + '%', '%' + term + '%'])

        query += ") AND address LIKE ?"
        params.append('%' + (address if address else '') + '%')

        # Add conditions for selected keywords
        if keywords:
            keyword_conditions = []
            for keyword in keywords:
                keyword_conditions.append("(description LIKE ? OR features LIKE ?)")
                params.extend(['%' + keyword + '%', '%' + keyword + '%'])
            query += " AND " + " AND ".join(keyword_conditions)

        # Add additional filters if provided
        if bedrooms:
            query += " AND bedrooms = ?"
            params.append(bedrooms if bedrooms else '')
        if bathrooms:
            query += " AND bathrooms = ?"
            params.append(bathrooms if bathrooms else '')
        
        # Add conditions for selected suburbs
        if suburbs:
            suburb_conditions = []
            for suburb in suburbs:
                suburb_conditions.append("suburb = ?")
                params.append(suburb)
            query += " AND (" + " OR ".join(suburb_conditions) + ")"

        # Add conditions for price range and greatness_score range

        if min_price:
            query += " AND price >= ?"
            params.append(min_price if min_price else '')
        if max_price:
            query += " AND price <= ?"
            params.append(max_price if max_price else '')
        if min_score:
            query += " AND greatness_score >= ?"
            params.append(min_score if min_score else '')
        if max_score:
            query += " AND greatness_score <= ?"
            params.append(max_score if max_score else '')

        # Add conditions for date range if provided
        if start_date:
            query += " AND date_added >= ?"
            params.append(start_date if start_date else '')
        if end_date:
            query += " AND date_added <= ?"
            params.append(end_date if end_date else '')

        # Add ORDER BY clause for ranking
        if ranking == 'price_asc':
            query += " ORDER BY price"
        elif ranking == 'price_desc':
            query += " ORDER BY price DESC"
        elif ranking == 'date_asc':
            query += " ORDER BY date_added"
        elif ranking == 'date_desc':
            query += " ORDER BY date_added DESC"
        elif ranking == 'greatness_asc':
            query += " ORDER BY greatness_score"
        elif ranking == 'greatness_desc':
            query += " ORDER BY greatness_score DESC"
        elif ranking == 'value_asc':  # Add this condition
            query += " ORDER BY value_score"
        elif ranking == 'value_desc':  # Add this condition
            query += " ORDER BY value_score DESC"

        # Add LIMIT and OFFSET to your query
        offset = (page - 1) * per_page
        query += " LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

    # Get unique suburbs and their corresponding counts
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT suburb, COUNT(*) as count FROM listings GROUP BY suburb ORDER BY count DESC")
        unique_suburbs = [row['suburb'] for row in cursor.fetchall()]

    # Execute the query and fetch the listings only when a search is made
    cursor = get_db().cursor()

    # Execute the query and fetch the listings only when a search is made
    if query:  # Add this condition
        cursor.execute(query, params)
        listings = cursor.fetchall()  # Fetch the listings
    else:
        cursor.execute("SELECT * FROM listings")
        listings = cursor.fetchall()  # Fetch all listings
        
    # Convert sqlite3.Row objects to dictionaries
    listings = [dict(row) for row in listings]

    # Calculate the total number of pages
    total_listings = 0
    total_pages = 0

    if query:  # Add this condition
        count_query = query.replace("SELECT *", "SELECT COUNT(*)").rsplit("LIMIT", 1)[0]
        cursor.execute(count_query, params[:-2])
        result = cursor.fetchone()
        if result is not None:  # Add this condition to check for None
            total_listings = result[0]
        total_pages = max(1, ((total_listings - 1) // per_page) + 1)

    return render_template('search.html', listings=listings, query=request.form, unique_suburbs=unique_suburbs, suburbs=suburbs, searched=searched, page=page, per_page=per_page, total_pages=total_pages, form_data=form_data)

# Listing detail page
@app.route('/listing/<int:listing_id>')
def listing(listing_id):
    with get_db() as conn:
        query = "SELECT * FROM listings WHERE id=?"
        cursor = conn.cursor()
        cursor.execute(query, (listing_id,))
        listing = cursor.fetchone()

        postcode = extract_postcode(listing['address']) # Extract postcode from address

        cursor.execute("SELECT * FROM favorites WHERE listing_id = ?", (listing_id,))  # Check if listing is in favorites
        is_favorite = cursor.fetchone() is not None  # True if listing is in favorites, else False

        images_path = listing['images_path']
        images = []
        if os.path.isdir(images_path):
            images = [f for f in os.listdir(images_path) if os.path.isfile(os.path.join(images_path, f))]

        # Decode greatness_details into a Python dictionary
        greatness_details = json.loads(listing['greatness_details'])

    return render_template('listing.html', listing=listing, images=images, is_favorite=is_favorite, greatness_details=greatness_details, postcode=postcode)  

# Serve static images
@app.route('/<path:filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/add_to_favorites/<int:listing_id>', methods=['POST'])
def add_to_favorites(listing_id):
    positive_notes = request.form.get('positive_notes')  # Get positive notes from form data
    negative_notes = request.form.get('negative_notes')  # Get negative notes from form data
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM favorites WHERE listing_id = ?", (listing_id,))  # Check if listing is already in favorites
        if cursor.fetchone() is None:  # If listing is not in favorites
            cursor.execute("INSERT INTO favorites (listing_id, positive_notes, negative_notes) VALUES (?, ?, ?)",
                           (listing_id, positive_notes, negative_notes))  # Add listing to favorites
            conn.commit()
    return redirect(url_for('listing', listing_id=listing_id))

@app.route('/remove_from_favorites/<int:listing_id>', methods=['POST'])
def remove_from_favorites(listing_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM favorites WHERE listing_id = ?", (listing_id,))  # Remove listing from favorites
        conn.commit()
    return redirect(url_for('listing', listing_id=listing_id))  # Correct redirection to the listing route

@app.route('/favorites')
def favorites():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM favorites INNER JOIN listings ON favorites.listing_id = listings.id")
        favorite_listings = cursor.fetchall()
    return render_template('favorites.html', favorite_listings=favorite_listings)

# Suburbs page
@app.route('/suburbs', methods=['GET', 'POST'])
def suburbs():
    # Connect to the database and get the stats for each suburb
    with get_db() as conn:
        cursor = conn.cursor()

        # Fetch global averages
        cursor.execute("SELECT AVG(price) as global_avg_price, AVG(greatness_score) as global_avg_greatness_score FROM listings")
        global_avgs = cursor.fetchone()

        # Retrieve the selected sort order from the form data
        sort_order = request.form.get('sort_order') if request.method == 'POST' else 'suburb_asc'

        # Determine the ORDER BY clause of the SQL query based on the selected sort order
        if sort_order == 'price_asc':
            order_by_clause = "ORDER BY avg_price ASC"
        elif sort_order == 'price_desc':
            order_by_clause = "ORDER BY avg_price DESC"
        elif sort_order == 'greatness_asc':
            order_by_clause = "ORDER BY avg_greatness_score ASC"
        elif sort_order == 'greatness_desc':
            order_by_clause = "ORDER BY avg_greatness_score DESC"
        else:  # Default to sorting by suburb name in ascending order
            order_by_clause = "ORDER BY suburb ASC"

        cursor.execute(f"SELECT suburb, address, COUNT(*) as total_listings, AVG(price) as avg_price, AVG(greatness_score) as avg_greatness_score FROM listings GROUP BY suburb {order_by_clause}")

        suburb_stats_raw = cursor.fetchall()

    # Compute percentage differences and round them
    suburb_stats = []
    for stats in suburb_stats_raw:
        price_diff = round(((stats['avg_price'] - global_avgs['global_avg_price']) / global_avgs['global_avg_price'] * 100), 1)
        greatness_diff = round(((stats['avg_greatness_score'] - global_avgs['global_avg_greatness_score']) / global_avgs['global_avg_greatness_score'] * 100), 1)
        postcode = extract_postcode(stats['address']) # Extract postcode from address
        suburb_stats.append({
            'suburb': stats['suburb'],
            'total_listings': stats['total_listings'],
            'avg_price': round(stats['avg_price'],2),
            'avg_greatness_score': round(stats['avg_greatness_score'],2),
            'price_diff': price_diff,
            'greatness_diff': greatness_diff,
            'postcode': postcode
        })

    return render_template('suburbs.html', suburb_stats=suburb_stats, global_avgs=global_avgs, sort_order=sort_order)

if __name__ == '__main__':
    app.run(debug=True)