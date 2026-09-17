from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re

class DataItemBase(BaseModel):
    date: str = Field(..., description="날짜 (YYYY-MM-DD)", examples=["2024-01-02"])
    value: float = Field(..., gt=0, le=10000000.0, description="수치값 (종가, 0 초과 1,000만 이하)", examples=[76000.0])
    memo: Optional[str] = Field("", max_length=500, description="메모 또는 추가 정보 (최대 500자)", examples=["시가 74,693원, 거래량 1,714만주"])

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v.strip()):
            raise ValueError("날짜 형식은 YYYY-MM-DD 이어야 합니다.")
        return v.strip()

    @field_validator("memo")
    @classmethod
    def sanitize_memo(cls, v: Optional[str]) -> str:
        if not v:
            return ""
        # Strip dangerous HTML script tags for XSS protection
        sanitized = re.sub(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", "", v, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r"[<>]", "", sanitized)
        return sanitized.strip()

class DataItemCreate(DataItemBase):
    pass

class DataItemUpdate(BaseModel):
    date: Optional[str] = Field(None, description="날짜 (YYYY-MM-DD)")
    value: Optional[float] = Field(None, gt=0, le=10000000.0, description="수치값")
    memo: Optional[str] = Field(None, max_length=500, description="메모 또는 추가 정보 (최대 500자)")

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", v.strip()):
                raise ValueError("날짜 형식은 YYYY-MM-DD 이어야 합니다.")
            return v.strip()
        return v

    @field_validator("memo")
    @classmethod
    def sanitize_memo(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            sanitized = re.sub(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", "", v, flags=re.IGNORECASE | re.DOTALL)
            sanitized = re.sub(r"[<>]", "", sanitized)
            return sanitized.strip()
        return v

class DataItemResponse(DataItemBase):
    id: str = Field(..., description="문서 ID")
    created_at: Optional[str] = Field(None, description="생성 일시")
    updated_at: Optional[str] = Field(None, description="수정 일시")

class DataMetrics(BaseModel):
    total: float = Field(..., description="합계")
    average: float = Field(..., description="평균")
    max: float = Field(..., description="최고값")
    min: float = Field(..., description="최저값")
    latest: Optional[float] = Field(None, description="최신값")

class DataSummaryResponse(BaseModel):
    period: str = Field(..., description="데이터 기간 (예: 2024-01 ~ 2026-09)")
    count: int = Field(..., description="총 데이터 개수")
    metrics: DataMetrics = Field(..., description="주요 수치 지표")
    trend: str = Field(..., description="추세 분석 결과 (상승/하락/유지)")
    insights: Optional[str] = Field(None, description="도메인 특화 인사이트 요약")

class DataStatisticsResponse(BaseModel):
    period: str = Field(..., description="데이터 기간")
    count: int = Field(..., description="총 데이터 개수")
    volatility: float = Field(..., description="20일 역사적 변동성(표준편차)")
    sma_20: float = Field(..., description="20일 단순이동평균")
    sma_60: float = Field(..., description="60일 단순이동평균")
    max_price: float = Field(..., description="최고가")
    max_date: str = Field(..., description="최고가 기록 일자")
    min_price: float = Field(..., description="최저가")
    min_date: str = Field(..., description="최저가 기록 일자")
    total_return_pct: float = Field(..., description="전체 기간 누적 수익률(%)")
    rsi_14: float = Field(..., description="14일 상대강도지수(RSI)")

