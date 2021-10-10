from threading import Thread
import vk_api
import datetime
import time
import random


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

    def server_upload(self, photo_path):
        try:
            vk_server_photo = self.upload.photo_wall(photos=photo_path,
                                                     group_id=self.group_id
                                                     )
        except BaseException as ex:
            raise f"Ошибка при загрузке фото {ex}"

        return vk_server_photo

    def make_attachments(self, uploaded_photo):
        atcms = [f"photo{str(photo['owner_id'])}_{str(photo['id'])}" for photo in uploaded_photo]
        return ','.join(atcms)

    def calc_publish_date(self):
        last_post_time = self.get_last_postponed_time()
        delta_published_time = datetime.timedelta(minutes=random.randint(60, 100))
        if last_post_time is None:
            publish_date = datetime.datetime.now() + delta_published_time
        else:
            publish_date = last_post_time + delta_published_time
            publish_date_unix = int(time.mktime((publish_date.timetuple())))

            #return publish_date_unix

        if 23 > publish_date.hour > 9:
            publish_date_unix = int(time.mktime((publish_date.timetuple())))
        else:
            if publish_date.hour == 23:
                publish_date = publish_date + datetime.timedelta(days=1)
            first_time = datetime.time(hour=9, minute=random.randint(0, 59))
            publish_date = datetime.datetime.combine(publish_date, first_time)
            publish_date_unix = int(time.mktime((publish_date.timetuple())))

        return publish_date_unix

    def post_publish(self, atcms, publish_date_unix):
        self.vk_methods.wall.post(owner_id=-self.group_id,
                                  from_group=True,
                                  attachments=atcms,
                                  publish_date=publish_date_unix
                                  )

    def queue_picker(self):
        print("берем пост из очереди")
        post_to_public = self.db_conn.post_getter({"published": False})
        if post_to_public is None:
            self.empty_picker_queue.put(True)

            return False

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
                post_data = self.queue_picker()
                print(post_data)
                if post_data:
                    print("загружаем фото")
                    uploaded_photo = self.server_upload(post_data["photo_path"])
                    print(f"загруженные фото {uploaded_photo}")
                    print("make attacms")
                    atcms = self.make_attachments(uploaded_photo)
                    publish_date_unix = self.calc_publish_date()
                    print("публикуем пост")
                    self.post_publish(atcms, publish_date_unix)
                    self.db_conn.post_updater(post_data["post_id"])
                time.sleep(3600)
            except BaseException as ex:
                print(f"Ошибка в треде vk_workers {ex}")
                print("Пропускаем пост")
                self.db_conn.post_updater(post_data["post_id"], status="Fail")
