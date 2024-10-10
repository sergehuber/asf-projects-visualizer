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

4. Create a `.env` file in the root directory and add your configuration:
   ```
   LLM_PROVIDER=openai  # or 'local'
   OPENAI_API_KEY=your_api_key_here
   OPENAI_MODEL=gpt-4o  # or another OpenAI model
   LOCAL_MODEL_NAME=your_local_model_name  # if using a local LLM
   HUGGINGFACE_TOKEN=your_huggingface_token  # if using Hugging Face models
   ```

5. Run the initial data collection script:
   ```
   python src/data_collector.py --collect
   ```

6. (Optional) If using a local LLM, train it using the collected data:
   ```
   python src/fine_tune_model.py
   ```

7. Run the enhanced data collection using the configured LLM:
   ```
   python src/data_collector.py --enhance
   ```

8. Start the Flask server:
   ```
   python src/app.py
   ```

9. Open `http://127.0.0.1:5000` in a web browser.

## Usage

- Use the dimension selector to choose how projects are grouped (category, key features, refined category, or programming language).
- Enter your requirements in the input field and click "Query" to find relevant Apache projects.
- Use the checkboxes to filter projects by their groupings.
- Click on a project to view more details, including its description, features, and latest release information.

## LLM Configuration

This project supports two LLM providers: OpenAI and a local LLM. You can configure which one to use by setting the `LLM_PROVIDER` environment variable in the `.env` file.

### Using OpenAI

Set the `LLM_PROVIDER` to `openai` and provide your `OPENAI_API_KEY` in the `.env` file.

### Using Local LLM

Set the `LLM_PROVIDER` to `local` and specify your `LOCAL_MODEL_NAME` in the `.env` file. Make sure you have trained the local LLM before using this option.

## Project Structure

- `src/data_collector.py`: Handles data collection and enhancement for Apache projects.
- `src/app.py`: Flask server that provides API endpoints for the frontend.
- `src/llms.py`: Contains the LLM interface for querying project information.
- `src/config.py`: Manages configuration and environment variables.
- `src/fine_tune_model.py`: Script for fine-tuning a local LLM (if used).
- `static/`: Contains the frontend files (HTML, CSS, JavaScript).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.