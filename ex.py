from http.client import HTTPException
from pydantic import BaseModel
from typing import List, Dict
from fastapi import FastAPI, Request, Form, Query
import pandas as pd
import numpy as np


from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from passlib.context import CryptContext
import jwt
from typing import Optional
from datetime import datetime, timedelta

# Constants
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# FastAPI instance
app = FastAPI()

# Database connection
uri = "mongodb+srv://chaitanyak21:<ChaitU2004>@cluster0.cv4jf3z.mongodb.net/?appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['fantasy_cricket']

# Ping to confirm connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Password Bearer instance
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# User models


class UserInDB(BaseModel):
    username: str
    email: EmailStr
    hashed_password: str
    disabled: Optional[bool] = None


class User(BaseModel):
    username: str
    email: EmailStr
    disabled: Optional[bool] = None


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(min_length=8)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None

# Helper functions


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_user(username: str):
    user = await db['users'].find_one({"username": username})
    if user:
        return UserInDB(**user)


async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    user = await get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# Register endpoint


@app.post("/register", response_model=User)
async def register_user(user: UserCreate):
    user_in_db = await get_user(user.username)
    if user_in_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    hashed_password = get_password_hash(user.password)
    user_dict = user.dict()
    user_dict['hashed_password'] = hashed_password
    del user_dict['password']
    await db['users'].insert_one(user_dict)
    return user

# Login endpoint


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Get current user endpoint


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


# Global Variables
Team1_Squad = {}
Team2_Squad = {}
user_choice1 = None
user_choice2 = None

# Load CSV files
byb = pd.read_csv('IPl Ball-by-Ball 2008-2023.csv')
match = pd.read_csv('IPL Mathces 2008-2023.csv')

# Fantasy Points
Batsman_points = {
    'Run': 1, 'bFour': 1, 'bSix': 2, '30Runs': 4,
    'Half_century': 8, 'Century': 16, 'Duck': -2, '170sr': 6,
    '150sr': 4, '130sr': 2, '70sr': -2, '60sr': -4, '50sr': -6
}

Bowling_points = {
    'Wicket': 25, 'LBW_Bowled': 8, '3W': 4, '4W': 8,
    '5W': 16, 'Maiden': 12, '5rpo': 6, '6rpo': 4, '7rpo': 2, '10rpo': -2,
    '11rpo': -4, '12rpo': -6
}

Fielding_points = {
    'Catch': 8, '3Catch': 4, 'Stumping': 12, 'RunOutD': 12,
    'RunOutInd': 6
}

# TEAM 1
srh = ['Abdul Samad', 'HC Brook', 'AK Markram', 'H Klaasen', 'RA Tripathi',
       'B Kumar', 'T Natarajan', 'Washington Sundar', 'M Jansen', 'Kartik Tyagi', 'Umran Malik']

srh_fp = {'HC Brook': 111, 'Adil Rashid': 111, 'H Klaasen': 111, 'B Kumar': 111, 'Abdul Samad': 111, 'Abhishek Sharma': 111, 'AK Markram': 111, 'Fazalhaq Farooqi': 111,
          'M Jansen': 111, 'RA Tripathi': 111, 'Kartik Tyagi': 111, 'T Natarajan': 111, 'Umran Malik': 111,
          'Washington Sundar': 111, 'M Markande': 111, 'Vivrant Sharma': 111, 'Samarth Vyas': 111, 'Sanvir Singh': 111, 'Upendra Yadav': 111, 'Mayank Dagar': 111, }

# TEAM 2
pbks = ['S Dhawan', 'MA Agarwal', 'Arshdeep Singh', 'LS Livingstone', 'K Rabada', 'Jitesh Sharma',
        'SM Curran', 'Bhanuka Rajapakse', 'RD Chahar', 'Harpreet Brar', 'M Shahrukh Khan']

pbks_fp = {'S Dhawan': 111, 'MA Agarwal': 111, 'M Shahrukh Khan': 111, 'RD Chahar': 111, 'Arshdeep Singh': 111, 'Harpreet Brar': 111, 'RA Bawa': 111,
           'Prabhsimran Singh': 111, 'R Dhawan': 111, 'Jitesh Sharma': 111,
           'Baltej Singh Dhanda': 111, 'Atharva Taide': 111, 'LS Livingstone': 111, 'K Rabada': 111, 'JM Bairstow': 111,
           'NT Ellis': 111,   'Bhanuka Rajapakse': 111, 'Shivam Singh': 111, 'Mohit Rathee': 111, 'Vidwath Kaverappa': 111, 'R Bhatia': 111, 'Sikandar Raza': 111, 'SM Curran': 111, }

