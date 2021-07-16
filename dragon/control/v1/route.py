from fastapi import APIRouter

from api.v1 import jd_front_event, jd_web_hook

# 暴露出路由
jd_front_event_router = APIRouter()

jd_web_hook_router = APIRouter()

# 控制器
# 注册 简道云 前端事件 的 api
jd_front_event.copy_value_to_field.register(jd_front_event_router)
jd_front_event.activity_postponed_count.register(jd_front_event_router)
jd_front_event.test.register(jd_front_event_router)

# 注册 简道云 web hook 的 api
jd_web_hook.customer_error_activation.register(jd_web_hook_router)
jd_web_hook.product_change_application.register(jd_web_hook_router)
jd_web_hook.entry_application_verify_field.register(jd_web_hook_router)
jd_web_hook.free_contract_batch_modify.register(jd_web_hook_router)
jd_web_hook.activity_delay_apply.register(jd_web_hook_router)
jd_web_hook.personnel_maintain.register(jd_web_hook_router)
jd_web_hook.add_or_modify_logistics_note.register(jd_web_hook_router)