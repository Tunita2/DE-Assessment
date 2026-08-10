"""
Analytics & Reporting Module
Answers the 4 customer business questions using Pandas and DuckDB SQL
"""

from typing import Dict, Any, List
import pandas as pd
import duckdb
from tabulate import tabulate

from pipeline.src.models import CleanedLogRecord, QuarantineRecord


class LogAnalytics:
    """Performs statistical queries and business analytics on cleaned logs."""

    def __init__(self, cleaned_records: List[CleanedLogRecord], quarantine_records: List[QuarantineRecord]):
        self.cleaned_records = cleaned_records
        self.quarantine_records = quarantine_records
        self.df_clean = pd.DataFrame([r.to_dict() for r in cleaned_records]) if cleaned_records else pd.DataFrame()
        self.df_quarantine = pd.DataFrame([r.to_dict() for r in quarantine_records]) if quarantine_records else pd.DataFrame()

    def question_1_service_errors(self) -> Dict[str, Any]:
        """
        Câu 1: Service nào có nhiều lỗi (level=ERROR) nhất trong 7 ngày?
        """
        if self.df_clean.empty:
            return {"top_service": None, "table": [], "total_errors": 0}

        query = """
        SELECT 
            service,
            COUNT(*) AS error_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS percentage
        FROM df_clean
        WHERE level = 'ERROR'
        GROUP BY service
        ORDER BY error_count DESC;
        """
        df_clean = self.df_clean
        result_df = duckdb.query(query).to_df()
        
        top_service = result_df.iloc[0]["service"] if not result_df.empty else None
        top_errors = int(result_df.iloc[0]["error_count"]) if not result_df.empty else 0
        total_errors = int(result_df["error_count"].sum()) if not result_df.empty else 0

        return {
            "top_service": top_service,
            "top_errors": top_errors,
            "total_errors": total_errors,
            "df": result_df,
            "table_markdown": tabulate(result_df, headers=["Service", "Số lỗi (ERROR)", "Tỷ lệ (%)"], tablefmt="github", showindex=False)
        }

    def question_2_daily_trend(self) -> Dict[str, Any]:
        """
        Câu 2: Số lượng lỗi theo ngày của toàn hệ thống — ngày nào bất thường?
        """
        if self.df_clean.empty:
            return {"anomaly_date": None, "table": []}

        query = """
        SELECT 
            log_date AS date,
            SUM(CASE WHEN level = 'ERROR' THEN 1 ELSE 0 END) AS error_count,
            SUM(CASE WHEN level = 'WARN' THEN 1 ELSE 0 END) AS warn_count,
            SUM(CASE WHEN level = 'INFO' THEN 1 ELSE 0 END) AS info_count,
            COUNT(*) AS total_logs,
            ROUND(SUM(CASE WHEN level = 'ERROR' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 2) AS error_rate_pct
        FROM df_clean
        GROUP BY log_date
        ORDER BY date ASC;
        """
        df_clean = self.df_clean
        result_df = duckdb.query(query).to_df()

        # Find anomaly date (highest error count / rate)
        anomaly_row = result_df.sort_values(by="error_count", ascending=False).iloc[0] if not result_df.empty else None
        anomaly_date = str(anomaly_row["date"]) if anomaly_row is not None else None
        anomaly_errors = int(anomaly_row["error_count"]) if anomaly_row is not None else 0
        anomaly_rate = float(anomaly_row["error_rate_pct"]) if anomaly_row is not None else 0.0

        return {
            "anomaly_date": anomaly_date,
            "anomaly_errors": anomaly_errors,
            "anomaly_rate": anomaly_rate,
            "df": result_df,
            "table_markdown": tabulate(
                result_df,
                headers=["Ngày (UTC)", "Số ERROR", "Số WARN", "Số INFO", "Tổng Log", "Tỷ lệ Lỗi (%)"],
                tablefmt="github",
                showindex=False
            )
        }

    def question_3_top_error_types(self) -> Dict[str, Any]:
        """
        Câu 3: Top 3 loại lỗi (message/error code) phổ biến nhất, thuộc service nào?
        """
        if self.df_clean.empty:
            return {"top_3": [], "table": []}

        query = """
        SELECT 
            service,
            message,
            COUNT(*) AS occurrence_count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM df_clean WHERE level = 'ERROR'), 2) AS pct_of_all_errors
        FROM df_clean
        WHERE level = 'ERROR'
        GROUP BY service, message
        ORDER BY occurrence_count DESC
        LIMIT 3;
        """
        df_clean = self.df_clean
        result_df = duckdb.query(query).to_df()

        top_3_list = result_df.to_dict(orient="records")

        return {
            "top_3": top_3_list,
            "df": result_df,
            "table_markdown": tabulate(
                result_df,
                headers=["Service", "Thông điệp Lỗi (Error Pattern)", "Số lần xuất hiện", "Tỷ lệ trong tổng ERROR (%)"],
                tablefmt="github",
                showindex=False
            )
        }

    def question_4_cleaning_statistics(self, total_raw_lines: int) -> Dict[str, Any]:
        """
        Câu 4: Có bao nhiêu bản ghi bị loại/sửa trong bước làm sạch, thuộc những loại vấn đề gì?
        """
        total_quarantined = len(self.quarantine_records)
        total_clean = len(self.cleaned_records)

        if self.df_quarantine.empty:
            breakdown_df = pd.DataFrame(columns=["issue_category", "count", "pct"])
        else:
            query = """
            SELECT 
                issue_category AS issue_type,
                COUNT(*) AS count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM df_quarantine), 2) AS pct_of_quarantine
            FROM df_quarantine
            GROUP BY issue_category
            ORDER BY count DESC;
            """
            df_quarantine = self.df_quarantine
            breakdown_df = duckdb.query(query).to_df()

        # Add resolution action column
        action_map = {
            "Duplicate Record": "Loại bỏ bản ghi trùng lặp (Deduplication)",
            "Invalid Timestamp": "Loại bỏ (giá trị không thể parse thành mốc thời gian)",
            "Malformed JSON": "Loại bỏ (dòng log bị cắt cụt / lỗi cú pháp JSON)",
            "Missing / Invalid Level": "Loại bỏ (trường level bị null/thiếu)"
        }
        breakdown_df["action"] = breakdown_df["issue_type"].map(lambda x: action_map.get(x, "Loại bỏ vào Quarantine"))

        return {
            "total_raw_lines": total_raw_lines,
            "total_clean": total_clean,
            "total_quarantined": total_quarantined,
            "quarantine_pct": round((total_quarantined / total_raw_lines) * 100, 2) if total_raw_lines > 0 else 0,
            "breakdown_df": breakdown_df,
            "table_markdown": tabulate(
                breakdown_df[["issue_type", "count", "pct_of_quarantine", "action"]],
                headers=["Loại vấn đề dữ liệu", "Số lượng", "Tỷ lệ trong Quarantine (%)", "Hành động xử lý"],
                tablefmt="github",
                showindex=False
            )
        }
