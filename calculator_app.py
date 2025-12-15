import streamlit as st
import pandas as pd

# --- 核心逻辑类 ---
class FeeCalculator:
    def __init__(self):
        # A. 基础行政费率 (保持不变)
        self.data_general = {
            "按日": (3000, 0.0011, 6000, 2000, 0.0009, 5000),
            "按周": (3000, 0.0008, 4000, 2000, 0.0007, 3500),
            "按月": (3000, 0.0006, 3000, 2000, 0.0005, 2500),
            "按季度": (3000, 0.0005, 2500, 2000, 0.0004, 2000),
            "按半年": (3000, 0.0005, 2000, 2000, 0.0004, 1500),
            "按年": (3000, 0.0005, 1500, 2000, 0.0004, 1000),
        }
        self.data_complex = {
            "按日": (5000, 0.0013, 7000, 4000, 0.0011, 6000),
            "按周": (5000, 0.0010, 5000, 4000, 0.0009, 4500),
            "按月": (5000, 0.0008, 4000, 4000, 0.0007, 3500),
            "按季度": (5000, 0.0007, 3500, 4000, 0.0006, 3000),
            "按半年": (5000, 0.0007, 3000, 4000, 0.0006, 2500),
            "按年": (5000, 0.0007, 2500, 4000, 0.0004, 2000),
        }
        self.data_lpf = {
            "按月": (4000, None, 36000, 3000, 0.0003, 33000),
            "按季度": (4000, None, 30000, 3000, 0.0003, 27000),
            "按半年": (4000, None, 20000, 3000, 0.0003, 17000),
            "按年": (4000, None, 15000, 3000, 0.0003, 12000),
        }

        # B. 新增：市场次托管数据 (Market Sub-custody Data)
        # 格式: "市场名": (托管费率bps, 单笔交易费USD)
        # 数据来源：费率底稿.csv
        self.market_data = {
            "不涉及/仅现金 (Cash only)": (0.0, 0),
            "香港结算系统 (Hong Kong CCASS)": (0.9, 25),
            "美国 (U.S.A)": (0.7, 20),
            "欧洲清算系统 (Euroclear/Clearsteam)": (0.75, 20),
            "香港债务工具 (CMU)": (0.9, 0), # 假设无固定交易费或按实报销
            "韩国 (South Korea)": (2.5, 0),
            "港股通 (Hong Kong Stock Connect)": (2.5, 35),
            "债券通 (Hong Kong Bond Connect)": (1.0, 0),
        }

    def get_quote(self, fund_type, is_complex, frequency, market_name):
        # 1. 获取行政管理费
        if fund_type == "LPF":
            if frequency not in self.data_lpf: return None
            row = self.data_lpf[frequency]
        else:
            data = self.data_complex if is_complex else self.data_general
            row = data.get(frequency)
            if not row: return None

        std_setup, std_rate, std_min, disc_setup, disc_rate, disc_min = row
        
        # 2. 获取托管费
        custody_bps, trans_fee = self.market_data.get(market_name, (0, 0))
        custody_rate = custody_bps / 10000  # 转换为小数
        
        # 格式化工具
        def fmt_rate(r): return f"{r*10000:.2f} bps" if r is not None else "N/A"
        def fmt_money(m): return f"${m:,}"
        
        # 计算总费率 (行政 + 托管)
        # 注意：LPF 标准报价没有费率(None)，无法相加
        def sum_rate(admin_r, cust_r):
            if admin_r is None: return f"仅托管: {fmt_rate(cust_r)}"
            return fmt_rate(admin_r + cust_r)

        return {
            "行政设立费": (fmt_money(std_setup), fmt_money(disc_setup)),
            "行政最低费": (fmt_money(std_min), fmt_money(disc_min)),
            # 费率部分拆解
            "行政费率": (fmt_rate(std_rate), fmt_rate(disc_rate)),
            "托管费率 (额外)": (fmt_rate(custody_rate), fmt_rate(custody_rate)),
            "-> 总预估费率": (sum_rate(std_rate, custody_rate), sum_rate(disc_rate, custody_rate)),
            # 交易费
            "单笔交易费": (f"${trans_fee}" if trans_fee > 0 else "实报实销", f"${trans_fee}" if trans_fee > 0 else "实报实销")
        }

# --- Streamlit 界面代码 ---
st.set_page_config(page_title="费用函计算器 V2", layout="centered")

st.title("📊 基金报价计算器 (含托管)")
st.markdown("---")

# 1. 侧边栏
with st.sidebar:
    st.header("1. 基金结构")
    fund_type = st.selectbox("基金类型", ["OFC", "SPC", "LPF"])
    
    is_complex = False
    if fund_type != "LPF":
        structure = st.radio("结构复杂度", ["普通结构", "多层复杂结构"])
        is_complex = (structure == "多层复杂结构")
    
    st.header("2. 运营参数")
    frequency = st.selectbox("估值频率", ["按日", "按周", "按月", "按季度", "按半年", "按年"])
    
    # 新增：市场选择
    st.header("3. 投资市场 (影响托管费)")
    calculator = FeeCalculator()
    market_list = list(calculator.market_data.keys())
    market = st.selectbox("主要投资市场", market_list)
    
    calc_btn = st.button("计算总报价", type="primary")

# 2. 主区域
if calc_btn:
    result = calculator.get_quote(fund_type, is_complex, frequency, market)
    
    if result:
        st.subheader(f"报价单：{fund_type} ({frequency})")
        st.caption(f"投资市场：{market}")
        
        # 构建表格数据
        # 列：标准报价 | 优惠报价
        data = {
            "项目 (Item)": [
                "1. 设立费 (One-off Setup)", 
                "2. 最低年费 (Min Fee)", 
                "---",
                "3. 行政费率 (Admin Rate)",
                f"4. 托管费率 ({market})",
                "👉 总费率 (Total Rate)",
                "---",
                "5. 单笔交易费 (Per Trade)"
            ],
            "标准报价 (Standard)": [
                result["行政设立费"][0],
                result["行政最低费"][0],
                "",
                result["行政费率"][0],
                result["托管费率 (额外)"][0],
                f"**{result['-> 总预估费率'][0]}**", # 加粗
                "",
                result["单笔交易费"][0]
            ],
            "优惠报价 (Discount)": [
                result["行政设立费"][1],
                result["行政最低费"][1],
                "",
                result["行政费率"][1],
                result["托管费率 (额外)"][1],
                f"**{result['-> 总预估费率'][1]}**", # 加粗
                "",
                result["单笔交易费"][1]
            ]
        }
        
        df = pd.DataFrame(data)
        
        # 使用 Streamlit 的 markdown 表格渲染以支持加粗
        st.markdown(df.to_markdown(index=False))
        
        st.warning("注意：总费率 = 行政费率 + 市场次托管费率。如涉及多个市场，请以实际发生的混合成本为准。")
        
    else:
        st.error(f"配置错误：{fund_type} 不支持 {frequency} 估值。")
else:
    st.info("👈 请在左侧选择参数（含投资市场）并点击计算")