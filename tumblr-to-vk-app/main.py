from config import Config
from db_client import DbConn
from tumblr_worker import TumblrWorker
from vk_worker import VkWorker
import queue

if __name__ == "__main__":
    print("get configs")
    config = Config()
    print("start db init")
    db_worker = DbConn(db_user=config.db_user,
                       db_password=config.db_password,
                       connection_string=config.connection_string)
    print(f"db init success {db_worker.tumblr_db}")
    empty_picker_queue = queue.Queue()
    tumblr_worker = TumblrWorker(db_worker,
                                 empty_picker_queue,
                                 config.consumer_key,
                                 config.consumer_secret,
                                 config.oauth_token,
                                 config.oauth_secret,
                                 config.files_folder)
    tumblr_worker.start()
    print(f"tumblr_worker started")
    vk_worker = VkWorker(config.group_id, config.user_access_token, db_worker, empty_picker_queue, config.files_folder)
    print(f"vk_worker starting")
    vk_worker.start()
    print(f"vk_worker started")
