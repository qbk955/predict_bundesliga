# utils/helpers.py

import os
import base64
import streamlit as st
import plotly.graph_objects as go

def get_base64_encoded_image(image_path):
    """
    Encode an image to a base64 string.
    """
    try:
        with open(image_path, 'rb') as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
        return encoded_string
    except FileNotFoundError:
        st.warning(f"Image not found at path: {image_path}")
        return None

def get_team_logo_path(team_name):
    """
    Get the path to a team's logo image.
    """
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_filename = f"{team_name}.png"
    logo_path = os.path.join(script_dir, '..', 'logos', logo_filename)
    return logo_path

def local_css():
    """
    Inject custom CSS into the Streamlit app.
    """
    st.markdown(
        """
        <style>
        .team-logo {
            height: 150px;          /* Set a fixed height */
            width: auto;            /* Maintain aspect ratio */
            display: block;         /* Ensure block-level element */
            margin-left: auto;      /* Center the image horizontally */
            margin-right: auto;
            object-fit: contain;    /* Scale the image to fit within the container */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def create_radar_chart(team_a_stats, team_b_stats, team_a_name, team_b_name, min_salary, max_salary):
    """
    Creates a radar chart comparing statistics of two teams.
    """
    categories = list(team_a_stats.keys())

    # Normalize the values to a 0-100 scale
    max_values = {
        "Overall": 100,
        "Attack": 100,
        "Midfield": 100,
        "Defense": 100,
        "avg Goals Scored last 4 games": 6,        # Adjust based on realistic maximums
        "avg xG last 4 games": 6,               # Adjust based on realistic maximums
        "avg Possession last 4 games": 100,
        "Salary Level": 100     # Since we normalize to 0-100
    }

    # Normalize stats for both teams
    def normalize_stats(stats):
        normalized = []
        for category in categories:
            value = stats.get(category, 0)  # Use .get to handle missing keys
            if category == 'Salary Level':
                # Use Min-Max Normalization for Salary Level
                normalized_value = ((value - min_salary) / (max_salary - min_salary)) * 100
                normalized_value = max(0, min(normalized_value, 100))  # Clamp between 0 and 100
            else:
                max_value = max_values.get(category, 100)
                normalized_value = (value / max_value) * 100
                normalized_value = max(0, min(normalized_value, 100))  # Clamp between 0 and 100
            normalized.append(normalized_value)
        return normalized

    team_a_values = normalize_stats(team_a_stats)
    team_b_values = normalize_stats(team_b_stats)

    # Close the loop for the radar chart
    team_a_values += team_a_values[:1]
    team_b_values += team_b_values[:1]
    categories += categories[:1]

    fig = go.Figure()

    # Add Team A to the radar chart
    fig.add_trace(go.Scatterpolar(
        r=team_a_values,
        theta=categories,
        fill='toself',
        name=team_a_name,
        line_color='blue',
        opacity=0.7
    ))

    # Add Team B to the radar chart
    fig.add_trace(go.Scatterpolar(
        r=team_b_values,
        theta=categories,
        fill='toself',
        name=team_b_name,
        line_color='red',
        opacity=0.7
    ))

    # Update layout for better readability
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont_size=12,
                showline=True,
                linewidth=1,
                gridcolor='gray',
                gridwidth=0.5
            ),
            angularaxis=dict(
                tickfont_size=12
            )
        ),
        legend=dict(
            font_size=14,
            orientation="h",
            yanchor="bottom",
            y=1.1,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=50, r=50, t=50, b=50)
    )
    return fig