from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from concurrent.futures import ThreadPoolExecutor
import random
import unicodedata
# 1. Get player from web.
special_names = {
    'sávio'                   : "savio-moreira-moreira-de-oliveira",
    "santiago bueno"          : "santiago-ignacio-bueno-sciutto",
    "joão pedro"              : "joao-pedro-junqueira-de-jesus",
    "igor"                    : "igor-julio-igor",
    "enzo fernández"          : "enzo-jeremias-fernandez",
    "ederson"                 : "ederson-moraes",
    "beto"                    : "beto-beto-1",
    "andré"                   : "andre-trindade-da-costa-neto",
    "alisson"                 : "alisson-4",
    "adama traoré"            : "adama-traore-3",
    "pau torres"              : "pau-torres-1",
    "josé sá"                 : "jose-sa",
    "harvey barnes"           : "harvey-barnes",
    "kepa arrizabalaga"       : "arrizabalaga",
    "flynn downes"            : "flynn-downes",
    "amadou onana"            : "amadou-onana",
    "alejandro garnacho"      : "alejandro-garnacho-ferreyra",
    "aaron wan-bissaka"       : "aaron-wanbissaka", 
    "amad diallo"             : "amad-diallo-diallo",
    "antonee robinson"        : "antonee-robinson-1",
    "ben johnson"             : "benjamin-johnson",
    "bilal el khannouss"      : "bilal-el-khannous",
    "bruno guimarães"         : "bruno-guimaraes-bruno-guimaraes",
    "caleb okoli"             : "memeh-caleb-okoli",
    "calvin bassey"           : "calvin-bassey-ughelumba",
    "carlos baleba"           : "carlos-balepa-noom-quomah",
    "chris wood"              : "chris-wood-2",
    "christian nørgaard"      : "christian-norgaard",
    "cristian romero"         : "cristian-gabriel-romero",
    "curtis jones"            : "curtis-jones-1",
    "dango ouattara"          : "dango-aboubacar-faissal-ouattara",
    "daniel muñoz"            : "daniel-munoz-mejia",
    "darwin núñez"            : "darwin-gabriel-nunez-ribeiro",
    "david raya"              : "david-raya-martin",
    "destiny udogie"          : "iyenoma-destiny-udogie",
    "diogo dalot"             : "jose-diogo-dalot-teixeira",
    "elliot anderson"         : "elliott-anderson",
    "emerson palmieri"        : "emerson-2",
    "erling haaland"          : "erling-braut-haaland",
    "evanilson"               : "francisco-evanilson-de-lima-barbosa",
    "ezri konsa"              : "ezri-konsa-ngoyo",
    "facundo buonanotte"      : "facundo-valentin-buonanotte",
    "gabriel martinelli"      : "gabriel-martinelli-1",
    "idrissa gana gueye"      : "idrissa-gueye",
    "jack clarke"             : "jack-clarke-1",
    "jake o'brien"            : "jake-obrien-1",
    "james tarkowski"         : "james-alan-tarkowski",
    "jean-clair todibo"       : "jeanclair-dimitri-roger-todibo",
    "jens cajuste"            : "jenslys-michel-cajuste",
    "jesper lindstrøm"        : "jesper-grange-lindstrom",
    "joe aribo"               : "joseph-oluwaseyi-temitope-ayodelearibo",
    "joelinton"               : "joelinton-cassio-joelinton",
    "joão gomes"              : "joao-victor-gomes-da-silva",
    "jurriën timber"          : "jurrin-david-norman-timber",
    "jørgen strand larsen"    : "jorgen-strand-strand-larsen",
    "kamaldeen sulemana"      : "kamal-deen-sulemana",
    "kepa arrizabalag"        : "arrizabalaga",
    "lesley ugochukwu"        : "chimuanya-ugochukwu",
    "levi colwill"            : "levi-samuels-colwill",
    "lewis hall"              : "lewis-hall-2",
    "luis díaz"               : "luis-fernando-diaz-marulanda",
    "mads roerslev"           : "luis-fernando-diaz-marulanda",
    "manuel akanji"           : "manuel-obafemi-akanji",
    "marc cucurella"          : "marc-cucurella-saseta",
    "marcos senesi"           : "marcos-nicolas-senesi-baron",
    "martin ødegaard"         : "martin-odegaard",
    "mateus fernandes"        : "mateus-goncalo-espanha-fernandes",
    "matheus cunha"           : "matheus-santos-carneiro-da-cunha",
    "matheus nunes"           : "matheus-luiz-nunes",
    "max kilman"              : "maximilian-kilman",
    "murillo"                 : "murillo-santiago-costa-dos-santos",
    "myles lewis-skelly"      : "myles-anthony-lewisskelly",
    "nathan collins"          : "nathan-michael-collins",
    "neco williams"           : "neco-shay-williams",
    "nicolas jackson"         : "nicolas-jackson-1",
    "nicolás domínguez"       : "nicolas-martin-dominguez",
    "noni madueke"            : "chukwunonso-tristan-madueke",
    "nélson semedo"           : "nelsinho-1",
    "omar marmoush"           : "omar-khaled-mohamed-marmoush",
    "pape matar sarr"         : "pape-matar-sarr-1",
    "pedro neto"              : "pedro-neto-1",
    "pedro porro"             : "pedro-antonio-porro-sauceda",
    "pervis estupiñán"        : "pervis-josue-estupinan-tenorio",
    "rasmus højlund"          : "rasmus-winther-hojlund",
    "rayan aït-nouri"         : "rayan-ait-nouri",
    "robert sánchez"          : "robert-lynch-sanchez",
    "rodrigo muniz"           : "rodrigo-muniz-carvalho",
    "ryan christie"           : "ryan-christie-1",
    "ryan gravenberch"        : "ryan-jiro-gravenberch",
    "sam morsy"               : "samy-morsy",
    "sammie szmodics"         : "samuel-szmodics",
    "sander berge"            : "sander-gard-bolin-berge",
    "son heung-min"           : "heungmin-son",
    "stefan ortega"           : "stefan-ortega-moreno",
    "taylor harwood-bellis"   : "taylor-harwood-bellis",
    "toti gomes"              : "toti-antonio-gomes",
    "tyler dibling"           : "tyler-obling",
    "victor bernth kristiansen": "victor-kristiansen",
    "yasin ayari"             : "yasin-abbas-ayari",
    "youri tielemans"         : "youri-tielemans",
    "yehor yarmoliuk"         : "yegor-yarmolyuk",
    "łukasz fabiański"        : "lukasz-fabianski",
    "stephy mavididi"         : "stephy-mavididi",
}

