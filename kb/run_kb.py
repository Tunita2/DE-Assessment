"""
Mini Knowledge Base - Entrypoint & Demo Query Runner
Part B of Xbrain Data Engineer Assessment
"""

from pathlib import Path
import sys

def main():
    print("=== [KB] Bắt đầu khởi tạo & truy vấn Mini Knowledge Base ===")
    docs_dir = Path(__file__).resolve().parent.parent / "data" / "docs"
    
    if not docs_dir.exists():
        print(f"[Error] Không tìm thấy thư mục tài liệu tại {docs_dir}")
        sys.exit(1)
        
    print(f"[Info] Nguồn tài liệu: {docs_dir}")
    # KB Indexing and querying logic will be implemented here

if __name__ == "__main__":
    main()
