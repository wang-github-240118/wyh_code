from osgeo import gdal
import numpy as np
import time
import os
import math
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from scipy.spatial import KDTree
import pandas as pd


start = time.time()
font_path = r'C:\Windows\Fonts\STKAITI.TTF'  # 替换为你的字体文件路径
my_font = fm.FontProperties(fname=font_path)

# plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


def create_binary_image(input_path):
    """处理单个TIFF图像生成二值图像"""
    output_folder = os.path.join(os.path.dirname(input_path), 'binary_image')
    os.makedirs(output_folder, exist_ok=True)

    filename = os.path.basename(input_path)
    output_path = os.path.join(output_folder, filename.replace('.tif', '_binary_image.tif'))

    # 如果输出文件已存在则跳过处理
    if os.path.exists(output_path):
        return output_path

    dataset = gdal.Open(input_path)
    projection = dataset.GetProjection()
    geotransform = dataset.GetGeoTransform()
    band = dataset.GetRasterBand(1)
    image = band.ReadAsArray()

    # 获取 NoData 值
    no_data_value = band.GetNoDataValue()

    # 创建掩膜：标记 NoData 区域
    if no_data_value is not None:
        mask = (image == no_data_value)
    else:
        mask = np.zeros_like(image, dtype=bool)

    # 忽略 NoData 值并计算有效数据范围
    valid_data = image[~mask] if no_data_value is not None else image
    min_val = np.min(valid_data)
    max_val = np.max(valid_data)
    threshold = min_val + 0.18 * (max_val - min_val)
    # threshold = 0.001

    # 二值化处理（同时排除NoData区域）
    binary_image = np.where((~mask) & (image > threshold), 255, 1).astype(np.uint8)

    # 创建输出文件
    driver = gdal.GetDriverByName('GTiff')
    out_dataset = driver.Create(output_path, dataset.RasterXSize, dataset.RasterYSize, 1, gdal.GDT_Byte)
    out_dataset.SetProjection(projection)
    out_dataset.SetGeoTransform(geotransform)
    out_band = out_dataset.GetRasterBand(1)
    out_band.SetNoDataValue(0)  # 设置输出影像的 NoData 值为 0
    out_band.WriteArray(binary_image)
    out_band.FlushCache()
    out_dataset = None
    dataset = None

    return output_path


