"""거래 데이터 초기화 스크립트 — 위험! 명시적 확인 필요.

사용법:
    # 드라이런 (기본: 삭제 건수만 출력, 실제 삭제 X)
    python -m app.scripts.reset_transactions

    # 실제 삭제 — --yes 플래그 필수
    python -m app.scripts.reset_transactions --yes

    # 프로덕션 DB에 대해 실행 (DATABASE_URL이 Postgres를 가리키는 환경에서 실행)
    DATABASE_URL=postgresql://... python -m app.scripts.reset_transactions --yes

삭제 대상:
    - JournalEntry (거래 FK cascade로 함께 제거됨, 여기선 명시적으로 먼저 삭제)
    - Transaction

유지되는 데이터:
    - Account (계정과목 마스터)
    - Category (카테고리 마스터)
"""
from __future__ import annotations

import argparse
import sys

from ..database import SessionLocal, engine
from .. import models


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="거래 데이터 초기화")
    parser.add_argument("--yes", action="store_true", help="실제 삭제 수행 (미지정 시 드라이런)")
    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        tx_count = db.query(models.Transaction).count()
        je_count = db.query(models.JournalEntry).count()

        url = str(engine.url)
        print(f"[reset] target DB: {url.split('@')[-1] if '@' in url else url}")
        print(f"[reset] Transaction 행수: {tx_count}")
        print(f"[reset] JournalEntry 행수: {je_count}")

        if not args.yes:
            print("\n[dry-run] 실제 삭제하려면 --yes 플래그를 붙여 다시 실행하세요.")
            return 0

        # 명시적 CLI 확인 한 번 더
        confirm = input(f"\n정말 {tx_count}건의 거래를 삭제하시겠습니까? (yes 입력): ").strip()
        if confirm != "yes":
            print("[abort] 취소되었습니다.")
            return 1

        db.query(models.JournalEntry).delete()
        db.query(models.Transaction).delete()
        db.commit()
        print(f"[ok] 거래 {tx_count}건 및 분개 {je_count}건을 삭제했습니다.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
