import csv
import io
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from backend.schemas.data import (
    DataItemCreate,
    DataItemUpdate,
    DataItemResponse,
    DataSummaryResponse
)
from backend.services.data_service import DataService

router = APIRouter(prefix="/api/data", tags=["Data"])
data_service = DataService()

@router.post("", response_model=DataItemResponse, status_code=201, summary="새 데이터 추가")
def create_data_item(item: DataItemCreate):
    """
    (date, value, memo) 형태의 새 시계열 데이터를 추가합니다.
    """
    return data_service.add_item(item)

@router.get("", summary="데이터 목록 조회")
def get_data_items(
    limit: int = Query(50, ge=1, le=1000, description="조회 개수"),
    offset: int = Query(0, ge=0, description="건너뛸 개수"),
    sort_by: str = Query("date", description="정렬 기준 (date, value, created_at)"),
    sort_order: str = Query("desc", description="정렬 순서 (asc, desc)")
):
    """
    저장된 시계열 데이터 목록을 페이징 및 정렬하여 반환합니다.
    """
    items, total = data_service.get_items(limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order)
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/summary", response_model=DataSummaryResponse, summary="데이터 요약 정보 조회")
def get_data_summary():
    """
    AI 시스템 프롬프트 주입 및 대시보드 KPI용 데이터 요약(기간, 건수, 평균/최고/최저/최신, 추세)을 반환합니다.
    """
    return data_service.get_summary()

@router.get("/statistics", summary="심층 통계 지표 조회 (보너스 과제)")
def get_data_statistics():
    """
    보너스 과제 요구사항:
    변동성(표준편차), 20일 이동평균, 60일 이동평균, RSI, 최고/최저가 및 누적 수익률을 반환합니다.
    """
    return data_service.get_statistics()


@router.get("/export", summary="데이터 내보내기 (CSV/JSON)")
def export_data(format: str = Query("csv", pattern="^(csv|json)$", description="내보내기 포맷")):
    """
    전체 시계열 데이터를 CSV 또는 JSON 파일로 다운로드합니다.
    """
    items, _ = data_service.get_items(limit=10000, sort_by="date", sort_order="asc")
    
    if format == "json":
        data = [item.model_dump() for item in items]
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="samsung_stock_data.json"'}
        )
    else:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "date", "value", "memo", "created_at"])
        for item in items:
            writer.writerow([item.id, item.date, item.value, item.memo, item.created_at])
        output.seek(0)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="samsung_stock_data.csv"'}
        )

@router.get("/{id}", response_model=DataItemResponse, summary="특정 데이터 단건 조회")
def get_data_item(id: str):
    item = data_service.get_item(id)
    if not item:
        raise HTTPException(status_code=404, detail="해당 ID의 데이터를 찾을 수 없습니다.")
    return item

@router.put("/{id}", response_model=DataItemResponse, summary="데이터 수정")
def update_data_item(id: str, item: DataItemUpdate):
    """
    지정한 ID의 데이터(date, value, memo)를 수정합니다.
    """
    updated = data_service.update_item(id, item)
    if not updated:
        raise HTTPException(status_code=404, detail="해당 ID의 데이터를 찾을 수 없습니다.")
    return updated

@router.delete("/{id}", summary="데이터 삭제")
def delete_data_item(id: str):
    """
    지정한 ID의 데이터를 삭제합니다.
    """
    success = data_service.delete_item(id)
    if not success:
        raise HTTPException(status_code=404, detail="해당 ID의 데이터를 찾을 수 없습니다.")
    return {"message": "데이터가 성공적으로 삭제되었습니다.", "id": id}