# TEAM 3
csk = ['MS Dhoni', 'Matheesha Pathirana', 'Shivam Dube', 'RD Gaikwad', 'AT Rayudu',
       'MM Ali', 'RA Jadeja', 'AM Rahane', 'Devon Conway', 'DL Chahar', 'MJ Santner']

csk_fp = {'MS Dhoni': 111, 'Devon Conway': 111, 'RD Gaikwad': 111, 'AT Rayudu': 111, 'Shivam Dube': 111,
          'MM Ali': 111, 'RA Jadeja': 111, 'Simarjeet Singh': 111, 'Subhranshu Senapati': 111, 'Matheesha Pathirana': 111,
          'TU Deshpande': 111, 'Bhagath Varma': 111, 'Ajay Mandal': 111, 'KA Jamieson': 111, 'Nishant Sindhu': 111,
          'Shaik Rasheed': 111, 'BA Stokes': 111, 'AM Rahane': 111, 'DL Chahar': 111, 'D Pretorius': 111, 'M Theekshana': 111, 'MJ Santner': 111,
          'Mukesh Choudhary': 111,  'PH Solanki': 111, 'RS Hangargekar': 111, }

# TEAM 4
kkr = ['N Rana', 'AD Russell', 'UT Yadav', 'SP Narine', 'Rahmanullah Gurbaz',
       'SN Thakur', 'RK Singh', 'LH Ferguson', 'KL Nagarkoti', 'VR Iyer', 'Varun Chakravarthy']

kkr_fp = {'N Rana': 326, 'AD Russell': 545, 'SP Narine': 172, 'Shakib Al Hasan': 120, 'LH Ferguson': 0,
          'KL Nagarkoti': -2, 'Harshit Rana': 111, 'Rahmanullah Gurbaz': 111, 'RK Singh': 111, 'SN Thakur': 111,
          'TG Southee': 111, 'UT Yadav': 111, 'Varun Chakravarthy': 111, 'VR Iyer': 111, 'Mandeep Singh': 111, 'Liton Das': 111, 'K Khejroliya': 111, 'David Wiese': 111,
          'Suyash Sharma': 111, 'VG Arora': 111, 'N Jagadeesan': 111, 'Anukul Roy': 111, }

# TEAM 5
dc = ['DA Warner', 'A Nortje', 'AR Patel', 'C Sakariya', 'KL Nagarkoti',
      'Kuldeep Yadav', 'Lalit Yadav', 'L Ngidi', 'MR Marsh', 'Mustafizur Rahman', 'PP Shaw']

dc_fp = {'Aman Khan': 111, 'DA Warner': 111, 'A Nortje': 111, 'AR Patel': 111, 'C Sakariya': 111, 'KL Nagarkoti': 111, 'Kuldeep Yadav': 111,
         'Lalit Yadav': 111, 'L Ngidi': 111, 'MR Marsh': 111, 'Mustafizur Rahman': 111, 'P Dubey': 111,
         'PP Shaw': 111, 'Ripal Patel': 111, 'R Powell': 111, 'Sarfaraz Khan': 111, 'KK Ahmed': 111, 'Vicky Ostwal': 111, 'YV Dhull': 111,
         'RR Rossouw': 111, 'MK Pandey': 111, 'Mukesh Kumar': 111, 'I Sharma': 111, 'PD Salt': 111, }

# TEAM 6
rcb = ['V Kohli', 'GJ Maxwell',  'Mohammed Siraj',  'JR Hazlewood', 'RM Patidar',
       'Anuj Rawat', 'Shahbaz Ahmed',  'KD Karthik', 'KV Sharma', 'Wanindu Hasaranga',  'HV Patel']

rcb_fp = {'V Kohli': 414, 'GJ Maxwell': 392, 'Shahbaz Ahmed': 194, 'Faf Duplesis': 350,
          'DT Christian': 47, 'HV Patel': 634, 'Mohammed Siraj': 275, 'Akash Deep': 111, 'Anuj Rawat': 111, 'DJ Willey': 111,
          'KD Karthik': 111, 'FA Allen': 111, 'JR Hazlewood': 111, 'KV Sharma': 111, 'MK Lomror': 111, 'RM Patidar': 111, 'S Kaul': 111,
          'SS Prabhudessai': 111, 'Wanindu Hasaranga': 111, 'Sonu Yadav': 111, 'Avinash Singh': 111, 'Rajan Kumar': 111, 'Manoj Bhandage': 111,
          'Will Jacks': 111, 'Himanshu Sharma': 111, 'RJW Topley': 111, }

