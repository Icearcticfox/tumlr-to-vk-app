import datetime

from pymongo import MongoClient


class DbConn:

    def __init__(self, db_user, db_password, db_name=None, collection_name=None, connection_string=None):
        self.db_user = db_user
        self.db_password = db_password
        if connection_string is None:
            connection_string = "mongo:27017"
        self.CONNECTION_STRING = connection_string
        self.client = MongoClient(f"mongodb://{self.db_user}:{self.db_password}@{self.CONNECTION_STRING}")
        if db_name is None:
            db_name = "tumblr"
        self.tumblr_db = self.client.get_database(db_name)
        print(self.tumblr_db)
        if collection_name is None:
            collection_name = "posts"
        self.tumblr_posts_collection = self.tumblr_db.get_collection(collection_name)
        print(self.tumblr_posts_collection)

    def post_adder(self, blog_name, post_id, photos, source_url):
        published = False
        add_date = str(datetime.datetime.now().date())
        if not self.tumblr_posts_collection.find_one({"post_id": post_id}):
            try:
                self.tumblr_posts_collection.insert_one({"post_id": post_id, "published": published,
                                                         "blog_name": blog_name, "photos": photos,
                                                         "source_url": source_url, "date_add": add_date})
            except Exception as ex:
                print(ex)

    def post_getter(self, view_):
        post = self.tumblr_posts_collection.find_one(view_)
        return post

    def daily_posts_queue_publish(self, published):
        all_public_daily = self.tumblr_posts_collection.find({"published": published})
        return all_public_daily

    def post_updater(self, post_id, publish_date=None, status=True):
        self.tumblr_posts_collection.update_one({"post_id": post_id}, {"$set": {"published": status,
                                                "publish_date": publish_date}})

        # Provide the mongodb atlas url to connect python to mongodb using pymongo
        #CONNECTION_STRING = "mongodb+srv://<username>:<password>@<cluster-name>.mongodb.net/myFirstDatabase"

        # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
        #tumblr_posts_collection = tumblr_db.get_collection("posts")
        #tumblr_posts_collection.insert_one({"_id": 123, "Test": "Test"})
        #print(tumblr_db.list_collection_names())
        #.create_collection("posts"))

        # Create the database for our example (we will use the same database throughout the tutorial
        #return client['user_shopping_list']


# This is added so that many files can reuse the function get_database()
    # Get the database
