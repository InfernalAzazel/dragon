from loguru import logger


class JdType:

    @staticmethod
    def subform(**kwargs):
        """
        子表单创建和更新 JSON 序列化

        subform_field: String 子表单字段ID

        data: Array [{}] 用于子表单查询返回的数据

        :param kwargs: 包含 subform_field，data
        :return: subform_data JSON
        """

        """
            forma_field = '_widget_1623150457402'
            data = [{
            '_id': '60bf5e3456262300083b2775',
            '_widget_1623150457454': '启用',
            '_widget_1623150457516': '百事',
            '_widget_1623150457539': '002',
            '_widget_1623150923283': '张三002'
                }, {
            '_id': '60bf5e91ff26fc00077e2f9d',
            '_widget_1623150457454': '启用',
            '_widget_1623150457516': '可乐',
            '_widget_1623150457539': '001',
            '_widget_1623150923283': '张三001'
            }]
        """

        for key, value in kwargs.items():
            if key == 'subform_field':
                subform_field = value
            elif key == 'data':
                data = value
            else:
                logger.error('[!] 差数不正确')
                return {}
        subform_data = {subform_field: {}}
        subform_data[subform_field]['value'] = []

        children = {}

        for data_value in data:
            for key, value in data_value.items():
                if key == '_id':
                    children[key] = {}
                    children[key]['value'] = value
                else:
                    children[key] = {}
                    children[key]['value'] = value
            subform_data[subform_field]['value'].append(children)
            children = {}

        # logger.info(subform_data)
        return subform_data
