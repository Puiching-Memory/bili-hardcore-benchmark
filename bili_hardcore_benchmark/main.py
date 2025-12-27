"""程序主入口 - 答题模式

运行答题会话，收集题目数据。可多次运行累积数据。
"""

import random
import sys
import time
from typing import Any, Dict, Optional

from loguru import logger
from qrcode.constants import ERROR_CORRECT_L
from qrcode.main import QRCode

from .application.models.question import Question
from .application.services.benchmark_service import BenchmarkService
from .application.services.quiz_service import QuizService
from .common.exceptions import APIError, AuthError, BiliHardcoreError, QuizError
from .container import Container
from .infrastructure.bilibili.auth import BilibiliAuthClient
from .infrastructure.bilibili.senior import BilibiliSeniorClient
from .infrastructure.config.settings import get_settings


def display_qrcode(url: str) -> None:
    """显示二维码

    Args:
        url: 二维码URL
    """
    try:
        qr = QRCode(version=1, error_correction=ERROR_CORRECT_L, box_size=2, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii()
    except Exception as e:
        logger.warning(f"显示二维码失败: {e}")

    logger.info("请使用 B站APP 扫描二维码登录")
    logger.info("如果二维码无法正常显示，请访问: https://cli.im/ 手动生成二维码")
    logger.info(f"二维码URL: {url}")


def _extract_auth_tokens(login_data: Dict[str, Any]) -> tuple[str, str]:
    """从登录响应中提取认证令牌

    Args:
        login_data: 登录响应的 data 字段

    Returns:
        (access_token, csrf)

    Raises:
        AuthError: 如果缺少必要字段
    """
    access_token = login_data.get("access_token")

    # 提取 csrf (bili_jct)
    csrf = None
    cookie_info = login_data.get("cookie_info", {})
    for cookie in cookie_info.get("cookies", []):
        if cookie.get("name") == "bili_jct":
            csrf = cookie.get("value")
            break

    if not access_token:
        raise AuthError("登录响应缺少 access_token")
    if not csrf:
        raise AuthError("登录响应缺少 csrf (bili_jct)")

    return access_token, csrf


def _poll_login_status(
    auth_client: BilibiliAuthClient, auth_code: str, max_retries: int = 60
) -> tuple[str, str]:
    """轮询二维码登录状态

    Args:
        auth_client: 认证客户端
        auth_code: 认证码
        max_retries: 最大重试次数（默认60秒）

    Returns:
        (access_token, csrf)

    Raises:
        AuthError: 如果登录失败或超时
    """
    logger.info("等待扫码...")

    for i in range(max_retries):
        try:
            result = auth_client.poll_qrcode(auth_code)

            if result.get("code") == 0:
                login_data = result.get("data", {})
                access_token, csrf = _extract_auth_tokens(login_data)
                logger.info("✅ 登录成功！")
                return access_token, csrf

        except AuthError:
            # 如果是认证错误，直接抛出
            raise
        except Exception as e:
            logger.debug(f"轮询登录状态: {e}")

        time.sleep(1)

    raise AuthError("二维码登录超时（60秒）")


def qrcode_login(container: Container) -> tuple[str, str]:
    """二维码登录

    Args:
        container: 依赖注入容器

    Returns:
        (access_token, csrf)

    Raises:
        AuthError: 如果登录失败
    """
    auth_client = container.get_auth_client()

    # 获取二维码
    logger.info("正在获取二维码...")
    qrcode_data = auth_client.get_qrcode()
    url = qrcode_data["url"]
    auth_code = qrcode_data["auth_code"]

    # 显示二维码
    display_qrcode(url)

    # 轮询登录状态
    return _poll_login_status(auth_client, auth_code)


def _fetch_question(
    senior_client: BilibiliSeniorClient,
) -> tuple[Optional[Dict[str, Any]], bool]:
    """获取题目

    Args:
        senior_client: B站答题客户端

    Returns:
        (题目数据字典, 是否应该停止答题)
        题目数据字典包含 id, question, answers, question_num
        如果获取失败，返回 (None, should_stop)
        should_stop=True 表示需要验证码或达到答题限制，应该停止答题
        should_stop=False 表示临时错误，可以继续尝试
    """
    try:
        response = senior_client.get_question()

        if response.get("code") != 0:
            logger.warning("需要验证码验证或达到答题限制，停止答题")
            return None, True  # 返回 None 和 should_stop=True

        data = response.get("data", {})
        question_id = str(data.get("id"))
        question_text = data.get("question")
        answers = data.get("answers", [])
        question_num = data.get("question_num", 0)

        if not question_text or not answers:
            logger.warning("题目数据不完整，跳过")
            return None, False  # 数据不完整，可以继续尝试

        return {
            "id": question_id,
            "question": question_text,
            "answers": answers,
            "question_num": question_num,
            "choices": [ans.get("ans_text", "") for ans in answers],
        }, False  # 成功获取，不需要停止
    except Exception as e:
        logger.error(f"获取题目失败: {e}")
        return None, False  # 临时错误，可以继续尝试


def _handle_skip_question(
    question: Question,
    question_data: Dict[str, Any],
    senior_client: BilibiliSeniorClient,
    current_score: int,
) -> int:
    """处理跳过题目逻辑

    Args:
        question: 题目对象
        question_data: 题目数据
        senior_client: B站答题客户端
        current_score: 当前分数

    Returns:
        更新后的分数
    """
    logger.info("跳过该题，提交错误答案以获取下一题")

    question_id = question_data["id"]
    answers = question_data["answers"]

    # 已完整题目，选择错误答案
    wrong_choices = question.get_wrong_choices()
    if not wrong_choices:
        logger.warning(f"题目 {question_id} 已完整但没有错误选项，选择第一个选项")
        answer_idx = 0
    else:
        answer_idx = random.choice(wrong_choices)

    # 提交错误答案
    selected_answer = answers[answer_idx]
    try:
        submit_result = senior_client.submit_answer(
            question_id=int(question_id),
            ans_hash=selected_answer.get("ans_hash", ""),
            ans_text=selected_answer.get("ans_text", ""),
        )

        if submit_result.get("code") != 0:
            logger.warning(f"提交跳过答案失败: {submit_result}")
            return current_score

        # 等待处理并更新分数
        time.sleep(0.5)
        result_data = senior_client.get_result()
        new_score = int(result_data.get("score", current_score))
        logger.debug(f"跳过后分数: {new_score}")
        return new_score
    except Exception as e:
        logger.warning(f"提交跳过答案时出错: {e}")
        return current_score


def _get_category_scores(senior_client: BilibiliSeniorClient) -> Dict[str, int]:
    """获取分区得分

    Args:
        senior_client: B站答题客户端

    Returns:
        分区得分字典 {category: score}
    """
    try:
        result = senior_client.get_result()
        return {cat["category"]: cat["score"] for cat in result.get("scores", [])}
    except Exception as e:
        logger.debug(f"获取分区得分失败: {e}")
        return {}


def _detect_category(before_scores: Dict[str, int], after_scores: Dict[str, int]) -> Optional[str]:
    """推断题目分区

    通过比较答题前后的分区得分变化，推断题目所属分区。

    Args:
        before_scores: 答题前的分区得分
        after_scores: 答题后的分区得分

    Returns:
        检测到的分区名称，如果无法检测则返回 None
    """
    for category, after_score in after_scores.items():
        before_score = before_scores.get(category, 0)
        if after_score > before_score:
            logger.debug(f"检测到题目分区: {category}")
            return category
    return None


def _process_answer_result(
    question: Question,
    question_id: str,
    answer_idx: int,
    current_score: int,
    new_score: int,
    quiz_service: QuizService,
    benchmark_service: BenchmarkService,
) -> None:
    """处理答题结果并记录

    Args:
        question: 题目对象
        question_id: 题目ID
        answer_idx: 选择的答案索引
        current_score: 答题前分数
        new_score: 答题后分数
        quiz_service: 答题服务
        benchmark_service: 数据收集服务
    """
    # 判断结果
    is_correct, correct_answer = quiz_service.judge_result(
        question, answer_idx, current_score, new_score
    )

    # 只记录未完整题目的结果
    # 如果题目已完整，说明是故意选错以避免通过，不需要再记录
    if question.is_complete():
        return

    if is_correct:
        # 使用judge_result返回的correct_answer，而不是用户选择的answer_idx
        if correct_answer is not None:
            benchmark_service.record_correct_answer(question_id, correct_answer)
        else:
            # 如果correct_answer为None，说明判断逻辑有问题，使用answer_idx作为后备
            logger.warning(
                f"题目 {question_id} 判断正确但correct_answer为None，"
                f"使用answer_idx {answer_idx}"
            )
            benchmark_service.record_correct_answer(question_id, answer_idx)
    else:
        benchmark_service.record_wrong_answer(question_id, answer_idx)


def _process_question(
    question_data: Dict[str, Any],
    question: Question,
    senior_client: BilibiliSeniorClient,
    quiz_service: QuizService,
    benchmark_service: BenchmarkService,
    current_score: int,
) -> tuple[int, Optional[str]]:
    """处理一道题目（正常答题流程）

    Args:
        question_data: 题目数据
        question: 题目对象
        senior_client: B站答题客户端
        quiz_service: 答题服务
        benchmark_service: 数据收集服务
        current_score: 当前分数

    Returns:
        (更新后的分数, 检测到的分区)
    """
    question_id = question_data["id"]
    question_data["question"]
    choices = question_data["choices"]
    answers = question_data["answers"]

    # 选择答案
    answer_idx, reason = quiz_service.select_answer(question)
    logger.info(f"选择答案: {answer_idx + 1} ({choices[answer_idx]}) - {reason}")

    # 获取答题前的分区得分（用于推断题目分区）
    before_scores = _get_category_scores(senior_client)

    # 提交答案
    selected_answer = answers[answer_idx]
    submit_result = senior_client.submit_answer(
        question_id=int(question_id),
        ans_hash=selected_answer.get("ans_hash", ""),
        ans_text=selected_answer.get("ans_text", ""),
    )

    if submit_result.get("code") != 0:
        logger.error(f"提交答案失败: {submit_result}")
        return current_score, None

    # 等待处理
    time.sleep(0.5)

    # 获取结果
    result_data = senior_client.get_result()
    new_score = result_data.get("score", 0)

    # 推断题目分区
    after_scores = _get_category_scores(senior_client)
    detected_category = _detect_category(before_scores, after_scores)

    # 更新题目分区信息
    if detected_category and not question.category:
        question.category = detected_category

    # 处理答题结果并记录
    _process_answer_result(
        question, question_id, answer_idx, current_score, new_score, quiz_service, benchmark_service
    )

    return new_score, detected_category


def run_quiz_session(container: Container, access_token: str, csrf: str) -> None:
    """运行答题会话

    Args:
        container: 依赖注入容器
        access_token: 访问令牌
        csrf: CSRF 令牌
    """
    settings = container.settings

    # 验证用户等级
    logger.info("正在验证用户信息...")
    user_client = container.get_user_client(access_token)

    try:
        user_info = user_client.get_account_info()
        user_level = user_info.get("level", 0)
        user_name = user_info.get("name", "Unknown")

        logger.info(f"用户: {user_name} (等级: {user_level})")

        if user_level < 6:
            logger.error("❌ 当前用户等级不足6级，无法参与答题")
            sys.exit(1)
    except APIError as e:
        logger.error(f"获取用户信息失败: {e}")
        sys.exit(1)

    # 初始化服务
    senior_client = container.get_senior_client(access_token, csrf)
    quiz_service = container.get_quiz_service()
    benchmark_service = container.get_benchmark_service()

    # 获取初始分数
    try:
        result_data = senior_client.get_result()
        current_score = result_data.get("score", 0)
        logger.info(f"初始得分: {current_score}")

        if current_score >= settings.safety_threshold:
            logger.warning(
                f"⚠️  当前分数 {current_score} 已达到或超过安全阈值 {settings.safety_threshold}，"
                f"建议等待答题重置"
            )
            return
    except APIError as e:
        logger.error(f"获取答题结果失败: {e}")
        current_score = 0

    # 开始答题
    logger.info(f"开始答题会话，最多 {settings.max_questions} 题")
    logger.info(f"安全阈值: {settings.safety_threshold} 分")

    question_count = 0

    try:
        while question_count < settings.max_questions:
            try:
                # 1. 获取题目
                question_data, should_stop = _fetch_question(senior_client)

                # 如果需要停止（验证码或答题限制），退出循环
                if should_stop:
                    logger.info("停止答题")
                    break

                # 如果获取失败但不是停止条件，等待后继续
                if question_data is None:
                    time.sleep(2)  # 添加延迟避免快速重试
                    continue

                question_id = question_data["id"]
                question_text = question_data["question"]
                choices = question_data["choices"]
                question_num = question_data["question_num"]

                # 显示题目信息
                logger.info(f"\n第 {question_num} 题: {question_text}")
                for i, choice in enumerate(choices, 1):
                    logger.info(f"  {i}. {choice}")

                # 2. 获取或创建题目对象
                question = benchmark_service.get_or_create_question(
                    question_id=question_id, question_text=question_text, choices=choices
                )

                # 3. 检查是否应该跳过（只会跳过已完整题目）
                if quiz_service.should_skip_question(
                    question, current_score, settings.safety_threshold
                ):
                    current_score = _handle_skip_question(
                        question, question_data, senior_client, current_score
                    )
                    question_count += 1
                    continue

                # 4. 正常答题流程
                new_score, detected_category = _process_question(
                    question_data,
                    question,
                    senior_client,
                    quiz_service,
                    benchmark_service,
                    current_score,
                )

                current_score = new_score
                question_count += 1

                # 5. 显示进度
                category_info = f", 分区: {detected_category}" if detected_category else ""
                logger.info(
                    f"进度: 本次第 {question_count} 题 "
                    f"(B站题号: {question_num}{category_info})，"
                    f"当前得分: {current_score}"
                )

                # 6. 安全检查
                if current_score >= settings.safety_threshold:
                    logger.warning(
                        f"⚠️  当前得分 {current_score} 已达到安全阈值 {settings.safety_threshold}，"
                        f"停止答题以防止通过"
                    )
                    break

                # 短暂延迟
                time.sleep(1)

            except (APIError, QuizError) as e:
                logger.error(f"处理题目时出错: {e}")
                time.sleep(2)
                continue

    except KeyboardInterrupt:
        logger.info("\n⚠️  用户中断答题")

    # 显示统计信息
    stats = benchmark_service.get_statistics()
    logger.info("\n" + "=" * 50)
    logger.info("答题会话结束")
    logger.info(f"{stats}")
    logger.info("=" * 50)
    logger.info(f"\n数据已保存到: {settings.get_raw_data_path()}")
    logger.info("使用 'uv run python -m bili-hardcore.export' 导出 HuggingFace 格式")


def main() -> None:
    """主函数"""
    try:
        # 加载配置
        settings = get_settings()
        container = Container(settings)

        logger.info("=" * 50)
        logger.info("Bili-Hardcore-Benchmark - 答题模式")
        logger.info("=" * 50)

        # 登录
        access_token, csrf = qrcode_login(container)

        # 运行答题会话
        run_quiz_session(container, access_token, csrf)

    except BiliHardcoreError as e:
        logger.error(f"❌ {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n程序已中断")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"❌ 未预期的错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
