import streamlit as st
import pandas as pd

# --- 核心逻辑类 ---
class FeeCalculator:
    def __init__(self):
        # A. 行政费率 (保持不变)
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

        # B. 市场次托管数据 (Market Sub-custody Data)
        # 格式: "市场名": (托管费率bps, 单笔交易费USD)
        self.market_data = {
            "不涉及/仅现金 (Cash only)": (0.0, 0),
            "香港结算系统 (Hong Kong CCASS)": (0.9, 25),
            "美国 (U.S.A)": (0.7, 20),
            "欧洲清算系统 (Euroclear/Clearsteam)": (0.75, 20),
            "香港债务工具 (CMU)": (0.9, 0),
            "韩国 (South Korea)": (2.5, 0),
            "港股通 (Hong Kong Stock Connect)": (2.5, 35),
            "债券通 (Hong Kong Bond Connect)": (1.0, 0),
        }

    def get_quote(self, fund_type, is_complex, frequency, selected_markets):
        # 1. 获取行政管理费
        if fund_type == "LPF":
            if frequency not in self.data_lpf: return None
            row = self.data_lpf[frequency]
        else:
            data = self.data_complex if is_complex else self.data_general
            row = data.get(frequency)
            if not row: return None

        std_setup, std_rate, std_min, disc_setup, disc_rate, disc_min = row
        
        # 2. 计算托管费 (逻辑：取所有选定市场中的最大费率)
        if not selected_markets:
            max_custody_bps = 0
            trans_fees_list = []
        else:
            # 提取费率列表
            rates = [self.market_data[m][0] for m in selected_markets]
            max_custody_bps = max(rates) if rates else 0
            
            # 提取交易费列表 (只列出 > 0 的)
            trans_fees_list = []
            for m in selected_markets:
                fee = self.market_data[m][1]
                if fee > 0:
                    trans_fees_list.append(f"${fee} ({m})")
        
        custody_rate = max_custody_bps / 10000
        
        # 格式化工具
        def fmt_rate(r): return f"{r*10000:.2f} bps" if r is not None else "N/A"
        def fmt