# TEAM 7
mi = ['Ishan Kishan', 'RG Sharma',  'SA Yadav',  'JJ Bumrah', 'Akash Madhwal',
      'Tilak Varma',  'C Green',  'TH David', 'PP Chawla', 'K Kartikeya', 'JP Behrendorff']

mi_fp = {'Ishan Kishan': 134, 'RG Sharma': 393, 'SA Yadav': 307,
         'JJ Bumrah': 382, 'Akash Madhwal': 111, 'Arjun Tendulkar': 111, 'D Brevis': 111,
         'HR Shokeen': 111, 'JP Behrendorff': 111, 'JC Archer': 111, 'K Kartikeya': 111, 'Arshad Khan': 111, 'Tilak Varma': 111,
         'Ramandeep Singh': 111, 'TH David': 111, 'T Stubbs': 111, 'R Goyal': 111, 'N Wadhera': 111,
         'Shams Mulani': 111, 'Vishnu Vinod': 111, 'M Jansen': 111, 'PP Chawla': 111, 'JA Richardson': 111, 'C Green': 111, }

# TEAM 8
rr = ['SV Samson', 'JC Buttler', 'YBK Jaiswal', 'TA Boult', 'R Parag', 'SO Hetmyer',
      'R Ashwin', 'M Prasidh Krishna', 'YS Chahal', 'D Padikkal', 'OC McCoy']

rr_fp = {'SV Samson': 111, 'JC Buttler': 111, 'D Padikkal': 111, 'Dhruv Jurel': 111, 'KC Cariappa': 111, 'Kuldeep Sen': 111, 'Kuldeep Yadav': 111,
         'NA Saini': 111, 'OC McCoy': 111, 'M Prasidh Krishna': 111, 'R Ashwin': 111, 'R Parag': 111, 'SO Hetmyer': 111, 'TA Boult': 111,
         'YBK Jaiswal': 111, 'YS Chahal': 111, 'Root': 111, 'Abdul P A': 111, 'Akash Vashisht': 111, 'M Ashwin': 111,
         'KM Asif': 111, 'A Zampa': 111, 'Kunal Rathore': 111, 'Donovan Ferreira': 111, 'JO Holder': 111, }

# TEAM 9
gt = ['HH Pandya', 'Rashid Khan', 'Shubman Gill', 'AS Joseph',  'R Tewatia',
      'Mohammed Shami', 'WP Saha', 'Yash Dayal', 'DA Miller', 'B Sai Sudharsan', 'V Shankar']

gt_fp = {'HH Pandya': 111, 'Rashid Khan': 111, 'Shubman Gill': 111, 'Abhinav Sadarangani': 111, 'AS Joseph': 111, 'B Sai Sudharsan': 111,
         'DG Nalkande': 111, 'DA Miller': 111, 'J Yadav': 111, 'MS Wade': 111, 'Mohammed Shami': 111, 'Noor Ahmad': 111, 'PJ Sangwan': 111, 'R Sai Kishore': 111,
         'R Tewatia': 111, 'V Shankar': 111, 'WP Saha': 111, 'Yash Dayal': 111, 'MM Sharma': 111, 'J Little': 111, 'Urvil Patel': 111, 'Shivam Mavi': 111,
         'KS Bharat': 111, 'OF Smith': 111, 'KS Williamson': 111, }

# TEAM 10

lsg = ['KL Rahul', 'KH Pandya', 'MP Stoinis', 'N Pooran', 'MA Wood',
       'Q de Kock', 'Ravi Bishnoi', 'Avesh Khan', 'A Badoni', 'DJ Hooda', 'A Mishra']

lsg_fp = {'KL Rahul': 111, 'Avesh Khan': 111, 'A Badoni': 111, 'DJ Hooda': 111, 'K Gowtham': 111, 'KS Sharma': 111, 'KH Pandya': 111,
          'KR Mayers': 111, 'M Vohra': 111, 'MP Stoinis': 111, 'MA Wood': 111, 'Mayank Yadav': 111, 'Mohsin Khan': 111, 'Q de Kock': 111, 'Ravi Bishnoi': 111,
          'Yudhvir Charak': 111, 'Naveen-ul-Haq': 111, 'Swapnil Singh': 111, 'PN Mankad': 111, 'A Mishra': 111, 'Daniel Sams': 111, 'R Shepherd': 111, 'Yash Thakur': 111,
          'JD Unadkatt': 111, 'N Pooran': 111, }


