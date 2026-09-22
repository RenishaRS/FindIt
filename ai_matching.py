from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_similarity(lost_item, found_item):
    """
    Compare a lost item with a found item
    and return a similarity percentage.
    """

    lost_text = (
        lost_item["item_name"] + " " +
        lost_item["location"] + " " +
        lost_item["description"]
    )

    found_text = (
        found_item["item_name"] + " " +
        found_item["location"] + " " +
        found_item["description"]
    )

    documents = [lost_text, found_text]

    vectorizer = TfidfVectorizer()

    tfidf_matrix = vectorizer.fit_transform(documents)

    similarity = cosine_similarity(
        tfidf_matrix[0:1],
        tfidf_matrix[1:2]
    )[0][0]

    return round(similarity * 100, 2)


def find_matches(lost_item, found_items, minimum_score=30):
    """
    Compare one lost item with multiple found items.

    Only matches above the minimum similarity score
    are returned.
    """

    matches = []

    for found_item in found_items:

        score = calculate_similarity(
            lost_item,
            found_item
        )

        if score >= minimum_score:

            matches.append({
                "item": found_item,
                "score": score
            })

    matches.sort(
        key=lambda match: match["score"],
        reverse=True
    )

    return matches


# Test the AI matching system
if __name__ == "__main__":

    lost_item = {
        "item_name": "Black Wallet",
        "location": "College Library",
        "description": "Black leather wallet with three card slots"
    }

    found_items = [

        {
            "item_name": "Black Wallet",
            "location": "College Library",
            "description": "Black leather wallet found near the reading area"
        },

        {
            "item_name": "Blue Water Bottle",
            "location": "College Canteen",
            "description": "Blue bottle found near the tables"
        },

        {
            "item_name": "Black Pencil Case",
            "location": "Computer Lab",
            "description": "Black pencil pouch with several pens"
        }

    ]

    matches = find_matches(
        lost_item,
        found_items
    )

    print("\nAI-Assisted Matching Results")
    print("----------------------------")

    if matches:

        for match in matches:

            print(
                f"{match['item']['item_name']} "
                f"-> {match['score']}% similarity"
            )

    else:

        print("No possible matches found.")