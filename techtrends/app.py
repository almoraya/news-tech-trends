from crypt import methods
import sqlite3
from urllib import response
import logging

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort


################################################################################################


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post


################################################################################################


## https://circleci.com/blog/application-logging-with-flask/#c-consent-modal
logging.basicConfig(
    #filename='app.log',
    level=logging.DEBUG,
    format='%(levelname)s   %(asctime)s   %(name)s  :   %(message)s  %(module)s'
)


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'


################################################################################################


# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    total_posts = len(posts)
    total_connections = posts[0][0]
    connection.close()
    app.logger.info("<<  Connection to database was successful!  >>")
    app.logger.info("<<  Fetching all current {} posts from database  >>".format(total_posts))
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.warning("<<  Article with post id {} does not exist yet!  >>".format(post_id))
        return render_template('404.html'), 404    
    else:
        articleTitle = post['title']
        app.logger.info("<<  Rendering article with post id {}.  >>".format(post_id))
        app.logger.info("<<  Article '{}' was correctly rendered.  >>".format(articleTitle))
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.debug("<<  The 'About Us' page was accessed.  >>")
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
            app.logger.warning("<<  An attempt to add an article without a title was recorded.  >>")
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            app.logger.info("<<  A new article with title {} was created.  >>".format(title))
            return redirect(url_for('index'))

    return render_template('create.html')


# Define a healthcheck endpoint /healthz
# and check health of db connection
@app.route('/healthz')
def healthz():

    try:
        connection = get_db_connection()
        posts = connection.execute('SELECT * FROM posts').fetchall()
        connection.close()
        response = app.response_class(
            response=json.dumps(
                {"result": "OK - healthy"}
            ),
            status=200,
            mimetype="application/json"
        )
    except:
        response = app.response_class(
            response=json.dumps(
                {"result": "Not OK - unhealthy"}
            ),
            status=500,
            mimetype="application/json"
        )

    app.logger.debug("Checking the health of db connection")

    return response


# Define a metrics endpoint
@app.route("/metrics")
def metrics():
    connection = get_db_connection()
    db = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    total_connections = db[0][0]
    total_posts = len(db)
    response=app.response_class(
        response=json.dumps(
            {
                "db_connection_count": total_connections,
                "post_count": total_posts
            }

        ),
        status=200,
        mimetype="application/json"
    )

    app.logger.debug("Following metrics were recorded: total connections = {} and total posts = {}".format(total_connections, total_posts))
    return response

################################################################################################


# start the application on port 3111
if __name__ == "__main__":
    app.run(host='0.0.0.0', port='3111')


    