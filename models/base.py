# -*- coding: utf-8 -*-
"""
SQLModel のベースクラスとMetaData管理
"""
from sqlmodel import SQLModel, MetaData

# 共通のMetaDataインスタンスを作成
metadata = MetaData()

class BaseModel(SQLModel):
    """全モデルの基底クラス"""
    class Config:
        from_attributes = True

# SQLModelのmetadataを設定
SQLModel.metadata = metadata
