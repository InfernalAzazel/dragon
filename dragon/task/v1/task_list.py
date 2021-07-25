import logging

from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from task.v1.qw_address_book_department_task import QWAddressBookDepartmentTask


class TaskList:
    """
    登记任务
    """

    @staticmethod
    def register():
        executors = {
            'default': ThreadPoolExecutor(200),
            'processpool': ProcessPoolExecutor(10)
        }

        job_defaults = {
            'coalesce': True,  # 是否合并执行
            'max_instances': 1,  # 最大实例
            'misfire_grace_time': 60
        }

        # 企业微信同步客户档案
        logging.getLogger("apscheduler.scheduler").setLevel(logging.ERROR)
        scheduler = AsyncIOScheduler(executors=executors, job_defaults=job_defaults)
        scheduler.add_job(QWAddressBookDepartmentTask.run, 'interval', seconds=3)
        scheduler.start()
