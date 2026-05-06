# 定义文件路径（保留原路径，原始字符串r避免转义）
a = r'D:\桌面\sb\nac\tif.lis'
b = r'D:\桌面\sb\nac\tif——all.txt'

# 核心步骤1：读取tif.lis所有内容，清洗空行和首尾空格
with open(a, 'r', encoding='gbk') as file1:  # 适配CMD生成的tif.lis默认编码，避免乱码
    # 读取所有行，strip()去除首尾空格/换行，过滤空行
    all_lines = [line.strip() for line in file1 if line.strip()]

# 核心步骤2：定义排序函数，提取pt后纯数字作为排序依据（数值排序）
def get_pt_number(filename):
    """从文件名中提取pt后的纯数字，返回整数用于排序"""
    # 分割出pt后的部分（如pt100_dom... → 100_dom...）
    after_pt = filename.split('pt')[1]
    # 分割出_前的纯数字部分（如100_dom... → 100），转整数实现数值排序
    pt_num = after_pt.split('_')[0]
    return int(pt_num)

# 核心步骤3：按pt后数字从小到大排序（key指定排序依据，reverse=False升序）
sorted_lines = sorted(all_lines, key=get_pt_number, reverse=False)

# 核心步骤4：遍历排序后的列表，执行原有写入逻辑（完全保留原功能）
with open(b, 'w', encoding='utf-8') as file2:
    for line in sorted_lines:
        NAC = line.strip()
        # 原有Shadow文件名生成逻辑
        Shadow = line.strip().replace('_cropped_cropped.tif', '_cropped_dem_cropped_small.tif').replace('pt', 'shadow_pt')
        # 原有各类衍生文件名生成逻辑
        NAC_binary_image = line.strip().replace('.tif', '_binary_image.tif')
        Shadow_binary_image = Shadow.replace('.tif', '_binary_image.tif')
        XOR = line.strip().replace('.tif', '')
        xor2 = Shadow_binary_image.replace('_binary_image.tif', '_xor.tif')
        EXCEL = f'{XOR}_{xor2.replace(".tif", "_统计信息.xlsx")}'
        # 原有写入格式（各字段空格分隔，换行）
        file2.write(f'{NAC} {Shadow} {Shadow.replace(".tif","_hkpu.tif")} {NAC_binary_image} {Shadow_binary_image} {Shadow_binary_image.replace(".tif","_hkpu.tif")} {XOR}_{xor2} {XOR}_{xor2.replace(".tif","_hkpu.tif")} {EXCEL} {EXCEL.replace(".xlsx","_hkpu.xlsx")}\n')

print("处理完成！已按pt编号从小到大排序，并生成tif——all.txt")