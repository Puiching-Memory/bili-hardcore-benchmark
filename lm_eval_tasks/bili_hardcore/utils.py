"""Bili Hardcore 任务工具函数"""

from pathlib import Path
from datasets import Dataset, load_from_disk


def process_docs(dataset: Dataset) -> Dataset:
    """处理数据集文档
    
    将数据集转换为 lm_eval 需要的格式。
    数据集应包含：id, question, choices, answer, category
    """
    def _process_doc(doc):
        doc_id = doc.get("id", "unknown")
        
        # 确保 choices 是列表格式
        choices = doc.get("choices", [])
        if not isinstance(choices, list):
            # 如果 choices 是字符串或其他格式，尝试转换
            if isinstance(choices, str):
                # 尝试解析字符串格式的列表
                import json
                try:
                    choices = json.loads(choices)
                except (json.JSONDecodeError, TypeError):
                    # 如果无法解析，尝试按分隔符分割
                    choices = [c.strip() for c in choices.split(",") if c.strip()]
            else:
                choices = list(choices) if hasattr(choices, '__iter__') else [choices]
        
        # 检查 choices 是否为空
        if not choices or len(choices) == 0:
            raise ValueError(
                f"Empty choices list for document. "
                f"Doc ID: {doc_id}, "
                f"Question: {doc.get('question', 'N/A')[:50]}..., "
                f"Raw choices value: {repr(doc.get('choices', 'N/A'))}"
            )
        
        # 确保 answer 是整数（0-based 索引）
        answer = doc.get("answer", 0)
        if not isinstance(answer, int):
            try:
                answer = int(answer)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Invalid answer value '{doc.get('answer')}' (cannot convert to int). "
                    f"Doc ID: {doc_id}"
                )
        
        # 验证 answer 索引是否在有效范围内
        if answer < 0 or answer >= len(choices):
            raise ValueError(
                f"Invalid answer index {answer} for choices of length {len(choices)}. "
                f"Doc ID: {doc_id}, "
                f"Question: {doc.get('question', 'N/A')[:50]}..., "
                f"Choices: {choices}"
            )
        
        return {
            "question": doc.get("question", ""),
            "choices": choices,
            "answer": answer,
            "category": doc.get("category", "general"),
            "id": doc_id,
        }
    
    return dataset.map(_process_doc)


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
    """处理单选题的生成结果（用于 generate_until 模式）
    
    将模型生成的文本（如 "A"、"B"、"C"、"D"）转换为索引并计算准确率。
    
    Args:
        doc: 文档，包含 answer 字段（0-based 索引）
        results: 生成结果列表，第一个元素是生成的文本
        
    Returns:
        dict: 包含准确率信息的字典
    """
    import re
    pred_text = results[0].strip()
    
    # 0. 处理推理模型（如 DeepSeek-R1），移除 <think> 标签及其内容
    # 这样可以避免正则匹配到推理过程中的选项字母
    pred_text = re.sub(r"<think>.*?</think>", "", pred_text, flags=re.DOTALL).strip()
    
    # 1. 尝试匹配常见的回答格式，如 "答案是A", "选项 B", "选C", "应该选 D"
    # 优先匹配最后出现的字母，因为模型可能会先重复问题再给出答案
    patterns = [
        r"(?:答案|选项|选|应该选|是|为|最终答案|结论)\s*[:：]?\s*([A-D])",
        r"\b([A-D])\b",
        r"([A-D])"
    ]
    
    pred_letter = None
    for pattern in patterns:
        matches = re.findall(pattern, pred_text, re.IGNORECASE)
        if matches:
            pred_letter = matches[-1].upper() # 取最后一个匹配项
            break
    
    # 获取正确答案索引
    correct_index = doc["answer"]
    
    # 将字母转换为索引（A=0, B=1, C=2, D=3）
    if pred_letter:
        pred_index = ord(pred_letter) - ord('A')
        exact_match = 1 if pred_index == correct_index else 0
    else:
        # 如果完全无法解析，则认为回答错误，不再默认选 A
        exact_match = 0
    
    return {"acc": exact_match}

