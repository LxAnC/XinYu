"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    app_name: str = "心语"
    debug: bool = True
    secret_key: str = "dev-secret-key"

    # 数据库配置（开发模式使用 SQLite，生产使用 MySQL）
    database_url: str = "sqlite:///./xinyu.db"

    # Redis配置
    redis_url: str = "redis://localhost:6379/0"

    # JWT配置
    jwt_secret_key: str = "dev-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7

    # 短信服务
    sms_access_key: str = ""
    sms_secret_key: str = ""
    sms_sign_name: str = "心语"
    sms_template_code: str = ""

    # 微信配置
    wechat_app_id: str = ""
    wechat_app_secret: str = ""

    # 微信支付
    wechat_pay_mch_id: str = ""
    wechat_pay_api_key: str = ""
    wechat_pay_notify_url: str = ""

    # 文件上传
    upload_dir: str = "uploads"
    max_upload_size: int = 5 * 1024 * 1024  # 5MB

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
