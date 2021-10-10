import os


class Config:

    def __init__(self):
        self.connection_string = os.getenv("CONNECTION_STRING")
        self.app_id = int(os.getenv("APP_ID"))
        self.app_secret_key = os.getenv("APP_SECRET_KEY")
        self.app_service_key = os.getenv("APP_SERVICE_KEY")
        self.group_secret = os.getenv("GROUP_SECRET")
        self.user_access_token = os.getenv("USER_ACCESS_TOKEN")
        self.group_id = int(os.getenv("GROUP_ID"))
        self.consumer_key = os.getenv("TUMBLR_CONSUMER_KEY")
        self.consumer_secret = os.getenv("TUMBLR_CONSUMER_SECRET")
        self.oauth_token = os.getenv("TUMBLR_OAUTH_TOKEN")
        self.oauth_secret = os.getenv("TUMBLR_OAUTH_SECRET")
        self.files_folder = os.getenv("FILES_FOLDER")
