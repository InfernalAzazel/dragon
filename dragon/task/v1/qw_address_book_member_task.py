"""
 企业微信成员变动自动更新人员档案

 1.新增
 2.修改
 3.移动
 3.删除

"""
import asyncio
import time
from loguru import logger
from utils import QWAddressBookMember


class QWAddressBookMemberTask:

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
    logger.info(f'[+] <任务> 企业微信同步人员档案 计算中 ......')
    qw_a_b_member = QWAddressBookMember()

    # 初始化
    @qw_a_b_member.event_init
    async def member_event_init():
        pass
        return

    # 新增成员
    @qw_a_b_member.event_add
    async def member_event_add(qw_member):
        logger.info(f'[+] <任务> 发现新增成员 userid: {qw_member["userid"]} name: {qw_member["name"]}')
        await qw_a_b_member.mgo_db_member_init.insert_one(qw_member)

    # 删除成员
    @qw_a_b_member.event_delete
    async def member_event_delete(db_member):
        logger.info(f'[+] <任务> 发现删除成员 userid: {db_member["userid"]} name: {db_member["name"]}')
        await qw_a_b_member.mgo_db_member_init.delete_one({'_id': db_member['_id']})

    # 成员名称被修改
    @qw_a_b_member.event_change_name
    async def member_event_change_name(db_member, qw_member):
        print(qw_member)
        logger.info(
            f'[+] <任务> 成员名称被修改 userid: {db_member["userid"]} name: {db_member["name"]} -> '
            f'{qw_member["name"]}'
        )
        await qw_a_b_member.mgo_db_member_init.update_one(
            query={'userid': db_member["userid"]},
            data={'$set': {'name': qw_member['name']}})

    # 成员与部门关系被改变
    @qw_a_b_member.event_change_relation
    async def member_event_change_relation(db_member, qw_member, change_department):
        pass
        logger.info(
            f'[+] <任务> 成员的部门ID变动 userid: {qw_member["userid"]} name: {qw_member["name"]} '
            f' department: {db_member["department"]} -> department: {qw_member["department"]} change: {change_department}'
        )

        await qw_a_b_member.mgo_db_member_init.update_one({'userid': qw_member['userid']},
                                                          {'$set': {'department': qw_member["department"]}})

    # 部门关系被改变更新所有成员
    @qw_a_b_member.event_change_relation_d
    async def member_event_change_relation_d(update):
        pass
        logger.info(
            f'[+] <任务> 成员所在部门变动 部门: {update["name"]}'
        )

        c = await qw_a_b_member.query_personnel_files_form(cid=update['id'])

        print(c)

        # print(children_department)
        # print(update)

    await member_event_init()
    await member_event_add()
    await member_event_delete()
    await member_event_change_name()
    await member_event_change_relation()
    # await member_event_change_relation_d()

    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] <任务> 企业微信同步人员档案 处理耗时 {elapsed}s')

    # 间隔 1 秒循环运行
    time.sleep(1)
    await main()
