"""
Log Processing Pipeline - Entrypoint
Part A of Xbrain Data Engineer Assessment
"""

from pathlib import Path
import sys

def main():
    print("=== [Pipeline] Bắt đầu quy trình xử lý log 7 ngày ===")
    data_path = Path(__file__).resolve().parent.parent / "data" / "app_logs_7days.jsonl"
    output_dir = Path(__file__).resolve().parent / "output"
    
    if not data_path.exists():
        print(f"[Error] Không tìm thấy file dữ liệu tại {data_path}")
        sys.exit(1)
        
    print(f"[Info] Đọc dữ liệu từ: {data_path}")
    print(f"[Info] Kết quả sẽ được ghi vào: {output_dir}")
    # Pipeline execution logic will be implemented here

if __name__ == "__main__":
    main()