def xor(image1_path, image2_path, output_path):
    # 创建输出目录（如果不存在）
    output_folder = os.path.dirname(image1_path)
    os.makedirs(output_folder, exist_ok=True)

    # 打开输入图像
    image1 = gdal.Open(image1_path)
    image2 = gdal.Open(image2_path)

    # 检查图像尺寸是否一致
    if (image1.RasterXSize != image2.RasterXSize) or (image1.RasterYSize != image2.RasterYSize):
        print(f'图像1尺寸为{image1.RasterXSize} {image1.RasterYSize}')
        print(f'图像2尺寸为{image2.RasterXSize} {image2.RasterYSize}')
        print("错误：两幅图像尺寸不一致，请使用相同尺寸的图像。")
        return

    # 获取地理参考信息和投影
    geotransform = image1.GetGeoTransform()
    projection = image1.GetProjection()

    # 读取影像数据（假设是单波段二值图像）
    band1 = image1.GetRasterBand(1).ReadAsArray()
    band2 = image2.GetRasterBand(1).ReadAsArray()

    # 初始化输出图像（初始全0）
    outputimage = np.zeros(band1.shape, dtype=np.uint8)

    # 执行异或操作：
    # 相同位置像素值相同 -> 0
    # 图像1为0且图像2为1 -> 2（暗区失配）
    # 图像1为1且图像2为0 -> 1（亮区失配）
    outputimage[(band1 == band2)] = 0
    outputimage[(band1 == 1) & (band2 == 255)] = 2
    outputimage[(band1 == 255) & (band2 == 1)] = 1

    # 获取所有值为1或2的像素坐标
    y_coords, x_coords = np.where((outputimage == 1) | (outputimage == 2))
    coords = np.column_stack((x_coords, y_coords))  # 转换为 (x, y) 格式

    # 构建KD树（用于快速查找邻域）
    tree = KDTree(coords)

    # 查找每个像素的邻域（曼哈顿距离 ≤ √2，即8邻域）
    neighbors = tree.query_ball_point(coords, r=np.sqrt(2), p=np.inf)

    # 统计每个像素的相同值邻域数量
    same_neighbor_counts = np.zeros(len(coords), dtype=int)
    for i, neighbor_indices in enumerate(neighbors):
        # 统计邻域内相同值的像素数量（不包括自己）
        x, y = coords[i]
        val = outputimage[y, x]
        same_neighbor_counts[i] = sum(
            outputimage[coords[j][1], coords[j][0]] == val
            for j in neighbor_indices
            if j != i  # 排除自己
        )

    # 如果相同值邻域少于2个，则设为0
    for i, count in enumerate(same_neighbor_counts):
        if count < 2:
            y, x = coords[i][1], coords[i][0]
            outputimage[y, x] = 0

    # 创建输出图像文件
    driver = gdal.GetDriverByName('GTiff')
    output_image = driver.Create(output_path, outputimage.shape[1],
                                 outputimage.shape[0], 1, gdal.GDT_Byte)

    # 设置地理参考和投影信息
    output_image.SetGeoTransform(geotransform)
    output_image.SetProjection(projection)

    # 写入处理后的数据
    output_band = output_image.GetRasterBand(1)
    output_band.WriteArray(outputimage)

    # 创建颜色表
    colors = gdal.ColorTable()

    # 设置颜色 (R, G, B, Alpha)
    # 0值 - 绿色 (匹配区域)
    colors.SetColorEntry(0, (0, 255, 197, 255))
    # 1值 - 蓝色 (亮区失配)
    colors.SetColorEntry(1, (0, 112, 255, 255))
    # 2值 - 黄色 (暗区失配)
    colors.SetColorEntry(2, (230, 230, 0, 255))

    # 应用颜色表到输出波段
    output_band.SetRasterColorTable(colors)
    output_band.SetRasterColorInterpretation(gdal.GCI_PaletteIndex)

    # 设置无数据值为0（可选）
    # output_band.SetNoDataValue(0)

    output_image.FlushCache()  # 确保数据写入磁盘

    # 关闭文件释放资源
    output_image = None
    image1 = None
    image2 = None
    print(f"处理完成，结果已保存至：{output_path}")


def read_image(image_path):
    dataset = gdal.Open(image_path)
    if dataset is None:
        raise FileNotFoundError(f"无法打开文件 {image_path}")

    width = dataset.RasterXSize

    height = dataset.RasterYSize

    pixels = dataset.GetGeoTransform()[1]

    band = dataset.GetRasterBand(1)

    if band is None:
        raise ValueError(f"{image_path} 的波段数据无效或为空")
    image_data = band.ReadAsArray()

    return image_data, width, height, pixels


def get_line_intersections(image_data1, image_data2, width, height, start_x, start_y, end_x, end_y):
    line_segments = []
    current_gray_value = None
    segment_start = None
    gray_value1_start = gray_value2_start = None
    prev_x, prev_y = None, None

    # 使用 np.linspace 获取整数像素点
    num_steps = int(np.hypot(end_x - start_x, end_y - start_y))  # 步数 = 线段长度（像素）
    xs = np.linspace(start_x, end_x, num_steps).astype(int)
    ys = np.linspace(start_y, end_y, num_steps).astype(int)

    for x, y in zip(xs, ys):
        if 0 <= x < width and 0 <= y < height:
            gray_value1 = image_data1[y, x]
            gray_value2 = image_data2[y, x]

            if gray_value1 in [0, 1, 2]:
                if current_gray_value is None:
                    current_gray_value = gray_value1
                    segment_start = (x, y)
                    gray_value1_start = gray_value1
                    gray_value2_start = gray_value2
                    prev_x, prev_y = x, y
                elif gray_value1 != current_gray_value:
                    if prev_x is not None and prev_y is not None:
                        line_segments.append((
                            segment_start[0], segment_start[1],
                            prev_x, prev_y,
                            gray_value1_start, current_gray_value,
                            gray_value2_start, image_data2[prev_y, prev_x]
                        ))
                    current_gray_value = gray_value1
                    segment_start = (x, y)
                    gray_value1_start = gray_value1
                    gray_value2_start = gray_value2
                    prev_x, prev_y = x, y
                else:
                    prev_x, prev_y = x, y
            else:
                if current_gray_value is not None and prev_x is not None and prev_y is not None:
                    line_segments.append((
                        segment_start[0], segment_start[1],
                        prev_x, prev_y,
                        gray_value1_start, current_gray_value,
                        gray_value2_start, image_data2[prev_y, prev_x]
                    ))
                    current_gray_value = None
        else:
            if current_gray_value is not None and prev_x is not None and prev_y is not None:
                line_segments.append((
                    segment_start[0], segment_start[1],
                    prev_x, prev_y,
                    gray_value1_start, current_gray_value,
                    gray_value2_start, image_data2[prev_y, prev_x]
                ))
                current_gray_value = None

    # 最后一段
    if current_gray_value is not None and prev_x is not None and prev_y is not None:
        line_segments.append((
            segment_start[0], segment_start[1],
            prev_x, prev_y,
            gray_value1_start, current_gray_value,
            gray_value2_start, image_data2[prev_y, prev_x]
        ))

    return line_segments


