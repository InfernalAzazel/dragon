import time
import uuid

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from func.jd_web_hook.models import WebHookItem
from conf import Settings
from robak import Jdy, JdySerialize

doc = '''
    客户返利金额过渡表 -> 流程完成 -> 触发
    
    目标表单： 客户自销量核算申请表
    

'''


def register(router: APIRouter):
    @router.post('/c_r_amount_transition_table', tags=['客户返利金额过渡表-客户自销量核算申请表'], description=doc)
    async def c_r_amount_transition_table(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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
        # 客户自销量核算申请表
        jdy = Jdy(
            app_id=Settings.JD_APP_ID_BUSINESS,
            entry_id='615febe0571e8c0008f698fe',
            api_key=Settings.JD_API_KEY,
        )

        res, err = await jdy.get_form_data(
            data_filter={
                "cond": [
                    {
                        "field": 'years_code',
                        "type": 'text',
                        "method": "eq",
                        "value": whi.data['years_code']  # 年月客户代码
                    }
                ]
            })
        await errFn(err)
        uid = str(uuid.uuid4())
        suid = ''.join(uid.split('-'))
        if res:
            fl = []
            if res[0]['fl']:
                fl = res[0]['fl']
            fl.append({
                '_id': suid,
                'f_product_name': whi.data['product_name'],
                'f_product_code': whi.data['product_code'],
                'f_xl': whi.data['xl'],
                'f_khztbz': whi.data['khztbz'],
                'f_zixiaolian': whi.data['zixiaolian'],
                'f_fanli': whi.data['fanli']
            })
            _, err = await jdy.update_data(
                dataId=res[0]['_id'],
                data={
                    'fl': JdySerialize.subform('fl', fl)['fl'],
                })
            await errFn(err)
        else:
            fl = [
                {
                    '_id': suid,
                    'f_product_name': whi.data['product_name'],
                    'f_product_code': whi.data['product_code'],
                    'f_xl': whi.data['xl'],
                    'f_khztbz': whi.data['khztbz'],
                    'f_zixiaolian': whi.data['zixiaolian'],
                    'f_fanli': whi.data['fanli']
                },
            ]
            _, err = await jdy.create_data(
                data={
                    'customer_code': {'value': whi.data['customer_code']},
                    'customer_name': {'value': whi.data['customer_name']},
                    'years_code': {'value': whi.data['years_code']},
                    'zhuguan_bm': {'value': JdySerialize.department_err_to_none(whi.data, 'zhuguan_bm')},
                    'quyu_bm': {'value': JdySerialize.department_err_to_none(whi.data, 'quyu_bm')},
                    'daqu_bm': {'value': JdySerialize.department_err_to_none(whi.data, 'daqu_bm')},
                    'fuzong_bm': {'value': JdySerialize.department_err_to_none(whi.data, 'fuzong_bm')},
                    'fuzongjian_bm': {'value': JdySerialize.department_err_to_none(whi.data, 'fuzongjian_bm')},
                    'pp_zongjian_bm': {'value': JdySerialize.department_err_to_none(whi.data, 'pp_zongjian_bm')},
                    'shixiaoriqi': {'value': whi.data['shixiaoriqi']},
                    'shixiaonianyue': {'value': whi.data['shixiaonianyue']},
                    'xiaoliangheji': {'value': whi.data['xiaoliangheji']},
                    'chaerheji': {'value': whi.data['chaerheji']},
                    'khztbz': {'value': whi.data['khztbz']},
                    'fl': JdySerialize.subform('fl', fl)['fl'],
                },
                is_start_workflow=True
            )
            await errFn(err)
        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
