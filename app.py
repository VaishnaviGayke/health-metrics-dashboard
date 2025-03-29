from flask import Flask, render_template, request
import pandas as pd
import plotly.express as px
import plotly.io as pio
import requests

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def dashboard():
    # Read selected filters from query params
    selected_continent = request.args.get('continent')
    selected_country = request.args.get('country')

    # Fetch COVID-19 data
    response = requests.get("https://disease.sh/v3/covid-19/countries")
    if response.status_code != 200:
        return f"Error fetching data: {response.status_code}"

    data = response.json()

    # Convert to DataFrame
    df = pd.DataFrame([{
        "Country": country["country"],
        "Continent": country["continent"],
        "Cases": country["cases"],
        "Deaths": country["deaths"],
        "Recovered": country["recovered"]
    } for country in data])

    # Apply filters
    if selected_continent:
        df = df[df["Continent"] == selected_continent]
    if selected_country:
        df = df[df["Country"] == selected_country]

    # Get top 10 for display
    df_top10 = df.sort_values(by="Cases", ascending=False).head(10)

    # Bar chart
    fig_bar = px.bar(df_top10, x="Country", y="Cases", color="Deaths",
                     title="Top 10 Countries by COVID-19 Cases",
                     hover_data=["Recovered"])

    # Pie chart for deaths
    fig_pie = px.pie(df_top10, values="Deaths", names="Country", title="Death Distribution")

     # PIE CHART: Breakdown of a single country
    chart_pie = ""
    if selected_country and len(df) == 1:
        country_row = df.iloc[0]
        pie_data = pd.DataFrame({
            "Category": ["Active Cases", "Recovered", "Deaths"],
            "Count": [
                country_row["Cases"] - country_row["Recovered"] - country_row["Deaths"],
                country_row["Recovered"],
                country_row["Deaths"]
            ]
        })

        fig_pie = px.pie(
            pie_data,
            names="Category",
            values="Count",
            title=f"COVID-19 Case Breakdown in {selected_country}"
        )

        chart_pie = pio.to_html(fig_pie, full_html=False)
        
    # Convert charts to HTML
    chart_bar = pio.to_html(fig_bar, full_html=False)
    chart_pie = pio.to_html(fig_pie, full_html=False)

    # LINE CHART (Only if a single country is selected)
    chart_line = ""
    if selected_country:
        try:
            timeline_response = requests.get(
                f"https://disease.sh/v3/covid-19/historical/{selected_country}?lastdays=30"
            )
            if timeline_response.status_code == 200:
                timeline_data = timeline_response.json()
                cases_timeline = timeline_data["timeline"]["cases"]
                df_timeline = pd.DataFrame(list(cases_timeline.items()), columns=["Date", "Cases"])
                df_timeline["Date"] = pd.to_datetime(df_timeline["Date"])

                fig_line = px.line(df_timeline, x="Date", y="Cases",
                                   title=f"Daily COVID-19 Cases in {selected_country}")
                chart_line = pio.to_html(fig_line, full_html=False)
        except Exception as e:
            chart_line = f"<p>Error loading timeline for {selected_country}: {str(e)}</p>"

    # Dropdown lists
    continents = sorted(df["Continent"].dropna().unique())
    countries = sorted(df["Country"].unique())

    return render_template("dashboard.html",
                           chart_bar=chart_bar,
                           chart_pie=chart_pie,
                           chart_line=chart_line,
                           continents=continents,
                           countries=countries,
                           selected_continent=selected_continent,
                           selected_country=selected_country)

if __name__ == '__main__':
    app.run(debug=True)
