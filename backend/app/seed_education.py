"""교육용 시드 — 12개월치 가상 대기업 거래 데이터 (삼성전자 재무제표 참조).

삼성전자 연결재무제표(2023~2024 추정 평균) 비율을 반영해
실제 대기업 수준의 풍부한 거래 데이터셋을 생성합니다.

[연간 P&L 가이드라인 — 단위: 백만원]
- 매출액           : 약 280,000,000  (280조)
  · 제품매출 86%, 상품매출 9%, 용역매출 5%
- 매출원가율       : 62%  →  약 173,600,000
- 매출총이익률     : 38%
- 판관비율         : 22%  →  약 61,600,000
- 영업이익률       : 16%  →  약 44,800,000
- 영업외수익/금융원가 / 법인세 (실효세율 ~22%)

이 비율을 12개월·계절성 가중치로 분해하고, 매월 약 200~300건의 거래를 생성해
거래목록·차트가 충분히 풍부해지도록 합니다.

사용법:
    cd backend && python -m app.seed_education

주의:
- 기존 거래 데이터를 유지하면서 추가합니다. 완전 초기화가 필요하면 먼저
  `python -m app.scripts.reset_transactions --yes`를 실행하세요.
- 계정과목·카테고리가 비어 있으면 기본 seed.py의 마스터 데이터도 함께 넣습니다.
"""
from __future__ import annotations

import calendar
import random
from datetime import date
from decimal import Decimal

from .database import Base, SessionLocal, engine
from . import models
from .seed import DEFAULT_ACCOUNTS, DEFAULT_CATEGORIES


# ─────────────────────────────────────────────────────────────────────
# 연간 목표치 (단위: 천원) — 삼성전자 연결재무제표 비율 참조
# 실제 280조 매출을 1/100 스케일로 축소(2.8조 = 2,800,000,000천원) — 학습용 적정 규모
# ─────────────────────────────────────────────────────────────────────
SCALE = 1_000_000  # 백만원 단위(천원 기준 변환에 사용) → 거래 1건이 수십억 단위로 표시됨

ANNUAL_REVENUE = 2_800_000 * SCALE // 1000   # 약 2.8조 (천원)

# 매출 구성비 (삼성전자: DX·DS·SDC·하만 → 단순화: 제품/상품/용역)
REV_MIX = {
    "제품매출": 0.86,   # 반도체·MX·VD·DA 등 주력 제품
    "상품매출": 0.09,   # 액세서리·재판매 상품
    "용역매출": 0.05,   # 유지보수·라이선스·기술용역
}

# 매출원가 구성 (총 매출 대비 62%)
COGS_MIX = {
    "원재료매입": 0.42,   # 웨이퍼·메모리·디스플레이 패널·부품
    "외주가공비": 0.12,   # 패키징·테스트·OEM 가공
    "상품매입":   0.08,   # 상품 매입원가
}

# 판관비 (총 매출 대비 22%) — 세부 항목 가중치 (판관비 합계 1.0 기준)
SGA_MIX = {
    "급여":          0.22,   # 인건비 핵심
    "상여금":        0.05,
    "퇴직급여":      0.02,
    "복리후생비":    0.04,
    "감가상각비":    0.18,   # 대규모 설비투자 → 큰 비중
    "무형자산상각비":0.03,
    "연구개발비":    0.20,   # 삼성전자 R&D 비중 높음
    "광고선전비":    0.05,
    "접대비":        0.005,
    "지급수수료":    0.04,
    "운반비":        0.025,
    "임차료":        0.012,
    "수도광열비":    0.018,
    "통신비":        0.004,
    "여비교통비":    0.006,
    "차량유지비":    0.003,
    "수선비":        0.020,
    "보험료":        0.008,
    "교육훈련비":    0.006,
    "도서인쇄비":    0.001,
    "세금과공과":    0.022,
    "소모품비":      0.008,
    "대손상각비":    0.005,
}

# 영업외수익 (매출 대비 비율, 연간)
OTHER_INCOME_RATIO = {
    "이자수익":         0.012,
    "배당금수익":       0.005,
    "임대료수익":       0.001,
    "외환차익":         0.008,
    "유형자산처분이익": 0.002,
    "잡이익":           0.0005,
}

# 금융원가/기타비용 (매출 대비)
OTHER_EXPENSE_RATIO = {
    "이자비용":   0.005,
    "외환차손":   0.006,
    "기부금":     0.001,
}

