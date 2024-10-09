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

4. Set up your OpenAI API key as an environment variable (if using OpenAI):
   ```
   export OPENAI_API_KEY=your_api_key_here
   ```

5. Run the initial data collection script:
   ```
   python src/data_collector.py --collect
   ```

6. Train the local LLM using the collected data:
   ```
   python src/fine_tune_model.py
   ```

7. Run the enhanced data collection using the trained LLM:
   ```
   python src/data_collector.py --enhance
   ```

8. Start the Flask server:
   ```
   python src/app.py
   ```

9. Open `http://127.0.0.1:5000` in a web browser.

## Usage

Enter your requirements in the input field and click "Filter Projects" to visualize relevant Apache projects.

## LLM Configuration

This project supports two LLM providers: OpenAI and a local LLM. You can configure which one to use by setting the `LLM_PROVIDER` environment variable.

### Using OpenAI

Set the `LLM_PROVIDER` environment variable to `openai`:

      export LLM_PROVIDER=openai

### Using Local LLM

Set the `LLM_PROVIDER` environment variable to `local`:

      export LLM_PROVIDER=local

Make sure you have trained the local LLM before using this option.