# ══════════════════════════════════════════════════════════
#  AI Provider — "Cisca" Academic Advisor (Gemini, multi-key rotation)
# ══════════════════════════════════════════════════════════
#  Requires: pip install google-genai

import os
import itertools

from google import genai
from google.genai import types

_DEFAULT_KEYS = [
    os.environ.get("GEMINI_KEY_1", ""),
    os.environ.get("GEMINI_KEY_2", ""),
    os.environ.get("GEMINI_KEY_3", ""),
    os.environ.get("GEMINI_KEY_4", ""),
]

_env_keys = os.environ.get("GEMINI_API_KEYS")
GEMINI_API_KEYS = [k.strip() for k in _env_keys.split(",") if k.strip()] if _env_keys else _DEFAULT_KEYS

UNIVERSITY_SYSTEM_PROMPT = """
أنت "سيسكا" (Cisca)، مساعد ذكي وموظف إرشاد أكاديمي في "المعهد العالي لعلوم الحاسب ونظم المعلومات" (Smart Institute).
مهمتك الأساسية هي الرد على استفسارات الطلاب بخصوص اللائحة، القوانين، والمقررات الدراسية باللغة العربية (أو اللهجة المصرية بشكل مهني وودود).

### قواعد عامة للمعهد:
- التدريب الصيفي: يعد جزءاً مهماً في بناء مهارات الطالب العملية وتطبيق ما تعلموه، وربطهم بسوق العمل.
- المواد الاختيارية: يمكن للطالب اختيارها حسب اهتماماته في مجالات معينة.
- لا يمكن تسجيل مادة قبل اجتياز المادة المتطلبة لها (Prerequisite).

### الخطة الدراسية للمعهد:
1. السنة الأولى (سنة تأسيسية): تهدف إلى بناء قاعدة علمية في الرياضيات والعلوم الأساسية.
2. السنة الثانية: تركز على التطبيقات الأولية للبرمجة والنظريات الحسابية.
3. السنة الثالثة: تركز على المهارات التقنية المتقدمة والتخصصات المتعلقة بالحوسبة.
4. السنة الرابعة: تركز على المشاريع العملية والتخصصات المتقدمة.

### تعليمات هامة لتنسيق الرد:
- ممنوع منعاً باتاً استخدام أي علامات تنسيق (Markdown) مثل النجوم أو الهاشتاج.
- استخدم النص العادي فقط.
- التزم فقط ببيانات الطالب المذكورة أدناه. إذا لم تكن السنة والترم كافيين لتحديد المواد، اسأل الطالب عن سنته الدراسية ولا تفترض أنه في بداية الدراسة.
- إذا سأل الطالب عن اسم الدكتور الذي يدرس مادة معينة، ابحث في قائمة بيانات الدكاترة وأجب باسم الدكتور مباشرة.
- رد باختصار، بدون علامات تنسيق، ومنظم.
"""


class AIProvider:
    def generate(self, message: str, system_instruction: str) -> str:
        raise NotImplementedError


class GeminiProvider(AIProvider):
    def __init__(self):
        self._key_cycle = itertools.cycle(GEMINI_API_KEYS)

    def generate(self, message: str, system_instruction: str) -> str:
        last_error = None
        for _ in range(len(GEMINI_API_KEYS)):
            current_key = next(self._key_cycle)
            try:
                client = genai.Client(api_key=current_key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=message,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.1,
                    ),
                )
                return response.text or ""
            except Exception as e:
                last_error = e
                if "429" in str(e):
                    continue
                raise
        raise RuntimeError(
            f"عذراً، جميع مفاتيح الوصول استهلكت طاقتها اليومية. ({last_error})"
        )


_provider_instance = None


def get_ai_provider() -> AIProvider:
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = GeminiProvider()
    return _provider_instance