# 법인세 (영업이익+영업외 - 금융원가 의 약 22%)
INCOME_TAX_RATIO = 0.035  # 매출 대비 약 3.5% (실효세율 환산)

# 월별 가중치 — 삼성전자 분기 패턴 (4분기 강세, 1~2분기 비수기)
REV_WEIGHT = {1: 0.78, 2: 0.74, 3: 0.92, 4: 0.95, 5: 0.98, 6: 0.95,
              7: 0.92, 8: 0.88, 9: 1.05, 10: 1.18, 11: 1.28, 12: 1.37}
EXP_WEIGHT = {1: 0.95, 2: 0.92, 3: 1.00, 4: 0.98, 5: 0.98, 6: 1.00,
              7: 0.98, 8: 0.95, 9: 1.02, 10: 1.05, 11: 1.08, 12: 1.10}


# ─────────────────────────────────────────────────────────────────────
# 거래 명세 헬퍼 — 매월 다수 건으로 분할
# ─────────────────────────────────────────────────────────────────────
TX_SPLIT = {
    # 카테고리: (월별 거래 건수 min, max)
    "제품매출":   (40, 60),  # 거래처별 매출
    "상품매출":   (15, 25),
    "용역매출":   (8, 15),
    "원재료매입": (25, 40),
    "외주가공비": (10, 20),
    "상품매입":   (8, 15),
    "급여":       (1, 1),    # 월 1건 일괄
    "복리후생비": (8, 15),
    "감가상각비": (3, 5),
    "무형자산상각비":(1, 2),
    "연구개발비": (15, 25),
    "광고선전비": (8, 15),
    "접대비":     (10, 20),
    "지급수수료": (15, 25),
    "운반비":     (12, 20),
    "임차료":     (1, 2),
    "수도광열비": (3, 5),
    "통신비":     (3, 5),
    "여비교통비": (15, 25),
    "차량유지비": (10, 18),
    "수선비":     (5, 12),
    "보험료":     (1, 3),
    "교육훈련비": (3, 8),
    "도서인쇄비": (2, 5),
    "세금과공과": (2, 4),
    "소모품비":   (10, 18),
    "대손상각비": (1, 2),
    "이자수익":   (3, 6),
    "배당금수익": (1, 2),    # 분기 말 위주
    "임대료수익": (1, 2),
    "외환차익":   (4, 8),
    "유형자산처분이익":(1, 2),# 가끔
    "잡이익":     (2, 5),
    "이자비용":   (3, 6),
    "외환차손":   (3, 6),
    "기부금":     (2, 5),
    "법인세비용": (1, 1),    # 분기 말 1건
}

