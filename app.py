

from fastapi import FastAPI, HTTPException, Depends, Form, Query, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, constr
from typing import List, Dict
from passlib.context import CryptContext
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uvicorn

# Initialize FastAPI app
app = FastAPI()

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dummy in-memory database
fake_users_db = {}
fake_tokens_db = {}

# Dependency for OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models


class User(BaseModel):
    username: str
    email: EmailStr
    full_name: str = None
    password: str


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str


class TeamSelectionForm(BaseModel):
    team1: str
    team2: str


class PlayerSelectionForm(BaseModel):
    team: str
    players: List[str]


class FantasyPointsResponse(BaseModel):
    player_name: str
    fantasy_points: float


# In-memory user store
users_db = {}


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


# Password hashing
def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# User Authentication


def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if user and verify_password(password, user['password']):
        return user
    return None


def create_access_token(data: dict, expires_delta: timedelta = None):
    # Create a token (dummy implementation)
    return "fake-token"

# Endpoints


@app.post("/register")
async def register(user: User):
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=400, detail="Username already registered")
    if not (user.password and len(user.password) >= 8 and any(c.islower() for c in user.password) and any(c.isupper() for c in user.password) and any(c in '.,@' for c in user.password)):
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters long, contain both lowercase and uppercase letters, and include at least one special character.")
    fake_users_db[user.username] = {
        "username": user.username,
        "hashed_password": hash_password(user.password),
        "email": user.email
    }
    return {"message": "User registered successfully"}


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/select_teams")
async def select_teams(form_data: TeamSelectionForm, token: str = Depends(oauth2_scheme)):
    # Verify token (dummy implementation)
    if token != "fake-token":
        raise HTTPException(status_code=401, detail="Invalid token")

    team1 = form_data.team1
    team2 = form_data.team2

    if team1 not in teams_data or team2 not in teams_data:
        raise HTTPException(status_code=400, detail="Invalid team selection")

    return {"team1": team1, "team2": team2}


@app.post("/select_players")
async def select_players(form_data: PlayerSelectionForm, token: str = Depends(oauth2_scheme)):
    # Verify token (dummy implementation)
    if token != "fake-token":
        raise HTTPException(status_code=401, detail="Invalid token")

    team = form_data.team
    players = form_data.players

    if team not in teams_data:
        raise HTTPException(status_code=400, detail="Invalid team")

    if len(players) != 11:
        raise HTTPException(
            status_code=400, detail="Please select exactly 11 players")

    return {"team": team, "players": players}


@app.post("/calculate_fantasy_points", response_model=List[FantasyPointsResponse])
async def calculate_fantasy_points(request: Request, token: str = Depends(oauth2_scheme)):
    # Verify token (dummy implementation)
    if token != "fake-token":
        raise HTTPException(status_code=401, detail="Invalid token")

    # Here you can call the get_players function and calculate fantasy points
    # For simplicity, returning dummy data
    player_fantasy_points = [
        FantasyPointsResponse(player_name="Player1", fantasy_points=50.0),
        FantasyPointsResponse(player_name="Player2", fantasy_points=45.5),
    ]

    return player_fantasy_points

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
