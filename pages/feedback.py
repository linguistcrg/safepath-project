import streamlit as st
from streamlit_star_rating import st_star_rating

st.set_page_config(page_title="Feedback")

st.write("# We value your feedback!")

<<<<<<< HEAD
# st.markdown(
#     """
#     Streamlit is an open-source app framework built specifically for
#     Machine Learning and Data Science projects.
#     **👈 Select a demo from the sidebar** to see some examples
#     of what Streamlit can do!
#     ### Want to learn more?
#     - Check out [streamlit.io](https://streamlit.io)
#     - Jump into our [documentation](https://docs.streamlit.io)
#     - Ask a question in our [community
#         forums](https://discuss.streamlit.io)
#     ### See more complex demos
#     - Use a neural net to [analyze the Udacity Self-driving Car Image
#         Dataset](https://github.com/streamlit/demo-self-driving)
#     - Explore a [New York City rideshare dataset](https://github.com/streamlit/demo-uber-nyc-pickups)
# """
# )
=======
st.markdown(
    """
    Please help us improve SafePath by sharing your experience with your suggested route.
    You can rate different aspects of your route and leave a review below:
    """
)
>>>>>>> 9b0b805ce70f6b58163a7bc190eca516bea52b57

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