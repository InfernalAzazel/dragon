import time
from functools import wraps

import numpy as np

from utils.jd_api import JdAPI
from utils.mgo import Mgo
from utils.qw_api import QWAPI


class QWAddressBookMember:
    # 构造函数

    def __init__(self):
        self.qwAPI = QWAPI()
        # 简道云 -> 人员档案
        self.jd_personnel_files_form = JdAPI(JdAPI.APP_ID_MINISTRY_OF_PERSONNEL, '60d997e93c87e2000867447d')
        # 简道云 -> 企业微信同步成员变动表
        self.jd_log_member_form = JdAPI(JdAPI.APP_ID_MINISTRY_OF_PERSONNEL, '60da6c95e3e27a000782403c')
        # 数据库名称
        self.db_Azazel_dragon = 'Azazel-dragon'
        # 数据库 -> 企业微信成员初始值表
        self.mgo_db_member_init = Mgo(db_name=self.db_Azazel_dragon, coll_name='60e6cbb9dbc050718d754848')
        # 数据库 -> 企业微信成员闪存表
        self.mgo_qw_member_flash_memory = Mgo(db_name=self.db_Azazel_dragon, coll_name='60e80ebce01eea4ace9b4164')
        # 数据库 -> 成员更新任务表
        self.mgo_member_update_task = Mgo(
            db_name=self.db_Azazel_dragon,
            coll_name='60ea4a72f33c000073007c02'
        )

        self.qw_member_list = []

        self.db_member_userid = []
        self.db_member_department = []
        self.db_member_name = []

        self.qw_member_userid = []
        self.qw_member_department = []
        self.qw_member_name = []

    # 初始化
    def event_init(self, func):
        """
        初始化 企业微信成员监视器

        :param func: 无传参
        """

        @wraps(func)
        async def wrapper():
            # 初始化企业微信接口
            await self.qwAPI.interface_init()
            # 获取营销总监 以下所有成员包括子成员
            self.qw_member_list = await self.get_member_all()
            count = await self.mgo_db_member_init.count()
            if count == 0:
                # 数据插入成员
                await self.mgo_db_member_init.insert_many(self.qw_member_list)

            # add db userid to db_userid
            async for document in self.mgo_db_member_init.find():
                self.db_member_userid.append(document['userid'])
                self.db_member_department.append({'userid': document['userid'], 'department': document['department']})
                self.db_member_name.append({'userid': document['userid'], 'name': document['name']})

            # add member_list userid to member_userid
            for value in self.qw_member_list:
                self.qw_member_userid.append(value['userid'])
                self.qw_member_department.append({'userid': value['userid'], 'department': value['department']})
                self.qw_member_name.append({'userid': value['userid'], 'name': value['name']})

            return await func()

        return wrapper

    # 新增成员
    def event_add(self, func):
        """
        匹配并且发现新增的成员

        :param func: (qw_member) 一个参数
        """

        @wraps(func)
        async def wrapper():
            for qw_member in self.qw_member_list:
                if qw_member['userid'] not in self.db_member_userid:
                    return await func(qw_member)

        return wrapper

    # 成员被删除
    def event_delete(self, func):
        """
        匹配并且发现删除的成员

        :param func:  (db_member) 一个参数
        """

        @wraps(func)
        async def wrapper():
            async for db_member in self.mgo_db_member_init.find():
                if db_member['userid'] not in self.qw_member_userid:
                    return await func(db_member)

        return wrapper

    # 成员名称被改变
    def event_change_name(self, func):
        """
        成员名称被改变

        :param func: (db_member, qw_member) 传参2位
        """

        @wraps(func)
        async def wrapper():
            for i in range(len(self.qw_member_name)):
                if self.qw_member_name[i] not in self.db_member_name:
                    db_member = await self.mgo_db_member_init.find_one(
                        {'userid': self.qw_member_name[i]["userid"]})
                    # 过滤名字相同的
                    # name: 林映彬-广东省潮州市枫溪区喜乐儿副食店 -> 林映彬-广东省潮州市枫溪区喜乐儿副食店
                    if db_member['name'] == self.qw_member_list[i]['name']:
                        return
                    return await func(db_member, self.qw_member_list[i])

        return wrapper

    # 成员与部门的关系被改变
    def event_change_relation(self, func):
        """
        成员与部门的关系被改变

        :param func: (db_member, qw_member) 传参2位
        """

        @wraps(func)
        async def wrapper():
            for i in range(len(self.qw_member_department)):
                for db_member in self.db_member_department:
                    if self.qw_member_department[i]['userid'] == db_member['userid']:
                        qw = np.array(self.qw_member_department[i]['department'])
                        db = np.array(db_member['department'])
                        change_department = np.setdiff1d(qw, db)
                        if change_department.tolist():
                            return await func(db_member, self.qw_member_list[i], change_department.tolist())

        return wrapper

    # 部门关系被改变更新所有成员
    def event_change_relation_d(self, func):
        @wraps(func)
        async def wrapper():
            pass
            if await self.mgo_member_update_task.count() != 0:
                pipeline = [
                    {
                        u"$graphLookup": {
                            u"from": u"60e548a9b37cdd33d7989dae",
                            u"startWith": u"$id",
                            u"connectFromField": u"parentid",
                            u"connectToField": u"id",
                            u"as": u"document",
                            u"maxDepth": 18.0,
                            u"depthField": u"rank",
                            u"restrictSearchWithMatch": {}
                        }
                    }
                ]

                try:
                    async for department in self.mgo_member_update_task.aggregate(
                            pipeline,
                    ):
                        return await func(department)
                finally:
                    pass

        return wrapper

    # 方法 ------------------------------------------------------
    # 获取当前所有成员
    async def get_all_children_member(self, cid):
        await self.qwAPI.interface_init()
        return await self.qwAPI.get_user_simplelist(id=cid)

    # 查询人员档案
    async def query_personnel_files_form(self, cid):
        position = [
            'customer_dept',
            'zhuguan_bumen',
            'quyujinli_bumen',
            'daqujinli_bumen',
            'fuzong_bumen',
            'fuzongjian_bumen',
            'fuzongjian_bumen_name',
            'xiaoshou_bumen'
        ]
        for i in range(len(position)):
            res = await self.jd_personnel_files_form.get_all_data(
                data_filter={
                    "cond": [
                        {
                            "field": position[i],
                            "type": 'dept',
                            "method": "eq",  # 相等的
                            "value": cid  # 部门ID
                        },

                    ]
                }
            )
            print(res)
            if res:
                print(res)
                return res
        return []

    async def get_member_all(self):
        """
        获取营销总监以下所有成员
        :return: data LIST 数组成员信息
        """
        res = await self.qwAPI.get_user_simplelist(604, 1)

        return res

    async def log_info(self, event, userid, member_name, content):
        await self.jd_log_member_form.create_data({
            'code': {
                'value': str(int(time.time()))
            },
            'states': {
                'value': '成功'
            },
            'event': {
                'value': event
            },
            'userid': {
                'value': userid
            },
            'member_name': {
                'value': member_name
            },
            'content': {
                'value': content
            },
            'error': {
                'value': ''
            },

        })

    async def log_error(self, event, userid, member_name, content, error):
        await self.jd_log_member_form.create_data({
            'code': {
                'value': str(int(time.time()))
            },
            'states': {
                'value': '失败'
            },
            'event': {
                'value': event
            },
            'userid': {
                'value': userid
            },
            'member_name': {
                'value': member_name
            },
            'content': {
                'value': content
            },
            'error': {
                'value': error
            },

        })

    async def get_department_relation(self, id, qw_member):
        highest_department = {}
        res = await self.mgo_db_member_init.find_one({'id': id})
        result = res
        relation = []

        while True:
            try:
                res = await self.mgo_db_member_init.find_one({'id': res['parentid']})
            except Exception:
                await self.log_error('[异常] 读取部门数据库失败', qw_member['userid'], qw_member["name"],
                                     '读取部门数据库失败,或许数据刷新新的部门关系',
                                     '空值'
                                     )
                return [], {}

            if res['parentid'] == 604:
                break
            relation.append(res)

        if len(relation) != 7:
            relation.insert(0, result)
        # 初始化微信接口
        await self.qwAPI.interface_init()
        new_relation = []
        for value in relation:
            new_relation.append(value)
            member = await self.qwAPI.get_user_simplelist(value['id'])

            for mv in member:
                if qw_member['userid'] == mv['userid']:
                    highest_department = value
                    new_relation.remove(value)
        try:
            new_relation.insert(0, highest_department)
        except Exception:
            pass

        # 填充
        if len(new_relation) != 7:
            for i in range(7 - len(new_relation)):
                new_relation.insert(0, {'id': -1})
        return new_relation, highest_department

    #  获取表单数据
    async def get_personnel_files_form_data(self, field, no):
        res = await self.jd_personnel_files_form.get_form_data(data_filter={
            "cond": [
                {
                    "field": field,
                    "type": 'text',
                    "method": "eq",
                    "value": no
                }
            ]

        })
        return res

    # 更新人员档案
    async def update_personnel_files_form(
            self,
            dataId,
            ruzhibumen,
            zhuguan_bumen,
            quyujinli_bumen,
            daqujinli_bumen,
            fuzong_bumen,
            fuzongjian_bumen,
            xiaoshou_bumen,
    ):
        data = {
            # 工号
            'ruzhibumen': {
                'value': ruzhibumen
            },
            # 主管
            'zhuguan_bumen': {
                'value': zhuguan_bumen
            },
            # 区域
            'quyujinli_bumen': {
                'value': quyujinli_bumen
            },
            # 大区
            'daqujinli_bumen': {
                'value': daqujinli_bumen
            },
            # 副总
            'fuzong_bumen': {
                'value': fuzong_bumen
            },
            # 副总监
            'fuzongjian_bumen': {
                'value': fuzongjian_bumen
            },
            # 销售部
            'xiaoshou_bumen': {
                'value': xiaoshou_bumen
            },
        }

        await self.jd_personnel_files_form.update_data(dataId=dataId, data=data)
