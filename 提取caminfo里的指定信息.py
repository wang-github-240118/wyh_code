import os
import re
from openpyxl import Workbook


def extract_value_from_txt(file_path: str, target_key: str) -> str:
    """从文本文件中提取指定键的值（支持时间格式等特殊字符）"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if target_key in line:
                    # 修正正则表达式：匹配等号后的所有字符（除换行符外）
                    match = re.search(rf'{re.escape(target_key)}\s*=\s*(.+)', line.strip())
                    if match:
                        return match.group(1).strip()  # 去除首尾空格
    except Exception as e:
        print(f"读取文件出错: {file_path}, 错误信息: {e}")
    return "未找到"


def process_files_to_excel(
        input_folder: str,
        target_key: str = "IncidenceAngle",
        file_extension: str = ".txt"
) -> None:
    """处理所有文件并将结果保存到Excel"""

    # 自动生成输出文件路径
    output_excel_path = os.path.join(input_folder, f"{target_key}.xlsx")

    # 创建工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = target_key + "s" if not target_key.endswith("s") else target_key
    ws.append(["文件名", target_key])

    processed_count = 0
    for filename in sorted(os.listdir(input_folder)):
        if filename.lower().endswith(file_extension.lower()):
            file_path = os.path.join(input_folder, filename)
            if os.path.isfile(file_path):
                value = extract_value_from_txt(file_path, target_key)
                ws.append([filename, value])
                processed_count += 1

    # 保存结果
    if processed_count > 0:
        try:
            wb.save(output_excel_path)
            print(f"✅ 成功处理 {processed_count} 个文件，结果已保存到: {output_excel_path}")
        except Exception as e:
            print(f"❌ 保存Excel失败: {e}")
    else:
        print(f"⚠️ 警告: 在文件夹 {input_folder} 中未找到任何 {file_extension} 文件")


if __name__ == "__main__":
    # 配置参数
    config = {
        "input_folder": r"D:\桌面\sb\caminfo",  # 源文件夹路径
        "target_key": "StartTime ",                  # 要提取的参数名
        "file_ext": ".txt"                          # 要处理的文件扩展名
    }

    # 执行主程序
    if os.path.isdir(config["input_folder"]):
        process_files_to_excel(
            input_folder=config["input_folder"],
            target_key=config["target_key"],
            file_extension=config["file_ext"]
        )
    else:
        print(f"❌ 错误: 输入文件夹不存在: {config['input_folder']}")