def calculate_statistics(gray_values):
    stats = {}

    def calculate_trimmed_stats(lengths):
        if not lengths:
            return {
                "total_segments": 0,
                "max_length": 0,  # 改为0而不是None
                "min_length": 0,  # 改为0而不是None
                "mean_length": 0,  # 改为0而不是None
                "std_dev": 0,  # 改为0而不是None
                "3std_dev": 0  # 改为0而不是None
            }

        # Sort the lengths
        sorted_lengths = sorted(lengths)

        trimmed_lengths = sorted_lengths[2:-2] if len(sorted_lengths) > 20 else sorted_lengths

        if not trimmed_lengths:
            return {
                "total_segments": len(lengths),
                "max_length": max(lengths),
                "min_length": min(lengths),
                "mean_length": 0,  # 改为0而不是None
                "std_dev": 0,  # 改为0而不是None
                "3std_dev": 0  # 改为0而不是None
            }

        return {
            "total_segments": len(lengths),  # Original count before trimming
            "max_length": max(trimmed_lengths),
            "min_length": min(trimmed_lengths),
            "mean_length": np.mean(trimmed_lengths),
            "std_dev": np.std(trimmed_lengths),
            "3std_dev": 3 * np.std(trimmed_lengths)
        }

    for gray_value, lengths in gray_values.items():
        stats[gray_value] = calculate_trimmed_stats(lengths)

    # Calculate merged statistics with trimming
    merged_lengths = gray_values.get(1, []) + gray_values.get(2, [])
    stats['merged'] = calculate_trimmed_stats(merged_lengths)

    return stats


def shift_line(image_data1, image_data2, width, height, azimuth_angle, num_lines):
    k = math.tan(math.radians(azimuth_angle))  # 计算斜率k
    x_range = (0, width)
    y_range = (0, height)

    # 根据斜率k，确定截距的范围
    if k < 0:
        b_min = 0
        b_max = height - k * width
    else:
        b_min = -k * width
        b_max = height

    # 使用传入的num_lines生成等间隔的截距值
    b_values = np.linspace(b_min, b_max, num_lines)
    print(f'射线条数: {num_lines}')

    line_segments = []
    all_intersections = []  # 保存每条直线的交点信息

    for b_i in b_values:
        # 自动计算直线的起点和终点
        if k >= 0:
            # 起点
            if b_i >= 0:
                start_x, start_y = 0, b_i
            else:
                start_x, start_y = -b_i / k, 0

            # 终点
            if k * width + b_i <= height:
                end_x, end_y = width, k * width + b_i
            else:
                end_x, end_y = (height - b_i) / k, height
        else:
            # 当k为负时
            # 起点
            if b_i >= 0:
                start_x, start_y = max(0, (height - b_i) / k), min(b_i, height)
            else:
                start_x = (height - b_i) / k
                start_y = height

            # 终点
            end_y = k * width + b_i
            if end_y >= 0:
                end_x, end_y = width, end_y
            else:
                end_x = -b_i / k
                end_y = 0

        # 调用 get_line_intersections 函数，传递计算出的参数
        # intersections = get_line_intersections(image_data1, image_data2, width, height, k, b_i)
        intersections = get_line_intersections(
            image_data1, image_data2, width, height, k, b_i, end_x, end_y
        )
        # print(intersections)

        # 保存线段信息
        line_segments.append((start_x, start_y, end_x, end_y))
        all_intersections.append(intersections)

    return line_segments, all_intersections


