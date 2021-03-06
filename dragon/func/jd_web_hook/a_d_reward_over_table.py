import calendar
import datetime

from fastapi import APIRouter, Request, BackgroundTasks
from robak import Jdy, JdySerialize

from conf import Settings
from func.jd_web_hook.models import WebHookItem

doc = '''
    指定开发奖励申请过渡表-指定开发奖励申请

    1.[指定开发奖励申请过渡表] 通过工号查询 [人员档案] 获取大区是否存在存起大区数据
    2.把自身的考核月份 和 获取的大区 查询 [专项申请] 数据 如果有数据 获取子表单 [专项申请]
    3.判断指定奖励是否和 指定开发奖励申请过渡表一致，如果真则在指定开发 [开发奖励申请] 创建数据

'''


def register(router: APIRouter):
    @router.post('/a-d-reward-over-table', tags=['指定开发奖励申请过渡表-指定开发奖励审批'], description=doc)
    async def a_d_reward_over_table(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != Jdy.get_signature(
                nonce=req.query_params['nonce'],
                secret=Settings.JD_SECRET,
                timestamp=req.query_params['timestamp'],
                payload=bytes(await req.body()).decode('utf-8')):
            return 'fail', 401

        # 添加任务
        background_tasks.add_task(business, whi, str(req.url))
        return '2xx'


# 处理业务
async def business(whi: WebHookItem, url):
    async def errFn(e):
        if e is not None:
            await Settings.log.send(
                level=Settings.log.ERROR,
                url=url,
                secret=Settings.JD_SECRET,
                err=e,
                data=whi.dict(),
                is_start_workflow=True
            )
            return

    # 启动时间
    start = Settings.log.start_time()

    if whi.data['flowState'] == 1 and whi.op == 'data_update':
        createddate = datetime.datetime.strptime(
            whi.data['createddate'],
            '%Y-%m-%dT%H:%M:%S.000Z') + datetime.timedelta(hours=8)

        last_day = calendar.monthrange(createddate.year, createddate.month)[1]  # 最后一天
        # 开始时间
        start_time = datetime.datetime.strftime(
            datetime.datetime(createddate.year, createddate.month, 1, 0, 0, 0) - datetime.timedelta(hours=8),
            '%Y-%m-%dT%H:%M:%S.000Z')
        # 结束时间
        end_time = datetime.datetime.strftime(
            datetime.datetime(createddate.year, createddate.month, last_day, 0, 0, 0) - datetime.timedelta(hours=8),
            '%Y-%m-%dT%H:%M:%S.000Z')

        # print(whi.data)
        jd = Jdy.auto_init(

            app_id_list=[
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS
            ],
            entry_id_list=[
                '6127060adbc2410009f4a102',  # 专项申请
                '61052e6eb23ee70007657cc5',  # 指定开发奖励申请
            ],
            api_key=Settings.JD_API_KEY,
        )
        # 专项申请
        jd_a_d_special_apply_from = jd[0]
        # 指定开发奖励审批
        jd_a_d_reward_apply_from = jd[1]

        # 专项申请
        res, err = await jd_a_d_special_apply_from.get_form_data(
            data_filter={
                "rel": "and",  # 或者"or"
                "cond": [
                    {
                        "field": 'jixiao_nianyue',
                        "method": "range",
                        "value": [start_time, end_time]
                    },
                    {
                        "field": 'account',
                        "method": "eq",
                        "value": whi.data['account']
                    },
                    {
                        "field": 'flowState',
                        "method": "eq",
                        "value": [1]
                    },
                ]
            })
        await errFn(err)
        # print(whi.data['account'])
        # print(start_time, end_time)
        # print("找到数据:", len(res))
        if not res:
            return

        for vlaue in res[0]['jixiao_zb2']:
            if vlaue['khxm2'] == '指定开发奖励' and vlaue['qudao'] == whi.data['typename']:
                _, err = await jd_a_d_reward_apply_from.create_data(
                    data={
                        'serial_number': {'value': whi.data['serial_number']},  # 流水号
                        'managername': {'value': whi.data['managername']},  # 建档人
                        'workuser': {'value': JdySerialize.member_err_to_none(value=whi.data, name='workuser')},  # 建档人员
                        'id': {'value': whi.data['id']},  # 工号
                        'account': {'value': whi.data['account']},  # 终端工号
                        'createddate': {'value': whi.data['createddate']},  # 建档日期
                        'opendate': {'value': whi.data['opendate']},  # 合作日期
                        'code': {'value': whi.data['code']},  # 门店编码
                        'name': {'value': whi.data['name']},  # 门店名称
                        'typename': {'value': whi.data['typename']},  # 门店类型
                        'position': {'value': whi.data['position']},  # 职位
                        'dealername': {'value': whi.data['dealername']},  # 经销商
                        'dealercode': {'value': whi.data['dealercode']},  # 经销商代码
                        'contactertel': {'value': whi.data['contactertel']},  # 联系电话
                        'address': {'value': whi.data['address']},  # 终端建档位置
                        # 'daqubumen': {'value': daqujinli_bumen['dept_no']},  # 归属大区部门
                    },
                    is_start_workflow=True
                )
                await errFn(err)

        # 结束时间
        Settings.log.print(name=url, info=f'程序处理耗时 {Settings.log.elapsed(start)}s')
