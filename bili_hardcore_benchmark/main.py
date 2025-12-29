import random
import time

from loguru import logger

from .container import Container
from .core.exceptions import AuthError, BiliHardcoreError, QuizError
from .core.models import LoginData
from .core.settings import get_settings


def run_quiz(container: Container, login: LoginData) -> None:
    if not login.csrf:
        raise AuthError("登录信息不完整，缺少 CSRF")
    senior = container.get_senior_client(login.access_token, login.csrf)
    quiz, benchmark = container.quiz_service, container.benchmark_service

    result = senior.get_result()
    score = result.score
    category_scores = {s.category: s.score for s in result.scores}

    for _ in range(container.settings.max_questions):
        if score >= container.settings.safety_threshold:
            break
        try:
            q_data = senior.get_question()
            q = benchmark.get_or_create_question(str(q_data.id), q_data.question, q_data.choices)
            logger.info(f"题目: {q.question[:30]}...")

            if quiz.should_skip_question(q, score, container.settings.safety_threshold):
                idx = random.choice(q.wrong_answers or [0])
                logger.info(f"策略: 故意选错 (当前分数: {score})")
                senior.submit_answer(
                    int(q.id), q_data.answers[idx].ans_hash, q_data.answers[idx].ans_text
                )
                benchmark.record_attempt(q.id)
            else:
                idx, strategy = quiz.select_answer(q)
                logger.info(f"策略: {strategy} -> 选项 {idx}: {q.choices[idx]}")
                senior.submit_answer(
                    int(q.id), q_data.answers[idx].ans_hash, q_data.answers[idx].ans_text
                )
                time.sleep(0.5)

                new_result = senior.get_result()
                new_score = new_result.score

                if new_score > score:
                    # 通过分数变化推算分类
                    for s in new_result.scores:
                        if s.score > category_scores.get(s.category, 0):
                            q.category = s.category
                            logger.success(
                                f"✅ 回答正确! 分区: {s.category} | 分数: {score} -> {new_score}"
                            )
                            break
                    else:
                        logger.success(f"✅ 回答正确! 分数: {score} -> {new_score}")

                    benchmark.record_correct_answer(q.id, idx)
                else:
                    logger.warning(f"❌ 回答错误. 分数未变: {score}")
                    benchmark.record_wrong_answer(q.id, idx)

                score = new_score
                category_scores = {s.category: s.score for s in new_result.scores}
            time.sleep(1)
        except QuizError as e:
            logger.error(f"Quiz Error: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected Error: {e}")
            break


def main() -> None:
    try:
        container = Container(get_settings())
        login = container.auth_service.login()
        run_quiz(container, login)
    except BiliHardcoreError as e:
        logger.error(e)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