# 거래 설명 템플릿 (실감 나는 거래처/항목명)
DESC_TEMPLATES = {
    "제품매출":   ["DS사업부 메모리 매출", "MX모바일 제품 매출", "VD디스플레이 매출", "가전 DA 매출",
                  "Foundry 위탁생산 매출", "시스템LSI 매출", "OLED 패널 매출", "SSD 매출"],
    "상품매출":   ["액세서리 상품매출", "재판매 상품매출", "스마트워치 상품매출", "이어버즈 상품매출"],
    "용역매출":   ["기술용역 매출", "유지보수 용역", "라이선스 수수료", "컨설팅 용역"],
    "원재료매입": ["실리콘 웨이퍼 매입", "디스플레이 패널 매입", "메모리 IC 매입", "PCB 매입",
                  "리튬이온 배터리 매입", "광학필름 매입", "수동소자 매입"],
    "외주가공비": ["반도체 패키징 외주", "PCB 조립 외주", "테스트 외주", "OEM 조립"],
    "상품매입":   ["액세서리 매입", "재판매 상품 매입", "주변기기 매입"],
    "급여":       ["월 급여 일괄지급"],
    "복리후생비": ["식대 지원", "건강검진 비용", "경조사비", "선물 지급", "동호회 지원",
                  "사내 카페테리아 운영비"],
    "감가상각비": ["반도체 라인 감가상각", "본사 사옥 감가상각", "디스플레이 라인 감가상각",
                  "차량운반구 감가상각"],
    "무형자산상각비":["소프트웨어 상각", "특허권 상각"],
    "연구개발비": ["차세대 메모리 R&D", "AI 칩 개발", "OLED 신기술 개발", "무선통신 R&D",
                  "공정개선 연구", "신소재 연구개발"],
    "광고선전비": ["글로벌 마케팅 캠페인", "유튜브 광고 집행", "옥외광고", "인쇄 매체 광고",
                  "전시회 부스 운영"],
    "접대비":     ["거래처 접대비", "공급사 미팅 식대", "해외 바이어 접대"],
    "지급수수료": ["법무 자문료", "세무 자문료", "회계 감사보수", "물류 수수료",
                  "결제대행 수수료", "외부 컨설팅"],
    "운반비":     ["국내 운송비", "해외 수출 운송", "택배 운임", "보세창고 보관료"],
    "임차료":     ["본사 빌딩 임차료", "해외 지점 임차료"],
    "수도광열비": ["전력비", "수도료", "도시가스 요금"],
    "통신비":     ["전용회선 사용료", "모바일 통신비", "인터넷 회선료"],
    "여비교통비": ["국내 출장비", "해외 출장비", "출장 항공료", "출장 숙박비"],
    "차량유지비": ["주유비", "차량 정비비", "톨게이트 비용"],
    "수선비":     ["설비 수선", "건물 보수", "기계장치 정비"],
    "보험료":     ["화재보험료", "단체상해보험", "산재보험"],
    "교육훈련비": ["임직원 교육", "외부 세미나 참가비", "기술 교육 위탁"],
    "도서인쇄비": ["기술서적 구입", "사내 인쇄물 제작"],
    "세금과공과": ["재산세", "주민세", "환경부담금"],
    "소모품비":   ["사무용품 구입", "공구류 매입", "소모성 자재 매입"],
    "대손상각비": ["매출채권 대손상각"],
    "이자수익":   ["예금 이자수익", "대여금 이자수익", "채권 이자수익"],
    "배당금수익": ["관계사 배당금", "주식 배당금"],
    "임대료수익": ["임대 부동산 임대료"],
    "외환차익":   ["외환거래 차익", "외화 외상매출 회수 차익"],
    "유형자산처분이익":["설비 매각이익", "차량 처분이익"],
    "잡이익":     ["잡이익"],
    "이자비용":   ["사채 이자비용", "차입금 이자비용"],
    "외환차손":   ["외화부채 환산손실", "외환 결제 차손"],
    "기부금":     ["사회공헌 기부금", "재단 출연금"],
    "법인세비용": ["분기 법인세 추정 납부"],
}


# ─────────────────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────────────────
def _ensure_masters(db):
    if db.query(models.Account).count() == 0:
        for code, name, atype in DEFAULT_ACCOUNTS:
            db.add(models.Account(code=code, name=name, type=atype))
    if db.query(models.Category).count() == 0:
        for name, ttype in DEFAULT_CATEGORIES:
            db.add(models.Category(name=name, type=ttype))
        db.commit()


def _month_range(end: date, months: int):
    y, m = end.year, end.month
    out = []
    for _ in range(months):
        out.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(out))


def _random_day(y: int, m: int, max_day: int | None):
    last = calendar.monthrange(y, m)[1]
    upper = min(last, max_day) if max_day else last
    return random.randint(1, max(upper, 1))


def _split_amount(total: int, n: int, jitter: float = 0.45) -> list[int]:
    """total을 n등분하되 ±jitter 비율로 흔들어서 자연스러운 거래 금액 분포를 만든다."""
    if n <= 0 or total <= 0:
        return []
    base = total / n
    raws = [max(1.0, base * (1 + random.uniform(-jitter, jitter))) for _ in range(n)]
    s = sum(raws)
    scale = total / s
    out = [int(round(r * scale)) for r in raws]
    diff = total - sum(out)
    if out:
        out[-1] += diff
    return out


def _add_split_transactions(
    db, cats, cat_name: str, y: int, m: int, max_day, total_amount: int,
    ttype, memo: str | None = None,
):
    """카테고리별 월간 총액을 다건으로 분할해 거래 등록."""
    if cat_name not in cats or total_amount <= 0:
        return 0
    lo, hi = TX_SPLIT.get(cat_name, (3, 6))
    n = random.randint(lo, hi)
    amounts = _split_amount(total_amount, n)
    desc_pool = DESC_TEMPLATES.get(cat_name, [cat_name])
    inserted = 0
    for amt in amounts:
        if amt <= 0:
            continue
        desc = random.choice(desc_pool)
        db.add(models.Transaction(
            date=date(y, m, _random_day(y, m, max_day)),
            description=desc,
            amount=Decimal(amt),
            type=ttype,
            category_id=cats[cat_name].id,
            memo=memo,
        ))
        inserted += 1
    return inserted


