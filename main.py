#!/usr/bin/env python3
"""K-Stock CLI 진입점.

삼성전자 · 삼성전기 · SK하이닉스의 현재가와 시가총액을 조회하고,
삼성전자와 SK하이닉스의 시가총액 격차를 비교해 출력한다.

사용법:
    python main.py            # 1회 조회 후 출력
    python main.py --watch 30 # 30초마다 갱신 (Ctrl+C 종료)
    python main.py --json     # JSON 형식으로 출력
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from kstock import STOCKS, get_quote, render


def collect():
    quotes = []
    for stock in STOCKS:
        try:
            quotes.append(get_quote(stock))
        except RuntimeError as exc:
            print(f"[경고] {exc}", file=sys.stderr)
    return quotes


def as_json(quotes) -> str:
    payload = []
    for q in quotes:
        payload.append(
            {
                "code": q.stock.code,
                "name": q.stock.name,
                "price": q.price,
                "prev_close": q.prev_close,
                "change": q.change,
                "change_pct": q.change_pct,
                "shares": q.shares,
                "market_cap": q.market_cap,
                "source": q.source,
            }
        )
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="한국 반도체 3종목 시세 및 시가총액 비교"
    )
    parser.add_argument(
        "--watch",
        type=int,
        metavar="SEC",
        help="지정한 초 간격으로 반복 갱신 (Ctrl+C로 종료)",
    )
    parser.add_argument(
        "--json", action="store_true", help="JSON 형식으로 출력"
    )
    args = parser.parse_args()

    def run_once() -> int:
        quotes = collect()
        if not quotes:
            print("시세를 가져오지 못했습니다. 네트워크를 확인하세요.", file=sys.stderr)
            return 1
        print(as_json(quotes) if args.json else render(quotes))
        return 0

    if args.watch:
        try:
            while True:
                if not args.json:
                    print("\033[2J\033[H", end="")  # 화면 지우기
                run_once()
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\n종료합니다.")
            return 0
    return run_once()


if __name__ == "__main__":
    raise SystemExit(main())
