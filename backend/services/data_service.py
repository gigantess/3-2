import uuid
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

COLLECTION_NAME = "data"

class DataService:
    def __init__(self):
        self.db = get_db()
        self.collection = self.db.collection(COLLECTION_NAME)

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def add_item(self, item_in: DataItemCreate) -> DataItemResponse:
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
        return DataItemResponse(id=doc_id, **data)

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

        return DataItemResponse(id=doc_id, **current_data)

    def delete_item(self, doc_id: str) -> bool:
        doc_ref = self.collection.document(doc_id)
        doc = doc_ref.get()
        if not doc.exists:
            return False
        doc_ref.delete()
        return True

    def get_summary(self) -> DataSummaryResponse:
        """
        Calculate statistical summary and trend based on 3-1 time-series algorithms.
        """
        all_items: List[Dict[str, Any]] = []
        for doc in self.collection.stream():
            d = doc.to_dict()
            if "date" in d and "value" in d:
                all_items.append(d)

        if not all_items:
            return DataSummaryResponse(
                period="데이터 없음",
                count=0,
                metrics=DataMetrics(total=0.0, average=0.0, max=0.0, min=0.0, latest=0.0),
                trend="데이터가 등록되지 않았습니다.",
                insights="분석할 데이터가 없습니다. 새 데이터를 추가해주세요."
            )

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

        return DataSummaryResponse(
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
