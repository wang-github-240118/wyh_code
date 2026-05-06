a = r'C:\Users\Lenovo\Desktop\着陆区和长航程\2026试到航\24号两家一起\tif.lis'
b = r'C:\Users\Lenovo\Desktop\着陆区和长航程\2026试到航\24号两家一起\tif——all.txt'
with open(a, 'r') as file1, open(b, 'w',encoding='utf-8') as file2:
    for line in file1:
        NAC = line.strip()
        Shadow = line.strip().replace('_cropped_cropped.tif', '_cropped_dem_cropped_small.tif')  # shadow名字
        Shadow_hkpu = Shadow.replace('_dem_cropped_small.tif', '_cropped_dem_cropped_small_hkpu.tif')  # shadow名字
        NAC_binary_image = line.strip().replace('.tif', '_binary_image.tif')
        NAC_binary_image_hkpu = Shadow_hkpu.replace('_hkpu.tif', '_binary_image_hkpu.tif')
        Shadow_binary_image = Shadow.replace('.tif', '_binary_image.tif')
        XOR = line.strip().replace('.tif', '')
        xor2 = Shadow_binary_image.replace('_binary_image.tif', '_xor.tif')
        xor2_hkpu = Shadow_binary_image.replace('_binary_image.tif', '_xor_hkpu.tif')
        EXCEL = f'{XOR}_shadow_{xor2.replace(".tif", "_统计信息.xlsx")}'
        EXCEL_hkpu = f'{XOR}_shadow_{xor2.replace(".tif", "_统计信息_hkpu.xlsx")}'
        file2.write(f'{NAC} shadow_{Shadow} shadow_{Shadow_hkpu} {NAC_binary_image} shadow_{Shadow_binary_image} {NAC_binary_image_hkpu} {XOR}_shadow_{xor2} {XOR}_shadow_{xor2_hkpu} {EXCEL} {EXCEL_hkpu}\n')