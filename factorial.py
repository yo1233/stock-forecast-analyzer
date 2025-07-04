def factorial(n):
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

def main():
    try:
        num = int(input("Enter a number: "))
        result = factorial(num)
        print(f"The factorial of {num} is {result}")
    except ValueError as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")

if __name__ == "__main__":
    main()