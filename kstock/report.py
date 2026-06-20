"""조회 결과를 보기 좋게 출력하고, 시가총액 비교를 계산한다."""

from __future__ import annotations

from datetime import datetime
from typing import List

from .fetch import Quote
from .stocks import SAMSUNG_ELEC, SK_HYNIX


def _fmt_won(value: float) -> str:
    """원화를 '조/억' 단위 한글 표기로."""
    eok = value / 1_0000_0000  # 1억 = 1e8
    if eok >= 1_0000:  # 1조 이상
        jo = int(eok // 1_0000)
        rest = int(round(eok % 1_0000))
        return f"{jo:,}조 {rest:,}억" if rest else f"{jo:,}조"
    return f"{eok:,.0f}억"


def _fmt_change(q: Quote) -> str:
    if q.change is None:
        return "전일대비 N/A"
    arrow = "▲" if q.change > 0 else ("▼" if q.change < 0 else "-")
    pct = f"{q.change_pct:+.2f}%" if q.change_pct is not None else "N/A"
    return f"{arrow} {abs(q.change):,.0f}원 ({pct})"


def render(quotes: List[Quote]) -> str:
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append("=" * 56)
    lines.append(f"  한국 반도체 3종목 시세  ({now})")
    lines.append("=" * 56)

    by_code = {q.stock.code: q for q in quotes}

    # --- 종목별 시세 ---
    for q in quotes:
        lines.append("")
        lines.append(f"● {q.stock.name} ({q.stock.code})")
        lines.append(f"    현재가   : {q.price:>12,.0f} 원   {_fmt_change(q)}")
        lines.append(f"    시가총액 : {_fmt_won(q.market_cap):>12}")
        lines.append(f"    (출처: {q.source})")

    # --- 시가총액 비교: 삼성전자 vs SK하이닉스 ---
    se = by_code.get(SAMSUNG_ELEC.code)
    hy = by_code.get(SK_HYNIX.code)
    if se and hy:
        lines.append("")
        lines.append("-" * 56)
        lines.append("  시가총액 비교 — SK하이닉스가 삼성전자에 얼마나?")
        lines.append("-" * 56)
        se_cap = se.market_cap
        hy_cap = hy.market_cap
        ratio = hy_cap / se_cap * 100 if se_cap else 0
        gap = se_cap - hy_cap

        lines.append(f"    삼성전자   시총 : {_fmt_won(se_cap)}")
        lines.append(f"    SK하이닉스 시총 : {_fmt_won(hy_cap)}")
        lines.append("")
        lines.append(f"    하이닉스 / 삼성전자 = {ratio:.1f}%")
        lines.append(f"    격차              = {_fmt_won(abs(gap))}")
        if gap > 0:
            lines.append(
                f"    → SK하이닉스가 삼성전자를 따라잡으려면 "
                f"약 {_fmt_won(gap)} 더 필요"
            )
            # 하이닉스 주가가 몇 % 올라야 동률이 되는지
            need_pct = gap / hy_cap * 100 if hy_cap else 0
            lines.append(
                f"      (하이닉스 주가가 약 {need_pct:.1f}% 오르면 동률)"
            )
        elif gap < 0:
            lines.append("    → SK하이닉스 시총이 삼성전자를 이미 추월!")
        else:
            lines.append("    → 두 종목의 시총이 동일")

    lines.append("=" * 56)
    return "\n".join(lines)
