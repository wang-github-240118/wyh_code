import re


def extract_pt_numbers(file_path):
    """
    从文件中提取特定格式的PT编号（如pt10_dom_M108483317LE_cropped_cropped.tif）

    参数:
        file_path: 包含PT编号的文件路径

    返回:
        包含所有PT编号的集合
    """
    pt_numbers = set()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # 匹配pt开头，后面跟数字、下划线和其他字符的完整编号
                # 例如：pt10_dom_M108483317LE_cropped_cropped.tif
                pattern = r'pt\d+[_\w]+'
                matches = re.findall(pattern, line, re.IGNORECASE)

                # 添加到集合中（去重）
                for match in matches:
                    pt_numbers.add(match)

        print(f"从 {file_path} 中提取到 {len(pt_numbers)} 个PT编号")
        return pt_numbers

    except FileNotFoundError:
        print(f"错误：找不到文件 {file_path}")
        return set()
    except Exception as e:
        print(f"提取PT编号时发生错误：{str(e)}")
        return set()


def filter_lines_by_pt(source_file, pt_numbers, output_file):
    """
    从源文件中筛选出包含指定PT编号的行，并保存到输出文件

    参数:
        source_file: 源文件路径
        pt_numbers: 需要匹配的PT编号集合
        output_file: 输出文件路径
    """
    if not pt_numbers:
        print("没有需要匹配的PT编号，无法进行筛选")
        return

    matched_lines = []
    # 创建精确匹配的正则表达式模式
    patterns = {pt: re.compile(re.escape(pt), re.IGNORECASE) for pt in pt_numbers}

    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            for line in f:
                # 检查当前行是否包含任何一个PT编号
                for pt, pattern in patterns.items():
                    if pattern.search(line):
                        matched_lines.append(line)
                        break  # 找到匹配后不再检查其他编号

        print(f"从 {source_file} 中找到 {len(matched_lines)} 行匹配的内容")

        # 保存匹配的行到输出文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(matched_lines)

        print(f"匹配的内容已保存到 {output_file}")

    except FileNotFoundError:
        print(f"错误：找不到文件 {source_file}")
    except Exception as e:
        print(f"筛选文件时发生错误：{str(e)}")


# if __name__ == "__main__":
#     # 配置文件路径
#     pt_file = "pt_numbers.txt"  # 包含PT编号的文件
#     source_file = "source.txt"  # 需要筛选的源文件
#     output_file = "matched_lines.txt"  # 输出结果文件
#
#     # 提取PT编号
#     pt_numbers = extract_pt_numbers(pt_file)
#
#     # 筛选包含PT编号的行
#     if pt_numbers:
#         filter_lines_by_pt(source_file, pt_numbers, output_file)

if __name__ == "__main__":
    # 配置文件路径
    pt_file = r"D:\长航程\win25_协助502校核\eqc.lis"  # 包含pt编号的文件
    source_file = r"D:\长航程\win25_协助502校核\Azimuth_Elevation_henu_use.txt"  # 需要筛选的源文件
    output_file = r"D:\长航程\win25_协助502校核\eqc.txt"  # 输出结果文件

    # 提取pt编号
    pt_numbers = extract_pt_numbers(pt_file)

    # 筛选包含pt编号的行
    if pt_numbers:
        filter_lines_by_pt(source_file, pt_numbers, output_file)