teams_data = {
    'SRH': srh_fp,
    'PBKS': pbks_fp,
    'CSK': csk_fp,
    'KKR': kkr_fp,
    'DC': dc_fp,
    'RCB': rcb_fp,
    'MI': mi_fp,
    'RR': rr_fp,
    'GT': gt_fp,
    'LSG': lsg_fp
}


def get_players(team1, team2, team1_fp, byb):
    fantasy_team_players = []

    for i in range(len(team1)):
        unq_ids = byb[byb["batsman"] == team1[i]]['id'].unique()
        mathces_played = len(unq_ids)

        bbr = []
        for x in unq_ids:
            bat_run = sum(byb[(byb["batsman"] == team1[i]) &
                          (byb['id'] == x)]['batsman_runs'])
            bbr.append(bat_run)

        r30, r50, r100 = 0, 0, 0
        for m in bbr:
            if m >= 100:
                r100 += 1
            elif m >= 50:
                r50 += 1
            elif m >= 30:
                r30 += 1

        try:
            catches = len(byb[(byb['fielder'] == team1[i]) & (
                byb['dismissal_kind'] == 'caught')]) / mathces_played
            run_outs = len(byb[(byb['fielder'] == team1[i]) & (
                byb['dismissal_kind'] == 'run out')]) / mathces_played
            extra_points = (r30 / mathces_played) * Batsman_points['30Runs'] + \
                           (r50 / mathces_played) * Batsman_points['Half_century'] + \
                           (r100 / mathces_played) * Batsman_points['Century'] + \
                catches * Fielding_points['Catch'] + \
                run_outs * Fielding_points['RunOutInd']
        except:
            catches, run_outs, extra_points = 0, 0, 0

        wickets_taken = []
        for x in unq_ids:
            twx = sum(byb[(byb["bowler"] == team1[i])
                      & (byb['id'] == x)]['is_wicket'])
            wickets_taken.append(twx)

        w3, w4, w5 = 0, 0, 0
        for z in wickets_taken:
            if z >= 5:
                w5 += 1
            elif z >= 4:
                w4 += 1
            elif z >= 3:
                w3 += 1

        try:
            lbws = len((byb[(byb['bowler'] == team1[i]) & (
                byb['dismissal_kind'] == 'lbw')])) / mathces_played
            bowled = len((byb[(byb['bowler'] == team1[i]) & (
                byb['dismissal_kind'] == 'bowled')])) / mathces_played
            wexp = (w3 / mathces_played) * Bowling_points['3W'] + \
                   (w4 / mathces_played) * Bowling_points['4W'] + \
                   (w5 / mathces_played) * Bowling_points['5W'] + \
                lbws * Bowling_points['LBW_Bowled'] + \
                bowled * Bowling_points['LBW_Bowled']
        except:
            lbws, bowled, wexp = 0, 0, 0

        ffp = []
        for j in range(len(team2)):
            bat_vs_bowl = byb[(byb["batsman"] == team1[i]) &
                              (byb["bowler"] == team2[j])]
            bowls_played = len(bat_vs_bowl.batsman_runs)
            runs_scored = sum(bat_vs_bowl.batsman_runs)
            fours = len(bat_vs_bowl[bat_vs_bowl['batsman_runs'] == 4])
            sixes = len(bat_vs_bowl[bat_vs_bowl['batsman_runs'] == 6])
            wicket = sum(bat_vs_bowl.is_wicket)

            if bowls_played <= 6 * 10 and wicket >= 5:
                penalty = -16
            elif bowls_played <= 6 * 8 and wicket >= 4:
                penalty = -8
            elif bowls_played <= 6 * 6 and wicket >= 3:
                penalty = -4
            else:
                penalty = 0

            try:
                strike_rate = int(runs_scored / bowls_played * 100)
            except ZeroDivisionError:
                strike_rate = 'NA'

            if bowls_played >= 10 and strike_rate != 'NA':
                if strike_rate >= 170:
                    print(team1[i], "beaten", team2[j], "Runs", runs_scored, "bowls", bowls_played,
                          "strike rate", strike_rate, 'Out', wicket, 'times', "Fours", fours, "Sixes", sixes)
                elif strike_rate >= 150:
                    print(team1[i], "beaten", team2[j], "Runs", runs_scored, "bowls", bowls_played,
                          "strike rate", strike_rate, 'Out', wicket, 'times', "Fours", fours, "Sixes", sixes)

            bowl_vs_bat = byb[(byb["bowler"] == team1[i]) &
                              (byb["batsman"] == team2[j])]
            wicket_took = sum(bowl_vs_bat.is_wicket)
            fantasy_points1 = runs_scored + \
                fours * Batsman_points['bFour'] + \
                sixes * Batsman_points['bSix'] - \
                wicket * Bowling_points['Wicket'] + \
                wicket_took * Bowling_points['Wicket'] + \
                penalty

            ffp.append(fantasy_points1)
            print(team1[i], "against", team2[j], "Runs", runs_scored,
                  "bowls", bowls_played, "strike rate", strike_rate,
                  'Out', wicket, 'times', "Fours", fours, "Sixes", sixes, "fantasy points", fantasy_points1)

        sum_ffp = sum(ffp)

        if team1_fp[team1[i]] > 0:
            recent_performance_points = np.log(team1_fp[team1[i]])
        elif team1_fp[team1[i]] < 0:
            recent_performance_points = -np.log(abs(team1_fp[team1[i]]))
        else:
            recent_performance_points = 0

        weight1 = 0.5
        weight2 = 1 - weight1

        final_fantasy_point = (sum_ffp + extra_points + wexp) * \
            weight1 + recent_performance_points * weight2
        final_fantasy_point = round(final_fantasy_point, 2)

        fantasy_team_players.append((final_fantasy_point, team1[i]))
        fantasy_team_players.sort(reverse=True)

        print("Fantasy points of", team1[i], ":", final_fantasy_point)

    return fantasy_team_players


