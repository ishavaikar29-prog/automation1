# excel_builder.py
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

def style_header(row):
    for cell in row:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="FFC000", fill_type="solid")

def autosize(ws):
    for col in ws.columns:
        length = max(len(str(c.value or "")) for c in col)
        ws.column_dimensions[col[0].column_letter].width = length + 2

def build_excel(users, posts, todos, filename="daily_report.xlsx"):
    wb = Workbook()

    ws = wb.active
    ws.title = "Users"
    ws.append(["ID", "Name", "Username", "Email"])
    style_header(ws[1])
    for u in users:
        ws.append([u["id"], u["name"], u["username"], u["email"]])
    autosize(ws)

    ws2 = wb.create_sheet("Posts")
    ws2.append(["ID", "UserID", "Title"])
    style_header(ws2[1])
    for p in posts:
        ws2.append([p["id"], p["userId"], p["title"]])
    autosize(ws2)

    ws3 = wb.create_sheet("Todos")
    ws3.append(["ID", "UserID", "Title", "Completed"])
    style_header(ws3[1])
    for t in todos:
        ws3.append([t["id"], t["userId"], t["title"], t["completed"]])
    autosize(ws3)

    wb.save(filename)
    return filename
