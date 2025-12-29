import json
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field, field_validator
from datasets import Dataset, load_from_disk

class BiliDoc(BaseModel):
    id: str = "unknown"
    question: str
    choices: List[str]
    answer: int
    category: str = "general"

    @field_validator("choices", mode="before")
    @classmethod
    def parse_choices(cls, v):
        if isinstance(v, str):
            try: return json.loads(v)
            except: return [c.strip() for c in v.split(",") if c.strip()]
        return v

def process_docs(dataset: Dataset) -> Dataset:
    return dataset.map(lambda x: BiliDoc.model_validate(x).model_dump())


def load_dataset(**kwargs):
    """加载本地 Arrow 格式数据集
    
    使用 load_from_disk 正确加载 Arrow 格式的数据集，避免字段丢失。
    
    Args:
        **kwargs: 必须包含 'dataset_path' 键，指定数据集路径（本地目录）
        
    Returns:
        DatasetDict: 加载的数据集字典
    """
    dataset_path = kwargs.get("dataset_path")
    if not dataset_path:
        raise ValueError("dataset_path must be specified in dataset_kwargs")
    
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"数据集路径不存在: {dataset_path}")
    
    # 使用 load_from_disk 加载 Arrow 格式数据
    dataset = load_from_disk(str(path))
    return dataset


def process_results(doc, results):
    import re
    text = re.sub(r"<think>.*?</think>", "", results[0], flags=re.DOTALL).strip()
    patterns = [r"(?:答案|选项|选|是|为)\s*[:：]?\s*([A-J])", r"\b([A-J])\b", r"([A-J])"]
    
    pred = None
    for p in patterns:
        if m := re.findall(p, text, re.I):
            pred = m[-1].upper()
            break
    
    acc = 1.0 if pred and (ord(pred) - ord('A')) == doc["answer"] else 0.0
    return {"acc": acc}

