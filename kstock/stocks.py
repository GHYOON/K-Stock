"""대상 종목 정의.

각 종목의 종목코드, 표시 이름, 그리고 시가총액 계산용 상장주식수(폴백값)를
담는다. 상장주식수는 자사주 소각/증자 등으로 가끔 변하므로, 가능하면
실시간으로 가져오고(`fetch` 참고) 실패 시 아래 폴백값을 사용한다.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Stock:
    code: str          # 6자리 종목코드 (예: "005930")
    name: str          # 표시 이름
    yahoo: str         # 야후 파이낸스 심볼 (예: "005930.KS")
    # 상장주식수(보통주) 폴백값 — 실시간 조회 실패 시에만 사용.
    shares_fallback: int


# 종목 정의 -------------------------------------------------------------
SAMSUNG_ELEC = Stock(
    code="005930",
    name="삼성전자",
    yahoo="005930.KS",
    shares_fallback=5_969_782_550,
)

SAMSUNG_EM = Stock(
    code="009150",
    name="삼성전기",
    yahoo="009150.KS",
    shares_fallback=74_693_696,
)

SK_HYNIX = Stock(
    code="000660",
    name="SK하이닉스",
    yahoo="000660.KS",
    shares_fallback=728_002_365,
)

# 가격을 확인할 전체 종목 목록
STOCKS = [SAMSUNG_ELEC, SAMSUNG_EM, SK_HYNIX]
