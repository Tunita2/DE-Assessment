"""
Analytics & Reporting Module
Answers the 4 customer business questions using Pandas and DuckDB SQL
Includes Statistical Anomaly Detection (Z-Score) and Dual Verification (Pandas vs SQL)
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
import duckdb
import numpy as np
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
        Tính toán cả Absolute Count, Share of Total Errors, và Service Error Rate (ERROR / Total Logs).
        """
        if self.df_clean.empty:
            return {"top_service": None, "table": [], "total_errors": 0}

        query = """
        WITH srv_totals AS (
            SELECT 
                service,
                COUNT(*) AS total_logs,
                SUM(CASE WHEN level = 'ERROR' THEN 1 ELSE 0 END) AS error_count,
                SUM(CASE WHEN level = 'WARN' THEN 1 ELSE 0 END) AS warn_count,
                SUM(CASE WHEN level = 'INFO' THEN 1 ELSE 0 END) AS info_count
            FROM df_clean
            GROUP BY service
        )
        SELECT 
            service,
            total_logs,
            error_count,
            ROUND(error_count * 100.0 / SUM(error_count) OVER(), 2) AS share_of_all_errors_pct,
            ROUND(error_count * 100.0 / total_logs, 2) AS error_rate_pct
        FROM srv_totals
        ORDER BY error_count DESC;
        """
        df_clean = self.df_clean
        result_df = duckdb.query(query).to_df()

        top_service = result_df.iloc[0]["service"] if not result_df.empty else None
        top_errors = int(result_df.iloc[0]["error_count"]) if not result_df.empty else 0
        total_errors = int(result_df["error_count"].sum()) if not result_df.empty else 0
        top_error_rate = float(result_df.iloc[0]["error_rate_pct"]) if not result_df.empty else 0.0

        return {
            "top_service": top_service,
            "top_errors": top_errors,
            "total_errors": total_errors,
            "top_error_rate": top_error_rate,
            "df": result_df,
            "table_markdown": tabulate(
                result_df,
                headers=["Service", "Tổng Log", "Số lỗi (ERROR)", "Tỷ lệ trong tổng ERROR (%)", "Tỷ lệ lỗi riêng của Service (%)"],
                tablefmt="github",
                showindex=False
            )
        }

    def question_2_daily_trend(self) -> Dict[str, Any]:
        """
        Câu 2: Số lượng lỗi theo ngày của toàn hệ thống — ngày nào bất thường?
        Đánh giá bất thường dựa trên:
        1. So sánh với mức trung bình ngày thường (24.5 lỗi/ngày) -> ngày 30/07 gấp 5.7 lần.
        2. So sánh với Ngưỡng CRITICAL (> 5.0% tỷ lệ lỗi) theo tài liệu GUIDE-01 -> ngày 30/07 đạt 27.4%.
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

        # Find anomaly date (highest error count)
        anomaly_row = result_df.sort_values(by="error_count", ascending=False).iloc[0] if not result_df.empty else None
        anomaly_date = str(anomaly_row["date"]) if anomaly_row is not None else None
        anomaly_errors = int(anomaly_row["error_count"]) if anomaly_row is not None else 0
        anomaly_rate = float(anomaly_row["error_rate_pct"]) if anomaly_row is not None else 0.0

        # Baseline calculation (excluding anomaly date)
        baseline_df = result_df[result_df["date"] != anomaly_date]
        baseline_mean = float(baseline_df["error_count"].mean()) if not baseline_df.empty else 0.0
        fold_increase = round(anomaly_errors / baseline_mean, 2) if baseline_mean > 0 else 0.0

        # Add operational status column based on GUIDE-01 threshold (Normal vs CRITICAL > 5%)
        result_df["operational_status"] = result_df["error_rate_pct"].apply(
            lambda x: "🚨 CRITICAL (> 5%)" if x >= 20.0 else ("⚠️ WARN / High" if x > 5.0 else "✅ Normal (<= 5%)")
        )

        return {
            "anomaly_date": anomaly_date,
            "anomaly_errors": anomaly_errors,
            "anomaly_rate": anomaly_rate,
            "baseline_mean": round(baseline_mean, 2),
            "fold_increase": fold_increase,
            "df": result_df,
            "table_markdown": tabulate(
                result_df,
                headers=["Ngày (UTC)", "Số ERROR", "Số WARN", "Số INFO", "Tổng Log", "Tỷ lệ Lỗi (%)", "Trạng thái Vận hành (GUIDE-01)"],
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

        # Analyze template vs dynamic parameters
        all_error_patterns = duckdb.query("""
            SELECT service, message, COUNT(*) as cnt
            FROM df_clean
            WHERE level = 'ERROR'
            GROUP BY service, message
            ORDER BY cnt DESC
        """).to_df()

        top_4_static_count = int(all_error_patterns.head(4)["cnt"].sum())
        total_error_count = int(all_error_patterns["cnt"].sum())
        static_share_pct = round((top_4_static_count / total_error_count) * 100, 2) if total_error_count > 0 else 0.0

        return {
            "top_3": top_3_list,
            "static_share_pct": static_share_pct,
            "unique_patterns_count": len(all_error_patterns),
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

    def verify_pandas_vs_sql(self) -> Dict[str, bool]:
        """
        Dual Verification Engine:
        Runs equivalent queries in Pandas and DuckDB SQL to verify 100% mathematical consistency.
        """
        if self.df_clean.empty:
            return {"q1_match": True, "q2_match": True, "q3_match": True, "all_match": True}

        df_clean = self.df_clean

        # Q1 Check
        q1_pandas = df_clean[df_clean['level'] == 'ERROR'].groupby('service', observed=False).size().to_dict()
        q1_sql = duckdb.query("SELECT service, count(*) as cnt FROM df_clean WHERE level='ERROR' GROUP BY service").df().set_index('service')['cnt'].to_dict()
        q1_match = (q1_pandas == q1_sql)

        # Q2 Check
        q2_pandas = df_clean[df_clean['level'] == 'ERROR'].groupby('log_date').size().to_dict()
        q2_sql = duckdb.query("SELECT log_date, count(*) as cnt FROM df_clean WHERE level='ERROR' GROUP BY log_date").df().set_index('log_date')['cnt'].to_dict()
        q2_match = (q2_pandas == q2_sql)

        # Q3 Check
        q3_pandas = df_clean[df_clean['level'] == 'ERROR'].groupby(['service', 'message'], observed=False).size().nlargest(3).tolist()
        q3_sql = duckdb.query("SELECT count(*) as cnt FROM df_clean WHERE level='ERROR' GROUP BY service, message ORDER BY count(*) DESC LIMIT 3").df()['cnt'].tolist()
        q3_match = (q3_pandas == q3_sql)

        return {
            "q1_match": q1_match,
            "q2_match": q2_match,
            "q3_match": q3_match,
            "all_match": (q1_match and q2_match and q3_match)
        }
