from threading import Thread
import vk_api
import datetime
import time
import random
from collections import defaultdict


class VkWorker(Thread):
    def __init__(self, group_id, user_access_token, db_conn, empty_picker_queue, files_folder):
        super().__init__()
        self.group_id = group_id
        self.db_conn = db_conn
        vk_session = vk_api.VkApi(token=user_access_token, app_id=group_id)
        self.vk_methods = vk_session.get_api()
        self.upload = vk_api.VkUpload(vk_session)
        self.empty_picker_queue = empty_picker_queue
        self.files_folder = files_folder

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

    # def server_upload(self, photo_path):
    #     dict_uploaded_files = {"gif": [], "photo": []}
    #     try:
    #         for photo in photo_path:
    #             photo_type = photo.split(".")[-1]
    #             if photo_type in ["gif"]:
    #                 vk_server_gif = self.upload.photo_wall(photos=photo_path,
    #                                                        )
    #                 dict_uploaded_files["gif"].append(vk_server_gif)
    #             elif photo_type in ["jpg", "png", "jpeg"]:
    #                 vk_server_photo = self.upload.photo_wall(photos=photo_path,
    #                                                          group_id=self.group_id
    #                                                          )
    #                 dict_uploaded_files["photo"].append(vk_server_photo)
    #     except BaseException as ex:
    #         raise f"Ошибка при загрузке фото {ex}"
    #
    #     return dict_uploaded_files

    def server_upload(self, photo_path):
        try:
            # for photo in
            # vk_server_gif = self.upload.photo_wall(photos=photo_path,
            #                                        )
            vk_server_photo = self.upload.photo_wall(photos=photo_path,
                                                     group_id=self.group_id
                                                     )
        except BaseException as ex:
            raise f"Ошибка при загрузке фото {ex}"

        return vk_server_photo

    # def make_attachments(self, dict_uploaded_files):
    #     atcms_gif = []
    #     atcms_photo = []
    #     if dict_uploaded_files["gif"]:
    #         file_type = "gif"
    #         atcms_gif = [f"{file_type}{str(photo['owner_id'])}_{str(photo['id'])}" for photo in
    #                  dict_uploaded_files[file_type]]
    #     elif dict_uploaded_files["photo"]:
    #         file_type = "photo"
    #         atcms_photo = [f"{file_type}{str(photo['owner_id'])}_{str(photo['id'])}" for photo in
    #                  dict_uploaded_files[file_type]]
    #     atcms_all = atcms_gif + atcms_photo
    #
    #     return ','.join(atcms_all)

    def make_attachments(self, uploaded_photo):
        atcms = [f"photo{str(photo['owner_id'])}_{str(photo['id'])}" for photo in uploaded_photo]
        return ','.join(atcms)

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

    def post_publish(self, atcms, publish_date_unix):
        self.vk_methods.wall.post(owner_id=-self.group_id,
                                  from_group=True,
                                  attachments=atcms,
                                  publish_date=publish_date_unix
                                  )

    def queue_picker(self):
        blog_posted_daily_counter = defaultdict(int)
        posts_queue = [doc for doc in self.db_conn.daily_posts_queue_publish()]

        if not posts_queue:
            self.empty_picker_queue.put(True)

            return False

        for post in posts_queue:
            blog_posted_daily_counter[post["blog_name"]] += 1
        dice = random.randint(1, 2)
        if dice == 1:
            randomize_cho = max
        else:
            randomize_cho = min
        blog_name_to_public = randomize_cho(blog_posted_daily_counter, key=blog_posted_daily_counter.get)
        searching_post = {"published": False, "blog_name": blog_name_to_public}

        post_to_public = self.db_conn.post_getter(searching_post)

        photo_path = []
        for img in post_to_public["photos"]:
            photo = f"{self.files_folder}/" \
                    f"{post_to_public['blog_name']}/" \
                    f"{post_to_public['post_id']}/" \
                    f"{img}"
            photo_path.append(photo)
        print(photo_path)

        return {"post_id": post_to_public["post_id"], "photo_path": photo_path}

    def start(self):
        while True:
            try:
                post_data = False
                publish_date = self.calc_publish_date()
                print("берем пост из очереди")
                while post_data is False:
                    post_data = self.queue_picker()
                print("загружаем фото")
                uploaded_photo = self.server_upload(post_data["photo_path"])
                print(f"загруженные фото {uploaded_photo}")
                print("make attacms")
                atcms = self.make_attachments(uploaded_photo)
                # dict_uploaded_files = self.server_upload(post_data["photo_path"])
                # print(f"загруженные фото {dict_uploaded_files}")
                # print("make attacms")
                # atcms = self.make_attachments(dict_uploaded_files)
                print("публикуем пост")
                self.post_publish(atcms, publish_date["publish_time_unix"])
                self.db_conn.post_updater(post_data["post_id"], publish_date["publish_date_human"])
                time.sleep(1800)
            except BaseException as ex:
                print(f"Ошибка в треде vk_workers {ex}")
                print("Пропускаем пост")
                self.db_conn.post_updater(post_data["post_id"],
                                          publish_date["publish_date_human"],
                                          status="Failed")
