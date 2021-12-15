from threading import Thread
import vk_api
import datetime
import time
import random
from collections import defaultdict


class PostsPublisher:
    """
    Взаимодействие с апи вконтакте
    """

    def __init__(self, user_access_token, group_id, user_id, db_conn):
        self.owner_id = -group_id
        self.group_id = group_id
        vk_session = vk_api.VkApi(token=user_access_token, app_id=group_id)
        self.vk_methods = vk_session.get_api()
        self.user_id = user_id
        self.upload = vk_api.VkUpload(vk_session)
        self.db_conn = db_conn

    def get_last_postponed_time(self):
        # ограничение по постам
        postponed_posts = self.vk_methods.wall.get(owner_id=self.owner_id,
                                                   filter="postponed",
                                                   count=100
                                                   )
        if postponed_posts["count"] == 100:
            # TODO починить
            print("хватит пубиковать")
        if postponed_posts["count"] == 0:
            return datetime.datetime.now()
        last_time = max([post_time["date"] for post_time in postponed_posts["items"]])
        return datetime.datetime.fromtimestamp(last_time)

    def calc_publish_date(self):
        last_post_time = self.get_last_postponed_time()
        delta_published_time = datetime.timedelta(minutes=random.randint(40, 75))
        if last_post_time is None:
            publish_time = datetime.datetime.now() + delta_published_time
        else:
            publish_time = last_post_time + delta_published_time
        if 23 > publish_time.hour > 9:
            unix = int(time.mktime((publish_time.timetuple())))
        else:
            if publish_time.hour == 23:
                publish_time = publish_time + datetime.timedelta(days=1)
            first_time = datetime.time(hour=9, minute=random.randint(0, 39))
            publish_time = datetime.datetime.combine(publish_time, first_time)
            unix = int(time.mktime((publish_time.timetuple())))
        human = str(publish_time.date())

        return {"unix": unix, "human": human}

    def server_upload(self, photo_path):
        dict_uploaded_files = {}
        gif_to_upload = []
        photo_to_upload = []
        for photo in photo_path:
            photo_type = photo.split(".")[-1]
            if photo_type in ["gif"]:
                # TODO проверить почему публикуются по одной гифке, если их может быть много
                gif_to_upload.append(photo)
            elif photo_type in ["jpg", "png", "jpeg"]:
                photo_to_upload.append(photo)

        print(f"gif_to_upload {gif_to_upload}\n"
              f" photo_to_upload {photo_to_upload}")
        if gif_to_upload:
            print("это гифка")
            dict_uploaded_files["gif"] = [self.upload.document(doc=gif) for gif in gif_to_upload]
            # dict_uploaded_files["gif"] = self.upload.document(doc=gif_to_upload)
        elif photo_to_upload:
            dict_uploaded_files["photo"] = self.upload.photo_wall(photos=photo_to_upload,
                                                                  group_id=self.group_id
                                                                  )
        return dict_uploaded_files

    def make_attachments(self, photo_path):
        dict_uploaded_files = self.server_upload(photo_path)
        atcms_gif = []
        atcms_photo = []
        if "gif" in dict_uploaded_files:
            # doc = dict_uploaded_files["gif"]["doc"]
            file_type = "doc"
            atcms_gif = [f"{file_type}{str(gif['doc']['owner_id'])}_{str(gif['doc']['id'])}" for gif in
                         dict_uploaded_files["gif"]]
        elif "photo" in dict_uploaded_files:
            file_type = "photo"
            atcms_photo = [f"{file_type}{str(photo['owner_id'])}_{str(photo['id'])}" for photo in
                           dict_uploaded_files["photo"]]
        atcms_all = atcms_gif + atcms_photo
        print(f"atcms_all {atcms_all}")

        return ','.join(atcms_all)

    def post_publish(self, post_data):
        publish_date = self.calc_publish_date()
        atcms = self.make_attachments(post_data["photo_path"])
        source_url = post_data["source_url"]
        blog_name = post_data["blog_name"]

        if blog_name in ["dankmemeuniversity", "shitpostinguniverse"]:
            self.vk_methods.wall.post(owner_id=self.owner_id,
                                      from_group=True,
                                      attachments=atcms,
                                      publish_date=publish_date["unix"],
                                      copyright=source_url
                                      )
        else:
            self.vk_methods.wall.post(owner_id=self.owner_id,
                                      from_group=True,
                                      attachments=atcms,
                                      publish_date=publish_date["unix"],
                                      copyright=source_url
                                      )

        self.db_conn.post_updater(post_data["post_id"], publish_date["human"])

    def skip_post(self, post_data):
        self.db_conn.post_updater(post_data["post_id"],
                                  status="Failed")


class VkWorker(Thread):
    """
    Выборка и подготовка постов к публикации
    """

    def __init__(self, group_id, db_conn, files_folder, post_publisher):
        super().__init__()
        self.group_id = group_id
        self.db_conn = db_conn
        self.files_folder = files_folder
        self.post_publisher = post_publisher

    def search_by_blog_name(self, posted_posts_blog_name, awaiting_posts_blog_name):

        for blog_name in awaiting_posts_blog_name:
            if blog_name not in posted_posts_blog_name:
                return {"published": False, "blog_name": blog_name}

        blog_name_already_posted_min = min(posted_posts_blog_name, key=posted_posts_blog_name.get)
        if blog_name_already_posted_min in awaiting_posts_blog_name:
            return {"published": False, "blog_name": blog_name_already_posted_min}
        else:
            return {"published": False}

    def queue_picker(self):
        awaiting_posts_blog_name = defaultdict(int)
        posted_posts_blog_name = defaultdict(int)
        posts_queue = [doc for doc in self.db_conn.daily_posts_queue_publish(False)]

        if not posts_queue:
            print("Нет постов для публикации =(")
            return False

        posts_published = [doc for doc in self.db_conn.daily_posts_queue_publish(True)]
        for post in posts_published:
            posted_posts_blog_name[post["blog_name"]] += 1
        print(f"Опубликованные посты {posted_posts_blog_name}")

        for post in posts_queue:
            awaiting_posts_blog_name[post["blog_name"]] += 1
        print(f"Посты ожидающие публикации {awaiting_posts_blog_name}")

        post_to_public = self.db_conn.post_getter(self.search_by_blog_name(
            posted_posts_blog_name,
            awaiting_posts_blog_name
        ))

        photo_path = []
        for img in post_to_public["photos"]:
            photo = f"{self.files_folder}/" \
                    f"{post_to_public['blog_name']}/" \
                    f"{post_to_public['post_id']}/" \
                    f"{img}"
            photo_path.append(photo)
        print(photo_path)

        return {"post_id": post_to_public["post_id"],
                "photo_path": photo_path,
                "source_url": post_to_public["source_url"],
                "blog_name": post_to_public["blog_name"]}

    def start(self):
        while True:
            try:
                post_data = False
                print("берем пост из очереди")
                while post_data is False:
                    post_data = self.queue_picker()
                self.post_publisher.post_publish(post_data)
                print("ожидаем след поста")
                time.sleep(2400)
            except BaseException as ex:
                print(f"Ошибка в треде vk_workers {ex}")
                time.sleep(10)
                print("Пропускаем пост")
                self.post_publisher.skip_post(post_data)
