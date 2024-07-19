## PROJECT OVERVIEW :

This FastAPI application helps you select a fantasy cricket team based on player performance and predefined scoring criteria. It calculates fantasy points for players and predicts the best team lineup.

## Features
Selects teams based on user input.
Calculates fantasy points for players.
Predicts the best team lineup.
Provides endpoints to fetch teams and players data.
## Requirements
Python 3.7+
FastAPI
Pydantic
Pandas
Numpy
Uvicorn (for running the application)

## Endpoints
1. /select_team
Method: POST

Description: Handles team selection and prediction logic.

Request Body:

team1: The first team selected by the user.
team2: The second team selected by the user.
Response:

predicted_team: List of players with their predicted fantasy points.
Example:

json

{
    "team1": "team1",
    "team2": "team2"
}
2. /teams
Method: GET

Description: Returns the available teams.

Response:

teams: List of available teams.

3. /players/{team}
Method: GET

Description: Returns the players of a specified team.

Path Parameter:

team: The team for which to fetch players.
Response:

players: List of players in the specified team.
