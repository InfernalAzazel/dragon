"""
 简道云接口封装

 # 实例化

 jd = JdAPI("学习板块", "玄牝测试前端事件表单")

    # 获取字段数据

    widgets = jd.get_form_widgets()

    for w in widgets:
        if w['label'] == '姓名':
            name = w['name']
            types = w['type']
            break

    # 查询多条数据

    result = jd.get_form_data(fields=[name], filter={
        "rel": "and",
        "cond": [
            {
                "field": name,
                "type": types,
                "method": "eq",
                "value": item.name
            }
        ]
    })
    if not result:
        return {'result': '否'}
    return {'result': '是'}

"""

import hashlib

import aiohttp


class JdAPI:
    # 基本的 URL
    URL_BASIC = "https://api.jiandaoyun.com"
    # API 认证密钥
    API_KEY = 'Q20Prk3r78ih4w0ZYOr6iEFfj9g6cEk0'
    # 当接口被限制 1s 5次 限制是否重发
    RETRY_IF_LIMITED = True
    # API 认证
    TOKEN = 'eYhUCuXBGaqv6AeD2W1X3PwC'
    # web hook 加密
    SECRET = 'jIYbq5RGrjeA1AsrNGdWfpH0'
    # 学习板块
    APP_ID_LEARNING_SECTION = '5e3e162d6e511b00067f066b'
    # 业务管理
    APP_ID_BUSINESS = '5dde829086f77b0006f3833e'
    # 人事管理
    APP_ID_MINISTRY_OF_PERSONNEL = '5df62d315fb7f10006a0b21e'

    # 构造函数
    def __init__(self, app_id, entry_id):
        """
        初始化 简道云 API

        :param app_id:      String 应用ID
        :param entry_id:    String 表单ID
        """
        self.api_key = JdAPI.API_KEY
        self.app_id = app_id
        self.entry_id = entry_id
        self.url_get_widgets = JdAPI.URL_BASIC + '/api/v1/app/' + self.app_id + '/entry/' + self.entry_id + '/widgets'
        self.url_get_data = JdAPI.URL_BASIC + '/api/v2/app/' + self.app_id + '/entry/' + self.entry_id + '/data'
        self.url_retrieve_data = JdAPI.URL_BASIC + '/api/v2/app/' + self.app_id + '/entry/' + self.entry_id + '/data_retrieve '
        self.url_update_data = JdAPI.URL_BASIC + '/api/v3/app/' + self.app_id + '/entry/' + self.entry_id + '/data_update'
        self.url_create_data = JdAPI.URL_BASIC + '/api/v3/app/' + self.app_id + '/entry/' + self.entry_id + '/data_create'
        self.url_delete_data = JdAPI.URL_BASIC + '/api/v1/app/' + self.app_id + '/entry/' + self.entry_id + '/data_delete'
        # 流程总接口
        self.url_process = f'/api/v1/app/' + self.app_id + '/entry/' + self.entry_id + '/data'

    # 签名
    @staticmethod
    def get_signature(nonce, payload, timestamp):
        """
        解码签名

        :param nonce:
        :param payload:
        :param timestamp:
        :return:
        """
        content = ':'.join([nonce, payload, JdAPI.SECRET, timestamp]).encode('utf-8')
        m = hashlib.sha1()
        m.update(content)
        return m.hexdigest()

    # 带有认证信息的请求头
    def get_req_header(self):
        """
        带有认证信息的请求头

        :return: header     JSON 请求头部
        """
        return {
            'Authorization': 'Bearer ' + self.api_key,
            'Content-Type': 'application/json;charset=utf-8'
        }

    # 发送http请求
    async def send_request(self, method, request_url, data):
        """
        发送http请求

        :param method:          String      请求方式 POST 或者 GET
        :param request_url:     String      链接地址
        :param data:            Array|JSON	请求参数
        :return: result         Json        数据
        """
        headers = self.get_req_header()
        try:
            async with aiohttp.ClientSession() as session:
                if method == 'GET':
                    # httpbin.org/get?key=val
                    # params = {'key1': 'value1', 'key2': 'value2'}
                    async with session.get(request_url, params=data, headers=headers) as response:
                        result = await response.json()
                if method == 'POST':
                    async with session.post(request_url, json=data, headers=headers) as response:
                        result = await response.json()
                if response.status >= 400:
                    if result['code'] == 8303 and JdAPI.RETRY_IF_LIMITED:
                        return await self.send_request(method, request_url, data)
                    else:
                        raise Exception('请求错误！', result)
                else:
                    return result
        except Exception as e:
            return await self.send_request(method, request_url, data)

    # 获取表单字段
    async def get_form_widgets(self):
        """
        获取表单字段

        无参数

        例子 get_form_widgets()

        :return: json widgets	控件信息
                      widgets[].items	仅子表单控件有；数组里包含了每个子控件的信息
                      widgets[].label	控件标题
                      widgets[].name	字段名（设置了字段别名则采用别名，未设置则采用控件ID）
                      widgets[].type	控件类型；每种控件类型都有对应的数据类型
        """
        result = await self.send_request('POST', self.url_get_widgets, {})
        return result['widgets']

    # 查询表单多条数据
    async def get_form_data(self, dataId='', fields=None, data_filter=None, limit=10):
        """
        查询表单多条数据

        可以不带参，默认查询 10条

        例子: get_form_data()

        :param dataId:      String	上一次查询数据结果的最后一条数据的ID，没有则留空
        :param fields:      Array   数据筛选器
        :param data_filter:      JSON	需要查询的数据字段
        :param limit:       Number	查询的数据条数，1~100，默认10
        :return: data	    Array	多条数据的集合
        """
        if data_filter is None:
            data_filter = {}
        if fields is None:
            fields = []
        result = await self.send_request('POST', self.url_get_data, {
            'data_id': dataId,
            'limit': limit,
            'fields': fields,
            'filter': data_filter
        })
        return result['data']

    # 查询表单中满足条件的所有数据
    async def get_all_data(self, fields=None, data_filter=None):
        """
        查询表单中满足条件的所有数据

        :param fields:      Array   需要查询的数据字段
        :param data_filter:      JSON	数据筛选器
        :return: data	    Array	多条数据的集合
        """
        if data_filter is None:
            data_filter = {}
        if fields is None:
            fields = []
        form_data = []

        # 递归取下一页数据
        async def get_next_page(dataId):
            data = await self.get_form_data(dataId=dataId, limit=10, fields=fields, data_filter=data_filter)
            if data:
                for v in data:
                    form_data.append(v)
                dataId = data[len(data) - 1]['_id']
                await get_next_page(dataId)

        await get_next_page('')

        return form_data

    # 查询单条数据接口
    async def retrieve_data(self, dataId):
        """
        查询单条数据接口

        :param dataId:  String  数据ID
        :return: data	JSON	单条数据
        """
        result = await self.send_request('POST', self.url_retrieve_data, {
            'data_id': dataId
        })
        return result['data']

    # 创建一条数据
    async def create_data(self, data, is_start_workflow=False, is_start_trigger=False):
        """
        创建一条数据

        :param data:                JSON   数据内容
        :param is_start_workflow:   Bool	是否发起流程（仅流程表单有效）	false
        :param is_start_trigger:    Bool	是否触发智能助手	false
        :return: data	            JSON	返回提交后的完整数据，内容同查询单条数据接口
        """
        result = await self.send_request('POST', self.url_create_data, {
            'data': data,
            'is_start_workflow': is_start_workflow,
            'is_start_trigger': is_start_trigger
        })
        return result['data']

    # 更新数据
    async def update_data(self, dataId, data, is_start_trigger=False):
        """
        更新数据

        :param dataId:              String	数据ID
        :param data:                JSON	数据内容，其他同新建单条数据接口，子表单需要注明子表单数据ID
        :param is_start_trigger:    Bool	是否触发智能助手
        :return: data	            JSON	返回修改后的新数据，内容同查询单条数据接口
        """
        result = await self.send_request('POST', self.url_update_data, {
            'data_id': dataId,
            'data': data,
            'is_start_trigger': is_start_trigger
        })
        return result['data']

    # 删除数据
    async def delete_data(self, dataId, is_start_trigger=False):
        """
        删除数据

        :param dataId:              String	数据ID
        :param is_start_trigger:	Bool	是否触发智能助手	false
        :return: status             JSON    成功或者失败状态
        """
        result = await self.send_request('POST', self.url_delete_data, {
            'data_id': dataId,
            'is_start_trigger': is_start_trigger
        })
        return result['status']

    # 流程
    # --------------------------------------------------------------------------------------------

    # 获取审批意见
    async def get_approval_comments(self, dataId):
        result = await self.send_request('POST', self.url_process + f'/{dataId}/approval_comments', {
            'data_id': dataId,
        })
        return result['status']
