import time

import aiohttp


class QWAPI:
    # 企业 id
    CORP_ID = 'ww9ec26301b4320ef9'
    # 应用的凭证密钥
    CORP_SECRET = 'IAFxK_Qalqg6DHVEXIpXN9_b42wVWBSjcFn9HV-Y1b0'

    def __init__(self):

        self.access_token = ''
        self.url_basic = 'https://qyapi.weixin.qq.com/cgi-bin'

        self.url_gettoken = self.url_basic + '/gettoken?'
        self.url_department_list = self.url_basic + '/department/list?'

        self.url_user_simplelist = self.url_basic + '/user/simplelist?'
        self.url_user_list = self.url_basic + '/user/list?'

    # 接口初始化
    async def interface_init(self):
        result = await self.send_request('GET', self.url_gettoken,
                                         {'corpid': QWAPI.CORP_ID, 'corpsecret': QWAPI.CORP_SECRET})
        self.access_token = result['access_token']

    # 发送http请求
    async def send_request(self, method, request_url, data):
        """
        发送http请求

        :param method:          String      请求方式 POST 或者 GET
        :param request_url:     String      链接地址
        :param data:            Array|JSON	请求参数
        :return: result         Json        数据
        """
        # 请求超时1s
        timeout = aiohttp.ClientTimeout(total=1)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                if method == 'GET':
                    # httpbin.org/get?key=val
                    # params = {'key1': 'value1', 'key2': 'value2'}
                    async with session.get(request_url, params=data) as response:
                        result = await response.json()
                if method == 'POST':
                    async with session.post(request_url, json=data) as response:
                        result = await response.json()
                if response.status >= 400:
                    return await self.send_request(method, request_url, data)
                else:
                    return result
        except Exception:
            return await self.send_request(method, request_url, data)

    # 获取部门列表
    async def get_department_list(self, id=0):
        """
        获取部门列表

        :param id: INT 部门id。获取指定部门及其下的子部门（以及及子部门的子部门等等，递归）。 如果不填，默认获取全量组织架构
        :return: JSON
        """
        result = await self.send_request('GET', self.url_department_list,
                                         {'access_token': self.access_token, 'id': id})
        return result['department']

    # 获取成员
    async def get_user_simplelist(self, department_id, fetch_child=0):
        """
        获取成员

        :param department_id: INT 获取的部门id
        :param fetch_child: INT 是否递归获取子部门下面的成员：1-递归获取，0-只获取本部门
        :return: JSON
        """
        result = await self.send_request('GET', self.url_user_simplelist,
                                         {'access_token': self.access_token,
                                          'department_id': department_id,
                                          'fetch_child': fetch_child
                                          })
        return result['userlist']

    # 获取成员详细信息
    async def get_user_list(self, department_id, fetch_child=0):
        """
        获取成员详细信息

        :param department_id: INT 获取的部门id
        :param fetch_child: INT 是否递归获取子部门下面的成员：1-递归获取，0-只获取本部门
        :return: JSON
        """
        result = await self.send_request('GET', self.url_user_list,
                                         {'access_token': self.access_token,
                                          'department_id': department_id,
                                          'fetch_child': fetch_child
                                          })
        return result['userlist']
