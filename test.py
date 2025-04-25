from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import pandas as pd
import numpy as np

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36"
)
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
wait = WebDriverWait(driver, 30)

stat_urls = {
    'standard': 'https://fbref.com/en/comps/9/stats/Premier-League-Stats',
    'goalkeeping': 'https://fbref.com/en/comps/9/keepers/Premier-League-Stats',
    'shooting': 'https://fbref.com/en/comps/9/shooting/Premier-League-Stats',
    'passing': 'https://fbref.com/en/comps/9/passing/Premier-League-Stats',
    'passing_types': 'https://fbref.com/en/comps/9/passing_types/Premier-League-Stats',
    'gca': 'https://fbref.com/en/comps/9/gca/Premier-League-Stats',
    'defense': 'https://fbref.com/en/comps/9/defense/Premier-League-Stats',
    'possession': 'https://fbref.com/en/comps/9/possession/Premier-League-Stats',
    'misc': 'https://fbref.com/en/comps/9/misc/Premier-League-Stats'
}
all_player_data = {}

# Hàm chuyển đổi giá trị thành số
def convert_to_numeric(value):
    if value is None or value.strip() in ('', '-'):
        return "N/a"
    clean_value = value.strip().replace('%', '').replace(',', '')
    if "N/a" in clean_value or "N/A" in clean_value:
        return "N/a"
    try:
        return float(clean_value)
    except ValueError:
        return value.strip()

# Hàm trích xuất dữ liệu từ bảng
def extract_table_data(soup, table_id, is_goalkeeping=False):
    table = soup.find('table', {'id': table_id})
    if not table:
        print(f"Không tìm thấy bảng với ID: {table_id}")
        return []
    players_data = []
    na_count = 0  # Đếm số ô trống được thay thế
    try:
        tbody = table.find('tbody')
        if not tbody:
            print(f"Không tìm thấy tbody trong bảng {table_id}")
            return []
        rows = tbody.find_all('tr')
        print(f"Tìm thấy {len(rows)} hàng trong bảng {table_id}")
        for row in rows:
            if 'class' in row.attrs and any(cls in row.attrs['class'] for cls in ['thead', 'spacer']):
                continue
            name_col = row.find('th', {'data-stat': 'player'}) or row.find('td', {'data-stat': 'player'})
            if not name_col or not name_col.text.strip():
                print("Bỏ qua hàng: Không tìm thấy cột 'player'")
                continue
            qualified_player = True
            if not is_goalkeeping:  # Chỉ áp dụng lọc phút cho danh mục không phải thủ môn
                minutes_col = row.find('td', {'data-stat': 'minutes'})
                if minutes_col:
                    minutes_text = minutes_col.text.strip()
                    if minutes_text in ('-', ''):
                        qualified_player = False
                    else:
                        try:
                            minutes = int(minutes_text.replace(',', ''))
                            if minutes <= 90:
                                qualified_player = False
                        except ValueError:
                            qualified_player = False
            if qualified_player:
                player_info = {'player': name_col.text.strip()}
                player_link = name_col.find('a')
                if player_link:
                    player_info['player_url'] = player_link.get('href')
                for stat in row.find_all(['th', 'td']):
                    stat_name = stat.get('data-stat')
                    if stat_name and stat_name != 'player':
                        value = stat.text if stat.text else None
                        converted_value = convert_to_numeric(value)
                        if converted_value == "N/a":
                            na_count += 1
                        player_info[stat_name] = converted_value
                players_data.append(player_info)
    except Exception as e:
        print(f"Lỗi khi xử lý bảng {table_id}: {e}")
    return players_data

