# Text Summarizer

This is a text summarizer that uses the GPT API to summarize text from a given URL. 

## Usage

```sh
docker run -d -e OPENAI_API_KEY=... -p 8501:8501 tonypai/text-summarizer
```

| Environment Variable | Description |
|----------------------|-------------|
| OPENAI_API_KEY       | API key for OpenAI GPT API |
| OPENAI_MODEL         | Model to use for text summarization (default: gpt-3.5-turbo) |
| TS_LANG              | Language of the text to be summarized (default: en_us) |

To use it, visit `http://localhost:8501` and simply enter a URL in the input box and click enter. The program will then scrape the content from the URL, summarize it using the OpenAI API, and display the key takeaways.
