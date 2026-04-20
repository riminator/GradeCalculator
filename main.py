import requests

CANVAS_URL = "https://utexas.instructure.com"
API_TOKEN = "insert"
COURSE_ID = "1442211"

WEIGHTS = {
    "quiz": 0.20,
    "worksheet": 0.15,
    "exam1": 0.20,
    "exam2": 0.20,
    "final": 0.25
}

DROP_RULES = {
    "quiz": 2,
    "worksheet": 1,
    "exam1": 0,
    "exam2": 0,
    "final": 0
}

MANUAL_MAP = {
    "Midterm 1": "exam1",
    "Midterm 2": "exam2",
    "Final Exam": "final"
}

headers = {"Authorization": f"Bearer {API_TOKEN}"}

def extract_score(sub):
    if sub is None:
        return None

    if "score" in sub and sub["score"] is not None:
        return float(sub["score"])

    if "entered_score" in sub and sub["entered_score"] is not None:
        return float(sub["entered_score"])

    if "grade" in sub and sub["grade"] not in [None, ""]:
        try:
            return float(sub["grade"])
        except:
            pass

    return None

def get_assignments():
    url = f"{CANVAS_URL}/api/v1/courses/{COURSE_ID}/assignments?per_page=100"
    return requests.get(url, headers=headers).json()

def get_submissions():
    url = f"{CANVAS_URL}/api/v1/courses/{COURSE_ID}/students/submissions?per_page=100&include[]=assignment"
    data = requests.get(url, headers=headers).json()

    best = {}

    for s in data:
        aid = s["assignment_id"]

        score = s.get("score")

        # keep BEST score per assignment
        if aid not in best or score > best[aid].get("score", 0):
            best[aid] = s

    return best

def is_real_assignment(a):
    return (
        a.get("published", True) and
        a.get("points_possible", 0) > 0
    )

def categorize(name):
    n = name.lower()

    if "quiz" in n:
        if "practice" in n or "review" in n or "ungraded" in n:
            return "worksheet"
        return "quiz"

    if "worksheet" in n:
        return "worksheet"

    if "exam 1" in n or "midterm 1" in n:
        return "exam1"

    if "exam 2" in n or "midterm 2" in n:
        return "exam2"

    if "final" in n:
        return "final"

    return "worksheet"

def build_items(assignments, submissions):
    items = []

    for a in assignments:
        aid = a["id"]
        name = a["name"]
        possible = a.get("points_possible") or 0

        sub = submissions.get(aid, {})

        score = extract_score(sub)

        if score is not None:
            score = float(score)

        items.append({
            "name": name,
            "score": score,
            "possible": possible,
            "category": categorize(name)
        })

    return items

def apply_drop(items, drop_n):
    valid = [
        i for i in items
        if i["score"] is not None and i["possible"] > 0
    ]

    # safety: avoid division errors
    valid.sort(key=lambda x: x["score"] / x["possible"] if x["possible"] else 0)

    return valid[drop_n:] if drop_n > 0 else valid

def category_score(items):
    earned = 0
    possible = 0

    for i in items:
        if i["score"] is None or i["possible"] is None:
            continue
        if i["possible"] == 0:
            continue

        earned += i["score"]
        possible += i["possible"]

    return earned / possible if possible > 0 else 0

def calculate_final(items):
    scores = {}
    used_weights = {}

    for c in WEIGHTS:
        if c == "final":
            continue 

        cat_items = [i for i in items if i["category"] == c]
        cat_items = apply_drop(cat_items, DROP_RULES.get(c, 0))

        if len(cat_items) == 0:
            continue

        scores[c] = category_score(cat_items)
        used_weights[c] = WEIGHTS[c]

    weight_sum = sum(used_weights.values())

    final = sum(
        scores[c] * used_weights[c] / weight_sum
        for c in scores
    )

    return final, scores

def needed_on_final(current, exam_weight, target):
    return (target - current * (1 - exam_weight)) / exam_weight

def main():
    assignments = get_assignments()
    submissions = get_submissions()

    items = build_items(assignments, submissions)

    final_grade, breakdown = calculate_final(items)

    print("\n📘 GRADE BREAKDOWN")
    print("=" * 50)

    for k in WEIGHTS:
        print(k, len([i for i in items if i["category"] == k]))

    for k, v in breakdown.items():
        print(f"{k}: {v*100:.2f}%")

    print(f"\n📊 CURRENT GRADE (pre-final): {final_grade*100:.2f}%")

    exam_weight = WEIGHTS["final"]

    needed_90 = needed_on_final(final_grade, exam_weight, 0.90)
    needed_93 = needed_on_final(final_grade, exam_weight, 0.93)

    print("REAL QUIZ ITEMS:")
    for i in items:
        if i["category"] == "quiz":
            print(i["name"], i["score"], "/", i["possible"])

    print("\n🎯 FINAL EXAM REQUIREMENTS")
    print(f"Need for 90% overall: {needed_90*100:.2f}%")
    print(f"Need for 93% overall: {needed_93*100:.2f}%")

if __name__ == "__main__":
    main()