# Hàm hợp nhất dữ liệu
def merge_player_data(all_data):
    merged_data = {}
    player_teams = {}
    goalkeepers = set()  # Tập hợp các thủ môn
    
    # Xử lý dữ liệu từ bảng standard trước
    if 'standard' in all_data and all_data['standard']:
        for player in all_data['standard']:
            player_name = player['player']
            if 'team' in player:
                player_teams[player_name] = player['team']
            if player_name not in merged_data:
                merged_data[player_name] = {'Player': player_name}
            for stat, value in player.items():
                if stat != 'player' and stat != 'player_url':
                    merged_data[player_name][f"standard_{stat}"] = value
            if 'player_url' in player:
                merged_data[player_name]['player_url'] = player['player_url']
    
    # Xử lý riêng bảng goalkeeping để xác định thủ môn
    if 'goalkeeping' in all_data and all_data['goalkeeping']:
        for player in all_data['goalkeeping']:
            player_name = player['player']
            goalkeepers.add(player_name)  # Đánh dấu là thủ môn
            if player_name not in merged_data:
                merged_data[player_name] = {'Player': player_name}
                if 'team' in player:
                    player_teams[player_name] = player['team']
                    merged_data[player_name]['standard_team'] = player['team']
            if player_name in player_teams and 'standard_team' not in merged_data[player_name]:
                merged_data[player_name]['standard_team'] = player_teams[player_name]
            for stat, value in player.items():
                if stat != 'player' and stat != 'player_url':
                    merged_data[player_name][f"goalkeeping_{stat}"] = value
            if 'player_url' in player and 'player_url' not in merged_data[player_name]:
                merged_data[player_name]['player_url'] = player['player_url']
    
    # Xử lý các danh mục còn lại
    for category, players in all_data.items():
        if category in ['standard', 'goalkeeping']:
            continue
        for player in players:
            player_name = player['player']
            if player_name not in merged_data:
                merged_data[player_name] = {'Player': player_name}
                if 'team' in player:
                    player_teams[player_name] = player['team']
                    merged_data[player_name]['standard_team'] = player['team']
            if player_name in player_teams and 'standard_team' not in merged_data[player_name]:
                merged_data[player_name]['standard_team'] = player_teams[player_name]
            for stat, value in player.items():
                if stat != 'player' and stat != 'player_url':
                    merged_data[player_name][f"{category}_{stat}"] = value
            if 'player_url' in player and 'player_url' not in merged_data[player_name]:
                merged_data[player_name]['player_url'] = player['player_url']
    
    # Đảm bảo các cầu thủ không phải thủ môn có các cột goalkeeping là "N/a"
    goalkeeping_stats = [
        'goalkeeping_gk_goals_against_per90',
        'goalkeeping_gk_save_pct',
        'goalkeeping_gk_clean_sheets_pct',
        'goalkeeping_gk_pens_save_pct'
    ]
    for player_name, player_data in merged_data.items():
        if player_name not in goalkeepers:  # Nếu không phải thủ môn
            for stat in goalkeeping_stats:
                if stat not in player_data:
                    player_data[stat] = "N/a"

    return merged_data

table_ids = {
    'standard': 'stats_standard',
    'goalkeeping': 'stats_keeper',
    'shooting': 'stats_shooting',
    'passing': 'stats_passing',
    'passing_types': 'stats_passing_types',
    'gca': 'stats_gca',
    'defense': 'stats_defense',
    'possession': 'stats_possession',
    'misc': 'stats_misc'
}

