# Define a function to generate Fibonacci numbers

def generate_fibonacci(n):
    fibonacci_numbers = []
    a, b = 0, 1
    for _ in range(n):
        fibonacci_numbers.append(a)
        a, b = b, a + b
    return fibonacci_numbers

# Generate the first 20 Fibonacci numbers
fibonacci_list = generate_fibonacci(20)

# Print the Fibonacci numbers to verify
print(fibonacci_list)

# Format the Fibonacci numbers into a markdown list
markdown_output = '\n'.join([f'- {num}' for num in fibonacci_list])

# Write the formatted Fibonacci numbers to a markdown file
output_file = 'fibonacci_numbers.md'
with open(output_file, 'w') as f:
    f.write(markdown_output)