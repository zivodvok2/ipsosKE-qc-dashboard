import io
import pandas as pd


def to_excel_bytes(df: pd.DataFrame, sheet_name="Data") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        header_fmt = workbook.add_format({
            "bold": True, "font_color": "white",
            "bg_color": "#1F2B6C", "border": 1,
        })
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            worksheet.set_column(col_num, col_num, max(len(str(value)) + 4, 14))
    return buf.getvalue()


def to_sav_bytes(df: pd.DataFrame) -> bytes:
    try:
        import pyreadstat
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".sav", delete=False) as f:
            tmppath = f.name
        pyreadstat.write_sav(df, tmppath)
        with open(tmppath, "rb") as f:
            data = f.read()
        os.unlink(tmppath)
        return data
    except Exception as e:
        raise RuntimeError(f"SAV export failed: {e}")
