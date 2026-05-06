import csv
import os
import shutil
import re  # 导入正则模块，实现数字严格精确匹配


def copy_and_rename_files(csv_file_path, source_folder, target_folder):
    """
    读取CSV文件，严格匹配位数对应ptX文件，拷贝到目标文件夹并重命名（保留pt前缀）
    :param csv_file_path: CSV文件路径
    :param source_folder: 源文件所在文件夹（存放带ptX的文件）
    :param target_folder: 目标文件夹（拷贝并重命名后的文件存放位置）
    """
    # 1. 校验必要路径是否存在
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"CSV文件不存在：{csv_file_path}")
    if not os.path.isdir(source_folder):
        raise NotADirectoryError(f"源文件夹不存在：{source_folder}")

    # 2. 创建目标文件夹（如果不存在）
    os.makedirs(target_folder, exist_ok=True)

    # 3. 读取CSV文件并处理每一行数据
    with open(csv_file_path, 'r', encoding='gbk') as csv_file:
        # 按CSV表头读取数据（列名：点号、新点号）
        csv_reader = csv.DictReader(csv_file)

        # 校验CSV是否包含必要列
        required_columns = ['点号', '新点号']
        for col in required_columns:
            if col not in csv_reader.fieldnames:
                raise ValueError(f"CSV文件缺少必要列：{col}，当前列名：{csv_reader.fieldnames}")

        # 4. 遍历CSV中的每一条记录
        for row_num, row in enumerate(csv_reader, start=2):  # row_num从2开始（跳过表头，对应实际行号）
            try:
                # 提取原始点号和新点号（去除前后空格，确保严格匹配）
                original_point = row['点号'].strip()
                new_point = row['新点号'].strip()

                # 校验点号是否为有效非空内容
                if not original_point or not new_point:
                    print(f"警告：第{row_num}行数据为空，跳过处理")
                    continue

                # 5. 构建严格匹配的关键字（pt+原始点号，如pt2，确保位数一致）
                source_file_keyword = f"pt{original_point}"
                # 构建重命名后的新关键字（pt+新点号，如pt102，保留pt前缀）
                new_file_keyword = f"pt{new_point}"

                # 6. 构建正则表达式，实现数字严格位数匹配（杜绝pt2匹配pt20/pt02）
                # 正则说明：精确匹配source_file_keyword，且前后非数字（确保位数严格对应）
                regex_pattern = rf"(?<!\d){re.escape(source_file_keyword)}(?!\d)"

                # 7. 遍历源文件夹，查找包含严格匹配关键字的文件
                found_files = []
                for filename in os.listdir(source_folder):
                    if re.search(regex_pattern, filename):
                        found_files.append(filename)

                # 8. 处理未找到匹配文件的情况
                if not found_files:
                    print(f"警告：第{row_num}行，未找到严格匹配{source_file_keyword}的文件（位数对应），跳过")
                    continue

                # 9. 遍历匹配到的文件，进行拷贝并重命名
                for source_filename in found_files:
                    # 构建源文件完整路径
                    source_file_path = os.path.join(source_folder, source_filename)

                    # 正则精确替换，实现严格位数对应重命名（仅替换目标ptX，不干扰其他数字）
                    target_filename = re.sub(regex_pattern, new_file_keyword, source_filename)

                    # 构建目标文件完整路径
                    target_file_path = os.path.join(target_folder, target_filename)

                    # 拷贝文件（保留文件元数据：修改时间、权限等）
                    shutil.copy2(source_file_path, target_file_path)
                    print(f"成功处理：{source_filename} -> {target_filename}")

            except Exception as e:
                print(f"错误：处理第{row_num}行时失败 - {str(e)}")


# ---------------------- 配置参数（保持你的实际路径，无需修改） ----------------------
CSV_FILE_PATH = r"C:\Users\Lenovo\Desktop\着陆区和长航程\2026试到航\24日第一次试导航20个校核点 - 偶数点.csv"
SOURCE_FOLDER = r"C:\Users\Lenovo\Desktop\着陆区和长航程\2026试到航\24号全体文件"
TARGET_FOLDER = r"C:\Users\Lenovo\Desktop\着陆区和长航程\2026试到航\24号挑选出来——河南大学"
# --------------------------------------------------------------------------------

# 执行程序
if __name__ == "__main__":
    try:
        copy_and_rename_files(CSV_FILE_PATH, SOURCE_FOLDER, TARGET_FOLDER)
        print("\n程序执行完成！")
    except Exception as e:
        print(f"\n程序异常终止：{str(e)}")