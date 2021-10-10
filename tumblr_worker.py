import os
import time
import pytumblr
from urllib import request
from threading import Thread


class TumblrWorker(Thread):

    def __init__(self, db_client,
                 empty_picker_queue,
                 consumer_key,
                 consumer_secret,
                 oauth_token,
                 oauth_secret,
                 files_folder
                 ):
        super().__init__()
        self.client = pytumblr.TumblrRestClient(consumer_key=consumer_key,
                                                consumer_secret=consumer_secret,
                                                oauth_token=oauth_token,
                                                oauth_secret=oauth_secret)
        self.db_client = db_client
        self.empty_picker_queue = empty_picker_queue
        self.time_offset = 0
        self.files_folder = files_folder
        if self.files_folder is None:
            self.files_folder = "."

    def dashboard_post_image_saver(self, post):
        blog_name = post["blog_name"]
        post_id = post['trail'][0]["post"]['id']
        if self.db_client.post_getter({"post_id": post_id}) is None:
            photos = []
            if not os.path.isdir(f"{self.files_folder}/{blog_name}"):
                os.mkdir(f"{self.files_folder}/{blog_name}")
            if not os.path.isdir(f"{self.files_folder}/{blog_name}/{post_id}"):
                os.mkdir(f"{self.files_folder}/{blog_name}/{post_id}")
            for photo in post["photos"]:
                photo_name = photo['original_size']['url'].split('/')[-1]
                # if photo_name.split(".")[-1] in ["png", "jpg", jpeg]:
                request.urlretrieve(f"{photo['original_size']['url']}",
                                    f"{self.files_folder}/{blog_name}/{post_id}/"
                                    f"{photo_name}")
                photos.append(photo_name)
            self.db_client.post_adder(blog_name, post_id, photos)

            return True

    def dashboard_parser(self, dashboard):
        was_added = False
        for post in dashboard["posts"]:
            if post["type"] == "photo":
                if self.dashboard_post_image_saver(post):
                    was_added = True

        return was_added

    def dashboard_post_getter(self):

        """Получение постов с дашборда"""

        while True:
            if self.empty_picker_queue.get():
                self.time_offset += 2
            dashboard = self.client.dashboard(type="photo", offset=self.time_offset)

            if self.dashboard_parser(dashboard):
                self.time_offset = 0
                return True
            time.sleep(5)

    # def tag_image_getter(self):
    #
    #     """Получение постов по тегу"""
    #
    #     tags = self.client.tagged(tag="sweet")
    #     for post in tags:
    #         if post["type"] == "photo":
    #             if not os.path.isdir(f"./{post['blog_name']}"):
    #                 os.mkdir(f"{self.files_folder}/{post['blog_name']}")
    #             for photo in post["photos"]:
    #                 request.urlretrieve(f'{photo["original_size"]["url"]}',
    #                                     f'{self.files_folder}/{post["blog_name"]}/{photo["original_size"]["url"].split("/")[6]}')

    def run(self):
        while True:
            try:
                self.dashboard_post_getter()
                time.sleep(30)
            except Exception as ex:
                print(f"Ошибка в треде tumblr_workers {ex}")