def plot_lines(image_data2, line_segments, width, height):
    plt.figure(figsize=(10, 10))
    plt.imshow(image_data2, cmap='gray', extent=(0, width, 0, height))

    for start_x, start_y, end_x, end_y in line_segments:
        plt.plot([start_x, end_x], [start_y, end_y], color='yellow', lw=1)

    plt.title("Generated Parallel Lines")
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.gca().invert_yaxis()
    plt.show()


def bresenham_line(x1, y1, x2, y2):
    """Bresenham算法生成直线上的像素坐标"""
    points = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        points.append((x1, y1))
        if x1 == x2 and y1 == y2:
            break
        e2 = err * 2
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy
    return points


def trim_extremes(errors, n=1):
    if len(errors) <= 2 * n:
        raise ValueError("列表长度不足以剔除指定数量的极值")

    # 排序列表
    sorted_errors = sorted(errors)

    # 剔除最小的n个和最大的n个
    trimmed_list = sorted_errors[n:-n]

    return trimmed_list


def main(image_path1, image_path2, azimuth_angle, elevation_angle, output_file, sigma_threshold):
    """
    主函数，计算影像高程误差，输出统计报告和符合条件时绘制图像。

    参数：
        image_path1: str，第一幅影像路径
        image_path2: str，第二幅影像路径（DEM）
        azimuth_angle: float，方位角（度）
        elevation_angle: float，高程角（度）
        output_file: str，输出报告路径
        sigma_threshold: float，绘图时标准差阈值，默认10

    返回：
        sigma: float，整体高程误差标准差
        overall_mean_error: float，整体高程误差平均值
    """
    image_data1, width1, height1, pixel1 = read_image(image_path1)
    # print(width1)
    # print(height1)

    image_data2, width2, height2, pixel2 = read_image(image_path2)
    # print(width2)
    # print(height2)

    if (width1, height1) != (width2, height2):
        raise ValueError("两幅影像的尺寸不一致！")

    # num_lines = int(height1 / 2)
    num_lines = int(height1)
    line_segments, all_intersections = shift_line(image_data1, image_data2, width1, height1, azimuth_angle, num_lines)
    # print(all_intersections)
    # print(len(all_intersections))
    # plot_lines(image_data1, line_segments, width2, height2)

    report_dir = os.path.dirname(output_file)
    os.makedirs(report_dir, exist_ok=True)

    prefix = os.path.splitext(os.path.basename(image_path1))[0]
    detail_report_file = os.path.join(report_dir, f"{prefix}_高差报告.txt")

    hist_fig_path = os.path.join(report_dir, f"{prefix}_hist.png")
    abs_hist_fig_path = os.path.join(report_dir, f"{prefix}_abs_hist.png")
    box_fig_path = os.path.join(report_dir, f"{prefix}_boxplot.png")

    with open(output_file, 'w', encoding='utf-8') as file, open(detail_report_file, 'w', encoding='utf-8') as detail_file:
        gray_values = {0: [], 1: [], 2: []}
        elevation_errors_bright = []
        elevation_errors_dark = []
        total_elevation_errors = []

        for intersections in all_intersections:
            for start_x, start_y, end_x, end_y, gray_value1_start, _, gray_value2_start, gray_value2_end in intersections:
                points_on_line = bresenham_line(start_x, start_y, end_x, end_y)
                length = len(points_on_line)
                gray_values[gray_value1_start].append(length)

                if gray_value1_start == 1:
                    error = (length * pixel2 * math.tan(math.radians(elevation_angle))) - (
                            gray_value2_end - gray_value2_start)
                    elevation_errors_bright.append(error)
                    total_elevation_errors.append(error)
                elif gray_value1_start == 2:
                    error = -(length * pixel2 * math.tan(math.radians(elevation_angle))) + (
                            gray_value2_end - gray_value2_start)
                    elevation_errors_dark.append(error)
                    total_elevation_errors.append(error)
                elif gray_value1_start == 0:
                    error = 0
                    total_elevation_errors.append(error)  # 2025年12月17日
                detail_file.write(f"{error:.2f}\n")
        # 计算总线段条数
        total_segment_count = len(gray_values[0]) + len(gray_values[1]) + len(gray_values[2])
        # print(total_segment_count)

        # # 在报告中输出
        # file.write(f"总线段条数：{total_segment_count}\n")
        # file.write(f"光照未失配区域线段条数：{len(gray_values[0])}\n")
        # file.write(f"亮区失配区域线段条数：{len(gray_values[1])}\n")
        # file.write(f"暗区失配区域线段条数：{len(gray_values[2])}\n")
        # print(total_elevation_errors)

        def calc_rmse(errors):
            return np.sqrt(np.mean(np.square(errors))) if errors else 0

        bright_mean_error = np.mean(elevation_errors_bright) if elevation_errors_bright else 0
        bright_rmse = calc_rmse(elevation_errors_bright)
        dark_mean_error = np.mean(elevation_errors_dark) if elevation_errors_dark else 0
        dark_rmse = calc_rmse(elevation_errors_dark)
        overall_mean_error = np.sum(total_elevation_errors)/ total_segment_count if total_elevation_errors else 0
        overall_max_error = np.max(total_elevation_errors) if total_elevation_errors else 0
        overall_min_error = np.min(total_elevation_errors) if total_elevation_errors else 0
        overall_rmse = calc_rmse(total_elevation_errors)
        sum_squared_errors = np.sum((np.array(total_elevation_errors) - overall_mean_error) ** 2)
        sigma = np.sqrt(sum_squared_errors / total_segment_count)
        # sigma = np.std(total_elevation_errors)
        height_3sigma = 3 * sigma

        abs_errors = np.abs(total_elevation_errors)
        mean_abs_errors = np.mean(abs_errors)
        max_abs_errors = np.max(abs_errors)
        sigma_abs = np.std(abs_errors, ddof=1)
        three_sigma_abs = 3 * sigma_abs
        count_within_three_sigma = np.sum(abs_errors < three_sigma_abs)
        total_count = len(abs_errors)
        ratio_within_three_sigma = count_within_three_sigma / total_count if total_count > 0 else 0
        percentile_9974 = np.percentile(abs_errors, 99.74) if total_count > 0 else 0
        sorted_desc_errors = np.sort(abs_errors)[::-1] if total_count > 0 else np.array([])
        index_desc = np.searchsorted(-sorted_desc_errors, -percentile_9974, side='left') if total_count > 0 else 0
        count_within_three_sigma_height = np.sum(abs_errors < height_3sigma)
        ratio_within_three_sigma_height = count_within_three_sigma_height / total_count if total_count > 0 else 0
        index_desc_3sigma_height = np.searchsorted(-sorted_desc_errors, -height_3sigma,
                                                   side='left') if total_count > 0 else 0
        index_desc_3sigma = np.searchsorted(-sorted_desc_errors, -three_sigma_abs,
                                            side='left') if total_count > 0 else 0



        file.write("-------- 射线条数信息 --------\n")
        file.write(f"理论射线条数：{num_lines}\n")

        file.write("\n--------高程统计信息（单位：米）--------\n")
        file.write(f"整体高程误差平均值：{overall_mean_error:.2f}\n")
        file.write(f"整体高程误差RMSE：{overall_rmse:.2f}\n")
        file.write(f"整体高程误差最大值：{overall_max_error:.2f}\n")

        file.write(f"整体高程误差最小值：{overall_min_error:.2f}\n")
        file.write(f"整体高程误差σ值：{sigma:.2f}\n")
        file.write(f"整体高程误差σ值+均值：{sigma+abs(overall_mean_error):.2f}\n")
        file.write(f"整体高程误差3σ值+均值：{3*sigma+abs(overall_mean_error):.2f}\n")
        file.write(f"整体高程误差3σ值：{height_3sigma:.2f}\n")
        file.write(f"高度误差3σ在绝对值序列中的位置：{index_desc_3sigma_height + 1}\n")
        file.write(f"高度误差3σ在绝对值序列中的覆盖范围：{ratio_within_three_sigma_height:.4f}\n")

        file.write("\n--------高程绝对值信息统计（单位：米）--------\n")
        file.write(f"高程误差绝对值均值：{mean_abs_errors:.2f}\n")
        file.write(f"高程误差绝对值最大值：{max_abs_errors:.2f}\n")
        # file.write(f"高程误差绝对值σ值+均值：{sigma_abs + mean_abs_errors:.2f}\n")
        file.write(f"高程误差绝对值σ值：{sigma_abs:.2f}\n")
        file.write(f"高程误差绝对值3σ值：{three_sigma_abs:.2f}\n")
        file.write(f"高程误差绝对值RMSE：{overall_rmse:.2f}\n")
        file.write(f"高程误差绝对值3σ覆盖范围：{ratio_within_three_sigma:.4f}\n")
        file.write(f"高程误差绝对值3σ位置：{index_desc_3sigma + 1}\n")
        file.write(f"高程误差绝对值99.74%处高程值：{percentile_9974:.4f}\n")
        file.write(f"99.74%位置：{index_desc + 1}\n")

        stats = calculate_statistics(gray_values)
        file.write("\n--------不同失配区域的统计信息(单位：像素)--------\n")
        for gray_value, stat in stats.items():
            if gray_value == 0:
                file.write("光照未失配区域信息：\n")
            elif gray_value == 1:
                file.write("亮区失配区域信息：\n")
            elif gray_value == 2:
                file.write("暗区失配区域信息：\n")
            else:
                file.write("亮区和暗区失配区域信息合计：\n")

            file.write(f"    线段数量：{stat['total_segments']}\n")
            file.write(f"    最大长度：{stat['max_length']:.2f}\n")
            file.write(f"    最小长度：{stat['min_length']:.2f}\n")
            file.write(f"    平均长度：{stat['mean_length']:.2f}\n")
            file.write(f"    失配长度σ：{stat['std_dev']:.2f}\n")
            file.write(f"    失配长度3σ：{stat['3std_dev']:.2f}\n")
            file.write(f"    平均长度RMSE：{stat['std_dev']:.2f}\n")

        excel_path = os.path.join(report_dir, f"{prefix}_统计信息.xlsx")

        # 使用 stats 中的灰度1和2（亮、暗失配区域）统计值
        bright_stats = stats.get(1, {})
        dark_stats = stats.get(2, {})
        bright_count = bright_stats.get('total_segments', 0)
        dark_count = dark_stats.get('total_segments', 0)
        total_mismatch_count = bright_count + dark_count

        mismatch_mean_length = (
                                       bright_stats.get('mean_length', 0) * bright_count +
                                       dark_stats.get('mean_length', 0) * dark_count
                               ) / total_mismatch_count if total_mismatch_count else 0

        mismatch_rmse = (
                                bright_stats.get('std_dev', 0) * bright_count +
                                dark_stats.get('std_dev', 0) * dark_count
                        ) / total_mismatch_count if total_mismatch_count else 0

        mismatch_max_length = max(bright_stats.get('max_length', 0), dark_stats.get('max_length', 0))
        mismatch_3sigma = max(bright_stats.get('3std_dev', 0), dark_stats.get('3std_dev', 0))
        total_segments = sum(len(lengths) for lengths in gray_values.values())
        mismatch_mean_length_meters = mismatch_mean_length * pixel2
        mismatch_rmse_meters = mismatch_rmse * pixel2
        mismatch_max_length_meters = mismatch_max_length * pixel2
        mismatch_3sigma_meters = mismatch_3sigma * pixel2
        mismatch_segments = len(gray_values[1]) + len(gray_values[2])

        # 创建Excel数据
        excel_data = {
            '计算指标': [
                '射线数量',
                '线段总数',
                '失配线段数',
                '失配长度均值（米）',
                '失配长度RMSE（米）',
                '失配长度最大值（米）',
                '失配长度3σ值（米）',
                '整体高程误差σ值 + 均值',
                '整体高程误差3σ值 + 均值',
                '高程误差绝对值均值（米）',
                '高程误差绝对值σ（米）',
                '高程误差绝对值3σ（米）',
                '高程误差绝对值3σ覆盖范围',
                '高度误差均值（米）',
                '高程误差RMSE（米）',
                '高程误差σ值（米）',
                '高程误差3σ值（米）',
                '高程误差绝对值3σ位置',
                '99.74%位置',
                '高程误差绝对值99.74%处高程值（米）'
            ],
            '计算结果': [
                int(num_lines),
                int(total_segments),
                int(mismatch_segments),
                f"{mismatch_mean_length_meters:.2f}",  # 失配长度均值
                f"{mismatch_rmse_meters:.2f}",
                f"{mismatch_max_length_meters:.2f}",
                f"{mismatch_3sigma_meters:.2f}",  # 失配长度3sigam值
                f"{sigma + abs(overall_mean_error):.2f}",  # 整体高程误差σ值 + 均值
                f"{3 * sigma + abs(overall_mean_error):.2f}",
                f"{mean_abs_errors:.2f}",
                f"{sigma_abs:.2f}",
                f"{three_sigma_abs:.2f}",
                f"{ratio_within_three_sigma:.4f}",
                f"{overall_mean_error:.2f}",
                f"{overall_rmse:.2f}",
                f"{sigma:.2f}",
                f"{height_3sigma:.2f}",
                int(index_desc_3sigma + 1),
                int(index_desc + 1),
                f"{percentile_9974:.4f}"
            ]
        }

        # 创建DataFrame并保存到Excel
        df = pd.DataFrame(excel_data)
        df.to_excel(excel_path, index=False, engine='openpyxl')
        # 根据sigma阈值决定是否生成直方图和箱线图
        # if sigma < sigma_threshold:
        if sigma+abs(overall_mean_error) < sigma_threshold:
            errors = np.array(total_elevation_errors)

            # 高程误差分布直方图
            bins_middle = np.linspace(-100, 100, 11)
            bins = np.concatenate(([-np.inf], bins_middle, [np.inf]))
            counts, _ = np.histogram(errors, bins=bins)

            plt.figure(figsize=(10, 6))
            plt.bar(range(len(counts)), counts, width=0.8, align='center', color='skyblue', edgecolor='black')
            plt.xticks(
                ticks=range(len(counts)),
                labels=["< -100"] + [f"{bins_middle[i]:.2f}~{bins_middle[i + 1]:.2f}" for i in
                                     range(len(bins_middle) - 1)] + ["> 100"],
                rotation=45
            )
            plt.xlabel('高程误差 (米)', fontproperties=my_font)
            plt.ylabel('频数', fontproperties=my_font)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(hist_fig_path)
            plt.close()

        else:
            print(f"高程误差标准差+平均值 {sigma+abs(overall_mean_error):.2f} 超过阈值 {sigma_threshold}，不生成图表。")

    return sigma, overall_mean_error


