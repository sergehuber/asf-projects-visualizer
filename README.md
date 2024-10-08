# Apache Projects Visualizer

This project creates a visual map of Apache projects and allows filtering based on user queries.

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/apache-projects-visualizer.git
   cd apache-projects-visualizer
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your OpenAI API key as an environment variable:
   ```
   export OPENAI_API_KEY=your_api_key_here
   ```

5. Run the data collection script:
   ```
   python src/data_collector.py
   ```

6. Start the Flask server:
   ```
   python src/app.py
   ```

7. Open `static/index.html` in a web browser.

## Usage

Enter your requirements in the input field and click "Filter Projects" to visualize relevant Apache projects.

## License

This project is licensed under the MIT License.
