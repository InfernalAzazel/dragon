import asyncio
import time

from utils import QWAddressBookDepartment
from loguru import logger


class QWAddressBookDepartmentTask:

    @staticmethod
    def run():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.close()


async def main():
    # 启动时间
    start = time.perf_counter()
    logger.info(f'[+] <任务> 企业微信同步客户档案 计算中 ......')
    qw_address_book = QWAddressBookDepartment()

    # 初始化
    @qw_address_book.event_init
    async def event_init():
        pass

    # 新增部门
    @qw_address_book.department_event_add
    async def department_event_add(qw):
        logger.info(f'[+] 发现新增部门: {qw}')
        logger.info(f'[+] 正在处理 1条 .......')
        await qw_address_book.log_event_add_delete_dpartment_relation(status='成功', event='发现新增部门',
                                                                      add=f'{qw["name"]}   ID: {qw["id"]}',
                                                                      remarks='[注意事项] 程序只记录此条消息但不做如何修改')
        await qw_address_book.mgo_db_qw_department.insert_one(qw)
        logger.info(f'[+] 正在处理完毕 !!!')
        return True

    # 删除部门
    @qw_address_book.department_event_delete
    async def department_event_delete(db):
        logger.warning(f'[+] 发现删除部门: {db}')
        logger.info(f'[+] 正在处理 1 条 .......')
        await qw_address_book.log_event_add_delete_dpartment_relation(status='成功', event='发现删除部门',
                                                                      delete=f'{db["name"]}   ID: {db["id"]}',
                                                                      remarks='[注意事项] 程序只记录此条消息但不做任何修改')
        await qw_address_book.mgo_db_qw_department.delete_one(query={'_id': db['_id']})
        logger.info(f'[+] 正在处理完毕 !!!')

        return True

    # 部门改名
    @qw_address_book.department_event_change_name
    async def department_event_change_name(db, qw):
        logger.info(f'[+] 发现修改部门名称:  {db["id"]}  {db["name"]} -> {qw["name"]}')

        res = await qw_address_book.get_all_customer(db["name"])

        if len(res) == 0:
            logger.info(f'[+] 正在处理 1 条 .......')
            remarks = f'''[变动信息]\n[ID] -> {db["id"]}\n[姓名] -> {qw["name"]}'''
            await qw_address_book.log_event_department_change_name(status='成功', event='发现修改部门名称',
                                                                   change_name=f' [原部门名称] {db["name"]} -> [新部门名称] {qw["name"]}',
                                                                   remarks=remarks)
        else:
            logger.info(f'[+] 正在处理 {len(res)} 条 .......')
        await qw_address_book.update_customer_profile_form(res, event='发现修改部门名称')

        await qw_address_book.mgo_db_qw_department.update_one(query={'id': db["id"]},
                                                              data={'$set': {'name': qw['name']}})
        logger.info(f'[+] 正在处理完毕 !!!')

    # 部门关系被改变
    @qw_address_book.department_event_change_relation
    async def department_event_change_relation(db, qw):
        logger.info(f'[+] 发现修改部门关系:  {db["id"]}  {db["name"]}  {db["parentid"]}  -> {qw["parentid"]}')

        res = await qw_address_book.get_all_customer(db["name"])

        if not res:
            logger.info(f'[+] 正在处理 1 条 .......')
        else:
            logger.info(f'[+] 正在处理 {len(res)} 条.......')
        # logger.info(f'[+] 部门信息加入成员更新任务.......')
        # 给成员加任务
        # await qw_address_book.mgo_member_update_task.insert_one(qw)

        await qw_address_book.update_customer_profile_form(res, event='发现修改部门关系')

        await qw_address_book.mgo_db_qw_department.update_one(
            query={'_id': db["_id"]},
            data={
                '$set': {
                    'parentid': qw["parentid"]
                }
            }
        )
        logger.info(f'[+] 正在处理完毕 !!!')

    await event_init()
    await department_event_add()
    await department_event_delete()
    await department_event_change_name()
    await department_event_change_relation()

    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] <任务> 企业微信同步客户档案 处理耗时 {elapsed}s')
    # 间隔 1 秒循环运行
    time.sleep(1)
    await main()
