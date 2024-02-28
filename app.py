import streamlit as st
import sqlite3
import json

# Importing generative model related packages
import google.generativeai as genai

# Initialize SQLite database
conn = sqlite3.connect('blogs.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS blogs (title TEXT, content TEXT)''')
conn.commit()
conn.close()

# Configure GenerativeAI with API key
GOOGLE_API_KEY = "YOUR_API_KEY" # Provide your API key here
genai.configure(api_key=GOOGLE_API_KEY)

# Function to add a new blog to the database
def add_blog(title, content):
    conn = sqlite3.connect('blogs.db')
    c = conn.cursor()
    c.execute("INSERT INTO blogs (title, content) VALUES (?, ?)", (title, content))
    conn.commit()
    conn.close()

# Function to generate blog titles and content
def generate_blogs(user_request):
    model = genai.GenerativeModel('gemini-pro')

    base_prompt = """
    I want you to act as an experienced blog writer. The user will provide you with a prompt. Your task is to generate a list of blog titles from that prompt. The blogs titles should be on latest trends in the relevant topic given by the user. Please ensure that your response is in valid JSON format for easy parsing.
    You may use the following example as a guide

    {
      "blog 1" : 
      {
        "title": "AI and the Job Market: Friend or Foe? Navigating the Robot Revolution",
        "description": "There's no denying the anxiety AI inspires. Jobs once thought secure – from assembly lines to data entry – are now vulnerable to automation. Self-driving trucks loom on the horizon, threatening long-haul careers. Chatbots handle customer service queries with machine-like precision, potentially displacing human representatives. Headlines scream of 'mass unemployment' and a 'robot takeover,' fueling a sense of doom and gloom. But before we succumb to dystopian visions, let's take a breath and look at the bigger picture."
      },
      "blog n":
      {
        "title n": "description n"
      }
    }
    """

    blog_prompt = """
    I want you to act as a seasoned blog writer. The user will provide you with a blog title you will need to write content for. You must ensure that the content you generate sounds and looks human written ie 
    Below are a few things to look out for when editing.

    Repeated information: Cut out unnecessary words, repeated phrases, or sentences that simply reiterate the same point you’ve made earlier. 
    Heavy-handed language: Look out for formal or clunky words and phrases and simplify them to make your text sound more personable. For example, change “utilize” to “use,” “assist” to “help,” “endeavor” to “try,” and “pertaining to” to “about.”
    Facts: Always double-check any facts or statistics for accuracy and update with more recent ones (if available). Statista, Hubspot’s blog, and the SemRush blog are great places to find up-to-date statistics on content marketing, for example.
    Definitive statements: When reading AI-generated text, I always ask myself, “Is this statement completely true? Or could there be other opinions on this topic out there?” Be critical and trust your instincts. Read other articles and reports on your topic to see how yours compares and edit accordingly.
    """

    # Concatenate user request with base prompt
    prompt = base_prompt + user_request

    try:
        # Generate titles
        titles = model.generate_content(prompt)

        # Extract JSON data
        json_data = titles.text
        content = json.loads(extract_json(json_data))

        # Generate content for each title
        blogs = []
        for _, value in content.items():
            blog_title = value["title"]
            blog_description = value["description"]
            blog_content = model.generate_content(blog_prompt + blog_title + blog_description)
            blogs.append((blog_title, blog_content.text))
        
        return blogs

    except Exception as e:
        st.error(f"Error generating blogs: {e}")

# Function to extract JSON data from response text
def extract_json(response_text):
    start_index = response_text.find('{')  # Find the index of the first '{'
    end_index = response_text.rfind('}')  # Find the index of the last '}'

    if start_index == -1 or end_index == -1 or end_index <= start_index:
        raise ValueError("Invalid schema format: Couldn't find start or end brackets.")

    json_object = response_text[start_index:end_index + 1]  # Extract the content within the brackets
    return json_object

# Function to display blogs in Streamlit
def display_blogs():
    try:
        conn = sqlite3.connect('blogs.db')
        c = conn.cursor()
        c.execute("SELECT title FROM blogs")
        titles = c.fetchall()
        conn.close()
        return [title[0] for title in titles]
    except Exception as e:
        st.error(f"Error displaying blogs: {e}")
        return []

def main():
    st.title("Blog App")

    # Form for user input
    user_request = st.text_area("Enter your request:")
    if st.button("Generate Blogs"):
        if user_request:
            blogs = generate_blogs(user_request)
            if blogs:
                for title, content in blogs:
                    add_blog(title, content)  # Add title and content to the database
                st.success("Blogs generated and added successfully!")
        else:
            st.warning("Please enter your request.")

    # Main content area for displaying and selecting blog titles
    st.header("Blog Titles")
    titles = display_blogs()
    selected_title = st.selectbox("Select a blog title", titles)
    if selected_title:
        conn = sqlite3.connect('blogs.db')
        c = conn.cursor()
        c.execute("SELECT content FROM blogs WHERE title=?", (selected_title,))
        content = c.fetchone()
        conn.close()
        if content:
            st.subheader(selected_title)
            st.write(content[0])
        else:
            st.warning("No content found for this blog.")

if __name__ == "__main__":
    main()
