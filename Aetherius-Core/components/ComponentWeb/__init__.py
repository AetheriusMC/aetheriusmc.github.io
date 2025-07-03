"""
Aetherius Component: Web Interface
=================================

官方Web控制台组件，提供完整的Web界面管理功能
"""

from aetherius.api.component import ComponentInfo

try:
    from .backend.web_component import WebComponent
except ImportError:
    try:
        # 如果完整版本导入失败，使用简化版本
        from .backend.simple_web_component import WebComponent
    except ImportError:
        # 最终使用基础版本
        from .backend.final_web_component import WebComponent

# Aetherius标准组件信息导出
__component_class__ = WebComponent
__version__ = "0.1.0"
__author__ = "Aetherius Team"

# Required component info for loader
COMPONENT_INFO = ComponentInfo(
    name="ComponentWeb",
    description="官方Web控制台组件，提供完整的Web界面管理功能",
    version=__version__,
    author=__author__,
    main_class="WebComponent"
)