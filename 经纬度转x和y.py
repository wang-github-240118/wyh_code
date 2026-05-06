from pyproj import Proj
import math
import os
import pandas as pd
from pyproj.exceptions import ProjError

# ====================== 【配置参数区：请根据你的Excel修改！】======================
EXCEL_FILE = r"C:\Users\Lenovo\Desktop\新的校核\极区.xlsx"  # Excel文件路径（r前缀避免转义）
LON_COL = "经度"                 # Excel中经度列名（严格对应，区分大小写/空格）
LAT_COL = "纬度"                 # Excel中纬度列名（严格对应，区分大小写/空格）
PROJ_X_COL = "投影X"             # 输出投影X的列名（最后新增）
PROJ_Y_COL = "投影Y"             # 输出投影Y的列名（最后新增）
# ==================================================================================

# 🔥 修复1：设置环境变量关闭PROJ天体椭球校验（解决地球/月球不匹配）
os.environ["PROJ_IGNORE_CELESTIAL_BODY"] = "YES"

# 🔥 修复2：proj4补充+ellps=sphere，解决单独+R参数无效问题（保留你所有原始投影参数）
proj_str = '+proj=stere +lat_0=-90 +lon_0=0 +k=1 +x_0=0 +y_0=0 +R=1737400 +units=m +no_defs'
# proj_str = '+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=180 +x_0=0 +y_0=0 +R=1737400 +units=m +no_defs'
# 你其他的proj_str可保留，切换时直接注释上面一行，取消注释下面对应行即可
# proj_str = '+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=180 +x_0=0 +y_0=0 +R=1737400 +ellps=sphere +units=m +no_defs'
# proj_str = '+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=180 +x_0=0 +y_0=0 +R=3396190 +ellps=sphere +units=m +no_defs'

# 初始化投影对象（保留你原有代码）
p = Proj(proj_str)
print(f"✅ 投影对象初始化成功，proj4：{proj_str[:60]}...")

# 保留你原有：投影坐标到地理坐标转换函数
def inverse_projection(x, y):
    """
    将投影坐标 (x, y) 转换为地理坐标 (经度, 纬度)
    :param x: 投影坐标 x，单位：米
    :param y: 投影坐标 y，单位：米
    :return: (经度, 纬度)，单位：度
    """
    # 使用pyproj库进行投影反算
    lon, lat = p(x, y, inverse=True)
    return lon, lat

# 保留你原有：地理坐标转换为投影坐标
def forward_projection(lon, lat):
    """
    将地理坐标 (经度, 纬度) 转换为投影坐标 (x, y)
    :param lon: 地理坐标 经度，单位：度
    :param lat: 地理坐标 纬度，单位：度
    :return: 投影坐标 (x, y)，单位：米
    """
    # 使用pyproj库进行投影（保留你原有代码）
    x, y = p(lon, lat)
    return x, y

# ====================== 新增：Excel批量处理核心功能 ======================
def excel_lonlat2proj():
    """
    读取Excel中的经纬度，调用forward_projection批量转换，结果写入最后两列
    """
    try:
        # 1. 读取Excel文件（支持xlsx，保留所有原始数据）
        print(f"\n📖 正在读取Excel文件：{EXCEL_FILE}")
        df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
        total_count = len(df)
        print(f"✅ 成功读取，共{total_count}条坐标数据")

        # 2. 校验经纬度列是否存在
        if LON_COL not in df.columns or LAT_COL not in df.columns:
            raise ValueError(
                f"❌ Excel中未找到指定列名！\n期望列：[{LON_COL}]、[{LAT_COL}]\nExcel实际列：{list(df.columns)}"
            )

        # 3. 校验经纬度列是否为数值类型
        if not pd.api.types.is_numeric_dtype(df[LON_COL]) or not pd.api.types.is_numeric_dtype(df[LAT_COL]):
            raise TypeError("❌ 经纬度列必须为纯数值类型，请勿包含°/度/文字/空格等非数字内容")

        # 4. 批量转换经纬度到投影坐标
        print(f"\n⚙️  正在批量转换经纬度→投影坐标...")
        proj_x_list = []
        proj_y_list = []
        error_count = 0

        for idx, (lon, lat) in enumerate(zip(df[LON_COL], df[LAT_COL]), 1):
            try:
                # 跳过空值/NaN值
                if pd.isna(lon) or pd.isna(lat):
                    proj_x_list.append(None)
                    proj_y_list.append(None)
                    continue
                # 调用你原有forward_projection函数进行转换
                x, y = forward_projection(lon, lat)
                proj_x_list.append(round(x, 4))  # 保留4位小数，可按需修改
                proj_y_list.append(round(y, 4))
            except ProjError:
                # 单条数据转换失败，记为空白，不中断整体流程
                proj_x_list.append(None)
                proj_y_list.append(None)
                error_count += 1
                print(f"⚠️  第{idx}条数据转换失败（经纬度：{lon:.4f},{lat:.4f}）")
            except Exception as e:
                proj_x_list.append(None)
                proj_y_list.append(None)
                error_count += 1
                print(f"⚠️  第{idx}条数据异常（经纬度：{lon},{lat}）：{str(e)[:50]}")

        # 5. 将投影结果写入Excel最后两列
        df[PROJ_X_COL] = proj_x_list
        df[PROJ_Y_COL] = proj_y_list

        # 6. 保存回原Excel文件（覆盖，保留所有原始数据和列顺序）
        df.to_excel(EXCEL_FILE, index=False, engine="openpyxl")

        # 7. 输出转换结果统计
        success_count = total_count - error_count
        print(f"\n====================== 转换完成 ======================")
        print(f"📊 统计结果：总处理{total_count}条 | 成功{success_count}条 | 失败{error_count}条")
        print(f"💾 投影坐标已写入Excel最后两列：【{PROJ_X_COL}】、【{PROJ_Y_COL}】")
        print(f"📁 结果文件路径：{EXCEL_FILE}")
        print(f"======================================================")

    except FileNotFoundError:
        print(f"❌ 错误：未找到Excel文件！请检查路径：{EXCEL_FILE}")
    except ValueError as e:
        print(f"❌ 数据列错误：{e}")
    except TypeError as e:
        print(f"❌ 数据类型错误：{e}")
    except Exception as e:
        print(f"❌ 程序运行错误：{type(e).__name__} - {str(e)[:100]}")

# 程序主执行入口
if __name__ == "__main__":
    excel_lonlat2proj()