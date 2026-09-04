import streamlit as st
from recommender import recommend, movies

st.set_page_config(page_title="Movie Recommender", page_icon="🎬")

st.title("🎬 Smart Movie Recommender")
st.write("Pick a movie you like and get similar recommendations based on cosine similarity.")

movie_list = list(movies.keys())
choice = st.selectbox("Choose a movie you like:", movie_list)

how_many = st.slider("How many recommendations?", min_value=1, max_value=10, value=3)

if st.button("Recommend"):
    results = recommend(choice, how_many=how_many)
    st.subheader(f"Because you liked **{choice}**, you might enjoy:")
    for title, score in results:
        st.write(f"- **{title}** — similarity score: {score}")

st.divider()
st.caption("All movies in the system: " + ", ".join(movie_list))
# In recommender.py, wrap your existing while-loop section like this:

if __name__ == "__main__":
    print("Movies i know:", movies.keys())
    while True:
        choice = input("Tell me a movie you like:")
        if choice == "bye":
            break
        if choice not in movies:
            print("I don't know that movie, try again")
            continue
        print("Because you liked", choice, "you might enjoy:")
        for title, score in recommend(choice):
            print("-", title)

# Everything ABOVE this (movies dict, cosine_similarity, recommend function)
# should stay unindented at the top of the file, outside this block.