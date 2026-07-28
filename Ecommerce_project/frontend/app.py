def app():
    print("Starting the Flask application...")

def sum(a, b):
    return a + b

def main():
    app()
    print("Flask application is running.")

def add_numbers(a, b):
    result = sum(a, b)
    print(f"The sum of {a} and {b} is: {result}")

if __name__ == "__main__":
    main()
    add_numbers(5, 10)