try:
    # Truy cập và trích xuất dữ liệu từ từng trang thống kê
    for category, url in stat_urls.items():
        print(f"\nĐang truy cập trang {category}...")
        driver.get(url)
        table_id = table_ids[category]
        for attempt in range(3):  # Thử lại tối đa 3 lần
            try:
                wait.until(EC.presence_of_element_located((By.ID, table_id)))
                print(f"Đã tải bảng {table_id} thành công")
                break
            except TimeoutException:
                print(f"Thử {attempt + 1}/3: Hết thời gian chờ tải bảng {table_id}")
                if attempt == 2:
                    print("Không thể tải bảng, lưu HTML để kiểm tra")
                    with open(f'{category}_page.html', 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    print(f"Đã lưu HTML của trang {category} vào '{category}_page.html'")
                time.sleep(2)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        is_goalkeeping = (category == 'goalkeeping')
        players_data = extract_table_data(soup, table_id, is_goalkeeping)
        if players_data:
            all_player_data[category] = players_data
            print(f"Đã tìm thấy {len(players_data)} cầu thủ đủ điều kiện trong bảng {category}")
        else:
            print(f"Không tìm thấy dữ liệu cầu thủ nào trong bảng {category}")
    
    print("\nĐang gộp dữ liệu từ tất cả các bảng...")
    merged_player_data = merge_player_data(all_player_data)
    print(f"Đã gộp dữ liệu cho {len(merged_player_data)} cầu thủ")

    if not merged_player_data:
        print("Không có dữ liệu cầu thủ nào được tìm thấy!")
        exit(1)

    df = pd.DataFrame.from_dict(merged_player_data, orient='index')
    
    # Định nghĩa cột bắt buộc để xác định cầu thủ hợp lệ
    required_columns = ['standard_team', 'standard_position', 'standard_age', 'standard_minutes']
    
    # Lọc cầu thủ có đầy đủ thông tin cơ bản
    valid_players = df.copy()
    for col in required_columns:
        if col in valid_players.columns:
            valid_players = valid_players[valid_players[col].notnull() & (valid_players[col] != 'N/a')]
    
    print(f"Sau khi lọc: còn lại {len(valid_players)} cầu thủ đủ điều kiện")
    
    column_mapping = {
        'standard_nationality': 'Nation',
        'standard_team': 'Team',
        'standard_position': 'Pos',
        'standard_age': 'Age',
        'standard_games': 'MP',
        'standard_games_starts': 'Starts',
        'standard_minutes': 'Min',
        'standard_goals': 'Goals',
        'standard_assists': 'Assists',
        'standard_cards_yellow': 'Yellow_Card',
        'standard_cards_red': 'Red_Card',
        'standard_xg': 'stand_xG',
        'standard_xg_assist': 'xAG',
        'standard_progressive_carries': 'PrgC',
        'standard_progressive_passes': 'PrgP',
        'standard_progressive_passes_received': 'PrgR',
        'standard_goals_per90': 'Gls',
        'standard_assists_per90': 'Ast',
        'standard_xg_per90': 'xG',
        'standard_xg_assist_per90': 'xGA',

        'goalkeeping_gk_goals_against_per90': 'GA90',
        'goalkeeping_gk_save_pct': 'Save%',
        'goalkeeping_gk_clean_sheets_pct': 'CS%',
        'goalkeeping_gk_pens_save_pct': 'PKsv%',

        'shooting_shots_on_target_pct': 'SoT%',
        'shooting_shots_on_target_per90': 'SoT/90',
        'shooting_goals_per_shot': 'G/Sh',
        'shooting_average_shot_distance': 'Dist',

        'passing_passes': 'Cmp',
        'passing_passes_pct': 'Cmp%',
        'passing_passes_total_distance': 'TotDist',
        'passing_passes_pct_short': 'Short_Cmp%',
        'passing_passes_pct_medium': 'Medium_Cmp%',
        'passing_assisted_shots': 'KP',
        'passing_passes_into_final_third': '1/3',
        'passing_passes_into_penalty_area': 'PPA',
        'passing_crosses_into_penalty_area': 'CrsPA',
        'passing_progressive_passes': 'PrgP_passing',

        'gca_sca': 'SCA',
        'gca_sca_per90': 'SCA90',
        'gca_gca': 'GCA',
        'gca_gca_per90': 'GCA90',

        'defense_tackles': 'Tkl',
        'defense_tackles_won': 'TklW',
        'defense_challenges': 'Att',
        'defense_dribbles_tackles_pct': 'Lost',
        'defense_blocks': 'Blocks',
        'defense_blocked_shots': 'Sh',
        'defense_blocked_passes': 'Pass',
        'defense_interceptions': 'Int',

        'possession_touches': 'Touches',
        'possession_touches_def_pen_area': 'Def_Pen',
        'possession_touches_def_3rd': 'Def_3rd',
        'possession_touches_mid_3rd': 'Mid_3rd',
        'possession_touches_att_3rd': 'Att_3rd',
        'possession_touches_att_pen_area': 'Att_Pen',
        'possession_take_ons': 'Att_take_ons',
        'possession_take_ons_won_pct': 'Succ%',
        'possession_take_ons_tackled_pct': 'Tkld%',
        'possession_carries': 'Carries',
        'possession_carries_progressive_distance': 'ProDist',
        'possession_progressive_carries': 'ProgC',
        'possession_carries_into_final_third': '1/3_carries',
        'possession_carries_into_penalty_area': 'CPA',
        'possession_miscontrols': 'Mis',
        'possession_dispossessed': 'Dis',
        'possession_passes_received': 'Rec',
        'possession_progressive_passes_received': 'PrgR_possession',

        'misc_fouls': 'Fls',
        'misc_fouled': 'Fld',
        'misc_offsides': 'Off',
        'misc_crosses': 'Crs',
        'misc_ball_recoveries': 'Recov',
        'misc_aerials_won': 'Won',
        'misc_aerials_lost': 'Lost',
        'misc_aerials_won_pct': 'Won%'
    }
    
    final_columns = {}
    if 'Player' in valid_players.columns:
        final_columns['Player'] = valid_players['Player']
    for old_col, new_col in column_mapping.items():
        if old_col in valid_players.columns:
            final_columns[new_col] = valid_players[old_col]
        else:
            final_columns[new_col] = pd.Series(['N/a'] * len(valid_players), index=valid_players.index)
    
    final_df = pd.DataFrame(final_columns)
    final_df = final_df.sort_values(by='Player')
    
    # Thêm cột đếm dữ liệu có sẵn
    available_data_counts = (final_df != 'N/a').sum(axis=1)
    final_df['Available_Data_Count'] = available_data_counts
    
    # Lọc bỏ cầu thủ không có đủ dữ liệu cần thiết
    # Loại bỏ những dòng có các giá trị trống trong cột tiêu đề chính
    critical_cols = ['Player', 'Team', 'Pos', 'Age', 'MP', 'Starts', 'Min']
    final_df_filtered = final_df.copy()
    
    for col in critical_cols:
        if col in final_df_filtered.columns:
            final_df_filtered = final_df_filtered[final_df_filtered[col].notnull() & 
                                                 (final_df_filtered[col] != '') & 
                                                 (final_df_filtered[col] != 'N/a')]
    
    print(f"Sau khi lọc các cột quan trọng: còn lại {len(final_df_filtered)} cầu thủ")
    
    final_df_filtered.to_csv('results_filtered.csv', index=False, encoding='utf-8-sig')
    final_df.to_csv('results_all.csv', index=False, encoding='utf-8-sig')

    data_completeness = ((final_df_filtered != 'N/a').sum().sum() / (len(final_df_filtered) * (len(final_df_filtered.columns) - 1)) * 100)
    print(f"Tỷ lệ dữ liệu đầy đủ trong tập dữ liệu đã lọc: {data_completeness:.2f}%")
    
except Exception as e:
    print(f"\nĐã xảy ra lỗi: {e}")
finally:
    driver.quit()
    print("\nĐã đóng trình điều khiển webdriver.")