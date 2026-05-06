import os
import csv
import glob
import chardet  # 需要安装chardet库来检测编码

def detect_encoding(file_path):
    """检测文件编码"""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read(10000))  # 读取前10000字节检测编码
    return result['encoding']

def rename_images(csv_file_path, images_dir):
    """
    根据CSV文件中的信息重命名影像文件
    
    参数:
    csv_file_path: CSV文件路径
    images_dir: 影像文件所在文件夹路径
    """
    # 读取CSV文件，建立NAC_ID与点号的映射关系
    nac_to_point = {}
    try:
        # 尝试检测文件编码
        encoding = detect_encoding(csv_file_path)
        print(f"检测到文件编码: {encoding}")
        
        # 如果检测失败，尝试常见编码
        if not encoding:
            encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'iso-8859-1', 'cp1252']
        else:
            encodings_to_try = [encoding] + ['utf-8', 'gbk', 'gb2312']
        
        # 尝试用不同编码打开文件并读取内容
        success = False
        for enc in encodings_to_try:
            try:
                with open(csv_file_path, 'r', encoding=enc) as csvfile:
                    print(f"成功使用编码 {enc} 打开文件")
                    
                    # 读取CSV内容
                    reader = csv.reader(csvfile)
                    
                    # 跳过表头（如果有的话）
                    # 如果你需要处理表头，请注释掉下面这行
                    next(reader)
                    
                    for row in reader:
                        # 检查行是否有足够的列
                        if len(row) >= 8:
                            # 第一列是点号，第八列是NAC_ID
                            point_number = row[0].strip()
                            nac_id = row[7].strip()
                            nac_to_point[nac_id] = point_number
                        else:
                            print(f"警告：行 {row} 列数不足，已跳过")
                
                success = True
                break  # 成功读取后退出编码尝试循环
                
            except UnicodeDecodeError:
                print(f"使用编码 {enc} 读取失败，尝试下一种编码...")
                continue
        
        if not success:
            print("错误：无法解析CSV文件，请尝试手动指定编码")
            return
        
        print(f"成功读取CSV文件，共获取 {len(nac_to_point)} 条映射关系")
        
    except FileNotFoundError:
        print(f"错误：找不到CSV文件 {csv_file_path}")
        return
    except Exception as e:
        print(f"读取CSV文件时发生错误：{str(e)}")
        return
    
    # 获取文件夹中所有影像文件
    # 假设影像文件格式为常见的图片格式，可以根据需要修改
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.tif', '*.tiff']
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(images_dir, ext)))
    
    if not image_files:
        print(f"警告：在 {images_dir} 中未找到任何影像文件")
        return
    
    # 遍历影像文件并进行重命名
    renamed_count = 0
    skipped_count = 0
    
    for image_path in image_files:
        # 获取文件名（不含路径）
        image_filename = os.path.basename(image_path)
        
        # 查找文件名中包含的NAC_ID
        matched_nac = None
        for nac_id in nac_to_point.keys():
            if nac_id in image_filename:
                matched_nac = nac_id
                break
        
        if matched_nac:
            # 获取对应的点号
            point_number = nac_to_point[matched_nac]
            
            # 构建新文件名：pt_点号_原文件名
            new_filename = f"pt{point_number}_{image_filename}"
            new_filepath = os.path.join(images_dir, new_filename)
            
            # 执行重命名
            try:
                os.rename(image_path, new_filepath)
                print(f"已重命名: {image_filename} -> {new_filename}")
                renamed_count += 1
            except Exception as e:
                print(f"重命名 {image_filename} 时出错：{str(e)}")
                skipped_count += 1
        else:
            print(f"未找到匹配的NAC_ID，已跳过：{image_filename}")
            skipped_count += 1
    
    print(f"\n重命名完成！成功重命名 {renamed_count} 个文件，跳过 {skipped_count} 个文件")

if __name__ == "__main__":
    # 请根据实际情况修改以下路径
    csv_file = "/media/aerospace/long_8t_3/win25_检核/stere_20/dom/byte1/最新点号坐标_odd_even_imgs——总.csv"  # CSV文件路径
    images_folder = "/media/aerospace/long_8t_3/win25_检核/stere_20/dom/byte1/"  # 影像文件所在文件夹
    
    # 检查路径是否存在
    if not os.path.isfile(csv_file):
        print(f"错误：CSV文件 {csv_file} 不存在")
    elif not os.path.isdir(images_folder):
        print(f"错误：影像文件夹 {images_folder} 不存在")
    else:
        # 安装chardet库（如果尚未安装）
        try:
            import chardet
        except ImportError:
            print("正在安装chardet库...")
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", "chardet"])
        
        rename_images(csv_file, images_folder)