def calculate_individual_fantasy_points(player, opponent_team, player_fp, byb):
    unq_ids = byb[byb["batsman"] == player]['id'].unique()
    matches_played = len(unq_ids)

    bbr = []
    for x in unq_ids:
        bat_run = sum(byb[(byb["batsman"] == player) &
                      (byb['id'] == x)]['batsman_runs'])
        bbr.append(bat_run)

    r30, r50, r100 = 0, 0, 0
    for m in bbr:
        if m >= 100:
            r100 += 1
        elif m >= 50:
            r50 += 1
        elif m >= 30:
            r30 += 1

    try:
        catches = len(byb[(byb['fielder'] == player) & (
            byb['dismissal_kind'] == 'caught')]) / matches_played
        run_outs = len(byb[(byb['fielder'] == player) & (
            byb['dismissal_kind'] == 'run out')]) / matches_played
        extra_points = (r30 / matches_played) * Batsman_points['30Runs'] + \
                       (r50 / matches_played) * Batsman_points['Half_century'] + \
                       (r100 / matches_played) * Batsman_points['Century'] + \
            catches * Fielding_points['Catch'] + \
            run_outs * Fielding_points['RunOutInd']
    except ZeroDivisionError:
        catches, run_outs, extra_points = 0, 0, 0

    wickets_taken = []
    for x in unq_ids:
        twx = sum(byb[(byb["bowler"] == player) &
                  (byb['id'] == x)]['is_wicket'])
        wickets_taken.append(twx)

    w3, w4, w5 = 0, 0, 0
    for z in wickets_taken:
        if z >= 5:
            w5 += 1
        elif z >= 4:
            w4 += 1
        elif z >= 3:
            w3 += 1

    try:
        lbws = len((byb[(byb['bowler'] == player) & (
            byb['dismissal_kind'] == 'lbw')])) / matches_played
        bowled = len((byb[(byb['bowler'] == player) & (
            byb['dismissal_kind'] == 'bowled')])) / matches_played
        wexp = (w3 / matches_played) * Bowling_points['3W'] + \
               (w4 / matches_played) * Bowling_points['4W'] + \
               (w5 / matches_played) * Bowling_points['5W'] + \
            lbws * Bowling_points['LBW_Bowled'] + \
            bowled * Bowling_points['LBW_Bowled']
    except ZeroDivisionError:
        lbws, bowled, wexp = 0, 0, 0

    ffp = []
    for j in range(len(opponent_team)):
        bat_vs_bowl = byb[(byb["batsman"] == player) &
                          (byb["bowler"] == opponent_team[j])]
        bowls_played = len(bat_vs_bowl.batsman_runs)
        runs_scored = sum(bat_vs_bowl.batsman_runs)
        fours = len(bat_vs_bowl[bat_vs_bowl['batsman_runs'] == 4])
        sixes = len(bat_vs_bowl[bat_vs_bowl['batsman_runs'] == 6])
        wicket = sum(bat_vs_bowl.is_wicket)

        if bowls_played <= 6 * 10 and wicket >= 5:
            penalty = -16
        elif bowls_played <= 6 * 8 and wicket >= 4:
            penalty = -8
        elif bowls_played <= 6 * 6 and wicket >= 3:
            penalty = -4
        else:
            penalty = 0

        try:
            strike_rate = int(runs_scored / bowls_played * 100)
        except ZeroDivisionError:
            strike_rate = 'NA'

        bowl_vs_bat = byb[(byb["bowler"] == player) & (
            byb["batsman"] == opponent_team[j])]
        wicket_took = sum(bowl_vs_bat.is_wicket)
        fantasy_points1 = runs_scored + \
            fours * Batsman_points['bFour'] + \
            sixes * Batsman_points['bSix'] - \
            wicket * Bowling_points['Wicket'] + \
            wicket_took * Bowling_points['Wicket'] + \
            penalty

        ffp.append(fantasy_points1)

    sum_ffp = sum(ffp)

    if player_fp > 0:
        recent_performance_points = np.log(player_fp)
    elif player_fp < 0:
        recent_performance_points = -np.log(abs(player_fp))
    else:
        recent_performance_points = 0

    weight1 = 0.5
    weight2 = 1 - weight1

    final_fantasy_point = (sum_ffp + extra_points + wexp) * \
        weight1 + recent_performance_points * weight2
    final_fantasy_point = round(final_fantasy_point, 2)

    return final_fantasy_point


