import uuid
import time
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from backend.database import get_db
from backend.schemas.data import (
    DataItemCreate,
    DataItemUpdate,
    DataItemResponse,
    DataSummaryResponse,
    DataMetrics
)

logger = logging.getLogger("backend.data_service")
COLLECTION_NAME = "data"
CACHE_TTL_SECONDS = 60

class DataService:
    def __init__(self):
        self.db = get_db()
        self.collection = self.db.collection(COLLECTION_NAME)
        self._summary_cache: Dict[str, Tuple[DataSummaryResponse, float]] = {}

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _invalidate_cache(self):
        """Invalidate in-memory summary cache upon data mutations."""
        self._summary_cache.clear()

    def add_item(self, item_in: DataItemCreate) -> DataItemResponse:
        try:
            now = self._now_iso()
            doc_id = str(uuid.uuid4())
            data = {
                "date": item_in.date,
                "value": float(item_in.value),
                "memo": item_in.memo or "",
                "created_at": now,
                "updated_at": now
            }
            self.collection.document(doc_id).set(data)
            self._invalidate_cache()
            return DataItemResponse(id=doc_id, **data)
        except Exception as e:
            logger.error(f"Failed to add data item: {e}")
            raise RuntimeError(f"데이터 추가 중 오류가 발생했습니다: {str(e)}")

    def get_items(self, limit: int = 100, offset: int = 0, sort_by: str = "date", sort_order: str = "desc") -> Tuple[List[DataItemResponse], int]:
        all_docs = []
        for doc in self.collection.stream():
            d = doc.to_dict()
            all_docs.append(DataItemResponse(
                id=doc.id,
                date=d.get("date", ""),
                value=float(d.get("value", 0.0)),
                memo=d.get("memo", ""),
                created_at=d.get("created_at"),
                updated_at=d.get("updated_at")
            ))

        # Sort items
        reverse = (sort_order.lower() == "desc")
        if sort_by == "date":
            all_docs.sort(key=lambda x: x.date, reverse=reverse)
        elif sort_by == "value":
            all_docs.sort(key=lambda x: x.value, reverse=reverse)
        else:
            all_docs.sort(key=lambda x: x.created_at or "", reverse=reverse)

        total_count = len(all_docs)
        paginated = all_docs[offset : offset + limit]
        return paginated, total_count

    def get_item(self, doc_id: str) -> Optional[DataItemResponse]:
        doc = self.collection.document(doc_id).get()
        if not doc.exists:
            return None
        d = doc.to_dict()
        return DataItemResponse(
            id=doc.id,
            date=d.get("date", ""),
            value=float(d.get("value", 0.0)),
            memo=d.get("memo", ""),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at")
        )

    def update_item(self, doc_id: str, item_in: DataItemUpdate) -> Optional[DataItemResponse]:
        try:
            doc_ref = self.collection.document(doc_id)
            doc = doc_ref.get()
            if not doc.exists:
                return None

            current_data = doc.to_dict()
            now = self._now_iso()
            update_dict: Dict[str, Any] = {"updated_at": now}

            if item_in.date is not None:
                update_dict["date"] = item_in.date
            if item_in.value is not None:
                update_dict["value"] = float(item_in.value)
            if item_in.memo is not None:
                update_dict["memo"] = item_in.memo

            current_data.update(update_dict)
            doc_ref.set(current_data, merge=True)
            self._invalidate_cache()

            return DataItemResponse(id=doc_id, **current_data)
        except Exception as e:
            logger.error(f"Failed to update data item {doc_id}: {e}")
            raise RuntimeError(f"데이터 수정 중 오류가 발생했습니다: {str(e)}")

    def delete_item(self, doc_id: str) -> bool:
        try:
            doc_ref = self.collection.document(doc_id)
            doc = doc_ref.get()
            if not doc.exists:
                return False
            doc_ref.delete()
            self._invalidate_cache()
            return True
        except Exception as e:
            logger.error(f"Failed to delete data item {doc_id}: {e}")
            raise RuntimeError(f"데이터 삭제 중 오류가 발생했습니다: {str(e)}")

    def get_summary(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> DataSummaryResponse:
        """
        Calculate statistical summary and trend based on 3-1 time-series algorithms.
        Includes In-Memory TTL caching (60s) to reduce database overhead.
        Supports optional period filtering (start_date, end_date: YYYY-MM-DD).
        """
        cache_key = f"{start_date or ''}_{end_date or ''}"
        now_ts = time.time()
        if cache_key in self._summary_cache:
            cached_res, timestamp = self._summary_cache[cache_key]
            if now_ts - timestamp < CACHE_TTL_SECONDS:
                return cached_res

        all_items: List[Dict[str, Any]] = []
        for doc in self.collection.stream():
            d = doc.to_dict()
            if "date" in d and "value" in d:
                dt = d["date"]
                if start_date and dt < start_date:
                    continue
                if end_date and dt > end_date:
                    continue
                all_items.append(d)

        period_desc = "데이터 없음"
        if start_date and end_date:
            period_desc = f"{start_date} ~ {end_date} (데이터 없음)"
        elif start_date:
            period_desc = f"{start_date} 이후 (데이터 없음)"
        elif end_date:
            period_desc = f"{end_date} 이전 (데이터 없음)"

        if not all_items:
            empty_summary = DataSummaryResponse(
                period=period_desc,
                count=0,
                metrics=DataMetrics(total=0.0, average=0.0, max=0.0, min=0.0, latest=0.0),
                trend="지정된 기간의 데이터가 등록되지 않았습니다.",
                insights="해당 기간에 분석할 데이터가 없습니다. 기간 필터를 조정하거나 새 데이터를 추가해주세요."
            )
            self._summary_cache[cache_key] = (empty_summary, now_ts)
            return empty_summary

        # Sort chronologically (ascending) for time series analysis
        all_items.sort(key=lambda x: x["date"])

        dates = [x["date"] for x in all_items]
        values = [float(x["value"]) for x in all_items]

        period = f"{dates[0]} ~ {dates[-1]}"
        count = len(values)
        total = round(sum(values), 2)
        avg = round(total / count, 2)
        max_val = round(max(values), 2)
        min_val = round(min(values), 2)
        latest_val = round(values[-1], 2)

        # Find max and min dates for rich insights
        max_date = dates[values.index(max_val)]
        min_date = dates[values.index(min_val)]

        # Trend analysis using 3-1 methodology:
        # Compare latest price against the 20-period Moving Average (SMA 20) and recent slope
        window = min(20, count)
        recent_window = values[-window:]
        recent_avg = sum(recent_window) / window

        pct_vs_window = ((latest_val - recent_avg) / recent_avg) * 100 if recent_avg else 0
        overall_pct = ((latest_val - values[0]) / values[0]) * 100 if values[0] else 0

        if pct_vs_window >= 2.0:
            trend_str = f"상승세 (최근 {window}거래일 이동평균 대비 +{pct_vs_window:.1f}%)"
        elif pct_vs_window <= -2.0:
            trend_str = f"하락세 (최근 {window}거래일 이동평균 대비 {pct_vs_window:.1f}%)"
        else:
            trend_str = f"보합/횡보 (최근 {window}거래일 이동평균 대비 {pct_vs_window:+.1f}%)"

        insights = (
            f"총 {count}개 거래일 중 최고가는 {max_date}의 {max_val:,.0f}원이며, "
            f"최저가는 {min_date}의 {min_val:,.0f}원입니다. "
            f"전체 기간 시작일 대비 수익률은 {overall_pct:+.2f}%, "
            f"최신 종가는 {latest_val:,.0f}원입니다."
        )

        res = DataSummaryResponse(
            period=period,
            count=count,
            metrics=DataMetrics(
                total=total,
                average=avg,
                max=max_val,
                min=min_val,
                latest=latest_val
            ),
            trend=trend_str,
            insights=insights
        )
        self._summary_cache[cache_key] = (res, now_ts)
        return res

    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculate extended quantitative financial statistics:
        - 20-day historical volatility (standard deviation)
        - 20-day & 60-day Simple Moving Average (SMA)
        - 14-day Relative Strength Index (RSI 14)
        - Max & Min record dates & Overall cumulative return
        """
        all_items = []
        for doc in self.collection.stream():
            d = doc.to_dict()
            if "date" in d and "value" in d:
                all_items.append(d)

        if not all_items:
            return {
                "period": "데이터 없음",
                "count": 0,
                "volatility": 0.0,
                "sma_20": 0.0,
                "sma_60": 0.0,
                "max_price": 0.0,
                "max_date": "-",
                "min_price": 0.0,
                "min_date": "-",
                "total_return_pct": 0.0,
                "rsi_14": 50.0
            }

        all_items.sort(key=lambda x: x["date"])
        dates = [x["date"] for x in all_items]
        values = [float(x["value"]) for x in all_items]
        count = len(values)

        max_val = max(values)
        min_val = min(values)
        max_date = dates[values.index(max_val)]
        min_date = dates[values.index(min_val)]

        # Volatility (20-day standard deviation)
        w20 = values[-min(20, count):]
        mean20 = sum(w20) / len(w20)
        variance = sum((x - mean20) ** 2 for x in w20) / len(w20)
        volatility = round((variance ** 0.5), 2)
        sma_20 = round(mean20, 2)

        # 60-day SMA
        w60 = values[-min(60, count):]
        sma_60 = round(sum(w60) / len(w60), 2)

        # 14-day RSI
        rsi_window = min(14, count - 1)
        if rsi_window > 0:
            diffs = [values[i] - values[i - 1] for i in range(len(values) - rsi_window, len(values))]
            gains = [d for d in diffs if d > 0]
            losses = [-d for d in diffs if d < 0]
            avg_gain = sum(gains) / rsi_window if gains else 0
            avg_loss = sum(losses) / rsi_window if losses else 0
            if avg_loss == 0:
                rsi_14 = 100.0 if avg_gain > 0 else 50.0
            else:
                rs = avg_gain / avg_loss
                rsi_14 = round(100 - (100 / (1 + rs)), 2)
        else:
            rsi_14 = 50.0

        total_return_pct = round(((values[-1] - values[0]) / values[0]) * 100, 2) if values[0] else 0.0

        return {
            "period": f"{dates[0]} ~ {dates[-1]}",
            "count": count,
            "volatility": volatility,
            "sma_20": sma_20,
            "sma_60": sma_60,
            "max_price": round(max_val, 2),
            "max_date": max_date,
            "min_price": round(min_val, 2),
            "min_date": min_date,
            "total_return_pct": total_return_pct,
            "rsi_14": rsi_14
        }

    def sync_latest_data(self, symbol: str = "005930.KS") -> Dict[str, Any]:
        """
        오늘(실시간)까지의 최신 주가 데이터를 외부 금융 소스(Yahoo Finance)에서 조회하여
        기존 DB에 없는 신규 거래일 데이터를 자동으로 적재합니다.
        신규 추가된 데이터는 CSV 원본 파일에도 동기화되어 영구 보존됩니다.
        """
        import urllib.request
        import json
        from pathlib import Path

        existing_items, _ = self.get_items(limit=1000, sort_by="date", sort_order="desc")
        existing_dates = {item.date for item in existing_items}
        latest_date = max(existing_dates) if existing_dates else "2024-01-01"

        fetched_records = []
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1mo"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                if res.status == 200:
                    chart_data = json.loads(res.read().decode("utf-8"))
                    result = chart_data["chart"]["result"][0]
                    timestamps = result.get("timestamp", [])
                    quotes = result["indicators"]["quote"][0]
                    for i in range(len(timestamps)):
                        dt = datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d")
                        c = quotes["close"][i]
                        if c is None:
                            continue
                        o = quotes.get("open", [c])[i] or c
                        h = quotes.get("high", [c])[i] or c
                        l = quotes.get("low", [c])[i] or c
                        v = quotes.get("volume", [0])[i] or 0
                        fetched_records.append({
                            "date": dt,
                            "close": round(float(c), 0),
                            "open": round(float(o), 0),
                            "high": round(float(h), 0),
                            "low": round(float(l), 0),
                            "volume": int(float(v))
                        })
        except Exception as e:
            logger.warning(f"External stock sync warning: {e}")

        added_items = []
        csv_candidates = [
            Path(__file__).resolve().parent.parent.parent / "data" / "samsung_stock_2024_present.csv",
            Path("data/samsung_stock_2024_present.csv")
        ]
        csv_path = None
        for p in csv_candidates:
            if p.exists():
                csv_path = p
                break

        csv_append_lines = []
        fetched_records.sort(key=lambda x: x["date"])

        for rec in fetched_records:
            if rec["date"] > latest_date and rec["date"] not in existing_dates:
                memo = (
                    f"시가 {rec['open']:,.0f} | 고가 {rec['high']:,.0f} | "
                    f"저가 {rec['low']:,.0f} | 거래량 {rec['volume']:,.0f}주"
                )
                item_in = DataItemCreate(
                    date=rec["date"],
                    value=rec["close"],
                    memo=memo
                )
                created = self.add_item(item_in)
                added_items.append({
                    "id": created.id,
                    "date": created.date,
                    "value": created.value,
                    "memo": created.memo
                })
                existing_dates.add(rec["date"])
                csv_append_lines.append(
                    f"{rec['date']},{rec['close']},{rec['high']},{rec['low']},{rec['open']},{rec['volume']}\n"
                )

        if csv_path and csv_append_lines:
            try:
                with open(csv_path, "a", encoding="utf-8") as f:
                    for line in csv_append_lines:
                        f.write(line)
            except Exception as e:
                logger.warning(f"Could not append to CSV file: {e}")

        self._invalidate_cache()
        summary = self.get_summary()

        return {
            "status": "success",
            "updated_count": len(added_items),
            "added_items": added_items,
            "latest_date": summary.period.split(" ~ ")[-1] if " ~ " in summary.period else latest_date,
            "total_count": summary.count,
            "period": summary.period,
            "latest_price": summary.metrics.latest,
            "trend": summary.trend,
            "summary": {
                "period": summary.period,
                "count": summary.count,
                "latest_price": summary.metrics.latest,
                "trend": summary.trend
            }
        }

