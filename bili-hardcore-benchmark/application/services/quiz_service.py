"""答题核心服务

负责题目获取、答案选择策略和答题结果判断。
"""

import random
from typing import Protocol, Optional
from loguru import logger

from ..models.question import Question


class AIProvider(Protocol):
    """AI 提供者协议"""
    
    def predict(self, question: str, choices: list[str]) -> int:
        """预测答案
        
        Args:
            question: 题目内容
            choices: 选项列表
            
        Returns:
            预测的答案索引（0-based）
        """
        ...


class QuizService:
    """答题核心服务
    
    实现智能答题策略：
    - 已完整题目：随机选错误答案（避免通过60分）
    - 部分已知题目：从未尝试的选项中选择
    - 完全未知题目：使用 AI 判断
    """
    
    def __init__(self, ai_provider: AIProvider):
        """初始化答题服务
        
        Args:
            ai_provider: AI 提供者实例
        """
        self.ai_provider = ai_provider
    
    def select_answer(
        self,
        question: Question,
        use_ai_for_partial: bool = True
    ) -> tuple[int, str]:
        """选择答案
        
        Args:
            question: 题目实例
            use_ai_for_partial: 对于部分已知题目是否使用 AI（默认 True）
            
        Returns:
            (答案索引, 选择原因说明)
        """
        # 策略1：已完整题目，随机选错误答案
        if question.is_complete():
            wrong_choices = question.get_wrong_choices()
            if not wrong_choices:
                raise ValueError(f"题目 {question.id} 已完整但没有错误选项")
            
            answer_idx = random.choice(wrong_choices)
            reason = (
                f"已知正确答案为选项 {question.correct_answer + 1}，"
                f"故意选错以避免通过"
            )
            logger.info(f"题目 {question.id}: {reason}")
            return answer_idx, reason
        
        # 策略2：部分已知题目
        if question.is_partial():
            untried_choices = question.get_untried_choices()
            
            if not untried_choices:
                # 所有选项都尝试过但还没找到正确答案，这不应该发生
                raise ValueError(f"题目 {question.id} 所有选项都已尝试但未找到正确答案")
            
            # 如果只剩一个未尝试的选项，那它一定是正确答案
            if len(untried_choices) == 1:
                answer_idx = untried_choices[0]
                total_choices = len(question.choices)
                reason = (
                    f"逻辑推理：已尝试 {total_choices - 1} 个错误答案，"
                    f"剩余选项 {answer_idx + 1} 一定是正确答案"
                )
                logger.info(f"题目 {question.id}: {reason}")
                return answer_idx, reason
            
            if use_ai_for_partial and len(untried_choices) > 1:
                # 使用 AI 在剩余选项中判断
                try:
                    # 构造只包含未尝试选项的提示
                    filtered_choices = [
                        question.choices[i] for i in untried_choices
                    ]
                    ai_answer = self.ai_provider.predict(
                        question.question,
                        filtered_choices
                    )
                    # AI 返回的是 filtered_choices 中的索引，需要映射回原始索引
                    answer_idx = untried_choices[ai_answer]
                    reason = f"AI 在剩余 {len(untried_choices)} 个选项中推荐"
                    logger.info(f"题目 {question.id}: AI 选择索引 {ai_answer}，映射为选项 {answer_idx + 1}")
                    return answer_idx, reason
                except Exception as e:
                    logger.warning(f"AI 预测失败: {e}，随机选择未尝试选项")
            
            # 随机选择未尝试的选项
            answer_idx = random.choice(untried_choices)
            reason = f"随机选择（剩余 {len(untried_choices)} 个未尝试）"
            logger.info(f"题目 {question.id}: 随机选择未尝试的选项 {answer_idx} (选项 {answer_idx + 1})")
            return answer_idx, reason
        
        # 策略3：完全未知题目，使用 AI
        try:
            ai_answer = self.ai_provider.predict(
                question.question,
                question.choices
            )
            reason = f"AI 推荐"
            logger.info(f"题目 {question.id}: AI 选择答案 {ai_answer} (选项 {ai_answer + 1})")
            return ai_answer, reason
        except Exception as e:
            # AI 失败，随机选择
            logger.warning(f"AI 预测失败: {e}，随机选择答案")
            answer_idx = random.choice(range(len(question.choices)))
            reason = f"AI 失败，随机选择"
            logger.info(f"题目 {question.id}: 随机选择答案 {answer_idx} (选项 {answer_idx + 1})")
            return answer_idx, reason
    
    def should_skip_question(
        self,
        question: Question,
        current_score: int,
        safety_threshold: int
    ) -> bool:
        """判断是否应该跳过题目
        
        Args:
            question: 题目实例
            current_score: 当前分数
            safety_threshold: 安全阈值
            
        Returns:
            是否应该跳过
        """
        # 如果已知正确答案且接近阈值，跳过以避免分数过高
        if question.is_complete() and current_score >= safety_threshold - 5:
            logger.warning(
                f"题目 {question.id} 已完整且当前分数 {current_score} "
                f"接近阈值 {safety_threshold}，跳过该题"
            )
            return True
        
        return False
    
    def judge_result(
        self,
        question: Question,
        selected_answer: int,
        previous_score: int,
        current_score: int
    ) -> tuple[bool, Optional[int]]:
        """判断答题结果
        
        Args:
            question: 题目实例
            selected_answer: 选择的答案索引
            previous_score: 之前的分数
            current_score: 当前的分数
            
        Returns:
            (是否正确, 正确答案索引或None)
        """
        is_correct = current_score > previous_score
        correct_answer = selected_answer if is_correct else None
        
        if is_correct:
            logger.info(
                f"题目 {question.id} 回答正确！"
                f"分数: {previous_score} -> {current_score} (+{current_score - previous_score})"
            )
        else:
            logger.info(
                f"题目 {question.id} 回答错误。"
                f"分数保持: {current_score}"
            )
        
        return is_correct, correct_answer