df = pd.read_csv("results.csv")
eligible_players = df[df["Min"] > 900][[
    "Player", "Nation", "Team", "Pos", "Age", "MP", "Starts", "Min", "Goals", "Assists", 
    "Yellow_Card", "Red_Card", "stand_xG", "xAG", "PrgC", "PrgP", "PrgR", "Gls", "Ast", 
    "xG", "xGA", "GA90", "Save%", "CS%", "PKsv%", "SoT%", "SoT/90", "G/Sh", "Dist", 
    "Cmp", "Cmp%", "TotDist", "Short_Cmp%", "Medium_Cmp%", "KP", "1/3", "PPA", "CrsPA", 
    "PrgP_passing", "SCA", "SCA90", "GCA", "GCA90", "Tkl", "TklW", "Att", "Lost", 
    "Blocks", "Sh", "Pass", "Int", "Touches", "Def_Pen", "Def_3rd", "Mid_3rd", "Att_3rd", 
    "Att_Pen", "Att_take_ons", "Succ%", "Tkld%", "Carries", "ProDist", "ProgC", "1/3_carries", 
    "CPA", "Mis", "Dis", "Rec", "PrgR_possession", "Fls", "Fld", "Off", "Crs", "Recov", 
    "Won", "Won%", "Available_Data_Count"
]].head(298).copy()

def standardize_names(name):
    lower_name = name.lower().strip()
    if lower_name in special_names:
        return special_names[lower_name]
    name = lower_name
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.replace(' ', '-')
def get_etv(player_name, error_log):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 5)
        player_slug = standardize_names(player_name)
        url = f'https://www.footballtransfers.com/en/players/{player_slug}'
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "player-value")))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        possible_classes = [
            "player-value player-value-large",
            "player-value",
            "value-large",
            "etv-value"
        ]
        etv = None
        for class_name in possible_classes:
            etv_element = soup.find('div', class_=class_name)
            if etv_element:
                etv = etv_element.text.strip()
                match = re.search(r'€[\d.]+[M|K]', etv)
                if match:
                    return match.group(0)
                break
        if not etv:
            error_log.append({'Player': player_name, 'Error': 'ETV not found'})
            return "Not found"
        return etv
    except Exception as e:
        error_log.append({"Player": player_name, "Error": str(e)})
        return "Error"
    finally:
        if driver:
            driver.quit()
        time.sleep(random.uniform(0.5, 2))

def process_players(players_df, max_workers=4):
    error_log = []
    results = players_df.copy()
    results["ETV"] = None
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        etvs = list(executor.map(lambda x: get_etv(x, error_log), results["Player"]))
    results["ETV"] = etvs
    results.to_csv("bai4(beta).csv", index=False)
    print("Saved")
    return results
process_players(eligible_players, max_workers=10)