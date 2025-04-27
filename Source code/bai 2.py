import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

df = pd.read_csv('results.csv')

#1. Xác định top 3
exclude_columns = ['Player', 'Team', 'Pos', 'Nation', 'Available_Data_Count', 'Age']
valid_columns = []
for col in df.columns:
    if col not in exclude_columns:
        try:
            df[col] = pd.to_numeric(df[col].replace('N/a', np.nan))
            valid_columns.append(col)
        except:
            print(f"Không thể chuyển đổi {col} sang dạng số")
def get_top_bottom_players(df, column):
    valid_df = df[df[column].notna()]
    if len(valid_df) == 0:
        return [], []
    top_3 = valid_df.sort_values(by=column, ascending=False).head(3)
    top_players = []
    for _, row in top_3.iterrows():
        value = row[column]
        if abs(value - round(value)) < 0.01:
            value = int(round(value))
        top_players.append(f"{row['Player']} ({row['Team']}): {value}")
    bottom_3 = valid_df.sort_values(by=column, ascending=True).head(3)
    bottom_players = []
    for _, row in bottom_3.iterrows():
        value = row[column]
        if abs(value - round(value)) < 0.01:
            value = int(round(value))
        bottom_players.append(f"{row['Player']} ({row['Team']}): {value}")
    return top_players, bottom_players
top_3_results = {}
for col in valid_columns:
    top_players, bottom_players = get_top_bottom_players(df, col)
    if top_players and bottom_players:
        top_3_results[col] = {
            'top': top_players,
            'bottom': bottom_players
        }
with open('top_3.txt', 'w', encoding='utf-8') as f:
    f.write("Top 3 players for each stastic\n")
    f.write("-" * 70 + "\n\n")
    for col, data in top_3_results.items():
        f.write(f"{col}\n")
        f.write("Top 3 players with highest scores:\n")
        for i, player in enumerate(data['top'], 1):
            f.write(f"{i}. {player}\n")
        
        f.write("\nTop 3 players with the lowest scores:\n")
        for i, player in enumerate(data['bottom'], 1):
            f.write(f"{i}. {player}\n")
        f.write('\n')        

# 2.Tính median, mean và std.
def calculate(dataframe, columns):
    stats = {}
    all_stats = {'Team': 'all'}
    for col in columns:
        valid_data = dataframe[col].dropna()
        if len(valid_data) > 0:
            all_stats[f'Median_{col}'] = valid_data.median()
            all_stats[f'Mean_{col}'] = valid_data.mean()
            all_stats[f'Std_{col}'] = valid_data.std()
        else:
            all_stats[f'Median_{col}'] = np.nan
            all_stats[f'Mean_{col}'] = np.nan
            all_stats[f'Std_{col}'] = np.nan
    stats['all'] = all_stats
    teams = dataframe['Team'].unique()
    for team in teams:
        if pd.isna(team) or team == 'N/a':
            continue
        team_df = dataframe[dataframe['Team'] == team]
        team_stats = {'Team': team}
        for col in columns:
            valid_data = team_df[col].dropna()
            if len(valid_data) > 0:
                team_stats[f'Median_{col}'] = valid_data.median()
                team_stats[f'Mean_{col}'] = valid_data.mean()
                team_stats[f'Std_{col}'] = valid_data.std()
            else:
                team_stats[f'Median_{col}'] = np.nan
                team_stats[f'Mean_{col}'] = np.nan
                team_stats[f'Std_{col}'] = np.nan
        stats[team] = team_stats
    return stats
stats_results = calculate(df, valid_columns)
stats_rows = []
for team, stats in stats_results.items():
    stats_rows.append(stats)
stats_df = pd.DataFrame(stats_rows)
first_columns = ['Team']
other_columns = [col for col in stats_df.columns if col != 'Team']
stats_df = stats_df[first_columns + other_columns]
all_row = stats_df[stats_df['Team'] == 'all']
other_rows = stats_df[stats_df['Team'] != 'all']
stats_df = pd.concat([all_row, other_rows])
stats_df = stats_df.reset_index(drop=True)
stats_df.to_csv('results2.csv', index=True, encoding='utf-8-sig')
print("Đã lưu vào file results2.csv")

# 3 Vẽ histogram cho 3 chỉ số tấn công và 3 chỉ số phòng thủ
attack_metrics = ['Goals', 'Assists', 'xG']
defense_metrics = ['Tkl', 'Int', 'Blocks']

missing_metrics = [m for m in attack_metrics + defense_metrics if m not in df.columns]
if missing_metrics:
    print(f"Các chỉ số không tồn tại: {missing_metrics}")
else:
    teams = stats_df['Team'].unique()
    teams = [team for team in teams if team != 'all' and pd.notna(team)]

    os.makedirs('histograms', exist_ok=True)
    for team in teams:
        team_df = df[df['Team'] == team]
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'Histograms for {team}', fontsize=16)

        for i, metric in enumerate(attack_metrics):
            valid_data = team_df[metric].dropna()
            if len(valid_data) > 0:
                sns.histplot(data=valid_data, ax=axes[0, i], kde=True, bins=10)
                axes[0, i].set_title(f'Attack: {metric}')
                axes[0, i].set_xlabel(metric)
                axes[0, i].set_ylabel('Frequency')
            else:
                axes[0, i].text(0.5, 0.5, 'No Data', ha='center', va='center')
                axes[0, i].set_title(f'Attack: {metric}')

        for i, metric in enumerate(defense_metrics):
            valid_data = team_df[metric].dropna()
            if len(valid_data) > 0:
                sns.histplot(data=valid_data, ax=axes[1, i], kde=True, bins=10)
                axes[1, i].set_title(f'Defense: {metric}')
                axes[1, i].set_xlabel(metric)
                axes[1, i].set_ylabel('Frequency')
            else:
                axes[1, i].text(0.5, 0.5, 'No Data', ha='center', va='center')
                axes[1, i].set_title(f'Defense: {metric}')
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.savefig(f'histograms/{team}_histogram.png')
        plt.close()
    print("Đã lưu histogram\n")
# 4. Best team
columnsz = df.select_dtypes(include=np.number).columns

team_stats = df.groupby('Team')[columnsz].mean()
best_stat = team_stats.idxmax()
top_count = best_stat.value_counts()
top_team = top_count.idxmax()

with open('top_3.txt', 'a', encoding='utf-8') as f:
    f.write("-" * 70 + "\n\n")
    f.write('\nBest Teams by Statistic:\n')
    for stat, team in best_stat.items():
        f.write(f'{stat}: {team}\n')
    f.write(f'\nTeam with most top statistics: {top_team}\n')
