# app.py

import streamlit as st
import pandas as pd
import joblib
import os
import plotly.graph_objects as go
from utils.gsheets import init_gsheets, load_scoreboard, save_scoreboard
from utils.helpers import get_base64_encoded_image, get_team_logo_path, local_css, create_radar_chart

# Set page configuration to wide layout
st.set_page_config(layout="wide")
# Apply custom CSS
local_css()



# Load data and modelss
def load_resources():
    """
    Load the Bundesliga match data and the trained model.
    """
    try:
        df = pd.read_csv('data/bundesliga_matches.csv')
    except FileNotFoundError:
        st.error("Data file 'bundesliga_matches.csv' not found in 'data/' directory.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()
    
    try:
        model = joblib.load('data/best_lr_model.pkl')
    except FileNotFoundError:
        st.error("Model file 'best_lr_model.pkl' not found in 'data/' directory.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading model: {e}")
        st.stop()
    
    return df, model

# Initialize session state
def initialize_session_state():
    if 'game_started' not in st.session_state:
        st.session_state.game_started = False
        st.session_state.current_game_finished = False
        st.session_state.user_score = 0
        st.session_state.username = ""
        st.session_state.random_game = None
        st.session_state.round_count = 0  # Add a counter for rounds
        st.session_state.user_prediction = None  # Store user prediction
    if 'score_added' not in st.session_state:
        st.session_state.score_added = False  # Flag to prevent duplicate entries

# Function to select a random game
def get_random_game(df):
    return df.sample(1).iloc[0]

# Start the game
def start_game(username, df):
    st.session_state.username = username
    st.session_state.random_game = get_random_game(df)
    st.session_state.game_started = True
    st.session_state.current_game_finished = False
    st.session_state.round_count = 1  # Start with the first round
    st.session_state.score_added = False  # Reset score_added flag

def evaluate_prediction(user_choice, df, model):
    st.session_state.user_prediction = user_choice
    random_game = st.session_state.random_game
    model_input_df = pd.DataFrame([random_game[model_features]], columns=model_features)

    # Get model prediction and extract the scalar value
    model_prediction = model.predict(model_input_df)[0]

    real_result = random_game['result']  # 'W' for Win, 'L' for Loss, 'D' for Draw

    # Convert model prediction to a label
    model_prediction_label = 'Win' if model_prediction == 1 else 'Not Win'
    real_result_label = 'Win' if real_result == 'W' else 'Not Win'  # Treat 'L' and 'D' as 'Not Win'

    # Store predictions in session state
    st.session_state.model_prediction_label = model_prediction_label
    st.session_state.user_prediction_label = user_choice
    st.session_state.result_real_result = f"The real result: Team **{random_game['team']}** did **{real_result_label}** the game!"

    # Determine correctness
    user_correct = (st.session_state.user_prediction_label == real_result_label)
    model_correct = (st.session_state.model_prediction_label == real_result_label)

    # Update score logic and messages
    if user_correct and not model_correct:
        st.session_state.user_score += 1
        st.session_state.result_score_message = "Congratulations! You predicted correctly and the model was wrong. You get 1 point!"
        st.balloons()
    elif not user_correct and model_correct:
        st.session_state.user_score -= 1
        st.session_state.result_score_message = "The model predicted correctly, but you were wrong. You lose 1 point."
    elif user_correct and model_correct:
        st.session_state.result_score_message = "Both you and the model predicted correctly. No points awarded."
    else:
        st.session_state.result_score_message = "Both you and the model predicted incorrectly. No points awarded."

    # Mark the current game as finished
    st.session_state.current_game_finished = True

# Callback functions for buttons
def next_match():
    st.session_state.random_game = get_random_game(df)
    st.session_state.current_game_finished = False
    st.session_state.round_count += 1
    st.session_state.score_added = False  # Reset score_added flag for the new round

def predict_win():
    evaluate_prediction('Win', df, model)

def predict_not_win():
    evaluate_prediction('Not Win', df, model)

# Helper function to display team info (name and logo)
def display_team_info(team_name):
    logo_path = get_team_logo_path(team_name)
    logo_image = get_base64_encoded_image(logo_path)
    if logo_image:
        st.markdown(f"""
            <div style="text-align: center;">
                <h2>{team_name}</h2>
                <img class="team-logo" src="data:image/png;base64,{logo_image}" alt="{team_name} Logo">
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style="text-align: center;">
                <h2>{team_name}</h2>
                <p>Logo not found for {team_name}</p>
            </div>
        """, unsafe_allow_html=True)

# Display landing page content
def landing_page(scoreboard):
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Adjust the file extension and MIME type
    logo_path = os.path.join(script_dir, 'logos', 'Bundesliga Logo.gif')
    mime_type = 'image/gif'  # Set MIME type for GIF

    # CSS to center the landing page content
    st.markdown(
        """
        <style>
        .landing-page {
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Begin the landing page container
    st.markdown('<div class="landing-page">', unsafe_allow_html=True)

    # Display the Bundesliga logo at the top and center it
    logo_image = get_base64_encoded_image(logo_path)
    if logo_image:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <img src="data:{mime_type};base64,{logo_image}" width="300" />
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown("<p style='text-align: center;'>Bundesliga Logo not found.</p>", unsafe_allow_html=True)

    # Center the title
    st.markdown("<h1 style='text-align: center;'>Welcome to the Bundesliga Prediction Game!</h1>", unsafe_allow_html=True)

    # Style the rules section
    st.markdown("""
    <style>
    .rule-list {
        font-size: 16px;
        margin-left: 20px;
    }
    </style>

    ### Game Rules:

    **Objective:**  
    Your goal is to outsmart the prediction model! You will be shown key statistics (some of the statistics are scaled for readability purposes) from real Bundesliga matches, and based on these, you'll have to predict whether **Team A** will win or **not win**. But be careful – the model will also make its own predictions!

    **Game Flow:**
    1. You will play **5 rounds**. In each round, a random game will be selected, and you'll see statistics for **Team A** and their opponent.
    2. For each match, you'll need to decide if **Team A** will win or **not win**. The model will also predict the outcome.
    3. After each round, you’ll find out:
        - **The real result** of the game.
        - **What the model predicted**.
        - **Whether you guessed correctly**.
    
    **Scoring System:**
    - If you predict **correctly** and the model is **wrong**, you earn **+1 point**.
    - If you predict **incorrectly** and the model is **right**, you lose **-1 point**.
    - If both you and the model guess correctly or both guess wrong, **no points are awarded**.

    """, unsafe_allow_html=True)

    # Username input with placeholder
    username = st.text_input("Enter your username:", key='username_input', placeholder='Type your username here...')

    # Display 'Start the Game' button and handle click
    if st.button("Start the Game", type='primary'):
        if username == "":
            st.error("You must enter a username to start the game.")
        elif 'Username' not in scoreboard.columns:
            st.error("Scoreboard is improperly configured. Please contact the administrator.")
        elif username in scoreboard['Username'].values:
            st.warning(f"The username '{username}' is already taken. Please choose another one.")
        else:
            start_game(username, df)

    # End the landing page container
    st.markdown('</div>', unsafe_allow_html=True)

# Display game content
def game_page():
    st.write(f"Round {st.session_state.round_count} of 5")

    random_game = st.session_state.random_game

    if st.session_state.current_game_finished:
        display_results()
        if st.session_state.round_count < 5:
            st.button("Next Match", on_click=next_match)
        else:
            display_final_results()
    else:
        # Display game stats and prediction buttons
        display_game_stats(random_game)

# Display game statistics
def display_game_stats(random_game):
    # Title for the match
    st.subheader(f"{random_game['team']} vs {random_game['opponent']}")

    # Create three columns with adjusted widths
    col1, col2, col3 = st.columns([3, 2, 3])  # Adjust widths as needed

    # Left Column - Team A Info
    with col1:
        display_team_info(random_game['team'])
        # Add prediction button under team logo, centered
        if not st.session_state.current_game_finished:
            col1_empty1, col1_button, col1_empty2 = st.columns([1, 2, 1])
            with col1_button:
                st.button(
                    f"🟢 Predict {random_game['team']} to Win the game",
                    on_click=predict_win,
                    key='predict_win_button'
                )

    # Middle Column - Game Information
    with col2:
        st.markdown("""
            <div style="text-align: center;">
                <h2>Game Information</h2>
                <p><strong>Venue:</strong> {venue}</p>
                <p><strong>Date:</strong> {date}</p>
                <p><strong>Referee:</strong> {referee}</p>
                <p><strong>Round:</strong> {round}</p>
            </div>
        """.format(
            venue=random_game['venue'],
            date=random_game['date'],
            referee=random_game['referee'],
            round=random_game['round']
        ), unsafe_allow_html=True)

    # Right Column - Opponent Info
    with col3:
        display_team_info(random_game['opponent'])
        # Add prediction button under opponent logo, centered
        if not st.session_state.current_game_finished:
            col3_empty1, col3_button, col3_empty2 = st.columns([1, 2, 1])
            with col3_button:
                st.button(
                    f"🔴 Predict {random_game['opponent']} to Win or Draw",
                    on_click=predict_not_win,
                    key='predict_not_win_button'
                )

    # Prepare stats for the radar chart
    team_a_stats = {
        "Overall": random_game["team_overall"],
        "Attack": random_game["team_attack"],
        "Midfield": random_game["team_midfield"],
        "Defense": random_game["team_defense"],
        "avg Goals Scored last 4 games": random_game["gf_last_4_games"],
        "avg xG last 4 games": random_game["xg_last_4_games"],
        "avg Possession last 4 games": random_game["poss_last_4_games"],
        "Salary Level": random_game["team_salary"]
    }

    opponent_stats = {
        "Overall": random_game["opponent_overall"],
        "Attack": random_game["opponent_attack"],
        "Midfield": random_game["opponent_midfield"],
        "Defense": random_game["opponent_defense"],
        "avg Goals Scored last 4 games": random_game["opponent_gf_last_4_games"],
        "avg xG last 4 games": random_game["opponent_xg_last_4_games"],
        "avg Possession last 4 games": random_game["opponent_poss_last_4_games"],
        "Salary Level": random_game["opponent_team_salary"]
    }

    # Create and display the combined radar chart
    fig = create_radar_chart(
        team_a_stats,
        opponent_stats,
        random_game['team'],
        random_game['opponent'],
        min_salary,
        max_salary
    )
    st.plotly_chart(fig, use_container_width=True)

# Display results after a prediction
def display_results():
    st.subheader("Results")
    
    # Display match information
    if st.session_state.random_game is not None:
        team_a = st.session_state.random_game['team']
        team_b = st.session_state.random_game['opponent']
        st.markdown(f"### Match: **{team_a}** vs **{team_b}**")
    else:
        st.markdown("### Match information not available.")
    
    # Create columns for better layout
    col1, col2 = st.columns([1, 1])

    # Column 1: User's Prediction
    with col1:
        st.markdown("### Your Prediction:")
        if st.session_state.user_prediction_label == 'Win':
            st.markdown("<h3 style='color: green;'>Win</h3>", unsafe_allow_html=True)
        else:
            st.markdown("<h3 style='color: red;'>Not Win</h3>", unsafe_allow_html=True)

    # Column 2: Model's Prediction
    with col2:
        st.markdown("### Model's Prediction:")
        if st.session_state.model_prediction_label == 'Win':
            st.markdown("<h3 style='color: blue;'>Win</h3>", unsafe_allow_html=True)
        else:
            st.markdown("<h3 style='color: orange;'>Not Win</h3>", unsafe_allow_html=True)

    # Real Game Result
    st.markdown("### Real Game Result:")
    st.write(st.session_state.result_real_result)

    # Use message functions for feedback
    if "Congratulations" in st.session_state.result_score_message:
        st.success(st.session_state.result_score_message)
    elif "lose 1 point" in st.session_state.result_score_message:
        st.error(st.session_state.result_score_message)
    else:
        st.info(st.session_state.result_score_message)

    # Correctly display the current score (no recalculation or overwriting)
    st.markdown(f"### Your Current Score: **{st.session_state.user_score}**")

# Display final results after 5 rounds
def display_final_results():
    st.subheader("Game Over!")
    st.write(f"Thanks for playing, {st.session_state.username}!")
    st.write(f"Your final score after 5 rounds: **{st.session_state.user_score}**")

    # Add player to scoreboard only once
    if not st.session_state.score_added:
        scoreboard = load_scoreboard(sheet)
        new_row = pd.DataFrame({'Username': [st.session_state.username], 'Score': [st.session_state.user_score]})
        scoreboard = pd.concat([scoreboard, new_row], ignore_index=True)
        save_scoreboard(sheet, scoreboard)
        st.session_state.score_added = True
    else:
        # Load the updated scoreboard
        scoreboard = load_scoreboard(sheet)

    # Sort the scoreboard descending by 'Score'
    sorted_scoreboard = scoreboard.sort_values(by='Score', ascending=False).reset_index(drop=True)

    # Display the sorted scoreboard
    st.write("### Scoreboard")
    st.table(sorted_scoreboard)

    if st.button("Start a New Game"):
        # Reset session state variables
        st.session_state.game_started = False
        st.session_state.current_game_finished = False
        st.session_state.user_score = 0
        st.session_state.round_count = 0
        st.session_state.username = ""
        st.session_state.random_game = None
        st.session_state.user_prediction = None
        st.session_state.score_added = False

# Display the scoreboard (if needed elsewhere)
def display_scoreboard(scoreboard):
    st.write("### Scoreboard")
    # Sort and display the scoreboard
    scoreboard = scoreboard.sort_values(by='Score', ascending=False).reset_index(drop=True)
    st.table(scoreboard)

# Load resources
df, model = load_resources()

# Initialize Google Sheets
sheet = init_gsheets()

# Load scoreboard from Google Sheets
scoreboard = load_scoreboard(sheet)

# Initialize session state
initialize_session_state()

# Calculate min and max salaries for normalization
min_salary = df[['team_salary', 'opponent_team_salary']].min().min()
max_salary = df[['team_salary', 'opponent_team_salary']].max().max()

# Define model features
model_features = [
    "team_overall", "team_attack", "team_midfield", "team_defense",
    "opponent_overall", "opponent_attack", "opponent_midfield", "opponent_defense",
    "gf_last_4_games", "ga_last_4_games", "xg_last_4_games", "xga_last_4_games",
    "avg_points_last_4_games", "sh_last_4_games", "sot_last_4_games", "poss_last_4_games",
    "opponent_gf_last_4_games", "opponent_ga_last_4_games", "opponent_xga_last_4_games",
    "opponent_avg_points_last_4_games", "team_salary", "opponent_team_salary", "hour",
    "venue", "day", "home_team_formation", "away_team_formation", "captain", "opponent_captain", "referee"
]

# Start the app logic
if not st.session_state.game_started:
    landing_page(scoreboard)
else:
    game_page()