# ─────────────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────────────
def seed_education():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _ensure_masters(db)
        cats = {c.name: c for c in db.query(models.Category).all()}

        random.seed(20260426)
        today = date.today()
        inserted = 0

        # 월별 가중치 정규화 — 12개월 합이 12.0이 되도록
        rev_w_total = sum(REV_WEIGHT.values())
        exp_w_total = sum(EXP_WEIGHT.values())

        for (y, m) in _month_range(today, 12):
            rw = REV_WEIGHT[m] * 12 / rev_w_total
            ew = EXP_WEIGHT[m] * 12 / exp_w_total
            max_day = today.day if (y == today.year and m == today.month) else None
            is_quarter_end = m in (3, 6, 9, 12)

            month_revenue = int(ANNUAL_REVENUE / 12 * rw)

            # ── 매출 ──
            for cat_name, mix in REV_MIX.items():
                target = int(month_revenue * mix)
                inserted += _add_split_transactions(
                    db, cats, cat_name, y, m, max_day, target,
                    models.TransactionType.INCOME,
                )

            # ── 매출원가 ──
            for cat_name, ratio in COGS_MIX.items():
                target = int(month_revenue * ratio * ew / max(rw, 0.5))
                inserted += _add_split_transactions(
                    db, cats, cat_name, y, m, max_day, target,
                    models.TransactionType.EXPENSE, memo="매출원가",
                )

            # ── 판관비 (매출 대비 22% × 항목별 가중치) ──
            month_sga = int(month_revenue * 0.22 * ew / max(rw, 0.5))
            for cat_name, w in SGA_MIX.items():
                target = int(month_sga * w)
                if target <= 0:
                    continue
                memo = "판관비"
                # 분기 말에만 발생하는 일부 항목
                if cat_name in ("상여금", "퇴직급여") and not is_quarter_end:
                    continue
                if cat_name == "상여금" and is_quarter_end:
                    target = int(target * 4)  # 연 4회 분기 정산
                    memo = f"{m//3}분기 상여"
                if cat_name == "퇴직급여" and is_quarter_end:
                    target = int(target * 4)
                    memo = f"{m//3}분기 퇴직급여 충당"
                inserted += _add_split_transactions(
                    db, cats, cat_name, y, m, max_day, target,
                    models.TransactionType.EXPENSE, memo=memo,
                )

            # ── 영업외수익 ──
            for cat_name, ratio in OTHER_INCOME_RATIO.items():
                if cat_name == "배당금수익" and not is_quarter_end:
                    continue
                if cat_name == "유형자산처분이익" and random.random() > 0.25:
                    continue
                target = int(month_revenue * ratio)
                inserted += _add_split_transactions(
                    db, cats, cat_name, y, m, max_day, target,
                    models.TransactionType.INCOME, memo="영업외수익",
                )

            # ── 금융원가/기타비용 ──
            for cat_name, ratio in OTHER_EXPENSE_RATIO.items():
                if cat_name == "기부금" and random.random() > 0.4:
                    continue
                target = int(month_revenue * ratio)
                inserted += _add_split_transactions(
                    db, cats, cat_name, y, m, max_day, target,
                    models.TransactionType.EXPENSE, memo="영업외비용",
                )

            # ── 법인세비용 (분기 말) ──
            if is_quarter_end:
                # 분기 매출의 3.5% × 4분기 분기당 = 약 분기 매출의 14% 수준
                quarterly_revenue = int(month_revenue * 3)  # 분기 추정
                tax = int(quarterly_revenue * INCOME_TAX_RATIO)
                inserted += _add_split_transactions(
                    db, cats, "법인세비용", y, m, max_day, tax,
                    models.TransactionType.EXPENSE, memo=f"{m//3}분기 법인세 추정납부",
                )

        db.commit()
        print(f"[seed_education] inserted {inserted} transactions over 12 months (~{today})")
    finally:
        db.close()


if __name__ == "__main__":
    seed_education()
