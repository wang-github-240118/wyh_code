import os
import pandas as pd

# 设定要读取的文件夹路径和输出文件路径
input_folder = r'D:\桌面\sb\河南大学结果汇总 - 副本'
output_file = r'D:\桌面\sb\结果\河南大学结果汇总.xlsx'

# 要提取的指标（保留原有）
target_metrics = [
    "失配长度均值（米）",
    "失配长度3σ值（米）",
    "高程误差绝对值均值（米）",
    "高程误差绝对值σ（米）",
    "高程误差绝对值3σ（米）",
    "高度误差均值（米）",
    "高程误差σ值（米）",
    "高程误差3σ值（米）",
    "整体高程误差σ值 + 均值",
    "整体高程误差3σ值 + 均值"
]

# ------------------- 新增核心：定义pt编号提取函数 + 收集并排序文件名 -------------------
def get_pt_number(filename):
    """从文件名中提取【第一个pt后】的纯数字，返回整数用于数值排序"""
    # 分割出第一个pt后的部分（适配文件名含多个pt的情况，如shadow_pt，只取第一个pt的编号）
    after_first_pt = filename.split('pt')[1]
    # 分割出_前的纯数字字符串，转整数实现数值排序（避免pt2排在pt10后）
    pt_num_str = after_first_pt.split('_')[0]
    return int(pt_num_str)

# 收集文件夹内所有xlsx文件名，过滤非xlsx文件
all_xlsx_files = [f for f in os.listdir(input_folder) if f.endswith('.xlsx')]
# 按pt编号从小到大数值排序
sorted_xlsx_files = sorted(all_xlsx_files, key=get_pt_number, reverse=False)

# 初始化汇总结果列表（保留原有）
results = []

# ------------------- 遍历【排序后】的文件名，执行原有汇总逻辑 -------------------
for filename in sorted_xlsx_files:
    file_path = os.path.join(input_folder, filename)
    try:
        # 读取Excel文件（保留原有engine='openpyxl'）
        df = pd.read_excel(file_path, engine='openpyxl')

        # 创建字典存储当前文件的结果（保留原有）
        row = {'文件名': filename}

        # 遍历指标提取值（保留原有）
        for metric in target_metrics:
            matched = df[df.iloc[:, 0] == metric]
            if not matched.empty:
                row[metric] = matched.iloc[0, 1]
            else:
                row[metric] = None  # 指标不存在则记为None

        results.append(row)
    except Exception as e:
        print(f"读取文件 {filename} 时出错: {e}")

# 保存排序后的汇总结果为Excel（保留原有）
summary_df = pd.DataFrame(results)
summary_df.to_excel(output_file, index=False, engine='openpyxl')

print(f"汇总完成！已按pt编号从小到大排序，结果保存在 {output_file}")