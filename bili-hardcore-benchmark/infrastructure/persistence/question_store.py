"""题目存储实现

使用JSON文件存储题目数据（中间格式）。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from loguru import logger

from ...common.exceptions import DataError


class JSONQuestionStore:
    """JSON 题目存储
    
    存储格式：
    {
        "version": "1.0",
        "updated_at": "2024-01-15T10:30:00",
        "questions": {
            "question_id": {
                "question": "题目内容",
                "choices": ["选项1", "选项2", "选项3", "选项4"],
                "correct_answer": 2,  # 或缺失
                "wrong_answers": [0, 1],  # 或缺失
                "category": "分类",
                "attempts": 3,
                "last_attempt": "2024-01-15T10:25:00"
            }
        }
    }
    
    注意：id 不存储在值中，因为它已经是字典的 key
    """
    
    def __init__(self, file_path: Path):
        """初始化存储
        
        Args:
            file_path: JSON 文件路径
        """
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> Dict[str, dict]:
        """加载所有题目
        
        Returns:
            题目ID到题目数据的映射
            
        Raises:
            FileNotFoundError: 如果文件不存在
            DataError: 如果文件格式错误
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {self.file_path}")
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                raise DataError("数据格式错误：根对象不是字典")
            
            questions = data.get('questions', {})
            if not isinstance(questions, dict):
                raise DataError("数据格式错误：questions 不是字典")
            
            logger.debug(f"从 {self.file_path} 加载了 {len(questions)} 道题目")
            return questions
            
        except json.JSONDecodeError as e:
            raise DataError(f"JSON 解析失败: {e}") from e
        except Exception as e:
            raise DataError(f"加载数据失败: {e}") from e
    
    def save(self, questions: Dict[str, dict]) -> None:
        """保存所有题目
        
        Args:
            questions: 题目ID到题目数据的映射
            
        Raises:
            DataError: 如果保存失败
        """
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "questions": questions
            }
            
            # 先写入临时文件，成功后再重命名（原子操作）
            temp_path = self.file_path.with_suffix('.tmp')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 重命名（Windows 上需要先删除目标文件）
            if self.file_path.exists():
                self.file_path.unlink()
            temp_path.rename(self.file_path)
            
            logger.debug(f"保存了 {len(questions)} 道题目到 {self.file_path}")
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            raise DataError(f"保存数据失败: {e}") from e