# 使用示例：主循环中根据 main() 返回的 sigma 和 overall_mean_error 控制是否输出报告

threshold_sigma = 30  # 设置你希望的阈值
input_file = r'D:\桌面\sb\60m_low\henu'
# input_txt = os.path.join(input_file, 'Azimuth_Elevation_60m_low_log_use.txt')
input_txt = os.path.join(input_file, '不满足精度要求列表.txt')
report_folder = os.path.join(os.path.dirname(input_file), '极区精度评价报告_60m-henu_补充')
os.makedirs(report_folder, exist_ok=True)
failed_cases_path = os.path.join(report_folder, '不满足精度要求列表.txt')

with open(failed_cases_path, 'w', encoding='utf-8') as fail_file:
    with open(input_txt, 'r', encoding='utf-8') as file1:
        for line in file1:
            parts = line.strip().split()
            if len(parts) < 5:
                continue

            img1_orig = os.path.join(input_file, parts[0])
            img2_orig = os.path.join(input_file, parts[1])
            DEM = os.path.join(input_file, parts[2])
            azimuth_angle = float(parts[3])
            elevation_angle = float(parts[4])

            # 二值图像路径（可跳过或复用）
            image1_binary = create_binary_image(img1_orig)
            image2_binary = create_binary_image(img2_orig)

            # 输出XOR图像路径（可选）
            image_output = f"{parts[0].replace('.tif', '')}_{parts[1].replace('.tif', '')}_xor.tif"
            output_xor = os.path.join(input_file, 'binary_image', image_output)
            xor(image1_binary, image2_binary, output_xor)

            # 临时报告文件
            temp_report = os.path.join(report_folder, 'temp.txt')
            sigma, overall_mean_error = main(output_xor, DEM, azimuth_angle, elevation_angle, temp_report, threshold_sigma)

            if sigma + abs(overall_mean_error) < threshold_sigma:
                # 通过，保留报告
                output_report = os.path.join(report_folder, f"{parts[2].replace('.tif', '')}_精度评价报告.txt")
                os.rename(temp_report, output_report)
            else:
                # 不通过，写入失败列表，删除报告
                fail_file.write(line)
                os.remove(temp_report)

print(f"已完成，结果保存到：{report_folder}\n不满足的记录在：{failed_cases_path}")