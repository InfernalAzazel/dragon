from lunar_you_ying import JDSDK
from conf import Settings


class DragonLogger:
    """
    对简道云 Azazel-DragonLog 表单插入日志信息
    """
    program_exception_table = JDSDK(
        app_id=Settings.JD_APP_ID_BUSINESS,
        entry_id='60e28f280840eb000756835e',
        api_key=Settings.JD_API_KEY,
    )

    @staticmethod
    async def create_data(grade, project_name, program_type, business_name, error_msg, is_start_workflow=False):
        await DragonLogger.program_exception_table.create_data(data={
            # 日志级别
            'grade': {
                'value': grade
            },
            # 项目名称
            'project_name': {
                'value': project_name
            },
            # 程序类型
            'program_type': {
                'value': program_type
            },
            # 业务名称
            'business_name': {
                'value': business_name
            },
            # 异常信息
            'error_msg': {
                'value': error_msg
            },
        }, is_start_workflow=is_start_workflow)

    @staticmethod
    async def info(project_name, program_type, business_name, error_msg):
        """
        信息日志

        :param project_name: 项目名称
        :param program_type: 程序类型
        :param business_name: 业务名称
        :param error_msg: 异常信息
        """
        await DragonLogger.create_data(
            grade='信息',
            project_name=project_name,
            program_type=program_type,
            business_name=business_name,
            error_msg=error_msg
        )

    @staticmethod
    async def warn(project_name, program_type, business_name, error_msg):
        """
        警告日志

        :param project_name: 项目名称
        :param program_type: 程序类型
        :param business_name: 业务名称
        :param error_msg: 异常信息
        """
        await DragonLogger.create_data(
            grade='警告',
            project_name=project_name,
            program_type=program_type,
            business_name=business_name,
            error_msg=error_msg
        )

    @staticmethod
    async def error(project_name, program_type, business_name, error_msg):
        """
        异常日志

        :param project_name: 项目名称
        :param program_type: 程序类型
        :param business_name: 业务名称
        :param error_msg: 异常信息
        """
        await DragonLogger.create_data(
            grade='异常',
            project_name=project_name,
            program_type=program_type,
            business_name=business_name,
            error_msg=error_msg,
            is_start_workflow=True
        )
