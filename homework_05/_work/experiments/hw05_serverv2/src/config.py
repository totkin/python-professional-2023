"""Получение конфигурации"""
from dynaconf import LazySettings

config = LazySettings(settings_files=["config.yaml"], environments=True)
