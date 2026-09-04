import numpy as np

# Each movie is represented as a vector of genre "scores"
# [Action, Comedy, Romance, Animation, Horror]  -- adjust to match your real data
movies = {
    "Die hard":   np.array([9, 2, 1, 0, 3]),
    "Notebook":   np.array([1, 2, 9, 0, 0]),
    "Deadpool":   np.array([8, 7, 2, 0, 1]),
    "Toy Story":  np.array([2, 6, 1, 9, 0]),
}


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def recommend(chosen, how_many=3):
    scores = []
    chosen_vector = movies[chosen]

    for title, vector in movies.items():
        if title == chosen:
            continue
        s = cosine_similarity(chosen_vector, vector)
        scores.append((title, s))

    scores.sort(key=lambda pair: pair[1], reverse=True)
    return scores[:how_many]


# quick demo test
print(recommend("Die hard"))
print("Movies i know:", movies.keys())

while True:
    choice = input("Tell me a movie you like: ")

    if choice == "bye":
        break

    if choice not in movies:
        print("I don't know that movie, try again")
        continue

    print("Because you liked", choice, "you might enjoy:")
    for title, score in recommend(choice):
        print("-", title)