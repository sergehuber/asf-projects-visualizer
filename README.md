# ASF Projects Visualizer

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

5. Getting your OpenAI API Key:
   - Go to https://platform.openai.com/signup and sign up for an account if you don't have one.
   - After logging in, navigate to https://platform.openai.com/account/api-keys
   - Although they will recommend a new project API key, for the moment this project only works with the old secret API key
   - Click on "Create new secret key"
   - Copy the generated key (you won't be able to see it again)
   - Paste this key as the value for OPENAI_API_KEY in your .env file

6. Run the initial data collection script:
   ```
   python src/data_collector.py --collect
   ```

7. (Optional) If using a local LLM, train it using the collected data:
   ```
   python src/fine_tune_model.py
   ```

8. Run the enhanced data collection using the configured LLM:
   ```
   python src/data_collector.py --enhance
   ```

9. Start the Flask server:
   ```
   python src/app.py
   ```

10. Open `http://127.0.0.1:5000` in a web browser.

## Usage

- Use the dimension selector to choose how projects are grouped (category, key features, refined category, or programming language).
- Enter your requirements in the input field and click "Query" to find relevant Apache projects.
- Use the checkboxes to filter projects by their groupings.
- Click on a project to view more details, including its description, features, and latest release information.

## LLM Configuration

This project supports two LLM providers: OpenAI and a local LLM. You can configure which one to use by setting the `LLM_PROVIDER` environment variable in the `.env` file.

### Using OpenAI (Recommended)

Set the `LLM_PROVIDER` to `openai` and provide your `OPENAI_API_KEY` in the `.env` file. This is currently the recommended option due to its superior performance and quality of results.

### Using Local LLM (Experimental)

Set the `LLM_PROVIDER` to `local` and specify your `LOCAL_MODEL_NAME` in the `.env` file. 

**Note:** The local LLM option is currently experimental and not yet as performant as the OpenAI backend. The fine-tuning process and training algorithm need further improvement to match the quality of OpenAI's models. We welcome contributions from the community to enhance the local LLM training and performance.

## Project Structure

- `src/data_collector.py`: Handles data collection and enhancement for Apache projects.
- `src/app.py`: Flask server that provides API endpoints for the frontend.
- `src/llms.py`: Contains the LLM interface for querying project information.
- `src/config.py`: Manages configuration and environment variables.
- `src/fine_tune_model.py`: Script for fine-tuning a local LLM (if used).
- `static/`: Contains the frontend files (HTML, CSS, JavaScript).

## Contributing

Contributions are welcome! Here are some areas where we particularly need help:

1. Improving the fine-tuning process for the local LLM to enhance its performance.
2. Developing better training algorithms for the local model to improve the quality of its outputs.
3. Expanding the dataset used for training to cover a wider range of Apache projects and their characteristics.

If you're interested in contributing to these areas or have other ideas for improvement, please feel free to submit a Pull Request or open an Issue for discussion.

## License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for details.