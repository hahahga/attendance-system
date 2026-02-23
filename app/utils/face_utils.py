"""
人脸识别相关工具函数
"""

import os
import pickle
from typing import List, Optional, Tuple, Dict

import cv2
import face_recognition
import numpy as np
from PIL import Image

from core.config import settings
from utils.file_utils import load_image, save_image, ensure_directory_exists


class FaceRecognitionUtils:
    """人脸识别工具类"""
    
    def __init__(self, encoding_file: str = None):
        """
        初始化人脸识别工具
        
        Args:
            encoding_file: 人脸编码文件路径
        """
        self.encoding_file = encoding_file or os.path.join(
            settings.UPLOAD_DIR, "face_encodings.pkl"
        )
        self.known_face_encodings = []
        self.known_face_ids = []
        self.load_face_encodings()
    
    def load_face_encodings(self) -> None:
        """加载已知人脸编码"""
        if os.path.exists(self.encoding_file):
            try:
                with open(self.encoding_file, "rb") as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data.get("encodings", [])
                    self.known_face_ids = data.get("ids", [])
            except Exception as e:
                print(f"加载人脸编码失败: {str(e)}")
                self.known_face_encodings = []
                self.known_face_ids = []
    
    def save_face_encodings(self) -> None:
        """保存已知人脸编码"""
        ensure_directory_exists(os.path.dirname(self.encoding_file))
        try:
            with open(self.encoding_file, "wb") as f:
                pickle.dump({
                    "encodings": self.known_face_encodings,
                    "ids": self.known_face_ids
                }, f)
        except Exception as e:
            print(f"保存人脸编码失败: {str(e)}")
    
    def extract_face_encoding(self, image_path: str) -> Optional[np.ndarray]:
        """
        从图片中提取人脸编码
        
        Args:
            image_path: 图片路径
            
        Returns:
            人脸编码，如果未检测到人脸则返回None
        """
        try:
            # 加载图片
            image = face_recognition.load_image_file(image_path)
            
            # 检测人脸位置
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                return None
            
            # 提取人脸编码（使用第一个人脸）
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if face_encodings:
                return face_encodings[0]
            
            return None
        except Exception as e:
            print(f"提取人脸编码失败: {str(e)}")
            return None
    
    def extract_face_encodings_from_image(self, image: np.ndarray) -> List[np.ndarray]:
        """
        从图片数组中提取所有人脸编码
        
        Args:
            image: 图片数组
            
        Returns:
            人脸编码列表
        """
        try:
            # 检测人脸位置
            face_locations = face_recognition.face_locations(image)
            
            # 提取人脸编码
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            return face_encodings
        except Exception as e:
            print(f"提取人脸编码失败: {str(e)}")
            return []
    
    def add_face(self, face_id: str, image_path: str) -> bool:
        """
        添加人脸到已知人脸库
        
        Args:
            face_id: 人脸ID（通常是用户ID）
            image_path: 图片路径
            
        Returns:
            是否成功添加
        """
        face_encoding = self.extract_face_encoding(image_path)
        
        if face_encoding is None:
            return False
        
        # 检查是否已存在
        if face_id in self.known_face_ids:
            # 更新现有的人脸编码
            index = self.known_face_ids.index(face_id)
            self.known_face_encodings[index] = face_encoding
        else:
            # 添加新的人脸编码
            self.known_face_encodings.append(face_encoding)
            self.known_face_ids.append(face_id)
        
        # 保存到文件
        self.save_face_encodings()
        
        return True
    
    def remove_face(self, face_id: str) -> bool:
        """
        从已知人脸库中移除人脸
        
        Args:
            face_id: 人脸ID
            
        Returns:
            是否成功移除
        """
        if face_id in self.known_face_ids:
            index = self.known_face_ids.index(face_id)
            self.known_face_encodings.pop(index)
            self.known_face_ids.pop(index)
            
            # 保存到文件
            self.save_face_encodings()
            
            return True
        
        return False
    
    def recognize_face(self, image_path: str, tolerance: float = 0.6) -> Optional[str]:
        """
        识别图片中的人脸
        
        Args:
            image_path: 图片路径
            tolerance: 人脸识别容差值
            
        Returns:
            识别到的人脸ID，如果未识别到则返回None
        """
        face_encoding = self.extract_face_encoding(image_path)
        
        if face_encoding is None:
            return None
        
        if not self.known_face_encodings:
            return None
        
        # 比较人脸编码
        face_distances = face_recognition.face_distance(
            self.known_face_encodings, face_encoding
        )
        
        if len(face_distances) == 0:
            return None
        
        # 找到最匹配的人脸
        best_match_index = np.argmin(face_distances)
        
        # 检查匹配度
        if face_distances[best_match_index] <= tolerance:
            return self.known_face_ids[best_match_index]
        
        return None
    
    def recognize_faces(self, image_path: str, tolerance: float = 0.6) -> List[Tuple[str, Tuple[int, int, int, int]]]:
        """
        识别图片中的所有人脸
        
        Args:
            image_path: 图片路径
            tolerance: 人脸识别容差值
            
        Returns:
            识别结果列表，每个元素为(人脸ID, 人脸位置)
        """
        try:
            # 加载图片
            image = face_recognition.load_image_file(image_path)
            
            # 检测人脸位置
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                return []
            
            # 提取人脸编码
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if not face_encodings:
                return []
            
            results = []
            
            if not self.known_face_encodings:
                # 没有已知人脸，返回未知人脸
                for location in face_locations:
                    results.append(("unknown", location))
                return results
            
            # 识别每个人脸
            for face_encoding, location in zip(face_encodings, face_locations):
                # 比较人脸编码
                face_distances = face_recognition.face_distance(
                    self.known_face_encodings, face_encoding
                )
                
                if len(face_distances) == 0:
                    results.append(("unknown", location))
                    continue
                
                # 找到最匹配的人脸
                best_match_index = np.argmin(face_distances)
                
                # 检查匹配度
                if face_distances[best_match_index] <= tolerance:
                    face_id = self.known_face_ids[best_match_index]
                else:
                    face_id = "unknown"
                
                results.append((face_id, location))
            
            return results
        except Exception as e:
            print(f"人脸识别失败: {str(e)}")
            return []
    
    def detect_faces(self, image_path: str) -> List[Tuple[int, int, int, int]]:
        """
        检测图片中的人脸位置
        
        Args:
            image_path: 图片路径
            
        Returns:
            人脸位置列表，每个位置为(top, right, bottom, left)
        """
        try:
            # 加载图片
            image = face_recognition.load_image_file(image_path)
            
            # 检测人脸位置
            face_locations = face_recognition.face_locations(image)
            
            return face_locations
        except Exception as e:
            print(f"人脸检测失败: {str(e)}")
            return []
    
    def draw_face_rectangles(self, image_path: str, output_path: str, face_locations: List[Tuple[int, int, int, int]] = None, face_ids: List[str] = None) -> None:
        """
        在图片上绘制人脸矩形框
        
        Args:
            image_path: 输入图片路径
            output_path: 输出图片路径
            face_locations: 人脸位置列表
            face_ids: 人脸ID列表
        """
        try:
            # 加载图片
            image = cv2.imread(image_path)
            
            # 如果没有提供人脸位置，则检测人脸
            if face_locations is None:
                face_locations = self.detect_faces(image_path)
            
            # 绘制人脸矩形框
            for i, (top, right, bottom, left) in enumerate(face_locations):
                # 绘制矩形框
                cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
                
                # 如果提供了人脸ID，则绘制标签
                if face_ids and i < len(face_ids):
                    label = face_ids[i]
                    cv2.putText(image, label, (left, top - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # 保存结果图片
            save_image(image, output_path)
        except Exception as e:
            print(f"绘制人脸矩形框失败: {str(e)}")
    
    def get_face_count(self, image_path: str) -> int:
        """
        获取图片中的人脸数量
        
        Args:
            image_path: 图片路径
            
        Returns:
            人脸数量
        """
        face_locations = self.detect_faces(image_path)
        return len(face_locations)
    
    def get_known_faces_count(self) -> int:
        """
        获取已知人脸数量
        
        Returns:
            已知人脸数量
        """
        return len(self.known_face_ids)
    
    def get_known_face_ids(self) -> List[str]:
        """
        获取所有已知人脸ID
        
        Returns:
            已知人脸ID列表
        """
        return self.known_face_ids.copy()
    
    def clear_known_faces(self) -> None:
        """清空已知人脸库"""
        self.known_face_encodings = []
        self.known_face_ids = []
        self.save_face_encodings()


# 创建全局人脸识别工具实例
face_recognition_utils = FaceRecognitionUtils()