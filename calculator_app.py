import streamlit as st

# --- 核心逻辑类 ---
class FeeCalculator:
    def __init__(self):
        # A. 行政费率 (普通 & 复杂)
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
        # LPF 数据
        self.data_lpf = {
            "按月": (4000, None, 36000, 3000, 0.0003, 33000),
            "按季度": (4000, None, 30000, 3000, 0.0003, 27000),
            "按半年": (4000, None, 20000, 3000, 0.0003, 17000),
            "按年": (4000, None, 15000, 3000, 0.0003, 12000),
        }

        # B. 市场数据 (Market Data)
        # 格式: "市场名": (托管费率bps, 标准交易费USD, 优惠交易费USD)
        self.market_data = {
            "Cash Only (仅现金)": (0.0, 30, 20),
            "HK CCASS (香港结算)": (0.9, 25, 20),
            "USA (美国)": (0.7, 20, 18),
            "Euroclear/Clearstream": (0.75, 20, 18),
            "HK Stock Connect (港股通)": (2.5, 35, 30),
            "HK Bond Connect (债券通)": (1.0, 25, 20),
            "CMU (香港债务工具)": (0.9, 0, 0),
            "South Korea (韩国)": (2.5, 0, 0),
        }

    def get_quote(self, fund_type, is_complex, frequency, selected_markets):
        # --- 1. 基础费用计算逻辑 ---
        
        # 纯托管逻辑 (Pure Custody)
        if fund_type == "纯托管":
            # 设立费: 1000 (Std) / 800 (Disc)
            std_setup, disc_setup = 1000, 800
            # 最低费: 用户未指定，暂设为 N/A
            std_min, disc_min = 0, 0 
            # 基础费率: 固定 3 bps
            std_rate = 0.0003
            disc_rate = 0.0003
            
        # LPF 逻辑
        elif fund_type == "LPF":
            if frequency not in self.data_lpf: return None
            row = self.data_lpf[frequency]
            std_setup, std_rate, std_min, disc_setup, disc_rate, disc_min = row
            
        # OFC / SPC 逻辑
        else:
            data = self.data_complex if is_complex else self.data_general
            row = data.get(frequency)
            if not row: return None
            std_setup, std_rate, std_min, disc_setup, disc_rate, disc_min = row
        
        # --- 2. 托管与交易费计算 ---
        if not selected_markets:
            max_custody_bps = 0
            std_trans_list = []
            disc_trans_list = []
        else:
            # 提取托管费率 (取最大值)
            rates = [self.market_data[m][0] for m in selected_markets]
            max_custody_bps = max(rates) if rates else 0
            
            # 提取交易费
            std_trans_list = []
            disc_trans_list = []
            
            for m in selected_markets:
                _, std_fee, disc_fee = self.market_data[m]
                if std_fee > 0:
                    std_trans_list.append(f"• {m}: ${std_fee}")
                if disc_fee > 0:
                    disc_trans_list.append(f"• {m}: ${disc_fee}")
        
        custody_rate = max_custody_bps / 10000
        
        # --- 3. 结果格式化 ---
        def fmt_rate(r): return f"{r*10000:.2f} bps" if r is not None else "N/A"
        def fmt_money(m): 
            if m == 0: return "N/A" # 针对纯托管最低费
            return f"${m:,}"
        
        # 总费率计算器
        def sum_rate(base_r, cust_r):
            if base_r is None: return f"仅托管: {fmt_rate(cust_r)}"
            return fmt_rate(base_r + cust_r)

        return {
            "设立费": (fmt_money(std_setup), fmt_money(disc_setup)),
            "最低费": (fmt_money(std_min), fmt_money(disc_min)),
            # 如果是纯托管，显示"基础费率"，否则显示"行政费率"
            "基础费率名": "基础托管费率 (3bps)" if fund_type == "纯托管" else "行政费率",
            "基础费率值": (fmt_rate(std_rate), fmt_rate(disc_rate)),
            "托管费率": (fmt_rate(custody_rate), fmt_rate(custody_rate)),
            "-> 总费率": (sum_rate(std_rate, custody_rate), sum_rate(disc_rate, custody_rate)),
            "标准交易费": "<br>".join(std_trans_list) if std_trans_list else "实报实销 / 无",
            "优惠交易费": "<br>".join(disc_trans_list) if disc_trans_list else "实报实销 / 无"
        }

# --- Streamlit 界面代码 ---
st.set_page_config(page_title="费用函计算器 V7", layout="centered")

