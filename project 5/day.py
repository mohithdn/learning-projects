fruits = ["apple", "banana", "cherry"]
print(fruits)
print(fruits[0]) 
print(fruits[1])
fruits.append("orange") 
print(fruits) 
print("Number of fruits:", len(fruits))
questions = ["what is 2+2?","what colour is the sky?"]
for q in questions:
    answer = input(q + " ")
    print("You said:", answer)
capital = {"France": "Paris", "Japan": "Tokyo"}
print(capital["France"])
print(capital["Japan"])
q1 = {"question": "What is 2 + 2?", "answer": "4"}
print(q1["question"])
print("Correct answer is:", q1["answer"])
questions = [   
    {"question": "What is 2 + 2?", "answer": "4"}, 
    {"question": "Capital of Japan?", "answer": "Tokyo"},
    {"question": "How many days in a week?", "answer": "7"}
]
print("First question:", questions[0]["question"])
print("Its answer:", questions[0]["answer"])
for item in questions:
     user_answer = input(item["question"] + " ")    
     if user_answer == item["answer"]:        
         print("Correct!")   
     else:        
        print("Wrong. The answer was", item["answer"])