from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
wait = WebDriverWait(driver, 30)

stat_configs = {
    'standard': {'url': 'https://fbref.com/en/comps/9/stats/Premier-League-Stats', 'table_id': 'stats_standard'},
    'goalkeeping': {'url': 'https://fbref.com/en/comps/9/keepers/Premier-League-Stats', 'table_id': 'stats_keeper'},
    'shooting': {'url': 'https://fbref.com/en/comps/9/shooting/Premier-League-Stats', 'table_id': 'stats_shooting'},
    'passing': {'url': 'https://fbref.com/en/comps/9/passing/Premier-League-Stats', 'table_id': 'stats_passing'},
    'gca': {'url': 'https://fbref.com/en/comps/9/gca/Premier-League-Stats', 'table_id': 'stats_gca'},
    'defense': {'url': 'https://fbref.com/en/comps/9/defense/Premier-League-Stats', 'table_id': 'stats_defense'},
    'possession': {'url': 'https://fbref.com/en/comps/9/possession/Premier-League-Stats', 'table_id': 'stats_possession'},
    'misc': {'url': 'https://fbref.com/en/comps/9/misc/Premier-League-Stats', 'table_id': 'stats_misc'}
}
def convert_to_numeric(value):
    if not value or value.strip() in ('', '-', 'N/a', 'N/A'):
        return "N/a"
    clean_value = value.strip().replace('%', '').replace(',', '')
    try:
        return float(clean_value)
    except ValueError:
        return value.strip()

def extract_table_data(soup, table_id, is_goalkeeping=False):
    table = soup.find('table', id=table_id)
    if not table:
        print(f"Không tìm thấy bảng {table_id}")
        return []
    players_data = []
    for row in table.find('tbody').find_all('tr'):
        if 'class' in row.attrs and any(cls in row.attrs['class'] for cls in ['thead', 'spacer']):
            continue
        name_col = row.find('th', {'data-stat': 'player'}) or row.find('td', {'data-stat': 'player'})
        if not name_col or not name_col.text.strip():
            continue
        qualified_player = True
        minutes_col = row.find('td', {'data-stat': 'minutes'})
        if minutes_col and minutes_col.text.strip():
            try:
                minutes = int(minutes_col.text.replace(',', ''))
                qualified_player = minutes > 90
            except ValueError:
                qualified_player = False
        if qualified_player:
            player_info = {'player': name_col.text.strip()}
            if link := name_col.find('a'):
                player_info['player_url'] = link.get('href')
            for stat in row.find_all(['th', 'td']):
                if stat_name := stat.get('data-stat'):
                    if stat_name != 'player':
                        player_info[stat_name] = convert_to_numeric(stat.text)
            players_data.append(player_info)
    return players_data

def merge_player_data(all_data):
    merged_data = {}
    player_teams = {}
    goalkeepers = set()
    for player in all_data.get('standard', []):
        name = player['player']
        merged_data[name] = {'Player': name, 'player_url': player.get('player_url')}
        player_teams[name] = player.get('team')
        for stat, value in player.items():
            if stat not in ['player', 'player_url']:
                merged_data[name][f"standard_{stat}"] = value
    for player in all_data.get('goalkeeping', []):
        name = player['player']
        goalkeepers.add(name)
        if name not in merged_data:
            merged_data[name] = {'Player': name}
        merged_data[name].update({'player_url': player.get('player_url'), 'standard_team': player.get('team') or player_teams.get(name)})
        for stat, value in player.items():
            if stat not in ['player', 'player_url']:
                merged_data[name][f"goalkeeping_{stat}"] = value
    for category, players in all_data.items():
        if category in ['standard', 'goalkeeping']:
            continue
        for player in players:
            name = player['player']
            if name not in merged_data:
                merged_data[name] = {'Player': name}
            merged_data[name].update({'player_url': player.get('player_url'), 'standard_team': player.get('team') or player_teams.get(name)})
            for stat, value in player.items():
                if stat not in ['player', 'player_url']:
                    merged_data[name][f"{category}_{stat}"] = value
    for player_data in merged_data.values():
        if player_data['Player'] not in goalkeepers:
            for stat in ['goalkeeping_gk_goals_against_per90', 'goalkeeping_gk_save_pct', 
                         'goalkeeping_gk_clean_sheets_pct', 'goalkeeping_gk_pens_save_pct']:
                player_data.setdefault(stat, "N/a")
    return merged_data
all_player_data = {}
try:
    for category, config in stat_configs.items():
        print(f"\nĐang truy cập trang {category}...")
        driver.get(config['url'])
        for attempt in range(3):
            try:
                wait.until(EC.presence_of_element_located((By.ID, config['table_id'])))
                print(f"Đã tải bảng {config['table_id']} thành công")
                break
            except TimeoutException:
                print(f"Thử {attempt + 1}/3: Hết thời gian chờ tải bảng {config['table_id']}")
                if attempt == 2:
                    with open(f'{category}_page.html', 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        players_data = extract_table_data(soup, config['table_id'])
        all_player_data[category] = players_data or []
        print(f"Thu thập được {len(players_data)} cầu thủ từ {category}")
    merged_data = merge_player_data(all_player_data)
    if not merged_data:
        raise ValueError("Không có dữ liệu cầu thủ nào được thu thập")
    df = pd.DataFrame.from_dict(merged_data, orient='index')
    valid_players = df[df[['standard_team', 'standard_position', 'standard_age', 'standard_minutes']].notnull().all(axis=1) & 
                      (df[['standard_team', 'standard_position', 'standard_age', 'standard_minutes']] != 'N/a').all(axis=1)]

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
        'defense_dribbles_tackles_pct': 
        'Lost', 'defense_blocks': 'Blocks', 
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
    final_columns = {'Player': valid_players['Player']}
    for old_col, new_col in column_mapping.items():
        final_columns[new_col] = valid_players.get(old_col, pd.Series(['N/a'] * len(valid_players)))

    final_df = pd.DataFrame(final_columns).sort_values('Player')
    final_df['Available_Data_Count'] = (final_df != 'N/a').sum(axis=1)
    
    final_df_filtered = final_df[final_df[['Player', 'Team', 'Pos', 'Age', 'MP', 'Starts', 'Min']].notnull().all(axis=1) & 
                                (final_df[['Player', 'Team', 'Pos', 'Age', 'MP', 'Starts', 'Min']] != 'N/a').all(axis=1)]
    
    final_df.to_csv('results.csv', index=False, encoding='utf-8-sig')
except Exception as e:
    print(f"\nĐã xảy ra lỗi: {e}")
finally:
    driver.quit()
    print("OK.")
