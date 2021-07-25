from functools import wraps

from loguru import logger

from utils import Mgo, QWAPI, JdAPI


class QWAddressBookDepartment:
    data_fields = [
        '_id',  # id
        'fazhan_nian_yue',  # 发展 年月
        'kehu_bumen',  # 客户归属部门
        'kehu_bumen_name',  # 客户归属部门（名称）
        'zhuguan',  # 市场主管
        'zhuguan_name',  # 市场主管（名称）
        'zhuguan_bumen',  # 市场主管归属部门
        'zhuguan_bumen_name',  # 市场主管归属部门（名称）
        'zhuguan_num',  # 市场主管工号
        'zhuguan_zhiwei',  # 市场主管职位
        'zhuguan_synthesize',  # 市场主管-年月-姓名-工号-职位
        'qyjl',  # 区域经理
        'qyjlbm',  # 区域经理（名称）
        'quyujingli_bumen',  # 区域经理归属部门
        'quyujingli_bumen_name',  # 区域经理归属部门（名称）
        'jingli_num',  # 区域经理工号
        'quyujingli_zhiwei',  # 区域经理职位
        'quyujingli_synthesize',  # 区域经理-年月-姓名-工号-职位
        'daqujingli',  # 大区经理
        'daqujingli_name',  # 大区经理（名称）
        'daqujingli_bumen',  # 大区经理归属部门
        'daqujingli_bumen_name',  # 大区经理归属部门（名称）
        'daqujingli_num',  # 大区经理工号
        'daqujingli_zhiwei',  # 大区经理职位
        'daqujingli_synthesize',  # 大区经理-年月-姓名-工号-职位
        'fuzong',  # 副总
        'fuzong_name',  # 副总（名称）
        'fuzong_bumen',  # 副总归属部门
        'fuzong_bumen_t',  # 副总归属部门（名称）
        'fuzong_num',  # 副总工号
        'fuzong_zhiwei',  # 副总职位
        'fuzong_synthesize',  # 副总-年月-姓名-工号-职位
        'pinpaizongjian',  # 品牌总监
        'pinpaizongjian_t',  # 品牌总监（文本）
        'pinpaizongjian_num',  # 品牌总监工号
        'pinpaizongjian_bumen',  # 品牌总监部门
        'pinpaizongjian_bumen_t',  # 品牌总监部门（文本）
        'fuzongjian',  # 副总监
        'fuzongjian_num',  # 副总监工号
        'fuzongjian_bumen',  # 副总监部门
        'fuzongjian_bumen_name',  # 副总监部门（文本）
        'xiaoshou_bumen',  # 销售部
        'xiaoshou_bumen_name',  # 销售部（文本）
    ]

    def __init__(self):
        self.qwAPI = QWAPI()
        # 简道云 -> 客户档案
        self.jd_customer_profile_form = JdAPI(JdAPI.APP_ID_BUSINESS, '5dd102e307747e0006801bee')
        # 简道云 -> 人员档案
        self.personnel_files_form = JdAPI(JdAPI.APP_ID_MINISTRY_OF_PERSONNEL, '5df7a704c75c0e00061de8f6')
        # 简道云 -> 企业微信部门变动表
        self.jd_log_department_form = JdAPI(JdAPI.APP_ID_BUSINESS, '60e57b34baba460009824c8c')
        # 数据库名称
        self.db_Azazel_dragon = 'Azazel-dragon'

        # 数据库 -> 客户档案闪存表
        self.mgo_customer_profile_flash_memory = Mgo(db_name=self.db_Azazel_dragon,
                                                     coll_name='60e3bb501f3d0000d3000d17')
        # 数据库 -> 企业微信部门初始值表
        self.mgo_db_qw_department = Mgo(db_name=self.db_Azazel_dragon, coll_name='60e3bb731f3d0000d3000d18')
        # 数据库 -> 企业微信部门闪存表
        self.mgo_qw_department_flash_memory = Mgo(db_name=self.db_Azazel_dragon, coll_name='60e548a9b37cdd33d7989dae')
        # 数据库 -> 客户档案与企业微信部门关系中间表
        self.mgo_cp_qw_middle = Mgo(db_name=self.db_Azazel_dragon, coll_name='60e3bc0b1f3d0000d3000d1a')
        # 数据库 -> 成员更新任务表
        self.mgo_member_update_task = Mgo(
            db_name=self.db_Azazel_dragon,
            coll_name='60ea4a72f33c000073007c02'
        )

        self.qw_d_list = []

        self.db_qw_d_id = []
        self.db_qw_d_parentid = []
        self.db_qw_d_id_name = []

        self.qw_d_id = []
        self.qw_d_parentid = []
        self.qw_d_id_name = []

    # 初始化事件
    def event_init(self, func):
        @wraps(func)
        async def wrapper():

            # 初始化企业微信
            await self.qwAPI.interface_init()
            # 获取营销总监下所有部门
            self.qw_d_list = await self.qwAPI.get_department_list(604)

            # 数据库 -> 企业微信部门初始值表
            if await self.mgo_db_qw_department.count() == 0:
                await self.mgo_db_qw_department.insert_many(self.qw_d_list)
            # 数据库 -> 企业微信部门闪存表
            if await self.mgo_qw_department_flash_memory.count() != 0:
                await self.mgo_qw_department_flash_memory.delete_all()
            await self.mgo_qw_department_flash_memory.insert_many(self.qw_d_list)

            async for document in self.mgo_db_qw_department.find():
                self.db_qw_d_id.append(document['id'])
                self.db_qw_d_parentid.append({'id': document['id'], 'parentid': document['parentid']})
                self.db_qw_d_id_name.append({'id': document['id'], 'name': document['name']})

            for value in self.qw_d_list:
                self.qw_d_id.append(value['id'])
                self.qw_d_parentid.append({'id': value['id'], 'parentid': value['parentid']})
                self.qw_d_id_name.append({'id': value['id'], 'name': value['name']})

            return await func()

        return wrapper

    # 部门新增
    def department_event_add(self, func):
        @wraps(func)
        async def wrapper():
            # 匹配并且发现新增的
            for value in self.qw_d_list:
                # 获取新增的部门信息
                if value['id'] not in self.db_qw_d_id:
                    return await func(value)

        return wrapper

    # 部门删除
    def department_event_delete(self, func):
        @wraps(func)
        async def wrapper():
            async for document in self.mgo_db_qw_department.find():
                # 获取删除的部门信息
                if document['id'] not in self.qw_d_id:
                    return await func(document)

        return wrapper

    # 部门改名
    def department_event_change_name(self, func):
        @wraps(func)
        async def wrapper():
            for i in range(len(self.qw_d_id_name)):
                # 获取被修改的部门信息
                if self.qw_d_id_name[i] not in self.db_qw_d_id_name:
                    document = await self.mgo_db_qw_department.find_one({'id': self.qw_d_id_name[i]["id"]})
                    # 过滤
                    # 发现被改名的部门 id:9817 name: A罗C -> name: A罗C
                    if document["name"] == self.qw_d_list[i]['name']:
                        return
                    return await func(document, self.qw_d_list[i])

        return wrapper

    # 部门关系被改变
    def department_event_change_relation(self, func):
        @wraps(func)
        async def wrapper():
            for i in range(len(self.qw_d_parentid)):
                if self.qw_d_parentid[i] not in self.db_qw_d_parentid:
                    document = await self.mgo_db_qw_department.find_one({'id': self.qw_d_parentid[i]["id"]})
                    # 过滤新增时触发此条件
                    #  发现修改部门关系:  10093  11111  9778  -> 9778
                    if document["parentid"] == self.qw_d_list[i]['parentid']:
                        return
                    return await func(document, self.qw_d_list[i])

        return wrapper

    # 方法 ---------------------------------------------------------------

    # 获取所有客户
    async def get_all_customer(self, department_name):
        position = [
            'kehu_bumen_name',
            'zhuguan_bumen_name',
            'quyujingli_bumen_name',
            'daqujingli_bumen_name',
            'fuzong_bumen_t',
            'pinpaizongjian_bumen_t',
            'fuzongjian_bumen_name',
            'xiaoshou_bumen_name'
        ]
        for i in range(len(position)):
            res = await self.jd_customer_profile_form.get_all_data(
                fields=self.data_fields,
                data_filter={
                    "cond": [
                        {
                            "field": position[i],
                            "type": 'text',
                            "method": "eq",
                            "value": department_name
                        },
                    ]
                }
            )
            if res:
                break
        if not res:
            return []
        if await self.mgo_customer_profile_flash_memory.count() != 0:
            # 清空 客户档案闪存表
            await self.mgo_customer_profile_flash_memory.delete_all()
        # 插入数据
        await self.mgo_customer_profile_flash_memory.insert_many(res)

        pipeline = [
            {
                u"$lookup": {
                    # 企业微信部门闪存表
                    u"from": u"60e548a9b37cdd33d7989dae",
                    u"localField": u"kehu_bumen.dept_no",
                    u"foreignField": u"id",
                    u"as": u"qw_department"
                }
            },
            {
                u"$unwind": {
                    u"path": u"$qw_department",
                    u"preserveNullAndEmptyArrays": False
                }
            },
            {
                u"$graphLookup": {
                    # 企业微信部门闪存表
                    u"from": u"60e548a9b37cdd33d7989dae",
                    u"startWith": u"$qw_department.id",
                    u"connectFromField": u"parentid",
                    u"connectToField": u"id",
                    u"as": u"relation",
                    u"maxDepth": 11.0,
                    u"depthField": u"rank",
                    u"restrictSearchWithMatch": {}
                }
            },
            {
                # 输出到 客户档案与企业微信部门关系中间表
                u"$out": u"60e3bc0b1f3d0000d3000d1a"
            }
        ]
        try:
            async for doc in self.mgo_customer_profile_flash_memory.aggregate(query=pipeline):
                print(doc)
        finally:
            pass

        return [v async for v in self.mgo_cp_qw_middle.find()]

    # 排序部门
    async def sort_department(self, relation):
        for value in relation:
            rank = value["rank"]
            if rank == 0:
                kehu_bumen_name = value
            elif rank == 1:
                zhuguan_bumen_name = value
            elif rank == 2:
                quyujingli_bumen_name = value
            elif rank == 3:
                daqujingli_bumen_name = value
            elif rank == 4:
                fuzong_bumen_t = value
            elif rank == 5:
                pinpaizongjian_bumen_t = value
            elif rank == 6:
                fuzongjian_bumen_name = value
            elif rank == 7:
                xiaoshou_bumen_name = value
        # print(kehu_bumen_name, zhuguan_bumen_name, quyujingli_bumen_name, daqujingli_bumen_name, fuzong_bumen_t, pinpaizongjian_bumen_t, fuzongjian_bumen_name, xiaoshou_bumen_name)
        return kehu_bumen_name, zhuguan_bumen_name, quyujingli_bumen_name, daqujingli_bumen_name, fuzong_bumen_t, pinpaizongjian_bumen_t, fuzongjian_bumen_name, xiaoshou_bumen_name

    # 日志 - > 修改部门名称
    async def log_event_department_change_name(self, status, event, add='', delete='', change_name='', error='',
                                               remarks=''):
        await self.jd_log_department_form.create_data(
            data={
                # 状态
                'status': {
                    'value': status
                },
                # 事件
                'event': {
                    'value': event
                },
                # 添加部门
                'add': {
                    'value': add
                },
                # 删除部门
                'delete': {
                    'value': delete
                },
                # 删除部门
                'change_name': {
                    'value': change_name
                },
                'error': {
                    'value': error
                },
                'remarks': {
                    'value': remarks
                },
            })

    # 日志 -> 新增部门
    async def log_event_add_delete_dpartment_relation(self, status, event, add='', delete='', error='', remarks=''):
        await self.jd_log_department_form.create_data(
            data={
                # 状态
                'status': {
                    'value': status
                },
                # 事件
                'event': {
                    'value': event
                },
                # 添加部门
                'add': {
                    'value': add
                },
                # 删除部门
                'delete': {
                    'value': delete
                },
                'error': {
                    'value': error
                },
                'remarks': {
                    'value': remarks
                },
            })

    # 日志->修改部门关系
    async def log_event_modify_department_relation(self, val_res, status, event, error='', remarks=''):
        if val_res:
            kehu_bumen_name, zhuguan_bumen_name, quyujingli_bumen_name, daqujingli_bumen_name, fuzong_bumen_t, pinpaizongjian_bumen_t, fuzongjian_bumen_name, xiaoshou_bumen_name = await self.sort_department(
                relation=val_res['relation'])
            await self.jd_log_department_form.create_data(
                data={
                    # 状态
                    'status': {
                        'value': status
                    },
                    # 事件
                    'event': {
                        'value': event
                    },
                    # 客户
                    'kehu_bumen_name': {
                        'value': val_res['kehu_bumen_name']
                    },
                    # 主管
                    'zhuguan_bumen_name': {
                        'value': val_res['zhuguan_bumen_name']
                    },
                    # 小区
                    'quyujingli_bumen_name': {
                        'value': val_res['quyujingli_bumen_name']
                    },
                    # 大区
                    'daqujingli_bumen_name': {
                        'value': val_res['daqujingli_bumen_name']
                    },
                    # 副总
                    'fuzong_bumen_t': {
                        'value': val_res['fuzong_bumen_t']
                    },
                    # 品牌副总
                    'pinpaizongjian_bumen_t': {
                        'value': val_res['pinpaizongjian_bumen_t']
                    },
                    # 副总监
                    'fuzongjian_bumen_name': {
                        'value': val_res['fuzongjian_bumen_name']
                    },
                    # 销售部门
                    'xiaoshou_bumen_name': {
                        'value': val_res['xiaoshou_bumen_name']
                    },
                    # 客户（新）
                    'new_kehu_bumen_name': {
                        'value': kehu_bumen_name['name']
                    },
                    # 主管（新）
                    'new_zhuguan_bumen_name': {
                        'value': zhuguan_bumen_name['name']
                    },
                    # 小区（新）
                    'new_quyujingli_bumen_name': {
                        'value': quyujingli_bumen_name['name']
                    },
                    # 大区（新）
                    'new_daqujingli_bumen_name': {
                        'value': daqujingli_bumen_name['name']
                    },
                    # 副总（新）
                    'new_fuzong_bumen_t': {
                        'value': fuzong_bumen_t['name']
                    },
                    # 品牌副总（新）
                    'new_pinpaizongjian_bumen_t': {
                        'value': pinpaizongjian_bumen_t['name']
                    },
                    # 副总监（新）
                    'new_fuzongjian_bumen_name': {
                        'value': fuzongjian_bumen_name['name']
                    },
                    # 销售部门（新）
                    'new_xiaoshou_bumen_name': {
                        'value': xiaoshou_bumen_name['name']
                    },
                    'error': {
                        'value': error
                    },
                    'remarks': {
                        'value': remarks
                    },
                })

    # 部门名称比较并找出更新-> 返回文本 备注
    async def compare_department_to_remarks(self, val_res):
        if val_res:
            kehu_bumen_name, zhuguan_bumen_name, quyujingli_bumen_name, daqujingli_bumen_name, fuzong_bumen_t, pinpaizongjian_bumen_t, fuzongjian_bumen_name, xiaoshou_bumen_name = await self.sort_department(
                relation=val_res['relation'])
            msg = '[变动信息] \n'
            if val_res['zhuguan_bumen_name'] != zhuguan_bumen_name["name"]:
                msg = msg + f'[主管部门] -> {zhuguan_bumen_name["name"]}\n[ID] -> {zhuguan_bumen_name["id"]}\n '
            if val_res['quyujingli_bumen_name'] != quyujingli_bumen_name["name"]:
                msg = msg + f'[区域经理部门] ->  {quyujingli_bumen_name["name"]}\n[ID] -> {quyujingli_bumen_name["id"]}\n '
            if val_res['daqujingli_bumen_name'] != daqujingli_bumen_name["name"]:
                msg = msg + f'[大区经理部门] -> {daqujingli_bumen_name["name"]}\n[ID] -> {daqujingli_bumen_name["id"]}\n'
            if val_res['fuzong_bumen_t'] != fuzong_bumen_t["name"]:
                msg = msg + f'[副总部门] -> {fuzong_bumen_t["name"]}\n[ID] -> {fuzong_bumen_t["id"]}\n'
            if val_res['pinpaizongjian_bumen_t'] != pinpaizongjian_bumen_t["name"]:
                msg = msg + f'[品牌总监部门] ->  {pinpaizongjian_bumen_t["name"]}\n[ID] -> {pinpaizongjian_bumen_t["id"]}\n'
            if val_res['fuzongjian_bumen_name'] != fuzongjian_bumen_name["name"]:
                msg = msg + f'[副总监部门] -> {fuzongjian_bumen_name["name"]}\n[ID] -> {fuzongjian_bumen_name["id"]}\n'
            if val_res['xiaoshou_bumen_name'] != xiaoshou_bumen_name["name"]:
                msg = msg + f'[销售部门] -> {xiaoshou_bumen_name["name"]}\n[ID] -> {xiaoshou_bumen_name["id"]}\n'
            return msg

    # 日志异常信息转备注格式
    async def log_error_to_remarks(self, info, no, name, text):
        return f' [{info}]\n [工号] -> {no}\n[姓名] -> {name}\n[注意事项] -> {text}'

    # 更新客户档案部门
    async def update_customer_profile_form(self, data, event):
        if data:
            for val_res in data:

                remarks = await self.compare_department_to_remarks(
                    val_res)
                # 部门名称一致，返回不做处理
                if remarks == '[变动信息] \n':
                    logger.info('[+] 部门名称相等返回不做任何改动 .......')
                    return

                _, zhuguan_bumen, quyujingli_bumen, daqujingli_bumen, fuzong_bumen, pinpaizongjian, fuzongjian_bumen, xiaoshou_bumen = await self.sort_department(
                    relation=val_res['relation'])

                await self.qwAPI.interface_init()

                member2 = await self.qwAPI.get_user_simplelist(zhuguan_bumen['id'])
                member3 = await self.qwAPI.get_user_simplelist(quyujingli_bumen['id'])
                member4 = await self.qwAPI.get_user_simplelist(daqujingli_bumen['id'])
                member5 = await self.qwAPI.get_user_simplelist(fuzong_bumen['id'])
                member6 = await self.qwAPI.get_user_simplelist(pinpaizongjian['id'])
                member7 = await self.qwAPI.get_user_simplelist(fuzongjian_bumen['id'])

                if not member2:
                    await self.log_event_modify_department_relation(
                        val_res,
                        status='失败',
                        event=event,
                        error='空值',
                        remarks=await self.log_error_to_remarks(
                            info='读取企业微信成员失败',
                            no='',
                            name='',
                            text=f'请检查企业微信 <{zhuguan_bumen["name"]}> 成员是否为最顶层 和 是否存在（注此关系需要手动维护）')
                    )
                    continue
                if not member3:
                    await self.log_event_modify_department_relation(
                        val_res,
                        status='失败',
                        event=event,
                        error='空值',
                        remarks=await self.log_error_to_remarks(
                            info='读取企业微信成员失败',
                            no='',
                            name='',
                            text=f'请检查企业微信 <{quyujingli_bumen["name"]}> 成员是否为最顶层 和 是否存在（注此关系需要手动维护）')
                    )
                    continue
                if not member4:
                    await self.log_event_modify_department_relation(
                        val_res,
                        status='失败',
                        event=event, error='空值',
                        remarks=await self.log_error_to_remarks(
                            info='读取企业微信成员失败',
                            no='',
                            name='',
                            text=f'请检查企业微信 <{daqujingli_bumen["name"]}> 成员是否为最顶层 和 是否存在（注此关系需要手动维护）')
                    )
                    continue
                if not member5:
                    await self.log_event_modify_department_relation(
                        val_res,
                        status='失败',
                        event=event, error='空值',
                        remarks=await self.log_error_to_remarks(
                            info='读取企业微信成员失败',
                            no='',
                            name='',
                            text=f'请检查企业微信 <{fuzong_bumen["name"]}> 成员是否为最顶层 和 是否存在（注此关系需要手动维护）')
                    )
                    continue
                if not member6:
                    await self.log_event_modify_department_relation(
                        val_res,
                        status='失败',
                        event=event, error='空值',
                        remarks=await self.log_error_to_remarks(
                            info='读取企业微信成员失败',
                            no='',
                            name='',
                            text=f'请检查企业微信 <{pinpaizongjian["name"]}> 成员是否为最顶层 和 是否存在（注此关系需要手动维护）')
                    )
                    continue
                if not member7:
                    await self.log_event_modify_department_relation(
                        val_res,
                        status='失败',
                        event=event, error='空值',
                        remarks=await self.log_error_to_remarks(
                            info='读取企业微信成员失败',
                            no='',
                            name='',
                            text=f'请检查企业微信 <{fuzongjian_bumen["name"]}> 成员是否为最顶层 和 是否存在（注此关系需要手动维护）')
                    )
                    continue

                personnel2 = await self.personnel_files_form.get_form_data(data_filter={
                    "cond": [{"field": 'no', "type": 'text', "method": "eq", "value": member2[0]['userid']}]})
                personnel3 = await self.personnel_files_form.get_form_data(data_filter={
                    "cond": [{"field": 'no', "type": 'text', "method": "eq", "value": member3[0]['userid']}]})
                personnel4 = await self.personnel_files_form.get_form_data(data_filter={
                    "cond": [{"field": 'no', "type": 'text', "method": "eq", "value": member4[0]['userid']}]})
                personnel5 = await self.personnel_files_form.get_form_data(data_filter={
                    "cond": [{"field": 'no', "type": 'text', "method": "eq", "value": member5[0]['userid']}]})
                personnel6 = await self.personnel_files_form.get_form_data(data_filter={
                    "cond": [{"field": 'no', "type": 'text', "method": "eq", "value": member6[0]['userid']}]})
                personnel7 = await self.personnel_files_form.get_form_data(data_filter={
                    "cond": [{"field": 'no', "type": 'text', "method": "eq", "value": member7[0]['userid']}]})

                if not personnel2:
                    await self.log_event_modify_department_relation(
                        val_res,
                        status='失败',
                        event=event,
                        error='空值',
                        remarks=await self.log_error_to_remarks(
                            info='读取人员档案失败',
                            no=member2[0]["userid"],
                            name=member2[0]["name"],
                            text='请检查人员档案是否存在此人（注此关系需要手动维护）')
                    )
                    continue
                if not personnel3:
                    await self.log_event_modify_department_relation(
                        val_res,
                        status='失败',
                        event=event,
                        error='空值',
                        remarks=await self.log_error_to_remarks(
                            info='读取人员档案失败',
                            no=member3[0]["userid"],
                            name=member3[0]["name"],
                            text='请检查人员档案是否存在此人（注此关系需要手动维护）')
                    )
                    continue
                if not personnel4:
                    await self.log_event_modify_department_relation(
                        val_res,
                        status='失败',
                        event=event,
                        error='空值',
                        remarks=await self.log_error_to_remarks(
                            info='读取人员档案失败',
                            no=member4[0]["userid"],
                            name=member4[0]["name"],
                            text='请检查人员档案是否存在此人（注此关系需要手动维护）')
                    )
                    continue
                if not personnel5:
                    await self.log_event_modify_department_relation(
                        val_res,
                        status='失败',
                        event=event,
                        error='空值',
                        remarks=await self.log_error_to_remarks(
                            info='读取人员档案失败',
                            no=member5[0]["userid"],
                            name=member5[0]["name"],
                            text='请检查人员档案是否存在此人（注此关系需要手动维护）')
                    )
                    continue
                if not personnel6:
                    await self.log_event_modify_department_relation(
                        val_res,
                        status='失败',
                        event=event,
                        error='空值',
                        remarks=await self.log_error_to_remarks(
                            info='读取人员档案失败',
                            no=member6[0]["userid"],
                            name=member6[0]["name"],
                            text='请检查人员档案是否存在此人（注此关系需要手动维护）')
                    )
                    continue
                if not personnel7:
                    await self.log_event_modify_department_relation(
                        val_res,
                        status='失败',
                        event=event,
                        error='空值',
                        remarks=await self.log_error_to_remarks(
                            info='读取人员档案失败',
                            no=member7[0]["userid"],
                            name=member7[0]["name"],
                            text='请检查人员档案是否存在此人（注此关系需要手动维护）')
                    )
                    continue

                data_form = self.customer_profile_form(
                    # 主管
                    zhuguan=member2[0]['userid'],
                    zhuguan_name=member2[0]['name'],
                    zhuguan_bumen_name=zhuguan_bumen['name'],
                    zhuguan_bumen=zhuguan_bumen['id'],
                    zhuguan_num=personnel2[0]['no'],
                    zhuguan_zhiwei=personnel2[0]['position'],
                    zhuguan_synthesize=val_res[
                                           'fazhan_nian_yue'] +
                                       member2[0]['name'] +
                                       personnel2[0]['no'] +
                                       personnel2[0][
                                           'position'],
                    # 区域
                    qyjl=member3[0]['userid'],
                    qyjlbm=member3[0]['name'],
                    quyujingli_bumen=quyujingli_bumen['id'],
                    quyujingli_bumen_name=quyujingli_bumen[
                        'name'],
                    jingli_num=personnel3[0]['no'],
                    quyujingli_zhiwei=personnel3[0]['position'],
                    quyujingli_synthesize=val_res[
                                              'fazhan_nian_yue'] +
                                          member3[0]['name'] +
                                          personnel3[0]['no'] +
                                          personnel3[0][
                                              'position'],
                    # 大区
                    daqujingli=member4[0]['userid'],
                    daqujingli_name=member4[0]['name'],
                    daqujingli_bumen=daqujingli_bumen['id'],
                    daqujingli_bumen_name=daqujingli_bumen[
                        'name'],
                    daqujingli_num=personnel4[0]['no'],
                    daqujingli_zhiwei=personnel4[0]['position'],
                    daqujingli_synthesize=val_res[
                                              'fazhan_nian_yue'] +
                                          member4[0]['name'] +
                                          personnel4[0]['no'] +
                                          personnel4[0][
                                              'position'],
                    # 副总
                    fuzong=member5[0]['userid'],
                    fuzong_name=member5[0]['name'],
                    fuzong_bumen=fuzong_bumen['id'],
                    fuzong_bumen_t=fuzong_bumen['name'],
                    fuzong_num=personnel5[0]['no'],
                    fuzong_zhiwei=personnel5[0]['position'],
                    fuzong_synthesize=val_res[
                                          'fazhan_nian_yue'] +
                                      member5[0]['name'] +
                                      personnel5[0]['no'] +
                                      personnel5[0]['position'],
                    # 品牌
                    pinpaizongjian=member6[0]['userid'],
                    pinpaizongjian_t=member6[0]['name'],
                    pinpaizongjian_num=personnel6[0]['no'],
                    pinpaizongjian_bumen=pinpaizongjian['id'],
                    pinpaizongjian_bumen_t=pinpaizongjian[
                        'name'],
                    # 副总监
                    fuzongjian=member7[0]['userid'],
                    fuzongjian_num=personnel7[0]['no'],
                    fuzongjian_bumen=fuzongjian_bumen['id'],
                    fuzongjian_bumen_name=fuzongjian_bumen[
                        'name'],
                    # 销售
                    xiaoshou_bumen=xiaoshou_bumen['id'],
                    xiaoshou_bumen_name=xiaoshou_bumen['name']
                )

                await self.jd_customer_profile_form.update_data(
                    dataId=val_res['_id'],
                    data=data_form
                )
                await self.log_event_modify_department_relation(
                    val_res,
                    status='成功',
                    event=event,
                    remarks=remarks
                )

    # 客户档案表单格式
    @staticmethod
    def customer_profile_form(
            zhuguan,
            zhuguan_name,
            zhuguan_bumen_name,
            zhuguan_bumen,
            zhuguan_num,
            zhuguan_zhiwei,
            zhuguan_synthesize,
            qyjl,
            qyjlbm,
            quyujingli_bumen,
            quyujingli_bumen_name,
            jingli_num,
            quyujingli_zhiwei,
            quyujingli_synthesize,
            daqujingli,
            daqujingli_name,
            daqujingli_bumen,
            daqujingli_bumen_name,
            daqujingli_num,
            daqujingli_zhiwei,
            daqujingli_synthesize,
            fuzong,
            fuzong_name,
            fuzong_bumen,
            fuzong_bumen_t,
            fuzong_num,
            fuzong_zhiwei,
            fuzong_synthesize,
            pinpaizongjian,
            pinpaizongjian_t,
            pinpaizongjian_num,
            pinpaizongjian_bumen,
            pinpaizongjian_bumen_t,
            fuzongjian,
            fuzongjian_num,
            fuzongjian_bumen,
            fuzongjian_bumen_name,
            xiaoshou_bumen,
            xiaoshou_bumen_name
    ):
        data = {
            'zhuguan': {
                'value': zhuguan
            },
            'zhuguan_name': {
                'value': zhuguan_name
            },
            'zhuguan_bumen': {
                'value': zhuguan_bumen
            },
            'zhuguan_bumen_name': {
                'value': zhuguan_bumen_name
            },
            'zhuguan_num': {
                'value': zhuguan_num
            },
            'zhuguan_zhiwei': {
                'value': zhuguan_zhiwei
            },
            'zhuguan_synthesize': {
                'value': zhuguan_synthesize
            },
            'qyjl': {
                'value': qyjl
            },
            'qyjlbm': {
                'value': qyjlbm
            },
            'quyujingli_bumen': {
                'value': quyujingli_bumen
            },
            'quyujingli_bumen_name': {
                'value': quyujingli_bumen_name
            },
            'jingli_num': {
                'value': jingli_num
            },
            'quyujingli_zhiwei': {
                'value': quyujingli_zhiwei
            },
            'quyujingli_synthesize': {
                'value': quyujingli_synthesize
            },
            'daqujingli': {
                'value': daqujingli
            },
            'daqujingli_name': {
                'value': daqujingli_name
            },
            'daqujingli_bumen': {
                'value': daqujingli_bumen
            },
            'daqujingli_bumen_name': {
                'value': daqujingli_bumen_name
            },
            'daqujingli_num': {
                'value': daqujingli_num
            },
            'daqujingli_zhiwei': {
                'value': daqujingli_zhiwei
            },
            'daqujingli_synthesize': {
                'value': daqujingli_synthesize
            },
            'fuzong': {
                'value': fuzong
            },
            'fuzong_name': {
                'value': fuzong_name
            },
            'fuzong_bumen': {
                'value': fuzong_bumen
            },
            'fuzong_bumen_t': {
                'value': fuzong_bumen_t
            },
            'fuzong_num': {
                'value': fuzong_num
            },
            'fuzong_zhiwei': {
                'value': fuzong_zhiwei
            },
            'fuzong_synthesize': {
                'value': fuzong_synthesize
            },
            'pinpaizongjian': {
                'value': pinpaizongjian
            },
            'pinpaizongjian_t': {
                'value': pinpaizongjian_t
            },
            'pinpaizongjian_num': {
                'value': pinpaizongjian_num
            },
            'pinpaizongjian_bumen': {
                'value': pinpaizongjian_bumen
            },
            'pinpaizongjian_bumen_t': {
                'value': pinpaizongjian_bumen_t
            },
            'fuzongjian': {
                'value': fuzongjian
            },
            'fuzongjian_num': {
                'value': fuzongjian_num
            },
            'fuzongjian_bumen': {
                'value': fuzongjian_bumen
            },
            'fuzongjian_bumen_name': {
                'value': fuzongjian_bumen_name
            },
            'xiaoshou_bumen': {
                'value': xiaoshou_bumen
            },
            'xiaoshou_bumen_name': {
                'value': xiaoshou_bumen_name
            },
        }
        return data
