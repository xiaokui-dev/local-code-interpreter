import pymysql.cursors


class DBManager:

    def __init__(self):
        self.connection = pymysql.connect(host='mysql',
                                          user='root',
                                          password='aETbb4GXDsnfkCW',
                                          database='code-interpreter',
                                          cursorclass=pymysql.cursors.DictCursor)
        self.cursor = self.connection.cursor()
        self._initialize_database()

    def _initialize_database(self):
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS `code_interpreter_title` (
              `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
              `title` varchar(128) NOT NULL DEFAULT '' COMMENT '标题',
              `create_user` varchar(64) NOT NULL DEFAULT '' COMMENT '创建人',
              `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
              `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
              PRIMARY KEY (`id`),
              KEY `idx_create_time` (`create_time`),
              KEY `idx_update_time` (`update_time`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        ''')
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS  `code_interpreter_messages` (
              `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
              `title_id` bigint unsigned NOT NULL DEFAULT 0 COMMENT 'title_id',
              `category` varchar(32) NOT NULL DEFAULT '' COMMENT '分类',
              `content` TEXT DEFAULT NULL COMMENT '内容',
              `file_urls` TEXT DEFAULT NULL COMMENT '文件url',
              `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
              `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
              PRIMARY KEY (`id`),
              KEY `idx_create_time` (`create_time`),
              KEY `idx_update_time` (`update_time`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        ''')

    def execute_query(self, query, params=()):
        self.cursor.execute(query, params)
        self.connection.commit()

    def fetch_query(self, query, params=()):
        self.cursor.execute(query, params)
        results = self.cursor.fetchall()
        return_list = []
        for d in results:
            return_list.append(tuple(d.values()))
        return return_list

    def fetch_one(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def save_chat(self, title):
        self.execute_query("insert into code_interpreter_title (title) values (%s)", (title))
        return self.cursor.lastrowid

    def update_chat(self, title, primary_id):
        self.execute_query("update code_interpreter_title set title = %s where id = %s", (title, primary_id))

    def get_chat(self, primary_id):
        return self.fetch_one("select id,title from code_interpreter_title where id = %s", (primary_id,))

    def get_chats(self):
        return self.fetch_query("select id,title from code_interpreter_title order by create_time desc")

    def get_message_by_chat_id(self, title_id):
        return self.fetch_query(
            "select id,category,content,file_urls from code_interpreter_messages where title_id = %s",
            (title_id,))

    def get_message_by_id(self, primary_id):
        return self.fetch_one("select id,category,content from code_interpreter_messages where id = %s",
                              (primary_id,))

    def save_chat_messages(self, title_id, category, content, file_url_list):
        file_urls = ""
        if len(file_url_list) != 0:
            file_urls = "####".join(file_url_list)
        self.execute_query(
            "insert into code_interpreter_messages (title_id,category, content,file_urls) values (%s,%s,%s,%s)",
            (title_id, category, content, file_urls))
        return self.cursor.lastrowid

    def update_file_url(self, file_url_list, primary_id):
        file_urls = "####".join(file_url_list)
        self.execute_query("update code_interpreter_messages set file_urls = %s where id = %s", (file_urls, primary_id))
