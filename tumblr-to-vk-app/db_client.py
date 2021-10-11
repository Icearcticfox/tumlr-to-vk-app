from pymongo import MongoClient
import datetime


class DbConn:

    def __init__(self, db_name=None, collection_name=None, connection_string=None):
        self.CONNECTION_STRING = connection_string
        self.CONNECTION_STRING = "mongo:27017"
        self.client = MongoClient(self.CONNECTION_STRING)
        if db_name is None:
            db_name = "tumblr"
        self.tumblr_db = self.client.get_database(db_name)
        print(self.tumblr_db)
        if collection_name is None:
            collection_name = "posts"
        self.tumblr_posts_collection = self.tumblr_db.get_collection(collection_name)
        print(self.tumblr_posts_collection)

    def post_adder(self, blog_name, post_id, photos):
        published = False
        #datetime.datetime.now()
        if not self.tumblr_posts_collection.find_one({"post_id": post_id}):
            try:
                if [photo for photo in photos if photo.split(".")[-1] in ["gif"]]:
                    published = "Failed"
                self.tumblr_posts_collection.insert_one({"post_id": post_id, "published": published,
                                                         "blog_name": blog_name, "photos": photos})
            except Exception as ex:
                print(ex)

    def post_getter(self, view_):
        post = self.tumblr_posts_collection.find_one(view_)
        return post

    def daily_posts_published(self, publish_date):
        all_public_daily = self.tumblr_posts_collection.find({"published": True, "publish_date": publish_date}).sort({'_id': -1}).limit()
        return all_public_daily

    def post_updater(self, post_id, publish_date, status=True):
        self.tumblr_posts_collection.update_one({"post_id": post_id}, {"$set": {"published": status}},
                                                {"publish_date": publish_date})

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