st.title("📊 基金报价计算器")
st.markdown("---")

# 1. 侧边栏
with st.sidebar:
    st.header("1. 基金类型")
    # 新增 "纯托管" 选项
    fund_type = st.selectbox("选择类型", ["OFC", "SPC", "LPF", "纯托管"])
    
    is_complex = False
    frequency = "不适用" # 默认值
    
    # 动态显示控件：纯托管不需要选结构和频率
    if fund_type == "纯托管":
        st.info("ℹ️ 纯托管模式：无需估值，费率 = 3bps + 市场托管费")
    
    elif fund_type == "LPF":
        st.header("2. 运营参数")
        frequency = st.selectbox("估值频率", ["按月", "按季度", "按半年", "按年"])
        
    else: # OFC / SPC
        st.header("2. 运营参数")
        structure = st.radio("结构复杂度", ["普通结构", "多层复杂结构"])
        is_complex = (structure == "多层复杂结构")
        frequency = st.selectbox("估值频率", ["按日", "按周", "按月", "按季度", "按半年", "按年"])
    
    st.header("3. 投资市场")
    calculator = FeeCalculator()
    market_list = list(calculator.market_data.keys())
    # 默认选中一个
    default_mk = [market_list[1]] if len(market_list) > 1 else []
    selected_markets = st.multiselect("选择拟投资市场 (可多选)", market_list, default=default_mk)
    
    calc_btn = st.button("计算报价", type="primary")

# 2. 主区域
if calc_btn:
    # 调用计算
    result = calculator.get_quote(fund_type, is_complex, frequency, selected_markets)
    
    if result:
        # 标题动态展示
        title_suffix = "" if fund_type == "纯托管" else f" ({frequency})"
        st.subheader(f"报价单：{fund_type}{title_suffix}")
        
        # HTML 表格渲染
        html_table = f"""
        <style>
            table.quote-table {{
                width: 100%; border-collapse: collapse; font-family: sans-serif;
            }}
            table.quote-table th, table.quote-table td {{
                border: 1px solid #ddd; padding: 10px; text-align: left; vertical-align: top;
            }}
            table.quote-table th {{ background-color: #f0f2f6; color: #31333F; }}
            .highlight {{ font-weight: bold; color: #0f52ba; }}
        </style>

        <table class="quote-table">
            <thead>
                <tr>
                    <th style="width:30%">项目 (Item)</th>
                    <th style="width:35%">标准报价 (Standard)</th>
                    <th style="width:35%">优惠报价 (Discount)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>1. 设立费</strong></td>
                    <td>{result['设立费'][0]}</td>
                    <td>{result['设立费'][1]}</td>
                </tr>
                <tr>
                    <td><strong>2. 最低费用</strong></td>
                    <td>{result['最低费'][0]}</td>
                    <td>{result['最低费'][1]}</td>
                </tr>
                <tr>
                    <td colspan="3" style="background-color: #fafafa; height: 5px; padding:0;"></td>
                </tr>
                <tr>
                    <td>3. {result['基础费率名']}</td>
                    <td>{result['基础费率值'][0]}</td>
                    <td>{result['基础费率值'][1]}</td>
                </tr>
                <tr>
                    <td>4. 市场次托管费率 (Max)</td>
                    <td>{result['托管费率'][0]}</td>
                    <td>{result['托管费率'][1]}</td>
                </tr>
                <tr>
                    <td><strong class="highlight">👉 总费率</strong></td>
                    <td><strong class="highlight">{result['-> 总费率'][0]}</strong></td>
                    <td><strong class="highlight">{result['-> 总费率'][1]}</strong></td>
                </tr>
                <tr>
                    <td colspan="3" style="background-color: #fafafa; height: 5px; padding:0;"></td>
                </tr>
                <tr>
                    <td><strong>5. 单笔交易费</strong></td>
                    <td>{result['标准交易费']}</td>
                    <td>{result['优惠交易费']}</td>
                </tr>
            </tbody>
        </table>
        """
        st.markdown(html_table, unsafe_allow_html=True)
        
        # 备注
        if fund_type == "纯托管":
            st.caption("注：纯托管模式费率结构为 3bps 基础费 + 市场次托管费。")
        if len(selected_markets) > 1:
            st.caption("注：多个市场时，次托管费率取其中最高值计入总成本。")

    else:
        st.error("计算失败，请检查参数设置。")
else:
    st.info("👈 请在左侧选择参数并点击计算")
