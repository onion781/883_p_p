# SmartCampus 智慧校园服务系统

CSIT883 System Analysis and Project Management，Group G17。

## 模块分工

- Huang：学业预警
- Song：校园智能问答
- Yang：教室预约、故障报修与维护
- Wang：统一材料申请、材料自动审核

## 本地运行

在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python core/database.py
python -m streamlit run app.py