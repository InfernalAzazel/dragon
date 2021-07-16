import motor.motor_asyncio


class Mgo:
    ADDRESS = 'mongodb://cattle:AXMMvqWddZ6vACPhBWHWiR6w@61.143.126.226:27017'

    def __init__(self, db_name, coll_name):
        """
        初始化数据库 mongodb

        :param db_name: 数据库名称
        :param coll_name: 集合名称
        """
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Mgo.ADDRESS)
        self.db = self.client[db_name]
        self.coll = self.client[db_name][coll_name]

    @staticmethod
    async def get_for_mgo(db_name, coll_name):
        mgo_form = Mgo(db_name, 'form')
        async for doc in mgo_form.find():
            if doc['name'] == coll_name:
                mgo_form = Mgo(db_name, str(doc['_id']))
                break
        return mgo_form

    async def database_does_it_exist(self, database_names):
        """
        数据库是否存在

        :param database_names: String 数据库名称
        :return: Bool 存在返回 True 否则返回 False
        """
        db_list = await self.client.list_database_names()
        if database_names in db_list:
            return True
        return False

    async def collection_does_it_exist(self, collection_names):
        """
        合集是否存在

        :param collection_names: 集合名称
        :return: Bool 存在返回 True 否则返回 False
        """
        coll_list = await self.coll.list_collection_names()
        if collection_names in coll_list:
            return True
        return False

    async def insert_one(self, data):
        """
        插入一条数据

        :param data:
        :return: id
        """
        result = await self.coll.insert_one(data)
        self.client.close()
        return result

    # 批量插入
    async def insert_many(self, data):
        """
        批量插入

        - 例子

         result = await db.test_collection.insert_many(
            [{'i': i} for i in range(2000)])  # insert_many可以插入一条或多条数据，但是必须以列表(list)的形式组织数据
         print('inserted %d docs' % (len(result.inserted_ids),))

        :param data: JSON 数据
        :return: result
        """
        result = await self.coll.insert_many(data)
        self.client.close()
        return result

    async def find_one(self, query={}):
        """
        查询一条数据

        :param query:
        :return:
        """
        result = await self.coll.find_one(query)
        self.client.close()
        return result

    def find(self, query={}):
        """
        查询多条数据

        - 例子:

            >>> async def do_find():
            ...     c = db.test_collection
            ...     async for document in c.find({'i': {'$lt': 2}}):
            ...         pprint.pprint(document)

        :param query: 查询条件
        :return: data
        """
        result = self.coll.find(query)
        self.client.close()
        return result

    async def distinct(self, key):
        """
        某键下的所有值

        :param key: String 键
        :return:
        """
        result = await self.coll.distinct(key)
        self.client.close()
        return result

    async def update_one(self, query, data):
        """
        更新一条数据

        :param query: 查询条件
        :param data:  欲更新的数据
        :return:
        """
        result = await self.coll.update_one(query, data)
        self.client.close()
        return result

    async def delete_one(self, query):
        """
        删除一条数据

        :param query: 查询条件
        :return:
        """
        result = await self.coll.delete_one(query)
        self.client.close()
        return result

    async def delete_all(self):
        """
        删除所有数据

        :return: deleted_count
        """
        result = await self.coll.delete_many({})
        self.client.close()
        return result

    async def count(self, query={}):
        """
        查询文档数量

        :param query: 查询条件
        :return:
        """
        result = await self.coll.count_documents(query)
        self.client.close()
        return result

    # 聚合操作
    def aggregate(self, query):
        """
        聚合操作

        :param query:
        :return:
        """
        result = self.coll.aggregate(query)
        self.client.close()
        return result
