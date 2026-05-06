def process_text_file(input_file, output_file=None):
    """
    处理文本文件，从第一行开始，将每三行汇总到一行

    参数:
        input_file: 输入的txt文件路径
        output_file: 输出的txt文件路径，若为None则不保存到文件
    """
    try:
        # 读取文件内容
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            print("文件为空或不包含有效内容")
            return

        # 处理内容，从第一行开始
        result = []
        total_lines = len(lines)

        # 每三行一组进行处理
        for i in range(0, total_lines, 3):
            # 获取当前组的三行（可能不足三行）
            group = lines[i:i + 3]

            # 如果组内至少有一行
            if len(group) >= 1:
                # 第一部分保留完整内容
                part1 = group[0].strip().replace(':', '').replace('_large.tif', '_small.tif')
                part4 = group[0].strip().replace('_cropped_dem_cropped_large.tif:', '_cropped_cropped.tif')
                #part5 = group[0].strip().replace('_cropped_dem_cropped_large.tif:', '_cropped_cropped.tif')

                # 第二部分取等号后面的数字（如果存在）
                part2 = ""
                if len(group) >= 2 and '=' in group[1]:
                    part2 = group[1].split('=', 1)[1].strip()

                # 第三部分取等号后面的数字（如果存在）
                part3 = ""
                if len(group) >= 3 and '=' in group[2]:
                    part3 = group[2].split('=', 1)[1].strip()

                # 组合成一行，用逗号分隔
                combined = f"{part4} shadow_{part1} {part1} {part2} {90 - float(part3)}"
                result.append(combined)

        # 输出结果
        print("处理后的内容：")
        for line in result:
            print(line)

        # 如果指定了输出文件，则保存结果
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(result))
            print(f"\n结果已保存到 {output_file}")

        return result

    except FileNotFoundError:
        print(f"错误：找不到文件 {input_file}")
    except Exception as e:
        print(f"处理文件时发生错误：{str(e)}")


if __name__ == "__main__":
    # 示例用法
    input_filename = r"D:\桌面\sb\Azimuth_Elevation_5m_log.txt"  # 输入文件名
    output_filename = r"D:\桌面\sb\Azimuth_Elevation_5m_log_use.txt"  # 输出文件名

    # 处理文件
    process_text_file(input_filename, output_filename)
