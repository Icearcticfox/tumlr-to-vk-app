from config import Config
from db_client import DbConn
from tumblr_worker import TumblrWorker
from vk_worker import VkWorker, PostsPublisher

if __name__ == "__main__":
    config = Config()
    db_worker = DbConn(db_user=config.db_user,
                       db_password=config.db_password,
                       connection_string=config.connection_string)
    print(f"db init success {db_worker.tumblr_db}")

    tumblr_worker = TumblrWorker(db_worker,
                                 config.consumer_key,
                                 config.consumer_secret,
                                 config.oauth_token,
                                 config.oauth_secret,
                                 config.files_folder)
    tumblr_worker.start()
    print(f"tumblr_worker started")
    post_publisher = PostsPublisher(config.user_access_token,
                                    config.group_id,
                                    config.user_id,
                                    db_worker)
    vk_worker = VkWorker(config.group_id,
                         db_worker,
                         config.files_folder,
                         post_publisher)
    vk_worker.start()
    print(f"vk_worker started")
