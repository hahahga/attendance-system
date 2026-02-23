"""
文件处理相关工具函数
"""

import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from fastapi import UploadFile, HTTPException
from PIL import Image
import cv2
import numpy as np

from core.config import settings


def get_unique_filename(original_filename: str) -> str:
    """
    生成唯一的文件名
    
    Args:
        original_filename: 原始文件名
        
    Returns:
        唯一的文件名
    """
    file_ext = os.path.splitext(original_filename)[1]
    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{timestamp}_{unique_id}{file_ext}"


def save_upload_file(
    upload_file: UploadFile, 
    directory: str, 
    max_size: int = None
) -> str:
    """
    保存上传的文件
    
    Args:
        upload_file: 上传的文件对象
        directory: 保存目录
        max_size: 最大文件大小（字节）
        
    Returns:
        保存后的文件路径
        
    Raises:
        HTTPException: 文件大小超出限制
    """
    # 检查文件大小
    if max_size and upload_file.size and upload_file.size > max_size:
        raise HTTPException(
            status_code=413, 
            detail=f"文件大小超出限制，最大允许 {max_size / 1024 / 1024:.2f}MB"
        )
    
    # 确保目录存在
    os.makedirs(directory, exist_ok=True)
    
    # 生成唯一文件名
    filename = get_unique_filename(upload_file.filename)
    file_path = os.path.join(directory, filename)
    
    # 保存文件
    with open(file_path, "wb") as file:
        shutil.copyfileobj(upload_file.file, file)
    
    return file_path


def save_image_file(
    upload_file: UploadFile,
    directory: str,
    max_size: int = None,
    resize: Optional[Tuple[int, int]] = None,
    quality: int = 85
) -> str:
    """
    保存上传的图片文件
    
    Args:
        upload_file: 上传的文件对象
        directory: 保存目录
        max_size: 最大文件大小（字节）
        resize: 调整图片尺寸 (宽度, 高度)
        quality: 图片质量 (1-100)
        
    Returns:
        保存后的文件路径
        
    Raises:
        HTTPException: 文件大小超出限制或不是有效的图片
    """
    # 检查文件大小
    if max_size and upload_file.size and upload_file.size > max_size:
        raise HTTPException(
            status_code=413, 
            detail=f"文件大小超出限制，最大允许 {max_size / 1024 / 1024:.2f}MB"
        )
    
    # 确保目录存在
    os.makedirs(directory, exist_ok=True)
    
    # 生成唯一文件名
    filename = get_unique_filename(upload_file.filename)
    file_path = os.path.join(directory, filename)
    
    try:
        # 使用PIL处理图片
        image = Image.open(upload_file.file)
        
        # 转换为RGB模式（处理RGBA或其他格式）
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # 调整图片尺寸
        if resize:
            image = image.resize(resize, Image.LANCZOS)
        
        # 保存图片
        image.save(file_path, "JPEG", quality=quality)
        
        return file_path
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无效的图片文件: {str(e)}")


def delete_file(file_path: str) -> bool:
    """
    删除文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否成功删除
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False


def get_file_size(file_path: str) -> int:
    """
    获取文件大小
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小（字节）
    """
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    return 0


def get_file_extension(filename: str) -> str:
    """
    获取文件扩展名
    
    Args:
        filename: 文件名
        
    Returns:
        文件扩展名（包含点号）
    """
    return os.path.splitext(filename)[1].lower()


def is_allowed_file(filename: str, allowed_extensions: List[str]) -> bool:
    """
    检查文件扩展名是否在允许的列表中
    
    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名列表
        
    Returns:
        是否允许
    """
    file_ext = get_file_extension(filename)
    return file_ext in allowed_extensions


def load_image(file_path: str) -> np.ndarray:
    """
    加载图片为numpy数组
    
    Args:
        file_path: 图片路径
        
    Returns:
        图片的numpy数组
    """
    return cv2.imread(file_path)


def save_image(image: np.ndarray, file_path: str) -> bool:
    """
    保存numpy数组为图片
    
    Args:
        image: 图片的numpy数组
        file_path: 保存路径
        
    Returns:
        是否成功保存
    """
    try:
        cv2.imwrite(file_path, image)
        return True
    except Exception:
        return False


def resize_image(image: np.ndarray, width: int, height: int) -> np.ndarray:
    """
    调整图片尺寸
    
    Args:
        image: 图片的numpy数组
        width: 目标宽度
        height: 目标高度
        
    Returns:
        调整后的图片
    """
    return cv2.resize(image, (width, height))


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    将图片转换为灰度图
    
    Args:
        image: 图片的numpy数组
        
    Returns:
        灰度图
    """
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def create_directory(directory: str) -> bool:
    """
    创建目录
    
    Args:
        directory: 目录路径
        
    Returns:
        是否成功创建
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception:
        return False


def clean_directory(directory: str, keep_subdirs: bool = True) -> bool:
    """
    清理目录中的文件
    
    Args:
        directory: 目录路径
        keep_subdirs: 是否保留子目录
        
    Returns:
        是否成功清理
    """
    try:
        if not os.path.exists(directory):
            return True
        
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path) and not keep_subdirs:
                shutil.rmtree(item_path)
        
        return True
    except Exception:
        return False


def get_relative_path(file_path: str, base_path: str) -> str:
    """
    获取相对路径
    
    Args:
        file_path: 文件路径
        base_path: 基础路径
        
    Returns:
        相对路径
    """
    try:
        return os.path.relpath(file_path, base_path)
    except ValueError:
        return file_path


def ensure_directory_exists(directory: str) -> None:
    """
    确保目录存在，不存在则创建
    
    Args:
        directory: 目录路径
    """
    Path(directory).mkdir(parents=True, exist_ok=True)