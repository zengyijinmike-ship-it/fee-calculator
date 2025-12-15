import streamlit as st
import pandas as pd

# --- 核心逻辑类 (保持不变) ---
class FeeCalculator:
    def __init__(self):
        # A. 普通结构 (OFC/SPC - General)
        self.data_general = {
            "按日": (3000, 0.0011, 6000, 2000, 0.0009, 5000),
            "按周": (3000, 0.0008, 4000, 2000, 0.0007, 3500),
            "按月": (3000, 0.0006, 3000, 2000, 0.0005, 2500),
            "按季度": (3000, 0.0005, 2500, 2000, 0.0004, 2000),
            "按半年": (3000, 0.0005, 2000, 2000, 0.0004, 1500),
            "按年": (3000, 0.0005, 1500, 2000, 0.0004, 1000),
        }
        # B. 复杂结构 (OFC/SPC - Complex)
        self.data_complex = {
            "按日": (5000, 0.0013, 7000, 4000, 0.0011, 6000),
            "按周": (5000, 0.0010, 5000, 4000, 0.0009, 4500),
            "按月": (5000, 0.0008, 4000, 4000, 0.0007, 3500),
            "按季度": (5000, 0.0007, 3500, 4000, 0.0006, 3000),
            "按半年": (5000, 0.0007, 3000, 4000, 0.0006, 2500),
            "按年": (5000, 0.0007, 2500, 4000, 0.0004, 2000),
        }
        # C. LPF
        self.data_lpf = {
            "按月": (4000, None, 36000, 3000, 0.0003, 33000),
            "按季度": (4000, None, 30000, 3000, 0.0003, 27000),
            "按半年": (4000, None, 20000, 3000, 0.0003, 17000),
            "按年": (4000, None, 15000, 3000, 0.0003, 12000),
        }

    def get_quote(self, fund_type, is_complex, frequency):
        if fund_type == "LPF":
            if frequency not in self.data_lpf: return None
            row = self.data_lpf[frequency]
        else:
            data = self.data_complex if is_complex else self.data_general
            row = data.get(frequency)
            if not row: return None

        std_setup, std_rate, std_min, disc_setup, disc_rate, disc_min = row
        
        # 格式化函数
        def fmt_rate(r): return f"{r*10000:.1f} bps" if r is not None else "N/A"
        def fmt_money(m): return f"${m:,}"

        return {
            "标准报价": [fmt_money(std_setup), fmt_rate(std_rate), fmt_money(std_min)],
            "优惠报价": [fmt_money(disc_setup), fmt_rate(disc_rate), fmt_money(disc_min)]
        }

# --- Streamlit 界面代码 ---
st.set_page_config(page_title="费用函计算器", layout="centered")

st.title("📊 基金行政管理费率计算器")
st.markdown("---")

# 1. 侧边栏：输入区域
with st.sidebar:
    st.header("参数设置")
    fund_type = st.selectbox("基金类型", ["OFC", "SPC", "LPF"])
    
    # LPF 没有复杂结构选项
    is_complex = False
    if fund_type != "LPF":
        structure = st.radio("是否为多层复杂结构?", ["否 (普通)", "是 (复杂)"])
        is_complex = (structure == "是 (复杂)")
    
    freq_options = ["按日", "按周", "按月", "按季度", "按半年", "按年"]
    frequency = st.selectbox("估值频率", freq_options)
    
    calc_btn = st.button("生成报价", type="primary")

# 2. 主区域：显示结果
if calc_btn:
    calculator = FeeCalculator()
    result = calculator.get_quote(fund_type, is_complex, frequency)
    
    if result:
        st.subheader(f"报价结果：{fund_type} - {frequency}")
        
        # 创建展示表格
        df = pd.DataFrame(result, index=["设立费 (Setup Fee)", "最低年费率 (Min Rate)", "最低收费 (Min Fee)"])
        st.table(df)
        
        # 提示信息
        st.info("注：上述费用仅包含行政管理人基础费用，不含第三方托管费及单笔交易费。")
    else:
        st.error(f"无法计算：{fund_type} 通常不支持 {frequency} 估值。")
else:
    st.info("👈 请在左侧选择参数并点击“生成报价”")
    