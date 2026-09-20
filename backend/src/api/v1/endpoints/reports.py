from fastapi import APIRouter, Depends
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.schemas.reports import ReportsSummaryOut
from src.services.reports_service import ReportsService

router = APIRouter()

@router.get("/summary", response_model=ReportsSummaryOut)
def get_reports_summary(db: Session = Depends(get_db)):
    return ReportsService.get_summary(db)

@router.get("/excel")
def export_excel(db: Session = Depends(get_db)):
    excel_stream = ReportsService.generate_excel(db)
    headers = {
        "Content-Disposition": "attachment; filename=PredictCNC_Fleet_Report.xlsx"
    }
    return Response(
        content=excel_stream.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )

@router.get("/pdf")
def export_pdf(db: Session = Depends(get_db)):
    pdf_stream = ReportsService.generate_pdf(db)
    headers = {
        "Content-Disposition": "inline; filename=PredictCNC_Fleet_Report.pdf"
    }
    return Response(
        content=pdf_stream.getvalue(),
        media_type="application/pdf",
        headers=headers
    )
