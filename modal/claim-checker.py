import modal

app = modal.App(name="claim-checker")
gpu = "a10g"

claim_checker_image = modal.Image.debian_slim(python_version="3.10").pip_install(
    "unsloth", "bitsandbytes", "torch"
)


def inference_prompt(claim, article):
    return f"""You are an impartial evaluator tasked with determining the relationship between a given claim and an article's content. Your job is to analyze the text of the article and assess whether it **agrees**, **disagrees**, is **unrelated**, or if there was an **error** in processing the input. Additionally, provide a single overall comment summarizing your reasoning first, followed by a probability score (0%-100%) for each label.

If the "An error occurred" label has a probability higher than 5%, it indicates a significant pipeline issue. Set the probabilities for other labels to 0% in this case, and reflect this issue in your overall comment.

### Instructions:
1. Carefully read the claim and the article.
2. Write a **single overall comment** in 10 to 20 words summarizing your evaluation. Include:
   - Key points from the article and their relationship to the claim.
   - A note if an error occurred, such as the article being missing, corrupted, or unrelated to the claim.
3. Populate the following table of probabilities based on your evaluation:
   - **Label**:
     - **Agrees**: Use this label if the article explicitly supports the claim.
     - **Disagrees**: Use this label if the article explicitly opposes the claim.
     - **Unrelated**: Use this label if the article does not discuss the claim or its related concepts.
     - **An error occurred**: Use this label if there was an issue in processing or fetching the article.
   - **Probability**: Provide a certainty score as a percentage (0%-100%) for each label.

### Output Format:
**Overall Comment:**  
[Insert a concise explanation summarizing the reasoning for your evaluation.]

| Label              | Probability |
|--------------------|-------------|
| Agrees             | [0-100]%    |
| Disagrees          | [0-100]%    |
| Unrelated          | [0-100]%    |
| An error occurred  | [0-100]%    |

---

**Claim:**  
`"{claim}"`

**Article:**  
```  
{article["content"]}
```
"""


def load_model():
    from unsloth import FastLanguageModel
    import time

    max_seq_length = 2048
    dtype = None
    model_name_or_path = "Eugenius0/lora_model_tuned"

    # Load model
    print("Loading model ...")
    time_start = time.time()
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name_or_path,
        max_seq_length=max_seq_length,
        dtype=dtype,
        load_in_4bit=True,
    )
    print(f"model loaded in {time.time() - time_start} s")
    FastLanguageModel.for_inference(model)  # Enable native 2x faster inference
    return model, tokenizer


def infer_stance(claim, article, model_tokenizer=None):
    try:
        import torch
        import time

        if model_tokenizer == None:
            model, tokenizer = load_model()
        else:
            model, tokenizer = model_tokenizer

        title = article["title"]
        publisher = article["publisher"]

        device = "cuda" if torch.cuda.is_available() else "cpu"

        prompt = inference_prompt(claim, article)
        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]
        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(device)

        # Generate response
        print(f"Analyzing article {title} from {publisher}...")
        time_start = time.time()
        outputs = model.generate(
            input_ids=inputs,
            max_new_tokens=256,
            use_cache=True,
            temperature=1.2,
            repetition_penalty=1.1,
            min_p=0.1,
        )
        print(f"Done in {time.time() - time_start}.")
        time_start = time.time()
        response = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        if len(response) > len(prompt):
            return response[len(prompt) :]
        return response
    except Exception as e:
        return f"Error while inferring stance: {e}"


@app.function(gpu=gpu, image=claim_checker_image)
def batch_infer_stances(claim, articles):
    model_tokenizer = load_model()
    return [infer_stance(claim, article, model_tokenizer) for article in articles]


@app.local_entrypoint()  # defining a CLI entrypoint
def main(claim):
    from googlesearch import search
    from newspaper import Article
    from urllib.parse import urlparse

    def fetch_urls(query, num_results=3):
        return [url for url in search(query, num_results=num_results)]

    def scrape_article(url):
        try:
            article = Article(url)
            article.download()
            article.parse()
            publisher = (
                urlparse(url).netloc.split(".")[-2].capitalize()
            )  # Extract publisher's name
            return {
                "title": article.title,
                "content": article.text,
                "url": url,
                "publisher": publisher,
            }
        except Exception as e:
            print(f"Failed to fetch article from {url}: {e}")

    def query_articles(claim, num_results=3):
        print(f"Fetching URLs for query: {claim}")

        # Fetch URLs
        urls = fetch_urls(claim, num_results)
        print("Fetched URLs:")
        for url in urls:
            print(url)

        articles = []

        for url in urls:
            print(f"\nScraping {url}...")
            article = scrape_article(url)
            if article:
                print("\nScraped Content (First 500 characters):")
                print(article["content"][:500])
                articles.append(article)
            else:
                print("\nFailed to scrape content.")

        return articles

    articles = query_articles(claim)
    for response in batch_infer_stances.remote(claim, articles):
        print(response)
