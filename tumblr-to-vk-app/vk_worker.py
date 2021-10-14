from threading import Thread
import vk_api
import datetime
import time
import random
from collections import defaultdict


class VkWorker(Thread):
    def __init__(self, group_id, user_access_token, db_conn, empty_picker_queue, files_folder, user_id):
        super().__init__()
        self.group_id = group_id
        self.db_conn = db_conn
        vk_session = vk_api.VkApi(token=user_access_token, app_id=group_id)
        self.vk_methods = vk_session.get_api()
        self.upload = vk_api.VkUpload(vk_session)
        self.empty_picker_queue = empty_picker_queue
        self.files_folder = files_folder
        self.user_id = user_id

    def get_last_postponed_time(self):
        # ограничение по постам
        postponed_posts = self.vk_methods.wall.get(owner_id=-self.group_id,
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

    def server_upload(self, photo_path):
        dict_uploaded_files = {}
        gif_to_upload = []
        photo_to_upload = []
        for photo in photo_path:
            photo_type = photo.split(".")[-1]
            if photo_type in ["gif"]:
                gif_to_upload.append(photo)
            elif photo_type in ["jpg", "png", "jpeg"]:
                photo_to_upload.append(photo)

        print(f"gif_to_upload {gif_to_upload}\n"
              f" photo_to_upload {photo_to_upload}")
        if gif_to_upload:
            print("это гифка")
            dict_uploaded_files["gif"] = self.upload.document(doc=gif_to_upload)
        elif photo_to_upload:
            dict_uploaded_files["photo"] = self.upload.photo_wall(photos=photo_to_upload,
                                                                  group_id=self.group_id
                                                                  )
        return dict_uploaded_files

    def make_attachments(self, dict_uploaded_files):
        atcms_gif = []
        atcms_photo = []
        if "gif" in dict_uploaded_files:
            doc = dict_uploaded_files["gif"]["doc"]
            file_type = "doc"
            atcms_gif = [f"{file_type}{str(doc['owner_id'])}_{str(doc['id'])}"]
        elif "photo" in dict_uploaded_files:
            file_type = "photo"
            atcms_photo = [f"{file_type}{str(photo['owner_id'])}_{str(photo['id'])}" for photo in
                           dict_uploaded_files["photo"]]
        atcms_all = atcms_gif + atcms_photo
        print(f"atcms_all {atcms_all}")

        return ','.join(atcms_all)

    def calc_publish_date(self):
        last_post_time = self.get_last_postponed_time()
        delta_published_time = datetime.timedelta(minutes=random.randint(40, 75))
        if last_post_time is None:
            publish_time = datetime.datetime.now() + delta_published_time
        else:
            publish_time = last_post_time + delta_published_time
        if 23 > publish_time.hour > 9:
            publish_time_unix = int(time.mktime((publish_time.timetuple())))
        else:
            if publish_time.hour == 23:
                publish_time = publish_time + datetime.timedelta(days=1)
            first_time = datetime.time(hour=9, minute=random.randint(0, 39))
            publish_time = datetime.datetime.combine(publish_time, first_time)
            publish_time_unix = int(time.mktime((publish_time.timetuple())))
        publish_date_human = str(publish_time.date())

        return {"publish_time_unix": publish_time_unix, "publish_date_human": publish_date_human}

    def post_publish(self, atcms, publish_date_unix, blog_name, source_url):
        owner_id = -self.group_id
        if blog_name in ["dankmemeuniversity"]:
            self.vk_methods.wall.post(owner_id=owner_id,
                                      from_group=True,
                                      attachments=atcms,
                                      publish_date=publish_date_unix,
                                      copyright=source_url
                                      )
        else:
            self.vk_methods.wall.post(owner_id=owner_id,
                                      from_group=True,
                                      attachments=atcms,
                                      publish_date=publish_date_unix,
                                      )

    def queue_picker(self):
        blog_posted_daily_counter = defaultdict(int)
        all_posted_posts = defaultdict(int)
        posts_queue = [doc for doc in self.db_conn.daily_posts_queue_publish(False)]

        if not posts_queue:
            print("Нет постов для публикации =(")
            return False

        posts_published = [doc for doc in self.db_conn.daily_posts_queue_publish(True)]
        for post in posts_published:
            all_posted_posts[post["blog_name"]] += 1
        print(f"Опубликованные посты {all_posted_posts}")

        for post in posts_queue:
            blog_posted_daily_counter[post["blog_name"]] += 1
        print(f"Посты ожидающие публикации {blog_posted_daily_counter}")

        # dice = random.randint(1, 2)
        # if dice == 1:
        #     randomize_cho = max
        # else:
        #     randomize_cho = min

        post_to_public = {}
        while not post_to_public:
            blog_name_already_posted = min(all_posted_posts, key=all_posted_posts.get)
            if blog_name_already_posted in blog_posted_daily_counter:
                #blog_name_to_public = randomize_cho(blog_posted_daily_counter, key=blog_posted_daily_counter.get)
                #searching_post = {"published": False, "blog_name": blog_name_to_public}
                searching_post = {"published": False, "blog_name": blog_name_already_posted}
                post_to_public = self.db_conn.post_getter(searching_post)
            else:
                all_posted_posts.pop(blog_name_already_posted)

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
                publish_date = self.calc_publish_date()
                print("берем пост из очереди")
                while post_data is False:
                    post_data = self.queue_picker()
                source_url = post_data["source_url"]
                blog_name = post_data["blog_name"]
                print("загружаем фото")
                dict_uploaded_files = self.server_upload(post_data["photo_path"])
                print(f"загруженные фото {dict_uploaded_files}")
                print("make attacms")
                atcms = self.make_attachments(dict_uploaded_files)
                print("публикуем пост")
                self.post_publish(atcms, publish_date["publish_time_unix"], blog_name, source_url)
                print("Пост опубликован")
                self.db_conn.post_updater(post_data["post_id"], publish_date["publish_date_human"])
                print("ожидаем след поста")
                time.sleep(3600)
            except BaseException as ex:
                print(f"Ошибка в треде vk_workers {ex}")
                print("Пропускаем пост")
                self.db_conn.post_updater(post_data["post_id"],
                                          publish_date["publish_date_human"],
                                          status="Failed")
