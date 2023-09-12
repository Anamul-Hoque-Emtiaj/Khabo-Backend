import pandas as pd
import openai
import time
import ast

# Load your DALL-E API key
openai.api_key = "my_api_key"
c = 1
# Function to generate image paths using DALL-E with rate limiting
def generate_image_path_with_rate_limit(row):
    global c
    ingredients = ast.literal_eval(row['ingredients'])
    merged_ingredients = ""
    for ingredient in ingredients:
        merged_ingredients += ingredient + ","
    
    prompt = f"Make an image of recipe titled {row['title']} using ingredients: {merged_ingredients}"
    # Control rate of API calls
    try:
        # Control rate of API calls
        while True:
            # Get the current timestamp
            current_time = time.time()

            # Check if it's been at least 20 seconds since the last request
            if 'last_request_time' in generate_image_path_with_rate_limit.__dict__:
                elapsed_time = current_time - generate_image_path_with_rate_limit.last_request_time
                if elapsed_time < 30:
                    # Wait for the remaining time to reach 20 seconds
                    time.sleep(30 - elapsed_time)

            response = openai.Image.create(prompt=prompt, n=1, size="1024x1024")
            # Update the last request time
            generate_image_path_with_rate_limit.last_request_time = time.time()
            print(c,response['data'][0]['url'])
            c+=1
            return response['data'][0]['url']
    except Exception as e:
        # If an error occurs, return the prompt
        print(f"Error: {str(e)} for prompt: {prompt} {c}")
        return prompt

# Read the original CSV file
df = pd.read_csv('dataset1.csv')

# Add a new column 'image_path' using the DALL-E API with rate limiting and error handling
df['image_path'] = df.apply(generate_image_path_with_rate_limit, axis=1)

# Save the updated DataFrame to a new CSV file
df.to_csv('dataset1_with_img.csv', index=False)
