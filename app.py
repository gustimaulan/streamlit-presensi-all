import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import altair as alt

st.set_page_config(
    page_title="Monthly Recap",
    layout="wide"
)

st.title("Sigmath Recap")

@st.cache_data
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)
    return conn.read(worksheet="Presensi", usecols=list(range(5)))

df = load_data()

# Convert "Hari dan Tanggal Les" from dd/mm/yyyy to datetime and sort
df["Hari dan Tanggal Les"] = pd.to_datetime(df["Hari dan Tanggal Les"], format="%d/%m/%Y", errors='coerce')
df = df.sort_values(by="Hari dan Tanggal Les", ascending=False)

# Convert dates back to yyyy/mm/dd format for display
df["Hari dan Tanggal Les"] = df["Hari dan Tanggal Les"].dt.strftime('%Y/%m/%d')

# Extract year and month from the dataframe for filtering
df["Year"] = pd.to_datetime(df["Hari dan Tanggal Les"], format='%Y/%m/%d').dt.year
df["Month"] = pd.to_datetime(df["Hari dan Tanggal Les"], format='%Y/%m/%d').dt.month

# Get current year and month
current_year = datetime.now().year
current_month = datetime.now().month

# Create two columns for year and month selection
col1, col2 = st.sidebar.columns(2)

with col1:
    # Year selection
    year = st.sidebar.selectbox(
        "Select Year",
        list(df["Year"].unique()),
        index=list(df["Year"].unique()).index(current_year)
    )

with col2:
    # Month selection
    month = st.sidebar.selectbox(
        "Select Month",
        list(range(1, 13)),
        index=list(range(1, 13)).index(current_month)
    )

# Filter the DataFrame based on selected year and month
filtered_df = df[
    (df["Year"] == year) &
    (df["Month"] == month)
]

# Create a sidebar filter for selecting "Nama Tentor"
tutors = sorted(filtered_df["Nama Tentor"].unique())  # Sort the list of tutors in ascending order based on filtered data
selected_tutor = st.sidebar.selectbox(
    "Select Tutor",
    options=["All"] + tutors,  # Add "All" option for no filtering
    index=0  # Default to "All"
)

# Further filter by selected tutor
if selected_tutor != "All":
    filtered_df = filtered_df[filtered_df["Nama Tentor"] == selected_tutor].reset_index(drop=True)

# Drop the year and month columns for display
filtered_df = filtered_df.drop(columns=["Year", "Month", "Timestamp"])

# Count entries for each date
date_counts = filtered_df["Hari dan Tanggal Les"].value_counts().sort_index()

# Create a DataFrame for plotting
date_counts_df = pd.DataFrame({
    "Date": date_counts.index,
    "Count": date_counts.values
})

# Calculate counts
total_entries = len(filtered_df)
unique_tutors = filtered_df["Nama Tentor"].nunique()
unique_students = filtered_df["Nama Siswa"].nunique()


# Create three columns for scorecards
col1, col2, col3 = st.columns(3)

