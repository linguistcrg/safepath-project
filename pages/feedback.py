import streamlit as st
from streamlit_star_rating import st_star_rating

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
)

st.write("# Welcome to Feedback! 👋")

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

st.write("## We value your feedback!")
st.write("Please rate your experience and leave a review below.")

# Rating input using star rating
rating = st_star_rating("Rate your path from 1 to 5 stars:", maxValue=5, defaultValue=1, key="rating")

# Review input
review = st.text_area("Write your review here:")

# Display submitted feedback
if st.button("Submit"):
    st.write("Thank you for your feedback!")
    st.write(f"Rating: {'⭐' * rating}")
    st.write(f"Review: {review}")