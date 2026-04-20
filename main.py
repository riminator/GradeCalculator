import requests

# =========================
# CONFIG (FILL THESE IN)
# =========================
CANVAS_URL = "https://utexas.instructure.com/"
API_TOKEN = "1017~6nUrXLYhYDXDf3wY4eTf68AkYnyruv6tJPBKcuzvhHvNUPUGazLWk8QnYTACGkEX"
COURSE_ID = "1442211"

headers = {"Authorization": f"Bearer {API_TOKEN}"}

# =========================
# HANDLE PAGINATION (CRITICAL FIX)
# =========================
def get_all_pages(url):
    items = []

    while url:
        response = requests.get(url, headers=headers)
        data = response.json()

        if isinstance(data, list):
            items.extend(data)
        else:
            break

        # Canvas pagination header
        url = response.links.get("next", {}).get("url")

    return items

# =========================
# ALL ASSIGNMENTS (WORKSHEETS INCLUDED)
# =========================
def get_assignments():
    url = f"{CANVAS_URL}/api/v1/courses/{COURSE_ID}/assignments?per_page=100"
    return get_all_pages(url)

# =========================
# ALL SUBMISSIONS
# =========================
def get_submissions():
    url = f"{CANVAS_URL}/api/v1/courses/{COURSE_ID}/students/submissions?include[]=assignment&per_page=100"
    subs = get_all_pages(url)

    return {s["assignment_id"]: s for s in subs if "assignment_id" in s}

# =========================
# QUIZZES (CLASSIC ONLY)
# =========================
def get_quiz_scores():
    url = f"{CANVAS_URL}/api/v1/courses/{COURSE_ID}/quizzes?per_page=100"
    quizzes = get_all_pages(url)

    quiz_scores = {}

    for q in quizzes:
        quiz_id = q["id"]

        url2 = f"{CANVAS_URL}/api/v1/courses/{COURSE_ID}/quizzes/{quiz_id}/submission"
        sub = requests.get(url2, headers=headers).json()

        submission = (sub.get("quiz_submissions") or [{}])[0]
        quiz_scores[quiz_id] = submission.get("score")

    return quiz_scores

# =========================
# PRINT EVERYTHING
# =========================
def print_gradebook():
    assignments = get_assignments()
    submissions = get_submissions()

    print("\n📘 FULL CANVAS GRADEBOOK\n")
    print("=" * 60)

    total = 0
    earned = 0

    for a in assignments:
        aid = a["id"]
        name = a["name"]
        possible = a.get("points_possible") or 0

        sub = submissions.get(aid)

        # FIX: correct score handling
        score = sub.get("score") if sub else None

        if score is None:
            display = "Not graded / Missing"
            score_val = 0
        else:
            display = f"{score}/{possible}"
            score_val = score

        print(name)
        print(f"   Score: {display}")
        print("-" * 60)

        if possible:
            total += possible
            earned += score_val if score is not None else 0

    if total:
        print(f"\n🎯 FINAL GRADE: {(earned/total)*100:.2f}%")

def main():
    print_gradebook()

if __name__ == "__main__":
    main()