with col1:
    entry_label = "Entry" if total_entries == 1 else "Entries"
    st.markdown(f"""
    <div style="
        padding: 10px;
        border: 1px solid rgba(49, 51, 63, 0.1);
        margin-bottom: 20px;
        border-radius: 5px;
        text-align: left;
    ">
        <h4>Total {entry_label}</h4>
        <h2>{total_entries}</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    tutor_label = "Tutor" if unique_tutors == 1 else "Unique Tutors"
    st.markdown(f"""
    <div style="
        padding: 10px;
        border: 1px solid rgba(49, 51, 63, 0.1);
        margin-bottom: 20px;
        border-radius: 5px;
        text-align: left;
    ">
        <h4>{tutor_label}</h4>
        <h2>{unique_tutors}</h2>
    </div>
    """, unsafe_allow_html=True)

with col3:
    student_label = "Student" if unique_students == 1 else "Unique Students"
    st.markdown(f"""
    <div style="
        padding: 10px;
        border: 1px solid rgba(49, 51, 63, 0.1);
        margin-bottom: 20px;
        border-radius: 5px;
        text-align: left;
    ">
        <h4>{student_label}</h4>
        <h2>{unique_students}</h2>
    </div>
    """, unsafe_allow_html=True)


# Check if filtered_df is empty and handle accordingly
if filtered_df.empty:
    st.write("No data available for the selected filters.")
else:
    filtered_df = filtered_df.reset_index(drop=True)
    filtered_df = filtered_df[["Hari dan Tanggal Les", "Nama Tentor", "Nama Siswa", "Jam Kegiatan Les"]]
    # Drop the unnecessary columns and reset the index, starting from 1
    filtered_df = filtered_df.rename(columns={
        "Hari dan Tanggal Les": "Date",
        "Nama Tentor": "Tutor",
        "Nama Siswa": "Student",
        "Jam Kegiatan Les": "Time",
    })

    # Set the index to start from 1
    filtered_df.index += 1
    st.dataframe(filtered_df, height=380, use_container_width=True)

# Create the base bar chart
bar_chart = alt.Chart(date_counts_df).mark_bar().encode(
    x=alt.X('Date:T', title='Date', axis=alt.Axis(format='%d')),
    y=alt.Y('Count:Q', title='Count', axis=alt.Axis(format='d')),  # Ensure integer formatting
    tooltip=['Date:T', 'Count:Q']
)

# Create the text layer for data labels
text_labels = bar_chart.mark_text(
    align='center',  # Center the text horizontally
    baseline='middle',  # Center the text vertically
    dy=-10,  # Adjust the vertical position of the text
    color='gray'
).encode(
    text='Count:Q'  # Display the count as text
)

# Combine the bar chart and text labels into one chart
chart_with_labels = bar_chart + text_labels

# Add a title and display the chart
chart_with_labels = chart_with_labels.properties(
    title='Number of Entries per Date'
)

st.markdown("---")

# Display the bar chart
st.altair_chart(chart_with_labels, use_container_width=True)

st.markdown("---")

date_counts_df["Day of Week"] = pd.to_datetime(date_counts_df["Date"]).dt.day_name()

# Step 2: Group by the Day of the Week and count entries
day_counts_df = date_counts_df.groupby("Day of Week").agg({'Count': 'sum'}).reset_index()

# Step 3: Ensure all days of the week are represented
# Create a complete list of days
days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
full_day_df = pd.DataFrame(days_of_week, columns=["Day of Week"])

# Merge with your existing data
day_counts_df = full_day_df.merge(day_counts_df, on="Day of Week", how="left").fillna(0)

# Convert the 'Count' column to integer for proper display
day_counts_df["Count"] = day_counts_df["Count"].astype(int)

# Step 4: Create the base bar chart
bar_chart = alt.Chart(day_counts_df).mark_bar().encode(
    x=alt.X('Day of Week:O', title='Day of the Week', sort=days_of_week),
    y=alt.Y('Count:Q', title='Count', axis=alt.Axis(format='d')),  # Ensure integer formatting
    tooltip=['Day of Week:O', 'Count:Q']
)

# Create the text layer for data labels
text_labels = bar_chart.mark_text(
    align='center',  # Center the text horizontally
    baseline='middle',  # Center the text vertically
    dy=-10,  # Adjust the vertical position of the text
    color='gray'   
).encode(
    text='Count:Q'  # Display the count as text
)

# Combine the bar chart and text labels into one chart
chart_with_labels = bar_chart + text_labels

# Add a title and display the chart
chart_with_labels = chart_with_labels.properties(
    title='Number of Entries per Day of the Week'
)

st.altair_chart(chart_with_labels, use_container_width=True)


# Convert "Jam Kegiatan Les" from HH:MM:SS to HH:MM for heatmap processing
df["Jam Kegiatan Les"] = pd.to_datetime(df["Jam Kegiatan Les"], format="%H:%M:%S").dt.strftime('%H:%M')

# Filter the DataFrame again for heatmap processing
heatmap_df = df[
    (df["Year"] == year) &
    (df["Month"] == month)
]

