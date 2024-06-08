import streamlit as st
from streamlit_star_rating import st_star_rating

st.set_page_config(page_title="Feedback")

st.write("# We value your feedback!")

st.markdown(
    """
    Please help us improve SafePath by sharing your experience with your suggested route.
    You can rate different aspects of your route and leave a review below:
    """
)

# Rating input

safety_rating = st_star_rating(label="Feeling of safety", maxValue=5, defaultValue=3, key="easiness_rating", emoticons=True)
lighting_rating = st_star_rating(label="Number of street lights", maxValue=5, defaultValue=3, key="lighting_rating", emoticons=True)
speed_rating = st_star_rating(label="Travel time", maxValue=5, defaultValue=3, key="speed_rating", emoticons=True)
overall_rating = st_star_rating(label="Overall experience", maxValue=5, defaultValue=3, key="overall_rating", emoticons=True)

# Review input
review = st.text_area("Write your review here:")

# Display submitted feedback
if st.button("Submit"):
    st.write("Thank you for your feedback!")
    st.write(f"Feeling of safety: {safety_rating}")
    st.write(f"Number of street lights: {lighting_rating}")
    st.write(f"Travel time: {speed_rating}")
    st.write(f"Overall experience: {overall_rating}")
    st.write(f"Review: {review}")