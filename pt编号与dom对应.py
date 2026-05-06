import os
import csv
import glob
import shutil
import chardet

def detect_encoding(file_path):
    """检测文件编码"""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read(10000))
    return result['encoding']

def copy_rename_images(csv_file_path, images_dir):
    """
    方案2：同一NAC_ID对应多个点号 → 批量生成多个重命名文件（全保留，无丢失）
    复制重命名文件到新文件夹，原文件保留，含重复NAC_ID检测
    """
    # 自动创建新文件夹
    new_folder = os.path.join(images_dir, "重命名文件")
    try:
        os.makedirs(new_folder, exist_ok=True)
        print(f"✅ 成功创建/检测到重命名文件夹：{new_folder}")
    except Exception as e:
        print(f"❌ 创建重命名文件夹失败：{str(e)}")
        return

    # 🔥 核心修改：映射字典值为列表，存储同一NAC_ID的所有点号
    nac_to_points = {}  # 映射关系：NAC_ID → [点号1, 点号2, ...]
    try:
        # 编码检测
        encoding = detect_encoding(csv_file_path)
        print(f"检测到文件编码: {encoding}")
        encodings_to_try = [encoding] + ['utf-8', 'gbk', 'gb2312'] if encoding else ['utf-8', 'gbk', 'gb2312', 'iso-8859-1', 'cp1252']
        
        success = False
        for enc in encodings_to_try:
            try:
                with open(csv_file_path, 'r', encoding=enc) as csvfile:
                    print(f"成功使用编码 {enc} 打开文件")
                    reader = csv.reader(csvfile)
                    next(reader)  # 跳过表头
                    
                    for row_idx, row in enumerate(reader, 2):
                        if len(row) >= 8:
                            point_number = row[0].strip()
                            nac_id = row[5].strip()
                            # 跳过空的NAC_ID或点号
                            if not nac_id or not point_number:
                                print(f"警告：第{row_idx}行，NAC_ID/点号为空，已跳过")
                                continue
                            
                            # 🔥 核心：将点号追加到列表，不覆盖
                            if nac_id not in nac_to_points:
                                nac_to_points[nac_id] = [point_number]  # 首次出现，初始化列表
                            else:
                                if point_number not in nac_to_points[nac_id]:  # 避免同一NAC_ID重复添加相同点号
                                    nac_to_points[nac_id].append(point_number)
                                    print(f"ℹ️  发现多点点号：NAC_ID【{nac_id}】新增点号{point_number}，当前共{len(nac_to_points[nac_id])}个点号")
                        else:
                            print(f"警告：第{row_idx}行，列数不足（仅{len(row)}列），已跳过")
                
                success = True
                break
            except UnicodeDecodeError:
                print(f"编码 {enc} 读取失败，尝试下一种...")
                continue
        
        if not success:
            print("错误：无法解析CSV文件，请手动指定编码")
            return
        
        # 🔥 统计重复NAC_ID（点号数量>1的）
        dup_nac_count = sum(1 for nac, points in nac_to_points.items() if len(points) > 1)
        if dup_nac_count:
            print(f"\n========== 多点点号NAC_ID汇总（共{dup_nac_count}个）==========")
            for nac, points in nac_to_points.items():
                if len(points) > 1:
                    print(f"NAC_ID：{nac} → 对应所有点号：{points}（将生成{len(points)}个文件）")
            print("=====================================================")
        print(f"\n成功读取CSV，共获取 {len(nac_to_points)} 个唯一NAC_ID，其中{dup_nac_count}个对应多点点号")
        
    except FileNotFoundError:
        print(f"错误：找不到CSV文件 {csv_file_path}")
        return
    except Exception as e:
        print(f"读取CSV错误：{str(e)}")
        return
    
    # 获取所有影像文件
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.tif', '*.tiff']
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(images_dir, ext)))
    
    if not image_files:
        print(f"警告：{images_dir} 中未找到任何影像文件")
        return
    
    # 🔥 核心修改：遍历点号列表，批量生成重命名文件
    copied_count = 0
    skipped_count = 0
    multi_file_count = 0  # 统计多点点号生成的文件数
    
    for image_path in image_files:
        image_filename = os.path.basename(image_path)
        matched_nac = None
        for nac_id in nac_to_points.keys():
            if nac_id in image_filename:
                matched_nac = nac_id
                break
        
        if matched_nac:
            point_list = nac_to_points[matched_nac]
            # 一个NAC_ID对应多个点号，循环生成文件
            for point_number in point_list:
                new_filename = f"pt{point_number}_{image_filename}"
                new_filepath = os.path.join(new_folder, new_filename)
                try:
                    shutil.copy2(image_path, new_filepath)
                    print(f"已复制并重命名: {image_filename} -> {new_filename}")
                    copied_count += 1
                    if len(point_list) > 1:
                        multi_file_count += 1
                except Exception as e:
                    print(f"复制 {image_filename} 为{new_filename} 失败：{str(e)}")
                    skipped_count += 1
        else:
            print(f"未匹配NAC_ID，跳过：{image_filename}")
            skipped_count += 1
    
    # 最终统计
    print(f"\n✅ 复制重命名完成！")
    print(f"📊 统计结果：成功复制 {copied_count} 个（含{multi_file_count}个多点点号文件）| 跳过 {skipped_count} 个")
    print(f"📁 新文件保存路径：{new_folder}")
    print(f"⚠️  原文件已保留在：{images_dir}")
    if dup_nac_count:
        print(f"🔔 提示：{dup_nac_count}个NAC_ID对应多点点号，共生成{multi_file_count}个关联文件")

if __name__ == "__main__":
    # 请修改为你的实际路径
    csv_file = "/media/wang/pcie4y/校核20260201/图像/用的/极区.csv"
    images_folder = "/media/wang/pcie4y/校核20260201/图像/20m_byte"
    
    if not os.path.isfile(csv_file):
        print(f"错误：CSV文件 {csv_file} 不存在")
    elif not os.path.isdir(images_folder):
        print(f"错误：影像文件夹 {images_folder} 不存在")
    else:
        # 自动安装chardet
        try:
            import chardet
        except ImportError:
            print("正在安装chardet库...")
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", "chardet"])
        
        copy_rename_images(csv_file, images_folder)
