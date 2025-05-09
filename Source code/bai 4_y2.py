import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_squared_error
import re

def convert_etv(value):
    try:
        if value in ["Not found", "Error"] or pd.isna(value):
            return np.nan
        match = re.search(r'€([\d.]+)([MK])', str(value))
        if not match:
            return np.nan
        number, unit = float(match.group(1)), match.group(2)
        return number if unit == "M" else number / 1000
    except:
        return np.nan
    
df = pd.read_csv("bai4.csv")

avai_columns = df.columns.tolist()
df["ETV_numeric"] = df["ETV"].apply(convert_etv)
df = df.dropna(subset=["ETV_numeric"])
le_pos = LabelEncoder()
le_team = LabelEncoder()
le_nation = LabelEncoder()
for col, encoder in [("Pos", le_pos), ("Team", le_team), ("Nation", le_nation)]:
    if col in df.columns:
        df[f"{col}_encoded"] = encoder.fit_transform(df[col].astype(str))
    else:
        print(f"Lỗi")
        exit(1)
feature_columns = [
    "Nation_encoded", "Age", "MP", "Starts", "Min", "Goals", "Assists", "Yellow_Card", 
    "Red_Card", "stand_xG", "xAG", "PrgC", "PrgP", "PrgR", "Gls", "Ast", "xG", "xGA", 
    "GA90", "Save%", "CS%", "PKsv%", "SoT%", "SoT/90", "G/Sh", "Dist", "Cmp", "Cmp%", 
    "TotDist", "Short_Cmp%", "Medium_Cmp%", "KP", "1/3", "PPA", "CrsPA", "PrgP_passing", 
    "SCA", "SCA90", "GCA", "GCA90", "Tkl", "TklW", "Att", "Lost", "Blocks", "Sh", "Pass", 
    "Int", "Touches", "Def_Pen", "Def_3rd", "Mid_3rd", "Att_3rd", "Att_Pen", 
    "Att_take_ons", "Succ%", "Tkld%", "Carries", "ProDist", "ProgC", "1/3_carries", 
    "CPA", "Mis", "Dis", "Rec", "PrgR_possession", "Fls", "Fld", "Off", "Crs", 
    "Recov", "Won", "Won%", "Available_Data_Count", "Pos_encoded", "Team_encoded"
]
for col in feature_columns:
    if col in df.columns:
        df[col] = df[col].replace('N/a', np.nan)
        try:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(df[col].mean() if df[col].dtype in ['float64', 'int64'] else 0)
        except Exception as e:
            print(f"Lỗi khi xử lý cột {col}: {str(e)}")
            df[col] = df[col].fillna(0)
    else:
        print(f"Cột {col} không tồn tại trong file, bỏ qua.")
        feature_columns.remove(col)
for col in feature_columns:
    if not np.issubdtype(df[col].dtype, np.number):
        print(f"Lỗi: Cột {col} chứa giá trị không phải số: {df[col].head()}")
        exit(1)

scaler = StandardScaler()
try:
    X = scaler.fit_transform(df[feature_columns])
    y = df["ETV_numeric"]
except Exception as e:
    print(f"Lỗi khi chuẩn hóa dữ liệu: {str(e)}")
    exit(1)

model = RandomForestRegressor(n_estimators=50, random_state=42)
model.fit(X, y)

df["ETV_predicted"] = np.round(model.predict(X), 2)
rmse = np.sqrt(mean_squared_error(df["ETV_numeric"], df["ETV_predicted"]))
print(f"RMSE: €{rmse:.2f}M")
result = df[["Player", "ETV_predicted", "ETV"]].copy()
result.rename(columns={"ETV": "ETV_actual"}, inplace=True)
result.to_csv("bai4_predict_and_actual.csv", index=False)
print("Đã lưu kết quả vào bai4_predict_and_actual.csv")