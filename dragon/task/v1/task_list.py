from multiprocessing import Process


from task.v1.qw_address_book_department_task import QWAddressBookDepartmentTask


class TaskList:
    """
    登记任务
    """

    @staticmethod
    def register():
        pass

        # department_ps = Process(target=QWAddressBookDepartmentTask.run, name='企业微信同步客户档案')
        # member_ps = Process(target=QWAddressBookMemberTask.run, name='企业微信同步人员档案')
        # department_ps.start()
        # member_ps.start()
