# handlers/__init__.py
from .add_task import router as add_task_router
from .start import router as start_router
from .help import router as help_router
from .tasks import router as tasks_router
from .group import router as group_router
from .about import router as about_router
from .edit_task import router as edit_task_router
from .delete_task import router as delete_task_router
from .balance import router as balance_router
from .join_group import router as join_group_router
from .group_info import router as group_info_router
from .exit_group import router as exit_group_router
from .temp_results import router as temp_results_router
from .group_settings import router as group_settings_router


routers = [
            start_router, help_router, group_router, about_router, 
            add_task_router, edit_task_router, delete_task_router, 
            tasks_router, balance_router, join_group_router, 
            group_info_router, exit_group_router, temp_results_router,
            group_settings_router
]