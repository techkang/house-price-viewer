import os
import re
import json
from bs4 import BeautifulSoup

def _get_table_for_type(soup, property_type):
    """Finds the correct table based on property type ('new' or 'secondhand')."""
    all_tables = soup.find_all('table')
    if property_type == 'new':
        return all_tables[0] if len(all_tables) > 0 else None
    elif property_type == 'secondhand':
        return all_tables[1] if len(all_tables) > 1 else None
    return None

def _clean_text(text):
    """Cleans text by removing special spaces and stripping whitespace."""
    return text.replace('\u3000', '').replace(' ', '').strip()

def _is_valid_city_name(name):
    """Validates if a string from a cell is a likely city name."""
    cleaned_name = _clean_text(name)
    if not cleaned_name or len(cleaned_name) < 2 or len(cleaned_name) > 4:
        return False
    if cleaned_name.replace('.', '', 1).isdigit():
        return False
    if any(header in cleaned_name for header in ['城市', '环比', '同比', '定基', '平均', '上月', '上年']):
        return False
    return True

def _process_table_for_month(table, property_type, month, all_data):
    """Processes a single data table and updates the all_data dictionary."""
    rows = table.find_all('tr')
    for row in rows:
        cells = row.find_all('td')
        # A valid data row should have a specific structure, typically with 8 columns for 2 cities
        if not cells or len(cells) < 8:
            continue

        # Process the first city in the row (columns 0 and 1)
        city_1_raw = cells[0].get_text()
        if _is_valid_city_name(city_1_raw):
            city_1_cleaned = _clean_text(city_1_raw)
            index_1 = cells[1].get_text(strip=True)
            all_data.setdefault(city_1_cleaned, {}).setdefault(property_type, {})[month] = index_1

        # Process the second city in the row (columns 4 and 5)
        if len(cells) > 5:
            city_2_raw = cells[4].get_text()
            if _is_valid_city_name(city_2_raw):
                city_2_cleaned = _clean_text(city_2_raw)
                index_2 = cells[5].get_text(strip=True)
                all_data.setdefault(city_2_cleaned, {}).setdefault(property_type, {})[month] = index_2

def get_processed_months(all_data):
    """Gets a set of all months that have been processed."""
    processed = set()
    for city_data in all_data.values():
        for type_data in city_data.values():
            processed.update(type_data.keys())
    return processed

def append_new_data(stats_file="all_stats.json", html_dir="html_files"):
    """
    Checks for new HTML files and appends their data to the existing stats JSON file.
    """
    if not os.path.exists(stats_file):
        print(f"错误: '{stats_file}' 不存在。请先运行 'parse_stats.py' 生成初始数据文件。")
        return

    if not os.path.exists(html_dir):
        print(f"错误: 文件夹 '{html_dir}' 不存在。")
        return

    # 1. Load existing data
    with open(stats_file, 'r', encoding='utf-8') as f:
        all_data = json.load(f)

    # 2. Find processed and available files
    processed_months = get_processed_months(all_data)
    available_files = {f.replace('.html', '') for f in os.listdir(html_dir) if f.endswith('.html')}
    
    # 3. Determine new files to process
    new_months_to_process = sorted(list(available_files - processed_months))

    if not new_months_to_process:
        print("数据已是最新，无需更新。")
        return

    print(f"发现 {len(new_months_to_process)} 个新文件需要处理: {', '.join(new_months_to_process)}")

    # 4. Process new files
    for month in new_months_to_process:
        filename = f"{month}.html"
        filepath = os.path.join(html_dir, filename)
        print(f"正在处理: {filename}...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')

        # Process both tables for the new month
        new_homes_table = _get_table_for_type(soup, 'new')
        if new_homes_table:
            _process_table_for_month(new_homes_table, 'new', month, all_data)
            
        secondhand_homes_table = _get_table_for_type(soup, 'secondhand')
        if secondhand_homes_table:
            _process_table_for_month(secondhand_homes_table, 'secondhand', month, all_data)

    # 5. Save updated data
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

    print(f"\n成功处理了 {len(new_months_to_process)} 个新文件。")
    print(f"'{stats_file}' 已更新。")

if __name__ == "__main__":
    append_new_data() 