class TeamSelectionForm(BaseModel):
    team1: str
    team2: str


@app.post('/select_team')
async def handle_team_selection(form_data: TeamSelectionForm):
    user_choice1 = form_data.team1
    user_choice2 = form_data.team2

    # Load team data based on user_choice1 and user_choice2
    if user_choice1 in teams_data:
        Team1_Squad = teams_data[user_choice1]
    else:
        return {'error_message': 'Invalid choice for Team 1.'}

    if user_choice2 in teams_data:
        Team2_Squad = teams_data[user_choice2]
    else:
        return {'error_message': 'Invalid choice for Team 2.'}

    # Further processing like selecting players, calculating fantasy points, etc.
    # Ensure to handle form data and return appropriate responses or render templates

    if not team1 or not team2:
        return {'error_message': 'Please select both teams.'}

    if team1 not in teams_data or team2 not in teams_data:
        return {'error_message': 'Invalid team selection.'}

    players1 = get_players_from_excel(team1)
    players2 = get_players_from_excel(team2)

   # if len(player1) != 11 or len(player2) != 11:
    #    return {'error_message': 'Please select exactly 11 players for both teams.'}

    # Further processing logic for team predictions
    Team1_Squad = teams_data[team1]
    Team2_Squad = teams_data[team2]

    # Assuming you have functions like get_players and prediction logic
    t1 = get_players(player1, player2, Team1_Squad)
    t2 = get_players(player2, player1, Team2_Squad)

    t3 = t1 + t2
    t3.sort(reverse=True)
    Result = pd.DataFrame(t3).head(10)

    predicted_team = Result.to_dict(orient='records')

    return {'predicted_team': predicted_team}


@app.post('/fantasy_points')
async def calculate_fantasy_points(team_selection: TeamSelectionForm):
    team1 = team_selection.team1
    team2 = team_selection.team2

    if team1 not in teams_data or team2 not in teams_data:
        return {'error_message': 'Please select both teams.'}

    players1 = list(teams_data[team1].keys())
    players2 = list(teams_data[team2].keys())

    # if len(players1) != 11 or len(players2) != 11:
    #     return {'error_message': 'Please select exactly 11 players for both teams.'}

    fantasy_points = {}
    for player in players1:
        fantasy_points[player] = calculate_individual_fantasy_points(
            player, players2, teams_data[team1][player], byb)

    for player in players2:
        fantasy_points[player] = calculate_individual_fantasy_points(
            player, players1, teams_data[team2][player], byb)
    sorted_fantasy_points = dict(
        sorted(fantasy_points.items(), key=lambda item: item[1], reverse=True))
    return {'fantasy_points': sorted_fantasy_points}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7004)
