import gradio as gr
import logging

from query_articles import query_articles
from response_handler import parse_result, get_stance

# from inference_local import batch_infer_stances

import modal

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Logs to console
        logging.FileHandler("gradio_app.log"),  # Logs to file
    ],
)


COLOR_MAP = {
    "supports": "green",
    "contradicts": "orange",
    "nuanced": "#c9dfe3",
    "unrelated": "white",
    "error": "gray",
}


def verify_claim(claim, num_articles=6):
    try:
        # articles = [(url, scrape_article(url)) for url in urls]
        articles = query_articles(claim, num_articles)
        logging.info(f"Scraped {len(articles)} articles.")

        batch_infer_stances = modal.Function.lookup(
            "claim-checker", "batch_infer_stances"
        )

        results = []
        results_raw = batch_infer_stances.remote(claim, articles)
        for result_raw, article in zip(results_raw, articles):
            analyze = parse_result(result_raw)
            if analyze["error_flag"]:
                continue
            stance = get_stance(analyze)
            color = COLOR_MAP.get(stance, "black")
            publisher = article["publisher"]  # Extract publisher's name
            results.append(
                {
                    "url": article["url"],
                    "publisher": publisher,
                    "comment": analyze["comment"],
                    "stance": stance,
                    "color": color,
                }
            )
        print(results)
        return results

    except Exception as e:
        error_message = f"Error occurred: {e}"
        logging.error(error_message, exc_info=True)
        return [
            {
                "url": "N/A",
                "publisher": "N/A",
                "comment": error_message,
                "stance": "N/A",
                "color": "grey",
            }
        ]


def create_table(results):
    table_html = """
    <style>
        .custom-table {{
            border-collapse: collapse;
            width: 100%;
            text-align: left;
        }}
        .custom-table th, .custom-table td {{
            border: 1px solid #ddd;
            padding: 8px;
        }}
        .custom-table th {{
            background-color: #f4f4f4;
        }}
        .custom-table tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .custom-table tr:hover {{ background-color: #f1f1f1; }}
    </style>
    <table class="custom-table">
        <thead>
            <tr>
                <th>Article Link</th>
                <th>Publisher</th>
                <th>Comment</th>
                <th>Stance</th>
            </tr>
        </thead>
        <tbody>
    """
    for result in results:
        table_html += f"""
        <tr style="background-color: {result['color']};">
            <td><a href="{result['url']}" target="_blank">View Article</a></td>
            <td>{result['publisher']}</td>
            <td>{result['comment']}</td>
            <td>{result['stance']}</td>
        </tr>
        """
    table_html += "</tbody></table>"
    return table_html


def main():
    interface = gr.Interface(
        fn=lambda claim, num_articles: create_table(verify_claim(claim, num_articles)),
        inputs=[
            gr.Textbox(label="Enter a Claim"),
            gr.Number(
                label="Number of articles.",
                value=4,
                interactive=True,
                minimum=1,
                maximum=12,
            ),
        ],
        outputs=gr.HTML(),
        title="Claim Verification Tool",
        description="Input a claim to verify whether web sources support, contradict, or remain neutral about it. Results include article links, publishers, comment, and stances.",
    )

    interface.launch(share=True, debug=True)


if __name__ == "__main__":
    main()
