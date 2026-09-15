# hours studied  ->  exam score 
hours  = [1, 2, 3, 4, 5] 
scores = [52, 58, 62, 71, 78] 
for h, s in zip(hours, scores):    
 print(h, "hours ->", s, "score")
 m = 6      # slope: score goes up ~6 per hour (a guess)
 c = 46     # intercept: score at 0 hours (a guess)
 def predict(x):
    return m * x + c 
 print("Predict 3 hours:", predict(3)) 
 print("Predict 5 hours:", predict(5))
 import matplotlib.pyplot as plt 
 hours  = [1, 2, 3, 4, 5] 
 scores = [52, 58, 62, 71, 78] 
 m, c = 6, 46 
 plt.scatter(hours, scores)                 # real data as dots 
 line_y = [m*x + c for x in hours] 
 plt.plot(hours, line_y, color="red")       # your line 
 plt.xlabel("Hours"); plt.ylabel("Score") 
 plt.show()
 def predict(x, m, c):    
   return m * x + c 
 real = 62
 guess = predict(3, 6, 46)   # predict 3 hours 
 error = guess - real 
 print("Guess:", guess, "Real:", real, "Error:", error)
 errors = [2, -3, 5, -1] 
 print("Just added (misleading):", sum(errors)) 
 squared = [e*e for e in errors] 
 print("Squared (honest):", squared) 
 print("Sum of squared:", sum(squared))
 hours  = [1, 2, 3, 4, 5] 
 scores = [52, 58, 62, 71, 78] 
 def loss(m, c):    
    total = 0    
    for x, real in zip(hours, scores):        
        guess = m * x + c        
        total = total + (guess - real) ** 2    
    return total / len(hours) 
print("Loss for m=6, c=46:", loss(6, 46)) 
print("Loss for m=2, c=50:", loss(2, 50))
def gradients(m, c):    
    grad_m = 0    
    grad_c = 0    
    n = len(hours)    
    for x, real in zip(hours, scores):       
         error = (m * x + c) - real        
         grad_m = grad_m + 2 * error * x        
         grad_c = grad_c + 2 * error    
    return grad_m / n, grad_c / n
m, c = 0, 0          
learning_rate = 0.01 
gm, gc = gradients(m, c)
m = m - learning_rate * gm
c = c - learning_rate * gc
print("After one step: m =", round(m,3), "c =", round(c,3))
m, c = 0, 0 
learning_rate = 0.01 
for step in range(1000):    
    gm, gc = gradients(m, c)   
    m = m - learning_rate * gm    
    c = c - learning_rate * gc    
    if step % 200 == 0:        
       print("step", step, "loss", round(loss(m, c), 2)) 
print("Learned line: m =", round(m,2), "c =", round(c,2))
train_hours  = [1, 2, 3, 4]
train_scores = [52, 58, 62, 71] 
test_hours   = [5]  
test_scores  = [78] 
while True:    
    text = input("Enter hours (or quit): ")    
    if text == "quit":        
        break    
    x = float(text)    
    print("Predicted score:", round(m * x + c, 1))         # kept hidden during training