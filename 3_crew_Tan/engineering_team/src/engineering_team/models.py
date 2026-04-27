from pydantic import BaseModel


class ModuleSpec(BaseModel):
    module_name: str
    class_name: str
    description: str
    dependencies: list[str]


class SystemDesign(BaseModel):
    system_overview: str
    modules: list[ModuleSpec]
