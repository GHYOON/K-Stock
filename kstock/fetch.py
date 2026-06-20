"""주가/시가총액 데이터 조회.

데이터 출처를 여러 개 두고 순서대로 시도(폴백)한다.

  1) 네이버 증권 모바일 API  (가격 + 상장주식수 → 시가총액)
  2) 야후 파이낸스 차트 API  (가격) + 종목 정의의 상장주식수 폴백

어느 한쪽이 막혀 있거나 응답 형식이 바뀌어도 다른 경로로 동작하도록
방어적으로 파싱한다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .stocks import Stock

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_TIMEOUT = 10


@dataclass
class Quote:
    """한 종목의 조회 결과."""

    stock: Stock
    price: float                 # 현재가(원)
    prev_close: Optional[float]  # 전일 종가(원)
    shares: int                  # 시가총액 계산에 사용한 상장주식수
    source: str                  # 데이터 출처 표시

    @property
    def change(self) -> Optional[float]:
        if self.prev_close is None:
            return None
        return self.price - self.prev_close

    @property
    def change_pct(self) -> Optional[float]:
        if not self.prev_close:
            return None
        return (self.price - self.prev_close) / self.prev_close * 100

    @property
    def market_cap(self) -> float:
        """시가총액(원) = 현재가 × 상장주식수."""
        return self.price * self.shares


# --- 내부 유틸 --------------------------------------------------------

def _http_get(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
    with urlopen(req, timeout=_TIMEOUT) as resp:
        return resp.read()


def _to_number(value) -> Optional[float]:
    """"59,000" / "-1.23" / 59000 등을 float로. 실패 시 None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "").replace("%", "")
    if text in ("", "-", "N/A"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


# --- 출처 1: 네이버 증권 ---------------------------------------------

def _fetch_naver(stock: Stock) -> Quote:
    base = _http_get(f"https://m.stock.naver.com/api/stock/{stock.code}/basic")
    basic = json.loads(base)

    price = _to_number(basic.get("closePrice"))
    if price is None:
        raise ValueError("네이버 응답에 현재가 없음")

    # 전일 종가 = 현재가 - 전일대비
    diff = _to_number(basic.get("compareToPreviousClosePrice"))
    sign = basic.get("compareToPreviousPrice", {})
    if isinstance(sign, dict) and sign.get("name") in ("FALLING", "LOWER_LIMIT"):
        diff = -abs(diff) if diff is not None else None
    prev_close = price - diff if diff is not None else None

    # 상장주식수는 integration 엔드포인트의 totalInfos에서 시도
    shares = _naver_shares(stock)

    return Quote(stock, price, prev_close, shares, "네이버 증권")


def _naver_shares(stock: Stock) -> int:
    try:
        raw = _http_get(
            f"https://m.stock.naver.com/api/stock/{stock.code}/integration"
        )
        data = json.loads(raw)
        for item in data.get("totalInfos", []):
            key = item.get("key") or item.get("code")
            if key in ("listedStockCnt", "listedShares", "shareCount"):
                n = _to_number(item.get("value"))
                if n:
                    return int(n)
    except (HTTPError, URLError, ValueError, json.JSONDecodeError):
        pass
    return stock.shares_fallback


# --- 출처 2: 야후 파이낸스 -------------------------------------------

def _fetch_yahoo(stock: Stock) -> Quote:
    raw = _http_get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{stock.yahoo}"
        "?interval=1d&range=2d"
    )
    data = json.loads(raw)
    meta = data["chart"]["result"][0]["meta"]

    price = _to_number(meta.get("regularMarketPrice"))
    prev_close = _to_number(meta.get("chartPreviousClose") or meta.get("previousClose"))
    if price is None:
        raise ValueError("야후 응답에 현재가 없음")

    shares = stock.shares_fallback
    return Quote(stock, price, prev_close, shares, "야후 파이낸스")


# --- 공개 함수 -------------------------------------------------------

_SOURCES = (_fetch_naver, _fetch_yahoo)


def get_quote(stock: Stock) -> Quote:
    """여러 출처를 순서대로 시도해 시세를 가져온다."""
    errors = []
    for source in _SOURCES:
        try:
            return source(stock)
        except (HTTPError, URLError, ValueError, KeyError, json.JSONDecodeError) as exc:
            errors.append(f"{source.__name__}: {exc}")
    raise RuntimeError(
        f"{stock.name}({stock.code}) 시세 조회 실패\n  - " + "\n  - ".join(errors)
    )
