def app():
    print("Starting the Flask application...")

def sum(a, b):
    return a + b
def visibles():
    print("This function is visible outside this module.")
    
def not_visibles():
    print("This function is not visible outside this module.") 


def main():
    app()
    print("Flask application" " is running.")

def add_numbers(a, b):
    result = sum(a, b)
    print(f"The sum of {a} and {b} is: {result}")

def subtract_numbers(a, b):
    result = a - b
    print(f"The difference between {a} and {b} is: {result}")   

def multiply_numbers(a, b):
    result = a * b
    print(f"The product of {a} and {b} is: {result}")   

def not_started():
    print("This function is not started yet.")

def started():
    print("This function has started.")
    
def divide_numbers(a, b):
    if b != 0:
        result = a / b
        print(f"The division of {a} by {b} is: {result}")
    else:
        print("Error: Division by zero is not allowed.")

def divide_numbers(a, b):
    if b == 0:
        print("Error: Division by zero is not allowed.")
        return None
    result = a / b
    print(f"The quotient of {a} and {b} is: {result}")
    return result   

if __name__ == "__main__":
    main()
    add_numbers(5, 10)
    subtract_numbers(10, 5)
    multiply_numbers(5, 10)
    divide_numbers(10, 2)       