import pyodbc

def connect_db():
    conn_str = (
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=localhost\SQLEXPRESS;"
        r"DATABASE=VSLStudyDB;"
        r"Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)

try:
    conn = connect_db()
    cursor = conn.cursor()

    print("===== DANH SÁCH CHỦ ĐỀ =====")
    cursor.execute("""
        SELECT MaChuDe, TenChuDe, LoaiChuDe, MoTa
        FROM ChuDeHoc
        WHERE TrangThai = 1
    """)

    for row in cursor.fetchall():
        print(row.MaChuDe, row.TenChuDe, row.LoaiChuDe, row.MoTa)

    print("\n===== DANH SÁCH BÀI HỌC =====")
    cursor.execute("""
        SELECT bh.MaBaiHoc, cd.TenChuDe, bh.TieuDe, bh.NhanHienThi, bh.ModelLabel
        FROM BaiHoc bh
        JOIN ChuDeHoc cd ON bh.MaChuDe = cd.MaChuDe
        WHERE bh.TrangThai = 1
        ORDER BY cd.MaChuDe, bh.ThuTu
    """)

    for row in cursor.fetchall():
        print(row.MaBaiHoc, row.TenChuDe, row.TieuDe, row.NhanHienThi, row.ModelLabel)

    conn.close()

except Exception as e:
    print("Lỗi:")
    print(e)